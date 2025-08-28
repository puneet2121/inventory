from django.db.models import Sum, Q
from django.shortcuts import render, get_object_or_404, redirect
from app.customers.models import Customer, CustomerLedger
from app.point_of_sale.models import Invoice
from app.customers.forms import CustomerForm
from django.db.models.signals import post_save
from django.dispatch import receiver
from app.point_of_sale.models import Payment
from .models import CustomerFinancialSnapshot
from decimal import Decimal
from django.db.models import Prefetch
from django.core.paginator import Paginator
from datetime import datetime, time, date as date_class
from django.contrib import messages
from django.views.decorators.http import require_http_methods
import io
import pandas as pd
from django.db import connection, reset_queries
import time


def add_customer(request):
    if request.method == 'POST':
        form = CustomerForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('customers:list_customers')
    else:
        form = CustomerForm()

    print(len(connection.queries), "queries executed")
    for q in connection.queries:
        print(q["sql"], q["time"])
    return render(request, 'customers/page/add_customer.html', {'form': form})


@require_http_methods(["GET", "POST"])
def import_customers(request):
    """
    Bulk import customers from CSV or Excel.
    Expected columns (case-insensitive): name, city, customer_type, contact, email, shop, total_debt
    Only 'name', 'city', 'customer_type', 'contact' are recommended; others optional.
    Matching strategy: if 'contact' provided, upsert by contact; else upsert by (name, city).
    """
    if request.method == 'GET':
        return render(request, 'customers/page/import_customers.html')

    upload = request.FILES.get('file')
    if not upload:
        messages.error(request, 'Please select a CSV or Excel file to upload.')
        return redirect('customers:import_customers')

    filename = upload.name.lower()
    try:
        content = upload.read()
        buf = io.BytesIO(content)
        if filename.endswith('.csv'):
            df = pd.read_csv(io.BytesIO(content))
        elif filename.endswith('.xlsx') or filename.endswith('.xls'):
            df = pd.read_excel(buf)
        else:
            messages.error(request, 'Unsupported file type. Please upload .csv or .xlsx')
            return redirect('customers:import_customers')
    except Exception as e:
        messages.error(request, f'Failed to read file: {e}')
        return redirect('customers:import_customers')

    # Normalize columns
    df.columns = [str(c).strip().lower() for c in df.columns]
    required_any = {'name', 'city'}
    if not required_any.issubset(set(df.columns)):
        messages.error(request, 'Missing required columns. Need at least: name, city. Optional: customer_type, contact, email, shop, total_debt')
        return redirect('customers:import_customers')

    created, updated, skipped = 0, 0, 0
    for _, row in df.iterrows():
        name = str(row.get('name') or '').strip()
        city = str(row.get('city') or '').strip()
        if not name or not city:
            skipped += 1
            continue

        customer_type = str(row.get('customer_type') or 'C').strip().upper()[:1]
        if customer_type not in ['A','B','C']:
            customer_type = 'C'
        contact = str(row.get('contact') or '').strip()
        email = str(row.get('email') or '').strip() or None
        shop = str(row.get('shop') or '').strip() or None
        total_debt = row.get('total_debt')
        try:
            if pd.isna(total_debt):
                total_debt = Decimal('0.00')
            else:
                total_debt = Decimal(str(total_debt))
        except Exception:
            total_debt = Decimal('0.00')

        # Upsert strategy
        try:
            if contact:
                obj, created_flag = Customer.objects.get_or_create(
                    contact=contact,
                    defaults={
                        'name': name,
                        'city': city,
                        'customer_type': customer_type,
                        'email': email,
                        'shop': shop,
                        'total_debt': total_debt,
                    }
                )
            else:
                obj, created_flag = Customer.objects.get_or_create(
                    name=name,
                    city=city,
                    defaults={
                        'customer_type': customer_type,
                        'contact': contact,
                        'email': email,
                        'shop': shop,
                        'total_debt': total_debt,
                    }
                )

            if created_flag:
                created += 1
            else:
                # Update existing
                changed = False
                if obj.name != name:
                    obj.name = name; changed = True
                if obj.city != city:
                    obj.city = city; changed = True
                if obj.customer_type != customer_type:
                    obj.customer_type = customer_type; changed = True
                if (obj.contact or '') != contact:
                    obj.contact = contact or obj.contact; changed = True
                if (obj.email or '') != (email or ''):
                    obj.email = email; changed = True
                if (obj.shop or '') != (shop or ''):
                    obj.shop = shop; changed = True
                if obj.total_debt != total_debt:
                    obj.total_debt = total_debt; changed = True
                if changed:
                    obj.save()
                    updated += 1
                else:
                    skipped += 1
        except Exception as e:
            skipped += 1

    messages.success(request, f'Import finished. Created: {created}, Updated: {updated}, Skipped: {skipped}.')
    return redirect('customers:list_customers')


def edit_customer(request, pk):
    customer = get_object_or_404(Customer, pk=pk)

    if request.method == 'POST':
        form = CustomerForm(request.POST, instance=customer)
        if form.is_valid():
            form.save()
            return redirect('customers:list_customers')
    else:
        form = CustomerForm(instance=customer)

    return render(request, 'customers/page/add_customer.html', {'form': form, 'edit_mode': True})


def customer_detail(request, pk):
    customer = get_object_or_404(Customer, pk=pk)
    snapshot = getattr(customer, 'financial_snapshot', None)
    
    # Optimized: Add pagination and select_related for ledger entries
    ledger_entries = CustomerLedger.objects.filter(
        customer=customer
    ).select_related('invoice').order_by('-date')
    
    # Add pagination to prevent loading too many records
    paginator = Paginator(ledger_entries, 50)  # Show 50 entries per page
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)

    context = {
        'customer': customer,
        'snapshot': snapshot,
        'ledger_entries': page_obj,
    }
    return render(request, 'customers/page/customer_detail.html', context)


def list_customers(request):
    start = time.time()
    
    # Optimized: Use select_related and add search/filtering
    customers = Customer.objects.select_related().all()
    
    # Add search functionality
    search_query = request.GET.get('search', '')
    if search_query:
        customers = customers.filter(
            Q(name__icontains=search_query) |
            Q(city__icontains=search_query) |
            Q(contact__icontains=search_query)
        )
    
    # Add pagination to prevent loading all customers at once
    paginator = Paginator(customers, 100)  # Show 100 customers per page
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)
    
    # Optimized: Use database aggregation instead of fetching all records
    total_customers = customers.count()
    total_debt = customers.aggregate(
        total_debt=Sum('total_debt')
    ).get('total_debt') or Decimal('0.00')

    context = {
        'customers': page_obj,
        'total_customers': total_customers,
        'total_debt': total_debt,
        'search_query': search_query,
    }

    end = time.time()
    print(f"Query executed in {end - start}s")
    start = time.time()
    response = render(request, 'customers/page/list_customers.html', context)
    end = time.time()
    print(f"View + template render time: {end - start}s")
    return response


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

    # payments = customer.direct_payments.all()  # Advance payments (if allowed)
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
