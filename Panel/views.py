from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.contrib.auth.views import LoginView, LogoutView
from django.contrib.messages.views import SuccessMessageMixin
from django.db.models import Count, Q
from django.db.models.deletion import ProtectedError
from django.http import JsonResponse
from django.shortcuts import redirect, render
from django.urls import reverse, reverse_lazy
from django.views import View
from django.views.generic import CreateView, DeleteView, ListView, TemplateView, UpdateView

from Category.models import Category, Subcategory
from Core.slugs import make_slug
from Product.models import Product

from .forms import CategoryForm, PanelLoginForm, ProductForm, SubcategoryForm
from .templatetags.panel_extras import to_fa

PAGE_SIZE = 8


# ---------------------------------------------------------------- پایه

class PanelMixin(LoginRequiredMixin, PermissionRequiredMixin):
    """ورود لازم است و کاربر باید مجوز همان مدل را داشته باشد (از گروه «مدیر کاتالوگ» یا سوپریوزر)."""

    login_url = reverse_lazy("panel:login")
    section = ""

    def handle_no_permission(self):
        if self.request.user.is_authenticated:
            return render(self.request, "Panel/forbidden.html", status=403)
        return super().handle_no_permission()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["section"] = self.section
        return context


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


# ---------------------------------------------------------------- ورود و خروج

class PanelLoginView(LoginView):
    template_name = "Panel/login.html"
    authentication_form = PanelLoginForm
    redirect_authenticated_user = True

    def get_default_redirect_url(self):
        return reverse("panel:dashboard")


class PanelLogoutView(LogoutView):
    next_page = reverse_lazy("panel:login")


class SlugPreviewView(LoginRequiredMixin, View):
    login_url = reverse_lazy("panel:login")

    def get(self, request):
        text = request.GET.get("text", "")[:200]
        return JsonResponse({"slug": make_slug(text, fallback="")})


# ---------------------------------------------------------------- داشبورد

class DashboardView(PanelMixin, TemplateView):
    permission_required = "Product.view_product"
    template_name = "Panel/dashboard.html"
    section = "dashboard"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        categories = list(
            Category.objects.annotate(product_count=Count("products", distinct=True))
        )
        categories.sort(key=lambda c: (-c.product_count, c.order, c.name))
        top = max((c.product_count for c in categories), default=0)
        for c in categories:
            c.percent = round(c.product_count * 100 / top) if top else 0
        context.update(
            product_total=Product.objects.count(),
            category_total=len(categories),
            subcategory_total=Subcategory.objects.count(),
            categories=categories,
        )
        return context


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


class ProductFormMixin(PanelMixin, SuccessMessageMixin):
    model = Product
    form_class = ProductForm
    template_name = "Panel/product_form.html"
    success_url = reverse_lazy("panel:product_list")
    section = "products"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
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


class PanelDeleteView(PanelMixin, DeleteView):
    """صفحهٔ تأیید حذف؛ اگر حذف ممکن نباشد دلیلش را نشان می‌دهد."""

    template_name = "Panel/confirm_delete.html"
    label = ""
    cancel_url_name = ""

    def blocked_reason(self):
        return ""

    def extra_note(self):
        return ""

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(
            label=self.label,
            blocked_reason=self.blocked_reason(),
            extra_note=self.extra_note(),
            cancel_url=reverse(self.cancel_url_name),
        )
        return context

    def form_valid(self, form):
        reason = self.blocked_reason()
        if reason:
            messages.error(self.request, reason)
            return redirect(self.success_url)
        title = str(self.object)
        try:
            self.object.delete()
        except ProtectedError:
            messages.error(self.request, "این مورد به‌خاطر وابستگی به داده‌های دیگر حذف نمی‌شود.")
            return redirect(self.success_url)
        messages.success(self.request, f"«{title}» حذف شد.")
        return redirect(self.success_url)


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
