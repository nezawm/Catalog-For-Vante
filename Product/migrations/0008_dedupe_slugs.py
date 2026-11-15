from django.db import migrations


def dedupe(apps, schema_editor):
    Product = apps.get_model("Product", "Product")
    taken = set()
    for obj in Product.objects.order_by("pk"):
        base = obj.slug or "product"
        slug, number = base, 2
        while slug in taken:
            suffix = f"-{number}"
            slug = base[: 100 - len(suffix)] + suffix
            number += 1
        taken.add(slug)
        if slug != obj.slug:
            Product.objects.filter(pk=obj.pk).update(slug=slug)


class Migration(migrations.Migration):
    """قبل از یکتا کردن اسلاگ محصول، اسلاگ‌های تکراری با «-2»، «-3» و ... اصلاح می‌شوند."""

    dependencies = [
        ("Product", "0007_product_slug_blank_auto"),
    ]

    operations = [
        migrations.RunPython(dedupe, migrations.RunPython.noop),
    ]
