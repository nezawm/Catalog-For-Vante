from django.urls import path

from . import views

app_name = "panel"

urlpatterns = [
    path("", views.DashboardView.as_view(), name="dashboard"),
    path("login/", views.PanelLoginView.as_view(), name="login"),
    path("logout/", views.PanelLogoutView.as_view(), name="logout"),
    path("slugify/", views.SlugPreviewView.as_view(), name="slugify"),

    path("products/", views.ProductListView.as_view(), name="product_list"),
    path("products/new/", views.ProductCreateView.as_view(), name="product_create"),
    path("products/<int:pk>/", views.ProductUpdateView.as_view(), name="product_update"),
    path("products/<int:pk>/delete/", views.ProductDeleteView.as_view(), name="product_delete"),

    path("categories/", views.CategoryListView.as_view(), name="category_list"),
    path("categories/new/", views.CategoryCreateView.as_view(), name="category_create"),
    path("categories/<int:pk>/", views.CategoryUpdateView.as_view(), name="category_update"),
    path("categories/<int:pk>/delete/", views.CategoryDeleteView.as_view(), name="category_delete"),

    path("subcategories/", views.SubcategoryListView.as_view(), name="subcategory_list"),
    path("subcategories/new/", views.SubcategoryCreateView.as_view(), name="subcategory_create"),
    path("subcategories/<int:pk>/", views.SubcategoryUpdateView.as_view(), name="subcategory_update"),
    path("subcategories/<int:pk>/delete/", views.SubcategoryDeleteView.as_view(), name="subcategory_delete"),
]
