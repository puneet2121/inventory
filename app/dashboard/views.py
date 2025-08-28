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
    
    # Today's Sales
    orders_today = SalesOrder.objects.filter(created_at__date=today, status='completed')
    order_items_today = OrderItem.objects.filter(sales_order__in=orders_today)
    total_sales_today = sum(item.quantity * item.price for item in order_items_today)
    
    # Yesterday's Sales for comparison
    orders_yesterday = SalesOrder.objects.filter(created_at__date=yesterday, status='completed')
    order_items_yesterday = OrderItem.objects.filter(sales_order__in=orders_yesterday)
    total_sales_yesterday = sum(item.quantity * item.price for item in order_items_yesterday)
    
    # Calculate today's sales trend
    if total_sales_yesterday > 0:
        today_sales_trend = ((total_sales_today - total_sales_yesterday) / total_sales_yesterday) * 100
    else:
        today_sales_trend = 100 if total_sales_today > 0 else 0
    
    # Monthly Sales
    orders_this_month = SalesOrder.objects.filter(
        created_at__gte=this_month,
        status='completed'
    )
    order_items_this_month = OrderItem.objects.filter(sales_order__in=orders_this_month)
    total_sales_this_month = sum(item.quantity * item.price for item in order_items_this_month)
    
    # Last month's sales for comparison
    orders_last_month = SalesOrder.objects.filter(
        created_at__gte=last_month,
        created_at__lt=this_month,
        status='completed'
    )
    order_items_last_month = OrderItem.objects.filter(sales_order__in=orders_last_month)
    total_sales_last_month = sum(item.quantity * item.price for item in order_items_last_month)
    
    # Calculate monthly sales trend
    if total_sales_last_month > 0:
        monthly_sales_trend = ((total_sales_this_month - total_sales_last_month) / total_sales_last_month) * 100
    else:
        monthly_sales_trend = 100 if total_sales_this_month > 0 else 0
    
    # Total Orders
    total_orders = SalesOrder.objects.filter(status='completed').count()
    orders_today_count = orders_today.count()
    
    # Low Stock Items
    low_stock_items = Inventory.objects.filter(quantity__lte=5).select_related('product')
    low_stock_count = low_stock_items.count()
    
    # Expiring Soon (<= 90 days)
    cutoff_date = today + timedelta(days=90)
    expiring_products = Product.objects.filter(expiry_date__isnull=False, expiry_date__lte=cutoff_date)
    # Map inventories by product id for quick lookup
    inventories = Inventory.objects.filter(product__in=expiring_products).select_related('product', 'product__category')
    inv_map = {inv.product_id: inv for inv in inventories}
    expiring_soon_items = []
    for p in expiring_products.select_related('category'):
        days_left = (p.expiry_date - today).days if p.expiry_date else None
        expiring_soon_items.append({
            'product': p,
            'inventory': inv_map.get(p.id),
            'days_left': days_left,
        })
    expiring_soon_count = len(expiring_soon_items)
    
    # Recent Orders (last 10)
    recent_orders = SalesOrder.objects.filter(status='completed').select_related('customer').order_by('-created_at')[:10]
    
    # Sales Trend Data (last 7 days)
    sales_trend_data = []
    sales_trend_labels = []
    for i in range(7):
        date = today - timedelta(days=i)
        orders_for_date = SalesOrder.objects.filter(
            created_at__date=date,
            status='completed'
        )
        order_items_for_date = OrderItem.objects.filter(sales_order__in=orders_for_date)
        daily_sales = sum(item.quantity * item.price for item in order_items_for_date)
        sales_trend_data.insert(0, float(daily_sales))
        sales_trend_labels.insert(0, date.strftime('%b %d'))
    
    # If no sales data, provide sample data for demonstration
    if not any(sales_trend_data):
        sales_trend_data = [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0]
        sales_trend_labels = []
        for i in range(6, -1, -1):
            date = today - timedelta(days=i)
            sales_trend_labels.insert(0, date.strftime('%b %d'))

    # Top Selling Products (last 30 days)
    thirty_days_ago = today - timedelta(days=30)
    recent_orders_30_days = SalesOrder.objects.filter(
        created_at__gte=thirty_days_ago,
        status='completed'
    )
    order_items_30_days = OrderItem.objects.filter(sales_order__in=recent_orders_30_days)
    
    # Group by product and sum quantities
    product_sales = {}
    for item in order_items_30_days:
        product_name = item.product.name
        if product_name in product_sales:
            product_sales[product_name] += item.quantity
        else:
            product_sales[product_name] = item.quantity
    
    # Get top 5 products
    top_products = sorted(product_sales.items(), key=lambda x: x[1], reverse=True)[:5]
    
    # If no product data, provide sample data
    if not top_products:
        top_products = [["Sample Product 1", 10], ["Sample Product 2", 8], ["Sample Product 3", 6]]
    
    # Category Distribution
    category_sales = {}
    for item in order_items_30_days:
        category_name = item.product.category.name if item.product.category else 'Uncategorized'
        if category_name in category_sales:
            category_sales[category_name] += float(item.quantity * item.price)
        else:
            category_sales[category_name] = float(item.quantity * item.price)
    
    # If no category data, provide sample data
    if not category_sales:
        category_sales = {"Electronics": 1500.0, "Clothing": 800.0, "Books": 300.0}
    
    # Monthly Sales Data for Chart
    monthly_sales_data = []
    monthly_labels = []
    for i in range(6):
        month_start = timezone.make_aware(datetime.combine(this_month - timedelta(days=30*i), datetime.min.time()))
        month_end = timezone.make_aware(datetime.combine(month_start.date() + timedelta(days=30), datetime.min.time()))
        orders_month = SalesOrder.objects.filter(
            created_at__gte=month_start,
            created_at__lt=month_end,
            status='completed'
        )
        order_items_month = OrderItem.objects.filter(sales_order__in=orders_month)
        monthly_sales = sum(item.quantity * item.price for item in order_items_month)
        monthly_sales_data.insert(0, float(monthly_sales))
        monthly_labels.insert(0, month_start.strftime('%b %Y'))
    
    # If no monthly data, provide sample data
    if not any(monthly_sales_data):
        monthly_sales_data = [0.0, 0.0, 0.0, 0.0, 0.0, 0.0]
        monthly_labels = []
        for i in range(5, -1, -1):
            month_date = this_month - timedelta(days=30*i)
            monthly_labels.insert(0, month_date.strftime('%b %Y'))
 
    
    context = {
        # Sales Data
        'total_sales_today': total_sales_today,
        'today_sales_trend': round(today_sales_trend, 1),
        'total_sales_this_month': total_sales_this_month,
        'monthly_sales_trend': round(monthly_sales_trend, 1),
        
        # Orders Data
        'total_orders': total_orders,
        'orders_today': orders_today_count,
        
        # Inventory Data
        'low_stock_count': low_stock_count,
        'low_stock_items': low_stock_items,
        'expiring_soon_count': expiring_soon_count,
        'expiring_soon_items': expiring_soon_items,
        
        # Recent Data
        'recent_orders': recent_orders,
        
        # # Chart Data - JSON serialized for JavaScript
        # 'sales_trend_data_json': json.dumps(sales_trend_data, cls=DecimalEncoder),
        # 'sales_trend_labels_json': json.dumps(sales_trend_labels),
        # 'top_products_json': json.dumps(top_products, cls=DecimalEncoder),
        # 'category_sales_json': json.dumps(category_sales, cls=DecimalEncoder),
        # 'monthly_sales_data_json': json.dumps(monthly_sales_data, cls=DecimalEncoder),
        # 'monthly_labels_json': json.dumps(monthly_labels),
        
        # Additional Stats
        'total_customers': SalesOrder.objects.filter(status='completed').values('customer').distinct().count(),
        'total_products': Product.objects.count(),
        'total_categories': Category.objects.count(),
    }
    
    return render(request, 'dashboard/index.html', context)
