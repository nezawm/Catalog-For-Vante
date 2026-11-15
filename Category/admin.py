from django.contrib import admin

from Core.admin import BaseModelAdmin

from .models import Category, Subcategory


class SubcategoryInline(admin.TabularInline):
    """زیردسته‌ها را مستقیم داخل صفحهٔ دسته‌بندی اصلی (مثلاً ونکال) اضافه/ویرایش کنید."""

    model = Subcategory
    extra = 4
    fields = ("name", "name_en", "slug", "order", "is_active")


@admin.register(Category)
class CategoryAdmin(BaseModelAdmin):
    list_display = ("name", "title", "order", "is_active")
    list_editable = ("order", "is_active")
    search_fields = ("name", "title", "title_en")
    fieldsets = (
        (None, {"fields": ("name", "slug", "order", "is_active")}),
        ("فارسی", {"fields": ("title", "description")}),
        ("English", {"fields": ("title_en", "description_en")}),
        ("اطلاعات سیستمی", {"fields": ("created_at", "updated_at")}),
    )
    inlines = [SubcategoryInline]


@admin.register(Subcategory)
class SubcategoryAdmin(BaseModelAdmin):
    list_display = ("name", "category", "order", "is_active")
    list_editable = ("order", "is_active")
    list_filter = BaseModelAdmin.list_filter + ("category",)
    list_select_related = ("category",)
    search_fields = ("name", "name_en")
    fieldsets = (
        (None, {"fields": ("category", "slug", "order", "is_active")}),
        ("فارسی", {"fields": ("name", "description")}),
        ("English", {"fields": ("name_en", "description_en")}),
        ("اطلاعات سیستمی", {"fields": ("created_at", "updated_at")}),
    )
