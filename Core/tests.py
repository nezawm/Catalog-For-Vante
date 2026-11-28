import shutil
import tempfile

from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings

from Category.models import Category, Subcategory
from Core.models import QRCode
from Product.models import Product


class CleanUrlTests(TestCase):
    def setUp(self):
        self.cat = Category.objects.create(name="Vancal", title="ونکال")
        self.sub = Subcategory.objects.create(category=self.cat, name="PET")
        self.p1 = Product.objects.create(category=self.cat, subcategory=self.sub, name="سفید براق")
        self.p2 = Product.objects.create(category=self.cat, name="سفید براق")

    def test_urls_have_no_id(self):
        self.assertEqual(self.cat.get_absolute_url(), "/fa/categories/vancal/")
        self.assertEqual(self.sub.get_absolute_url(), "/fa/categories/vancal/pet/")
        self.assertEqual(self.p1.get_absolute_url(), "/fa/products/white-glossy/")

    def test_duplicate_product_slug_gets_suffix(self):
        self.assertEqual(self.p2.slug, "white-glossy-2")

    def test_pages_open(self):
        for url in (self.cat.get_absolute_url(), self.sub.get_absolute_url(), self.p1.get_absolute_url()):
            self.assertEqual(self.client.get(url).status_code, 200, url)

    def test_old_slug_id_urls_redirect(self):
        r = self.client.get(f"/fa/categories/vancal-{self.cat.pk}/")
        self.assertRedirects(r, "/fa/categories/vancal/", status_code=301)
        r = self.client.get(f"/fa/categories/vancal-{self.cat.pk}/pet-{self.sub.pk}/")
        self.assertRedirects(r, "/fa/categories/vancal/pet/", status_code=301)
        r = self.client.get(f"/fa/products/white-glossy-{self.p1.pk}/")
        self.assertRedirects(r, "/fa/products/white-glossy/", status_code=301)

    def test_wrong_slug_is_404(self):
        self.assertEqual(self.client.get("/fa/categories/nope/").status_code, 404)
        self.assertEqual(self.client.get("/fa/categories/vancal/nope/").status_code, 404)


class EnglishContentTests(TestCase):
    def setUp(self):
        self.cat = Category.objects.create(
            name="Vancal", title="انواع شیت", title_en="Sheets", description="توضیح", description_en="About"
        )
        self.sub = Subcategory.objects.create(category=self.cat, name="کاغذی", name_en="Paper")
        self.product = Product.objects.create(
            category=self.cat, subcategory=self.sub, name="سفید براق", name_en="Glossy white",
            face_material="گلاسه", face_material_en="Coated", description="شرح", description_en="Details",
        )
        self.untranslated = Product.objects.create(category=self.cat, name="شفاف مات")

    def get(self, url, lang):
        return self.client.get(url, HTTP_ACCEPT_LANGUAGE=lang).content.decode()

    def test_english_pages_use_english_content(self):
        body = self.client.get(f"/en/products/{self.product.slug}/").content.decode()
        self.assertIn("Glossy white", body)
        self.assertIn("Coated", body)
        self.assertIn("Details", body)
        self.assertNotIn("سفید براق", body)
        body = self.client.get(f"/en/categories/{self.cat.slug}/").content.decode()
        self.assertIn("Sheets", body)
        self.assertIn("Paper", body)
        body = self.client.get(f"/en/categories/{self.cat.slug}/{self.sub.slug}/").content.decode()
        self.assertIn("Glossy white", body)
        self.assertIn("Coated", body)
        self.assertNotIn("سفید براق", body)

    def test_persian_pages_unchanged(self):
        body = self.client.get(f"/fa/products/{self.product.slug}/").content.decode()
        self.assertIn("سفید براق", body)
        self.assertNotIn("Glossy white", body)

    def test_missing_english_falls_back_to_persian(self):
        body = self.client.get(f"/en/products/{self.untranslated.slug}/").content.decode()
        self.assertIn("شفاف مات", body)


PDF = b"%PDF-1.4\n1 0 obj\n<<>>\nendobj\ntrailer\n<<>>\n%%EOF\n"


class CatalogTestBase(TestCase):
    """فایل‌های آپلودی تست داخل یک پوشهٔ موقت می‌روند، نه MEDIA_ROOT واقعی."""

    @classmethod
    def setUpClass(cls):
        cls._media = tempfile.mkdtemp()
        cls._override = override_settings(MEDIA_ROOT=cls._media)
        cls._override.enable()
        super().setUpClass()

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        cls._override.disable()
        shutil.rmtree(cls._media, ignore_errors=True)

    def make_catalog(self, lang, active=True):
        from Core.models import CatalogFile

        return CatalogFile.objects.create(
            language=lang, is_active=active, file=SimpleUploadedFile("x.pdf", PDF, content_type="application/pdf")
        )


class CatalogDownloadTests(CatalogTestBase):
    def test_each_language_downloads_its_own_file_and_is_counted(self):
        fa, en = self.make_catalog("fa"), self.make_catalog("en")
        response = self.client.get("/catalog/fa/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "application/pdf")
        self.assertIn("Vante-Catalog-fa.pdf", response["Content-Disposition"])
        self.assertEqual(b"".join(response.streaming_content), PDF)
        self.client.get("/catalog/en/")
        self.client.get("/catalog/en/")
        fa.refresh_from_db()
        en.refresh_from_db()
        self.assertEqual((fa.download_count, en.download_count), (1, 2))

    def test_missing_or_inactive_or_unknown_language_is_404(self):
        self.assertEqual(self.client.get("/catalog/fa/").status_code, 404)
        self.make_catalog("fa", active=False)
        self.assertEqual(self.client.get("/catalog/fa/").status_code, 404)
        self.assertEqual(self.client.get("/catalog/de/").status_code, 404)

    def test_head_request_is_not_counted(self):
        catalog = self.make_catalog("fa")
        self.client.head("/catalog/fa/")
        catalog.refresh_from_db()
        self.assertEqual(catalog.download_count, 0)


class CatalogHeaderButtonTests(CatalogTestBase):
    def test_button_in_header_matches_page_language(self):
        self.make_catalog("fa")
        self.make_catalog("en")
        fa = self.client.get("/fa/").content.decode()
        en = self.client.get("/en/").content.decode()
        self.assertIn('href="/catalog/fa/"', fa)
        self.assertNotIn('href="/catalog/en/"', fa)
        self.assertIn('href="/catalog/en/"', en)
        self.assertIn("Download catalog", en)

    def test_button_hidden_when_no_active_file_for_that_language(self):
        self.make_catalog("fa")
        self.make_catalog("en", active=False)
        self.assertNotIn("/catalog/", self.client.get("/en/").content.decode())
        self.assertIn("/catalog/fa/", self.client.get("/fa/categories/").content.decode())


class CatalogFileTransactionTests(CatalogTestBase):
    """مدل: حذف/جایگزینی فایل فقط بعد از commit؛ در رولبک رکورد قدیمی و فایلش سالم می‌مانند."""

    def test_rollback_after_replace_keeps_old_file(self):
        from django.db import transaction

        catalog = self.make_catalog("fa")
        old, storage = catalog.file.name, catalog.file.storage
        with self.captureOnCommitCallbacks(execute=True) as callbacks:
            with self.assertRaises(RuntimeError), transaction.atomic():
                catalog.file = SimpleUploadedFile("n.pdf", PDF + b"%n", content_type="application/pdf")
                catalog.save()
                raise RuntimeError("fail after save")
        self.assertEqual(callbacks, [])
        self.assertTrue(storage.exists(old))
        catalog.refresh_from_db()
        self.assertEqual(catalog.file.name, old)

    def test_commit_after_replace_deletes_old_file(self):
        catalog = self.make_catalog("fa")
        old, storage = catalog.file.name, catalog.file.storage
        with self.captureOnCommitCallbacks(execute=True):
            catalog.file = SimpleUploadedFile("n.pdf", PDF + b"%n", content_type="application/pdf")
            catalog.save()
        self.assertFalse(storage.exists(old))
        self.assertTrue(storage.exists(catalog.file.name))

    def test_rollback_after_delete_keeps_file(self):
        from django.db import transaction

        catalog = self.make_catalog("en")
        name, storage = catalog.file.name, catalog.file.storage
        with self.captureOnCommitCallbacks(execute=True):
            with self.assertRaises(RuntimeError), transaction.atomic():
                catalog.delete()
                raise RuntimeError("fail after delete")
        self.assertTrue(storage.exists(name))
        self.assertTrue(type(catalog).objects.filter(language="en").exists())

    def test_commit_after_delete_removes_file(self):
        catalog = self.make_catalog("en")
        name, storage = catalog.file.name, catalog.file.storage
        with self.captureOnCommitCallbacks(execute=True):
            catalog.delete()
        self.assertFalse(storage.exists(name))


class HomeAndLanguageTests(TestCase):
    """صفحهٔ انتخاب زبان حذف شده؛ تغییر زبان از هدر، محصولات در صفحهٔ اصلی و فوتر تماس."""

    @classmethod
    def setUpTestData(cls):
        cls.cat = Category.objects.create(name="Vancal", title="وانکال")
        cls.sub = Subcategory.objects.create(category=cls.cat, name="PET")
        cls.in_sub = Product.objects.create(category=cls.cat, subcategory=cls.sub, name="سفید براق")
        cls.loose = Product.objects.create(category=cls.cat, name="بدون زیردسته")
        cls.hidden = Product.objects.create(category=cls.cat, name="غیرفعال", is_active=False)

    def test_root_goes_straight_to_persian_home(self):
        response = self.client.get("/")
        self.assertRedirects(response, "/fa/", fetch_redirect_response=False)

    def test_header_language_toggle_keeps_page(self):
        body = self.client.get("/fa/").content.decode()
        self.assertIn('href="/en/"', body)
        self.assertIn("flag-ir.svg", body)
        self.assertIn("flag-gb.svg", body)
        en = self.client.get("/en/categories/").content.decode()
        self.assertIn('href="/fa/categories/"', en)
        self.assertIn("lang-toggle", en)

    def test_products_are_listed_inline_on_home(self):
        body = self.client.get("/fa/").content.decode()
        self.assertIn('id="catalog"', body)
        self.assertIn('data-reveal="catalog"', body)
        self.assertIn('class="cat-card"', body)  # هر دسته یک دکمه است
        self.assertIn(f'id="cat-panel-{self.cat.pk}"', body)  # پنل زیردسته‌ها (پیش‌فرض hidden)
        self.assertIn(self.in_sub.get_absolute_url(), body)
        self.assertIn(self.loose.get_absolute_url(), body)
        self.assertNotIn(self.hidden.get_absolute_url(), body)

    def test_footer_has_instagram_and_phone(self):
        body = self.client.get("/fa/").content.decode()
        self.assertIn("vanteholding.ir", body)
        for number in ("011-3514", "0912 968 7747", "021-3641-9873", "021-3641-9881", "0933 249 7732"):
            self.assertIn(number, body)
        self.assertIn("دفتر مرکزی", body)
        self.assertIn("Sales expert", self.client.get("/en/").content.decode())
        footer = body.split('<footer')[1]
        self.assertNotIn("<a ", footer.split('<a class="footer-logo"')[0])  # آدرس و تماس لینک نیستند
        self.assertIn("footer-logo", body)

    def test_new_qr_defaults_to_persian_home(self):
        qr = QRCode.objects.create(name="x")
        self.assertEqual(qr.target, "/fa/")
        self.assertRedirects(self.client.get(f"/q/{qr.code}/"), "/fa/", fetch_redirect_response=False)
