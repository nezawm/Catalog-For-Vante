from django.db import models

# Create your models here.
from django.db import models
from django.urls import reverse

from Core.models import BaseModel
from Core.slugs import SLUG_HELP, make_slug, unique_slug


class Category(BaseModel):
    name = models.CharField("نام لاتین", max_length=100)
    title = models.CharField("عنوان", max_length=150)
    title_en = models.CharField("عنوان (انگلیسی)", max_length=150, blank=True)
    slug = models.SlugField("اسلاگ", max_length=100, allow_unicode=True, blank=True, unique=True, help_text=SLUG_HELP)
    description = models.TextField("توضیحات", blank=True)
    description_en = models.TextField("توضیحات (انگلیسی)", blank=True)
    order = models.PositiveSmallIntegerField("ترتیب نمایش", default=0)

    class Meta(BaseModel.Meta):
        verbose_name = "دسته‌بندی"
        verbose_name_plural = "دسته‌بندی‌ها"
        ordering = ["order", "name"]

    def __str__(self):
        return f"{self.name} - {self.title}"

    def save(self, *args, **kwargs):
        base = self.slug or make_slug(self.name, fallback="category")
        self.slug = unique_slug(Category, base, pk=self.pk)
        super().save(*args, **kwargs)

    @property
    def display_title(self):
        return self.localized("title")

    @property
    def display_description(self):
        return self.localized("description")

    def get_absolute_url(self):
        return reverse("Category:detail", kwargs={"slug": self.slug})


class Subcategory(BaseModel):
    """زیردسته‌بندی؛ مثلاً زیر «ونکال»: PP، PVC، PET، کاغذی."""

    category = models.ForeignKey(
        Category,
        verbose_name="دسته‌بندی اصلی",
        on_delete=models.CASCADE,
        related_name="subcategories",
    )
    name = models.CharField("نام", max_length=100)
    name_en = models.CharField("نام (انگلیسی)", max_length=100, blank=True)
    slug = models.SlugField("اسلاگ", max_length=100, allow_unicode=True, blank=True, help_text=SLUG_HELP)
    description = models.TextField("توضیحات", blank=True)
    description_en = models.TextField("توضیحات (انگلیسی)", blank=True)
    order = models.PositiveSmallIntegerField("ترتیب نمایش", default=0)

    class Meta(BaseModel.Meta):
        verbose_name = "زیردسته‌بندی"
        verbose_name_plural = "زیردسته‌بندی‌ها"
        ordering = ["category__order", "order", "name"]
        constraints = [
            models.UniqueConstraint(
                fields=["category", "slug"], name="unique_subcategory_slug_per_category"
            )
        ]

    def __str__(self):
        return f"{self.category.name} / {self.name}"

    def save(self, *args, **kwargs):
        base = self.slug or make_slug(self.name, fallback="subcategory")
        self.slug = unique_slug(Subcategory, base, pk=self.pk, category_id=self.category_id)
        super().save(*args, **kwargs)

    @property
    def display_name(self):
        return self.localized("name")

    @property
    def display_description(self):
        return self.localized("description")

    def get_absolute_url(self):
        return reverse(
            "Category:subcategory",
            kwargs={"category_slug": self.category.slug, "slug": self.slug},
        )
