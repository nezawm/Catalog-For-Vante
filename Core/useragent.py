"""تشخیص ساده و بدون وابستگی نوع دستگاه، مدل، سیستم‌عامل و مرورگر از User-Agent."""
import hashlib
import re

from django.conf import settings

BOT_RE = re.compile(
    r"bot|crawler|spider|slurp|preview|facebookexternalhit|whatsapp|telegram|curl/|wget|python-requests|"
    r"httpclient|headless|monitor|uptime|lighthouse",
    re.I,
)

DEVICE_LABELS = {
    "mobile": "موبایل",
    "tablet": "تبلت",
    "desktop": "کامپیوتر",
    "bot": "ربات",
    "unknown": "نامشخص",
}


def is_bot(ua):
    return bool(BOT_RE.search(ua or ""))


def parse_user_agent(ua):
    """برمی‌گرداند: device_type (mobile/tablet/desktop/bot/unknown)، device_model، os، browser."""
    ua = (ua or "")[:500]
    result = {"device_type": "unknown", "device_model": "", "os": "", "browser": ""}
    if not ua:
        return result
    if is_bot(ua):
        result["device_type"] = "bot"
        return result

    # --- سیستم‌عامل و دستگاه
    if m := re.search(r"\b(iPhone|iPad|iPod)\b", ua):
        result["device_model"] = m.group(1)
        result["device_type"] = "tablet" if m.group(1) == "iPad" else "mobile"
        v = re.search(r"OS (\d+)[_.](\d+)", ua)
        result["os"] = f"iOS {v.group(1)}.{v.group(2)}" if v else "iOS"
    elif m := re.search(r"Android ([\d.]+)", ua):
        result["os"] = f"Android {m.group(1)}"
        result["device_type"] = "mobile" if "Mobile" in ua else "tablet"
        model = re.search(r"Android [\d.]+; ([^;)]+?)(?: Build/[^;)]*)?(?:;|\))", ua)
        if model:
            name = model.group(1).strip()
            if name and name.lower() not in {"wv", "k", "linux", "mobile"}:
                result["device_model"] = name[:60]
    elif "Windows" in ua:
        result["device_type"] = "desktop"
        result["os"] = "Windows 10/11" if "Windows NT 10" in ua else "Windows"
    elif "CrOS" in ua:
        result["device_type"], result["os"] = "desktop", "ChromeOS"
    elif "Macintosh" in ua or "Mac OS X" in ua:
        result["device_type"], result["os"] = "desktop", "macOS"
    elif "Linux" in ua or "X11" in ua:
        result["device_type"], result["os"] = "desktop", "Linux"

    # --- مرورگر (ترتیب مهم است)
    for pattern, name in (
        (r"EdgA?/|Edg/", "Edge"),
        (r"OPR/|Opera", "Opera"),
        (r"SamsungBrowser", "Samsung Internet"),
        (r"FxiOS|Firefox", "Firefox"),
        (r"CriOS|Chrome/", "Chrome"),
        (r"Version/.*Safari|Safari/", "Safari"),
        (r"MSIE|Trident", "Internet Explorer"),
    ):
        if re.search(pattern, ua):
            result["browser"] = name
            break
    return result


def client_ip(request):
    """آی‌پی کاربر. هدر X-Forwarded-For فقط وقتی معتبر است که LOG_TRUST_PROXY_HEADER=True باشد (پشت nginx)."""
    if getattr(settings, "LOG_TRUST_PROXY_HEADER", False):
        forwarded = request.META.get("HTTP_X_FORWARDED_FOR", "")
        if forwarded:
            return forwarded.split(",")[0].strip() or None
    return request.META.get("REMOTE_ADDR") or None


def visitor_hash(request):
    """شناسهٔ ناشناس (هش آی‌پی + مرورگر) برای شمارش بازدیدکنندهٔ یکتا؛ آی‌پی خام ذخیره نمی‌شود."""
    raw = f"{settings.SECRET_KEY}|{client_ip(request)}|{request.META.get('HTTP_USER_AGENT', '')}"
    return hashlib.sha256(raw.encode()).hexdigest()[:16]
