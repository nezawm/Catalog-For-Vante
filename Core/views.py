from django.contrib.admin.views.decorators import staff_member_required
from django.http import Http404, HttpResponsePermanentRedirect, JsonResponse
from django.views.generic import TemplateView
import re

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


class LanguageSelectView(TemplateView):
    template_name = "Core/language_select.html"


@staff_member_required
def admin_slugify(request):
    """پیش‌نمایش زندهٔ اسلاگ انگلیسی برای ادمین (فقط کاربران staff)."""
    return JsonResponse({"slug": make_slug(request.GET.get("text", "")[:200], fallback="")})
