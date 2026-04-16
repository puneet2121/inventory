from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.utils import timezone
from django.utils.text import slugify

from app.core.tenant_middleware import get_current_tenant
from app.inventory.models import Product


class CompatibilityTag(models.Model):
    """
    Represents device compatibility metadata (e.g., 'iPhone 15', 'Samsung S24').
    """
    name = models.CharField(max_length=80, unique=True)
    slug = models.SlugField(max_length=90, unique=True)
    description = models.CharField(max_length=255, blank=True)

    class Meta:
        ordering = ["name"]

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name


class StorefrontProductQuerySet(models.QuerySet):
    def for_current_tenant(self):
        tenant_id = get_current_tenant()
        if tenant_id is None:
            return self.none()
        return self.filter(product__tenant_id=tenant_id)

    def published(self):
        return self.for_current_tenant().filter(is_published=True)


class StorefrontProduct(models.Model):
    """
    Extends the core Product model with storefront specific attributes.
    """
    product = models.OneToOneField(
        Product,
        on_delete=models.CASCADE,
        related_name='storefront_listing'
    )
    slug = models.SlugField(max_length=180, unique=True)
    list_price = models.DecimalField(max_digits=10, decimal_places=2)
    seven_day_test_price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Special promotional price valid for the next seven days."
    )
    test_price_expires_at = models.DateTimeField(null=True, blank=True)
    compatibility = models.ManyToManyField(
        CompatibilityTag,
        blank=True,
        related_name='products'
    )
    compatibility_notes = models.TextField(blank=True, help_text="Short description of supported devices.")
    is_trending = models.BooleanField(default=False)
    is_published = models.BooleanField(default=False)
    short_tagline = models.CharField(max_length=120, blank=True)
    seo_title = models.CharField(max_length=160, blank=True)
    seo_description = models.CharField(max_length=160, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = StorefrontProductQuerySet.as_manager()

    class Meta:
        ordering = ["-is_trending", "product__name"]

    def __str__(self):
        return f"{self.product.name} storefront listing"

    @property
    def active_price(self):
        """
        Returns the effective price (seven day test price if active, else list price).
        """
        if self.seven_day_test_price and self.test_price_expires_at:
            if timezone.now() <= self.test_price_expires_at:
                return self.seven_day_test_price
        return self.list_price

    def clean(self):
        super().clean()
        if self.test_price_expires_at and self.seven_day_test_price is None:
            raise models.ValidationError("Provide a seven day test price when setting an expiry timestamp.")

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.product.name)
        super().save(*args, **kwargs)


def product_image_upload_to(instance, filename):
    return f"storefront/products/{instance.product.slug}/{filename}"


class StorefrontProductImage(models.Model):
    product = models.ForeignKey(
        StorefrontProduct,
        on_delete=models.CASCADE,
        related_name='images'
    )
    image = models.ImageField(upload_to=product_image_upload_to)
    alt_text = models.CharField(max_length=160, blank=True)
    display_order = models.PositiveIntegerField(default=0)
    is_primary = models.BooleanField(default=False)

    class Meta:
        ordering = ["display_order", "id"]
        constraints = [
            models.UniqueConstraint(
                fields=["product", "display_order"],
                name="unique_product_image_display_order"
            )
        ]

    def __str__(self):
        return f"{self.product.product.name} image #{self.display_order}"


class StorefrontVariant(models.Model):
    """
    Optional variant layer for color, length, bundle etc.
    """
    product = models.ForeignKey(
        StorefrontProduct,
        on_delete=models.CASCADE,
        related_name='variants'
    )
    option_name = models.CharField(max_length=60, help_text="e.g., Color, Length")
    option_value = models.CharField(max_length=60, help_text="e.g., Midnight Black, 1m")
    sku = models.CharField(max_length=120, blank=True)
    additional_price = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        default=0,
        validators=[MinValueValidator(0)]
    )
    extra_inventory = models.IntegerField(
        null=True,
        blank=True,
        help_text="If set, overrides base product stock for this variant."
    )

    class Meta:
        unique_together = ("product", "option_name", "option_value")

    def __str__(self):
        return f"{self.product.product.name} - {self.option_name}: {self.option_value}"

    @property
    def available_quantity(self):
        if self.extra_inventory is not None:
            return self.extra_inventory
        # fallback to base product inventory total
        return self.product.product.inventory_set.aggregate(total=models.Sum("quantity")).get("total") or 0


class StorefrontProductReview(models.Model):
    product = models.ForeignKey(
        StorefrontProduct,
        on_delete=models.CASCADE,
        related_name='reviews',
    )
    reviewer_name = models.CharField(max_length=120)
    rating = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)]
    )
    body = models.TextField()
    is_published = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.product.product.name} review by {self.reviewer_name}"
