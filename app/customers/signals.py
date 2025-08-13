# customers/signals.py
from django.db import models
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from decimal import Decimal
from .models import CustomerLedger, CustomerFinancialSnapshot
from app.point_of_sale.models import Invoice
from app.point_of_sale.models import Payment


# ---- Helper to update snapshot ----
def update_snapshot(customer):
    ledger_entries = CustomerLedger.objects.filter(customer=customer)

    total_sales = ledger_entries.filter(type='debit').aggregate(total=models.Sum('amount'))['total'] or Decimal('0.00')
    total_payments = ledger_entries.filter(type='credit').aggregate(total=models.Sum('amount'))['total'] or Decimal('0.00')
    total_refunds = ledger_entries.filter(description__icontains='refund').aggregate(total=models.Sum('amount'))['total'] or Decimal('0.00')
    total_debt = total_sales - total_payments

    snapshot, created = CustomerFinancialSnapshot.objects.get_or_create(customer=customer)
    snapshot.total_sales = total_sales
    snapshot.total_payments = total_payments
    snapshot.total_refunds = total_refunds
    snapshot.total_debt = total_debt
    snapshot.save()


# ---- When an Invoice is created ----
@receiver(post_save, sender=Invoice)
def create_ledger_for_invoice(sender, instance, created, **kwargs):
    if created:
        CustomerLedger.objects.create(
            customer=instance.sales_order.customer,
            amount=instance.total_invoice_amount,
            type='debit',  # Debit means customer owes money
            description=f"Invoice #{instance.id}",
            reference=str(instance.id)
        )
        update_snapshot(instance.sales_order.customer)


# ---- When a Payment is created ----
@receiver(post_save, sender=Payment)
def create_ledger_for_payment(sender, instance, created, **kwargs):
    if created:
        ledger_type = 'credit' if instance.type == 'payment' else 'debit'  # Refunds can be debit or credit depending on logic
        desc = "Payment" if instance.type == 'payment' else "Refund"

        CustomerLedger.objects.create(
            customer=instance.invoice.sales_order.customer,
            amount=instance.amount,
            type=ledger_type,
            description=f"{desc} for Invoice #{instance.invoice.id}",
            reference=str(instance.id)
        )
        update_snapshot(instance.invoice.sales_order.customer)


# ---- If an entry is deleted, recalc snapshot ----
@receiver(post_delete, sender=CustomerLedger)
def recalc_on_delete(sender, instance, **kwargs):
    update_snapshot(instance.customer)
