from django.db import migrations


def copy_product_vanlite_data(apps, schema_editor):
    """رنگ، ابعاد رول و دوامی که قبلاً از پنل روی خود Product ذخیره شده بود به یک ردیف Vanlite منتقل می‌شود
    تا در سایت دیده شود. فقط برای محصولی که هنوز هیچ ردیف Vanlite ندارد؛ ردیف‌های موجود هرگز دست نمی‌خورند.
    ستون‌های قدیمی Product پاک نمی‌شوند، پس هیچ اطلاعاتی از بین نمی‌رود."""
    Product = apps.get_model("Product", "Product")
    Vanlite = apps.get_model("Product", "Vanlite")
    candidates = Product.objects.filter(vanlite_items__isnull=True).exclude(
        durability_years__isnull=True, colors="", colors_en="", roll_size=""
    )
    for product in candidates:
        Vanlite.objects.create(
            product=product,
            name=product.name,
            name_en=product.name_en,
            roll_size=product.roll_size,
            durability_years=product.durability_years,
            colors=product.colors,
            colors_en=product.colors_en,
            is_active=True,
        )


class Migration(migrations.Migration):

    dependencies = [
        ("Product", "0015_vanlite_colors"),
    ]

    operations = [
        migrations.RunPython(copy_product_vanlite_data, migrations.RunPython.noop),
    ]
