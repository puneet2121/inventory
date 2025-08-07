# yourapp/management/commands/create_roles.py

from django.core.management.base import BaseCommand
from django.contrib.auth.models import Group, Permission


class Command(BaseCommand):
    help = 'Creates default user roles and assigns permissions'

    def handle(self, *args, **options):
        config = {
            'admin': {'all': True},
            'manager': {'apps': ['sales', 'customers', 'point_of_sale', 'invoices', 'employees', 'inventory', 'dashboard', 'reports']},
            'salesman': {'apps': ['sales', 'customers', 'point_of_sale', 'invoices', 'employees', 'inventory', 'dashboard']},  # no reports
        }

        for role, setup in config.items():
            group, created = Group.objects.get_or_create(name=role)
            group.permissions.clear()

            if setup.get('all'):
                perms = Permission.objects.all()
            else:
                perms = Permission.objects.filter(content_type__app_label__in=setup['apps'])

            group.permissions.set(perms)
            self.stdout.write(self.style.SUCCESS(f"{role}: {perms.count()} permissions assigned"))
