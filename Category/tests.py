from django.test import TestCase

from Category.models import Category, Subcategory
from Product.models import Product


class SubcategoryMoveTests(TestCase):
    def setUp(self):
        self.a = Category.objects.create(name="Vancal", title="ونکال")
        self.b = Category.objects.create(name="Vanjet", title="ونجت")
        self.sub = Subcategory.objects.create(category=self.a, name="PVC")
        self.p1 = Product.objects.create(category=self.a, subcategory=self.sub, name="p1")
        self.p2 = Product.objects.create(category=self.a, subcategory=self.sub, name="p2")
        self.other = Product.objects.create(category=self.a, name="no-sub")

    def test_moving_subcategory_moves_its_products(self):
        self.sub.category = self.b
        self.sub.save()
        for p in (self.p1, self.p2):
            p.refresh_from_db()
            self.assertEqual((p.category_id, p.subcategory_id), (self.b.pk, self.sub.pk))
            p.full_clean()  # دیگر با Product.clean ناسازگار نیست

    def test_products_without_subcategory_stay_put(self):
        self.sub.category = self.b
        self.sub.save()
        self.other.refresh_from_db()
        self.assertEqual(self.other.category_id, self.a.pk)

    def test_saving_without_category_change_touches_nothing(self):
        before = Product.objects.filter(pk=self.p1.pk).values_list("updated_at", flat=True).get()
        self.sub.name = "PVC 2"
        self.sub.save()
        self.assertEqual(Product.objects.filter(pk=self.p1.pk).values_list("updated_at", flat=True).get(), before)

    def test_slug_clash_in_new_category_gets_suffix_and_products_still_move(self):
        Subcategory.objects.create(category=self.b, name="PVC")  # اسلاگ pvc در مقصد هست
        self.sub.category = self.b
        self.sub.save()
        self.sub.refresh_from_db()
        self.assertNotEqual(self.sub.slug, "pvc")
        self.p1.refresh_from_db()
        self.assertEqual(self.p1.category_id, self.b.pk)

    def test_new_subcategory_save_works(self):
        s = Subcategory.objects.create(category=self.b, name="PET")
        self.assertTrue(s.pk)
