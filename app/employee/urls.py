from django.urls import path
from . import views

app_name = 'employee'

urlpatterns = [
    path('create/', views.create_or_edit_employee, name='create_employee'),
    path('edit/<int:pk>', views.create_or_edit_employee, name='edit_employee'),
    path('delete/<int:pk>', views.delete_employee, name='delete_employee'),
    path('list/', views.employee_list, name='employee_list'),

]
