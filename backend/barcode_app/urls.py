from django.urls import path
from .views import BarcodeListCreateView, ProductListCreateView, BarcodeCreateView

urlpatterns = [
    path('barcodes/', BarcodeListCreateView.as_view(), name='barcode-list'),
    path('products/', ProductListCreateView.as_view(), name='product-list'),
    path('add-barcode/', BarcodeCreateView.as_view(), name='add-barcode'),
]
