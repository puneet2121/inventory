from django.apps import AppConfig


class CustomersConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'app.customers'
    label = 'customers'
    def ready(self):
        import app.customers.signals
