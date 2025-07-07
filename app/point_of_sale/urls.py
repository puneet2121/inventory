from django.urls import path
from . import views

app_name = 'point_of_sale'

urlpatterns = [
    path('', views.sales_order_list, name='sales_order_list'),  # Default to sales order list
    path('sales-order/', views.sales_order_list, name='sales_order_list'),
    path('sales-order/create/', views.create_sales_order, name='create_sales_order'),
    path('sales-order/<int:sales_order_id>/', views.sales_order_detail, name='sales_order_detail'),
    path('sales-order/<int:sales_order_id>/edit/', views.edit_sales_order, name='edit_sales_order'),
    path('sales-order/<int:sales_order_id>/add-items/', views.add_order_items, name='add_order_items'),
    path('sales-order/<int:sales_order_id>/convert-to-invoice/', views.convert_to_invoice, name='convert_to_invoice'),
    path('invoices/', views.invoice_list, name='invoice_list'),
    path('invoices/<int:invoice_id>/', views.invoice_detail, name='invoice_detail'),
    path('invoices/<int:invoice_id>/add-payment/', views.add_payment, name='add_payment'),
]
