from django.contrib import admin
from .models import Bill, Vendor, PurchaseOrder, PurchaseOrderItem

# Register your models here.

@admin.register(Vendor)
class VendorAdmin(admin.ModelAdmin):
    list_display = ('name', 'contact', 'email')
    search_fields = ('name', 'contact', 'email')


class PurchaseOrderItemInline(admin.TabularInline):
    model = PurchaseOrderItem
    extra = 0


@admin.register(PurchaseOrder)
class PurchaseOrderAdmin(admin.ModelAdmin):
    list_display = ('id', 'vendor', 'order_date', 'status', 'location', 'total_amount')
    list_filter = ('status', 'location', 'order_date')
    search_fields = ('id', 'vendor__name')
    inlines = [PurchaseOrderItemInline]


@admin.register(Bill)
class BillAdmin(admin.ModelAdmin):
    list_display = ('bill_date', 'amount', 'category', 'paid_to')
    list_filter = ('category', 'bill_date')
    search_fields = ('notes',)
