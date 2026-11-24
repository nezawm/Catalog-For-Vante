import os
import subprocess
import sys
import tempfile
from pathlib import Path

from django.conf import settings
from django.core.management import call_command
from django.test import SimpleTestCase, override_settings

from VanteCTL.settings import BASE_DIR, LEAKED_SECRET_KEYS, load_env_file

GOOD_KEY = "abcde" * 12  # ۶۰ نویسه با ۵ نویسهٔ متفاوت؛ از معیار قدرت کلید رد می‌شود


def run_settings(env, code="from django.conf import settings as s; print(s.DEBUG, list(s.ALLOWED_HOSTS), s.SECRET_KEY == %r)" % GOOD_KEY):
    """settings را در یک پروسهٔ جدا با محیط کنترل‌شده بارگذاری می‌کند (بدون ارث‌بردن متغیرهای فعلی)."""
    clean = {k: v for k, v in os.environ.items() if not k.startswith("DJANGO_") and k not in ("CONTACT_PHONE", "LOG_TRUST_PROXY_HEADER")}
    # فایل env را به مسیری که وجود ندارد می‌بریم تا .env شخصی توسعه‌دهنده روی نتیجه اثر نگذارد.
    clean.update(env, DJANGO_SETTINGS_MODULE="VanteCTL.settings", DJANGO_ENV_FILE=str(BASE_DIR / "no-such.env"))
    return subprocess.run(
        [sys.executable, "-c", code], cwd=BASE_DIR, env=clean, capture_output=True, text=True
    )


class SettingsFromEnvTests(SimpleTestCase):
    def test_production_without_secret_key_refuses_to_start(self):
        result = run_settings({"DJANGO_ALLOWED_HOSTS": "a.com"})
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("DJANGO_SECRET_KEY", result.stderr)

    def test_leaked_key_is_rejected_in_production(self):
        for key in LEAKED_SECRET_KEYS:
            result = run_settings({"DJANGO_SECRET_KEY": key, "DJANGO_ALLOWED_HOSTS": "a.com"})
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("SECRET_KEY", result.stderr)

    def test_missing_allowed_hosts_refuses_to_start_when_not_debug(self):
        result = run_settings({"DJANGO_SECRET_KEY": GOOD_KEY})
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("DJANGO_ALLOWED_HOSTS", result.stderr)

    def test_values_come_from_environment_and_debug_defaults_to_false(self):
        result = run_settings({"DJANGO_SECRET_KEY": GOOD_KEY, "DJANGO_ALLOWED_HOSTS": "a.com, www.a.com ,"})
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout.strip(), f"False ['a.com', 'www.a.com'] True")

    def test_debug_can_be_enabled_and_gets_local_hosts(self):
        result = run_settings({"DJANGO_DEBUG": "true", "DJANGO_SECRET_KEY": GOOD_KEY})
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertTrue(result.stdout.startswith("True ['localhost'"))

    def test_debug_false_values(self):
        for value in ("False", "0", "no", ""):
            result = run_settings({"DJANGO_DEBUG": value, "DJANGO_SECRET_KEY": GOOD_KEY, "DJANGO_ALLOWED_HOSTS": "a.com"})
            self.assertTrue(result.stdout.startswith("False"), (value, result.stderr))

    def test_weak_keys_are_rejected_in_production(self):
        weak = {
            "short": "a1b2c3d4e5" * 4,                      # ۴۰ نویسه
            "placeholder": "یک-رشته-دلخواه-طولانی",          # عبارت نمونه‌ی .env.example
            "low variety": "k" * 60,
            "django default prefix": "django-insecure-" + "abcde" * 12,
        }
        for label, key in weak.items():
            result = run_settings({"DJANGO_SECRET_KEY": key, "DJANGO_ALLOWED_HOSTS": "a.com"})
            self.assertNotEqual(result.returncode, 0, label)
            self.assertIn("DJANGO_SECRET_KEY", result.stderr, label)

    def test_weak_key_is_fine_in_debug(self):
        result = run_settings({"DJANGO_DEBUG": "true", "DJANGO_SECRET_KEY": "short"})
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_production_enables_secure_cookies_and_ssl_redirect(self):
        code = ("from django.conf import settings as s; "
                "print(s.SESSION_COOKIE_SECURE, s.CSRF_COOKIE_SECURE, s.SECURE_SSL_REDIRECT, s.SECURE_HSTS_SECONDS, s.SECURE_PROXY_SSL_HEADER)")
        result = run_settings({"DJANGO_SECRET_KEY": GOOD_KEY, "DJANGO_ALLOWED_HOSTS": "a.com"}, code)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout.strip(), "True True True 0 None")

    def test_proxy_header_and_hsts_only_when_asked(self):
        code = "from django.conf import settings as s; print(s.SECURE_HSTS_SECONDS, s.SECURE_PROXY_SSL_HEADER, s.CSRF_TRUSTED_ORIGINS)"
        result = run_settings({"DJANGO_SECRET_KEY": GOOD_KEY, "DJANGO_ALLOWED_HOSTS": "a.com", "DJANGO_HSTS_SECONDS": "3600",
                               "DJANGO_BEHIND_PROXY": "1", "DJANGO_CSRF_TRUSTED_ORIGINS": "https://a.com"}, code)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout.strip(), "3600 ('HTTP_X_FORWARDED_PROTO', 'https') ['https://a.com']")

    def test_debug_does_not_force_https(self):
        code = "from django.conf import settings as s; print(s.SESSION_COOKIE_SECURE, s.SECURE_SSL_REDIRECT)"
        result = run_settings({"DJANGO_DEBUG": "true", "DJANGO_SECRET_KEY": GOOD_KEY}, code)
        self.assertEqual(result.stdout.strip(), "False False")

    def test_settings_source_has_no_hardcoded_leaked_key_outside_blocklist(self):
        source = (BASE_DIR / "VanteCTL" / "settings.py").read_text(encoding="utf-8")
        for key in LEAKED_SECRET_KEYS:
            self.assertEqual(source.count(key), 1)  # فقط داخل لیست مسدودها

    def test_env_file_is_read_but_real_environment_wins(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / ".env"
            path.write_text('# comment\nA_ONE=1\nA_TWO="two words"\nA_KEEP=file\n\nbad line\n', encoding="utf-8")
            os.environ["A_KEEP"] = "env"
            try:
                load_env_file(path)
                self.assertEqual(os.environ["A_ONE"], "1")
                self.assertEqual(os.environ["A_TWO"], "two words")
                self.assertEqual(os.environ["A_KEEP"], "env")
            finally:
                for k in ("A_ONE", "A_TWO", "A_KEEP"):
                    os.environ.pop(k, None)
            load_env_file(Path(tmp) / "missing.env")  # فایل نبودن خطا نمی‌دهد


class StaticRootTests(SimpleTestCase):
    def test_static_root_is_defined_and_collectstatic_works(self):
        self.assertTrue(settings.STATIC_ROOT)
        with tempfile.TemporaryDirectory() as tmp, override_settings(STATIC_ROOT=tmp):
            call_command("collectstatic", interactive=False, verbosity=0)
            self.assertTrue(any(Path(tmp).rglob("panel.css")))
