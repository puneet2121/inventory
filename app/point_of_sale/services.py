"""Utility services for point_of_sale domain."""

import calendar
from decimal import Decimal

from django.conf import settings
from django.db.models import Count, DecimalField, ExpressionWrapper, F, IntegerField, Sum, Value
from django.db.models.functions import Coalesce

from .models import OrderItem, ProductSalesSummary


def _resolve_period_bounds(order_datetime, period: str):
    """Return (period_start_date, period_end_date) for the configured summary period."""

    if order_datetime is None:
        return None, None

    # Always operate on the naive/local date so summaries stay aligned with business calendar.
    order_date = order_datetime.date()

    if period == 'monthly':
        period_start = order_date.replace(day=1)
        last_day = calendar.monthrange(order_date.year, order_date.month)[1]
        period_end = order_date.replace(day=last_day)
    else:
        period_start = order_date
        period_end = order_date

    return period_start, period_end


def refresh_product_sales_summary(product, order_datetime, tenant_id, *, period: str | None = None):
    """Recalculate the denormalized sales summary for a product and period."""

    if product is None or order_datetime is None or tenant_id is None:
        return

    period = period or getattr(settings, 'PRODUCT_SALES_SUMMARY_PERIOD', 'daily')
    period_start, period_end = _resolve_period_bounds(order_datetime, period)

    if period_start is None or period_end is None:
        return

    if period == 'monthly':
        date_filter = {
            'sales_order__created_at__date__range': (period_start, period_end)
        }
    else:
        date_filter = {'sales_order__created_at__date': period_start}

    base_qs = OrderItem._base_manager.filter(
        tenant_id=tenant_id,
        product=product,
        **date_filter,
    )

    revenue_expression = ExpressionWrapper(
        F('quantity') * F('price'),
        output_field=DecimalField(max_digits=15, decimal_places=2),
    )

    summary_data = base_qs.aggregate(
        total_quantity=Coalesce(
            Sum('quantity'),
            Value(0),
            output_field=IntegerField(),
        ),
        total_revenue=Coalesce(
            Sum(revenue_expression),
            Value(Decimal('0.00')),
            output_field=DecimalField(max_digits=15, decimal_places=2),
        ),
        total_orders=Coalesce(
            Count('sales_order', distinct=True),
            Value(0),
            output_field=IntegerField(),
        ),
        item_count=Coalesce(
            Count('id'),
            Value(0),
            output_field=IntegerField(),
        ),
    )

    if summary_data['item_count'] == 0:
        ProductSalesSummary._base_manager.filter(
            tenant_id=tenant_id,
            product=product,
            period_start=period_start,
            period_end=period_end,
        ).delete()
        return

    ProductSalesSummary._base_manager.update_or_create(
        tenant_id=tenant_id,
        product=product,
        period_start=period_start,
        period_end=period_end,
        defaults={
            'total_quantity': summary_data['total_quantity'],
            'total_revenue': summary_data['total_revenue'],
            'total_orders': summary_data['total_orders'],
        },
    )


def refresh_product_sales_summary_for_order_item(order_item, *, period: str | None = None):
    """Convenience wrapper to update the summary for a specific order item."""

    if order_item is None:
        return

    sales_order = getattr(order_item, 'sales_order', None)
    product = getattr(order_item, 'product', None)
    tenant_id = getattr(order_item, 'tenant_id', None) or getattr(sales_order, 'tenant_id', None)

    if product is None or sales_order is None:
        return

    refresh_product_sales_summary(
        product,
        getattr(sales_order, 'created_at', None),
        tenant_id,
        period=period,
    )
