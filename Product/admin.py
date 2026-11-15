from django.contrib import admin

# Register your models here.
from django.contrib import admin

from Core.admin import BaseModelAdmin

from .models import Product


@admin.register(Product)
class ProductAdmin(BaseModelAdmin):
    list_display = ("name", "category", "subcategory", "face_material", "adhesive", "order", "is_active")
    list_editable = ("order", "is_active")
    list_filter = BaseModelAdmin.list_filter + ("category", "subcategory", "adhesive")
    list_select_related = ("category", "subcategory")
    search_fields = ("name", "name_en", "face_material")

    fieldsets = (
        (None, {"fields": ("category", "subcategory", "slug", "order", "is_active")}),
        ("فارسی", {"fields": ("name", "face_material", "description")}),
        ("English", {"fields": ("name_en", "face_material_en", "description_en")}),
        ("مشخصات", {"fields": ("face_value", "face_unit", "liner_gsm", "adhesive")}),
        ("ونجت (عرض‌ها)", {"fields": ("width_107", "width_127", "width_152")}),
        ("اطلاعات سیستمی", {"fields": ("created_at", "updated_at")}),
    )
