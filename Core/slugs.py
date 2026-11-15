"""ساخت خودکار اسلاگ انگلیسی از نام فارسی/انگلیسی.

کلمه‌های فارسی با دیکشنری WORDS به انگلیسی برگردانده می‌شوند (نه حرف‌به‌حرف، تا اسلاگ خوانا بماند).
کلمهٔ فارسی که در دیکشنری نباشد حذف می‌شود؛ کلمه‌های لاتین و عددها همان‌طور می‌مانند.
برای ترجمهٔ کلمهٔ جدید فقط یک خط به WORDS اضافه کنید (کلید را بدون نیم‌فاصله بنویسید).
"""
import re

SLUG_HELP = "خالی بگذارید تا خودکار از نام، به انگلیسی ساخته شود"

# کلمه‌های بی‌اثر که در اسلاگ نمی‌آیند
STOP_WORDS = {"و", "با", "برای", "از", "در", "به", "انواع", "ای", "های", "یا"}

WORDS = {
    # برندها / دسته‌ها
    "ونته": "vante", "ونکال": "vancal", "ونجت": "vanjet", "ونگارد": "vanguard",
    "ونفیکس": "vanfix", "ونلایت": "vanlight",
    # جنس و نوع
    "کاغذی": "paper", "کاغذ": "paper", "پلاستیکی": "plastic", "شیت": "sheet", "رول": "roll",
    "لمینت": "laminate", "وینیل": "vinyl", "شبرنگ": "reflective", "گلاسه": "coated",
    "چسب": "adhesive", "پشتچسبدار": "self-adhesive", "دوطرفه": "double-sided",
    "دو": "double", "طرفه": "sided", "چاپی": "printable", "سرد": "cold",
    "میکرون": "micron", "محصول": "product", "ملات": "melt", "هاتملت": "hotmelt", "اکریلیک": "acrylic", "دائم": "permanent",
    "قابل": "removable", "جداسازی": "", "لاینر": "liner", "رویه": "face",
    # ظاهر
    "سفید": "white", "شفاف": "clear", "مشکی": "black", "سیاه": "black", "قرمز": "red",
    "آبی": "blue", "سبز": "green", "زرد": "yellow", "نارنجی": "orange", "طلایی": "gold",
    "نقرهای": "silver", "نقره": "silver", "خاکستری": "gray", "براق": "glossy", "مات": "matte",
    "صدفی": "pearl", "متالایز": "metalized", "فلورسنت": "fluorescent", "ساتن": "satin",
    # کیفیت
    "استاندارد": "standard", "پرمیوم": "premium", "اقتصادی": "economy", "ویژه": "special",
    "معمولی": "regular", "ضخیم": "thick", "نازک": "thin",
}

_ARABIC_TO_PERSIAN = str.maketrans({"ي": "ی", "ك": "ک", "ة": "ه"})
_DIGITS = str.maketrans("۰۱۲۳۴۵۶۷۸۹٠١٢٣٤٥٦٧٨٩", "01234567890123456789")
_ZWNJ = "\u200c"
# عبارت‌های چندکلمه‌ای که باید یکجا ترجمه شوند (نیم‌فاصله و فاصله‌ها نادیده گرفته می‌شوند)
PHRASES = [
    (re.compile(r"پشت[\s\u200c]*چسب[\s\u200c]*دار"), " self-adhesive "),
    (re.compile(r"چسب[\s\u200c]*دو[\s\u200c]*طرفه"), " double-sided-tape "),
]
_PERSIAN = re.compile(r"[\u0600-\u06FF]")


def _translate(token):
    plain = token.replace(_ZWNJ, "")
    if plain in WORDS:
        return [WORDS[plain]]
    if plain in STOP_WORDS:
        return []
    if _ZWNJ in token:  # «نقره‌ای» اگر کامل در دیکشنری نبود، تکه‌تکه امتحان می‌شود
        out = []
        for part in token.split(_ZWNJ):
            out.extend(_translate(part))
        return out
    return []  # کلمهٔ فارسیِ ناشناخته حذف می‌شود


def make_slug(text, fallback="item", max_length=100):
    text = (text or "").translate(_ARABIC_TO_PERSIAN).translate(_DIGITS)
    for pattern, replacement in PHRASES:
        text = pattern.sub(replacement, text)
    parts = []
    for token in re.split(r"[\s,;:/\\|()\[\]{}\"'،؛.+_\-]+", text):
        if not token:
            continue
        if _PERSIAN.search(token):
            parts.extend(_translate(token))
        else:
            parts.append(token.lower())
    slug = "-".join(p for p in parts if p)
    slug = re.sub(r"[^a-z0-9-]+", "", slug)
    slug = re.sub(r"-{2,}", "-", slug).strip("-")
    if len(slug) > max_length:
        slug = slug[:max_length].rsplit("-", 1)[0] or slug[:max_length]
    return slug or fallback


def unique_slug(model, base, *, pk=None, max_length=100, **scope):
    """اگر اسلاگ در همان محدوده تکراری بود، «-2»، «-3» و ... به آخرش اضافه می‌شود."""
    queryset = model._default_manager.filter(**scope)
    if pk:
        queryset = queryset.exclude(pk=pk)
    slug, number = base, 2
    while queryset.filter(slug=slug).exists():
        suffix = f"-{number}"
        slug = base[: max_length - len(suffix)] + suffix
        number += 1
    return slug
