import json

from django.core import signing
from django.db.models import Q
from django.http import HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, render
from django.urls import reverse
from django.views.decorators.http import require_http_methods

from app.core.tenant_middleware import get_current_tenant, set_current_tenant
from app.customers.models import Customer
from app.storefront.forms import StorefrontCustomerSignupForm, StorefrontProductReviewForm
from app.storefront.models import StorefrontProduct

_CUSTOMER_SIGNUP_TOKEN_SALT = "storefront.customer_signup.company"
_CUSTOMER_SIGNUP_TOKEN_MAX_AGE_SECONDS = 365 * 24 * 60 * 60  # 1 year


def _make_company_signup_token(company_id):
    return signing.dumps({"company_id": int(company_id)}, salt=_CUSTOMER_SIGNUP_TOKEN_SALT)


def _load_company_id_from_token(token):
    payload = signing.loads(
        token,
        salt=_CUSTOMER_SIGNUP_TOKEN_SALT,
        max_age=_CUSTOMER_SIGNUP_TOKEN_MAX_AGE_SECONDS,
    )
    company_id = int(payload.get("company_id"))
    if company_id <= 0:
        raise signing.BadSignature("Invalid company id.")
    return company_id


def product_list_view(request):
    """
    Basic storefront listing page showing published products with trending first.
    """
    products = (
        StorefrontProduct.objects.all()
        .select_related('product', 'product__category')
        .prefetch_related('images', 'compatibility')
    )

    filters = {}

    query = request.GET.get('q')
    if query:
        products = products.filter(
            Q(product__name__icontains=query)
            | Q(product__model__icontains=query)
            | Q(short_tagline__icontains=query)
            | Q(seo_description__icontains=query)
            | Q(compatibility__name__icontains=query)
        ).distinct()
        filters['q'] = query

    category_filter = request.GET.get('category')
    if category_filter:
        if category_filter == 'uncategorized':
            products = products.filter(product__category__isnull=True)
        else:
            products = products.filter(product__category_id=category_filter)
        filters['category'] = category_filter

    item_slug = request.GET.get('item')
    if item_slug:
        products = products.filter(slug=item_slug)
        filters['item'] = item_slug

    compatibility_slug = request.GET.get('compatibility')
    if compatibility_slug:
        products = products.filter(compatibility__slug=compatibility_slug)
        filters['compatibility'] = compatibility_slug

    trending = request.GET.get('trending')
    if trending in {'1', 'true', 'True'}:
        products = products.filter(is_trending=True)
        filters['trending'] = True

    context = {
        'products': products,
        'active_filters': filters,
    }

    tenant_id = get_current_tenant()
    if tenant_id:
        token = _make_company_signup_token(tenant_id)
        context.update(
            {
                "customer_signup_token": token,
                "customer_signup_url": request.build_absolute_uri(
                    reverse("storefront:customer_signup", args=[token])
                ),
            }
        )

    return render(request, 'storefront/product_list.html', context)


def product_detail_view(request, slug):
    """
    Simple product detail page showing images, description, compatibility tags, etc.
    """
    product = get_object_or_404(
        StorefrontProduct.objects.all()
        .select_related('product')
        .prefetch_related('images', 'compatibility', 'variants'),
        slug=slug,
    )
    return render(request, 'storefront/product_detail.html', {'product': product})


def checkout_view(request):
    """
    Lightweight placeholder checkout shell – frontend reads cart data from localStorage
    until backend order creation is ready.
    """
    return render(request, 'storefront/checkout.html')


@require_http_methods(["GET"])
def customer_signup_qr_png(request, token):
    """
    Returns a PNG QR code that encodes the signup URL for a specific company token.
    """
    try:
        # Validate early so we don't emit QR codes for malformed tokens.
        _load_company_id_from_token(token)
    except signing.BadSignature:
        return HttpResponse("Invalid signup token.", status=404, content_type="text/plain")

    try:
        import qrcode
    except ImportError:
        return HttpResponse(
            "QR support is not installed. Add `qrcode` to requirements and deploy.",
            status=501,
            content_type="text/plain",
        )

    signup_url = request.build_absolute_uri(reverse("storefront:customer_signup", args=[token]))
    img = qrcode.make(signup_url)
    response = HttpResponse(content_type="image/png")
    img.save(response, format="PNG")
    return response


@require_http_methods(["GET", "POST"])
def customer_signup_view(request, token):
    """
    Public flow: customer scans a QR, lands here, and submits minimal details.
    Creates a Customer in the correct company (tenant) and forces customer_type='C'.
    """
    try:
        company_id = _load_company_id_from_token(token)
    except signing.BadSignature:
        return HttpResponse("Invalid or expired signup link.", status=404, content_type="text/plain")

    # Ensure the tenant-aware model save() and manager filtering work for this request.
    set_current_tenant(company_id)

    if request.method == "POST":
        form = StorefrontCustomerSignupForm(request.POST)
        if form.is_valid():
            customer_kwargs = form.to_customer_kwargs()
            customer = Customer(
                tenant_id=company_id,  # defensive: don't rely only on thread-local
                customer_type="C",
                city="",
                **customer_kwargs,
            )
            customer.save()
            return render(
                request,
                "storefront/customer_signup.html",
                {
                    "form": StorefrontCustomerSignupForm(),
                    "submitted": True,
                },
            )
    else:
        form = StorefrontCustomerSignupForm()

    return render(
        request,
        "storefront/customer_signup.html",
        {
            "form": form,
            "submitted": False,
        },
    )


def _serialize_review(review):
    return {
        'id': review.id,
        'name': review.reviewer_name,
        'rating': review.rating,
        'body': review.body,
        'created_at': review.created_at.strftime('%b %d, %Y %I:%M %p'),
    }


@require_http_methods(["GET", "POST"])
def product_review_api(request, slug):
    product = get_object_or_404(
        StorefrontProduct.objects.all(),
        slug=slug,
    )

    if request.method == 'GET':
        limit = request.GET.get('limit')
        try:
            limit = int(limit) if limit else 10
        except ValueError:
            limit = 10
        limit = max(1, min(limit, 20))
        reviews = product.reviews.filter(is_published=True).order_by('-created_at')[:limit]
        return JsonResponse({'reviews': [_serialize_review(review) for review in reviews]})

    try:
        payload = json.loads(request.body or '{}')
    except json.JSONDecodeError:
        return JsonResponse({'errors': {'__all__': ['Invalid JSON payload.']}}, status=400)

    form = StorefrontProductReviewForm(payload)
    if not form.is_valid():
        return JsonResponse({'errors': form.errors}, status=400)

    review = form.save(commit=False)
    review.product = product
    review.save()

    return JsonResponse({'review': _serialize_review(review)}, status=201)
