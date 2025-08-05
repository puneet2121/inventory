from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.db.models import Sum, Count, F, Q, Value, DecimalField, Case, When
from django.db.models.functions import Coalesce, TruncDate, TruncMonth, TruncYear
from django.utils import timezone
from django.http import HttpResponse, JsonResponse
from django.core.paginator import Paginator
from django.template.loader import render_to_string
from app.point_of_sale.models import Invoice, SalesOrder, Payment, OrderItem
from app.inventory.models import Product, Category
from app.customers.models import Customer
from app.reports.forms import SalesReportForm
# from app.reports.report_utils import export_to_pdf, export_to_csv, get_report_context

@login_required
def reports_dashboard(request):
    """Main reports dashboard showing all report categories"""
    report_categories = [
        {
            'name': 'Sales Reports',
            'icon': 'bi-graph-up',
            'description': 'Generate detailed sales reports by period, product, or customer.',
            'url': 'reports:sales_reports'
        },
        {
            'name': 'Inventory Reports',
            'icon': 'bi-box-seam',
            'description': 'View stock levels, inventory valuation, and movement reports.',
            'url': 'reports:inventory_reports'
        },
        {
            'name': 'Employee Reports',
            'icon': 'bi-people',
            'description': 'Track employee performance, sales, and attendance.',
            'url': 'reports:employee_reports'
        },
        {
            'name': 'Purchases Reports',
            'icon': 'bi-cart-plus',
            'description': 'Analyze purchase orders, vendor performance, and expenses.',
            'url': 'reports:purchases_reports'
        },
    ]
    return render(request, 'reports/dashboard.html', {'report_categories': report_categories})

@login_required
def sales_reports(request):
    """Sales reports view with date filtering"""
    form = SalesReportForm(request.GET or None)
    
    if form.is_valid():
        # Get date range from form
        start_date, end_date = form.get_date_range()
        
        # Base queryset
        orders = SalesOrder.objects.filter(
            created_at__date__gte=start_date,
            created_at__date__lte=end_date
        )
        
        # Apply filters
        if form.cleaned_data.get('customer'):
            orders = orders.filter(customer=form.cleaned_data['customer'])
            
        if form.cleaned_data.get('status'):
            orders = orders.filter(status=form.cleaned_data['status'])
        else:
            # Default to only completed orders if no status is selected
            orders = orders.filter(status='completed')
        
        # Get report data based on report type
        report_type = form.cleaned_data.get('report_type', 'summary')
        
        if report_type == 'summary':
            data = get_sales_summary(orders)
            template = 'reports/partials/sales_summary.html'
            
        elif report_type == 'detailed':
            data = get_detailed_sales(orders, request)
            template = 'reports/partials/detailed_sales.html'
            
        elif report_type == 'product_wise':
            data = get_product_wise_sales(orders, request)
            template = 'reports/partials/product_wise_sales.html'
            
        elif report_type == 'customer_wise':
            data = get_customer_wise_sales(orders, request)
            template = 'reports/partials/customer_wise_sales.html'
        
        # Add common data
        data.update({
            'start_date': start_date,
            'end_date': end_date,
        })
        
        # Handle export formats
        output_format = form.cleaned_data.get('output_format', 'html')
        
        # if output_format == 'pdf':
        #     # Generate PDF
        #     context = get_report_context(
        #         form=form,
        #         title=f"Sales Report - {report_type.replace('_', ' ').title()}",
        #         **data
        #     )
        #     return export_to_pdf(
        #         template_src='reports/export/pdf_template.html',
        #         context_dict=context,
        #         filename=f'sales_report_{report_type}'
        #     )
        #
        # elif output_format == 'csv':
        #     # Generate CSV based on report type
        #     if report_type == 'summary':
        #         return export_sales_summary_csv(data, form)
        #     elif report_type == 'detailed':
        #         return export_detailed_sales_csv(data, form)
        #     elif report_type == 'product_wise':
        #         return export_product_wise_csv(data, form)
        #     elif report_type == 'customer_wise':
        #         return export_customer_wise_csv(data, form)
        #
        # # For HTML, just add the data to context
        # context = {
        #     'title': 'Sales Reports',
        #     'form': form,
        #     'report_data': data,
        #     'active_tab': report_type,
        # }
        
        # if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        #     # Return partial template for AJAX requests
        #     html = render_to_string(template, context, request)
        #     return JsonResponse({'html': html})
            
    else:
        # Initial load or form validation failed
        context = {
            'title': 'Sales Reports',
            'form': form,
            'report_data': None,
            'active_tab': 'summary',
        }
    
    return render(request, 'reports/sales_reports.html', context)

@login_required
def inventory_reports(request):
    """Inventory reports view"""
    context = {
        'report_types': [
            {'id': 'stock_levels', 'name': 'Current Stock Levels'},
            {'id': 'low_stock', 'name': 'Low Stock Items'},
            {'id': 'inventory_valuation', 'name': 'Inventory Valuation'},
            {'id': 'inventory_movement', 'name': 'Inventory Movement'},
        ]
    }
    return render(request, 'reports/inventory_reports.html', context)

@login_required
def employee_reports(request):
    """Employee performance reports view"""
    context = {
        'report_types': [
            {'id': 'sales_by_employee', 'name': 'Sales by Employee'},
            {'id': 'employee_performance', 'name': 'Employee Performance'},
            {'id': 'attendance', 'name': 'Attendance'},
            {'id': 'commission', 'name': 'Commission Reports'},
        ]
    }
    return render(request, 'reports/employee_reports.html', context)

@login_required
def purchases_reports(request):
    """Purchases reports view"""
    context = {
        'report_types': [
            {'id': 'purchase_summary', 'name': 'Purchase Summary'},
            {'id': 'purchase_by_vendor', 'name': 'Purchases by Vendor'},
            {'id': 'purchase_by_category', 'name': 'Purchases by Category'},
            {'id': 'expense_analysis', 'name': 'Expense Analysis'},
        ]
    }
    return render(request, 'reports/purchases_reports.html', context)

# AJAX/API endpoints for report data
@login_required
def get_sales_summary(request):
    """Get sales summary data for the dashboard"""
    # Default to last 30 days
    end_date = datetime.now()
    start_date = end_date - timedelta(days=30)
    
    # Get total sales
    total_sales = Payment.objects.filter(
        payment_date__range=[start_date, end_date],
        payment_type='payment'
    ).aggregate(total=Sum('amount'))['total'] or 0
    
    # Get number of orders
    order_count = SalesOrder.objects.filter(
        created_at__range=[start_date, end_date]
    ).count()
    
    # Get average order value
    avg_order_value = total_sales / order_count if order_count > 0 else 0
    
    return JsonResponse({
        'total_sales': total_sales,
        'order_count': order_count,
        'avg_order_value': avg_order_value,
        'period': f"{start_date.strftime('%b %d, %Y')} - {end_date.strftime('%b %d, %Y')}"
    })

# Helper functions for sales reports
def get_sales_summary(orders):
    """Generate summary data for sales report"""
    # Calculate totals
    total_sales = orders.aggregate(
        total=Coalesce(Sum('cached_total'), 0, output_field=DecimalField())
    )['total']
    
    total_orders = orders.count()
    
    # Get sales by status
    sales_by_status = orders.values('status').annotate(
        count=Count('id'),
        total=Coalesce(Sum('cached_total'), 0, output_field=DecimalField())
    ).order_by('-total')
    
    # Get top selling products
    top_products = OrderItem.objects.filter(
        order__in=orders
    ).values(
        'product__name', 'product__barcode'
    ).annotate(
        total_quantity=Coalesce(Sum('quantity'), 0),
        total_revenue=Coalesce(Sum(F('quantity') * F('unit_price')), 0, output_field=DecimalField())
    ).order_by('-total_quantity')[:10]
    
    # Get sales by day for chart
    sales_by_day = orders.annotate(
        date=TruncDate('created_at')
    ).values('date').annotate(
        total=Coalesce(Sum('cached_total'), 0, output_field=DecimalField())
    ).order_by('date')
    
    # Get sales by category
    sales_by_category = OrderItem.objects.filter(
        order__in=orders
    ).values(
        'product__category__name'
    ).annotate(
        total_sales=Coalesce(Sum(F('quantity') * F('unit_price')), 0, output_field=DecimalField()),
        total_quantity=Coalesce(Sum('quantity'), 0)
    ).order_by('-total_sales')
    
    return {
        'total_sales': total_sales,
        'total_orders': total_orders,
        'sales_by_status': sales_by_status,
        'top_products': top_products,
        'sales_by_day': sales_by_day,
        'sales_by_category': sales_by_category,
    }


def get_detailed_sales(orders, request):
    """Generate detailed sales data with pagination"""
    # Get all orders with related data
    orders = orders.select_related('customer').prefetch_related('items')
    
    # Apply pagination
    paginator = Paginator(orders, 25)  # Show 25 orders per page
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)
    
    return {
        'orders': page_obj,
        'total_sales': orders.aggregate(
            total=Coalesce(Sum('cached_total'), 0, output_field=DecimalField())
        )['total'],
    }


def get_product_wise_sales(orders, request):
    """Generate product-wise sales data"""
    # Get order items with product details
    order_items = OrderItem.objects.filter(
        order__in=orders
    ).select_related('product', 'product__category')
    
    # Apply search filter
    search_query = request.GET.get('search', '')
    if search_query:
        order_items = order_items.filter(
            Q(product__name__icontains=search_query) |
            Q(product__barcode=search_query) |
            Q(product__category__name__icontains=search_query)
        )
    
    # Group by product
    products_data = order_items.values(
        'product__id', 'product__name', 'product__barcode', 'product__category__name'
    ).annotate(
        total_quantity=Coalesce(Sum('quantity'), 0),
        total_sales=Coalesce(Sum(F('quantity') * F('unit_price')), 0, output_field=DecimalField()),
        avg_price=Coalesce(Avg('unit_price'), 0, output_field=DecimalField())
    ).order_by('-total_sales')
    
    # Apply pagination
    paginator = Paginator(products_data, 25)  # Show 25 products per page
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)
    
    return {
        'products': page_obj,
        'total_products': products_data.count(),
        'total_quantity': products_data.aggregate(
            total=Coalesce(Sum('total_quantity'), 0)
        )['total'],
        'total_sales': products_data.aggregate(
            total=Coalesce(Sum('total_sales'), 0, output_field=DecimalField())
        )['total'],
        'search_query': search_query,
    }


def get_customer_wise_sales(orders, request):
    """Generate customer-wise sales data"""
    # Group by customer
    customers_data = orders.values(
        'customer__id', 'customer__name', 'customer__email', 'customer__phone'
    ).annotate(
        order_count=Count('id'),
        total_sales=Coalesce(Sum('cached_total'), 0, output_field=DecimalField()),
        avg_order_value=Coalesce(Avg('cached_total'), 0, output_field=DecimalField())
    ).order_by('-total_sales')
    
    # Apply search filter
    search_query = request.GET.get('search', '')
    if search_query:
        customers_data = customers_data.filter(
            Q(customer__name__icontains=search_query) |
            Q(customer__email__icontains(search_query)) |
            Q(customer__phone__icontains(search_query))
        )
    
    # Apply pagination
    paginator = Paginator(customers_data, 25)  # Show 25 customers per page
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)
    
    return {
        'customers': page_obj,
        'total_customers': customers_data.count(),
        'total_sales': customers_data.aggregate(
            total=Coalesce(Sum('total_sales'), 0, output_field=DecimalField())
        )['total'],
        'search_query': search_query,
    }


# Export functions
def export_sales_summary_csv(data, form):
    """Export sales summary to CSV"""
    # Prepare data for CSV
    csv_data = []
    
    # Add summary section
    csv_data.append(['Sales Summary', ''])
    csv_data.append(['Start Date', form.get_date_range()[0]])
    csv_data.append(['End Date', form.get_date_range()[1]])
    csv_data.append(['Total Sales', data['total_sales']])
    csv_data.append(['Total Orders', data['total_orders']])
    csv_data.append([''])
    
    # Add sales by status
    csv_data.append(['Sales by Status', 'Count', 'Total'])
    for item in data['sales_by_status']:
        csv_data.append([item['status'], item['count'], item['total']])
    csv_data.append([''])
    
    # Add top products
    csv_data.append(['Top Selling Products', 'Barcode', 'Quantity', 'Revenue'])
    for product in data['top_products']:
        csv_data.append([
            product['product__name'] or 'Unknown Product',
            product['product__barcode'] or '-',
            product['total_quantity'],
            product['total_revenue']
        ])
    
    # Generate CSV response
    return export_to_csv(
        data=csv_data,
        filename='sales_summary',
        field_names=[]
    )


def export_detailed_sales_csv(data, form):
    """Export detailed sales to CSV"""
    # Prepare data for CSV
    csv_data = []
    
    # Add header
    csv_data.append([
        'Order ID', 'Date', 'Customer', 'Status', 
        'Items', 'Subtotal', 'Tax', 'Discount', 'Total'
    ])
    
    # Add order data
    for order in data['orders']:
        csv_data.append([
            order.id,
            order.created_at.strftime('%Y-%m-%d %H:%M'),
            str(order.customer),
            order.get_status_display(),
            sum(item.quantity for item in order.items.all()),
            order.subtotal,
            order.tax_amount,
            order.discount_amount,
            order.cached_total
        ])
    
    # Generate CSV response
    return export_to_csv(
        data=csv_data,
        filename='detailed_sales',
        field_names=[]
    )


def export_product_wise_csv(data, form):
    """Export product-wise sales to CSV"""
    # Prepare data for CSV
    csv_data = []
    
    # Add header
    csv_data.append(['Product', 'Barcode', 'Category', 'Quantity Sold', 'Total Sales', 'Avg. Price'])
    
    # Add product data
    for product in data['products']:
        csv_data.append([
            product['product__name'] or 'Unknown Product',
            product['product__barcode'] or '-',
            product['product__category__name'] or 'Uncategorized',
            product['total_quantity'],
            product['total_sales'],
            product['avg_price']
        ])
    
    # Generate CSV response
    return export_to_csv(
        data=csv_data,
        filename='product_wise_sales',
        field_names=[]
    )


def export_customer_wise_csv(data, form):
    """Export customer-wise sales to CSV"""
    # Prepare data for CSV
    csv_data = []
    
    # Add header
    csv_data.append(['Customer', 'Email', 'Phone', 'Orders', 'Total Spent', 'Avg. Order Value'])
    
    # Add customer data
    for customer in data['customers']:
        csv_data.append([
            customer['customer__name'],
            customer['customer__email'] or '-',
            customer['customer__phone'] or '-',
            customer['order_count'],
            customer['total_sales'],
            customer['avg_order_value']
        ])
    
    # Generate CSV response
    return export_to_csv(
        data=csv_data,
        filename='customer_wise_sales',
        field_names=[]
    )
