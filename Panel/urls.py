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

    path("catalog/", views.CatalogListView.as_view(), name="catalog"),
    path("catalog/<slug:lang>/", views.CatalogUploadView.as_view(), name="catalog_upload"),
    path("catalog/<slug:lang>/preview/", views.CatalogPreviewView.as_view(), name="catalog_preview"),
    path("catalog/<slug:lang>/toggle/", views.CatalogToggleView.as_view(), name="catalog_toggle"),
    path("catalog/<slug:lang>/delete/", views.CatalogDeleteView.as_view(), name="catalog_delete"),

    path("qr/", views.QRListView.as_view(), name="qr_list"),
    path("qr/new/", views.QRCreateView.as_view(), name="qr_create"),
    path("qr/<int:pk>/", views.QRDetailView.as_view(), name="qr_detail"),
    path("qr/<int:pk>/edit/", views.QRUpdateView.as_view(), name="qr_update"),
    path("qr/<int:pk>/delete/", views.QRDeleteView.as_view(), name="qr_delete"),
    path("qr/<int:pk>/image/", views.QRImageView.as_view(), name="qr_image"),
    path("visits/", views.VisitStatsView.as_view(), name="visits"),
    path("login-log/", views.LoginLogView.as_view(), name="login_log"),

    path("users/", views.UserListView.as_view(), name="user_list"),
    path("users/new/", views.UserCreateView.as_view(), name="user_create"),
    path("users/<int:pk>/", views.UserUpdateView.as_view(), name="user_update"),
    path("users/<int:pk>/password/", views.UserPasswordView.as_view(), name="user_password"),
    path("users/<int:pk>/toggle/", views.UserToggleView.as_view(), name="user_toggle"),
    path("users/<int:pk>/delete/", views.UserDeleteView.as_view(), name="user_delete"),
    path("account/", views.AccountView.as_view(), name="account"),
]
