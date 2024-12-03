from django.db.models.signals import post_save
from django.contrib.auth.models import Group
from django.dispatch import receiver
from .models import EmployeeProfile


@receiver(post_save, sender=EmployeeProfile)
def assign_role_permissions(sender, instance, created, **kwargs):
    if created:
        role = instance.role
        group, _ = Group.objects.get_or_create(name=role)
        instance.user.groups.add(group)
