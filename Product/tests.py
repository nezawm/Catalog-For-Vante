import importlib

from django.apps import apps
from django.test import TestCase
from django.urls import reverse

from Category.models import Category, Subcategory
from Product.models import Product, Vanlite


class VanliteFieldsTests(TestCase):
    def test_vanlite_fields_saved_and_localized(self):
        cat = Category.objects.create(name="Vanlite", title="شبرنگ")
        p = Product.objects.create(
            category=cat, name="EGP", durability_years=7,
            colors="سفید - قرمز", colors_en="White - Red", roll_size="1.22 × 45.7",
        )
        self.assertEqual(p.display_colors, "سفید - قرمز")
        self.assertEqual((p.durability_years, p.roll_size), (7, "1.22 × 45.7"))

    def test_vanlite_row_colors_localized(self):
        cat = Category.objects.create(name="Vanlite", title="شبرنگ")
        p = Product.objects.create(category=cat, name="EGP")
        row = Vanlite.objects.create(product=p, name="EGP", colors="سفید", colors_en="White")
        self.assertEqual(row.display_colors, "سفید")
        from django.utils import translation

        with translation.override("en"):
            self.assertEqual(row.display_colors, "White")


class VanliteSiteTests(TestCase):
    def setUp(self):
        self.cat = Category.objects.create(name="Vanlite", title="شبرنگ")
        self.product = Product.objects.create(category=self.cat, name="شبرنگ EGP")

    def url(self):
        return reverse("Product:detail", kwargs={"slug": self.product.slug})

    def test_active_rows_are_shown_inactive_hidden(self):
        Vanlite.objects.create(product=self.product, name="EGP-White", roll_size="1.22 x 45.7", durability_years=7, product_code="V607W")
        Vanlite.objects.create(product=self.product, name="EGP-Hidden", product_code="V999", is_active=False)
        html = self.client.get(self.url()).content.decode()
        self.assertIn("V607W", html)
        self.assertNotIn("V999", html)

    def test_colors_column_only_when_some_row_has_colors(self):
        row = Vanlite.objects.create(product=self.product, name="EGP", product_code="V1")
        self.assertNotIn("<th>رنگ‌ها</th>", self.client.get(self.url()).content.decode())
        row.colors = "سفید - قرمز"
        row.save()
        html = self.client.get(self.url()).content.decode()
        self.assertIn("<th>رنگ‌ها</th>", html)
        self.assertIn("سفید - قرمز", html)

    def test_table_hidden_when_all_rows_inactive(self):
        Vanlite.objects.create(product=self.product, name="EGP", is_active=False)
        self.assertNotIn("ونلایت (شبرنگ)", self.client.get(self.url()).content.decode())


class VanliteDataMigrationTests(TestCase):
    def run_migration(self):
        module = importlib.import_module("Product.migrations.0016_move_product_vanlite_data")
        module.copy_product_vanlite_data(apps, None)

    def test_old_product_values_become_a_vanlite_row_and_are_kept(self):
        cat = Category.objects.create(name="Vanlite", title="شبرنگ")
        old = Product.objects.create(
            category=cat, name="EGP", name_en="EGP en", durability_years=7,
            colors="سفید", colors_en="White", roll_size="1.22 × 45.7",
        )
        self.run_migration()
        row = old.vanlite_items.get()
        self.assertEqual(
            (row.name, row.name_en, row.roll_size, row.durability_years, row.colors, row.colors_en),
            ("EGP", "EGP en", "1.22 × 45.7", 7, "سفید", "White"),
        )
        old.refresh_from_db()  # ستون‌های قدیمی دست‌نخورده می‌مانند
        self.assertEqual((old.colors, old.durability_years, old.roll_size), ("سفید", 7, "1.22 × 45.7"))

    def test_rerun_is_idempotent(self):
        cat = Category.objects.create(name="Vanlite", title="شبرنگ")
        p = Product.objects.create(category=cat, name="EGP", colors="سفید")
        self.run_migration()
        self.run_migration()
        self.assertEqual(p.vanlite_items.count(), 1)

    def test_existing_rows_and_empty_products_are_untouched(self):
        cat = Category.objects.create(name="Vanlite", title="شبرنگ")
        has_rows = Product.objects.create(category=cat, name="A", colors="قرمز", roll_size="9 x 9")
        keep = Vanlite.objects.create(product=has_rows, name="A-row", roll_size="1.22 x 45.7")
        empty = Product.objects.create(category=cat, name="B")
        self.run_migration()
        keep.refresh_from_db()
        self.assertEqual((keep.roll_size, keep.colors), ("1.22 x 45.7", ""))
        self.assertEqual(has_rows.vanlite_items.count(), 1)
        self.assertEqual(empty.vanlite_items.count(), 0)


class InactiveCategoryProductTests(TestCase):
    def setUp(self):
        self.cat = Category.objects.create(name="Vancal", title="ونکال")
        self.sub = Subcategory.objects.create(category=self.cat, name="PVC")
        self.product = Product.objects.create(category=self.cat, subcategory=self.sub, name="PVC سفید")

    def test_product_opens_while_category_active(self):
        self.assertEqual(self.client.get(self.product.get_absolute_url()).status_code, 200)

    def test_product_link_404_when_category_inactive(self):
        self.cat.is_active = False
        self.cat.save()
        self.assertEqual(self.client.get(self.product.get_absolute_url()).status_code, 404)

    def test_legacy_id_url_also_404_when_category_inactive(self):
        self.cat.is_active = False
        self.cat.save()
        self.assertEqual(self.client.get(f"/fa/products/old-{self.product.pk}/").status_code, 404)

    def test_reactivating_category_restores_product(self):
        self.cat.is_active = False
        self.cat.save()
        self.cat.is_active = True
        self.cat.save()
        self.assertEqual(self.client.get(self.product.get_absolute_url()).status_code, 200)

    def test_inactive_subcategory_does_not_hide_product(self):
        self.sub.is_active = False
        self.sub.save()
        self.assertEqual(self.client.get(self.product.get_absolute_url()).status_code, 200)
