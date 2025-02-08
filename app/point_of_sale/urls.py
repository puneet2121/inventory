from django.urls import path
from . import views
from .views import quick_checkout, product_by_barcode

app_name = 'point_of_sale'

urlpatterns = [
    path('sales-order/create/', views.create_sales_order, name='create_sales_order'),
    path('sales-order/<int:sales_order_id>/add-items/', views.add_order_items, name='add_order_items'),
    path('sales-order/<int:sales_order_id>/convert-to-invoice/', views.convert_to_invoice, name='convert_to_invoice'),
    path('invoices/', views.invoice_list, name='invoice_list'),
    path('invoices/<int:invoice_id>/', views.invoice_detail, name='invoice_detail'),
    path('invoices/<int:invoice_id>/add-payment/', views.add_payment, name='add_payment'),
    path('quick-checkout/', quick_checkout, name='quick_checkout'),
    path('api/products/<str:barcode>/', product_by_barcode, name='product_by_barcode'),
]
