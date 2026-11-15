import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("Category", "0001_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="Subcategory",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("created_at", models.DateTimeField(auto_now_add=True, verbose_name="تاریخ ایجاد")),
                ("updated_at", models.DateTimeField(auto_now=True, verbose_name="تاریخ ویرایش")),
                ("is_active", models.BooleanField(default=True, verbose_name="فعال")),
                ("name", models.CharField(max_length=100, verbose_name="نام")),
                ("slug", models.SlugField(allow_unicode=True, verbose_name="اسلاگ")),
                ("description", models.TextField(blank=True, verbose_name="توضیحات")),
                ("order", models.PositiveSmallIntegerField(default=0, verbose_name="ترتیب نمایش")),
                ("category", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="subcategories", to="Category.category", verbose_name="دسته\u200cبندی اصلی")),
            ],
            options={
                "verbose_name": "زیردسته\u200cبندی",
                "verbose_name_plural": "زیردسته\u200cبندی\u200cها",
                "ordering": ["category__order", "order", "name"],
                "abstract": False,
                "constraints": [models.UniqueConstraint(fields=("category", "slug"), name="unique_subcategory_slug_per_category")],
            },
        ),
    ]
