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
    """Ensure the user's group membership matches their EmployeeProfile.role.
    - On create: add to the role group
    - On update: remove from other role groups and add to the current role group
    """
    role = instance.role
    # Ensure the role group exists
    role_group, _ = Group.objects.get_or_create(name=role)

    # All role groups in our RBAC scheme
    role_group_names = {"admin", "manager", "salesman"}
    existing_role_groups = Group.objects.filter(name__in=role_group_names)

    # Remove user from any other role groups
    instance.user.groups.remove(*existing_role_groups)

    # Add to the current role group
    instance.user.groups.add(role_group)
