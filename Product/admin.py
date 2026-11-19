from django.contrib import admin

# Register your models here.
from django.contrib import admin

from Core.admin import BaseModelAdmin

from .models import Product, Vanlite


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
        ("English", {"fields": ("name_en", "face_material_en", "colors_en", "description_en")}),
        ("مشخصات", {"fields": ("face_value", "face_unit", "liner_gsm", "adhesive")}),
        ("ونجت (عرض‌ها)", {"fields": ("width_107", "width_127", "width_152")}),
        ("اطلاعات سیستمی", {"fields": ("created_at", "updated_at")}),
    )



@admin.register(Vanlite)
class VanliteAdmin(BaseModelAdmin):
    """ونلایت: منوی کاملاً جدا در ادمین، با دو بخش «Vanlite - فارسی» و «Vanlite - English»."""

    list_display = ("name", "name_en", "type", "roll_size", "durability_years", "product_code", "product", "order", "is_active")
    list_editable = ("order", "is_active")
    list_filter = BaseModelAdmin.list_filter + ("type",)
    list_select_related = ("product",)
    search_fields = ("name", "name_en", "product_code", "product_code_en", "type")
    autocomplete_fields = ("product",)

    fieldsets = (
        (None, {"fields": ("product", "order", "is_active")}),
        ("Vanlite - فارسی", {"fields": ("name", "type", "roll_size", "durability_years", "product_code")}),
        ("Vanlite - English", {"fields": ("name_en", "type_en", "roll_size_en", "durability_years_en", "product_code_en")}),
        ("اطلاعات سیستمی", {"fields": ("created_at", "updated_at")}),
    )
