from django.apps import AppConfig


class AnalyticsConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.analytics"
    verbose_name = "Statistiques et acquisition"

    def ready(self):
        from . import signals  # noqa: F401  (date de vente et événement « vente »)
