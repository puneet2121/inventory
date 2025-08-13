from django.db import models

from app.core.models import TenantAwareModel, TenantManager
from app.core.storage_backends import StaticStorage, MediaStorage
from django.db.models import JSONField
from django.contrib.auth.models import User


class OrderStatusChoices(models.TextChoices):
    PENDING = 'PENDING', 'Pending'
    SHIPPING = 'SHIPPING', 'Shipping'
    DELIVERED = 'DELIVERED', 'Delivered'
    CANCELLED = 'CANCELLED', 'Cancelled'


class OrderTypeChoices(models.TextChoices):
    RETAIL = 'RETAIL', 'Retail'
    WHOLESALE = 'WHOLESALE', 'Wholesale'


class Category(TenantAwareModel):
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    # Tenant-aware manager
    objects = TenantManager()

    class Meta:
        verbose_name_plural = "Categories"
        ordering = ['name']

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
