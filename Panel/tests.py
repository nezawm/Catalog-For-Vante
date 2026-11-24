from django.contrib.auth import get_user_model
from django.contrib.messages import get_messages
from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.management import call_command
from django.test import TestCase
from django.urls import reverse

from Category.models import Category, Subcategory
from Core.models import CatalogFile
from Core.tests import PDF, CatalogTestBase
from Product.models import Product, Vanlite

PASSWORD = "client-pass-12345"


class PanelTestBase(TestCase):
    def setUp(self):
        call_command("create_panel_client", "client", password=PASSWORD)
        self.category = Category.objects.create(name="Vancal", title="ونکال")
        self.sub = Subcategory.objects.create(category=self.category, name="PVC")
        self.product = Product.objects.create(category=self.category, subcategory=self.sub, name="PVC سفید براق")

    def login(self):
        self.assertTrue(self.client.login(username="client", password=PASSWORD))


class PanelGroupTests(TestCase):
    def test_group_is_ready_after_migrate_with_catalog_permissions_only(self):
        from django.contrib.auth.models import Group

        group = Group.objects.get(name="مدیر کاتالوگ")
        codenames = set(group.permissions.values_list("codename", flat=True))
        self.assertEqual(len(codenames), 20)
        self.assertTrue(all(c.split("_", 1)[1] in {"category", "subcategory", "product", "catalogfile", "qrcode"} for c in codenames))

    def test_user_made_like_in_admin_can_enter_panel(self):
        from django.contrib.auth.models import Group

        user = get_user_model().objects.create_user("owner-made", password=PASSWORD)
        user.groups.add(Group.objects.get(name="مدیر کاتالوگ"))
        self.client.login(username="owner-made", password=PASSWORD)
        self.assertEqual(self.client.get(reverse("panel:dashboard")).status_code, 200)


class PanelAccessTests(PanelTestBase):
    def test_anonymous_is_sent_to_panel_login(self):
        response = self.client.get(reverse("panel:dashboard"))
        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse("panel:login"), response["Location"])

    def test_client_is_not_staff_and_cannot_use_django_admin(self):
        user = get_user_model().objects.get(username="client")
        self.assertFalse(user.is_staff)
        self.login()
        response = self.client.get("/admin/")
        self.assertEqual(response.status_code, 302)
        self.assertIn("/admin/login/", response["Location"])

    def test_client_opens_all_panel_pages(self):
        self.login()
        urls = [
            reverse("panel:dashboard"),
            reverse("panel:product_list"),
            reverse("panel:product_create"),
            reverse("panel:product_update", args=[self.product.pk]),
            reverse("panel:category_list"),
            reverse("panel:category_create"),
            reverse("panel:category_update", args=[self.category.pk]),
            reverse("panel:subcategory_list"),
            reverse("panel:subcategory_create"),
            reverse("panel:subcategory_update", args=[self.sub.pk]),
            reverse("panel:catalog"),
            reverse("panel:catalog_upload", args=["fa"]),
            reverse("panel:catalog_upload", args=["en"]),
        ]
        for url in urls:
            self.assertEqual(self.client.get(url).status_code, 200, url)

    def test_user_without_permissions_gets_403(self):
        get_user_model().objects.create_user("nobody", password=PASSWORD)
        self.client.login(username="nobody", password=PASSWORD)
        self.assertEqual(self.client.get(reverse("panel:product_list")).status_code, 403)


class PanelProductTests(PanelTestBase):
    def test_create_product(self):
        self.login()
        response = self.client.post(reverse("panel:product_create"), {
            "category": self.category.pk, "subcategory": "", "name": "PET شفاف براق",
            "face_unit": "micron", "face_value": "50", "adhesive": "hotmelt",
            "is_active": "on", "order": "0",
        })
        self.assertRedirects(response, reverse("panel:product_list"))
        product = Product.objects.get(name="PET شفاف براق")
        self.assertEqual(product.slug, "pet-clear-glossy")

    def test_subcategory_must_belong_to_category(self):
        other = Category.objects.create(name="Vanjet", title="ونجت")
        self.login()
        response = self.client.post(reverse("panel:product_update", args=[self.product.pk]), {
            "category": other.pk, "subcategory": self.sub.pk, "name": self.product.name,
            "face_unit": "micron", "order": "0",
        })
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.context["form"].errors.get("subcategory"))

    def test_search_and_status_filter(self):
        Product.objects.create(category=self.category, name="گلاسه", is_active=False)
        self.login()
        response = self.client.get(reverse("panel:product_list"), {"status": "inactive"})
        self.assertEqual([p.name for p in response.context["products"]], ["گلاسه"])
        response = self.client.get(reverse("panel:product_list"), {"q": "PVC"})
        self.assertEqual(len(response.context["products"]), 1)

    def test_delete_product(self):
        self.login()
        response = self.client.post(reverse("panel:product_delete", args=[self.product.pk]))
        self.assertRedirects(response, reverse("panel:product_list"))
        self.assertFalse(Product.objects.filter(pk=self.product.pk).exists())


class PanelCategoryTests(PanelTestBase):
    def test_category_with_products_is_not_deleted(self):
        self.login()
        self.client.post(reverse("panel:category_delete", args=[self.category.pk]))
        self.assertTrue(Category.objects.filter(pk=self.category.pk).exists())

    def test_empty_category_is_deleted(self):
        empty = Category.objects.create(name="Vanlite", title="ونلایت")
        self.login()
        self.client.post(reverse("panel:category_delete", args=[empty.pk]))
        self.assertFalse(Category.objects.filter(pk=empty.pk).exists())


class PanelCatalogTests(CatalogTestBase):
    def setUp(self):
        call_command("create_panel_client", "client", password=PASSWORD)
        self.assertTrue(self.client.login(username="client", password=PASSWORD))

    def upload(self, lang, name="catalog.pdf", data=PDF, **extra):
        return self.client.post(
            reverse("panel:catalog_upload", args=[lang]),
            {"file": SimpleUploadedFile(name, data, content_type="application/pdf"), "is_active": "on", **extra},
        )

    def test_client_uploads_both_languages(self):
        from Core.models import CatalogFile

        self.assertRedirects(self.upload("fa"), reverse("panel:catalog"))
        self.assertRedirects(self.upload("en"), reverse("panel:catalog"))
        self.assertEqual(CatalogFile.objects.count(), 2)
        self.assertEqual(self.client.get("/catalog/fa/").status_code, 200)
        self.assertEqual(self.client.get("/catalog/en/").status_code, 200)

    def test_non_pdf_is_rejected(self):
        from Core.models import CatalogFile

        response = self.upload("fa", name="evil.exe", data=b"MZ")
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.context["form"].errors.get("file"))
        response = self.upload("fa", name="fake.pdf", data=b"not really a pdf")
        self.assertTrue(response.context["form"].errors.get("file"))
        self.assertFalse(CatalogFile.objects.exists())

    def test_replace_removes_old_file_and_keeps_download_count(self):
        from Core.models import CatalogFile

        self.upload("fa")
        catalog = CatalogFile.objects.get(language="fa")
        CatalogFile.objects.filter(pk=catalog.pk).update(download_count=7)
        old_name = catalog.file.name
        with self.captureOnCommitCallbacks(execute=True):
            self.upload("fa", data=PDF + b"%new")
        catalog.refresh_from_db()
        self.assertNotEqual(catalog.file.name, old_name)
        self.assertFalse(catalog.file.storage.exists(old_name))
        self.assertTrue(catalog.file.storage.exists(catalog.file.name))
        self.assertEqual(catalog.download_count, 7)

    def test_edit_without_new_file_keeps_file_and_can_deactivate(self):
        from Core.models import CatalogFile

        self.upload("fa")
        name = CatalogFile.objects.get(language="fa").file.name
        response = self.client.post(reverse("panel:catalog_upload", args=["fa"]), {})  # is_active unchecked
        self.assertRedirects(response, reverse("panel:catalog"))
        catalog = CatalogFile.objects.get(language="fa")
        self.assertEqual(catalog.file.name, name)
        self.assertFalse(catalog.is_active)
        self.assertEqual(self.client.get("/catalog/fa/").status_code, 404)

    def test_toggle_and_preview(self):
        from Core.models import CatalogFile

        self.upload("en")
        self.client.post(reverse("panel:catalog_toggle", args=["en"]))
        self.assertFalse(CatalogFile.objects.get(language="en").is_active)
        self.client.post(reverse("panel:catalog_toggle", args=["en"]))
        self.assertTrue(CatalogFile.objects.get(language="en").is_active)
        preview = self.client.get(reverse("panel:catalog_preview", args=["en"]))
        self.assertEqual(preview.status_code, 200)
        self.assertEqual(CatalogFile.objects.get(language="en").download_count, 0)  # پیش‌نمایش شمرده نمی‌شود

    def test_delete_removes_record_and_file(self):
        from Core.models import CatalogFile

        self.upload("fa")
        catalog = CatalogFile.objects.get(language="fa")
        name, storage = catalog.file.name, catalog.file.storage
        with self.captureOnCommitCallbacks(execute=True):
            response = self.client.post(reverse("panel:catalog_delete", args=["fa"]))
        self.assertRedirects(response, reverse("panel:catalog"))
        self.assertFalse(CatalogFile.objects.filter(language="fa").exists())
        self.assertFalse(storage.exists(name))

    def test_unknown_language_is_404_and_anonymous_is_redirected(self):
        self.assertEqual(self.client.get(reverse("panel:catalog_upload", args=["de"])).status_code, 404)
        self.client.logout()
        response = self.client.get(reverse("panel:catalog"))
        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse("panel:login"), response["Location"])

    def test_dashboard_shows_catalog_card(self):
        self.upload("fa")
        response = self.client.get(reverse("panel:dashboard"))
        self.assertContains(response, "کاتالوگ PDF سایت")



ANDROID_UA = "Mozilla/5.0 (Linux; Android 13; SM-G991B Build/TP1A.220624.014) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Mobile Safari/537.36"
IPHONE_UA = "Mozilla/5.0 (iPhone; CPU iPhone OS 17_1 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.1 Mobile/15E148 Safari/604.1"
WIN_UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 Edg/120.0.0.0"


class UserAgentTests(TestCase):
    def test_android_model_os_browser(self):
        from Core.useragent import parse_user_agent

        info = parse_user_agent(ANDROID_UA)
        self.assertEqual((info["device_type"], info["device_model"], info["os"], info["browser"]), ("mobile", "SM-G991B", "Android 13", "Chrome"))

    def test_iphone_and_windows_and_bot(self):
        from Core.useragent import parse_user_agent

        iphone = parse_user_agent(IPHONE_UA)
        self.assertEqual((iphone["device_type"], iphone["device_model"], iphone["os"], iphone["browser"]), ("mobile", "iPhone", "iOS 17.1", "Safari"))
        win = parse_user_agent(WIN_UA)
        self.assertEqual((win["device_type"], win["os"], win["browser"]), ("desktop", "Windows 10/11", "Edge"))
        self.assertEqual(parse_user_agent("WhatsApp/2.23")["device_type"], "bot")


class QRTests(PanelTestBase):
    def make_qr(self):
        from Core.models import QRCode

        return QRCode.objects.create(name="بنر", target="/fa/")

    def test_scan_counts_and_redirects(self):
        from Core.models import QRScan

        qr = self.make_qr()
        response = self.client.get(reverse("qr_scan", args=[qr.code]), HTTP_USER_AGENT=ANDROID_UA)
        self.assertRedirects(response, "/fa/", fetch_redirect_response=False)
        scan = QRScan.objects.get()
        self.assertEqual((scan.device_model, scan.os), ("SM-G991B", "Android 13"))

    def test_bots_and_inactive_are_not_counted(self):
        from Core.models import QRScan

        qr = self.make_qr()
        self.client.get(reverse("qr_scan", args=[qr.code]), HTTP_USER_AGENT="TelegramBot (like TwitterBot)")
        self.assertEqual(QRScan.objects.count(), 0)
        qr.is_active = False
        qr.save()
        self.assertEqual(self.client.get(reverse("qr_scan", args=[qr.code])).status_code, 404)

    def test_panel_pages_and_images(self):
        qr = self.make_qr()
        self.client.get(reverse("qr_scan", args=[qr.code]), HTTP_USER_AGENT=IPHONE_UA)
        self.login()
        for name, args in (("panel:qr_list", []), ("panel:qr_create", []), ("panel:qr_detail", [qr.pk]), ("panel:qr_update", [qr.pk]), ("panel:visits", [])):
            self.assertEqual(self.client.get(reverse(name, args=args)).status_code, 200, name)
        png = self.client.get(reverse("panel:qr_image", args=[qr.pk]) + "?fmt=png&download=1")
        self.assertEqual(png["Content-Type"], "image/png")
        self.assertTrue(png.content.startswith(b"\x89PNG"))
        svg = self.client.get(reverse("panel:qr_image", args=[qr.pk]))
        self.assertIn(b"<svg", svg.content)

    def test_qr_requires_login(self):
        qr = self.make_qr()
        self.assertEqual(self.client.get(reverse("panel:qr_detail", args=[qr.pk])).status_code, 302)

    def test_site_visits_counted_once_per_day_visitor_and_not_for_bots(self):
        from Core.models import DailyVisit

        self.client.get("/fa/", HTTP_USER_AGENT=ANDROID_UA)
        self.client.get("/fa/", HTTP_USER_AGENT=ANDROID_UA)
        self.client.get("/fa/", HTTP_USER_AGENT="Googlebot/2.1")
        row = DailyVisit.objects.get(lang="fa")
        self.assertEqual((row.views, row.visitors), (2, 1))


class LoginLogTests(PanelTestBase):
    def test_failed_and_successful_panel_logins_are_logged(self):
        from Core.models import LoginAttempt

        self.client.post(reverse("panel:login"), {"username": "hacker", "password": "x"}, HTTP_USER_AGENT=ANDROID_UA)
        self.client.post(reverse("panel:login"), {"username": "client", "password": PASSWORD}, HTTP_USER_AGENT=WIN_UA)
        bad, good = LoginAttempt.objects.order_by("id")
        self.assertEqual((bad.username, bad.success, bad.device_model, bad.os, bad.source), ("hacker", False, "SM-G991B", "Android 13", "panel"))
        self.assertEqual((good.username, good.success, good.device_type), ("client", True, "desktop"))
        self.assertTrue(bad.ip)

    def test_password_is_never_stored(self):
        from Core.models import LoginAttempt

        self.client.post(reverse("panel:login"), {"username": "client", "password": "SECRET-PW-999"})
        attempt = LoginAttempt.objects.get()
        self.assertNotIn("SECRET-PW-999", " ".join(str(v) for v in vars(attempt).values()))

    def test_test_client_login_helper_is_not_logged(self):
        from Core.models import LoginAttempt

        self.login()
        self.assertEqual(LoginAttempt.objects.count(), 0)

    def test_log_page_is_superuser_only_and_filters(self):
        from Core.models import LoginAttempt

        self.client.post(reverse("panel:login"), {"username": "hacker", "password": "x"}, HTTP_USER_AGENT=ANDROID_UA)
        self.login()
        self.assertEqual(self.client.get(reverse("panel:login_log")).status_code, 403)
        self.client.logout()
        get_user_model().objects.create_superuser("boss", password=PASSWORD)
        self.client.login(username="boss", password=PASSWORD)
        page = self.client.get(reverse("panel:login_log"), {"status": "failed", "q": "hacker"})
        self.assertEqual(page.status_code, 200)
        self.assertContains(page, "hacker")
        self.assertContains(page, "SM-G991B")
        self.assertEqual(LoginAttempt.objects.filter(success=False).count(), 1)


class MemberManagementTests(PanelTestBase):
    def setUp(self):
        super().setUp()
        User = get_user_model()
        self.boss = User.objects.create_superuser("boss", password=PASSWORD)

    def as_boss(self):
        self.assertTrue(self.client.login(username="boss", password=PASSWORD))

    def new_user_data(self, **extra):
        data = {"username": "sara", "first_name": "سارا", "last_name": "", "email": "", "role": "editor",
                "password1": "Str0ng-pass-77", "password2": "Str0ng-pass-77", "is_active": "on"}
        data.update(extra)
        return data

    def test_only_senior_sees_member_pages(self):
        self.login()  # کاربر کارفرما (مدیر کاتالوگ)
        for name in ("panel:user_list", "panel:user_create"):
            self.assertEqual(self.client.get(reverse(name)).status_code, 403, name)
        self.assertEqual(self.client.post(reverse("panel:user_create"), self.new_user_data()).status_code, 403)
        self.assertFalse(get_user_model().objects.filter(username="sara").exists())
        self.client.logout()
        self.assertEqual(self.client.get(reverse("panel:user_list")).status_code, 302)

    def test_senior_creates_member_with_role(self):
        from Panel.groups import user_role

        self.as_boss()
        self.assertEqual(self.client.get(reverse("panel:user_list")).status_code, 200)
        response = self.client.post(reverse("panel:user_create"), self.new_user_data())
        self.assertRedirects(response, reverse("panel:user_list"))
        sara = get_user_model().objects.get(username="sara")
        self.assertEqual(user_role(sara), "editor")
        self.assertFalse(sara.is_staff or sara.is_superuser)
        self.assertTrue(sara.check_password("Str0ng-pass-77"))

    def test_weak_or_mismatched_password_rejected(self):
        self.as_boss()
        self.client.post(reverse("panel:user_create"), self.new_user_data(password1="12345678", password2="12345678"))
        self.client.post(reverse("panel:user_create"), self.new_user_data(password2="different-pass"))
        self.assertFalse(get_user_model().objects.filter(username="sara").exists())

    def test_role_permissions_differ(self):
        self.as_boss()
        self.client.post(reverse("panel:user_create"), self.new_user_data(username="ed", role="editor"))
        self.client.post(reverse("panel:user_create"), self.new_user_data(username="vw", role="viewer"))
        self.client.logout()
        self.client.login(username="ed", password="Str0ng-pass-77")
        self.assertEqual(self.client.get(reverse("panel:product_create")).status_code, 200)
        self.assertEqual(self.client.get(reverse("panel:product_delete", args=[self.product.pk])).status_code, 403)
        self.assertEqual(self.client.get(reverse("panel:qr_list")).status_code, 403)
        self.client.logout()
        self.client.login(username="vw", password="Str0ng-pass-77")
        self.assertEqual(self.client.get(reverse("panel:product_list")).status_code, 200)
        self.assertEqual(self.client.get(reverse("panel:product_create")).status_code, 403)
        self.assertEqual(self.client.get(reverse("panel:qr_list")).status_code, 200)

    def test_change_role_senior_and_back(self):
        from Panel.groups import user_role

        self.as_boss()
        client_user = get_user_model().objects.get(username="client")
        data = {"username": "client", "first_name": "", "last_name": "", "email": "", "role": "senior", "is_active": "on"}
        self.client.post(reverse("panel:user_update", args=[client_user.pk]), data)
        client_user.refresh_from_db()
        self.assertEqual((user_role(client_user), client_user.is_staff), ("senior", True))
        self.client.post(reverse("panel:user_update", args=[client_user.pk]), {**data, "role": "viewer"})
        client_user.refresh_from_db()
        self.assertEqual((user_role(client_user), client_user.is_staff, client_user.is_superuser), ("viewer", False, False))
        self.assertEqual(client_user.groups.count(), 1)

    def test_admin_resets_password_and_deactivated_cannot_login(self):
        self.as_boss()
        member = get_user_model().objects.get(username="client")
        self.client.post(reverse("panel:user_password", args=[member.pk]), {"new_password1": "Brand-new-pass-5", "new_password2": "Brand-new-pass-5"})
        member.refresh_from_db()
        self.assertTrue(member.check_password("Brand-new-pass-5"))
        self.client.post(reverse("panel:user_toggle", args=[member.pk]))
        member.refresh_from_db()
        self.assertFalse(member.is_active)
        self.client.logout()
        self.assertFalse(self.client.login(username="client", password="Brand-new-pass-5"))

    def test_cannot_lock_out_last_senior_or_self(self):
        self.as_boss()
        boss = self.boss
        self.client.post(reverse("panel:user_toggle", args=[boss.pk]))
        self.client.post(reverse("panel:user_delete", args=[boss.pk]))
        boss.refresh_from_db()
        self.assertTrue(boss.is_active)
        self.assertTrue(get_user_model().objects.filter(pk=boss.pk).exists())
        # حتی اگر مدیر ارشد دومی خودش را بخواهد حذف کند، نمی‌شود؛ و دیگری هم نمی‌تواند آخرین را تنزل دهد
        second = get_user_model().objects.create_superuser("boss2", password=PASSWORD)
        self.client.logout()
        self.client.login(username="boss2", password=PASSWORD)
        data = {"username": "boss", "first_name": "", "last_name": "", "email": "", "role": "viewer", "is_active": "on"}
        self.client.post(reverse("panel:user_update", args=[boss.pk]), data)  # boss2 هنوز فعال است، پس مجاز
        boss.refresh_from_db()
        self.assertFalse(boss.is_superuser)
        data.update(username="boss2")
        self.client.post(reverse("panel:user_update", args=[second.pk]), data)  # خودش و آخرین مدیر ارشد
        second.refresh_from_db()
        self.assertTrue(second.is_superuser)

    def test_my_account_profile_and_password_change_keep_session(self):
        self.login()
        page = self.client.get(reverse("panel:account"))
        self.assertEqual(page.status_code, 200)
        self.client.post(reverse("panel:account"), {"which": "profile", "p-first_name": "علی", "p-last_name": "رضایی", "p-email": "a@b.com"})
        user = get_user_model().objects.get(username="client")
        self.assertEqual((user.first_name, user.email), ("علی", "a@b.com"))
        bad = self.client.post(reverse("panel:account"), {"which": "password", "w-old_password": "wrong", "w-new_password1": "Another-pass-9", "w-new_password2": "Another-pass-9"})
        self.assertEqual(bad.status_code, 200)
        self.client.post(reverse("panel:account"), {"which": "password", "w-old_password": PASSWORD, "w-new_password1": "Another-pass-9", "w-new_password2": "Another-pass-9"})
        user.refresh_from_db()
        self.assertTrue(user.check_password("Another-pass-9"))
        self.assertEqual(self.client.get(reverse("panel:dashboard")).status_code, 200)  # هنوز واردِ پنل است


def vanlite_post(rows, initial=0, **product):
    """داده‌ی POST فرم محصول + ردیف‌های ونلایت (با management form)."""
    data = {"vanlite-TOTAL_FORMS": str(len(rows)), "vanlite-INITIAL_FORMS": str(initial),
            "vanlite-MIN_NUM_FORMS": "0", "vanlite-MAX_NUM_FORMS": "1000", **product}
    for i, row in enumerate(rows):
        for key, value in row.items():
            data[f"vanlite-{i}-{key}"] = value
    return data


class PanelVanliteTests(PanelTestBase):
    """چیزی که در پنل وارد می‌شود باید همان چیزی باشد که در سایت دیده می‌شود."""

    def product_data(self, product, **extra):
        return {"category": product.category_id, "subcategory": "", "name": product.name,
                "face_unit": "micron", "order": "0", "is_active": "on", **extra}

    def test_panel_values_show_on_site(self):
        self.login()
        data = vanlite_post(
            [{"name": "EGP-White", "type": "EGP", "product_code": "V607W", "roll_size": "1.22 × 45.7",
              "durability_years": "7", "colors": "سفید - قرمز", "colors_en": "White - Red",
              "order": "0", "is_active": "on"}],
            **self.product_data(self.product),
        )
        response = self.client.post(reverse("panel:product_update", args=[self.product.pk]), data)
        self.assertRedirects(response, reverse("panel:product_list"))
        row = self.product.vanlite_items.get()
        self.assertEqual((row.roll_size, row.durability_years, row.colors), ("1.22 × 45.7", 7, "سفید - قرمز"))
        html = self.client.get(self.product.get_absolute_url()).content.decode()
        for expected in ("V607W", "سفید - قرمز", "1.22 × 45.7"):
            self.assertIn(expected, html)
        # بدون کپی روی ستون‌های قدیمی Product
        self.product.refresh_from_db()
        self.assertEqual((self.product.colors, self.product.roll_size, self.product.durability_years), ("", "", None))

    def test_form_page_shows_existing_rows_and_empty_template(self):
        Vanlite.objects.create(product=self.product, name="EGP-Red", product_code="V607R")
        self.login()
        response = self.client.get(reverse("panel:product_update", args=[self.product.pk]))
        html = response.content.decode()
        self.assertIn("V607R", html)
        self.assertIn("vanlite-__prefix__-name", html)
        self.assertEqual(len(response.context["vanlite_formset"].forms), 1)

    def test_blank_name_falls_back_to_product_name_and_blank_extra_row_is_ignored(self):
        self.login()
        data = vanlite_post(
            [{"name": "", "roll_size": "1.22 x 45.7", "order": "0", "is_active": "on"},
             {"order": "0", "is_active": "on"}],
            **self.product_data(self.product),
        )
        self.client.post(reverse("panel:product_update", args=[self.product.pk]), data)
        self.assertEqual(list(self.product.vanlite_items.values_list("name", flat=True)), [self.product.name])

    def test_edit_existing_row_keeps_other_rows(self):
        a = Vanlite.objects.create(product=self.product, name="A", roll_size="old", product_code="CA")
        b = Vanlite.objects.create(product=self.product, name="B", product_code="CB")
        self.login()
        rows = [
            {"id": a.pk, "product": self.product.pk, "name": "A", "roll_size": "new", "product_code": "CA", "order": "0", "is_active": "on"},
            {"id": b.pk, "product": self.product.pk, "name": "B", "product_code": "CB", "order": "0", "is_active": "on"},
        ]
        self.client.post(reverse("panel:product_update", args=[self.product.pk]),
                         vanlite_post(rows, initial=2, **self.product_data(self.product)))
        a.refresh_from_db()
        self.assertEqual(a.roll_size, "new")
        self.assertTrue(Vanlite.objects.filter(pk=b.pk).exists())

    def test_post_without_vanlite_form_leaves_rows_untouched(self):
        Vanlite.objects.create(product=self.product, name="A", product_code="CA")
        self.login()
        response = self.client.post(reverse("panel:product_update", args=[self.product.pk]), self.product_data(self.product))
        self.assertRedirects(response, reverse("panel:product_list"))
        self.assertEqual(self.product.vanlite_items.count(), 1)

    def test_new_product_with_rows_created_together(self):
        self.login()
        data = vanlite_post([{"name": "N1", "product_code": "X1", "order": "0", "is_active": "on"}],
                            category=self.category.pk, subcategory="", name="محصول نو", face_unit="micron",
                            order="0", is_active="on")
        self.client.post(reverse("panel:product_create"), data)
        self.assertEqual(Product.objects.get(name="محصول نو").vanlite_items.get().product_code, "X1")

    def test_invalid_product_saves_no_rows(self):
        self.login()
        data = vanlite_post([{"name": "N1", "order": "0", "is_active": "on"}],
                            category=self.category.pk, subcategory="", name="", face_unit="micron", order="0")
        response = self.client.post(reverse("panel:product_create"), data)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(Vanlite.objects.count(), 0)

    def test_invalid_row_blocks_save_and_shows_error(self):
        self.login()
        data = vanlite_post([{"name": "N", "durability_years": "abc", "order": "0", "is_active": "on"}],
                            **self.product_data(self.product, name="تغییر نام"))
        response = self.client.post(reverse("panel:product_update", args=[self.product.pk]), data)
        self.assertEqual(response.status_code, 200)
        self.product.refresh_from_db()
        self.assertNotEqual(self.product.name, "تغییر نام")  # هیچ‌چیز نیمه‌کاره ذخیره نشد

    def test_delete_row_needs_delete_permission(self):
        row = Vanlite.objects.create(product=self.product, name="A", product_code="CA")
        editor = get_user_model().objects.create_user("ed", password=PASSWORD)
        from Panel.groups import set_user_role

        set_user_role(editor, "editor")
        self.client.login(username="ed", password=PASSWORD)
        rows = [{"id": row.pk, "product": self.product.pk, "name": "A", "DELETE": "on", "order": "0", "is_active": "on"}]
        self.client.post(reverse("panel:product_update", args=[self.product.pk]),
                         vanlite_post(rows, initial=1, **self.product_data(self.product)))
        self.assertTrue(Vanlite.objects.filter(pk=row.pk).exists())  # ویرایشگر حذف نمی‌تواند
        self.client.logout()
        self.login()  # مدیر کاتالوگ مجوز حذف دارد
        self.client.post(reverse("panel:product_update", args=[self.product.pk]),
                         vanlite_post(rows, initial=1, **self.product_data(self.product)))
        self.assertFalse(Vanlite.objects.filter(pk=row.pk).exists())

    def test_product_form_no_longer_has_old_vanlite_fields(self):
        self.login()
        form = self.client.get(reverse("panel:product_update", args=[self.product.pk])).context["form"]
        for name in ("colors", "colors_en", "roll_size", "durability_years"):
            self.assertNotIn(name, form.fields)


class PanelSubcategoryMoveTests(PanelTestBase):
    def setUp(self):
        super().setUp()
        self.other_cat = Category.objects.create(name="Vanjet", title="ونجت")

    def move(self, sub, category):
        return self.client.post(reverse("panel:subcategory_update", args=[sub.pk]), {
            "category": category.pk, "name": sub.name, "order": "0", "is_active": "on"})

    def test_moving_subcategory_in_panel_moves_products_and_says_so(self):
        self.login()
        response = self.move(self.sub, self.other_cat)
        self.assertRedirects(response, reverse("panel:subcategory_list"))
        self.product.refresh_from_db()
        self.assertEqual(self.product.category_id, self.other_cat.pk)
        self.assertEqual(self.product.subcategory_id, self.sub.pk)
        texts = [str(m) for m in get_messages(response.wsgi_request)]
        self.assertTrue(any("منتقل شد" in t for t in texts), texts)

    def test_product_is_not_left_inconsistent(self):
        self.login()
        self.move(self.sub, self.other_cat)
        self.product.refresh_from_db()
        self.product.full_clean()
        self.assertEqual(self.product.subcategory.category_id, self.product.category_id)

    def test_edit_without_category_change_does_not_move_anything(self):
        self.login()
        response = self.move(self.sub, self.category)
        self.assertRedirects(response, reverse("panel:subcategory_list"))
        self.product.refresh_from_db()
        self.assertEqual(self.product.category_id, self.category.pk)


class PanelCatalogRollbackTests(CatalogTestBase):
    """فایل PDF فقط بعد از موفقیت تراکنش پاک می‌شود."""

    def setUp(self):
        call_command("create_panel_client", "client", password=PASSWORD)
        self.assertTrue(self.client.login(username="client", password=PASSWORD))

    def post_upload(self, data):
        return self.client.post(
            reverse("panel:catalog_upload", args=["fa"]),
            {"file": SimpleUploadedFile("c.pdf", data, content_type="application/pdf"), "is_active": "on"},
        )

    def test_old_file_not_deleted_before_commit(self):
        self.post_upload(PDF)
        catalog = CatalogFile.objects.get(language="fa")
        old = catalog.file.name
        with self.captureOnCommitCallbacks(execute=False) as callbacks:
            self.post_upload(PDF + b"%new")
        self.assertTrue(catalog.file.storage.exists(old))  # هنوز قطعی نشده
        for callback in callbacks:
            callback()
        self.assertFalse(catalog.file.storage.exists(old))

    def test_error_after_save_keeps_old_record_and_file(self):
        from unittest import mock

        self.post_upload(PDF)
        catalog = CatalogFile.objects.get(language="fa")
        old = catalog.file.name
        from Panel.views import CatalogUploadView

        # خطا بعد از ذخیرهٔ رکورد جدید (داخل form_valid) رخ می‌دهد
        with mock.patch.object(CatalogUploadView, "get_success_url", side_effect=RuntimeError("boom")):
            self.client.raise_request_exception = False
            with self.captureOnCommitCallbacks(execute=True) as callbacks:
                self.post_upload(PDF + b"%new")
        self.assertEqual(callbacks, [])
        catalog.refresh_from_db()
        self.assertEqual(catalog.file.name, old)
        self.assertTrue(catalog.file.storage.exists(old))

    def test_delete_keeps_file_until_commit(self):
        self.post_upload(PDF)
        catalog = CatalogFile.objects.get(language="fa")
        name, storage = catalog.file.name, catalog.file.storage
        with self.captureOnCommitCallbacks(execute=False) as callbacks:
            self.client.post(reverse("panel:catalog_delete", args=["fa"]))
        self.assertFalse(CatalogFile.objects.filter(language="fa").exists())
        self.assertTrue(storage.exists(name))
        for callback in callbacks:
            callback()
        self.assertFalse(storage.exists(name))
