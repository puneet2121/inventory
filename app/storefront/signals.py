from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils.text import slugify

from app.inventory.models import Product
from app.storefront.models import StorefrontProduct


def _generate_unique_slug(name, product_id):
    base_slug = slugify(name) or f"product-{product_id}"
    slug = base_slug
    suffix = 1
    while StorefrontProduct.objects.filter(slug=slug).exists():
        slug = f"{base_slug}-{suffix}"
        suffix += 1
    return slug


@receiver(post_save, sender=Product)
def create_storefront_listing(sender, instance, created, **kwargs):
    """
    Automatically create a storefront wrapper whenever a new inventory product is added.
    """
    if not created:
        return

    # Avoid duplicate creation if something else already made it.
    if hasattr(instance, 'storefront_listing'):
        return

    slug = _generate_unique_slug(instance.name, instance.pk)

    StorefrontProduct.objects.create(
        product=instance,
        slug=slug,
        list_price=instance.price,
        seven_day_test_price=None,
        test_price_expires_at=None,
        compatibility_notes='',
        is_trending=False,
        is_published=False,
        short_tagline='',
    )
