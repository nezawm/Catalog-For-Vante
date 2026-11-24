"""داشبورد، کد QR، آمار بازدید و لاگ ورود."""
from django.contrib.messages.views import SuccessMessageMixin
from datetime import timedelta
from django.db.models import Count, Q, Sum
from django.db.models.functions import TruncDate
from django.shortcuts import get_object_or_404
from django.urls import reverse, reverse_lazy
from django.views import View
from django.utils import timezone
from django.views.generic import CreateView, DetailView, ListView, TemplateView, UpdateView
from Category.models import Category, Subcategory
from Core.models import DailyVisit, LoginAttempt, QRCode, QRScan
from Core.qr import make_png, make_svg
from Core.useragent import DEVICE_LABELS
from Product.models import Product

from ..forms import QRCodeForm
from .base import PanelDeleteView, PanelMixin
from .catalog import catalog_rows


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
