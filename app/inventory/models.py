from django.db import models

from app.core.models import TenantAwareModel, TenantManager
from app.core.storage_backends import StaticStorage, MediaStorage
from django.db.models import JSONField
from django.contrib.auth.models import User
from django.utils.translation import gettext_lazy as _


class OrderStatusChoices(models.TextChoices):
    PENDING = 'PENDING', 'Pending'
    SHIPPING = 'SHIPPING', 'Shipping'
    DELIVERED = 'DELIVERED', 'Delivered'
    CANCELLED = 'CANCELLED', 'Cancelled'


class OrderTypeChoices(models.TextChoices):
    RETAIL = 'RETAIL', 'Retail'
    WHOLESALE = 'WHOLESALE', 'Wholesale'


class Category(TenantAwareModel):
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    # Tenant-aware manager
    objects = TenantManager()

    class Meta:
        verbose_name_plural = "Categories"
        ordering = ['name']
        unique_together = (('tenant_id', 'name'),)

    def __str__(self):
        return self.name

    def product_count(self):
        return self.product_set.count()


class Product(TenantAwareModel):
    name = models.CharField(max_length=200)
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, blank=True)
    cost = models.DecimalField(max_digits=10, decimal_places=2)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    description = models.TextField(max_length=200, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    barcode = models.CharField(max_length=100, default='')
    model = models.CharField(max_length=100)
    sku = models.CharField(max_length=100, blank=True, null=True)
    expiry_date = models.DateField(null=True, blank=True)

    # Tenant-aware manager
    objects = TenantManager()

    def __str__(self):
        return self.name

    class Meta:
        db_table = 'product'


class Inventory(TenantAwareModel):
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    location = models.CharField(max_length=100)
    quantity = models.IntegerField()
    last_updated = models.DateTimeField(auto_now=True)

    # Tenant-aware manager
    objects = TenantManager()

    class Meta:
        db_table = 'inventory'


class Notification(TenantAwareModel):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    message = models.TextField()
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Notification for {self.user.username}"

    class Meta:
        db_table = 'notification'


class AuditLog(TenantAwareModel):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    action = models.CharField(max_length=50, help_text="Action taken like CREATE, UPDATE, DELETE")
    table_name = models.CharField(max_length=100, help_text="Affected table")
    record_id = models.IntegerField()
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.action} by {self.user.username} on {self.table_name} id {self.record_id}"

    class Meta:
        db_table = 'audit_log'


class InventoryImage(TenantAwareModel):
    inventory = models.ForeignKey(Inventory, on_delete=models.CASCADE)
    image = models.FileField()
    image_url = models.URLField()

    def __str__(self):
        return self.image.url

    class Meta:
        db_table = 'inventory_image'


class StockMovementType(models.TextChoices):
    PURCHASE_RECEIVE = 'PURCHASE_RECEIVE', _('Purchase Receive')
    SALE = 'SALE', _('Sale')
    RETURN_IN = 'RETURN_IN', _('Return In')
    RETURN_OUT = 'RETURN_OUT', _('Return Out')
    ADJUSTMENT = 'ADJUSTMENT', _('Adjustment')


class StockMovement(TenantAwareModel):
    """Immutable log of all stock changes for auditability and reporting."""
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='stock_movements')
    location = models.CharField(max_length=100)
    change_type = models.CharField(max_length=30, choices=StockMovementType.choices)
    quantity_change = models.IntegerField(help_text="Positive for inbound, negative for outbound")
    related_purchase_order = models.ForeignKey('purchase.PurchaseOrder', null=True, blank=True, on_delete=models.SET_NULL, related_name='stock_movements')
    related_sales_order = models.ForeignKey('point_of_sale.SalesOrder', null=True, blank=True, on_delete=models.SET_NULL, related_name='stock_movements')
    note = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'stock_movement'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.change_type} {self.quantity_change} of {self.product.name} at {self.location}"
