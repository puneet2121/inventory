from django.contrib import admin
from app.inventory import models

# Register your models here.
admin.site.register(models.Inventory)

@admin.register(models.Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('name', 'sku', 'price', 'cost', 'category')
    search_fields = ('name', 'sku')


@admin.register(models.StockMovement)
class StockMovementAdmin(admin.ModelAdmin):
    list_display = (
        'product', 'location', 'change_type', 'quantity_change',
        'related_purchase_order', 'related_sales_order', 'created_at'
    )
    list_filter = ('change_type', 'location')
    search_fields = ('product__name',)
    date_hierarchy = 'created_at'
