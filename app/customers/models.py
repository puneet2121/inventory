from django.db import models


class Customer(models.Model):
    CUSTOMER_TYPE_CHOICES = [
        ('A', 'A - High Priority'),
        ('B', 'B - Medium Priority'),
        ('C', 'C - Low Priority'),
    ]

    name = models.CharField(max_length=255)
    city = models.CharField(max_length=100)
    customer_type = models.CharField(max_length=1, choices=CUSTOMER_TYPE_CHOICES)
    contact = models.CharField(max_length=15)
    email = models.EmailField(blank=True, null=True)
    shop = models.CharField(max_length=255, blank=True, null=True)
    total_debt = models.DecimalField(max_digits=10, decimal_places=2, default=0.0)

    def __str__(self):
        return self.name


class CustomerBalance(models.Model):
    customer = models.OneToOneField(Customer, on_delete=models.CASCADE, related_name="debt")
    total_balance = models.DecimalField(max_digits=10, decimal_places=2, default=0.0)
    @property
    def total_bal(self):
        sales_orders = self.customer.sales_orders.all()
        total_balance = sum(order.total_price - sum(payment.amount for payment in order.invoice.payments.all())
                            for order in sales_orders if hasattr(order, 'invoice'))
        return total_balance

    def __str__(self):
        return f"Debt for {self.customer.name}: {self.total_bal}"

    class Meta:
        db_table = 'customer_balance'
