from collections import OrderedDict

from django.utils.text import slugify

from app.storefront.models import StorefrontProduct


def storefront_navigation(request):
    """
    Supplies the storefront templates with a ready-to-render category/subcategory tree
    and a short trending list without leaking the dashboard sidebar.
    """
    match = getattr(request, "resolver_match", None)
    if not match or match.namespace != "storefront":
        return {}

    listings = list(
        StorefrontProduct.objects.published()
        .select_related("product__category")
        .only(
            "id",
            "slug",
            "is_trending",
            "list_price",
            "seven_day_test_price",
            "test_price_expires_at",
            "product__id",
            "product__name",
            "product__model",
            "product__category__id",
            "product__category__name",
        )
    )

    categories = OrderedDict()
    trending_links = []

    for listing in listings:
        category = listing.product.category
        cat_id = category.id if category else 0
        cat_name = category.name if category else "Uncategorized"
        cat_slug = slugify(cat_name) or "uncategorized"

        filter_value = cat_id or "uncategorized"

        if cat_id not in categories:
            categories[cat_id] = {
                "id": cat_id,
                "name": cat_name,
                "slug": cat_slug,
                "filter_value": filter_value,
                "subcategories": [],
            }

        categories[cat_id]["subcategories"].append(
            {
                "label": listing.product.model or listing.product.name,
                "product_name": listing.product.name,
                "slug": listing.slug,
                "price": listing.active_price,
            }
        )

        if listing.is_trending and len(trending_links) < 8:
            trending_links.append(
                {
                    "name": listing.product.name,
                    "slug": listing.slug,
                }
            )

    return {
        "storefront_category_tree": list(categories.values()),
        "storefront_trending_links": trending_links,
    }
