from django.urls import path

from . import views

app_name = 'storefront'

urlpatterns = [
    path('', views.product_list_view, name='product_list'),
    path('checkout/', views.checkout_view, name='checkout'),
    path('new-customer/<str:token>/', views.customer_signup_view, name='customer_signup'),
    path('new-customer/<str:token>/qr.png', views.customer_signup_qr_png, name='customer_signup_qr'),
    path('api/products/<slug:slug>/reviews/', views.product_review_api, name='product_reviews_api'),
    path('<slug:slug>/', views.product_detail_view, name='product_detail'),
]
