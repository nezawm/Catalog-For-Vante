from django.db import migrations

# ترجمهٔ اولیه برای داده‌های موجود؛ فقط فیلدهای خالی پر می‌شوند. در ادمین قابل ویرایش است.
CATEGORY_TITLES = {
    "Vancal": "Self-adhesive sheets",
    "Vanjet": "Self-adhesive vinyl rolls",
    "Vanguard": "Lamination rolls",
    "Vanfix": "Double-sided tape",
    "Vanlite": "Reflective sheeting EGP & HIP",
}
CATEGORY_DESCRIPTIONS = {
    "Vanguard": (
        "Clear PVC film for covering and protecting surfaces. The glossy finish has a brighter shine, "
        "and the matte finish reduces surface reflection.\r\n----------\r\n"
        "Common specifications: roll length 50 m, permanent clear acrylic adhesive and 100 g/m² white paper liner."
    ),
    "Vanjet": (
        "Self-adhesive vinyl roll\r\nPrintable PVC film for indoor and outdoor advertising graphics. "
        "The models are compatible with wide-format solvent and eco-solvent printers.\r\n----------\r\n"
        "Common specifications: roll length 50 m, removable clear acrylic adhesive and 140 g/m² white paper liner."
    ),
    "Vancal": "Self-adhesive sheets, printable vinyl, cold lamination and double-sided tape",
    "Vanfix": (
        "---------- For inquiries and orders, send the product code and the required quantity "
        "to the Vante sales department. Double-sided tape roll"
    ),
}
SUBCATEGORY_NAMES = {"PVC": "PVC", "PET": "PET", "PP": "PP", "کاغذی": "Paper"}


def prefill(apps, schema_editor):
    Category = apps.get_model("Category", "Category")
    Subcategory = apps.get_model("Category", "Subcategory")
    for obj in Category.objects.filter(title_en=""):
        english = CATEGORY_TITLES.get(obj.name.strip())
        if english:
            Category.objects.filter(pk=obj.pk).update(title_en=english)
    for obj in Category.objects.filter(description_en=""):
        english = CATEGORY_DESCRIPTIONS.get(obj.name.strip())
        if english:
            Category.objects.filter(pk=obj.pk).update(description_en=english)
    for obj in Subcategory.objects.filter(name_en=""):
        english = SUBCATEGORY_NAMES.get(obj.name.strip())
        if english:
            Subcategory.objects.filter(pk=obj.pk).update(name_en=english)


class Migration(migrations.Migration):

    dependencies = [
        ("Category", "0008_english_fields"),
    ]

    operations = [
        migrations.RunPython(prefill, migrations.RunPython.noop),
    ]
