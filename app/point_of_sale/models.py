from django.core.exceptions import ValidationError
from django.db import models, transaction
from app.employee.models import EmployeeProfile
from app.inventory.models import Inventory, Product
from app.customers.models import Customer

ORDER_STATUS_CHOICES = [
    ('draft', 'Draft'),
    ('completed', 'Completed'),
    ('cancelled', 'Cancelled'),
]


class SalesOrder(models.Model):
    customer = models.ForeignKey(Customer, on_delete=models.SET_NULL, null=True, blank=True, related_name="sales_orders")
    created_at = models.DateTimeField(auto_now_add=True)
    customer_type = models.CharField(max_length=20,
                                     choices=[('walk_in', 'Walk-in Customer'), ('registered', 'Registered Customer')],
                                     default='walk_in')
    employee = models.ForeignKey(EmployeeProfile, on_delete=models.SET_NULL, null=True, blank=True, related_name="sales_orders")

    status = models.CharField(max_length=20, choices=ORDER_STATUS_CHOICES, default='draft')
    note = models.TextField(blank=True, null=True)
    order_number = models.CharField(max_length=20, unique=True, blank=True, null=True)
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

            # Finalize order
            self.cached_total = self.total_price
            self.status = 'completed'
            self.save()

    def __str__(self):
        return f"Order #{self.id} - {self.customer.name or 'Walk-in Customer'}"

    class Meta:
        db_table = 'sales_order'


class OrderItem(models.Model):
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


class Invoice(models.Model):
    sales_order = models.OneToOneField(SalesOrder, on_delete=models.CASCADE, related_name="invoice")
    date = models.DateTimeField(auto_now_add=True)
    is_paid = models.BooleanField(default=False)
    invoice_number = models.CharField(max_length=20, unique=True, blank=True, null=True)
    cached_paid_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)

    @property
    def paid_amount(self):
        return sum(payment.amount for payment in self.payments.all())

    def update_cached_paid_amount(self):
        self.cached_paid_amount = sum(p.amount for p in self.payments.all())
        self.save()

    @property
    def payment_status(self):
        total_price = self.sales_order.cached_total
        if self.cached_paid_amount >= total_price:
            return 'paid'
        elif self.cached_paid_amount > 0:
            return 'partial'
        return 'unpaid'

    def __str__(self):
        return f"Invoice #{self.invoice_number or self.id}"

    class Meta:
        db_table = 'invoice'


class Payment(models.Model):
    PAYMENT_METHOD_CHOICES = [
        ('cash', 'Cash'),
        ('upi', 'UPI'),
    ]

    invoice = models.ForeignKey(Invoice, on_delete=models.CASCADE, related_name="payments")
    amount = models.DecimalField(max_digits=15, decimal_places=2)
    payment_method = models.CharField(max_length=10, choices=PAYMENT_METHOD_CHOICES)
    date = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Payment of {self.amount} for Invoice {self.invoice.invoice_number or self.invoice.id}"

    class Meta:
        db_table = 'payment'


class CustomerDebt(models.Model):
    customer = models.OneToOneField(Customer, on_delete=models.CASCADE, related_name="debt")

    @property
    def total_debt(self):
        sales_orders = self.customer.sales_orders.all()
        debt = sum(order.total_price - sum(payment.amount for payment in order.invoice.payments.all())
                   for order in sales_orders if hasattr(order, 'invoice'))
        return debt

    def __str__(self):
        return f"Debt for {self.customer.name}: {self.total_debt}"

    class Meta:
        db_table = 'customer_debt'
