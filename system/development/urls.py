"""
URL configuration for centuryAuto project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.landing, name='landing')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='landing')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('inventory/', include("app.inventory.urls"), name="inventory"),
    path('core/', include("app.core.urls"), name="core"),
    path('point_of_sale/', include("app.point_of_sale.urls"), name="point_of_sale"),
    path('authentication/', include("app.authentication.urls"), name="authentication"),
    path('dashboard/', include('app.dashboard.urls'), name="dashboard"),
    path('customers/', include('app.customers.urls')),
    path('employee/', include('app.employee.urls')),
    path('purchase/', include('app.purchase.urls')),

]
