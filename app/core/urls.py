from django.urls import path
from app.core import views
from django.conf import settings
from django.conf.urls.static import static

app_name = 'core'

urlpatterns = [
    path('', views.image_upload, name='inventory'),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
