"""ویوهای پنل مدیریت، تقسیم‌شده بر اساس بخش؛ urls.py و تست‌ها همچنان با «views.<Name>» به همه دسترسی دارند.

base: مجوزها و حذف | auth: ورود/حساب من | products: محصول/دسته/زیردسته |
catalog: PDF کاتالوگ | stats: داشبورد، QR، بازدید، لاگ ورود | users: مدیریت اعضا
"""
from .base import (  # noqa: F401
    PAGE_SIZE,
    PanelDeleteView,
    PanelMixin,
)
from .auth import (  # noqa: F401
    AccountView,
    PanelLoginView,
    PanelLogoutView,
    PanelPasswordChangeForm,
    SlugPreviewView,
)
from .products import (  # noqa: F401
    CategoryCreateView,
    CategoryDeleteView,
    CategoryFormMixin,
    CategoryListView,
    CategoryUpdateView,
    ProductCreateView,
    ProductDeleteView,
    ProductFormMixin,
    ProductListView,
    ProductUpdateView,
    SubcategoryCreateView,
    SubcategoryDeleteView,
    SubcategoryFormMixin,
    SubcategoryListView,
    SubcategoryUpdateView,
    VANLITE_PREFIX,
    duplicate_product_names,
    product_title,
    subcategory_map,
)
from .catalog import (  # noqa: F401
    CATALOG_LANGUAGES,
    CatalogDeleteView,
    CatalogListView,
    CatalogPreviewView,
    CatalogToggleView,
    CatalogUploadView,
    catalog_lang,
    catalog_rows,
)
from .stats import (  # noqa: F401
    DashboardView,
    LoginLogView,
    QRCreateView,
    QRDeleteView,
    QRDetailView,
    QRFormMixin,
    QRImageView,
    QRListView,
    QRUpdateView,
    VisitStatsView,
    breakdown,
    day_series,
    qr_public_url,
)
from .users import (  # noqa: F401
    SeniorMixin,
    UserCreateView,
    UserDeleteView,
    UserFormMixin,
    UserListView,
    UserPasswordView,
    UserToggleView,
    UserUpdateView,
    other_active_seniors,
)
