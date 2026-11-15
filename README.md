# VanteCTL

پروژه کاتالوگ محصولات (Django) با پنل مدیریت فارسی و سایت دوزبانه (فارسی/انگلیسی).

## راه‌اندازی

```bash
python -m venv .venv
source .venv/bin/activate        # ویندوز: .venv\Scripts\activate
pip install -r requirements.txt

cp .env.example .env             # سپس مقادیر را ویرایش کنید
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

## ساخت کاربر پنل کارفرما

```bash
python manage.py create_panel_client <username>
```

## اجرای تست‌ها

```bash
python manage.py test
```

## نکات استقرار

- `DJANGO_DEBUG=False` و یک `DJANGO_SECRET_KEY` تصادفی در `.env` تنظیم شود.
- `DJANGO_ALLOWED_HOSTS` و `DJANGO_CSRF_TRUSTED_ORIGINS` را با دامنه خود پر کنید.
- `python manage.py collectstatic` فایل‌های استاتیک را در `staticfiles/` جمع می‌کند.
- فایل `.env` و `db.sqlite3` عمداً در گیت قرار نمی‌گیرند.
