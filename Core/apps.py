from django.apps import AppConfig


class CoreConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "Core"
    verbose_name = "هسته"

    def ready(self):
        from . import converters  # noqa: F401  (ثبت مبدل آدرس uslug)
