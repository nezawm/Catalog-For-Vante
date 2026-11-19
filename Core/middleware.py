import logging

from django.db.models import F
from django.utils import timezone

from .models import DailyVisit
from .useragent import is_bot

logger = logging.getLogger(__name__)

VISITOR_COOKIE = "vante_v"


class VisitCounterMiddleware:
    """شمارش بازدید صفحات سایت (فقط GET موفق /fa/ و /en/، بدون ربات).
    بازدیدکنندهٔ یکتا با یک کوکی که تا پایان همان روز می‌ماند حساب می‌شود."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        path = request.path
        if (
            request.method == "GET"
            and response.status_code == 200
            and (path.startswith("/fa/") or path.startswith("/en/"))
            and not is_bot(request.META.get("HTTP_USER_AGENT", ""))
        ):
            try:
                self.count(request, response, path[1:3])
            except Exception:
                logger.exception("visit counter failed")
        return response

    def count(self, request, response, lang):
        now = timezone.localtime()
        today = now.date()
        is_new_visitor = request.COOKIES.get(VISITOR_COOKIE) != today.isoformat()
        row, _ = DailyVisit.objects.get_or_create(date=today, lang=lang)
        DailyVisit.objects.filter(pk=row.pk).update(
            views=F("views") + 1,
            visitors=F("visitors") + (1 if is_new_visitor else 0),
        )
        if is_new_visitor:
            midnight = now.replace(hour=23, minute=59, second=59, microsecond=0)
            response.set_cookie(
                VISITOR_COOKIE, today.isoformat(),
                max_age=max(int((midnight - now).total_seconds()), 60), samesite="Lax", httponly=True,
            )
