from django.db.models import Sum
from django.shortcuts import render, get_object_or_404, redirect
from app.customers.models import Customer
from app.customers.forms import CustomerForm
from django.db.models.signals import post_save
from django.dispatch import receiver
from app.point_of_sale.models import Payment
from .models import CustomerFinancialSnapshot
from decimal import Decimal


def add_customer(request):
    if request.method == 'POST':
        form = CustomerForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('list_customers')
    else:
        form = CustomerForm()
    return render(request, 'customers/page/add_customer.html', {'form': form})


def list_customers(request):
    customers = Customer.objects.all()
    total_customers = customers.count()  # Count the total number of customers
    total_debt = customers.aggregate(total_debt=Sum('total_debt')) or 0
    return render(request, 'customers/page/list_customers.html', {
        'customers': customers,
        'total_customers': total_customers,
        'total_debt': total_debt,
    })


def customers_with_debt(request):
    customers = Customer.objects.filter(debt__gt=0)
    return render(request, 'customers/page/customers_with_debt.html', {'customers': customers})


@receiver(post_save, sender=Payment)
def update_customer_snapshot_on_payment(sender, instance, **kwargs):
    invoice = instance.invoice
    customer = invoice.sales_order.customer

    if not customer:
        return  # Skip walk-in customers or unknown

    snapshot, _ = CustomerFinancialSnapshot.objects.get_or_create(customer=customer)

    # Recalculate everything
    sales_orders = customer.sales_orders.all()
    total_sales = sum(order.cached_total for order in sales_orders)

    payments = customer.direct_payments.all()  # Advance payments (if allowed)
    invoice_payments = Payment.objects.filter(invoice__sales_order__customer=customer)

    total_paid = sum(p.amount for p in invoice_payments if p.type == 'payment')
    total_refunded = sum(p.amount for p in invoice_payments if p.type == 'refund')

    credit_balance = customer.credit_balance if hasattr(customer, 'credit_balance') else Decimal(0)

    snapshot.total_sales = total_sales
    snapshot.total_payments = total_paid
    snapshot.total_refunds = total_refunded
    snapshot.total_debt = total_sales - total_paid + total_refunded
    snapshot.credit_balance = credit_balance
    snapshot.save()
