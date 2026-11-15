from django.db import migrations, models


class Migration(migrations.Migration):
    """اسلاگ دیگر یکتا نیست (آدرس‌ها «اسلاگ-id» هستند)."""

    dependencies = [
        ("Category", "0003_set_catalog_order"),
    ]

    operations = [
        migrations.RemoveConstraint(
            model_name="subcategory",
            name="unique_subcategory_slug_per_category",
        ),
        migrations.AlterField(
            model_name="category",
            name="slug",
            field=models.SlugField(allow_unicode=True, max_length=100, verbose_name="اسلاگ"),
        ),
        migrations.AlterField(
            model_name="subcategory",
            name="slug",
            field=models.SlugField(allow_unicode=True, max_length=100, verbose_name="اسلاگ"),
        ),
    ]
