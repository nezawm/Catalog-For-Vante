"""محصولات، دسته‌بندی‌ها و زیردسته‌ها."""
from django.contrib import messages
from django.contrib.messages.views import SuccessMessageMixin
from django.db import transaction
from django.db.models import Count, Q
from django.http import HttpResponseRedirect
from django.urls import reverse_lazy
from django.views.generic import CreateView, ListView, UpdateView
from Category.models import Category, Subcategory
from Product.models import Product

from ..forms import CategoryForm, ProductForm, SubcategoryForm, vanlite_formset_class
from ..templatetags.panel_extras import to_fa
from .base import PAGE_SIZE, PanelDeleteView, PanelMixin


def duplicate_product_names():
    rows = (
        Product.objects.order_by()
        .values("name")
        .annotate(n=Count("id"))
        .filter(n__gt=1)
        .values_list("name", flat=True)
    )
    return set(rows)


def product_title(product, duplicates):
    """نام محصول؛ اگر نام تکراری است مقدار رویه هم کنارش می‌آید تا قابل تشخیص باشد."""
    if product.name in duplicates and product.face_value:
        return f"{product.name} {to_fa(product.face_value)} {product.get_face_unit_display()}"
    return product.name


# ---------------------------------------------------------------- محصولات

class ProductListView(PanelMixin, ListView):
    permission_required = "Product.view_product"
    template_name = "Panel/product_list.html"
    context_object_name = "products"
    paginate_by = PAGE_SIZE
    section = "products"

    def get_queryset(self):
        qs = Product.objects.select_related("category", "subcategory")
        q = self.request.GET.get("q", "").strip()
        if q:
            qs = qs.filter(Q(name__icontains=q) | Q(name_en__icontains=q))
        category = self.request.GET.get("category", "")
        if category.isdigit():
            qs = qs.filter(category_id=int(category))
        status = self.request.GET.get("status", "")
        if status == "active":
            qs = qs.filter(is_active=True)
        elif status == "inactive":
            qs = qs.filter(is_active=False)
        return qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        duplicates = duplicate_product_names()
        products = list(context["products"])
        for p in products:
            p.panel_title = product_title(p, duplicates)
        params = self.request.GET.copy()
        params.pop("page", None)
        context.update(
            products=products,
            total=context["paginator"].count,
            categories=Category.objects.all(),
            q=self.request.GET.get("q", "").strip(),
            category=self.request.GET.get("category", ""),
            status=self.request.GET.get("status", ""),
            filtered=bool(params),
            query=params.urlencode(),
        )
        return context


def subcategory_map():
    data = {}
    for s in Subcategory.objects.order_by("category_id", "order", "name"):
        data.setdefault(str(s.category_id), []).append({"id": s.id, "name": s.name})
    return data


VANLITE_PREFIX = "vanlite"


class ProductFormMixin(PanelMixin, SuccessMessageMixin):
    """فرم محصول + ردیف‌های ونلایت (Vanlite) در یک تراکنش؛ ونلایت فقط از همین‌جا ذخیره می‌شود و سایت هم از همین ردیف‌ها می‌خواند."""

    model = Product
    form_class = ProductForm
    template_name = "Panel/product_form.html"
    success_url = reverse_lazy("panel:product_list")
    section = "products"

    def build_vanlite_formset(self, data=None):
        # حذف ردیف فقط برای کسی که مجوز حذف محصول دارد (ویرایشگر می‌تواند ردیف را غیرفعال کند).
        can_delete = self.request.user.has_perm("Product.delete_product")
        return vanlite_formset_class(can_delete)(data, instance=self.object, prefix=VANLITE_PREFIX)

    def post(self, request, *args, **kwargs):
        self.object = self.get_object() if self.pk_url_kwarg in self.kwargs else None
        form = self.get_form()
        # درخواستی که اصلاً فرم ونلایت ندارد (مثلاً کلاینت قدیمی) ردیف‌های ونلایت را دست‌نخورده می‌گذارد.
        has_vanlite = f"{VANLITE_PREFIX}-TOTAL_FORMS" in request.POST
        formset = self.build_vanlite_formset(request.POST if has_vanlite else None)
        if form.is_valid() and (not has_vanlite or formset.is_valid()):
            with transaction.atomic():
                self.object = form.save()
                if has_vanlite:
                    formset.instance = self.object
                    for row in formset.save(commit=False):
                        row.product = self.object
                        row.name = row.name or self.object.name
                        row.save()
                    for row in formset.deleted_objects:
                        row.delete()
            messages.success(request, self.success_message)
            return HttpResponseRedirect(self.get_success_url())
        return self.render_to_response(self.get_context_data(form=form, vanlite_formset=formset))

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if "vanlite_formset" not in context:
            context["vanlite_formset"] = self.build_vanlite_formset()
        context["subcategory_map"] = subcategory_map()
        if self.object and self.object.pk:
            context["page_subtitle"] = f"{self.object.category.name} — {product_title(self.object, duplicate_product_names())}"
        return context


class ProductCreateView(ProductFormMixin, CreateView):
    permission_required = "Product.add_product"
    success_message = "محصول جدید ساخته شد."


class ProductUpdateView(ProductFormMixin, UpdateView):
    permission_required = "Product.change_product"
    success_message = "تغییرات محصول ذخیره شد."


class ProductDeleteView(PanelDeleteView):
    model = Product
    permission_required = "Product.delete_product"
    section = "products"
    label = "محصول"
    cancel_url_name = "panel:product_list"
    success_url = reverse_lazy("panel:product_list")


# ---------------------------------------------------------------- دسته‌بندی‌ها

class CategoryListView(PanelMixin, ListView):
    permission_required = "Category.view_category"
    template_name = "Panel/category_list.html"
    context_object_name = "categories"
    section = "categories"

    def get_queryset(self):
        return Category.objects.annotate(
            subcategory_count=Count("subcategories", distinct=True),
            product_count=Count("products", distinct=True),
        ).order_by("order", "name")


class CategoryFormMixin(PanelMixin, SuccessMessageMixin):
    model = Category
    form_class = CategoryForm
    template_name = "Panel/category_form.html"
    success_url = reverse_lazy("panel:category_list")
    section = "categories"


class CategoryCreateView(CategoryFormMixin, CreateView):
    permission_required = "Category.add_category"
    success_message = "دسته‌بندی جدید ساخته شد."


class CategoryUpdateView(CategoryFormMixin, UpdateView):
    permission_required = "Category.change_category"
    success_message = "تغییرات دسته‌بندی ذخیره شد."


class CategoryDeleteView(PanelDeleteView):
    model = Category
    permission_required = "Category.delete_category"
    section = "categories"
    label = "دسته‌بندی"
    cancel_url_name = "panel:category_list"
    success_url = reverse_lazy("panel:category_list")

    def blocked_reason(self):
        count = self.object.products.count()
        if count:
            return (
                f"این دسته‌بندی {to_fa(count)} محصول دارد و حذف نمی‌شود. "
                "ابتدا محصولات را به دستهٔ دیگری ببرید یا حذف کنید."
            )
        return ""

    def extra_note(self):
        count = self.object.subcategories.count()
        return f"زیردسته‌های این دسته‌بندی ({to_fa(count)} مورد) هم حذف می‌شوند." if count else ""


# ---------------------------------------------------------------- زیردسته‌ها

class SubcategoryListView(PanelMixin, ListView):
    permission_required = "Category.view_subcategory"
    template_name = "Panel/subcategory_list.html"
    context_object_name = "subcategories"
    section = "subcategories"

    def get_queryset(self):
        return (
            Subcategory.objects.select_related("category")
            .annotate(product_count=Count("products", distinct=True))
            .order_by("category__order", "order", "name")
        )


class SubcategoryFormMixin(PanelMixin, SuccessMessageMixin):
    model = Subcategory
    form_class = SubcategoryForm
    template_name = "Panel/subcategory_form.html"
    success_url = reverse_lazy("panel:subcategory_list")
    section = "subcategories"


class SubcategoryCreateView(SubcategoryFormMixin, CreateView):
    permission_required = "Category.add_subcategory"
    success_message = "زیردستهٔ جدید ساخته شد."


class SubcategoryUpdateView(SubcategoryFormMixin, UpdateView):
    permission_required = "Category.change_subcategory"
    success_message = "تغییرات زیردسته ذخیره شد."

    def form_valid(self, form):
        response = super().form_valid(form)
        if form.moved_products:
            messages.info(
                self.request,
                f"{to_fa(form.moved_products)} محصول همراه این زیردسته به دستهٔ جدید منتقل شد.",
            )
        return response


class SubcategoryDeleteView(PanelDeleteView):
    model = Subcategory
    permission_required = "Category.delete_subcategory"
    section = "subcategories"
    label = "زیردسته"
    cancel_url_name = "panel:subcategory_list"
    success_url = reverse_lazy("panel:subcategory_list")

    def extra_note(self):
        count = self.object.products.count()
        return f"{to_fa(count)} محصول این زیردسته «بدون زیردسته» می‌شوند (حذف نمی‌شوند)." if count else ""
