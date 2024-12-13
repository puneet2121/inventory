from django.contrib import admin
from .models import SalesOrder, OrderItem


class SalesOrderAdmin(admin.ModelAdmin):
    list_display = ('id', 'customer_name', 'total_items', 'total_price', 'created_at')

    @admin.display(description='Total Items')
    def total_items(self, obj):
        """Calculate the total quantity of items in the order."""
        return sum(item.quantity for item in obj.items.all())


admin.site.register(SalesOrder, SalesOrderAdmin)
