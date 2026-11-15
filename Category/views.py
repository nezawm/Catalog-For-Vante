from django.db.models import Q
from django.views.generic import DetailView, ListView

from Core.views import SlugDetailMixin

from .models import Category, Subcategory


class CategoryListView(ListView):
    template_name = "Category/category_list.html"
    context_object_name = "categories"

    def get_queryset(self):
        return Category.objects.filter(is_active=True)


class CategoryDetailView(SlugDetailMixin, DetailView):
    template_name = "Category/category_detail.html"
    context_object_name = "category"

    def get_queryset(self):
        return Category.objects.filter(is_active=True)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        subcategories = self.object.subcategories.filter(is_active=True)
        products = self.object.products.filter(is_active=True)
        if subcategories:
            # اگر زیردسته دارد، اول زیردسته‌ها نمایش داده می‌شوند؛
            # محصولاتِ بدون زیردسته (هنوز دسته‌بندی‌نشده) پایین‌تر می‌آیند تا گم نشوند.
            products = products.filter(
                Q(subcategory__isnull=True) | Q(subcategory__is_active=False)
            )
        context["subcategories"] = subcategories
        context["products"] = products
        return context


class SubcategoryDetailView(SlugDetailMixin, DetailView):
    template_name = "Category/subcategory_detail.html"
    context_object_name = "subcategory"

    def slug_lookup(self):
        return {"category__slug": self.kwargs["category_slug"]}

    def get_queryset(self):
        return Subcategory.objects.select_related("category").filter(
            is_active=True, category__is_active=True
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["category"] = self.object.category
        context["products"] = self.object.products.filter(is_active=True)
        return context
