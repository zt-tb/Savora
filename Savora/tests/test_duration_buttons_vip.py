import asyncio
import unittest
from unittest import mock

from tests import _stubs  # noqa: F401
from tests._fakes import FakeBot, FakeContext, FakeMessage, FakeQuery, FakeUpdate

from app import buttons, duration, emoji_ids as E, ui
from app.handlers import admin_panel, common, payments


def run(coro):
    return asyncio.run(coro)


class TestParseHours(unittest.TestCase):
    def test_arabic_and_english_inputs(self):
        cases = {
            "يوم": 24, "1 يوم": 24, "3 ايام": 72, "٣ أيام": 72, "يومين": 48, "اسبوع": 168, "أسبوعين": 336,
            "شهر": 720, "الشهر": 720, "شهرين": 1440, "2 شهر": 1440, "3 اشهر": 2160, "12 ساعة": 12, "ساعتين": 2,
            "ساعه": 1, "سنة": 8760, "10": 240, "٣٠": 720, "1.5 يوم": 36, "1,5 يوم": 36,
            "30d": 720, "6h": 6, "2 weeks": 336, "1 month": 720, "2 months": 1440, "  5 days ": 120,
        }
        for raw, hours in cases.items():
            self.assertEqual(duration.parse_hours(raw), hours, raw)

    def test_rejects_garbage_and_out_of_range(self):
        for raw in ("", "   ", "abc", "يوم يوم", "0", "0 يوم", "-3 يوم", "1000 سنة", "كثير", "3 xyz", "...", None):
            self.assertIsNone(duration.parse_hours(raw), raw)

    def test_limit_is_ten_years(self):
        self.assertEqual(duration.parse_hours("10 سنة"), 24 * 365 * 10)
        self.assertIsNone(duration.parse_hours("11 سنة"))


class TestButtonIcon(unittest.TestCase):
    def tearDown(self):
        ui.set_animated(True)

    def test_single_icon_when_animated(self):
        b = buttons.btn("⬇️ ابدأ التحميل", "download", emoji=E.ZAP)
        self.assertEqual((b.text, b.icon_custom_emoji_id), ("ابدأ التحميل", E.ZAP))
        b = buttons.btn("⭐ 50 — يوم", "x", emoji=E.MEDAL)
        self.assertEqual(b.text, "50 — يوم")
        b = buttons.url_btn("✉️ تواصل", "https://t.me/K0_MG", emoji=E.MAIL)
        self.assertEqual((b.text, b.icon_custom_emoji_id), ("تواصل", E.MAIL))

    def test_plain_emoji_kept_when_animation_off(self):
        ui.set_animated(False)
        b = buttons.btn("⬇️ ابدأ التحميل", "download", emoji=E.ZAP)
        self.assertEqual((b.text, b.icon_custom_emoji_id), ("⬇️ ابدأ التحميل", None))

    def test_buttons_without_icon_are_untouched(self):
        self.assertEqual(buttons.btn("🇮🇶 العربية", "lang_ar").text, "🇮🇶 العربية")

    def test_never_returns_empty_label(self):
        self.assertEqual(buttons.btn("⬇️", "x", emoji=E.ZAP).text, "⬇️")


class TestCompactKeyboards(unittest.TestCase):
    def rows(self, markup):
        return [[b.callback_data or b.url for b in row] for row in markup.inline_keyboard]

    def test_main_keyboard_is_compact(self):
        plain = common.main_keyboard("ar", show_admin=False)
        admin = common.main_keyboard("ar", show_admin=True)
        self.assertEqual(len(plain.inline_keyboard), 4)
        self.assertEqual(len(admin.inline_keyboard), 4)
        self.assertEqual(self.rows(admin)[-1], ["https://t.me/K0_MG", "admin_panel"])
        self.assertEqual(self.rows(plain)[2], ["change_language", "my_id", "share_earn"])

    def test_admin_panel_and_menus_are_compact(self):
        with mock.patch.object(admin_panel.settings_store, "maintenance_on", lambda: False):
            self.assertEqual(len(admin_panel._panel_kb("ar").inline_keyboard), 6)
        self.assertEqual(len(admin_panel._caption_kb("ar").inline_keyboard), 2)
        self.assertEqual(len(admin_panel._welcome_kb("ar").inline_keyboard), 2)

    def test_vip_plans_in_one_row(self):
        q = FakeQuery("vip_sub")
        with mock.patch.object(payments, "lang_of", mock.AsyncMock(return_value="ar")):
            run(payments.show_vip_sub(FakeUpdate(query=q), FakeContext()))
        rows = self.rows(q.edits[0][1]["reply_markup"])
        self.assertEqual(rows[0], ["buy_vip_d1", "buy_vip_d7", "buy_vip_d30"])
        self.assertEqual(rows[1][-1], "back_to_main")


class TestAdminVipDuration(unittest.TestCase):
    def setUp(self):
        self.grant = mock.AsyncMock(return_value=True)
        for p in (mock.patch.object(admin_panel, "is_admin", lambda u: True),
                  mock.patch.object(admin_panel, "lang_of", mock.AsyncMock(return_value="ar")),
                  mock.patch.object(admin_panel.users, "exists", mock.AsyncMock(return_value=True)),
                  mock.patch.object(admin_panel.users, "grant_vip", self.grant),
                  mock.patch.object(admin_panel.users, "get_language", mock.AsyncMock(return_value="ar"))):
            p.start()
            self.addCleanup(p.stop)
        self.ctx = FakeContext(FakeBot())
        self.ctx.user_data.clear()

    def say(self, value):
        msg = FakeMessage(text=value)
        handled = run(admin_panel.handle_text_step(FakeUpdate(message=msg), self.ctx))
        return handled, msg

    def test_full_flow_id_then_duration(self):
        common.set_state(self.ctx, admin_panel.ST_ADD_VIP)
        handled, msg = self.say("7249021797")
        self.assertTrue(handled)
        self.assertEqual(common.get_state(self.ctx), admin_panel.ST_VIP_DURATION)
        self.grant.assert_not_awaited()
        handled, msg = self.say("شهرين")
        self.assertTrue(handled)
        self.grant.assert_awaited_once_with(7249021797, hours=1440)
        self.assertIn("60", msg.replies[0][1])
        self.assertIsNone(common.get_state(self.ctx))
        self.assertEqual(self.ctx.bot.sent[0][0], 7249021797)

    def test_bad_duration_keeps_waiting(self):
        common.set_state(self.ctx, admin_panel.ST_ADD_VIP)
        self.say("55")
        handled, msg = self.say("كثير كثير")
        self.assertTrue(handled)
        self.assertEqual(common.get_state(self.ctx), admin_panel.ST_VIP_DURATION)
        self.grant.assert_not_awaited()
        self.say("3 ايام")
        self.grant.assert_awaited_once_with(55, hours=72)

    def test_unknown_user_stops_before_asking_duration(self):
        with mock.patch.object(admin_panel.users, "exists", mock.AsyncMock(return_value=False)):
            common.set_state(self.ctx, admin_panel.ST_ADD_VIP)
            self.say("55")
        self.assertIsNone(common.get_state(self.ctx))
        self.grant.assert_not_awaited()

    def test_lost_target_does_not_grant(self):
        common.set_state(self.ctx, admin_panel.ST_VIP_DURATION)
        self.say("يوم")
        self.grant.assert_not_awaited()
        self.assertIsNone(common.get_state(self.ctx))

    def test_notice_failure_does_not_break_grant(self):
        async def boom(*a, **k):
            raise RuntimeError("blocked")
        self.ctx.bot.send_message = boom
        common.set_state(self.ctx, admin_panel.ST_ADD_VIP)
        self.say("55")
        handled, msg = self.say("يوم")
        self.assertTrue(handled)
        self.grant.assert_awaited_once_with(55, hours=24)

    def test_other_admin_steps_still_work(self):
        with mock.patch.object(admin_panel.users, "revoke_vip", mock.AsyncMock(return_value=True)) as rv:
            common.set_state(self.ctx, admin_panel.ST_REMOVE_VIP)
            handled, msg = self.say("55")
        self.assertTrue(handled)
        rv.assert_awaited_once_with(55)


if __name__ == "__main__":
    unittest.main()
