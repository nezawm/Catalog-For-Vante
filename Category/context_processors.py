import re

from django.conf import settings

from .models import Category


def nav_categories(request):
    return {
        "nav_categories": Category.objects.filter(is_active=True),
        "contact_phones": settings.CONTACT_PHONES,
        "contact_instagram": settings.CONTACT_INSTAGRAM,
        "contact_website": settings.CONTACT_WEBSITE,
        "contact_website_label": re.sub(r"^https?://|/+$", "", settings.CONTACT_WEBSITE),
    }
