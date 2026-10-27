from django.apps import AppConfig


class AppConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "app"
    verbose_name = "Hephys"

    def ready(self):
        # Registra la señal que escribe la bitácora transaccional.
        from .controllers import signals  # noqa: F401
