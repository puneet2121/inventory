from django.urls import path
from . import views

app_name = 'purchase'

urlpatterns = [
    path('bills/', views.create_bill, name='create_bill'),
    path('bills/list', views.bill_list, name='bill_list'),
    path('bills/edit/<int:pk>/', views.bill_edit, name='bill_edit'),
    path('bills/delete/<int:pk>/', views.bill_delete, name='bill_delete'),

]
