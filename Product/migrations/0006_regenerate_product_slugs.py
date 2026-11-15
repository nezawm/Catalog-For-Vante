import re

from django.db import migrations

# اسلاگ‌های قبلی (مثل pvc-sfd-brk) ترجمهٔ حرف‌به‌حرف و ناخوانا بودند؛ اینجا از نام محصول دوباره ساخته می‌شوند.
WORDS = {
    "سفید": "white", "شفاف": "clear", "براق": "glossy", "مات": "matte",
    "صدفی": "pearl", "متالایز": "metalized", "نقره": "silver", "نقره‌ای": "silver", "ای": "",
    "گلاسه": "coated", "استاندارد": "standard", "پرمیوم": "premium",
    "رول": "roll", "چسب": "tape", "دو": "double", "طرفه": "sided", "دوطرفه": "double-sided",
}


def make_slug(name):
    parts = []
    for token in re.split(r"[\s\u200c]+", name.strip()):
        token = WORDS.get(token, token)
        if token:
            parts.append(token)
    text = "-".join(parts).lower()
    text = re.sub(r"[^\w-]+", "-", text)
    return re.sub(r"-{2,}", "-", text).strip("-")


def regenerate(apps, schema_editor):
    Product = apps.get_model("Product", "Product")
    for product in Product.objects.all():
        product.slug = make_slug(product.name) or "product"
        product.save(update_fields=["slug"])


class Migration(migrations.Migration):

    dependencies = [
        ("Product", "0005_alter_product_slug"),
    ]

    operations = [
        migrations.RunPython(regenerate, migrations.RunPython.noop),
    ]
