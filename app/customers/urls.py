from django.urls import path
from .views import add_customer, list_customers, customers_with_debt, edit_customer, customer_detail
app_name = 'customers'


urlpatterns = [
    path('add/', add_customer, name='add_customer'),
    path('list/', list_customers, name='list_customers'),
    path('debt/', customers_with_debt, name='customers_with_debt'),
    path('edit/<int:pk>/', edit_customer, name='edit_customer'),
    path('customer/<int:pk>/', customer_detail, name='customer_detail'),

]
