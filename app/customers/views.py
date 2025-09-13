from django.contrib.auth.decorators import login_required
from django.db.models import Sum
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
from django.http import JsonResponse
from django.db.models import Q


@login_required(login_url='/authentication/login/')
def add_customer(request):
    if request.method == 'POST':
        form = CustomerForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('customers:list_customers')
    else:
        form = CustomerForm()

    return render(request, 'customers/page/add_customer.html', {'form': form})


@require_http_methods(["GET"])
@login_required(login_url='/authentication/login/')
def customers_search(request):
    query = (request.GET.get('query') or '').strip()
    qs = Customer.objects.all()
    if query:
        qs = qs.filter(
            Q(name__icontains=query) |
            Q(contact__icontains=query) |
            Q(shop__icontains=query)
        )
    results = list(qs.order_by('name')[:20].values('id', 'name', 'contact', 'shop', 'city'))
    return JsonResponse({'results': results})


@require_http_methods(["POST"])
@login_required(login_url='/authentication/login/')
def customers_quick_create(request):
    name = (request.POST.get('name') or '').strip()
    contact = (request.POST.get('contact') or '').strip()
    city = (request.POST.get('city') or '').strip() or 'Unknown'
    shop = (request.POST.get('shop') or '').strip() or None
    email = (request.POST.get('email') or '').strip() or None

    if not name:
        return JsonResponse({'error': 'Name is required'}, status=400)

    if contact:
        customer, _ = Customer.objects.get_or_create(
            contact=contact,
            defaults={
                'name': name,
                'city': city,
                'customer_type': 'C',
                'shop': shop,
                'email': email,
            }
        )
        changed = False
        if customer.name != name:
            customer.name = name; changed = True
        if customer.city != city:
            customer.city = city; changed = True
        if (customer.shop or '') != (shop or ''):
            customer.shop = shop; changed = True
        if (customer.email or '') != (email or ''):
            customer.email = email; changed = True
        if changed:
            customer.save()
    else:
        customer = Customer.objects.create(
            name=name,
            city=city,
            customer_type='C',
            contact='',
            shop=shop,
            email=email,
        )

    return JsonResponse({
        'id': customer.id,
        'name': customer.name,
        'contact': customer.contact,
        'shop': customer.shop,
        'city': customer.city,
    })


@require_http_methods(["GET", "POST"])
@login_required(login_url='/authentication/login/')
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


@login_required(login_url='/authentication/login/')
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


@login_required(login_url='/authentication/login/')
def customer_detail(request, pk):
    customer = get_object_or_404(Customer, pk=pk)
    snapshot = getattr(customer, 'financial_snapshot', None)
    ledger_entries = CustomerLedger.objects.filter(customer=customer).order_by('-date')

    context = {
        'customer': customer,
        'snapshot': snapshot,
        'ledger_entries': ledger_entries,
    }
    return render(request, 'customers/page/customer_detail.html', context)


@login_required(login_url='/authentication/login/')
def list_customers(request):
    customers = Customer.objects.all()
    total_customers = customers.count()  # Count the total number of customers
    agg = customers.aggregate(total_debt=Sum('total_debt'))
    total_debt = agg.get('total_debt') or Decimal('0.00')

    context = {
        'customers': customers,
        'total_customers': total_customers,
        'total_debt': total_debt,
    }

    return render(request, 'customers/page/list_customers.html', context)


@login_required(login_url='/authentication/login/')
def customers_with_debt(request):
    customers = Customer.objects.filter(total_debt__gt=0)
    return render(request, 'customers/page/customers_with_debt.html', {'customers': customers})


"""
Note: Snapshot updates are handled via customers/signals.py using CustomerLedger.
The redundant receiver previously defined here has been removed to prevent drift
and model attribute mismatches.
"""
