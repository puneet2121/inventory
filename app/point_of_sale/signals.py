"""Signal handlers for point_of_sale app."""

from django.conf import settings
from django.db.models.signals import post_delete, post_save, pre_save
from django.dispatch import receiver

from .models import OrderItem
from .services import (
    refresh_product_sales_summary,
    refresh_product_sales_summary_for_order_item,
)

SUMMARY_PERIOD = getattr(settings, 'PRODUCT_SALES_SUMMARY_PERIOD', 'daily')


@receiver(pre_save, sender=OrderItem)
def _cache_original_order_item_state(sender, instance, **kwargs):
    """Keep the original product/order period so summaries stay consistent after edits."""

    if not instance.pk:
        instance._original_product = None
        instance._original_order_created_at = None
        instance._original_tenant_id = None
        return

    try:
        original = sender._base_manager.select_related('sales_order', 'product').get(pk=instance.pk)
    except sender.DoesNotExist:
        instance._original_product = None
        instance._original_order_created_at = None
        instance._original_tenant_id = None
        return

    instance._original_product = original.product
    instance._original_order_created_at = getattr(original.sales_order, 'created_at', None)
    instance._original_tenant_id = original.tenant_id or getattr(original.sales_order, 'tenant_id', None)


@receiver(post_save, sender=OrderItem)
def order_item_saved(sender, instance, created, **kwargs):  # noqa: D401 - succinct hook doc
    """Refresh summary rows whenever an order item is inserted or updated."""

    refresh_product_sales_summary_for_order_item(instance, period=SUMMARY_PERIOD)

    original_product = getattr(instance, '_original_product', None)
    original_created_at = getattr(instance, '_original_order_created_at', None)
    original_tenant_id = getattr(instance, '_original_tenant_id', None)

    if (
        original_product
        and original_created_at
        and (
            original_product != instance.product
            or original_created_at != getattr(instance.sales_order, 'created_at', None)
        )
    ):
        refresh_product_sales_summary(
            original_product,
            original_created_at,
            original_tenant_id,
            period=SUMMARY_PERIOD,
        )

    for attr in ('_original_product', '_original_order_created_at', '_original_tenant_id'):
        if hasattr(instance, attr):
            delattr(instance, attr)


@receiver(post_delete, sender=OrderItem)
def order_item_deleted(sender, instance, **kwargs):
    """Ensure summary rows shrink appropriately when order items are removed."""

    refresh_product_sales_summary_for_order_item(instance, period=SUMMARY_PERIOD)
