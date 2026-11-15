from django.apps import AppConfig
from django.db.models.signals import post_migrate


def _sync_group(sender, using="default", **kwargs):
    from .groups import sync_client_group

    sync_client_group(using=using)


class PanelConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "Panel"
    verbose_name = "پنل مدیریت کارفرما"

    def ready(self):
        # بعد از هر migrate گروه «مدیر کاتالوگ» با مجوزهای درست آماده می‌شود،
        # تا بتوان کاربر کارفرما را مستقیم از ادمین جنگو ساخت و به این گروه داد.
        # Panel مدل ندارد، پس سیگنال post_migrate هرگز با sender=Panel ارسال نمی‌شود؛
        # بنابراین بدون sender وصل می‌کنیم (عملیات idempotent است).
        post_migrate.connect(_sync_group, dispatch_uid="panel_sync_client_group")
