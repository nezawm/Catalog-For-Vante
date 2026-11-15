from django.urls import path

from .views import CategoryDetailView, CategoryListView, SubcategoryDetailView

app_name = "Category"

urlpatterns = [
    path("", CategoryListView.as_view(), name="list"),
    path("<uslug:slug>/", CategoryDetailView.as_view(), name="detail"),
    path("<uslug:category_slug>/<uslug:slug>/", SubcategoryDetailView.as_view(), name="subcategory"),
]
