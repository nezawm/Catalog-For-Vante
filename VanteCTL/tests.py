import os
import subprocess
import sys
import tempfile
from pathlib import Path

from django.conf import settings
from django.core.management import call_command
from django.test import SimpleTestCase, override_settings

import hashlib
from unittest import mock

from VanteCTL import settings as project_settings
from VanteCTL.settings import BASE_DIR, is_leaked_secret_key, load_env_file

GOOD_KEY = "k" * 60


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

    def test_leaked_key_check_uses_hash_and_matches_only_listed_keys(self):
        fake = "a-pretend-leaked-key"
        hashes = {hashlib.sha256(fake.encode()).hexdigest()}
        with mock.patch.object(project_settings, "LEAKED_SECRET_KEY_HASHES", hashes):
            self.assertTrue(is_leaked_secret_key(fake))
            self.assertFalse(is_leaked_secret_key(GOOD_KEY))
        self.assertTrue(project_settings.LEAKED_SECRET_KEY_HASHES)  # لیست خالی نشده باشد

    def test_missing_allowed_hosts_refuses_to_start_when_not_debug(self):
        result = run_settings({"DJANGO_SECRET_KEY": GOOD_KEY})
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("DJANGO_ALLOWED_HOSTS", result.stderr)

    def test_values_come_from_environment_and_debug_defaults_to_false(self):
        result = run_settings({"DJANGO_SECRET_KEY": GOOD_KEY, "DJANGO_ALLOWED_HOSTS": "a.com, www.a.com ,"})
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout.strip(), "False ['a.com', 'www.a.com'] True")

    def test_debug_can_be_enabled_and_gets_local_hosts(self):
        result = run_settings({"DJANGO_DEBUG": "true", "DJANGO_SECRET_KEY": GOOD_KEY})
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertTrue(result.stdout.startswith("True ['localhost'"))

    def test_debug_false_values(self):
        for value in ("False", "0", "no", ""):
            result = run_settings({"DJANGO_DEBUG": value, "DJANGO_SECRET_KEY": GOOD_KEY, "DJANGO_ALLOWED_HOSTS": "a.com"})
            self.assertTrue(result.stdout.startswith("False"), (value, result.stderr))

    def test_no_secret_key_literal_in_settings_source(self):
        source = (BASE_DIR / "VanteCTL" / "settings.py").read_text(encoding="utf-8")
        self.assertNotIn("django-insecure-4@y", source)  # خود کلید لو رفته دیگر در ریپو نیست
        self.assertNotRegex(source, r"SECRET_KEY\s*=\s*['\"]django-insecure-[^d]")

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
