from django.db import migrations, models


class Migration(migrations.Migration):
    """اسلاگ می‌تواند خالی بماند و هنگام ذخیره خودکار (انگلیسی) ساخته می‌شود."""

    dependencies = [
        ("Category", "0004_slug_with_id"),
    ]

    operations = [
        migrations.AlterField(
            model_name="category",
            name="slug",
            field=models.SlugField(allow_unicode=True, blank=True, help_text="خالی بگذارید تا خودکار از نام، به انگلیسی ساخته شود", max_length=100, verbose_name="اسلاگ"),
        ),
        migrations.AlterField(
            model_name="subcategory",
            name="slug",
            field=models.SlugField(allow_unicode=True, blank=True, help_text="خالی بگذارید تا خودکار از نام، به انگلیسی ساخته شود", max_length=100, verbose_name="اسلاگ"),
        ),
    ]
