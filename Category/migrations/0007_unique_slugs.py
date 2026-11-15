from django.db import migrations, models


class Migration(migrations.Migration):
    """اسلاگ دسته‌بندی یکتاست و اسلاگ زیردسته داخل هر دسته‌بندی یکتاست (آدرس بدون id)."""

    dependencies = [
        ("Category", "0006_dedupe_slugs"),
    ]

    operations = [
        migrations.AlterField(
            model_name="category",
            name="slug",
            field=models.SlugField(allow_unicode=True, blank=True, help_text="خالی بگذارید تا خودکار از نام، به انگلیسی ساخته شود", max_length=100, unique=True, verbose_name="اسلاگ"),
        ),
        migrations.AddConstraint(
            model_name="subcategory",
            constraint=models.UniqueConstraint(fields=("category", "slug"), name="unique_subcategory_slug_per_category"),
        ),
    ]
