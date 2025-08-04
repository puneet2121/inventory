from django.shortcuts import render
from django.utils import timezone
from datetime import timedelta
from django.contrib.auth.decorators import login_required
from app.point_of_sale.models import SalesOrder, OrderItem, Product
from app.inventory.models import Product, Inventory


@login_required(login_url='/authentication/login/')
def dashboard_view(request):
    # Sales for today
    today = timezone.now().date()
    orders_today = SalesOrder.objects.filter(created_at__date=today)
    order_items_today = OrderItem.objects.filter(sales_order__in=orders_today)
    total_sales_today = sum(item.quantity * item.price for item in order_items_today)

    # Sales for the last week
    seven_days_ago = timezone.now() - timedelta(days=7)
    orders_last_week = SalesOrder.objects.filter(created_at__gte=seven_days_ago)
    order_items_last_week = OrderItem.objects.filter(sales_order__in=orders_last_week)
    total_sales_last_week = sum(item.quantity * item.price for item in order_items_last_week)

    # Sales for the current week
    start_of_week = timezone.now() - timedelta(days=timezone.now().weekday())
    orders_this_week = SalesOrder.objects.filter(created_at__gte=start_of_week)
    order_items_this_week = OrderItem.objects.filter(sales_order__in=orders_this_week)
    total_sales_this_week = sum(item.quantity * item.price for item in order_items_this_week)

    # Low inventory products
    low_inventory_products = Inventory.objects.filter(quantity__lte=5)

    return render(
        request,
        'dashboard/index.html',
        {
            'total_sales_today': total_sales_today,
            'total_sales_last_week': total_sales_last_week,
            'total_sales_this_week': total_sales_this_week,
            'low_inventory_products': low_inventory_products,
        }
    )
