from django.db import models
from django.contrib.auth.models import User


class StaffTypeChoices(models.TextChoices):
    Manager = 'Manager', 'Manager'
    Salesman = 'Salesman', 'Salesman'


class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    role = models.CharField(max_length=50)
    bio = models.TextField(blank=True)
    staff_type = models.CharField(choices=StaffTypeChoices.choices)

    def __str__(self):
        return f"{self.user.username}'s Profile"

    class Meta:
        db_table = 'profile'
