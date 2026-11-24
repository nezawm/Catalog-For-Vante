from django.core.exceptions import ValidationError
from django.db import models

# Create your models here.
from django.db import models
from django.urls import reverse
from django.utils.translation import get_language

from Category.models import Category
from Core.models import BaseModel
from Core.slugs import SLUG_HELP, make_slug, unique_slug


class Product(BaseModel):
    class FaceUnit(models.TextChoices):
        MICRON = "micron", "میکرون"
        GSM = "gsm", "گرم بر مترمربع"

    class Adhesive(models.TextChoices):
        PERMANENT_ACRYLIC = "permanent_acrylic", "اکریلیک دائم"
        REMOVABLE_ACRYLIC = "removable_acrylic", "اکریلیک قابل جداسازی"
        HOTMELT = "hotmelt", "هات‌ملت"

    category = models.ForeignKey(
        Category,
        verbose_name="دسته‌بندی",
        on_delete=models.PROTECT,
        related_name="products",
    )
    subcategory = models.ForeignKey(
        "Category.Subcategory",
        verbose_name="زیردسته‌بندی",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="products",
        help_text="اختیاری؛ باید یکی از زیردسته‌های همین دسته‌بندی باشد (مثلاً زیر ونکال: PP, PVC, PET, کاغذی).",
    )
    name = models.CharField("نام محصول", max_length=150)
    name_en = models.CharField("نام محصول (انگلیسی)", max_length=150, blank=True)
    slug = models.SlugField("اسلاگ", max_length=100, allow_unicode=True, blank=True, unique=True, help_text=SLUG_HELP)
    face_material = models.CharField("جنس رویه", max_length=50, blank=True)
    face_material_en = models.CharField("جنس رویه (انگلیسی)", max_length=50, blank=True)
    face_value = models.PositiveSmallIntegerField("مقدار رویه", null=True, blank=True)
    face_unit = models.CharField(
        "واحد رویه", max_length=10, choices=FaceUnit.choices, default=FaceUnit.MICRON
    )
    liner_gsm = models.PositiveSmallIntegerField("گرماژ لاینر", null=True, blank=True)
    adhesive = models.CharField(
        "نوع چسب", max_length=20, choices=Adhesive.choices, blank=True
    )
    width_107 = models.CharField(
        "عرض 1/07 متر", max_length=50, blank=True, null=True
    )
    width_127 = models.CharField(
        "عرض 1/27 متر", max_length=50, blank=True, null=True
    )
    width_152 = models.CharField(
        "عرض 1/52 متر", max_length=50, blank=True, null=True
    )
    # منسوخ: مشخصات ونلایت حالا فقط روی مدل Vanlite نگه‌داری و ویرایش می‌شود (پنل و سایت هر دو از آن می‌خوانند).
    # این ستون‌ها فقط برای حفظ داده‌های قدیمی مانده‌اند (مایگریشن 0016 مقدارشان را به Vanlite منتقل کرده)
    # و دیگر در پنل ویرایش یا در سایت نمایش داده نمی‌شوند. بعد از اطمینان از انتقال می‌شود حذفشان کرد.
    durability_years = models.PositiveSmallIntegerField(
        "دوام (سال)", null=True, blank=True, help_text="منسوخ؛ از ردیف‌های ونلایت استفاده کنید."
    )
    colors = models.CharField(
        "رنگ‌ها", max_length=200, blank=True, help_text="منسوخ؛ از ردیف‌های ونلایت استفاده کنید."
    )
    colors_en = models.CharField("رنگ‌ها (انگلیسی)", max_length=200, blank=True)
    roll_size = models.CharField(
        "ابعاد رول (متر)", max_length=40, blank=True, help_text="منسوخ؛ از ردیف‌های ونلایت استفاده کنید."
    )
    description = models.TextField("توضیحات", blank=True)
    description_en = models.TextField("توضیحات (انگلیسی)", blank=True)
    order = models.PositiveSmallIntegerField("ترتیب نمایش", default=0)

    class Meta(BaseModel.Meta):
        verbose_name = "محصول"
        verbose_name_plural = "محصولات"
        ordering = ["category__order", "order", "name"]

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        base = self.slug or make_slug(self.name, fallback="product")
        self.slug = unique_slug(Product, base, pk=self.pk)
        super().save(*args, **kwargs)

    def clean(self):
        super().clean()
        if self.subcategory_id and self.subcategory.category_id != self.category_id:
            raise ValidationError(
                {"subcategory": "این زیردسته‌بندی متعلق به دسته‌بندی انتخاب‌شده نیست."}
            )

    @property
    def display_name(self):
        return self.localized("name")

    @property
    def display_description(self):
        return self.localized("description")

    @property
    def display_face_material(self):
        return self.localized("face_material")

    @property
    def display_colors(self):
        return self.localized("colors")

    def get_absolute_url(self):
        return reverse("Product:detail", kwargs={"slug": self.slug})


class Vanlite(BaseModel):
    """ونلایت (شبرنگ EGP / HIP): بخش کاملاً جدا از مشخصات محصول، با دو بخش فارسی و انگلیسی.
    هر ردیف یک نوع/کد از یک محصول است؛ مقدار انگلیسیِ خالی در سایت با فارسی جایگزین می‌شود."""

    product = models.ForeignKey(
        Product, verbose_name="محصول", on_delete=models.CASCADE, related_name="vanlite_items"
    )
    # --- فارسی
    name = models.CharField("نام محصول", max_length=150)
    type = models.CharField("نوع", max_length=60, blank=True, help_text="مثلاً EGP یا HIP")
    roll_size = models.CharField("رول سایز", max_length=40, blank=True, help_text="مثلاً: 1.22 × 45.7")
    durability_years = models.PositiveSmallIntegerField("دوام (سال)", null=True, blank=True)
    colors = models.CharField("رنگ‌ها", max_length=200, blank=True, help_text="مثلاً: سفید - قرمز - سبز")
    product_code = models.CharField("کد محصول", max_length=60, blank=True)
    # --- English
    name_en = models.CharField("Product name", max_length=150, blank=True)
    type_en = models.CharField("Type", max_length=60, blank=True)
    roll_size_en = models.CharField("Roll size", max_length=40, blank=True)
    durability_years_en = models.PositiveSmallIntegerField("Durability (years)", null=True, blank=True)
    colors_en = models.CharField("Colors", max_length=200, blank=True)
    product_code_en = models.CharField("Product code", max_length=60, blank=True)
    order = models.PositiveSmallIntegerField("ترتیب نمایش", default=0)

    class Meta(BaseModel.Meta):
        verbose_name = "ونلایت"
        verbose_name_plural = "ونلایت (Vanlite)"
        ordering = ["order", "name"]

    def __str__(self):
        return f"{self.name} {self.product_code}".strip()

    @property
    def display_name(self):
        return self.localized("name")

    @property
    def display_type(self):
        return self.localized("type")

    @property
    def display_roll_size(self):
        return self.localized("roll_size")

    @property
    def display_colors(self):
        return self.localized("colors")

    @property
    def display_product_code(self):
        return self.localized("product_code")

    @property
    def display_durability_years(self):
        if (get_language() or "fa")[:2] == "en" and self.durability_years_en:
            return self.durability_years_en
        return self.durability_years
