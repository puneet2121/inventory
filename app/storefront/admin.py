from django.contrib import admin

from .models import (
    StorefrontProduct,
    StorefrontProductImage,
    StorefrontVariant,
    CompatibilityTag,
)


class StorefrontProductImageInline(admin.TabularInline):
    model = StorefrontProductImage
    extra = 1


class StorefrontVariantInline(admin.TabularInline):
    model = StorefrontVariant
    extra = 0


@admin.register(StorefrontProduct)
class StorefrontProductAdmin(admin.ModelAdmin):
    list_display = ("product", "is_published", "is_trending", "list_price", "active_price")
    list_filter = ("is_published", "is_trending")
    search_fields = ("product__name", "slug")
    inlines = [StorefrontProductImageInline, StorefrontVariantInline]


@admin.register(CompatibilityTag)
class CompatibilityTagAdmin(admin.ModelAdmin):
    search_fields = ("name", "slug")
    prepopulated_fields = {"slug": ("name",)}
