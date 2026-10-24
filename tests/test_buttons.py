import unittest

from tests import _stubs  # noqa: F401

from app import buttons, emoji_ids as E


class TestButtons(unittest.TestCase):
    def test_btn_default_style_is_primary(self):
        b = buttons.btn("نص", "cb_data")
        self.assertEqual(b.style, buttons.PRIMARY)
        self.assertIsNone(b.icon_custom_emoji_id)
        self.assertEqual(b.callback_data, "cb_data")

    def test_btn_success_with_emoji(self):
        b = buttons.btn("تحميل", "download", style=buttons.SUCCESS, emoji=E.ZAP)
        self.assertEqual(b.style, "success")
        self.assertEqual(b.icon_custom_emoji_id, E.ZAP)

    def test_btn_danger(self):
        b = buttons.btn("حظر", "ban", style=buttons.DANGER, emoji=E.SKULL)
        self.assertEqual(b.style, "danger")

    def test_url_btn_sets_url_not_callback(self):
        b = buttons.url_btn("تواصل", "https://t.me/K0_MG", style=buttons.PRIMARY, emoji=E.MAIL)
        self.assertEqual(b.url, "https://t.me/K0_MG")
        self.assertIsNone(b.callback_data)
        self.assertEqual(b.style, "primary")

    def test_web_app_btn_sets_web_app(self):
        sentinel = object()
        b = buttons.web_app_btn("فتح", sentinel, style=buttons.PRIMARY)
        self.assertIs(b.web_app, sentinel)

    def test_three_styles_are_distinct_strings(self):
        self.assertEqual({buttons.PRIMARY, buttons.SUCCESS, buttons.DANGER}, {"primary", "success", "danger"})


class TestMainKeyboardAllButtonsStyled(unittest.TestCase):

    def _assert_every_button_has_style(self, markup):
        for row in markup.inline_keyboard:
            for button in row:
                self.assertIn(button.style, ("primary", "success", "danger"),
                               f"زر بلا style صحيح: {button.text!r}")

    def test_main_keyboard_ar_with_admin(self):
        from app.handlers.common import main_keyboard

        self._assert_every_button_has_style(main_keyboard("ar", show_admin=True))

    def test_main_keyboard_en_without_admin(self):
        from app.handlers.common import main_keyboard

        self._assert_every_button_has_style(main_keyboard("en", show_admin=False))

    def test_language_keyboard(self):
        from app.handlers.common import language_keyboard

        self._assert_every_button_has_style(language_keyboard())

    def test_back_keyboard(self):
        from app.handlers.common import back_keyboard

        self._assert_every_button_has_style(back_keyboard("ar"))

    def test_admin_panel_keyboard(self):
        from app.handlers.admin_panel import _panel_kb

        self._assert_every_button_has_style(_panel_kb("ar"))
        self._assert_every_button_has_style(_panel_kb("en"))

    def test_session_login_menus(self):
        from app.handlers.session_login import _candidate_kb, _menu_kb

        self._assert_every_button_has_style(_menu_kb("ar"))
        self._assert_every_button_has_style(_candidate_kb("ar"))


if __name__ == "__main__":
    unittest.main()
