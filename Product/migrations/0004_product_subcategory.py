import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("Category", "0002_subcategory"),
        ("Product", "0003_alter_product_width_107_alter_product_width_127_and_more"),
    ]

    operations = [
        migrations.AddField(
            model_name="product",
            name="subcategory",
            field=models.ForeignKey(
                blank=True,
                help_text="اختیاری؛ باید یکی از زیردسته‌های همین دسته‌بندی باشد (مثلاً زیر ونکال: PP, PVC, PET, کاغذی).",
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="products",
                to="Category.subcategory",
                verbose_name="زیردسته‌بندی",
            ),
        ),
    ]
