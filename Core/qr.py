"""ساخت تصویر QR (SVG برای چاپ باکیفیت، PNG برای استفاده‌های عمومی)."""
import io

import qrcode
import qrcode.image.svg
from qrcode.constants import ERROR_CORRECT_M


def _qr(url):
    code = qrcode.QRCode(error_correction=ERROR_CORRECT_M, box_size=12, border=3)
    code.add_data(url)
    code.make(fit=True)
    return code


def make_svg(url):
    buf = io.BytesIO()
    _qr(url).make_image(image_factory=qrcode.image.svg.SvgPathImage).save(buf)
    return buf.getvalue()


def make_png(url):
    buf = io.BytesIO()
    _qr(url).make_image(fill_color="black", back_color="white").save(buf, format="PNG")
    return buf.getvalue()
