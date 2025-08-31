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
from django.db import transaction
from django.db import models

from .models import SalesOrder, OrderItem, Invoice, Payment
from .forms import SalesOrderForm, OrderItemForm, PaymentForm, RefundForm
from django.db import transaction

from ..customers.models import Customer
from ..inventory.models import Product
from ..employee.models import EmployeeProfile
from app.core.models import Company

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
        sales_order_form = SalesOrderForm(instance=sales_order)

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
                        # Auto-invoice and full payment for retail companies
                        try:
                            tenant_id = getattr(getattr(request.user, 'employee_profile', None), 'tenant_id', None)
                            company = Company.objects.filter(id=tenant_id).first()
                            if company and company.company_type == 'retail' and not hasattr(sales_order, 'invoice'):
                                invoice = Invoice.objects.create(
                                    sales_order=sales_order,
                                    total_invoice_amount=sales_order.cached_total,
                                    created_by=request.user,
                                )
                                # Record full payment (default to cash)
                                Payment.objects.create(
                                    invoice=invoice,
                                    amount=invoice.total_invoice_amount,
                                    payment_method='cash',
                                    received_by=request.user,
                                )
                                invoice.update_cached_paid_amount()
                        except Exception as e:
                            # Do not block order creation if auto-invoice fails; log message for now
                            messages.warning(request, f"Order created, but auto-invoice/payment failed: {str(e)}")
                        messages.success(request, f"Sales order {sales_order.order_number} created and inventory updated successfully!")
                        return redirect('point_of_sale:sales_order_list')
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
            messages.error(request, "Invalid sales order input.")
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
            # Update customer debt when invoice is generated
            if sales_order.customer and hasattr(sales_order.customer, 'total_debt'):
                sales_order.customer.total_debt += sales_order.cached_total
                sales_order.customer.save()

            invoice = Invoice.objects.create(
                sales_order=sales_order,
                total_invoice_amount=sales_order.cached_total,
            )

            messages.success(request, f"Sales order {sales_order.order_number} has been converted to invoice {invoice.invoice_number}! Customer debt updated.")
    else:
        messages.info(request, f"Sales order {sales_order.order_number} is already converted to an invoice.")

    return redirect('point_of_sale:invoice_list')


# Invoice Views
def invoice_list(request):
    invoices = Invoice.objects.all().select_related('sales_order', 'sales_order__customer')
    
    # Calculate payment and refund totals for each invoice
    for invoice in invoices:
        total_paid = invoice.payments.filter(type='payment').aggregate(
            total=models.Sum('amount')
        )['total'] or 0
        
        total_refunded = invoice.payments.filter(type='refund').aggregate(
            total=models.Sum('amount')
        )['total'] or 0
        
        invoice.net_paid = total_paid - total_refunded
        invoice.total_paid = total_paid
        invoice.total_refunded = total_refunded
        invoice.has_refunds = total_refunded > 0
    
    return render(request, 'point_of_sale/invoice_list.html', {'invoices': invoices})


def invoice_print(request, pk):
    invoice = get_object_or_404(Invoice, pk=pk)
    return render(request, 'point_of_sale/invoice_print.html', {'invoice': invoice})

@transaction.atomic
def process_refund(request, invoice_id):
    invoice = get_object_or_404(Invoice, id=invoice_id)
    customer = invoice.sales_order.customer

    # Check if invoice has been paid
    if invoice.payment_status == 'unpaid':
        messages.error(request, "Cannot process refund for unpaid invoice.")
        return redirect('point_of_sale:invoice_detail', invoice_id=invoice.id)

    # Calculate available amount for refund
    total_paid = invoice.payments.filter(type='payment').aggregate(
        total=models.Sum('amount')
    )['total'] or 0
    
    total_refunded = invoice.payments.filter(type='refund').aggregate(
        total=models.Sum('amount')
    )['total'] or 0
    
    available_for_refund = total_paid - total_refunded

    if available_for_refund <= 0:
        messages.error(request, "No amount available for refund.")
        return redirect('point_of_sale:invoice_detail', invoice_id=invoice.id)

    if request.method == 'POST':
        print("POST data received:", request.POST)
        form = RefundForm(request.POST, invoice=invoice)
        print("Form created with data:", form.data)
        print("Form is bound:", form.is_bound)
        
        if form.is_valid():
            print("Form is valid")
            try:
                refund = form.save(commit=False)
                refund.invoice = invoice
                refund.type = 'refund'
                refund.received_by = request.user
                print("About to save refund:", refund)
                refund.save()
                print("Refund saved successfully")

                # Update invoice payment state
                invoice.update_cached_paid_amount()

                # Update customer account balance (increase debt for refund)
                if customer:
                    customer.total_debt += refund.amount
                    customer.save()

                messages.success(request, f"Refund of ₹{refund.amount} processed successfully.")
                return redirect('point_of_sale:invoice_detail', invoice_id=invoice.id)
            except Exception as e:
                print("Exception occurred:", str(e))
                import traceback
                traceback.print_exc()
                messages.error(request, f"Error processing refund: {str(e)}")
        else:
            print("Form is not valid")
            print("Form errors:", form.errors)
            print("Form data:", request.POST)
            for field, errors in form.errors.items():
                print(f"Field {field} errors: {errors}")
            messages.error(request, "Invalid refund input. Please check the form and try again.")
    else:
        print("GET request - creating new form")
        form = RefundForm(invoice=invoice)
        print("Form fields:", list(form.fields.keys()))
        for field_name, field in form.fields.items():
            print(f"Field {field_name}: {field}")

    return render(request, 'point_of_sale/refund_form.html', {
        'invoice': invoice,
        'form': form,
        'total_paid': total_paid,
        'total_refunded': total_refunded,
        'available_for_refund': available_for_refund,
    })


def invoice_detail(request, invoice_id):
    invoice = get_object_or_404(Invoice, id=invoice_id)
    
    # Calculate payment and refund totals
    total_paid = invoice.payments.filter(type='payment').aggregate(
        total=models.Sum('amount')
    )['total'] or 0
    
    total_refunded = invoice.payments.filter(type='refund').aggregate(
        total=models.Sum('amount')
    )['total'] or 0
    
    available_for_refund = total_paid - total_refunded
    
    # Get payment and refund history
    payments = invoice.payments.filter(type='payment').order_by('-date')
    refunds = invoice.payments.filter(type='refund').order_by('-date')
    
    return render(request, 'point_of_sale/invoice_detail.html', {
        'invoice': invoice,
        'total_paid': total_paid,
        'total_refunded': total_refunded,
        'available_for_refund': available_for_refund,
        'payments': payments,
        'refunds': refunds,
    })


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
            payment.type = 'payment'
            payment.received_by = request.user
            payment.save()

            # Update invoice payment state
            invoice.update_cached_paid_amount()

            # Update customer account balance
            if customer:
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


@login_required(login_url='/authentication/login/')
@require_http_methods(["GET", "POST"])
@transaction.atomic
def quick_checkout(request):
    """
    Fast POS endpoint:
    - POST JSON payload with items and payment_method
    - Creates SalesOrder -> finalizes (adjust inventory) -> creates Invoice -> records full payment
    - Returns JSON with invoice_number and totals

    Expected JSON body:
    {
      "location": "Main Store",
      "items": [ {"product_id": 1, "quantity": 2, "price": 199.99}, ... ],
      "payment_method": "cash|card|upi"
    }
    """
    if request.method == 'GET':
        # Simple UI to test quick checkout; embed product catalog for selection/scanning
        products = Product.objects.all().values('id', 'name', 'price', 'barcode', 'model')
        # Convert Decimal to float for JSON serialization
        plist = []
        for p in products:
            d = dict(p)
            if isinstance(d.get('price'), Decimal):
                d['price'] = float(d['price'])
            plist.append(d)
        return render(request, 'point_of_sale/quick_checkout.html', { 'products': json.dumps(plist) })

    try:
        data = json.loads(request.body.decode('utf-8'))
    except Exception:
        return JsonResponse({"error": "Invalid JSON"}, status=400)

    items = data.get('items', [])
    payment_method = data.get('payment_method', 'cash')
    location = data.get('location', 'Main Store')

    if not items:
        return JsonResponse({"error": "No items provided"}, status=400)

    # Ensure a Walk-in Customer with static code exists (customer_id = "001" via contact field)
    walkin_customer = Customer.objects.filter(name='Walk-in Customer', city='Walk-in', contact='001').first()
    if not walkin_customer:
        walkin_customer = Customer.objects.create(
            name='Walk-in Customer',
            city='Walk-in',
            customer_type='C',
            contact='001',  # static code
            email='',
            shop=''
        )

    # Create draft order
    sales_order = SalesOrder.objects.create(
        customer=walkin_customer,
        customer_type='walk_in',
        employee=EmployeeProfile.objects.filter(user=request.user).first(),
        location=location,
        status='draft'
    )

    # Add items
    for it in items:
        try:
            product = Product.objects.get(pk=it['product_id'])
            qty = int(it['quantity'])
            price = Decimal(str(it.get('price', product.price)))
        except Exception:
            transaction.set_rollback(True)
            return JsonResponse({"error": "Invalid item in payload"}, status=400)
        OrderItem.objects.create(sales_order=sales_order, product=product, quantity=qty, price=price)

    # Finalize order: updates cached_total and deducts inventory + logs StockMovement
    try:
        sales_order.finalize_order()
    except ValidationError as e:
        transaction.set_rollback(True)
        return JsonResponse({"error": str(e)}, status=400)

    # Create invoice, mark paid, and record payment
    invoice = Invoice.objects.create(
        sales_order=sales_order,
        total_invoice_amount=sales_order.cached_total,
        created_by=request.user,
        payment_status='paid'
    )
    Payment.objects.create(
        invoice=invoice,
        amount=sales_order.cached_total,
        payment_method=payment_method,
        received_by=request.user
    )
    invoice.update_cached_paid_amount()

    return JsonResponse({
        "order_number": sales_order.order_number,
        "invoice_number": invoice.invoice_number,
        "total": float(sales_order.cached_total),
        "status": "paid"
    })
