from django.urls import register_converter


class SlugConverter:
    """اسلاگ تمیز در آدرس (مثل vancal یا pet)؛ حروف، عدد، خط تیره و زیرخط، فارسی هم مجاز است."""

    regex = r"[-\w]+"

    def to_python(self, value):
        return value

    def to_url(self, value):
        return value


register_converter(SlugConverter, "uslug")
