from django.apps import AppConfig


class NotificationsConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.notifications"
    verbose_name = "Notifications et relances"

    def ready(self):
        from . import signals  # noqa: F401  (branche les écouteurs : publication d'un bien, baisse de prix, visite confirmée)
