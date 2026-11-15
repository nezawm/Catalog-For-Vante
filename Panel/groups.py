from django.contrib.auth.models import Group, Permission

GROUP_NAME = "مدیر کاتالوگ"
PERMISSION_REGEX = r"^(view|add|change|delete)_(category|subcategory|product)$"


def sync_client_group(using="default"):
    """گروه «مدیر کاتالوگ» را می‌سازد و مجوزهایش را روی دسته، زیردسته و محصول تنظیم می‌کند."""
    group, _ = Group.objects.using(using).get_or_create(name=GROUP_NAME)
    permissions = Permission.objects.using(using).filter(
        content_type__app_label__in=["Category", "Product"],
        codename__regex=PERMISSION_REGEX,
    )
    group.permissions.set(permissions)
    return group
