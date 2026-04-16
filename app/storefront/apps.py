from importlib import import_module

from django.apps import AppConfig


class StorefrontConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'app.storefront'
    verbose_name = 'Storefront / Ecommerce'

    def ready(self):
        import_module('app.storefront.signals')
