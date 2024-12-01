from django.contrib.auth.models import AbstractUser
from django.db import models


class RoleChoices(models.TextChoices):
    ADMIN = 'Admin', 'Admin'
    MANAGER = 'Manager', 'Manager'
    SALESMAN = 'Salesman', 'salesman'
    LOGISTICS = 'Logistics', 'logistics'


class Employee(AbstractUser):
    employee_id = models.CharField(max_length=10, unique=True)
    role = models.CharField(max_length=20, choices=RoleChoices.choices, default=RoleChoices.SALESMAN)

    def __str__(self):
        return f"{self.employee_id} - {self.username} ({self.get_role_display()})"
