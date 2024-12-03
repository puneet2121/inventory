from django.urls import path
from . import views

urlpatterns = [
    path('create/', views.create_employee, name='create_employee'),
    path('list/', views.employee_list, name='employee_list'),
]
