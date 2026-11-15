from django import forms
from django.contrib.auth.forms import AuthenticationForm, UsernameField

from Category.models import Category, Subcategory
from Product.models import Product


class StyledFormMixin:
    """به همهٔ فیلدها (به جز چک‌باکس) کلاس input می‌دهد تا با استایل پنل بخوانند."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            if isinstance(field.widget, forms.CheckboxInput):
                continue
            css = field.widget.attrs.get("class", "")
            field.widget.attrs["class"] = f"{css} input".strip()


class PanelLoginForm(StyledFormMixin, AuthenticationForm):
    username = UsernameField(
        label="نام کاربری",
        widget=forms.TextInput(attrs={"autofocus": True, "autocomplete": "username"}),
    )
    password = forms.CharField(
        label="گذرواژه",
        strip=False,
        widget=forms.PasswordInput(attrs={"autocomplete": "current-password"}),
    )


class ProductForm(StyledFormMixin, forms.ModelForm):
    class Meta:
        model = Product
        fields = (
            "category", "subcategory", "name", "description",
            "name_en", "description_en", "face_material_en",
            "face_material", "face_value", "face_unit", "liner_gsm", "adhesive",
            "width_107", "width_127", "width_152",
            "is_active", "order",
        )
        labels = {
            "name": "نام محصول",
            "width_107": "عرض ۱/۰۷ متر",
            "width_127": "عرض ۱/۲۷ متر",
            "width_152": "عرض ۱/۵۲ متر",
            "is_active": "محصول فعال است و در سایت نمایش داده شود",
            "name_en": "نام محصول (English)",
            "description_en": "توضیحات (English)",
            "face_material_en": "جنس رویه (English)",
        }
        widgets = {
            "description": forms.Textarea(attrs={"rows": 4}),
            "description_en": forms.Textarea(attrs={"rows": 4, "dir": "ltr"}),
            "name_en": forms.TextInput(attrs={"dir": "ltr"}),
            "face_material_en": forms.TextInput(attrs={"dir": "ltr"}),
            "liner_gsm": forms.NumberInput(attrs={"placeholder": "مثلاً ۱۴۰", "min": 0}),
            "face_value": forms.NumberInput(attrs={"min": 0}),
            "order": forms.NumberInput(attrs={"min": 0}),
            "width_107": forms.TextInput(attrs={"dir": "ltr"}),
            "width_127": forms.TextInput(attrs={"dir": "ltr"}),
            "width_152": forms.TextInput(attrs={"dir": "ltr"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["category"].label_from_instance = lambda c: f"{c.name} — {c.title}"
        self.fields["category"].empty_label = "انتخاب کنید"
        self.fields["subcategory"].queryset = Subcategory.objects.select_related("category")
        self.fields["subcategory"].empty_label = "بدون زیردسته"
        self.fields["adhesive"].choices = [("", "—")] + list(Product.Adhesive.choices)


class CategoryForm(StyledFormMixin, forms.ModelForm):
    class Meta:
        model = Category
        fields = ("name", "title", "description", "title_en", "description_en", "order", "is_active")
        labels = {
            "name": "نام لاتین",
            "title_en": "عنوان (English)",
            "description_en": "توضیحات (English)",
            "is_active": "دسته‌بندی فعال است و در سایت نمایش داده شود",
        }
        widgets = {
            "name": forms.TextInput(attrs={"dir": "ltr"}),
            "title_en": forms.TextInput(attrs={"dir": "ltr"}),
            "description": forms.Textarea(attrs={"rows": 3}),
            "description_en": forms.Textarea(attrs={"rows": 3, "dir": "ltr"}),
            "order": forms.NumberInput(attrs={"min": 0}),
        }


class SubcategoryForm(StyledFormMixin, forms.ModelForm):
    class Meta:
        model = Subcategory
        fields = ("category", "name", "description", "name_en", "description_en", "order", "is_active")
        labels = {
            "category": "دسته‌بندی اصلی",
            "name_en": "نام (English)",
            "description_en": "توضیحات (English)",
            "is_active": "زیردسته فعال است و در سایت نمایش داده شود",
        }
        widgets = {
            "name_en": forms.TextInput(attrs={"dir": "ltr"}),
            "description": forms.Textarea(attrs={"rows": 3}),
            "description_en": forms.Textarea(attrs={"rows": 3, "dir": "ltr"}),
            "order": forms.NumberInput(attrs={"min": 0}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["category"].label_from_instance = lambda c: f"{c.name} — {c.title}"
        self.fields["category"].empty_label = "انتخاب کنید"
