from django.urls import path

from .views import ProductDetailView

app_name = "Product"

urlpatterns = [
    path("<uslug:slug>/", ProductDetailView.as_view(), name="detail"),
]
