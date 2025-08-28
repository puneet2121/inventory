from django.core.exceptions import ValidationError
from django.db import models, transaction

from app.core.models import TenantAwareModel
from app.employee.models import EmployeeProfile
from app.inventory.models import Inventory, Product, StockMovement, StockMovementType
from app.customers.models import Customer
from django.contrib.auth.models import User
from app.core.tenant_middleware import get_current_tenant

ORDER_STATUS_CHOICES = [
    ('draft', 'Draft'),
    ('completed', 'Completed'),
    ('cancelled', 'Cancelled'),
]


class SalesOrder(TenantAwareModel):
    customer = models.ForeignKey(Customer, on_delete=models.SET_NULL, null=True, blank=True,
                                 related_name="sales_orders")
    created_at = models.DateTimeField(auto_now_add=True)
    customer_type = models.CharField(max_length=20,
                                     choices=[('walk_in', 'Walk-in Customer'), ('registered', 'Registered Customer')],
                                     default='walk_in')
    employee = models.ForeignKey(EmployeeProfile, on_delete=models.SET_NULL, null=True, blank=True,
                                 related_name="sales_orders")
    location = models.CharField(max_length=100, default='Main Store')  # Add default location
    status = models.CharField(max_length=20, choices=ORDER_STATUS_CHOICES, default='draft')
    note = models.TextField(blank=True, null=True)
    order_number = models.CharField(max_length=20, blank=True, null=True)
    cached_total = models.DecimalField(max_digits=12, decimal_places=2, default=0)

    @property
    def total_price(self):
        return sum(item.total_price for item in self.items.all())

    def finalize_order(self):
        if self.status == 'completed':
            raise ValidationError("Order is already completed.")

        with transaction.atomic():
            # Check inventory availability per location
            for item in self.items.select_related('product').all():
                try:
                    inventory = Inventory.objects.get(product=item.product, location=self.location)
                except Inventory.DoesNotExist:
                    raise ValidationError(f"No inventory record found for {item.product.name} at {self.location}")

                if inventory.quantity < item.quantity:
                    raise ValidationError(f"Not enough stock for {item.product.name} at {self.location}")

            # Deduct inventory after all validations pass
            for item in self.items.select_related('product').all():
                inventory = Inventory.objects.get(product=item.product, location=self.location)
                inventory.quantity -= item.quantity
                inventory.save()
                # Log stock movement for sale (outbound)
                StockMovement.objects.create(
                    product=item.product,
                    location=self.location,
                    change_type=StockMovementType.SALE,
                    quantity_change=-(item.quantity),
                    related_sales_order=self,
                    tenant_id=self.tenant_id,
                    note=f"SO {self.order_number or self.id} finalized"
                )

            # Finalize order
            self.cached_total = self.total_price
            self.status = 'completed'
            self.save()

    def __str__(self):
        return f"Order #{self.id} - {self.customer.name or 'Walk-in Customer'}"

    class Meta:
        db_table = 'sales_order'
        unique_together = (('tenant_id', 'order_number'),)
        permissions = [
            ("view_reports", "Can view analytics and reports"),
        ]
        # Add database indexes for better performance
        indexes = [
            models.Index(fields=['status', 'created_at']),
            models.Index(fields=['customer', 'status']),
            models.Index(fields=['created_at']),
            models.Index(fields=['tenant_id', 'status']),
        ]

    def save(self, *args, **kwargs):
        # Ensure tenant_id is present before generating order number
        if not self.tenant_id:
            self.tenant_id = self.tenant_id or get_current_tenant()
        if not self.order_number:
            self.order_number = OrderNumberSequence.next_number(self.tenant_id)
        super().save(*args, **kwargs)


class OrderNumberSequence(TenantAwareModel):
    """Maintains a per-tenant counter for SalesOrder.order_number generation."""
    last_number = models.PositiveIntegerField(default=0)

    class Meta:
        db_table = 'order_number_sequence'

    @classmethod
    def next_number(cls, tenant_id):
        if not tenant_id:
            # Fallback to 1 if tenant unknown; still avoids global collisions
            return f"SO-{1:05d}"
        with transaction.atomic():
            seq = cls._base_manager.select_for_update().filter(tenant_id=tenant_id).first()
            if not seq:
                seq = cls(tenant_id=tenant_id, last_number=0)
            seq.last_number += 1
            seq.save()
            return f"SO-{seq.last_number:05d}"


class InvoiceNumberSequence(TenantAwareModel):
    """Maintains a per-tenant counter for Invoice.invoice_number generation."""
    last_number = models.PositiveIntegerField(default=0)

    class Meta:
        db_table = 'invoice_number_sequence'

    @classmethod
    def next_number(cls, tenant_id):
        if not tenant_id:
            # Fallback to 1 if tenant unknown; still avoids global collisions
            return f"INV-{1:05d}"
        with transaction.atomic():
            seq = cls._base_manager.select_for_update().filter(tenant_id=tenant_id).first()
            if not seq:
                seq = cls(tenant_id=tenant_id, last_number=0)
            seq.last_number += 1
            seq.save()
            return f"INV-{seq.last_number:05d}"


class OrderItem(TenantAwareModel):
    sales_order = models.ForeignKey(SalesOrder, on_delete=models.CASCADE, related_name="items")
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField()
    price = models.DecimalField(max_digits=10, decimal_places=2)
    total_price = models.DecimalField(max_digits=15, decimal_places=2, blank=True, null=True)

    def save(self, *args, **kwargs):
        """Automatically calculate total price and adjust inventory."""
        with transaction.atomic():
            # Adjust inventory
            self.total_price = self.quantity * self.price
            super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.quantity} x {self.product.name} (Order #{self.sales_order.id})"

    class Meta:
        db_table = 'order_item'


class Invoice(TenantAwareModel):
    PAYMENT_STATUS_CHOICE = [
        ('unpaid', 'Unpaid'),
        ('partially_paid', 'Partially_paid'),
        ('paid', 'Paid'),
    ]

    sales_order = models.OneToOneField(SalesOrder, on_delete=models.CASCADE, related_name="invoice")
    date = models.DateTimeField(auto_now_add=True)
    payment_status = models.CharField(max_length=20, choices=PAYMENT_STATUS_CHOICE, default='unpaid')
    invoice_number = models.CharField(max_length=20, blank=True, null=True)
    cached_paid_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    total_invoice_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='invoices_created')
    notes = models.TextField(blank=True, null=True)

    def paid_amount(self):
        total_payments = self.payments.filter(type='payment').aggregate(
            total=models.Sum('amount')
        )['total'] or 0
        
        total_refunds = self.payments.filter(type='refund').aggregate(
            total=models.Sum('amount')
        )['total'] or 0
        
        return total_payments - total_refunds

    def update_cached_paid_amount(self):
        total_paid = self.paid_amount()
        self.cached_paid_amount = total_paid
        self.update_payment_status()
        self.save()

    def update_payment_status(self):
        total_price = self.sales_order.cached_total
        
        # Calculate net paid amount (payments - refunds)
        total_payments = self.payments.filter(type='payment').aggregate(
            total=models.Sum('amount')
        )['total'] or 0
        
        total_refunds = self.payments.filter(type='refund').aggregate(
            total=models.Sum('amount')
        )['total'] or 0
        
        net_paid_amount = total_payments - total_refunds
        
        if net_paid_amount >= total_price:
            self.payment_status = 'paid'
        elif net_paid_amount > 0:
            self.payment_status = 'partially_paid'
        else:
            self.payment_status = 'unpaid'

    def __str__(self):
        return f"Invoice #{self.invoice_number or self.id}"

    class Meta:
        db_table = 'invoice'
        unique_together = (('tenant_id', 'invoice_number'),)

    def save(self, *args, **kwargs):
        if not self.tenant_id:
            self.tenant_id = self.tenant_id or get_current_tenant()
        if not self.invoice_number:
            self.invoice_number = InvoiceNumberSequence.next_number(self.tenant_id)
        super().save(*args, **kwargs)


class Payment(TenantAwareModel):
    PAYMENT_METHOD_CHOICES = [
        ('cash', 'Cash'),
        ('upi', 'UPI'),
    ]
    PAYMENT_TERM_CHOICES = [
        ('net_30', 'Net 30'),
        ('net_60', 'Net 60'),
        ('net_90', 'Net 90'),
    ]
    PAYMENT_TYPE_CHOICES = [
        ('payment', 'Payment'),
        ('refund', 'Refund'),
    ]

    invoice = models.ForeignKey(Invoice, on_delete=models.CASCADE, related_name="payments")
    amount = models.DecimalField(max_digits=15, decimal_places=2)
    payment_method = models.CharField(max_length=10, choices=PAYMENT_METHOD_CHOICES)
    date = models.DateTimeField(auto_now_add=True)
    reference = models.CharField(max_length=100, blank=True, null=True)
    # payment_term = models.CharField(max_length=10, choices=PAYMENT_TERM_CHOICES, default='net_30')
    # due_date = models.DateField()
    type = models.CharField(max_length=10, choices=PAYMENT_TYPE_CHOICES, default='payment')
    received_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='payments_received')

    def __str__(self):
        return f"Payment of {self.amount} for Invoice {self.invoice.invoice_number or self.invoice.id}"

    class Meta:
        db_table = 'payment'
