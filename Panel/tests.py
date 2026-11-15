from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.test import TestCase
from django.urls import reverse

from Category.models import Category, Subcategory
from Product.models import Product

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
        self.assertEqual(len(codenames), 12)
        self.assertTrue(all(c.split("_", 1)[1] in {"category", "subcategory", "product"} for c in codenames))

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
