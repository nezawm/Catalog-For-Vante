import secrets

from django.db import models, transaction
from django.db.models import F
from django.db.models.signals import post_delete
from django.dispatch import receiver
from django.utils import timezone
from django.utils.translation import get_language

from .validators import validate_catalog_pdf


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


def catalog_upload_to(instance, filename):
    stamp = timezone.localtime().strftime("%Y%m%d-%H%M%S")
    return f"catalogs/vante-catalog-{instance.language}-{stamp}.pdf"


class CatalogFile(BaseModel):
    """فایل PDF کاتالوگ برای هر زبان سایت (یک ردیف برای فارسی، یک ردیف برای انگلیسی)."""

    class Language(models.TextChoices):
        FA = "fa", "فارسی"
        EN = "en", "English"

    language = models.CharField("زبان", max_length=2, choices=Language.choices, unique=True)
    file = models.FileField(
        "فایل PDF کاتالوگ",
        upload_to=catalog_upload_to,
        max_length=200,
        validators=[validate_catalog_pdf],
    )
    download_count = models.PositiveIntegerField("تعداد دانلود", default=0, editable=False)

    class Meta(BaseModel.Meta):
        verbose_name = "کاتالوگ PDF"
        verbose_name_plural = "کاتالوگ‌های PDF"
        ordering = ["language"]

    def __str__(self):
        return "کاتالوگ فارسی" if self.language == self.Language.FA else "کاتالوگ انگلیسی (English)"

    @property
    def download_filename(self):
        return f"Vante-Catalog-{self.language}.pdf"

    @property
    def size(self):
        try:
            return self.file.size
        except (OSError, ValueError):
            return None

    def record_download(self):
        # با F تا دانلودهای همزمان گم نشوند؛ update باعث تغییر «تاریخ ویرایش» نمی‌شود.
        type(self).objects.filter(pk=self.pk).update(download_count=F("download_count") + 1)

    def save(self, *args, **kwargs):
        old_name = ""
        if self.pk:
            old_name = type(self).objects.filter(pk=self.pk).values_list("file", flat=True).first() or ""
        super().save(*args, **kwargs)
        if old_name and old_name != self.file.name:
            # فایل قدیمی فقط بعد از قطعی‌شدن تراکنش پاک می‌شود؛ اگر تراکنش برگردد، رکورد قدیمی و فایلش سالم می‌مانند.
            storage = self.file.storage
            transaction.on_commit(lambda: storage.delete(old_name))


@receiver(post_delete, sender=CatalogFile)
def _delete_catalog_file(sender, instance, **kwargs):
    if instance.file:
        # حذف فایل بعد از قطعی‌شدن حذف رکورد؛ در رولبک فایل می‌ماند.
        storage, name = instance.file.storage, instance.file.name
        transaction.on_commit(lambda: storage.delete(name))



# ---------------------------------------------------------------- QR و آمار بازدید

def make_qr_code():
    return secrets.token_urlsafe(6).replace("_", "x").replace("-", "y")[:8].lower()


class QRCode(BaseModel):
    """یک QR قابل چاپ؛ QR به آدرس کوتاه /q/<code>/ اشاره می‌کند، اسکن را می‌شمارد و به مقصد می‌رود.
    چون خودِ QR عوض نمی‌شود، می‌شود مقصد را بعد از چاپ هم تغییر داد."""

    TARGETS = [
        ("/fa/", "سایت فارسی"),
        ("/en/", "سایت انگلیسی (English)"),
        ("/fa/categories/", "کاتالوگ آنلاین فارسی"),
        ("/en/categories/", "کاتالوگ آنلاین انگلیسی"),
        ("/catalog/fa/", "دانلود مستقیم PDF فارسی"),
        ("/catalog/en/", "دانلود مستقیم PDF انگلیسی"),
    ]

    name = models.CharField("نام QR", max_length=80, help_text="مثلاً «بنر نمایشگاه» یا «کارت ویزیت»")
    code = models.CharField("کد", max_length=12, unique=True, default=make_qr_code, editable=False)
    target = models.CharField("مقصد", max_length=60, choices=TARGETS, default="/fa/")

    class Meta(BaseModel.Meta):
        verbose_name = "کد QR"
        verbose_name_plural = "کدهای QR"

    def __str__(self):
        return self.name


class QRScan(models.Model):
    qr = models.ForeignKey(QRCode, on_delete=models.CASCADE, related_name="scans", verbose_name="QR")
    scanned_at = models.DateTimeField("زمان اسکن", auto_now_add=True, db_index=True)
    device_type = models.CharField("نوع دستگاه", max_length=10, blank=True)
    device_model = models.CharField("مدل دستگاه", max_length=60, blank=True)
    os = models.CharField("سیستم‌عامل", max_length=30, blank=True)
    browser = models.CharField("مرورگر", max_length=30, blank=True)
    visitor = models.CharField("شناسه ناشناس", max_length=16, blank=True, db_index=True)

    class Meta:
        ordering = ["-scanned_at"]
        verbose_name = "اسکن QR"
        verbose_name_plural = "اسکن‌های QR"


class DailyVisit(models.Model):
    """شمارندهٔ روزانهٔ بازدید صفحات سایت (بدون ربات‌ها)؛ هر روز یک ردیف برای هر زبان."""

    date = models.DateField("تاریخ", db_index=True)
    lang = models.CharField("زبان", max_length=2)
    views = models.PositiveIntegerField("بازدید", default=0)
    visitors = models.PositiveIntegerField("بازدیدکنندهٔ یکتا", default=0)

    class Meta:
        unique_together = [("date", "lang")]
        ordering = ["-date"]
        verbose_name = "بازدید روزانه"
        verbose_name_plural = "بازدیدهای روزانه"


class LoginAttempt(models.Model):
    """لاگ تلاش‌های ورود به پنل مدیریت و ادمین جنگو (موفق و ناموفق)."""

    created_at = models.DateTimeField("زمان", auto_now_add=True, db_index=True)
    username = models.CharField("نام کاربری واردشده", max_length=150, blank=True, db_index=True)
    success = models.BooleanField("موفق", default=False, db_index=True)
    source = models.CharField("بخش", max_length=10, blank=True)
    ip = models.GenericIPAddressField("آی‌پی", null=True, blank=True, db_index=True)
    device_type = models.CharField("نوع دستگاه", max_length=10, blank=True)
    device_model = models.CharField("مدل دستگاه", max_length=60, blank=True)
    os = models.CharField("سیستم‌عامل", max_length=30, blank=True)
    browser = models.CharField("مرورگر", max_length=30, blank=True)
    user_agent = models.CharField("User-Agent", max_length=500, blank=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "تلاش ورود"
        verbose_name_plural = "تلاش‌های ورود"
