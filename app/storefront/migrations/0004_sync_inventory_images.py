from django.db import migrations


def sync_inventory_images(apps, schema_editor):
    InventoryImage = apps.get_model('inventory', 'InventoryImage')
    StorefrontProduct = apps.get_model('storefront', 'StorefrontProduct')
    StorefrontProductImage = apps.get_model('storefront', 'StorefrontProductImage')

    queryset = InventoryImage.objects.select_related('inventory__product')
    for inv_image in queryset.iterator():
        if not inv_image.image_url:
            continue
        product = inv_image.inventory.product
        storefront = StorefrontProduct.objects.filter(product=product).first()
        if not storefront:
            continue
        if StorefrontProductImage.objects.filter(product=storefront, image_url=inv_image.image_url).exists():
            continue
        display_order = StorefrontProductImage.objects.filter(product=storefront).count()
        StorefrontProductImage.objects.create(
            product=storefront,
            image_url=inv_image.image_url,
            display_order=display_order,
            alt_text=product.name,
        )


def noop(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('inventory', '0003_alter_inventoryimage_image'),
        ('storefront', '0003_alter_storefrontproductimage_image'),
    ]

    operations = [
        migrations.RunPython(sync_inventory_images, noop),
    ]
