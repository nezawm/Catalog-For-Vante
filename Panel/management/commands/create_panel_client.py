import getpass

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandError

from Panel.groups import sync_client_group


class Command(BaseCommand):
    help = (
        "کاربر کارفرما را می‌سازد: فقط به پنل /panel/ دسترسی دارد (staff نیست، پس وارد ادمین جنگو نمی‌شود) "
        "و فقط مجوز مدیریت دسته‌بندی، زیردسته، محصول و فایل PDF کاتالوگ را دارد."
    )

    def add_arguments(self, parser):
        parser.add_argument("username")
        parser.add_argument("--password", help="اگر داده نشود، به‌صورت مخفی پرسیده می‌شود.")

    def handle(self, *args, **options):
        User = get_user_model()
        username = options["username"]
        if User.objects.filter(**{User.USERNAME_FIELD: username}).exists():
            raise CommandError(f"کاربری با نام «{username}» از قبل وجود دارد.")

        group = sync_client_group()

        password = options["password"] or getpass.getpass("گذرواژه: ")
        if not password:
            raise CommandError("گذرواژه نباید خالی باشد.")

        user = User(**{User.USERNAME_FIELD: username}, is_staff=False, is_superuser=False)
        user.set_password(password)
        user.save()
        user.groups.add(group)
        self.stdout.write(self.style.SUCCESS(f"کاربر «{username}» ساخته شد. آدرس ورود: /panel/login/"))
