from django import template
from django.urls import translate_url
from django.utils.html import format_html_join
from django.utils.translation import get_language

from Core.models import CatalogFile
from Core.translations import DEFAULT_LANGUAGE, TRANSLATIONS

register = template.Library()


def _lang():
    lang = (get_language() or DEFAULT_LANGUAGE)[:2]
    return lang if lang in TRANSLATIONS else DEFAULT_LANGUAGE


@register.simple_tag
def t(key):
    """ترجمهٔ متن رابط: {% t "nav_home" %}"""
    return TRANSLATIONS[_lang()].get(key, key)


@register.simple_tag
def tv(prefix, value):
    """ترجمهٔ مقدار انتخابی: {% tv "adhesive" product.adhesive %}"""
    return TRANSLATIONS[_lang()].get(f"{prefix}_{value}", value)


@register.simple_tag(takes_context=True)
def other_language_url(context):
    """آدرس همین صفحه به زبان دیگر"""
    request = context["request"]
    target = "en" if _lang() == "fa" else "fa"
    return translate_url(request.get_full_path(), target)


@register.simple_tag(takes_context=True)
def language_url(context, lang):
    """آدرس همین صفحه به زبان دلخواه: {% language_url "en" %}"""
    return translate_url(context["request"].get_full_path(), lang)


@register.simple_tag
def motion_words(key, lang=None):
    """متن ترجمه‌شده را کلمه‌به‌کلمه در span می‌گذارد تا کلمه‌ها یکی‌یکی انیمیت شوند
    (حروف داخل هر کلمه جدا نمی‌شوند، پس اتصال حروف فارسی خراب نمی‌شود)."""
    text = TRANSLATIONS[lang][key] if lang in TRANSLATIONS else t(key)
    words = text.split()
    return format_html_join("", '<span class="mt-word" style="--w:{}">{}</span> ', enumerate(words))


@register.simple_tag
def catalog_file():
    """کاتالوگ PDFِ فعالِ زبان فعلی (یا None): {% catalog_file as catalog %}"""
    return CatalogFile.objects.filter(language=_lang(), is_active=True).exclude(file="").first()
