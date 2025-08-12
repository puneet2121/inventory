from django.apps import AppConfig
from django.db.models.signals import post_migrate


def _setup_role_groups(sender, **kwargs):
    """Ensure role-based groups exist and have appropriate permissions.
    - admin, manager: all permissions
    - salesman: only view_* permissions, excluding reports
    """
    from django.contrib.auth.models import Group, Permission

    # Create/get groups
    roles = ["admin", "manager", "salesman"]
    groups = {name: Group.objects.get_or_create(name=name)[0] for name in roles}

    # Permissions
    all_perms = Permission.objects.all()
    report_perm = Permission.objects.filter(codename="view_reports").first()

    # Assign permissions per role
    for role, group in groups.items():
        if role in ("admin", "manager"):
            # Full access
            group.permissions.set(all_perms)
        else:  # salesman: everything except reports
            salesman_perms = all_perms
            if report_perm:
                salesman_perms = all_perms.exclude(id=report_perm.id)
            group.permissions.set(salesman_perms)
        group.save()


class CoreConfig(AppConfig):
    name = 'app.core'
    default_auto_field = 'django.db.models.BigAutoField'

    def ready(self):
        # Ensure groups/permissions applied after migrations
        post_migrate.connect(_setup_role_groups, sender=self, dispatch_uid='core_setup_role_groups')
