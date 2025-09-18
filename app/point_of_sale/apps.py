from django.apps import AppConfig

app_name = 'point_of_sale'


class PointOfSaleConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'app.point_of_sale'
    label = 'point_of_sale'

    def ready(self):  # pragma: no cover - import side effect
        from . import signals  # noqa: F401
