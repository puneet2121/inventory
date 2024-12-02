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


class CustomerDebt(models.Model):
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE)
    debt_amount = models.DecimalField(max_digits=15, decimal_places=2, default=0)

    def __str__(self):
        return f"Debt for {self.customer.name}"

