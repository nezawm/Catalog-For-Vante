from django.contrib import messages
from django.contrib.auth import get_user_model, update_session_auth_hash
from django.contrib.auth.forms import PasswordChangeForm
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.contrib.auth.views import LoginView, LogoutView
from django.contrib.messages.views import SuccessMessageMixin
from datetime import timedelta

from django.db.models import Count, Q, Sum
from django.db.models.functions import TruncDate
from django.db.models.deletion import ProtectedError
from django.http import FileResponse, Http404, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse, reverse_lazy
from django.views import View
from django.utils import timezone
from django.views.generic import CreateView, DeleteView, DetailView, FormView, ListView, TemplateView, UpdateView

from Category.models import Category, Subcategory
from Core.models import CatalogFile, DailyVisit, LoginAttempt, QRCode, QRScan
from Core.qr import make_png, make_svg
from Core.useragent import DEVICE_LABELS
from Core.slugs import make_slug
from Product.models import Product

from .forms import (
    CatalogForm, CategoryForm, PanelLoginForm, PanelSetPasswordForm, ProductForm, ProfileForm, QRCodeForm,
    StyledFormMixin, SubcategoryForm, UserForm,
)
from .groups import ROLES, user_role
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
        rows = catalog_rows()
        context.update(
            catalogs=rows,
            catalog_downloads=sum(r["obj"].download_count for r in rows if r["obj"]),
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


# ---------------------------------------------------------------- کاتالوگ PDF (فارسی / انگلیسی)

CATALOG_LANGUAGES = (("fa", "فارسی"), ("en", "انگلیسی (English)"))


def catalog_rows():
    """برای هر زبان سایت یک ردیف: {code, label, obj}؛ obj اگر فایلی آپلود نشده باشد None است."""
    existing = {c.language: c for c in CatalogFile.objects.all()}
    return [{"code": code, "label": label, "obj": existing.get(code)} for code, label in CATALOG_LANGUAGES]


def catalog_lang(view):
    lang = view.kwargs["lang"]
    if lang not in dict(CATALOG_LANGUAGES):
        raise Http404
    return lang


class CatalogListView(PanelMixin, TemplateView):
    permission_required = "Core.view_catalogfile"
    template_name = "Panel/catalog_list.html"
    section = "catalog"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["rows"] = catalog_rows()
        return context


class CatalogUploadView(PanelMixin, SuccessMessageMixin, UpdateView):
    """آپلود کاتالوگ یک زبان؛ اگر قبلاً فایلی بوده، فایل جدید جایگزین (و قدیمی پاک) می‌شود."""

    model = CatalogFile
    form_class = CatalogForm
    template_name = "Panel/catalog_form.html"
    success_url = reverse_lazy("panel:catalog")
    section = "catalog"

    def get_object(self, queryset=None):
        lang = catalog_lang(self)
        return CatalogFile.objects.filter(language=lang).first() or CatalogFile(language=lang)

    def get_permission_required(self):
        exists = CatalogFile.objects.filter(language=catalog_lang(self)).exists()
        return ["Core.change_catalogfile" if exists else "Core.add_catalogfile"]

    def get_success_message(self, cleaned_data):
        return f"{self.object} ذخیره شد."

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["lang_label"] = dict(CATALOG_LANGUAGES)[catalog_lang(self)]
        return context


class CatalogToggleView(PanelMixin, View):
    """فعال/غیرفعال کردن سریع دکمهٔ دانلود سایت برای یک زبان."""

    permission_required = "Core.change_catalogfile"
    http_method_names = ["post"]

    def post(self, request, lang):
        catalog = get_object_or_404(CatalogFile, language=catalog_lang(self))
        catalog.is_active = not catalog.is_active
        catalog.save(update_fields=["is_active", "updated_at"])
        state = "فعال شد و دکمهٔ دانلود در سایت نمایش داده می‌شود" if catalog.is_active else "غیرفعال شد و دکمهٔ دانلود از سایت برداشته شد"
        messages.success(request, f"{catalog} {state}.")
        return redirect("panel:catalog")


class CatalogPreviewView(PanelMixin, View):
    """نمایش PDF داخل مرورگر برای کارفرما؛ در شمارندهٔ دانلود حساب نمی‌شود."""

    permission_required = "Core.view_catalogfile"

    def get(self, request, lang):
        catalog = get_object_or_404(CatalogFile, language=catalog_lang(self))
        try:
            handle = catalog.file.storage.open(catalog.file.name, "rb")
        except (FileNotFoundError, ValueError):
            raise Http404
        return FileResponse(handle, content_type="application/pdf", filename=catalog.download_filename)


class CatalogDeleteView(PanelDeleteView):
    model = CatalogFile
    permission_required = "Core.delete_catalogfile"
    section = "catalog"
    label = "کاتالوگ"
    cancel_url_name = "panel:catalog"
    success_url = reverse_lazy("panel:catalog")

    def get_object(self, queryset=None):
        return get_object_or_404(CatalogFile, language=catalog_lang(self))

    def extra_note(self):
        return "فایل PDF از سرور پاک می‌شود و دکمهٔ دانلود این زبان از سایت برداشته می‌شود."


# ---------------------------------------------------------------- کد QR و آمار

def day_series(counts, days=30):
    """counts: {date: عدد}. خروجی: لیست روزهای اخیر با درصد ارتفاع برای نمودار میله‌ای."""
    today = timezone.localdate()
    dates = [today - timedelta(days=i) for i in range(days - 1, -1, -1)]
    peak = max((counts.get(d, 0) for d in dates), default=0)
    return [
        {"date": d, "count": counts.get(d, 0), "percent": round(counts.get(d, 0) * 100 / peak) if peak else 0}
        for d in dates
    ]


def breakdown(qs, field, limit=8, labels=None, skip_blank=True):
    """تعداد به تفکیک یک فیلد: [{label, count, percent}]."""
    rows = qs.exclude(**{field: ""}) if skip_blank else qs
    rows = list(rows.values(field).annotate(n=Count("id")).order_by("-n")[:limit])
    top = rows[0]["n"] if rows else 0
    return [
        {
            "label": (labels or {}).get(r[field], r[field]) or "نامشخص",
            "count": r["n"],
            "percent": round(r["n"] * 100 / top) if top else 0,
        }
        for r in rows
    ]


class QRListView(PanelMixin, TemplateView):
    permission_required = "Core.view_qrcode"
    template_name = "Panel/qr_list.html"
    section = "qr"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        week = timezone.now() - timedelta(days=7)
        context["codes"] = QRCode.objects.annotate(
            total=Count("scans", distinct=True),
            week=Count("scans", filter=Q(scans__scanned_at__gte=week), distinct=True),
        ).order_by("-created_at")
        return context


class QRFormMixin(PanelMixin, SuccessMessageMixin):
    model = QRCode
    form_class = QRCodeForm
    template_name = "Panel/qr_form.html"
    section = "qr"

    def get_success_url(self):
        return reverse("panel:qr_detail", args=[self.object.pk])


class QRCreateView(QRFormMixin, CreateView):
    permission_required = "Core.add_qrcode"
    success_message = "QR ساخته شد؛ می‌توانید آن را دانلود و چاپ کنید."


class QRUpdateView(QRFormMixin, UpdateView):
    permission_required = "Core.change_qrcode"
    success_message = "تغییرات ذخیره شد (خودِ QR چاپ‌شده تغییری نمی‌کند)."


class QRDeleteView(PanelDeleteView):
    model = QRCode
    permission_required = "Core.delete_qrcode"
    section = "qr"
    label = "کد QR"
    cancel_url_name = "panel:qr_list"
    success_url = reverse_lazy("panel:qr_list")

    def extra_note(self):
        return "همهٔ آمار اسکن این QR پاک می‌شود و QRهای چاپ‌شده دیگر کار نمی‌کنند."


def qr_public_url(request, qr):
    return request.build_absolute_uri(reverse("qr_scan", args=[qr.code]))


class QRDetailView(PanelMixin, DetailView):
    permission_required = "Core.view_qrcode"
    model = QRCode
    template_name = "Panel/qr_detail.html"
    context_object_name = "qr"
    section = "qr"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        qr = self.object
        scans = qr.scans.all()
        now = timezone.now()
        per_day = {
            r["d"]: r["n"]
            for r in scans.filter(scanned_at__gte=now - timedelta(days=30))
            .annotate(d=TruncDate("scanned_at")).values("d").annotate(n=Count("id"))
        }
        context.update(
            public_url=qr_public_url(self.request, qr),
            total=scans.count(),
            unique=scans.exclude(visitor="").values("visitor").distinct().count(),
            today=scans.filter(scanned_at__date=timezone.localdate()).count(),
            week=scans.filter(scanned_at__gte=now - timedelta(days=7)).count(),
            month=scans.filter(scanned_at__gte=now - timedelta(days=30)).count(),
            series=day_series(per_day),
            by_device=breakdown(scans, "device_type", labels=DEVICE_LABELS),
            by_model=breakdown(scans, "device_model"),
            by_os=breakdown(scans, "os"),
            by_browser=breakdown(scans, "browser"),
            recent=scans[:15],
            device_labels=DEVICE_LABELS,
        )
        return context


class QRImageView(PanelMixin, View):
    """تصویر QR: ?fmt=svg|png و ?download=1 برای دانلود."""

    permission_required = "Core.view_qrcode"

    def get(self, request, pk):
        qr = get_object_or_404(QRCode, pk=pk)
        url = qr_public_url(request, qr)
        fmt = "png" if request.GET.get("fmt") == "png" else "svg"
        body = make_png(url) if fmt == "png" else make_svg(url)
        from django.http import HttpResponse

        response = HttpResponse(body, content_type="image/png" if fmt == "png" else "image/svg+xml")
        if request.GET.get("download"):
            response["Content-Disposition"] = f'attachment; filename="vante-qr-{qr.code}.{fmt}"'
        return response


class VisitStatsView(PanelMixin, TemplateView):
    permission_required = "Core.view_qrcode"
    template_name = "Panel/visit_stats.html"
    section = "visits"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        today = timezone.localdate()
        visits = DailyVisit.objects.all()

        def total(since=None):
            qs = visits.filter(date__gte=since) if since else visits
            agg = qs.aggregate(v=Sum("views"), u=Sum("visitors"))
            return {"views": agg["v"] or 0, "visitors": agg["u"] or 0}

        month_rows = visits.filter(date__gte=today - timedelta(days=29))
        per_day = {}
        for r in month_rows:
            per_day[r.date] = per_day.get(r.date, 0) + r.views
        by_lang = {r["lang"]: r["v"] for r in visits.values("lang").annotate(v=Sum("views"))}
        scans = QRScan.objects.all()
        rows = catalog_rows()
        context.update(
            today=total(today),
            week=total(today - timedelta(days=6)),
            month=total(today - timedelta(days=29)),
            overall=total(),
            series=day_series(per_day),
            fa_views=by_lang.get("fa", 0),
            en_views=by_lang.get("en", 0),
            scan_total=scans.count(),
            scan_month=scans.filter(scanned_at__gte=timezone.now() - timedelta(days=30)).count(),
            catalog_downloads=sum(r["obj"].download_count for r in rows if r["obj"]),
        )
        return context


# ---------------------------------------------------------------- لاگ ورود (فقط سوپریوزر)

class LoginLogView(PanelMixin, ListView):
    permission_required = "Core.view_loginattempt"
    template_name = "Panel/login_log.html"
    context_object_name = "attempts"
    paginate_by = 25
    section = "login_log"

    def get_queryset(self):
        qs = LoginAttempt.objects.all()
        g = self.request.GET
        if g.get("status") == "failed":
            qs = qs.filter(success=False)
        elif g.get("status") == "success":
            qs = qs.filter(success=True)
        if g.get("device") in DEVICE_LABELS:
            qs = qs.filter(device_type=g["device"])
        if g.get("source") in ("panel", "admin"):
            qs = qs.filter(source=g["source"])
        if q := g.get("q", "").strip():
            qs = qs.filter(Q(username__icontains=q) | Q(device_model__icontains=q) | Q(ip__icontains=q) | Q(os__icontains=q))
        return qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        now = timezone.now()
        day = LoginAttempt.objects.filter(created_at__gte=now - timedelta(hours=24))
        failed_week = LoginAttempt.objects.filter(success=False, created_at__gte=now - timedelta(days=7))
        suspicious = list(
            LoginAttempt.objects.filter(success=False, created_at__gte=now - timedelta(hours=1))
            .exclude(ip=None).values("ip").annotate(n=Count("id")).filter(n__gte=5).order_by("-n")
        )
        params = self.request.GET.copy()
        params.pop("page", None)
        context.update(
            failed_day=day.filter(success=False).count(),
            success_day=day.filter(success=True).count(),
            ips_day=day.filter(success=False).exclude(ip=None).values("ip").distinct().count(),
            suspicious=suspicious,
            top_usernames=breakdown(failed_week, "username", limit=6),
            top_devices=breakdown(failed_week.exclude(device_model=""), "device_model", limit=6),
            top_systems=breakdown(failed_week, "os", limit=6),
            device_labels=DEVICE_LABELS,
            f=self.request.GET,
            filtered=bool(params),
            query=params.urlencode(),
            total=context["paginator"].count,
        )
        return context


# ---------------------------------------------------------------- مدیریت اعضا (فقط مدیر ارشد)

class SeniorMixin(LoginRequiredMixin):
    """فقط مدیر ارشد (سوپریوزر)؛ بقیهٔ اعضا صفحهٔ «دسترسی ندارید» می‌بینند."""

    login_url = reverse_lazy("panel:login")
    section = "users"

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated and not request.user.is_superuser:
            return render(request, "Panel/forbidden.html", status=403)
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["section"] = self.section
        return context


def other_active_seniors(user):
    return get_user_model().objects.filter(is_superuser=True, is_active=True).exclude(pk=user.pk)


class UserListView(SeniorMixin, ListView):
    template_name = "Panel/user_list.html"
    context_object_name = "members"
    paginate_by = PAGE_SIZE

    def get_queryset(self):
        qs = get_user_model().objects.order_by("-is_superuser", "username")
        if q := self.request.GET.get("q", "").strip():
            qs = qs.filter(Q(username__icontains=q) | Q(first_name__icontains=q) | Q(last_name__icontains=q) | Q(email__icontains=q))
        return qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        members = list(context["members"])
        groups = {u.pk: list(u.groups.values_list("name", flat=True)) for u in members}
        for m in members:
            m.role_key = user_role(m)
            m.role_title = ROLES[m.role_key][0] if m.role_key else "بدون دسترسی"
            m.is_me = m.pk == self.request.user.pk
            m.group_names = groups[m.pk]
        params = self.request.GET.copy()
        params.pop("page", None)
        context.update(members=members, q=self.request.GET.get("q", "").strip(), query=params.urlencode(),
                       total=context["paginator"].count, roles=ROLES)
        return context


class UserFormMixin(SeniorMixin, SuccessMessageMixin):
    model = get_user_model()
    form_class = UserForm
    template_name = "Panel/user_form.html"
    success_url = reverse_lazy("panel:user_list")

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["editor"] = self.request.user
        return kwargs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["roles"] = ROLES
        return context


class UserCreateView(UserFormMixin, CreateView):
    success_message = "عضو جدید ساخته شد."


class UserUpdateView(UserFormMixin, UpdateView):
    success_message = "تغییرات عضو ذخیره شد."


class UserPasswordView(SeniorMixin, FormView):
    """مدیر ارشد گذرواژهٔ یک عضو را عوض می‌کند (رمز فعلی لازم نیست)."""

    template_name = "Panel/user_password.html"
    form_class = PanelSetPasswordForm
    success_url = reverse_lazy("panel:user_list")

    def dispatch(self, request, *args, **kwargs):
        self.member = get_object_or_404(get_user_model(), pk=kwargs["pk"])
        return super().dispatch(request, *args, **kwargs)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["user"] = self.member
        return kwargs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["member"] = self.member
        return context

    def form_valid(self, form):
        form.save()
        if self.member.pk == self.request.user.pk:
            update_session_auth_hash(self.request, self.member)  # خودش را از نشست بیرون نیندازد
        messages.success(self.request, f"گذرواژهٔ «{self.member.username}» تغییر کرد.")
        return super().form_valid(form)


class UserToggleView(SeniorMixin, View):
    """فعال/غیرفعال کردن سریع یک عضو."""

    http_method_names = ["post"]

    def post(self, request, pk):
        member = get_object_or_404(get_user_model(), pk=pk)
        if member.pk == request.user.pk:
            messages.error(request, "نمی‌توانید حساب خودتان را غیرفعال کنید.")
        elif member.is_active and member.is_superuser and not other_active_seniors(member).exists():
            messages.error(request, "این آخرین مدیر ارشد فعال است و نمی‌شود غیرفعالش کرد.")
        else:
            member.is_active = not member.is_active
            member.save(update_fields=["is_active"])
            messages.success(request, f"«{member.username}» {'فعال' if member.is_active else 'غیرفعال'} شد.")
        return redirect("panel:user_list")


class UserDeleteView(SeniorMixin, DeleteView):
    model = get_user_model()
    template_name = "Panel/confirm_delete.html"
    success_url = reverse_lazy("panel:user_list")

    def blocked_reason(self):
        member = self.get_object()
        if member.pk == self.request.user.pk:
            return "نمی‌توانید حساب خودتان را حذف کنید."
        if member.is_superuser and member.is_active and not other_active_seniors(member).exists():
            return "این آخرین مدیر ارشد فعال است و حذف نمی‌شود."
        return ""

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(
            label="عضو", cancel_url=reverse("panel:user_list"), blocked_reason=self.blocked_reason(),
            extra_note="اگر فقط می‌خواهید جلوی ورودش را بگیرید، به‌جای حذف «غیرفعال» کنید تا سابقه‌اش بماند.",
        )
        return context

    def form_valid(self, form):
        reason = self.blocked_reason()
        if reason:
            messages.error(self.request, reason)
            return redirect(self.success_url)
        name = self.object.username
        self.object.delete()
        messages.success(self.request, f"«{name}» حذف شد.")
        return redirect(self.success_url)


# ---------------------------------------------------------------- حساب من (همهٔ اعضا)

class PanelPasswordChangeForm(StyledFormMixin, PasswordChangeForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["old_password"].label = "گذرواژهٔ فعلی"
        self.fields["new_password1"].label = "گذرواژهٔ جدید"
        self.fields["new_password2"].label = "تکرار گذرواژهٔ جدید"


class AccountView(LoginRequiredMixin, TemplateView):
    """هر عضو نام/ایمیل و گذرواژهٔ خودش را اینجا عوض می‌کند (بدون نیاز به سطح دسترسی خاص)."""

    login_url = reverse_lazy("panel:login")
    template_name = "Panel/account.html"

    def forms(self, data=None, which=""):
        user = self.request.user
        return (
            ProfileForm(data if which == "profile" else None, instance=user, prefix="p"),
            PanelPasswordChangeForm(user, data if which == "password" else None, prefix="w"),
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        profile, password = kwargs.get("forms") or self.forms()
        role = user_role(self.request.user)
        context.update(section="account", profile_form=profile, password_form=password,
                       role_title=ROLES[role][0] if role else "بدون دسترسی")
        return context

    def post(self, request, *args, **kwargs):
        which = request.POST.get("which", "")
        profile, password = self.forms(request.POST, which)
        if which == "profile" and profile.is_valid():
            profile.save()
            messages.success(request, "مشخصات شما ذخیره شد.")
            return redirect("panel:account")
        if which == "password" and password.is_valid():
            user = password.save()
            update_session_auth_hash(request, user)  # بعد از تغییر رمز از پنل بیرون نیفتد
            messages.success(request, "گذرواژه تغییر کرد.")
            return redirect("panel:account")
        return self.render_to_response(self.get_context_data(forms=(profile, password)))
