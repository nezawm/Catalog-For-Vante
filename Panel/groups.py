from django.contrib.auth.models import Group, Permission

GROUP_NAME = "مدیر کاتالوگ"
EDITOR_GROUP_NAME = "ویرایشگر محصولات"
VIEWER_GROUP_NAME = "فقط مشاهده"

PERMISSION_REGEX = r"^(view|add|change|delete)_(category|subcategory|product|catalogfile|qrcode)$"
EDITOR_REGEX = r"^(view|add|change)_(category|subcategory|product)$|^view_catalogfile$"
VIEWER_REGEX = r"^view_(category|subcategory|product|catalogfile|qrcode)$"

# سطح‌های دسترسی پنل: کلید → (عنوان، توضیح). «senior» گروه ندارد و همان is_superuser است.
ROLES = {
    "senior": ("مدیر ارشد", "دسترسی کامل، از جمله مدیریت اعضا و دیدن لاگ ورود"),
    "catalog": (GROUP_NAME, "مدیریت کامل محصولات، دسته‌ها، کاتالوگ PDF، QR و آمار (بدون مدیریت اعضا)"),
    "editor": (EDITOR_GROUP_NAME, "افزودن و ویرایش محصول و دسته‌ها؛ بدون حذف، بدون QR و بدون تغییر کاتالوگ PDF"),
    "viewer": (VIEWER_GROUP_NAME, "فقط دیدن اطلاعات و آمار؛ هیچ تغییری نمی‌تواند بدهد"),
}
ROLE_GROUPS = {"catalog": GROUP_NAME, "editor": EDITOR_GROUP_NAME, "viewer": VIEWER_GROUP_NAME}
APP_LABELS = ["Core", "Category", "Product"]


def _sync(name, regex, using):
    group, _ = Group.objects.using(using).get_or_create(name=name)
    permissions = Permission.objects.using(using).filter(
        content_type__app_label__in=APP_LABELS, codename__regex=regex
    )
    group.permissions.set(permissions)
    return group


def sync_client_group(using="default"):
    """گروه‌های سطح دسترسی را می‌سازد و مجوزهایشان را تنظیم می‌کند؛ گروه «مدیر کاتالوگ» را برمی‌گرداند."""
    _sync(EDITOR_GROUP_NAME, EDITOR_REGEX, using)
    _sync(VIEWER_GROUP_NAME, VIEWER_REGEX, using)
    return _sync(GROUP_NAME, PERMISSION_REGEX, using)


def user_role(user):
    """سطح دسترسی فعلی کاربر: senior / catalog / editor / viewer / '' (بدون دسترسی)."""
    if user.is_superuser:
        return "senior"
    names = set(user.groups.values_list("name", flat=True))
    for key, group_name in ROLE_GROUPS.items():  # از قوی‌تر به ضعیف‌تر
        if group_name in names:
            return key
    return ""


def set_user_role(user, role):
    """سطح دسترسی را روی کاربرِ ذخیره‌شده اعمال می‌کند (گروه‌های غیرمرتبط دست نمی‌خورند)."""
    sync_client_group()
    user.groups.remove(*Group.objects.filter(name__in=ROLE_GROUPS.values()))
    senior = role == "senior"
    if user.is_superuser != senior or user.is_staff != senior:
        user.is_superuser = senior
        user.is_staff = senior  # فقط مدیر ارشد به ادمین جنگو هم راه دارد
        user.save(update_fields=["is_superuser", "is_staff"])
    if role in ROLE_GROUPS:
        user.groups.add(Group.objects.get(name=ROLE_GROUPS[role]))
