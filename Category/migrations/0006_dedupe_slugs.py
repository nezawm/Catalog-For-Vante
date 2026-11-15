from django.db import migrations


def _unique(base, taken):
    slug, number = base, 2
    while slug in taken:
        suffix = f"-{number}"
        slug = base[: 100 - len(suffix)] + suffix
        number += 1
    taken.add(slug)
    return slug


def dedupe(apps, schema_editor):
    Category = apps.get_model("Category", "Category")
    Subcategory = apps.get_model("Category", "Subcategory")
    taken = set()
    for obj in Category.objects.order_by("pk"):
        slug = _unique(obj.slug or "category", taken)
        if slug != obj.slug:
            Category.objects.filter(pk=obj.pk).update(slug=slug)
    taken_by_category = {}
    for obj in Subcategory.objects.order_by("pk"):
        taken = taken_by_category.setdefault(obj.category_id, set())
        slug = _unique(obj.slug or "subcategory", taken)
        if slug != obj.slug:
            Subcategory.objects.filter(pk=obj.pk).update(slug=slug)


class Migration(migrations.Migration):
    """قبل از یکتا کردن اسلاگ‌ها، اسلاگ‌های تکراری با «-2»، «-3» و ... اصلاح می‌شوند."""

    dependencies = [
        ("Category", "0005_slug_blank_auto"),
    ]

    operations = [
        migrations.RunPython(dedupe, migrations.RunPython.noop),
    ]
