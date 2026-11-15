from django.test import TestCase

from Category.models import Category, Subcategory
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
