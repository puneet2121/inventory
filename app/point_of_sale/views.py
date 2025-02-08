import json

from django.contrib.auth.decorators import login_required
from django.db.models import Sum
from django.forms import inlineformset_factory
from django.http import JsonResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from django.views.decorators.http import require_http_methods

from .models import SalesOrder, OrderItem, Invoice, Payment, EmployeeProfile
from .forms import SalesOrderForm, OrderItemForm
from django.db import transaction

from ..customers.models import Customer
from ..inventory.models import Product


# Sales Order Views
@login_required(login_url='/authentication/login/')
def create_sales_order(request):
    OrderItemFormSet = inlineformset_factory(
        SalesOrder, OrderItem, form=OrderItemForm, extra=1, can_delete=True
    )
    products = Product.objects.all()  # Fetch products to pass to the template
    customers = Customer.objects.all()
    employees = EmployeeProfile.objects.all()

    if request.method == "POST":
        sales_order_form = SalesOrderForm(request.POST)
        formset = OrderItemFormSet(request.POST, prefix="items")

        if sales_order_form.is_valid() and formset.is_valid():
            try:
                with transaction.atomic():
                    sales_order = sales_order_form.save()
                    order_items = formset.save(commit=False)
                    for item in order_items:
                        item.sales_order = sales_order
                        item.save()

                    # Save any remaining deleted forms from the formset
                    formset.save_m2m()

                    # invoice = Invoice.objects.create(
                    #     sales_order=sales_order,
                    #     is_paid=(sales_order.payment_status == 'paid')
                    # )
                    #
                    # # If payment is marked as paid, create a Payment record
                    # if sales_order.payment_status == 'paid':
                    #     Payment.objects.create(
                    #         invoice=invoice,
                    #         payment_method='cash'  # Default payment method, can be dynamic
                    #     )

                    return redirect('point_of_sale:create_sales_order')
            except Exception as e:
                formset.non_form_errors = [str(e)]  # Add error to non-form errors
        else:
            if not sales_order_form.is_valid():
                sales_order_form.add_error(None, "Sales order form is invalid.")
            if not formset.is_valid():
                for form in formset:
                    if not form.is_valid():
                        form.add_error(None, "Order item form is invalid.")
    else:
        sales_order_form = SalesOrderForm()
        formset = OrderItemFormSet(prefix="items")

    return render(request, 'point_of_sale/sales_order_form.html', {
        'sales_order_form': sales_order_form,
        'formset': formset,
        'products': products,  # Pass products to the template
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
        Invoice.objects.create(sales_order=sales_order, invoice_id=f"INV-{sales_order.id}")
    return redirect('invoice_list')


# Invoice Views
def invoice_list(request):
    invoices = Invoice.objects.all()
    return render(request, 'point_of_sale/invoice_list.html', {'invoices': invoices})


def invoice_detail(request, invoice_id):
    invoice = get_object_or_404(Invoice, id=invoice_id)
    return render(request, 'point_of_sale/invoice_detail.html', {'invoice': invoice})


# Payment Views
def add_payment(request, invoice_id):
    invoice = get_object_or_404(Invoice, id=invoice_id)
    if request.method == 'POST':
        form = PaymentForm(request.POST)
        if form.is_valid():
            payment = form.save(commit=False)
            payment.invoice = invoice
            payment.save()
            return redirect('invoice_detail', invoice_id)
    else:
        form = PaymentForm()
    return render(request, 'point_of_sale/payment_form.html', {'invoice': invoice, 'form': form})


def product_by_barcode(request, barcode):
    print('jijijji')
    try:
        product = Product.objects.get(barcode=barcode)
        print('jee')
        return JsonResponse({
            'id': product.id,
            'name': product.name,
            'price': float(product.price),
            'barcode': product.barcode
        })
    except Product.DoesNotExist:
        return JsonResponse({'error': 'Product not found'}, status=404)


@require_http_methods(["GET", "POST"])
@login_required(login_url='/authentication/login/')
def quick_checkout(request):
    if request.method == 'POST':
        try:
            with transaction.atomic():
                customer, _ = Customer.objects.get_or_create(
                    name="Walk-In",
                    customer_type='C'
                )
                print('this is the req id', request.user.id)
                # Create sales order
                sales_order = SalesOrder.objects.create(
                    customer=customer,
                    employee=request.user.employee_profile
                )

                # Add order items
                cart_data = json.loads(request.POST.get('cart_data', '[]'))
                for item in cart_data:
                    product = Product.objects.get(id=item['product']['id'])
                    OrderItem.objects.create(
                        sales_order=sales_order,
                        product=product,
                        quantity=item['quantity'],
                        price=product.price
                    )

                # Create invoice
                total_amount = sum(
                    item['product']['price'] * item['quantity']
                    for item in cart_data
                )

                invoice = Invoice.objects.create(
                    sales_order=sales_order,
                    total_amount=total_amount,
                    is_paid=(request.POST.get('payment_status') == 'paid')
                )

                # # Create payment if paid
                # if invoice.is_paid:
                #     Payment.objects.create(
                #         invoice=invoice,
                #         amount=total_amount,
                #         payment_method='cash'
                #     )

                return redirect('point_of_sale:create_sales_order')

        except Exception as e:
            return render(request, 'error.html', {'error': str(e)})

    return render(request, 'point_of_sale/quick_checkout.html')
