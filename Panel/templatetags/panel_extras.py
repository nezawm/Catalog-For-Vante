from django import template

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
