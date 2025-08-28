from django.urls import path
from .views import (add_customer, list_customers, customers_with_debt, edit_customer, customer_detail, import_customers,
                    add_customer2)
app_name = 'customers'


urlpatterns = [
    path('add/', add_customer, name='add_customer'),
    path('add1/', add_customer2, name='add_customer2'),
    path('list/', list_customers, name='list_customers'),
    path('debt/', customers_with_debt, name='customers_with_debt'),
    path('edit/<int:pk>/', edit_customer, name='edit_customer'),
    path('customer/<int:pk>/', customer_detail, name='customer_detail'),
    path('import/', import_customers, name='import_customers'),


]
