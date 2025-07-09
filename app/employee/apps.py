from django.apps import AppConfig


class EmployeeConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'app.employee'
    label = 'employee'

    def ready(self):
        import app.employee.signals

