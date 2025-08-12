from django.contrib.auth.models import User
from django.db import models

from app.core.models import TenantAwareModel


class EmployeeProfile(TenantAwareModel):
    ROLE_CHOICES = [
        ('manager', 'Manager'),
        ('admin', 'Admin'),
        ('salesman', 'Salesman'),
    ]

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='employee_profile')
    role = models.CharField(max_length=10, choices=ROLE_CHOICES)
    phone = models.CharField(max_length=15, blank=True, null=True)

    def __str__(self):
        return f"{self.user.username} - {self.get_role_display()}"


class EmployeeAssignment(TenantAwareModel):
    LOCATION_CHOICES = [
        ('Jalandhar', 'Jalandhar'),
        ('Bhogpur', 'Bhogur'),
        ('Begowal', 'Begowal'),
        ('Nava_Sehar', 'Nava Sehar'),
    ]

    employee = models.ForeignKey(EmployeeProfile, on_delete=models.CASCADE)
    location = models.CharField(max_length=50, choices=LOCATION_CHOICES)
    date = models.DateField()
    note = models.TextField(blank=True)
    assigned_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='assigned_tasks')

    class Meta:
        unique_together = ('employee', 'date')

    def __str__(self):
        return f"{self.employee.user.get_full_name()} → {self.location.name} on {self.date}"