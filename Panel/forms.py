from django import forms
from django.forms import inlineformset_factory
from django.contrib.auth import get_user_model, password_validation
from django.contrib.auth.forms import AuthenticationForm, SetPasswordForm, UsernameField

from Category.models import Category, Subcategory
from Core.models import CatalogFile, QRCode
from Product.models import Product, Vanlite

from .groups import ROLES, user_role


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


class VanliteForm(StyledFormMixin, forms.ModelForm):
    """یک ردیف ونلایت داخل فرم محصول؛ همان داده‌ای که سایت در جدول ونلایت نشان می‌دهد."""

    class Meta:
        model = Vanlite
        fields = (
            "name", "type", "product_code", "roll_size", "durability_years", "colors",
            "name_en", "type_en", "product_code_en", "roll_size_en", "durability_years_en", "colors_en",
            "order", "is_active",
        )
        labels = {
            "name": "نام",
            "type": "نوع (EGP / HIP)",
            "product_code": "کد محصول",
            "roll_size": "ابعاد رول (متر)",
            "durability_years": "دوام (سال)",
            "colors": "رنگ‌ها",
            "name_en": "Name (English)",
            "type_en": "Type (English)",
            "product_code_en": "Product code (English)",
            "roll_size_en": "Roll size (English)",
            "durability_years_en": "Durability, years (English)",
            "colors_en": "Colors (English)",
            "order": "ترتیب",
            "is_active": "فعال (در سایت نمایش داده شود)",
        }
        widgets = {
            "product_code": forms.TextInput(attrs={"dir": "ltr"}),
            "roll_size": forms.TextInput(attrs={"dir": "ltr", "placeholder": "1.22 × 45.7"}),
            "durability_years": forms.NumberInput(attrs={"min": 0, "placeholder": "مثلاً ۷"}),
            "colors": forms.TextInput(attrs={"placeholder": "سفید - قرمز - سبز"}),
            "name_en": forms.TextInput(attrs={"dir": "ltr"}),
            "type_en": forms.TextInput(attrs={"dir": "ltr"}),
            "product_code_en": forms.TextInput(attrs={"dir": "ltr"}),
            "roll_size_en": forms.TextInput(attrs={"dir": "ltr"}),
            "durability_years_en": forms.NumberInput(attrs={"min": 0}),
            "colors_en": forms.TextInput(attrs={"dir": "ltr", "placeholder": "White - Red - Green"}),
            "order": forms.NumberInput(attrs={"min": 0}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # نام خالی در ذخیره با نام محصول پر می‌شود.
        self.fields["name"].required = False


def vanlite_formset_class(can_delete):
    return inlineformset_factory(
        Product, Vanlite, form=VanliteForm, extra=0, can_delete=can_delete,
    )


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
        self.moved_products = 0
        if self.instance.pk:
            self.fields["category"].help_text = (
                "اگر دسته‌بندی را عوض کنید، محصولات این زیردسته هم به دستهٔ جدید منتقل می‌شوند."
            )

    def save(self, commit=True):
        # تعداد محصولاتی که همراه زیردسته جابه‌جا می‌شوند (برای پیام موفقیت)
        if commit and self.instance.pk and "category" in self.changed_data:
            self.moved_products = self.instance.products.count()
        return super().save(commit=commit)


class CatalogForm(StyledFormMixin, forms.ModelForm):
    class Meta:
        model = CatalogFile
        fields = ("file", "is_active")
        labels = {
            "file": "فایل PDF",
            "is_active": "کاتالوگ فعال است و دکمهٔ دانلود در سایت نمایش داده شود",
        }
        widgets = {"file": forms.FileInput(attrs={"accept": "application/pdf,.pdf"})}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # در ویرایش، اگر فایل جدیدی انتخاب نشود همان فایل قبلی می‌ماند.
        self.fields["file"].required = not bool(self.instance and self.instance.file)


class QRCodeForm(StyledFormMixin, forms.ModelForm):
    class Meta:
        model = QRCode
        fields = ("name", "target", "is_active")
        labels = {"is_active": "QR فعال است (اگر غیرفعال شود اسکن‌ها به صفحهٔ «پیدا نشد» می‌روند)"}
        widgets = {"name": forms.TextInput(attrs={"placeholder": "مثلاً بنر نمایشگاه"})}


class PanelSetPasswordForm(StyledFormMixin, SetPasswordForm):
    """تعیین رمز جدید برای یک عضو (توسط مدیر ارشد)؛ رمز فعلی لازم نیست."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["new_password1"].label = "گذرواژهٔ جدید"
        self.fields["new_password2"].label = "تکرار گذرواژهٔ جدید"


class UserForm(StyledFormMixin, forms.ModelForm):
    """ساخت/ویرایش عضو. در ساخت، گذرواژه هم گرفته می‌شود."""

    role = forms.ChoiceField(
        label="سطح دسترسی",
        choices=[(key, title) for key, (title, _) in ROLES.items()],
        widget=forms.RadioSelect,
    )
    password1 = forms.CharField(label="گذرواژه", strip=False, required=False,
                                widget=forms.PasswordInput(attrs={"autocomplete": "new-password"}))
    password2 = forms.CharField(label="تکرار گذرواژه", strip=False, required=False,
                                widget=forms.PasswordInput(attrs={"autocomplete": "new-password"}))

    class Meta:
        model = get_user_model()
        fields = ("username", "first_name", "last_name", "email", "is_active")
        labels = {
            "username": "نام کاربری",
            "first_name": "نام",
            "last_name": "نام خانوادگی",
            "email": "ایمیل",
            "is_active": "حساب فعال است (اگر غیرفعال شود نمی‌تواند وارد شود)",
        }
        widgets = {"username": forms.TextInput(attrs={"dir": "ltr", "autocomplete": "off"}),
                   "email": forms.EmailInput(attrs={"dir": "ltr"})}

    def __init__(self, *args, editor=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.editor = editor
        self.creating = self.instance.pk is None
        for name in ("first_name", "last_name", "email"):
            self.fields[name].required = False
        if self.creating:
            self.fields["password1"].required = True
            self.fields["password2"].required = True
            self.fields["is_active"].initial = True
            self.fields["role"].initial = "viewer"
        else:
            self.fields["role"].initial = user_role(self.instance)
            del self.fields["password1"], self.fields["password2"]
        self.is_self = bool(editor and self.instance.pk == editor.pk)
        if self.is_self:  # مدیر نمی‌تواند خودش را غیرفعال یا تنزل دهد
            self.fields["role"].disabled = True
            self.fields["is_active"].disabled = True

    def clean(self):
        data = super().clean()
        if self.creating:
            p1, p2 = data.get("password1"), data.get("password2")
            if p1 and p2 and p1 != p2:
                self.add_error("password2", "دو گذرواژه یکسان نیستند.")
            elif p1:
                temp = get_user_model()(username=data.get("username", ""), email=data.get("email", ""),
                                        first_name=data.get("first_name", ""), last_name=data.get("last_name", ""))
                try:
                    password_validation.validate_password(p1, temp)
                except forms.ValidationError as e:
                    self.add_error("password1", e)
        elif not self.is_self and self.instance.is_superuser:
            # آخرین مدیر ارشدِ فعال نباید تنزل یا غیرفعال شود
            others = get_user_model().objects.filter(is_superuser=True, is_active=True).exclude(pk=self.instance.pk)
            if not others.exists() and (data.get("role") != "senior" or not data.get("is_active")):
                raise forms.ValidationError("این آخرین مدیر ارشد فعال است و نمی‌شود تنزل یا غیرفعالش کرد.")
        return data

    def save(self, commit=True):
        user = super().save(commit=False)
        if self.creating:
            user.set_password(self.cleaned_data["password1"])
        user.save()
        from .groups import set_user_role

        if not self.is_self:
            set_user_role(user, self.cleaned_data["role"])
        return user


class ProfileForm(StyledFormMixin, forms.ModelForm):
    class Meta:
        model = get_user_model()
        fields = ("first_name", "last_name", "email")
        labels = {"first_name": "نام", "last_name": "نام خانوادگی", "email": "ایمیل"}
        widgets = {"email": forms.EmailInput(attrs={"dir": "ltr"})}
