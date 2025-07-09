from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Customer, CustomerFinancialSnapshot


@receiver(post_save, sender=Customer)
def create_customer_snapshot(sender, instance, created, **kwargs):
    if created:
        CustomerFinancialSnapshot.objects.create(customer=instance)
