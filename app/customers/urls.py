from django.urls import path
from .views import add_customer, list_customers, customers_with_debt
app_name = 'customers'


urlpatterns = [
    path('add/', add_customer, name='add_customer'),
    path('list/', list_customers, name='list_customers'),
    path('debt/', customers_with_debt, name='customers_with_debt'),
]
