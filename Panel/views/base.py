"""پایه‌ی مشترک ویوهای پنل: مجوزها و صفحهٔ تأیید حذف."""
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.db import transaction
from django.db.models.deletion import ProtectedError
from django.shortcuts import redirect, render
from django.urls import reverse, reverse_lazy
from django.views.generic import DeleteView




PAGE_SIZE = 8


class PanelMixin(LoginRequiredMixin, PermissionRequiredMixin):
    """ورود لازم است و کاربر باید مجوز همان مدل را داشته باشد (از گروه «مدیر کاتالوگ» یا سوپریوزر)."""

    login_url = reverse_lazy("panel:login")
    section = ""

    def handle_no_permission(self):
        if self.request.user.is_authenticated:
            return render(self.request, "Panel/forbidden.html", status=403)
        return super().handle_no_permission()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["section"] = self.section
        return context


class PanelDeleteView(PanelMixin, DeleteView):
    """صفحهٔ تأیید حذف؛ اگر حذف ممکن نباشد دلیلش را نشان می‌دهد."""

    template_name = "Panel/confirm_delete.html"
    label = ""
    cancel_url_name = ""

    def blocked_reason(self):
        return ""

    def extra_note(self):
        return ""

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(
            label=self.label,
            blocked_reason=self.blocked_reason(),
            extra_note=self.extra_note(),
            cancel_url=reverse(self.cancel_url_name),
        )
        return context

    def form_valid(self, form):
        reason = self.blocked_reason()
        if reason:
            messages.error(self.request, reason)
            return redirect(self.success_url)
        title = str(self.object)
        try:
            with transaction.atomic():  # حذف فایل‌های وابسته (مثل PDF) بعد از قطعی‌شدن تراکنش انجام می‌شود
                self.object.delete()
        except ProtectedError:
            messages.error(self.request, "این مورد به‌خاطر وابستگی به داده‌های دیگر حذف نمی‌شود.")
            return redirect(self.success_url)
        messages.success(self.request, f"«{title}» حذف شد.")
        return redirect(self.success_url)
