from django.shortcuts import render
from django.utils import timezone
from datetime import timedelta, datetime
from django.contrib.auth.decorators import login_required, permission_required
from django.db.models import Sum, Count, Q
from django.http import JsonResponse
import json
from decimal import Decimal
from app.point_of_sale.models import SalesOrder, OrderItem
from app.inventory.models import Product, Inventory, Category


class DecimalEncoder(json.JSONEncoder):
    """Custom JSON encoder to handle Decimal objects"""
    def default(self, obj):
        if isinstance(obj, Decimal):
            return float(obj)
        return super().default(obj)


# def convert_decimal_to_float(obj):
#     """Convert Decimal objects to float for JSON serialization"""
#     if isinstance(obj, Decimal):
#         return float(obj)
#     elif isinstance(obj, dict):
#         return {key: convert_decimal_to_float(value) for key, value in obj.items()}
#     elif isinstance(obj, list):
#         return [convert_decimal_to_float(item) for item in obj]
#     elif isinstance(obj, tuple):
#         return tuple(convert_decimal_to_float(item) for item in obj)
#     else:
#         return obj


@login_required(login_url='/authentication/login/')
@permission_required('point_of_sale.view_reports', login_url='/authentication/login/', raise_exception=True)
def sales_trend_api(request, period):
    """API endpoint for sales trend data"""
    today = timezone.now().date()
    
    if period == 'week':
        # Last 7 days
        labels = []
        values = []
        for i in range(7):
            date = today - timedelta(days=i)
            orders_for_date = SalesOrder.objects.filter(
                created_at__date=date,
                status='completed'
            )
            order_items_for_date = OrderItem.objects.filter(sales_order__in=orders_for_date)
            daily_sales = sum(item.quantity * item.price for item in order_items_for_date)
            labels.insert(0, date.strftime('%b %d'))
            values.insert(0, float(daily_sales))
    
    elif period == 'month':
        # Last 30 days
        labels = []
        values = []
        for i in range(30):
            date = today - timedelta(days=i)
            orders_for_date = SalesOrder.objects.filter(
                created_at__date=date,
                status='completed'
            )
            order_items_for_date = OrderItem.objects.filter(sales_order__in=orders_for_date)
            daily_sales = sum(item.quantity * item.price for item in order_items_for_date)
            labels.insert(0, date.strftime('%b %d'))
            values.insert(0, float(daily_sales))
    
    elif period == 'year':
        # Last 12 months
        labels = []
        values = []
        for i in range(12):
            month_start_date = today.replace(day=1) - timedelta(days=30*i)
            month_start = timezone.make_aware(datetime.combine(month_start_date, datetime.min.time()))
            month_end = timezone.make_aware(datetime.combine(month_start_date + timedelta(days=30), datetime.min.time()))
            orders_month = SalesOrder.objects.filter(
                created_at__gte=month_start,
                created_at__lt=month_end,
                status='completed'
            )
            order_items_month = OrderItem.objects.filter(sales_order__in=orders_month)
            monthly_sales = sum(item.quantity * item.price for item in order_items_month)
            labels.insert(0, month_start.strftime('%b %Y'))
            values.insert(0, float(monthly_sales))
    
    else:
        # Default to week
        labels = []
        values = []
        for i in range(7):
            date = today - timedelta(days=i)
            orders_for_date = SalesOrder.objects.filter(
                created_at__date=date,
                status='completed'
            )
            order_items_for_date = OrderItem.objects.filter(sales_order__in=orders_for_date)
            daily_sales = sum(item.quantity * item.price for item in order_items_for_date)
            labels.insert(0, date.strftime('%b %d'))
            values.insert(0, float(daily_sales))
    
    return JsonResponse({
        'labels': labels,
        'values': values
    })


@login_required(login_url='/authentication/login/')
@permission_required('point_of_sale.view_reports', login_url='/authentication/login/', raise_exception=True)
def dashboard_view(request):
    today = timezone.now().date()
    yesterday = today - timedelta(days=1)
    this_month = today.replace(day=1)
    last_month = (this_month - timedelta(days=1)).replace(day=1)
    
    # Optimized: Single query for all sales data with aggregation
    from django.db.models import Sum, F, Q, Count
    
    # Get all sales data in one query with date filtering
    sales_data = OrderItem.objects.filter(
        sales_order__status='completed'
    ).select_related('sales_order').values(
        'sales_order__created_at__date'
    ).annotate(
        daily_sales=Sum(F('quantity') * F('price'))
    ).filter(
        sales_order__created_at__date__gte=yesterday - timedelta(days=6)
    ).order_by('sales_order__created_at__date')
    
    # Create a lookup dictionary for quick access
    sales_lookup = {item['sales_order__created_at__date']: float(item['daily_sales']) for item in sales_data}
    
    # Today's and Yesterday's Sales
    total_sales_today = sales_lookup.get(today, 0.0)
    total_sales_yesterday = sales_lookup.get(yesterday, 0.0)
    
    # Calculate trends
    if total_sales_yesterday > 0:
        today_sales_trend = ((total_sales_today - total_sales_yesterday) / total_sales_yesterday) * 100
    else:
        today_sales_trend = 100 if total_sales_today > 0 else 0
    
    # Monthly Sales - use the same aggregated data
    monthly_sales = OrderItem.objects.filter(
        sales_order__status='completed',
        sales_order__created_at__gte=this_month
    ).aggregate(
        total=Sum(F('quantity') * F('price'))
    )['total'] or 0.0
    
    last_month_sales = OrderItem.objects.filter(
        sales_order__status='completed',
        sales_order__created_at__gte=last_month,
        sales_order__created_at__lt=this_month
    ).aggregate(
        total=Sum(F('quantity') * F('price'))
    )['total'] or 0.0
    
    # Calculate monthly trend
    if last_month_sales > 0:
        monthly_sales_trend = ((monthly_sales - last_month_sales) / last_month_sales) * 100
    else:
        monthly_sales_trend = 100 if monthly_sales > 0 else 0
    
    # Total Orders - single count query
    total_orders = SalesOrder.objects.filter(status='completed').count()
    orders_today_count = SalesOrder.objects.filter(
        created_at__date=today, 
        status='completed'
    ).count()
    
    # Low Stock Items - optimized query
    low_stock_items = Inventory.objects.filter(quantity__lte=5).select_related('product')
    low_stock_count = low_stock_items.count()
    
    # Expiring Soon - optimized with single query
    cutoff_date = today + timedelta(days=90)
    expiring_products = Product.objects.filter(
        expiry_date__isnull=False, 
        expiry_date__lte=cutoff_date
    ).select_related('category')
    
    # Get inventory data in one query
    expiring_inventories = Inventory.objects.filter(
        product__in=expiring_products
    ).select_related('product', 'product__category')
    
    # Create inventory lookup
    inv_map = {inv.product_id: inv for inv in expiring_inventories}
    
    expiring_soon_items = []
    for product in expiring_products:
        days_left = (product.expiry_date - today).days if product.expiry_date else None
        expiring_soon_items.append({
            'product': product,
            'inventory': inv_map.get(product.id),
            'days_left': days_left,
        })
    expiring_soon_count = len(expiring_soon_items)
    
    # Recent Orders - optimized with select_related
    recent_orders = SalesOrder.objects.filter(
        status='completed'
    ).select_related('customer').order_by('-created_at')[:10]
    
    # Sales Trend Data - use the pre-fetched data
    sales_trend_data = []
    sales_trend_labels = []
    for i in range(7):
        date = today - timedelta(days=i)
        daily_sales = sales_lookup.get(date, 0.0)
        sales_trend_data.insert(0, daily_sales)
        sales_trend_labels.insert(0, date.strftime('%b %d'))
    
    # If no sales data, provide sample data for demonstration
    if not any(sales_trend_data):
        sales_trend_data = [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0]
        sales_trend_labels = []
        for i in range(6, -1, -1):
            date = today - timedelta(days=i)
            sales_trend_labels.insert(0, date.strftime('%b %d'))

    # Top Selling Products - optimized with aggregation
    thirty_days_ago = today - timedelta(days=30)
    top_products = OrderItem.objects.filter(
        sales_order__status='completed',
        sales_order__created_at__gte=thirty_days_ago
    ).select_related('product', 'product__category').values(
        'product__name', 'product__category__name'
    ).annotate(
        total_quantity=Sum('quantity'),
        total_sales=Sum(F('quantity') * F('price'))
    ).order_by('-total_sales')[:5]
    
    # Top Customers - optimized with aggregation
    top_customers = SalesOrder.objects.filter(
        status='completed',
        created_at__gte=thirty_days_ago
    ).select_related('customer').values(
        'customer__name', 'customer__city'
    ).annotate(
        total_orders=Count('id'),
        total_sales=Sum('cached_total')
    ).order_by('-total_sales')[:5]
    
    # Low Stock Alerts - optimized query
    low_stock_alerts = Inventory.objects.filter(
        quantity__lte=5
    ).select_related('product', 'product__category')[:10]
    
    # Expiring Soon Alerts - optimized query
    expiring_alerts = Product.objects.filter(
        expiry_date__isnull=False,
        expiry_date__lte=cutoff_date
    ).select_related('category')[:10]
    
    context = {
        'total_sales_today': total_sales_today,
        'today_sales_trend': today_sales_trend,
        'monthly_sales': monthly_sales,
        'monthly_sales_trend': monthly_sales_trend,
        'total_orders': total_orders,
        'orders_today_count': orders_today_count,
        'low_stock_count': low_stock_count,
        'expiring_soon_count': expiring_soon_count,
        'recent_orders': recent_orders,
        'sales_trend_data': sales_trend_data,
        'sales_trend_labels': sales_trend_labels,
        'top_products': top_products,
        'top_customers': top_customers,
        'low_stock_alerts': low_stock_alerts,
        'expiring_alerts': expiring_alerts,
    }
    
    return render(request, 'dashboard/dashboard.html', context)
