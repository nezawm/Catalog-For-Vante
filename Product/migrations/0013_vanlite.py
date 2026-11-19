from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("Product", "0012_vanlite_fields"),
    ]

    operations = [
        migrations.CreateModel(
            name="Vanlite",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("created_at", models.DateTimeField(auto_now_add=True, verbose_name="تاریخ ایجاد")),
                ("updated_at", models.DateTimeField(auto_now=True, verbose_name="تاریخ بروزرسانی")),
                ("is_active", models.BooleanField(default=True, verbose_name="فعال")),
                ("name", models.CharField(max_length=150, verbose_name="نام محصول")),
                ("type", models.CharField(blank=True, help_text="مثلاً EGP یا HIP", max_length=60, verbose_name="نوع")),
                ("roll_size", models.CharField(blank=True, help_text="مثلاً: 1.22 × 45.7", max_length=40, verbose_name="رول سایز")),
                ("durability_years", models.PositiveSmallIntegerField(blank=True, null=True, verbose_name="دوام (سال)")),
                ("product_code", models.CharField(blank=True, max_length=60, verbose_name="کد محصول")),
                ("name_en", models.CharField(blank=True, max_length=150, verbose_name="Product name")),
                ("type_en", models.CharField(blank=True, max_length=60, verbose_name="Type")),
                ("roll_size_en", models.CharField(blank=True, max_length=40, verbose_name="Roll size")),
                ("durability_years_en", models.PositiveSmallIntegerField(blank=True, null=True, verbose_name="Durability (years)")),
                ("product_code_en", models.CharField(blank=True, max_length=60, verbose_name="Product code")),
                ("order", models.PositiveSmallIntegerField(default=0, verbose_name="ترتیب نمایش")),
                ("product", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="vanlite_items", to="Product.product", verbose_name="محصول")),
            ],
            options={
                "verbose_name": "ونلایت",
                "verbose_name_plural": "ونلایت (Vanlite)",
                "ordering": ["order", "name"],
            },
        ),
    ]
