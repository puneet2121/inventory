from django.db.models.signals import post_save
# Groups let you organize users and assign permissions to the group (instead of each user individually).
from django.contrib.auth.models import Group
# This receiver is a decorator used to connect your custom function to the signal (in our case: post_save).
# It tells Django:
# “Hey, when this model is saved, run this function.”
from django.dispatch import receiver
from .models import EmployeeProfile


@receiver(post_save, sender=EmployeeProfile)
def assign_role_permissions(sender, instance, created, **kwargs):
    if created:
        role = instance.role
        group, _ = Group.objects.get_or_create(name=role)
        instance.user.groups.add(group)
