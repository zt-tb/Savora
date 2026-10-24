import unittest
from datetime import timedelta

from tests import _stubs  # noqa: F401

from app import ui


class TestUiHelpers(unittest.TestCase):
    def test_bar_bounds(self):
        self.assertEqual(ui.bar(0), "▱" * 10)
        self.assertEqual(ui.bar(100), "▰" * 10)
        self.assertEqual(ui.bar(45), "▰▰▰▰▱▱▱▱▱▱")
        self.assertEqual(ui.bar(-5), "▱" * 10)
        self.assertEqual(ui.bar(250), "▰" * 10)

    def test_human_size(self):
        self.assertEqual(ui.human_size(None), "—")
        self.assertEqual(ui.human_size(512), "512 B")
        self.assertEqual(ui.human_size(1536), "1.5 KB")
        self.assertEqual(ui.human_size(5 * 1024 * 1024), "5.0 MB")
        self.assertEqual(ui.human_size(3 * 1024 ** 3), "3.0 GB")

    def test_human_seconds(self):
        self.assertEqual(ui.human_seconds(4.26, "en"), "4.3 s")
        self.assertEqual(ui.human_seconds(125, "en"), "2 m 5 s")
        self.assertIn("ث", ui.human_seconds(3, "ar"))

    def test_human_delta(self):
        self.assertEqual(ui.human_delta(timedelta(days=2, hours=3), "en"), "2 d 3 h")
        self.assertEqual(ui.human_delta(timedelta(minutes=45), "en"), "45 m")
        self.assertEqual(ui.human_delta(timedelta(seconds=5), "en"), "1 m")

    def test_esc_neutralizes_html(self):
        self.assertEqual(ui.esc("<b>&x</b>"), "&lt;b&gt;&amp;x&lt;/b&gt;")
        self.assertEqual(ui.esc(123), "123")


if __name__ == "__main__":
    unittest.main()
