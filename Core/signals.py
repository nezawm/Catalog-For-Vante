import logging

from django.contrib.auth.signals import user_logged_in, user_login_failed
from django.dispatch import receiver

from .models import LoginAttempt
from .useragent import client_ip, parse_user_agent

logger = logging.getLogger(__name__)


def _source(request):
    path = getattr(request, "path", "") or ""
    if path.startswith("/panel/"):
        return "panel"
    if path.startswith("/admin/"):
        return "admin"
    return ""


def _log(request, username, success):
    source = _source(request) if request is not None else ""
    if not source:  # فقط ورود به پنل و ادمین ثبت می‌شود
        return
    try:
        ua = request.META.get("HTTP_USER_AGENT", "")[:500]
        info = parse_user_agent(ua)
        LoginAttempt.objects.create(
            username=(username or "")[:150],
            success=success,
            source=source,
            ip=client_ip(request),
            device_type=info["device_type"],
            device_model=info["device_model"],
            os=info["os"],
            browser=info["browser"],
            user_agent=ua,
        )
    except Exception:  # لاگ هرگز نباید ورود را خراب کند
        logger.exception("login attempt log failed")


@receiver(user_login_failed)
def log_failed_login(sender, credentials, request=None, **kwargs):
    _log(request, credentials.get("username", ""), False)


@receiver(user_logged_in)
def log_successful_login(sender, request, user, **kwargs):
    _log(request, user.get_username(), True)
