from django.test import TestCase

# Create your tests here.


from django.test import TestCase

from Category.models import Category
from Product.models import Product


class VanliteFieldsTests(TestCase):
    def test_vanlite_fields_saved_and_localized(self):
        cat = Category.objects.create(name="Vanlite", title="شبرنگ")
        p = Product.objects.create(
            category=cat, name="EGP", durability_years=7,
            colors="سفید - قرمز", colors_en="White - Red", roll_size="1.22 × 45.7",
        )
        self.assertEqual(p.display_colors, "سفید - قرمز")
        self.assertEqual((p.durability_years, p.roll_size), (7, "1.22 × 45.7"))
