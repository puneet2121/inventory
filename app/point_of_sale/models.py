from django.db import models

from app.employee.models import EmployeeProfile
from app.inventory.models import Inventory, Product
from app.customers.models import Customer  # Assuming you have a Customer model


class SalesOrder(models.Model):
    PAYMENT_STATUS_CHOICES = [
        ('unpaid', 'Unpaid'),
        ('partial', 'Partial'),
        ('paid', 'Paid'),
    ]

    PAYMENT_METHOD_CHOICES = [
        ('cash', 'Cash'),
        ('gpay', 'G-Pay'),
        ('cheque', 'Cheque'),
    ]

    customer = models.ForeignKey(Customer, on_delete=models.SET_NULL, null=True, blank=True, related_name="sales_orders")
    customer_name = models.CharField(max_length=200, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    total_price = models.DecimalField(max_digits=15, decimal_places=2, blank=True, null=True)
    paid_amount = models.DecimalField(max_digits=15, decimal_places=2, default=0.00)
    unpaid_amount = models.DecimalField(max_digits=15, decimal_places=2, default=0.00)
    payment_status = models.CharField(max_length=10, choices=PAYMENT_STATUS_CHOICES, default='unpaid')
    payment_method = models.CharField(max_length=10, choices=PAYMENT_METHOD_CHOICES, null=True, blank=True)
    employee = models.ForeignKey(EmployeeProfile, on_delete=models.SET_NULL, null=True, blank=True, related_name="sales_orders")

    def calculate_totals(self):
        """Calculate total and unpaid amounts."""
        self.total_price = sum(item.total_price for item in self.items.all())
        self.unpaid_amount = self.total_price - self.paid_amount

        # Update payment status
        if self.unpaid_amount <= 0:
            self.payment_status = 'paid'
        elif self.paid_amount > 0:
            self.payment_status = 'partial'
        else:
            self.payment_status = 'unpaid'

    def save(self, *args, **kwargs):
        """Calculate totals and update debt for customer."""
        self.calculate_totals()

        if self.customer and self.unpaid_amount > 0:
            customer_debt, created = CustomerDebt.objects.get_or_create(customer=self.customer)
            customer_debt.total_debt += self.unpaid_amount
            customer_debt.save()

        super().save(*args, **kwargs)

    def __str__(self):
        return f"Order #{self.id} - {self.customer_name or 'Walk-in Customer'}"

    class Meta:
        db_table = 'sales_order_pos'


class OrderItem(models.Model):
    sales_order = models.ForeignKey(SalesOrder, on_delete=models.CASCADE, related_name="items")
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField()
    price = models.DecimalField(max_digits=10, decimal_places=2)
    total_price = models.DecimalField(max_digits=15, decimal_places=2, blank=True, null=True)

    def save(self, *args, **kwargs):
        """Automatically calculate total price and adjust inventory."""
        self.total_price = self.quantity * self.price

        # Reduce inventory
        inventory = Inventory.objects.get(product=self.product)
        if inventory.quantity < self.quantity:
            raise ValueError(f"Not enough inventory for {self.product.name}. Available: {inventory.quantity}")
        inventory.quantity -= self.quantity
        inventory.save()

        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.quantity} x {self.product.name} (Order #{self.sales_order.id})"

    class Meta:
        db_table = 'order_item_pos'


class CustomerDebt(models.Model):
    customer = models.OneToOneField(Customer, on_delete=models.CASCADE, related_name="debt")
    total_debt = models.DecimalField(max_digits=15, decimal_places=2, default=0.00)

    def __str__(self):
        return f"Debt for {self.customer.name}: {self.total_debt}"

    class Meta:
        db_table = 'customer_debt'
