from django.shortcuts import render

# Create your views here.
from django.views.generic import DetailView

from Core.views import SlugDetailMixin

from .models import Product


class ProductDetailView(SlugDetailMixin, DetailView):
    template_name = "Product/product_detail.html"
    context_object_name = "product"

    def get_queryset(self):
        return Product.objects.filter(is_active=True).select_related("category", "subcategory").prefetch_related("vanlite_items")