from django.urls import path
from . import views

app_name = 'purchase'

urlpatterns = [
    path('bills/', views.create_bill, name='create_bill'),
    path('bills/list', views.bill_list, name='bill_list'),
    path('bills/edit/<int:pk>/', views.bill_edit, name='bill_edit'),
    path('bills/delete/<int:pk>/', views.bill_delete, name='bill_delete'),

    # Purchase Orders
    path('purchase-orders/', views.purchase_order_list, name='purchase_order_list'),
    path('purchase-orders/create/', views.purchase_order_create, name='purchase_order_create'),
    path('purchase-orders/<int:pk>/edit/', views.purchase_order_edit, name='purchase_order_edit'),
    path('purchase-orders/<int:pk>/receive/', views.purchase_order_receive, name='purchase_order_receive'),

    # Vendors
    path('vendors/', views.vendor_list, name='vendor_list'),
    path('vendors/create/', views.vendor_create, name='vendor_create'),
    path('vendors/<int:pk>/edit/', views.vendor_edit, name='vendor_edit'),
    path('vendors/<int:pk>/delete/', views.vendor_delete, name='vendor_delete'),

]
