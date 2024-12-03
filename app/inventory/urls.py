from django.urls import path
from app.inventory import views
from django.conf import settings
from django.conf.urls.static import static

app_name = 'inventory'

urlpatterns = [
    path('', views.index, name='inventory'),
    path('add_product/', views.create_or_edit_product_info, name='add_product'),
    path('product/edit/<int:product_id>/', views.create_or_edit_product_info, name='edit_product'),
    path('item/list/', views.item_list_view, name='item_list'),
    path('product/delete/<int:product_id>/', views.product_delete_view, name='delete_product'),

    path('upload/<int:product_id>/', views.upload_images, name='upload_images'),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
