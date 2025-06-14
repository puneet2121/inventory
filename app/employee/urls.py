from django.urls import path
from . import views

app_name = 'employee'

urlpatterns = [
    path('create/', views.create_or_edit_employee, name='create_employee'),
    path('edit/<int:pk>', views.create_or_edit_employee, name='edit_employee'),
    path('delete/<int:pk>', views.delete_employee, name='delete_employee'),
    path('list/', views.employee_list, name='employee_list'),

# Calendar-related
    path('calendar/', views.assignment_calendar, name='assignment-calendar'),
    path('assignments/json/', views.assignment_events, name='assignment-events'),
    path('assignments/create/', views.assignment_create, name='assignment-create'),


]
