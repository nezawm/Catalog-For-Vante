from django.utils import translation


class PanelFarsiMiddleware:
    """پنل کارفرما همیشه فارسی است، مستقل از زبان مرورگر یا زبان سایت."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.path.startswith("/panel/"):
            translation.activate("fa")
            request.LANGUAGE_CODE = "fa"
        return self.get_response(request)
