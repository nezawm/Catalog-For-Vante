# VanteCTL

سایت کاتالوگ محصولات ونته (جنگو ۶) به‌همراه پنل مدیریت فارسی در `/panel/`.

## نصب برای توسعه

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env          # سپس مقدارها را پر کنید
python manage.py migrate
python manage.py create_panel_client <نام‌کاربری>   # کاربر پنل (کارفرما)
python manage.py createsuperuser                      # مدیر ارشد
python manage.py runserver
```

برای توسعهٔ محلی در `.env` مقدار `DJANGO_DEBUG=True` بگذارید. اگر `DJANGO_SECRET_KEY` خالی باشد، در حالت DEBUG و در تست‌ها یک کلید فقط‌توسعه استفاده می‌شود.

## تنظیمات (متغیرهای محیطی)

همهٔ تنظیمات حساس از محیط یا فایل `.env` کنار `manage.py` خوانده می‌شوند (متغیر واقعیِ محیط بر فایل `.env` مقدم است). نمونه در `.env.example` است و `.env` در `.gitignore` قرار دارد.

| متغیر | توضیح |
|---|---|
| `DJANGO_SECRET_KEY` | اجباری (وقتی DEBUG خاموش است). حداقل ۵۰ نویسهٔ تصادفی با دست‌کم ۵ نویسهٔ متفاوت؛ کلید کوتاه، نمونه، `django-insecure-…` یا کلیدِ لو رفته باعث می‌شود برنامه بالا نیاید. |
| `DJANGO_DEBUG` | پیش‌فرض `False`. روی سرور حتماً خاموش بماند. |
| `DJANGO_ALLOWED_HOSTS` | دامنه‌ها با کاما جدا می‌شوند؛ وقتی DEBUG خاموش است اجباری است. |
| `DJANGO_CSRF_TRUSTED_ORIGINS` | اختیاری؛ مبدأهای `https://...` مورد اعتماد برای CSRF (با کاما). |
| `DJANGO_BEHIND_PROXY` | `1` پشت nginx/پروکسی‌ای که `X-Forwarded-Proto` را خودش می‌گذارد. |
| `DJANGO_SSL_REDIRECT` | پیش‌فرض `True` در production؛ ریدایرکت HTTP به HTTPS. |
| `DJANGO_HSTS_SECONDS` | پیش‌فرض `0` (خاموش)؛ بعد از تست HTTPS مثلاً `31536000`. |
| `LOG_TRUST_PROXY_HEADER` | اختیاری؛ پشت پروکسی‌ای که `X-Forwarded-For` را خودش می‌گذارد `True` کنید. |
| `CONTACT_PHONE` | اختیاری؛ شمارهٔ فوتر سایت. |

ساخت کلید جدید:

```bash
python -c "from django.core.management.utils import get_random_secret_key as g; print(g())"
```

### کلید لو رفته

کلیدی که قبلاً داخل `settings.py` (و در گیت‌هاب) بوده لو رفته حساب می‌شود. اگر روی سرور استفاده شده، یک کلید جدید بسازید و فقط روی سرور تنظیم کنید؛ برنامه با آن کلید قدیمی در حالت production اجرا نمی‌شود. با تعویض کلید، نشست‌های ورود فعلی و لینک‌های ریست گذرواژه نامعتبر می‌شوند. پاک‌کردن کلید از فایل کافی نیست چون در تاریخچهٔ گیت می‌ماند.

## امنیت

- `SECRET_KEY`، `DEBUG` و `ALLOWED_HOSTS` فقط از محیط/`.env` خوانده می‌شوند؛ در کد مقدار ثابتی نیست (کلید لو رفته‌ی قدیمی فقط در لیست مسدودها هست تا اگر کسی دوباره استفاده‌اش کرد برنامه بالا نیاید).
- با `DJANGO_DEBUG=False` کوکی‌های نشست/CSRF فقط روی HTTPS می‌روند و HTTP به HTTPS ریدایرکت می‌شود. این تنظیمات در اجرای تست اعمال نمی‌شوند.
- پیش از انتشار این را اجرا کنید و هشدارها را بخوانید: `DJANGO_DEBUG=False python manage.py check --deploy`
- `.env` و `db.sqlite3` (شامل هش گذرواژه‌ها) و `media/` در `.gitignore` هستند و نباید در مخزن باشند. لاگ ورود پنل هرگز گذرواژه‌ی واردشده را ذخیره نمی‌کند.

## استقرار روی سرور

1. متغیرهای بالا را روی سرور تنظیم کنید (`DJANGO_DEBUG=False`).
2. `python manage.py migrate`
3. `python manage.py collectstatic --noinput` (خروجی در پوشهٔ `staticfiles/`).
4. برنامه را با یک سرور WSGI (مثلاً gunicorn؛ در `requirements.txt` نیست و جدا نصب می‌شود) اجرا کنید.
5. وب‌سرور (nginx) باید `/static/` را از `staticfiles/` و `/media/` را از `media/` سرو کند؛ جنگو با DEBUG خاموش این‌ها را سرو نمی‌کند.

پایگاه‌داده فعلاً SQLite (`db.sqlite3` کنار پروژه) است؛ از آن بکاپ بگیرید و در گیت نگذارید.

## ساختار پنل

`Panel/views/` (پکیج؛ فایل قدیمی `Panel/views.py` حذف شده) به بخش‌ها تقسیم شده: `base` (مجوزها و حذف)، `auth` (ورود و حساب من)، `products` (محصول/دسته/زیردسته)، `catalog` (PDF)، `stats` (داشبورد، QR، بازدید، لاگ ورود)، `users` (اعضا). همهٔ نام‌ها از `Panel.views` هم در دسترس‌اند.

## نکته‌های رفتاری

- **ونلایت:** فقط از ردیف‌های `Vanlite` ذخیره و نمایش داده می‌شود؛ در فرم محصول در پنل ویرایش می‌شوند و سایت دقیقاً همان را نشان می‌دهد. ستون‌های `colors`، `roll_size` و `durability_years` روی `Product` منسوخ‌اند (فقط برای حفظ داده‌ی قدیمی مانده‌اند).
- **انتقال زیردسته:** با عوض‌شدن دستهٔ یک زیردسته، محصولاتش هم به دستهٔ جدید می‌روند.
- **دستهٔ غیرفعال:** صفحهٔ محصولات آن دسته هم (حتی با لینک مستقیم) باز نمی‌شود.
- **تولید PDF خودکار (`Core/catalog_pdf.py`):** فعلاً در برنامه استفاده نمی‌شود (قالب `Core/catalog_pdf.html` و `weasyprint` در پروژه نیست)؛ مشخصات ونلایت را هم از ردیف‌های `Vanlite` می‌خواند، نه ستون‌های منسوخ.
- **فایل PDF:** پاک‌شدن فایل قبلی کاتالوگ فقط بعد از قطعی‌شدن تراکنش (`transaction.on_commit`) انجام می‌شود.

## تست

```bash
python manage.py test
```
