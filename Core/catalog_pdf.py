"""تولید خودکار PDF کاتالوگ از روی محصولات و دسته‌بندی‌های دیتابیس (فارسی/انگلیسی)."""
import re
from datetime import date

from django.conf import settings
from django.template.loader import render_to_string
from django.utils import translation

from Category.models import Category
from Product.models import Product

from .translations import TRANSLATIONS

SEPARATOR = re.compile(r"^\s*-{3,}\s*$", re.M)

EXTRA = {
    "fa": {
        "contents": "فهرست",
        "common": "مشخصات مشترک و توضیحات",
        "pdf_title": "کاتالوگ محصولات",
        "page": "صفحه",
        "other": "سایر محصولات",
    },
    "en": {
        "contents": "Contents",
        "common": "Common specifications & notes",
        "pdf_title": "Product Catalog",
        "page": "Page",
        "other": "Other products",
    },
}


def _split_description(text):
    """متن دسته: قبل از خط «----------» توضیح اصلی، بعدش مشخصات مشترک/یادداشت."""
    text = (text or "").replace("\r\n", "\n").strip()
    parts = [p.strip() for p in SEPARATOR.split(text, maxsplit=1)]
    # در دادهٔ فعلی گاهی جداکننده داخل یک خط است: «---------- متن»
    if len(parts) == 1 and "----------" in text:
        head, _, tail = text.partition("----------")
        parts = [head.strip(), tail.strip(" -\n")]
    intro = parts[0]
    note = parts[1] if len(parts) > 1 else ""
    return intro, note


def _product_rows(product, labels):
    rows = []
    if product.display_face_material:
        rows.append((labels["face_material"], product.display_face_material, False))
    if product.face_value:
        unit = labels.get(f"unit_{product.face_unit}", product.face_unit)
        rows.append((labels["face"], f"{product.face_value} {unit}", False))
    if product.liner_gsm:
        rows.append((labels["liner"], f"{product.liner_gsm} {labels['liner_unit']}", False))
    if product.adhesive:
        rows.append((labels["adhesive"], labels.get(f"adhesive_{product.adhesive}", product.adhesive), False))
    # ونلایت: فقط از ردیف‌های Vanlite (همان منبعی که پنل و سایت استفاده می‌کنند)؛ ستون‌های منسوخ Product خوانده نمی‌شوند.
    for item in (v for v in product.vanlite_items.all() if v.is_active):
        tag = f" ({item.display_product_code})" if item.display_product_code else ""
        if item.display_durability_years:
            rows.append((labels["durability"] + tag, f"{item.display_durability_years} {labels['durability_unit']}", False))
        if item.display_colors:
            rows.append((labels["colors"] + tag, item.display_colors, False))
        if item.display_roll_size:
            rows.append((labels["roll_size"] + tag, f"{item.display_roll_size} {labels['roll_unit']}", False))
    for field in ("width_107", "width_127", "width_152"):
        value = (getattr(product, field) or "").strip()
        if value and set(value) != {"-"}:
            rows.append((labels[field], value, True))  # True = کد لاتین، چپ‌به‌راست
    return rows


def _card(product, labels):
    return {
        "name": product.display_name,
        "face": (
            f"{product.face_value} {labels.get('unit_' + product.face_unit, product.face_unit)}"
            if product.face_value else ""
        ),
        "rows": _product_rows(product, labels),
        "description": (product.display_description or "").replace("\r\n", "\n").strip(),
    }


def _build_context(lang):
    labels = {**TRANSLATIONS[lang], **EXTRA[lang]}
    products = (
        Product.objects.filter(is_active=True, category__is_active=True)
        .select_related("category", "subcategory")
        .prefetch_related("vanlite_items")
        .order_by("category__order", "category__name", "subcategory__order", "subcategory__name", "order", "name")
    )
    by_category = {}
    for product in products:
        by_category.setdefault(product.category_id, []).append(product)

    sections = []
    for category in Category.objects.filter(is_active=True).order_by("order", "name"):
        items = by_category.get(category.pk)
        if not items:
            continue
        groups = {}
        for product in items:
            sub = product.subcategory if product.subcategory and product.subcategory.is_active else None
            groups.setdefault(sub.pk if sub else None, {"sub": sub, "cards": []})["cards"].append(_card(product, labels))
        # زیردسته‌ها اول، «سایر محصولات» آخر
        ordered = sorted(groups.values(), key=lambda g: (g["sub"] is None, g["sub"].order if g["sub"] else 0))
        intro, note = _split_description(category.display_description)
        sections.append(
            {
                "anchor": f"cat-{category.pk}",
                "name": category.name,
                "title": category.display_title,
                "intro": intro,
                "note": note,
                "groups": [
                    {
                        "title": g["sub"].display_name if g["sub"] else (labels["other"] if len(ordered) > 1 else ""),
                        "text": g["sub"].display_description if g["sub"] else "",
                        "cards": g["cards"],
                    }
                    for g in ordered
                ],
                "count": len(items),
            }
        )

    static = settings.BASE_DIR / "static" / "Core"
    return {
        "lang": lang,
        "rtl": lang == "fa",
        "labels": labels,
        "sections": sections,
        "year": date.today().year,
        "font_dir": (static / "fonts").as_uri(),
        "logo_url": (static / "img" / "vante-logo.svg").as_uri(),
    }


def build_catalog_pdf(lang):
    """PDF کاتالوگ را برای زبان داده‌شده می‌سازد و بایت‌ها را برمی‌گرداند."""
    from weasyprint import HTML  # import تنبل: فقط وقتی PDF ساخته می‌شود لازم است

    if lang not in TRANSLATIONS:
        raise ValueError(f"زبان نامعتبر: {lang}")
    with translation.override(lang):
        html = render_to_string("Core/catalog_pdf.html", _build_context(lang))
    return HTML(string=html, base_url=str(settings.BASE_DIR)).write_pdf()
