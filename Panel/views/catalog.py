"""کاتالوگ PDF فارسی/انگلیسی."""
from django.contrib import messages
from django.contrib.messages.views import SuccessMessageMixin
from django.db import transaction
from django.http import FileResponse, Http404
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse_lazy
from django.views import View
from django.views.generic import TemplateView, UpdateView
from Core.models import CatalogFile

from ..forms import CatalogForm
from .base import PanelDeleteView, PanelMixin


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

    def form_valid(self, form):
        # رکورد و فایل جدید در یک تراکنش؛ فایل قبلی فقط بعد از موفقیت کامل (on_commit) پاک می‌شود.
        with transaction.atomic():
            return super().form_valid(form)

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
