import datetime

from django import template
from django.utils import timezone

register = template.Library()

_TO_FA = str.maketrans("0123456789", "۰۱۲۳۴۵۶۷۸۹")
_EMPTY_WIDTHS = {"", "-", "--", "---", "—"}


def to_fa(value):
    """عددهای لاتین را فارسی می‌کند (فقط برای نمایش)."""
    return "" if value is None else str(value).translate(_TO_FA)


@register.filter
def fa_num(value):
    return to_fa(value)


@register.filter
def widths_info(product):
    """وضعیت تکمیل سه کد عرض ونجت: چندتا پر شده و آیا اصلاً عرضی ثبت شده."""
    values = (product.width_107, product.width_127, product.width_152)
    filled = sum(1 for v in values if (v or "").strip() not in _EMPTY_WIDTHS)
    return {"filled": filled, "total": 3, "any": filled > 0, "complete": filled == 3}


def gregorian_to_jalali(gy, gm, gd):
    g_d_m = [0, 31, 59, 90, 120, 151, 181, 212, 243, 273, 304, 334]
    gy2 = gy + 1 if gm > 2 else gy
    days = 355666 + (365 * gy) + ((gy2 + 3) // 4) - ((gy2 + 99) // 100) + ((gy2 + 399) // 400) + gd + g_d_m[gm - 1]
    jy = -1595 + 33 * (days // 12053)
    days %= 12053
    jy += 4 * (days // 1461)
    days %= 1461
    if days > 365:
        jy += (days - 1) // 365
        days = (days - 1) % 365
    if days < 186:
        jm, jd = 1 + days // 31, 1 + days % 31
    else:
        jm, jd = 7 + (days - 186) // 30, 1 + (days - 186) % 30
    return jy, jm, jd


def _localize(value):
    if isinstance(value, datetime.datetime) and timezone.is_aware(value):
        return timezone.localtime(value)
    return value


@register.filter
def jdate(value):
    """تاریخ شمسی با عدد فارسی: ۱۴۰۵/۰۸/۲۴"""
    if not value:
        return "—"
    value = _localize(value)
    jy, jm, jd = gregorian_to_jalali(value.year, value.month, value.day)
    return to_fa(f"{jy}/{jm:02d}/{jd:02d}")


@register.filter
def jdatetime(value):
    """تاریخ و ساعت شمسی: ۱۴۰۵/۰۸/۲۴ — ۱۴:۲۳"""
    if not value:
        return "—"
    value = _localize(value)
    jy, jm, jd = gregorian_to_jalali(value.year, value.month, value.day)
    return to_fa(f"{jy}/{jm:02d}/{jd:02d} — {value.hour:02d}:{value.minute:02d}")


@register.filter
def fa_filesize(size):
    """حجم فایل به فارسی: ۱٫۲ مگابایت"""
    if size is None:
        return "—"
    if size < 1024 * 1024:
        return to_fa(f"{max(size // 1024, 1)}") + " کیلوبایت"
    return to_fa(f"{size / (1024 * 1024):.1f}").replace(".", "٫") + " مگابایت"


@register.filter
def get_item(mapping, key):
    """{{ dict|get_item:key }}"""
    try:
        return mapping.get(key, "")
    except AttributeError:
        return ""
