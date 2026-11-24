"""ورود، خروج و «حساب من»."""
from django.contrib import messages
from django.contrib.auth import update_session_auth_hash
from django.contrib.auth.forms import PasswordChangeForm
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.views import LoginView, LogoutView
from django.http import JsonResponse
from django.shortcuts import redirect
from django.urls import reverse, reverse_lazy
from django.views import View
from django.views.generic import TemplateView
from Core.slugs import make_slug

from ..forms import PanelLoginForm, ProfileForm, StyledFormMixin
from ..groups import ROLES, user_role


# ---------------------------------------------------------------- ورود و خروج

class PanelLoginView(LoginView):
    template_name = "Panel/login.html"
    authentication_form = PanelLoginForm
    redirect_authenticated_user = True

    def get_default_redirect_url(self):
        return reverse("panel:dashboard")


class PanelLogoutView(LogoutView):
    next_page = reverse_lazy("panel:login")


class SlugPreviewView(LoginRequiredMixin, View):
    login_url = reverse_lazy("panel:login")

    def get(self, request):
        text = request.GET.get("text", "")[:200]
        return JsonResponse({"slug": make_slug(text, fallback="")})


# ---------------------------------------------------------------- حساب من (همهٔ اعضا)

class PanelPasswordChangeForm(StyledFormMixin, PasswordChangeForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["old_password"].label = "گذرواژهٔ فعلی"
        self.fields["new_password1"].label = "گذرواژهٔ جدید"
        self.fields["new_password2"].label = "تکرار گذرواژهٔ جدید"


class AccountView(LoginRequiredMixin, TemplateView):
    """هر عضو نام/ایمیل و گذرواژهٔ خودش را اینجا عوض می‌کند (بدون نیاز به سطح دسترسی خاص)."""

    login_url = reverse_lazy("panel:login")
    template_name = "Panel/account.html"

    def forms(self, data=None, which=""):
        user = self.request.user
        return (
            ProfileForm(data if which == "profile" else None, instance=user, prefix="p"),
            PanelPasswordChangeForm(user, data if which == "password" else None, prefix="w"),
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        profile, password = kwargs.get("forms") or self.forms()
        role = user_role(self.request.user)
        context.update(section="account", profile_form=profile, password_form=password,
                       role_title=ROLES[role][0] if role else "بدون دسترسی")
        return context

    def post(self, request, *args, **kwargs):
        which = request.POST.get("which", "")
        profile, password = self.forms(request.POST, which)
        if which == "profile" and profile.is_valid():
            profile.save()
            messages.success(request, "مشخصات شما ذخیره شد.")
            return redirect("panel:account")
        if which == "password" and password.is_valid():
            user = password.save()
            update_session_auth_hash(request, user)  # بعد از تغییر رمز از پنل بیرون نیفتد
            messages.success(request, "گذرواژه تغییر کرد.")
            return redirect("panel:account")
        return self.render_to_response(self.get_context_data(forms=(profile, password)))
