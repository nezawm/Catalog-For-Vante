from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("Product", "0008_dedupe_slugs"),
    ]

    operations = [
        migrations.AlterField(
            model_name="product",
            name="slug",
            field=models.SlugField(allow_unicode=True, blank=True, help_text="خالی بگذارید تا خودکار از نام، به انگلیسی ساخته شود", max_length=100, unique=True, verbose_name="اسلاگ"),
        ),
    ]
