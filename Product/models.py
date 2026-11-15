from django.core.exceptions import ValidationError
from django.db import models

# Create your models here.
from django.db import models
from django.urls import reverse

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

    def get_absolute_url(self):
        return reverse("Product:detail", kwargs={"slug": self.slug})