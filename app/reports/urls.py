from django.urls import path
from app.reports import views

app_name = 'reports'

urlpatterns = [
    path('', views.reports_dashboard, name='reports_dashboard'),
    path('sales/', views.sales_reports, name='sales_reports'),
    path('inventory/', views.inventory_reports, name='inventory_reports'),
    path('employee/', views.employee_reports, name='employee_reports'),
    path('purchases/', views.purchases_reports, name='purchases_reports'),
    # Add more report-specific URLs here
]
