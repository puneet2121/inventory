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
    ('in_transit', 'In Transit'),
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
    location = models.CharField(max_length=100, blank=True, null=True)
    status = models.CharField(max_length=20, choices=ORDER_STATUS_CHOICES, default='draft')
    note = models.TextField(blank=True, null=True)
    order_number = models.CharField(max_length=20, blank=True, null=True)
    cached_total = models.DecimalField(max_digits=12, decimal_places=2, default=0)

    @property
    def total_price(self):
        return sum(item.total_price for item in self.items.all())

    def finalize_order(self):
        """Finalize order.
        - Retail: deduct inventory now and log SALE.
        - Wholesale: requires in_transit first; on finalize, log SALE records with zero quantity (audit), no inventory change.
        """
        if self.status == 'completed':
            raise ValidationError("Order is already completed.")

        # Determine company type lazily to avoid circular imports
        from app.core.models import Company
        company = Company.objects.filter(id=self.tenant_id).first()
        is_wholesale = bool(company and company.company_type == 'wholesale')

        with transaction.atomic():
            if is_wholesale:
                if self.status != 'in_transit':
                    raise ValidationError("Wholesale orders must be moved to In Transit before completion.")

                # Create SALE records for audit without changing stock (already deducted at in_transit)
                transit_moves = StockMovement.objects.filter(
                    related_sales_order=self,
                    change_type=StockMovementType.SALE_IN_TRANSIT,
                )
                for mv in transit_moves:
                    StockMovement.objects.create(
                        product=mv.product,
                        location=mv.location,
                        change_type=StockMovementType.SALE,
                        quantity_change=0,
                        related_sales_order=self,
                        tenant_id=self.tenant_id,
                        note=f"Finalized from in-transit for SO {self.order_number or self.id}"
                    )

                self.cached_total = self.total_price
                self.status = 'completed'
                self.save()
                return

            # Retail flow: validate and deduct now
            # Validate inventory availability across ALL locations for each item
            for item in self.items.select_related('product').all():
                total_available = (Inventory.objects
                                   .filter(product=item.product)
                                   .aggregate(total=models.Sum('quantity'))['total'] or 0)
                if total_available < item.quantity:
                    raise ValidationError(f"Not enough stock for {item.product.name}")

            for item in self.items.select_related('product').all():
                qty_to_deduct = item.quantity
                inventories = list(Inventory.objects.select_for_update()
                                   .filter(product=item.product, quantity__gt=0)
                                   .order_by('-quantity'))
                for inv in inventories:
                    if qty_to_deduct <= 0:
                        break
                    deduct = min(inv.quantity, qty_to_deduct)
                    inv.quantity -= deduct
                    inv.save()
                    qty_to_deduct -= deduct
                    StockMovement.objects.create(
                        product=item.product,
                        location=inv.location,
                        change_type=StockMovementType.SALE,
                        quantity_change=-(deduct),
                        related_sales_order=self,
                        tenant_id=self.tenant_id,
                        note=f"SO {self.order_number or self.id} finalized"
                    )
                if qty_to_deduct > 0:
                    raise ValidationError(f"Insufficient stock while deducting for {item.product.name}")

            self.cached_total = self.total_price
            self.status = 'completed'
            self.save()

    def mark_in_transit(self):
        """Wholesale flow: deduct inventory now and log SALE_IN_TRANSIT, set status to in_transit."""
        if self.status not in ['draft']:
            raise ValidationError("Only draft orders can be moved to In Transit.")

        from app.core.models import Company
        company = Company.objects.filter(id=self.tenant_id).first()
        is_wholesale = bool(company and company.company_type == 'wholesale')
        if not is_wholesale:
            raise ValidationError("In Transit status is only applicable to wholesale.")

        with transaction.atomic():
            # Validate inventory availability across ALL locations for each item
            for item in self.items.select_related('product').all():
                total_available = (Inventory.objects
                                   .filter(product=item.product)
                                   .aggregate(total=models.Sum('quantity'))['total'] or 0)
                if total_available < item.quantity:
                    raise ValidationError(f"Not enough stock for {item.product.name}")

            for item in self.items.select_related('product').all():
                qty_to_deduct = item.quantity
                inventories = list(Inventory.objects.select_for_update()
                                   .filter(product=item.product, quantity__gt=0)
                                   .order_by('-quantity'))
                for inv in inventories:
                    if qty_to_deduct <= 0:
                        break
                    deduct = min(inv.quantity, qty_to_deduct)
                    inv.quantity -= deduct
                    inv.save()
                    qty_to_deduct -= deduct
                    StockMovement.objects.create(
                        product=item.product,
                        location=inv.location,
                        change_type=StockMovementType.SALE_IN_TRANSIT,
                        quantity_change=-(deduct),
                        related_sales_order=self,
                        tenant_id=self.tenant_id,
                        note=f"SO {self.order_number or self.id} moved to in-transit"
                    )
                if qty_to_deduct > 0:
                    raise ValidationError(f"Insufficient stock while deducting for {item.product.name}")

            self.cached_total = self.total_price
            self.status = 'in_transit'
            self.save()

    def __str__(self):
        return f"Order #{self.id} - {self.customer.name or 'Walk-in Customer'}"

    class Meta:
        db_table = 'sales_order'
        unique_together = (('tenant_id', 'order_number'),)
        permissions = [
            ("view_reports", "Can view analytics and reports"),
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
