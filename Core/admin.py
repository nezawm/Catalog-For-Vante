from django.contrib import admin

from django.contrib import admin

from .models import CatalogFile


class BaseModelAdmin(admin.ModelAdmin):
    """کلاس پایهٔ ادمین؛ ادمین ماژول‌های دیگر از این ارث می‌برند."""

    list_filter = ("is_active",)
    readonly_fields = ("created_at", "updated_at")
    list_per_page = 25

    class Media:
        js = ("Core/js/admin_auto_slug.js",)


@admin.register(CatalogFile)
class CatalogFileAdmin(BaseModelAdmin):
    list_display = ("language", "file", "download_count", "is_active", "updated_at")
    readonly_fields = BaseModelAdmin.readonly_fields + ("download_count",)
