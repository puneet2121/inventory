from django.db import models, transaction
from app.employee.models import EmployeeProfile
from app.inventory.models import Inventory, Product
from app.customers.models import Customer  # Assuming you have a Customer model

ORDER_STATUS_CHOICES = [
    ('draft', 'Draft'),
    ('completed', 'Completed'),
    ('cancelled', 'Cancelled'),
]


class SalesOrder(models.Model):
    customer = models.ForeignKey(Customer, on_delete=models.SET_NULL, null=True, blank=True, related_name="sales_orders")
    customer_name = models.CharField(max_length=200, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    customer_type = models.CharField(max_length=20,
                                     choices=[('walk_in', 'Walk-in Customer'), ('registered', 'Registered Customer')],
                                     default='walk_in')
    employee = models.ForeignKey(EmployeeProfile, on_delete=models.SET_NULL, null=True, blank=True, related_name="sales_orders")

    status = models.CharField(max_length=20, choices=ORDER_STATUS_CHOICES, default='draft')

    @property
    def total_price(self):
        return sum(item.total_price for item in self.items.all())

    def __str__(self):
        return f"Order #{self.id} - {self.customer_name or 'Walk-in Customer'}"

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
            self.total_price = self.quantity * self.price

            # Adjust inventory
            inventory = Inventory.objects.select_for_update().get(product=self.product)
            if inventory.quantity < self.quantity:
                raise ValueError(f"Not enough inventory for {self.product.name}. Available: {inventory.quantity}")
            inventory.quantity -= self.quantity
            inventory.save()

            super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.quantity} x {self.product.name} (Order #{self.sales_order.id})"

    class Meta:
        db_table = 'order_item'


class Invoice(models.Model):
    PAYMENT_STATUS_CHOICES = [
        ('unpaid', 'Unpaid'),
        ('partial', 'Partial'),
        ('paid', 'Paid'),
    ]

    sales_order = models.OneToOneField(SalesOrder, on_delete=models.CASCADE, related_name="invoice")
    date = models.DateTimeField(auto_now_add=True)
    is_paid = models.BooleanField(default=False)

    @property
    def paid_amount(self):
        return sum(payment.amount for payment in self.payments.all())

    @property
    def payment_status(self):
        total_price = self.sales_order.total_price
        if self.paid_amount >= total_price:
            return 'paid'
        elif 0 < self.paid_amount < total_price:
            return 'partial'
        else:
            return 'unpaid'

    def __str__(self):
        return f"Invoice {self.invoice_id}"

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
        return f"Payment of {self.amount} for Invoice {self.invoice.invoice_id}"

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
