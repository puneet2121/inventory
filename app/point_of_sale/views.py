from django.shortcuts import render, redirect
from django.db import transaction
from .models import SalesOrder, OrderItem
from app.inventory.models import Product
from app.customers.models import Customer
from django.http import JsonResponse


def get_customer_price(request, customer_id):
    try:
        customer = Customer.objects.get(id=customer_id)
        price_list = {}
        products = Product.objects.all()
        if customer.customer_type == 'A':
            for product in products:
                price_list[product.id] = product.price_A
        elif customer.customer_type == 'B':
            for product in products:
                price_list[product.id] = product.price_B
        else:
            for product in products:
                price_list[product.id] = product.price
        print(price_list)
        return JsonResponse(price_list)
    except Customer.DoesNotExist:
        return JsonResponse({'error': 'Customer not found'}, status=404)


def get_product_price(request, product_id):
    product = Product.objects.get(id=product_id)
    product_price = product.price
    print(product_price)
    return JsonResponse({'product_id': product.id, 'price': product_price})


def create_sales_order(request):
    if request.method == 'POST':
        customer_name = request.POST.get('customer_name', 'Walk-in Customer')
        customer_id = request.POST.get('customer')
        payment_status = request.POST.get('payment_status', 'unpaid')
        paid_amount = float(request.POST.get('paid_amount', 0))
        products = zip(
            request.POST.getlist('product_type'),
            request.POST.getlist('product'),
            request.POST.getlist('custom_product_name'),
            request.POST.getlist('quantity'),
            request.POST.getlist('price')
        )

        try:
            with transaction.atomic():
                sales_order = SalesOrder.objects.create(
                    customer_name=customer_name,
                    payment_status=payment_status,
                    paid_amount=paid_amount,
                )

                for product_type, product_id, custom_name, quantity, price in products:
                    if product_type == 'inventory' and product_id:
                        product = Product.objects.get(id=product_id)
                        OrderItem.objects.create(
                            sales_order=sales_order,
                            product=product,
                            quantity=int(quantity),
                            price=float(price),
                        )
                    elif product_type == 'custom':
                        OrderItem.objects.create(
                            sales_order=sales_order,
                            product_name=custom_name,
                            quantity=int(quantity),
                            price=float(price),
                        )

                sales_order.calculate_total_price()

            return redirect('sales_order_success', order_id=sales_order.id)

        except Exception as e:
            return render(request, 'point_of_sale/create_sales_order.html', {'error': str(e)})

    products = Product.objects.all()
    customers = Customer.objects.all()
    return render(request, 'point_of_sale/create_sales_order.html', {'products': products, 'customers': customers})
