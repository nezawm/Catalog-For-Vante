from django.db import migrations

# ترتیب نمایش صفحهٔ /categories/: ردیف بالا (از راست) ونکال، ونجت، ونگارد؛ ردیف پایین ونفیکس و ونلایت
ORDER = {"vancal": 1, "vanjet": 2, "vanguard": 3, "vanfix": 4, "vanlight": 5}


def set_order(apps, schema_editor):
    Category = apps.get_model("Category", "Category")
    for slug, order in ORDER.items():
        Category.objects.filter(slug=slug).update(order=order)


class Migration(migrations.Migration):

    dependencies = [
        ("Category", "0002_subcategory"),
    ]

    operations = [
        migrations.RunPython(set_order, migrations.RunPython.noop),
    ]
