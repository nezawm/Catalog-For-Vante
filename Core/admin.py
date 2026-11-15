from django.contrib import admin

# Register your models here.
from django.contrib import admin


class BaseModelAdmin(admin.ModelAdmin):
    """کلاس پایهٔ ادمین؛ ادمین ماژول‌های دیگر از این ارث می‌برند."""

    list_filter = ("is_active",)
    readonly_fields = ("created_at", "updated_at")
    list_per_page = 25

    class Media:
        js = ("Core/js/admin_auto_slug.js",)