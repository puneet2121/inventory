from django.db import models
from django.db import transaction
from app.core.models import TenantAwareModel
from app.inventory.models import Product, Inventory, StockMovement, StockMovementType
from app.employee.models import EmployeeProfile


class ExpenseCategory(models.TextChoices):
    SUPPLIER = 'supplier', 'Supplier Purchase'
    SALARY = 'salary', 'Salary'
    RENT = 'rent', 'Rent'
    GAS = 'gas', 'Gas'
    OTHER = 'other', 'Other'


class Bill(models.Model):
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    bill_date = models.DateField()
    category = models.CharField(max_length=20, choices=ExpenseCategory.choices, default=ExpenseCategory.SUPPLIER)
    vehicle = models.CharField(max_length=20, null=True, blank=True)
    # Optional references
    paid_to = models.ForeignKey(EmployeeProfile, null=True, blank=True, on_delete=models.SET_NULL)
    notes = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"{self.get_category_display()} - {self.amount} on {self.bill_date}"


class Vendor(TenantAwareModel):
    name = models.CharField(max_length=255)
    contact = models.CharField(max_length=50, blank=True, null=True)
    email = models.EmailField(blank=True, null=True)

    def __str__(self):
        return self.name


class PurchaseOrderStatus(models.TextChoices):
    DRAFT = 'DRAFT', 'Draft'
    RECEIVED = 'RECEIVED', 'Received'


class PurchaseOrder(TenantAwareModel):
    vendor = models.ForeignKey('purchase.Vendor', on_delete=models.SET_NULL, null=True, blank=True, related_name='purchase_orders')
    order_date = models.DateField(auto_now_add=True)
    status = models.CharField(max_length=20, choices=PurchaseOrderStatus.choices, default=PurchaseOrderStatus.DRAFT)
    location = models.CharField(max_length=100, default='Main Store')
    total_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    note = models.TextField(blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"PO #{self.id} - {self.vendor.name if self.vendor else 'No Vendor'}"

    def recalc_total(self):
        total = self.items.aggregate(t=models.Sum('subtotal'))['t'] or 0
        self.total_amount = total
        self.save(update_fields=['total_amount'])

    def receive(self):
        if self.status == PurchaseOrderStatus.RECEIVED:
            raise ValueError('Purchase Order already received')
        with transaction.atomic():
            # Ensure totals are correct before receiving
            self.recalc_total()
            # Track per-product totals for cost updates
            per_product_received = {}
            for item in self.items.select_related('product').all():
                inv, _ = Inventory.objects.get_or_create(product=item.product, location=self.location, defaults={'quantity': 0, 'tenant_id': self.tenant_id})
                inv.quantity = (inv.quantity or 0) + item.quantity
                inv.save()
                # Log stock movement
                StockMovement.objects.create(
                    product=item.product,
                    location=self.location,
                    change_type=StockMovementType.PURCHASE_RECEIVE,
                    quantity_change=item.quantity,
                    related_purchase_order=self,
                    tenant_id=self.tenant_id,
                    note=f"PO #{self.id} received"
                )
                # Aggregate for cost updates
                per_product_received.setdefault(item.product_id, {'product': item.product, 'qty': 0, 'value': 0})
                per_product_received[item.product_id]['qty'] += item.quantity
                per_product_received[item.product_id]['value'] += (item.quantity * item.unit_price)

            # Weighted average cost update per product
            for pp in per_product_received.values():
                product = pp['product']
                received_qty = pp['qty']
                received_value = pp['value']
                if received_qty <= 0:
                    continue
                old_cost = product.cost or 0
                # Sum current inventory across locations for this tenant and product
                current_qty = Inventory.objects.filter(product=product).aggregate(t=models.Sum('quantity'))['t'] or 0
                # current_qty includes just-updated location; to compute average correctly, subtract received_qty to get prior
                prior_qty = max((current_qty - received_qty), 0)
                new_total_qty = prior_qty + received_qty
                if new_total_qty > 0:
                    new_cost = ((prior_qty * old_cost) + received_value) / new_total_qty
                    product.cost = new_cost
                    product.save(update_fields=['cost'])
            self.status = PurchaseOrderStatus.RECEIVED
            self.save(update_fields=['status'])


class PurchaseOrderItem(TenantAwareModel):
    purchase_order = models.ForeignKey('purchase.PurchaseOrder', on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField()
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)
    subtotal = models.DecimalField(max_digits=12, decimal_places=2, default=0)

    def save(self, *args, **kwargs):
        self.subtotal = (self.quantity or 0) * (self.unit_price or 0)
        super().save(*args, **kwargs)
        # Update parent cached total
        if self.purchase_order_id:
            try:
                self.purchase_order.recalc_total()
            except Exception:
                pass

    def __str__(self):
        return f"{self.quantity} x {self.product.name}"
