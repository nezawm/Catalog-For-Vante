import Core.models
import Core.validators
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="CatalogFile",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("created_at", models.DateTimeField(auto_now_add=True, verbose_name="تاریخ ایجاد")),
                ("updated_at", models.DateTimeField(auto_now=True, verbose_name="تاریخ ویرایش")),
                ("is_active", models.BooleanField(default=True, verbose_name="فعال")),
                ("language", models.CharField(choices=[("fa", "فارسی"), ("en", "English")], max_length=2, unique=True, verbose_name="زبان")),
                ("file", models.FileField(max_length=200, upload_to=Core.models.catalog_upload_to, validators=[Core.validators.validate_catalog_pdf], verbose_name="فایل PDF کاتالوگ")),
                ("download_count", models.PositiveIntegerField(default=0, editable=False, verbose_name="تعداد دانلود")),
            ],
            options={
                "verbose_name": "کاتالوگ PDF",
                "verbose_name_plural": "کاتالوگ‌های PDF",
                "ordering": ["language"],
                "abstract": False,
            },
        ),
    ]
