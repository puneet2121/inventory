"""
Database Query Optimization Utilities
Common patterns to avoid N+1 queries and improve performance
"""
from django.db.models import Prefetch, Q, F, Sum, Count, Avg, Max, Min
from django.db.models.functions import Coalesce
from django.core.paginator import Paginator


def optimize_customer_queries(queryset):
    """
    Optimize customer-related queries with select_related and prefetch_related
    """
    return queryset.select_related(
        'financial_snapshot'
    ).prefetch_related(
        Prefetch(
            'sales_orders',
            queryset=queryset.model.sales_orders.model.objects.select_related('employee')
        ),
        Prefetch(
            'customer_ledger_set',
            queryset=queryset.model.customer_ledger_set.model.objects.select_related('invoice')
        )
    )


def optimize_sales_order_queries(queryset):
    """
    Optimize sales order queries with related data
    """
    return queryset.select_related(
        'customer', 'employee', 'invoice'
    ).prefetch_related(
        Prefetch(
            'items',
            queryset=queryset.model.items.model.objects.select_related('product', 'product__category')
        ),
        'payments'
    )


def optimize_inventory_queries(queryset):
    """
    Optimize inventory queries with product and category data
    """
    return queryset.select_related(
        'product', 'product__category'
    ).annotate(
        total_stock=Coalesce(Sum('quantity'), 0)
    )


def paginate_queryset(queryset, page_number, per_page=50):
    """
    Helper function for consistent pagination
    """
    paginator = Paginator(queryset, per_page)
    return paginator.get_page(page_number)


def bulk_update_related(instance, related_field, update_data):
    """
    Efficiently update related objects in bulk
    """
    related_objects = getattr(instance, related_field).all()
    for obj in related_objects:
        for field, value in update_data.items():
            setattr(obj, field, value)
    
    # Bulk update all objects at once
    if related_objects:
        model_class = related_objects[0].__class__
        model_class.objects.bulk_update(related_objects, list(update_data.keys()))


def get_aggregated_sales_data(start_date, end_date, customer=None):
    """
    Get aggregated sales data efficiently
    """
    from app.point_of_sale.models import OrderItem
    
    queryset = OrderItem.objects.filter(
        sales_order__status='completed',
        sales_order__created_at__date__range=[start_date, end_date]
    )
    
    if customer:
        queryset = queryset.filter(sales_order__customer=customer)
    
    return queryset.aggregate(
        total_sales=Sum(F('quantity') * F('price')),
        total_quantity=Sum('quantity'),
        order_count=Count('sales_order', distinct=True),
        customer_count=Count('sales_order__customer', distinct=True)
    )


def optimize_template_queries(queryset, select_fields=None, prefetch_fields=None):
    """
    Generic function to optimize queries for template rendering
    """
    if select_fields:
        queryset = queryset.select_related(*select_fields)
    
    if prefetch_fields:
        queryset = queryset.prefetch_related(*prefetch_fields)
    
    return queryset
