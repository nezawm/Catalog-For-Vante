from django.db import models
from django.utils.translation import get_language


class BaseModel(models.Model):
    """مدل انتزاعی پایه؛ همهٔ مدل‌های ماژول‌های دیگر از این ارث می‌برند."""

    created_at = models.DateTimeField("تاریخ ایجاد", auto_now_add=True)
    updated_at = models.DateTimeField("تاریخ ویرایش", auto_now=True)
    is_active = models.BooleanField("فعال", default=True)

    class Meta:
        abstract = True
        ordering = ["-created_at"]
        ordering = ["-created_at"]

    def localized(self, field):
        """مقدار فیلد به زبان فعلی؛ در انگلیسی اگر «<field>_en» پر باشد همان، وگرنه فارسی (پیش‌فرض)."""
        if (get_language() or "fa")[:2] == "en":
            value = getattr(self, f"{field}_en", "")
            if value:
                return value
        return getattr(self, field)
