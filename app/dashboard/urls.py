from django.urls import path
from . import views

app_name = 'dashboard'
urlpatterns = [
    path('', views.dashboard_view, name='dashboard'),
    path('api/sales/trend/<str:period>/', views.sales_trend_api, name='sales_trend_api'),
]
