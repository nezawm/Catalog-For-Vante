from django.shortcuts import render

# Create your views here.
from django.views.generic import DetailView

from Core.views import SlugDetailMixin

from .models import Product


class ProductDetailView(SlugDetailMixin, DetailView):
    template_name = "Product/product_detail.html"
    context_object_name = "product"

    def get_queryset(self):
        return Product.objects.filter(is_active=True, category__is_active=True).select_related("category", "subcategory").prefetch_related("vanlite_items")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # فقط فعال‌ها نمایش داده می‌شوند؛ ستون «رنگ‌ها» فقط وقتی دست‌کم یک ردیف رنگ دارد.
        items = [v for v in self.object.vanlite_items.all() if v.is_active]
        context["vanlite_items"] = items
        context["show_vanlite_colors"] = any(v.display_colors for v in items)
        return context
