"""مدیریت اعضا (فقط مدیر ارشد)."""
from django.contrib import messages
from django.contrib.auth import get_user_model, update_session_auth_hash
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.messages.views import SuccessMessageMixin
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse, reverse_lazy
from django.views import View
from django.views.generic import CreateView, DeleteView, FormView, ListView, UpdateView

from ..forms import PanelSetPasswordForm, UserForm
from ..groups import ROLES, user_role
from .base import PAGE_SIZE


# ---------------------------------------------------------------- مدیریت اعضا (فقط مدیر ارشد)

class SeniorMixin(LoginRequiredMixin):
    """فقط مدیر ارشد (سوپریوزر)؛ بقیهٔ اعضا صفحهٔ «دسترسی ندارید» می‌بینند."""

    login_url = reverse_lazy("panel:login")
    section = "users"

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated and not request.user.is_superuser:
            return render(request, "Panel/forbidden.html", status=403)
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["section"] = self.section
        return context


def other_active_seniors(user):
    return get_user_model().objects.filter(is_superuser=True, is_active=True).exclude(pk=user.pk)


class UserListView(SeniorMixin, ListView):
    template_name = "Panel/user_list.html"
    context_object_name = "members"
    paginate_by = PAGE_SIZE

    def get_queryset(self):
        qs = get_user_model().objects.order_by("-is_superuser", "username")
        if q := self.request.GET.get("q", "").strip():
            qs = qs.filter(Q(username__icontains=q) | Q(first_name__icontains=q) | Q(last_name__icontains=q) | Q(email__icontains=q))
        return qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        members = list(context["members"])
        groups = {u.pk: list(u.groups.values_list("name", flat=True)) for u in members}
        for m in members:
            m.role_key = user_role(m)
            m.role_title = ROLES[m.role_key][0] if m.role_key else "بدون دسترسی"
            m.is_me = m.pk == self.request.user.pk
            m.group_names = groups[m.pk]
        params = self.request.GET.copy()
        params.pop("page", None)
        context.update(members=members, q=self.request.GET.get("q", "").strip(), query=params.urlencode(),
                       total=context["paginator"].count, roles=ROLES)
        return context


class UserFormMixin(SeniorMixin, SuccessMessageMixin):
    model = get_user_model()
    form_class = UserForm
    template_name = "Panel/user_form.html"
    success_url = reverse_lazy("panel:user_list")

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["editor"] = self.request.user
        return kwargs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["roles"] = ROLES
        return context


class UserCreateView(UserFormMixin, CreateView):
    success_message = "عضو جدید ساخته شد."


class UserUpdateView(UserFormMixin, UpdateView):
    success_message = "تغییرات عضو ذخیره شد."


class UserPasswordView(SeniorMixin, FormView):
    """مدیر ارشد گذرواژهٔ یک عضو را عوض می‌کند (رمز فعلی لازم نیست)."""

    template_name = "Panel/user_password.html"
    form_class = PanelSetPasswordForm
    success_url = reverse_lazy("panel:user_list")

    def dispatch(self, request, *args, **kwargs):
        self.member = get_object_or_404(get_user_model(), pk=kwargs["pk"])
        return super().dispatch(request, *args, **kwargs)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["user"] = self.member
        return kwargs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["member"] = self.member
        return context

    def form_valid(self, form):
        form.save()
        if self.member.pk == self.request.user.pk:
            update_session_auth_hash(self.request, self.member)  # خودش را از نشست بیرون نیندازد
        messages.success(self.request, f"گذرواژهٔ «{self.member.username}» تغییر کرد.")
        return super().form_valid(form)


class UserToggleView(SeniorMixin, View):
    """فعال/غیرفعال کردن سریع یک عضو."""

    http_method_names = ["post"]

    def post(self, request, pk):
        member = get_object_or_404(get_user_model(), pk=pk)
        if member.pk == request.user.pk:
            messages.error(request, "نمی‌توانید حساب خودتان را غیرفعال کنید.")
        elif member.is_active and member.is_superuser and not other_active_seniors(member).exists():
            messages.error(request, "این آخرین مدیر ارشد فعال است و نمی‌شود غیرفعالش کرد.")
        else:
            member.is_active = not member.is_active
            member.save(update_fields=["is_active"])
            messages.success(request, f"«{member.username}» {'فعال' if member.is_active else 'غیرفعال'} شد.")
        return redirect("panel:user_list")


class UserDeleteView(SeniorMixin, DeleteView):
    model = get_user_model()
    template_name = "Panel/confirm_delete.html"
    success_url = reverse_lazy("panel:user_list")

    def blocked_reason(self):
        member = self.get_object()
        if member.pk == self.request.user.pk:
            return "نمی‌توانید حساب خودتان را حذف کنید."
        if member.is_superuser and member.is_active and not other_active_seniors(member).exists():
            return "این آخرین مدیر ارشد فعال است و حذف نمی‌شود."
        return ""

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(
            label="عضو", cancel_url=reverse("panel:user_list"), blocked_reason=self.blocked_reason(),
            extra_note="اگر فقط می‌خواهید جلوی ورودش را بگیرید، به‌جای حذف «غیرفعال» کنید تا سابقه‌اش بماند.",
        )
        return context

    def form_valid(self, form):
        reason = self.blocked_reason()
        if reason:
            messages.error(self.request, reason)
            return redirect(self.success_url)
        name = self.object.username
        self.object.delete()
        messages.success(self.request, f"«{name}» حذف شد.")
        return redirect(self.success_url)
