import json
from decimal import Decimal

from django.contrib.auth.decorators import login_required
from django.core.exceptions import ValidationError
from django.db.models import Sum
from django.forms import inlineformset_factory
from django.http import JsonResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from django.views.decorators.http import require_http_methods
from django.contrib import messages

from .models import SalesOrder, OrderItem, Invoice, Payment
from .forms import SalesOrderForm, OrderItemForm, PaymentForm
from django.db import transaction

from ..customers.models import Customer
from ..inventory.models import Product
from ..employee.models import EmployeeProfile


# Sales Order Views
@login_required(login_url='/authentication/login/')
def sales_order_list(request):
    """Display list of all sales orders with status and actions"""
    sales_orders = SalesOrder.objects.all().select_related('customer', 'employee').prefetch_related('items__product').order_by('-created_at')
    
    # Add computed fields
    for order in sales_orders:
        order.total_amount = sum(item.quantity * item.price for item in order.items.all())
        order.total_items = sum(item.quantity for item in order.items.all())
        order.has_invoice = hasattr(order, 'invoice')
        order.status_display = order.get_status_display() if hasattr(order, 'get_status_display') else 'Draft'
    
    return render(request, 'point_of_sale/sales_order_list.html', {
        'sales_orders': sales_orders
    })


@login_required(login_url='/authentication/login/')
def sales_order_detail(request, sales_order_id):
    """Display detailed view of a sales order"""
    sales_order = get_object_or_404(SalesOrder, id=sales_order_id)
    order_items = sales_order.items.all().select_related('product')
    
    # Calculate totals
    subtotal = sum(item.quantity * item.price for item in order_items)
    tax = subtotal * 0  # 0% tax for now
    total = subtotal + tax
    
    return render(request, 'point_of_sale/sales_order_detail.html', {
        'sales_order': sales_order,
        'order_items': order_items,
        'subtotal': subtotal,
        'tax': tax,
        'total': total,
        'has_invoice': hasattr(sales_order, 'invoice')
    })


@login_required(login_url='/authentication/login/')
def edit_sales_order(request, sales_order_id):
    """Edit an existing sales order"""
    sales_order = get_object_or_404(SalesOrder, id=sales_order_id)
    
    # Check if order can be edited (not invoiced yet)
    if hasattr(sales_order, 'invoice'):
        messages.error(request, "Cannot edit a sales order that has already been converted to an invoice.")
        return redirect('point_of_sale:sales_order_detail', sales_order_id=sales_order.id)
    
    # Serialize products for JavaScript
    products = Product.objects.all().values('id', 'name', 'price', 'barcode', 'model')
    products_list = []
    for product in products:
        product_dict = dict(product)
        if isinstance(product_dict.get('price'), Decimal):
            product_dict['price'] = float(product_dict['price'])
        products_list.append(product_dict)
    products_json = json.dumps(products_list)
    
    customers = Customer.objects.all()
    employees = EmployeeProfile.objects.all()
    order_items = sales_order.items.all()

    if request.method == "POST":
        sales_order_form = SalesOrderForm(request.POST, instance=sales_order)
        
        if sales_order_form.is_valid():
            try:
                with transaction.atomic():
                    # First, reverse the previous inventory changes by setting status back to draft
                    if sales_order.status == 'completed':
                        # TODO: Add inventory restoration logic here if needed
                        sales_order.status = 'draft'
                        sales_order.save()
                    
                    updated_sales_order = sales_order_form.save()
                    
                    # Delete existing items and recreate them
                    sales_order.items.all().delete()
                    
                    # Process items from the frontend
                    total_forms = int(request.POST.get('items-TOTAL_FORMS', 0))
                    
                    for i in range(total_forms):
                        product_id = request.POST.get(f'items-{i}-product')
                        quantity = request.POST.get(f'items-{i}-quantity')
                        price = request.POST.get(f'items-{i}-price')
                        
                        if product_id and quantity and price:
                            try:
                                product = Product.objects.get(id=product_id)
                                OrderItem.objects.create(
                                    sales_order=updated_sales_order,
                                    product=product,
                                    quantity=int(quantity),
                                    price=float(price)
                                )
                            except (Product.DoesNotExist, ValueError) as e:
                                messages.error(request, f"Error updating item: {str(e)}")
                                continue

                    # Finalize the updated order
                    try:
                        updated_sales_order.finalize_order()
                        messages.success(request, f"Sales order {updated_sales_order.order_number} updated and inventory adjusted successfully!")
                    except ValidationError as e:
                        messages.error(request, f"Error finalizing updated order: {str(e)}")
                        return render(request, 'point_of_sale/edit_sales_order.html', {
                            'sales_order_form': sales_order_form,
                            'sales_order': sales_order,
                            'order_items': order_items,
                            'products': products_json,
                            'customers': customers,
                            'employees': employees
                        })
                    
                    return redirect('point_of_sale:sales_order_detail', sales_order_id=updated_sales_order.id)
                    
            except Exception as e:
                messages.error(request, f"Error updating sales order: {str(e)}")
        else:
            for field, errors in sales_order_form.errors.items():
                for error in errors:
                    messages.error(request, f"{field}: {error}")
    else:
        # Initialize form with existing data
        initial_data = {
            'customer_name': sales_order.customer.name if sales_order.customer and sales_order.customer.city == 'Walk-in' else ''
        }
        sales_order_form = SalesOrderForm(instance=sales_order, initial=initial_data)

    return render(request, 'point_of_sale/edit_sales_order.html', {
        'sales_order_form': sales_order_form,
        'sales_order': sales_order,
        'order_items': order_items,
        'products': products_json,
        'customers': customers,
        'employees': employees
    })


@login_required(login_url='/authentication/login/')
def create_sales_order(request):
    OrderItemFormSet = inlineformset_factory(
        SalesOrder, OrderItem, form=OrderItemForm, extra=1, can_delete=True
    )
    
    # Serialize products for JavaScript
    products = Product.objects.all().values('id', 'name', 'price', 'barcode', 'model')
    # Convert Decimal to float for JSON serialization
    products_list = []
    for product in products:
        product_dict = dict(product)
        if isinstance(product_dict.get('price'), Decimal):
            product_dict['price'] = float(product_dict['price'])
        products_list.append(product_dict)
    products_json = json.dumps(products_list)
    
    customers = Customer.objects.all()
    employees = EmployeeProfile.objects.all()

    if request.method == "POST":
        sales_order_form = SalesOrderForm(request.POST)
        
        # Handle cart data from the frontend
        cart_data = request.POST.get('cart_data')
        if cart_data:
            try:
                cart_items = json.loads(cart_data)
            except json.JSONDecodeError:
                cart_items = []
        else:
            cart_items = []

        if sales_order_form.is_valid():
            try:
                with transaction.atomic():
                    sales_order = sales_order_form.save()
                    
                    # Process items from the frontend
                    total_forms = int(request.POST.get('items-TOTAL_FORMS', 0))
                    for i in range(total_forms):
                        product_id = request.POST.get(f'items-{i}-product')
                        quantity = request.POST.get(f'items-{i}-quantity')
                        price = request.POST.get(f'items-{i}-price')

                        if product_id and quantity and price:
                            try:
                                product = Product.objects.get(id=product_id)
                                qty = int(quantity)
                                unit_price = float(price)

                                OrderItem.objects.create(
                                    sales_order=sales_order,
                                    product=product,
                                    quantity=qty,
                                    price=unit_price
                                )
                            except (Product.DoesNotExist, ValueError) as e:
                                messages.error(request, f"Error adding item: {str(e)}")
                                continue

                    # Finalize the order: update cached_total and decrease inventory
                    try:
                        sales_order.finalize_order()
                        messages.success(request, f"Sales order {sales_order.order_number} created and inventory updated successfully!")
                        return redirect('point_of_sale:sales_order_detail', sales_order_id=sales_order.id)
                    except ValidationError as e:
                        messages.error(request, f"Error finalizing order: {str(e)}")
                        # Delete the sales order if finalization fails
                        sales_order.delete()
                        return render(request, 'point_of_sale/create_sales_order.html', {
                            'sales_order_form': sales_order_form,
                            'products': products_json,
                            'customers': customers,
                            'employees': employees
                        })
                    
            except Exception as e:
                messages.error(request, f"Error creating sales order: {str(e)}")
        else:
            for field, errors in sales_order_form.errors.items():
                for error in errors:
                    messages.error(request, f"{field}: {error}")
    else:
        sales_order_form = SalesOrderForm()

    return render(request, 'point_of_sale/create_sales_order.html', {
        'sales_order_form': sales_order_form,
        'products': products_json,
        'customers': customers,
        'employees': employees
    })


def add_order_items(request, sales_order_id):
    sales_order = get_object_or_404(SalesOrder, id=sales_order_id)
    if request.method == 'POST':
        form = OrderItemForm(request.POST)
        if form.is_valid():
            order_item = form.save(commit=False)
            order_item.sales_order = sales_order
            order_item.save()
            return redirect('add_order_items', sales_order.id)
    else:
        form = OrderItemForm()
    return render(request, 'point_of_sale/sales_order_detail.html', {'sales_order': sales_order, 'form': form})


def convert_to_invoice(request, sales_order_id):
    sales_order = get_object_or_404(SalesOrder, id=sales_order_id)
    if not hasattr(sales_order, 'invoice'):
        with transaction.atomic():
            # Generate a unique invoice number
            last_invoice = Invoice.objects.order_by('-id').first()
            next_number = (last_invoice.id + 1) if last_invoice else 1
            invoice_number = f"INV-{next_number:05d}"

            # Update customer debt when invoice is generated
            if sales_order.customer and hasattr(sales_order.customer, 'total_debt'):
                sales_order.customer.total_debt += sales_order.cached_total
                sales_order.customer.save()
            
            invoice = Invoice.objects.create(
                sales_order=sales_order,
                total_price=sales_order.cached_total,
                invoice_number=invoice_number
            )
            
            messages.success(request, f"Sales order {sales_order.order_number} has been converted to invoice {invoice_number}! Customer debt updated.")
    else:
        messages.info(request, f"Sales order {sales_order.order_number} is already converted to an invoice.")
    
    return redirect('point_of_sale:invoice_list')


# Invoice Views
def invoice_list(request):
    invoices = Invoice.objects.all()
    return render(request, 'point_of_sale/invoice_list.html', {'invoices': invoices})


def invoice_detail(request, invoice_id):
    invoice = get_object_or_404(Invoice, id=invoice_id)
    return render(request, 'point_of_sale/invoice_detail.html', {'invoice': invoice})


# Payment Views
@transaction.atomic
def add_payment(request, invoice_id):
    invoice = get_object_or_404(Invoice, id=invoice_id)
    customer = invoice.sales_order.customer

    if request.method == 'POST':
        form = PaymentForm(request.POST)
        if form.is_valid():
            payment = form.save(commit=False)
            payment.invoice = invoice
            payment.save()

            # Update invoice payment state
            invoice.update_cached_paid_amount()

            # Update customer account balance
            customer.total_debt -= payment.amount
            customer.save()

            messages.success(request, f"Payment of ₹{payment.amount} recorded.")
            return redirect('point_of_sale:invoice_detail', invoice_id=invoice.id)
        else:
            messages.error(request, "Invalid payment input.")
    else:
        form = PaymentForm()

    return render(request, 'point_of_sale/payment_form.html', {
        'invoice': invoice,
        'form': form,
    })

