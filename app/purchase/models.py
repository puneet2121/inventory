from django.db import models
from app.employee.models import models


class ExpenseCategory(models.TextChoices):
    SUPPLIER = 'supplier', 'Supplier Purchase'
    SALARY = 'salary', 'Salary'
    RENT = 'rent', 'Rent'
    GAS = 'gas', 'Gas'
    OTHER = 'other', 'Other'


class Bill(models.Model):
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    bill_date = models.DateField()
    category = models.CharField(max_length=20, choices=ExpenseCategory.choices, default=ExpenseCategory.SUPPLIER)
    vehicle = models.CharField(max_length=20, null=True, blank=True)
    # Optional references
    paid_to = models.ForeignKey('employee.EmployeeProfile', null=True, blank=True, on_delete=models.SET_NULL)
    notes = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"{self.get_category_display()} - {self.amount} on {self.bill_date}"
