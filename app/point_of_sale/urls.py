from django.urls import path
from app.point_of_sale import views

app_name = 'point_of_sale'

urlpatterns = [
    path('pos/', views.create_sales_order, name='pos_view'),
    path('get_customer_price/<int:customer_id>/', views.get_customer_price, name='get_customer_price'),
    path('get_product_price/<int:product_id>/', views.get_product_price, name='get_product_price'),
]
