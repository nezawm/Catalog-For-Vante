from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("Product", "0004_product_subcategory"),
    ]

    operations = [
        migrations.AlterField(
            model_name="product",
            name="slug",
            field=models.SlugField(allow_unicode=True, max_length=100, verbose_name="اسلاگ"),
        ),
    ]
