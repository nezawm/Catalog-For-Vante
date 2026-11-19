from django.core.exceptions import ValidationError

MAX_CATALOG_MB = 50


def validate_catalog_pdf(file):
    """فقط PDF واقعی (پسوند + امضای %PDF) و حداکثر ۵۰ مگابایت. فایل‌هایی که قبلاً ذخیره شده‌اند دوباره بررسی نمی‌شوند."""
    if getattr(file, "_committed", False):
        return
    name = (getattr(file, "name", "") or "").lower()
    if not name.endswith(".pdf"):
        raise ValidationError("فقط فایل PDF قابل قبول است.")
    if file.size > MAX_CATALOG_MB * 1024 * 1024:
        raise ValidationError(f"حجم فایل نباید بیشتر از {MAX_CATALOG_MB} مگابایت باشد.")
    file.seek(0)
    head = file.read(5)
    file.seek(0)
    if head != b"%PDF-":
        raise ValidationError("این فایل یک PDF معتبر نیست.")
