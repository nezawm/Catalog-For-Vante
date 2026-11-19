from django.apps import AppConfig
from django.db.models.signals import post_migrate


def _sync_group(sender, using="default", **kwargs):
    # اپ Panel مدل ندارد و جنگو برایش post_migrate نمی‌فرستد؛ پس روی آخرین اپِ دارای مجوز (Product) سوار می‌شویم
    # تا مجوزهای همهٔ اپ‌ها (Core, Category, Product) تا این لحظه ساخته شده باشند.
    if sender.label != "Product":
        return
    from .groups import sync_client_group

    sync_client_group(using=using)


class PanelConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "Panel"
    verbose_name = "پنل مدیریت کارفرما"

    def ready(self):
        # بعد از هر migrate گروه «مدیر کاتالوگ» با مجوزهای درست آماده می‌شود،
        # تا بتوان کاربر کارفرما را مستقیم از ادمین جنگو ساخت و به این گروه داد.
        post_migrate.connect(_sync_group)
