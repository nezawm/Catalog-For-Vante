from django.db import migrations

# ترجمهٔ اولیهٔ نام محصولات موجود؛ فقط فیلدهای خالی پر می‌شوند. در ادمین قابل ویرایش است.
NAMES = {
    "PVC سفید براق": "PVC glossy white",
    "PVC شفاف براق": "PVC glossy clear",
    "PP سفید صدفی براق": "PP glossy pearl white",
    "PET متالایز نقره ای براق": "PET glossy metalized silver",
    "گلاسه سفید براق استاندارد": "Coated glossy white - standard",
    "گلاسه سفید براق پرمیوم": "Coated glossy white - premium",
    "سفید براق": "Glossy white",
    "شفاف براق": "Glossy clear",
    "سفید مات": "Matte white",
    "شفاف مات": "Matte clear",
    "رول چسب دو طرفه Elite": "Double-sided tape roll Elite",
}

_PVC_NOTE = (
    "PVC sheets with permanent acrylic adhesive. The glossy white model is available for solvent, eco-solvent "
    "and UV printing, and the glossy clear models are available for solvent and eco-solvent printing. "
    "The specifications of each model are the same in both sizes."
)

# کلید: توضیحات فارسی با فاصله‌های یکدست‌شده (" ".join(text.split()))
DESCRIPTIONS = {
    "۱۰۰ × ۷۰ · GW-0114 ۵۱ × ۷۰ · GW-0208 شیت های PVC چسب اکریلیک دائم دارند مدل سفید براق برای چاپ سالونت،اکوسالونت و UV و مدل های شفاف براق برای چاپ سالونت و الکوسالونت معرفی شده است. مشخصات هر مدل در هر دو سایز یکسان است":
        "100 × 70 · GW-0114\r\n51 × 70 · GW-0208\r\n\r\n" + _PVC_NOTE,
    "۱۰۰ × ۷۰ · GT-0727 ۵۱ × ۷۰ · GT-0823 شیت های PVC چسب اکریلیک دائم دارند مدل سفید براق برای چاپ سالونت،اکوسالونت و UV و مدل های شفاف براق برای چاپ سالونت و الکوسالونت معرفی شده است. مشخصات هر مدل در هر دو سایز یکسان است":
        "100 × 70 · GT-0727\r\n51 × 70 · GT-0823\r\n\r\n" + _PVC_NOTE,
    "۵۱ × ۷۰ · PSP-21105": "51 × 70 · PSP-21105",
    "۵۱ × ۷۰ · PMTT-30522": "51 × 70 · PMTT-30522",
    "۵۱ × ۷۰ · GP- 10801": "51 × 70 · GP-10801",
    "۵۱ × ۷۰ · GP-11004": "51 × 70 · GP-11004",
    "سطح سفید براق در دو ضخامت برای گرافیک تبلیغاتی چاپی": "Glossy white surface in two thicknesses for printed advertising graphics",
    "قیلم شفاف برای گرافیک روی شیشه و سطوح شفاف": "Clear film for graphics on glass and transparent surfaces",
    "رویه سفید با بازتاب سطحی کم برای کاربرد هایی که فینیش مات میخواهند": "White face with low surface reflection, for applications that need a matte finish",
    "کدمحصول DST-70423": "Product code DST-70423",
}


def prefill(apps, schema_editor):
    Product = apps.get_model("Product", "Product")
    for obj in Product.objects.filter(name_en=""):
        english = NAMES.get(" ".join(obj.name.split()))
        if english:
            Product.objects.filter(pk=obj.pk).update(name_en=english)
    for obj in Product.objects.filter(description_en="").exclude(description=""):
        english = DESCRIPTIONS.get(" ".join(obj.description.split()))
        if english:
            Product.objects.filter(pk=obj.pk).update(description_en=english)


class Migration(migrations.Migration):

    dependencies = [
        ("Product", "0010_english_fields"),
    ]

    operations = [
        migrations.RunPython(prefill, migrations.RunPython.noop),
    ]
