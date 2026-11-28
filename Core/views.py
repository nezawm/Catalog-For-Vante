import re

from django.contrib.admin.views.decorators import staff_member_required
from django.http import FileResponse, Http404, HttpResponsePermanentRedirect, HttpResponseRedirect, JsonResponse
from django.db.models import Prefetch
from django.shortcuts import get_object_or_404
from django.utils.translation import get_language
from django.views.decorators.http import require_safe
from django.views.generic import TemplateView
from Category.models import Category, Subcategory
from Product.models import Product

from .models import CatalogFile, QRCode, QRScan
from .translations import TRANSLATIONS
from .useragent import is_bot, parse_user_agent, visitor_hash
from .slugs import make_slug


class SlugDetailMixin:
    """جستجوی آبجکت با اسلاگِ آدرس (بدون id).

    آدرس‌های قدیمیِ «اسلاگ-id» (مثل vancal-5) هنوز کار می‌کنند و ریدایرکت دائم به آدرس تمیز می‌شوند.
    """

    slug_kwarg = "slug"

    def slug_lookup(self):
        """فیلترهای اضافه برای پیدا کردن با اسلاگ (مثلاً دستهٔ والد برای زیردسته)."""
        return {}

    def get_object(self, queryset=None):
        queryset = self.get_queryset() if queryset is None else queryset
        slug = self.kwargs[self.slug_kwarg]
        obj = queryset.filter(slug=slug, **self.slug_lookup()).first()
        if obj is not None:
            self.legacy_url = False
            return obj
        match = re.search(r"(?:^|-)(\d+)$", slug)
        if match:
            obj = queryset.filter(pk=int(match.group(1))).first()
            if obj is not None:
                self.legacy_url = True
                return obj
        raise Http404

    def get(self, request, *args, **kwargs):
        self.object = self.get_object()
        if self.legacy_url:
            query = request.META.get("QUERY_STRING")
            return HttpResponsePermanentRedirect(self.object.get_absolute_url() + (f"?{query}" if query else ""))
        return self.render_to_response(self.get_context_data(object=self.object))


class HomeView(TemplateView):
    template_name = "Core/home.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["catalog_sections"] = self.catalog_sections()
        return context

    @staticmethod
    def catalog_sections():
        """همهٔ دسته‌ها با محصولاتشان برای نمایش در همان صفحهٔ اصلی (با کلیک روی «مشاهده محصولات»).

        مثل صفحهٔ هر دسته: اول محصولات هر زیردسته، بعد محصولاتِ بدون زیردسته زیر «سایر محصولات».
        """
        lang = (get_language() or "fa")[:2]
        other_title = TRANSLATIONS.get(lang, TRANSLATIONS["fa"])["other_products"]

        categories = Category.objects.filter(is_active=True).prefetch_related(
            Prefetch("subcategories", queryset=Subcategory.objects.filter(is_active=True), to_attr="active_subs"),
            Prefetch("products", queryset=Product.objects.filter(is_active=True), to_attr="active_products"),
        )
        sections = []
        for category in categories:
            by_sub = {}
            loose = []
            sub_ids = {sub.pk for sub in category.active_subs}
            for product in category.active_products:
                if product.subcategory_id in sub_ids:
                    by_sub.setdefault(product.subcategory_id, []).append(product)
                else:
                    loose.append(product)
            groups = [
                {"title": sub.display_name, "url": sub.get_absolute_url(), "products": by_sub[sub.pk]}
                for sub in category.active_subs
                if sub.pk in by_sub
            ]
            if loose:
                groups.append({"title": other_title if groups else "", "url": "", "products": loose})
            sections.append({"category": category, "groups": groups})
        return sections


@staff_member_required
def admin_slugify(request):
    """پیش‌نمایش زندهٔ اسلاگ انگلیسی برای ادمین (فقط کاربران staff)."""
    return JsonResponse({"slug": make_slug(request.GET.get("text", "")[:200], fallback="")})


@require_safe
def catalog_download(request, lang):
    """دانلود PDF کاتالوگِ همان زبان؛ فقط اگر فایل آپلود شده و فعال باشد. هر دانلود شمرده می‌شود."""
    catalog = (
        CatalogFile.objects.filter(language=lang, is_active=True).exclude(file="").first()
    )
    if catalog is None:
        raise Http404
    try:
        handle = catalog.file.storage.open(catalog.file.name, "rb")
    except (FileNotFoundError, ValueError):
        raise Http404
    if request.method == "GET":
        catalog.record_download()
    return FileResponse(handle, as_attachment=True, filename=catalog.download_filename, content_type="application/pdf")


@require_safe
def qr_scan(request, code):
    """آدرس کوتاهِ داخل QR: اسکن را ثبت می‌کند (ربات‌ها و پیش‌نمایش‌های پیام‌رسان‌ها نه) و به مقصد می‌رود."""
    qr = get_object_or_404(QRCode, code=code, is_active=True)
    ua = request.META.get("HTTP_USER_AGENT", "")
    if request.method == "GET" and not is_bot(ua):
        info = parse_user_agent(ua)
        QRScan.objects.create(
            qr=qr,
            device_type=info["device_type"],
            device_model=info["device_model"],
            os=info["os"],
            browser=info["browser"],
            visitor=visitor_hash(request),
        )
    response = HttpResponseRedirect(qr.target)
    response["Cache-Control"] = "no-store"  # تا هر اسکن به سرور برسد
    return response


