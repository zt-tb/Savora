import re
import unittest

from tests import _stubs  # noqa: F401

from app.texts import TEXTS, text


class TestTextKwargsRegression(unittest.TestCase):

    def test_login_candidate_with_keyword_args(self):
        body = text("ar", "login_candidate", name="محمد", username="@m", id=123)
        self.assertIn("محمد", body)
        self.assertIn("@m", body)
        self.assertIn("123", body)

    def test_login_activated_with_keyword_arg(self):
        body = text("ar", "login_activated", name="Account One")
        self.assertIn("Account One", body)

    def test_login_activate_failed_with_keyword_arg(self):
        body = text("en", "login_activate_failed", reason="network error")
        self.assertIn("network error", body)

    def test_positional_args_still_work(self):
        body = text("ar", "broadcast_done", 10, 2)
        self.assertIn("10", body)
        self.assertIn("2", body)

    def test_no_args_returns_raw_text(self):
        self.assertIn("رابط غير مدعوم", text("ar", "invalid_link"))

    def test_unknown_key_falls_back_to_key_name(self):
        self.assertEqual(text("ar", "no_such_key_xyz"), "no_such_key_xyz")

    def test_unknown_language_falls_back_to_arabic(self):
        self.assertEqual(text("fr", "invalid_link"), text("ar", "invalid_link"))


_FORMAT_FIELD_RE = re.compile(r"\{([a-zA-Z_][a-zA-Z0-9_]*)?\}")


class TestTextParity(unittest.TestCase):

    def test_same_key_set(self):
        self.assertEqual(set(TEXTS["ar"].keys()), set(TEXTS["en"].keys()))

    def test_same_format_fields_per_key(self):
        for key in TEXTS["ar"]:
            ar_fields = _FORMAT_FIELD_RE.findall(TEXTS["ar"][key])
            en_fields = _FORMAT_FIELD_RE.findall(TEXTS["en"][key])
            with self.subTest(key=key):
                self.assertEqual(ar_fields, en_fields, f"حقول تنسيق مختلفة بالمفتاح {key!r}")


if __name__ == "__main__":
    unittest.main()
