"""
URL configuration for VanteCTL project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/6.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
from django.views.generic import RedirectView
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""

from django.conf import settings
from django.conf.urls.i18n import i18n_patterns
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path
from django.views.generic import RedirectView

from Core.views import admin_slugify, catalog_download, qr_scan

urlpatterns = [
    path("admin/slugify/", admin_slugify, name="admin_slugify"),
    path("admin/", admin.site.urls),
    path("panel/", include("Panel.urls")),
    path("catalog/<slug:lang>/", catalog_download, name="catalog_download"),
    path("q/<slug:code>/", qr_scan, name="qr_scan"),
    # صفحهٔ انتخاب زبان حذف شد؛ ورود به ریشه مستقیم به صفحهٔ اصلیِ فارسی می‌رود (تغییر زبان از هدر).
    path("", RedirectView.as_view(url="/fa/", query_string=False, permanent=False), name="root"),
]

urlpatterns += i18n_patterns(
    path("categories/", include("Category.urls")),
    path("products/", include("Product.urls")),
    path("", include("Core.urls")),
)

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
