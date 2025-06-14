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
    path('export_inventory/', views.export_inventory, name='export_inventory'),
    path('import_inventory/', views.import_inventory, name='import_inventory'),
    path('categories/', views.category_list, name='category_list'),
    path('categories/add/', views.add_category, name='add_category'),
    path('categories/<int:pk>/edit/', views.edit_category, name='edit_category'),
    path('categories/<int:pk>/delete/', views.delete_category, name='delete_category'),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
