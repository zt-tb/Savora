import asyncio
import types
import unittest
from datetime import datetime, timedelta, timezone
from unittest import mock

from tests import _stubs  # noqa: F401
from tests._fakes import FakeBot, FakeContext, FakeMessage, FakeQuery, FakeUpdate, FakeUser

from app import antispam, settings_store, users, welcome_media
from app.config import settings
from app.handlers import admin_panel, common, start
from telegram.error import BadRequest
from telegram.ext import ApplicationHandlerStop


def run(coro):
    return asyncio.run(coro)


class RowSession:
    row = None
    added = []

    def __call__(self):
        return self

    async def __aenter__(self):
        return self

    async def __aexit__(self, *a):
        return False

    async def scalar(self, stmt):
        return RowSession.row

    def add(self, item):
        RowSession.added.append(item)

    async def commit(self):
        pass


def make_row(**kw):
    base = dict(user_id=1, free_used=0, locked_until=None, vip_until=None, downloads_count=0)
    base.update(kw)
    return types.SimpleNamespace(**base)


class TestFreeQuota(unittest.TestCase):
    def setUp(self):
        RowSession.row, RowSession.added = make_row(), []
        p = mock.patch.object(users, "Session", RowSession())
        p.start()
        self.addCleanup(p.stop)

    def test_two_downloads_then_locked_for_two_days(self):
        self.assertTrue(run(users.can_download(1)))
        self.assertEqual(run(users.quota_left(1)), 2)
        run(users.record_download(1, "video", True))
        self.assertEqual(run(users.quota_left(1)), 1)
        self.assertTrue(run(users.can_download(1)))
        run(users.record_download(1, "video", True))
        self.assertFalse(run(users.can_download(1)))
        self.assertEqual(run(users.quota_left(1)), 0)
        wait = run(users.wait_remaining(1))
        self.assertGreater(wait, timedelta(hours=47, minutes=59))
        self.assertLessEqual(wait, timedelta(days=2))

    def test_unlocks_after_cooldown_and_starts_new_window(self):
        RowSession.row = make_row(free_used=2, locked_until=datetime.now(timezone.utc) - timedelta(seconds=1))
        self.assertTrue(run(users.can_download(1)))
        self.assertEqual(run(users.quota_left(1)), 2)
        self.assertIsNone(run(users.wait_remaining(1)))
        run(users.record_download(1, "photo", True))
        self.assertEqual((RowSession.row.free_used, RowSession.row.locked_until), (1, None))

    def test_still_locked_just_before_unlock(self):
        RowSession.row = make_row(free_used=2, locked_until=datetime.now(timezone.utc) + timedelta(hours=1))
        self.assertFalse(run(users.can_download(1)))

    def test_failed_download_costs_nothing(self):
        run(users.record_download(1, "video", False, "no_video"))
        self.assertEqual(RowSession.row.free_used, 0)
        self.assertEqual(RowSession.added[0].error, "no_video")

    def test_vip_is_unlimited_and_does_not_consume_quota(self):
        RowSession.row = make_row(vip_until=datetime.now(timezone.utc) + timedelta(days=1))
        for _ in range(5):
            self.assertTrue(run(users.can_download(1)))
            run(users.record_download(1, "video", True))
        self.assertIsNone(run(users.quota_left(1)))
        self.assertIsNone(run(users.wait_remaining(1)))
        self.assertEqual((RowSession.row.free_used, RowSession.row.downloads_count), (0, 5))

    def test_expired_vip_falls_back_to_free_quota(self):
        RowSession.row = make_row(vip_until=datetime.now(timezone.utc) - timedelta(minutes=1))
        self.assertEqual(run(users.quota_left(1)), 2)

    def test_unknown_user_cannot_download(self):
        RowSession.row = None
        self.assertFalse(run(users.can_download(1)))

    def test_constants_match_policy(self):
        self.assertEqual((users.FREE_LIMIT, users.COOLDOWN, users.FREE_BATCH_LIMIT), (2, timedelta(days=2), 2))


class TestAntispam(unittest.TestCase):
    def setUp(self):
        antispam.reset()
        self.addCleanup(antispam.reset)

    def test_burst_blocks_for_a_minute_then_releases(self):
        results = [antispam.register(5, now=100.0 + i * 0.1) for i in range(antispam.MAX_ACTIONS)]
        self.assertTrue(all(r.allowed for r in results))
        blocked = antispam.register(5, now=101.0)
        self.assertEqual((blocked.allowed, blocked.wait, blocked.announce), (False, 60, True))
        again = antispam.register(5, now=130.0)
        self.assertEqual((again.allowed, again.wait, again.announce), (False, 31, False))
        self.assertTrue(antispam.register(5, now=161.5).allowed)

    def test_normal_pace_is_never_blocked(self):
        self.assertTrue(all(antispam.register(6, now=i * 1.0).allowed for i in range(200)))

    def test_users_are_independent(self):
        for i in range(20):
            antispam.register(1, now=10.0 + i * 0.01)
        self.assertTrue(antispam.register(2, now=10.3).allowed)

    def test_prune_keeps_memory_bounded(self):
        for uid in range(antispam._PRUNE_AT + 10):
            antispam.register(uid, now=1.0)
        antispam.register(10 ** 9, now=1000.0)
        self.assertLess(len(antispam._hits), 100)


class TestGuard(unittest.TestCase):
    def setUp(self):
        antispam.reset()
        self.addCleanup(antispam.reset)
        p = mock.patch.object(antispam.users, "get_language", mock.AsyncMock(return_value="ar"))
        p.start()
        self.addCleanup(p.stop)

    def burst_callbacks(self, user, n, query_factory=FakeQuery):
        queries = []
        for _ in range(n):
            q = query_factory("x")
            queries.append(q)
            try:
                run(antispam.guard(FakeUpdate(user=user, query=q), FakeContext()))
            except ApplicationHandlerStop:
                q.stopped = True
        return queries

    def test_button_flood_is_stopped_and_answered(self):
        queries = self.burst_callbacks(FakeUser(id=77), antispam.MAX_ACTIONS + 3)
        stopped = [q for q in queries if getattr(q, "stopped", False)]
        self.assertEqual(len(stopped), 3)
        self.assertTrue(all(q.answers and "ثانية" in q.answers[0][0] for q in stopped))

    def test_message_flood_announces_once_then_silent(self):
        replies = 0
        stops = 0
        for _ in range(antispam.MAX_ACTIONS + 5):
            msg = FakeMessage(text="hi")
            try:
                run(antispam.guard(FakeUpdate(user=FakeUser(id=78), message=msg), FakeContext()))
            except ApplicationHandlerStop:
                stops += 1
            replies += len(msg.replies)
        self.assertEqual((stops, replies), (5, 1))

    def test_admin_is_exempt(self):
        admin = FakeUser(id=settings.admin_id)
        queries = self.burst_callbacks(admin, 50)
        self.assertFalse(any(getattr(q, "stopped", False) for q in queries))

    def test_payment_updates_are_never_blocked(self):
        user = FakeUser(id=79)
        for _ in range(antispam.MAX_ACTIONS + 2):
            antispam.register(user.id)
        upd = FakeUpdate(user=user)
        upd.pre_checkout_query = object()
        run(antispam.guard(upd, FakeContext()))
        msg = FakeMessage()
        msg.successful_payment = object()
        run(antispam.guard(FakeUpdate(user=user, message=msg), FakeContext()))

    def test_failed_alert_still_stops_handlers(self):
        class BrokenQuery(FakeQuery):
            async def answer(self, *a, **k):
                raise BadRequest("Query is too old")
        queries = self.burst_callbacks(FakeUser(id=80), antispam.MAX_ACTIONS + 1, BrokenQuery)
        self.assertTrue(getattr(queries[-1], "stopped", False))


class AnimMessage(FakeMessage):
    async def reply_animation(self, media, **kw):
        sent = await super().reply_animation(media, **kw)
        sent.animation = types.SimpleNamespace(file_id="CACHED_ID")
        return sent


class TestWelcomeMedia(unittest.TestCase):
    def setUp(self):
        welcome_media._default_file_id = None
        settings_store._cache.clear()
        self.addCleanup(settings_store._cache.clear)

    def test_default_asset_exists_and_is_small(self):
        import os
        self.assertTrue(os.path.exists(welcome_media.DEFAULT_PATH))
        self.assertLess(os.path.getsize(welcome_media.DEFAULT_PATH), 1_000_000)

    def test_default_animation_sent_with_caption_and_buttons_then_cached(self):
        msg, markup = AnimMessage(), object()
        run(welcome_media.send_welcome(msg, "<b>hi</b>", markup))
        kind, size, kw = msg.replies[0]
        self.assertEqual((kind, kw["caption"], kw["reply_markup"]), ("animation", "<b>hi</b>", markup))
        self.assertGreater(size, 1000)
        self.assertEqual(welcome_media._default_file_id, "CACHED_ID")
        msg2 = AnimMessage()
        run(welcome_media.send_welcome(msg2, "<b>hi</b>", markup))
        self.assertEqual(msg2.replies[0][1], 0)

    def test_owner_custom_media_wins(self):
        settings_store._cache[settings_store.WELCOME_MEDIA] = "video:VID123"
        msg = AnimMessage()
        run(welcome_media.send_welcome(msg, "x", None))
        self.assertEqual(msg.replies[0][0], "video")

    def test_broken_custom_falls_back_to_default(self):
        settings_store._cache[settings_store.WELCOME_MEDIA] = "photo:BAD"

        class Msg(AnimMessage):
            async def reply_photo(self, *a, **k):
                raise BadRequest("wrong file identifier")
        msg = Msg()
        run(welcome_media.send_welcome(msg, "x", None))
        self.assertEqual(msg.replies[0][0], "animation")

    def test_everything_failing_still_sends_text(self):
        class Msg(FakeMessage):
            async def reply_animation(self, *a, **k):
                raise BadRequest("boom")
        msg = Msg()
        markup = object()
        run(welcome_media.send_welcome(msg, "hello", markup))
        self.assertEqual(msg.replies[0][:2], ("text", "hello"))

    def test_long_welcome_goes_as_separate_text(self):
        msg = AnimMessage()
        body = "<b>" + "ا" * 1100 + "</b>"
        run(welcome_media.send_welcome(msg, body, "M"))
        self.assertEqual([r[0] for r in msg.replies], ["animation", "text"])
        self.assertIsNone(msg.replies[0][2]["caption"])
        self.assertEqual(msg.replies[1][2]["reply_markup"], "M")

    def test_real_welcome_fits_caption_in_both_languages(self):
        from app.texts import text
        for lang in ("ar", "en"):
            for nudge in ("", text(lang, "nudge_locked", per_day=23)):
                body = text(lang, "welcome", name="X" * 64, plan=text(lang, "plan_free"),
                            quota=text(lang, "quota_locked", wait="1 يوم 23 س"), nudge=nudge)
                self.assertLessEqual(welcome_media._visible_len(body), welcome_media.CAPTION_LIMIT, lang)

    def test_parse_and_extract(self):
        self.assertEqual(welcome_media.parse("animation:AB"), ("animation", "AB"))
        for bad in ("", "gif:AB", "photo:", "nonsense"):
            self.assertIsNone(welcome_media.parse(bad))
        gif = types.SimpleNamespace(animation=types.SimpleNamespace(file_id="G"), video=None, photo=None)
        vid = types.SimpleNamespace(animation=None, video=types.SimpleNamespace(file_id="V"), photo=None)
        pic = types.SimpleNamespace(animation=None, video=None, photo=[types.SimpleNamespace(file_id="small"),
                                                                       types.SimpleNamespace(file_id="big")])
        self.assertEqual([welcome_media.extract(m) for m in (gif, vid, pic)],
                         [("animation", "G"), ("video", "V"), ("photo", "big")])
        self.assertIsNone(welcome_media.extract(types.SimpleNamespace(animation=None, video=None, photo=None)))


class TestEditMenu(unittest.TestCase):
    def mk(self, error):
        class Q(FakeQuery):
            async def edit_message_text(self, text, **kw):
                if error:
                    raise error
                await super().edit_message_text(text, **kw)
        msg = FakeMessage(bot=FakeBot(), chat_id=42)
        return Q("x", message=msg), msg

    def test_normal_edit(self):
        q, msg = self.mk(None)
        run(common.edit_menu(FakeUpdate(query=q), "body", "MK"))
        self.assertEqual(q.edits[0][0], "body")

    def test_media_message_is_replaced_not_edited(self):
        q, msg = self.mk(BadRequest("Bad Request: there is no text in the message to edit"))
        run(common.edit_menu(FakeUpdate(query=q), "body", "MK"))
        self.assertEqual(msg.bot.sent[0][:2], (42, "body"))
        self.assertEqual(msg.bot.sent[0][2]["reply_markup"], "MK")
        self.assertTrue(msg.deleted)

    def test_not_modified_is_ignored(self):
        q, msg = self.mk(BadRequest("Bad Request: message is not modified"))
        run(common.edit_menu(FakeUpdate(query=q), "body"))
        self.assertEqual(msg.bot.sent, [])

    def test_other_errors_propagate(self):
        q, _ = self.mk(BadRequest("Bad Request: can't parse entities"))
        with self.assertRaises(BadRequest):
            run(common.edit_menu(FakeUpdate(query=q), "body"))


class TestAdminWelcome(unittest.TestCase):
    def setUp(self):
        self.saved = {}

        async def set_value(key, value):
            self.saved[key] = value

        async def delete(key):
            self.saved.pop(key, None)
        for p in (mock.patch.object(admin_panel, "is_admin", lambda u: True),
                  mock.patch.object(admin_panel, "lang_of", mock.AsyncMock(return_value="ar")),
                  mock.patch.object(admin_panel.settings_store, "set_value", set_value),
                  mock.patch.object(admin_panel.settings_store, "delete", delete)):
            p.start()
            self.addCleanup(p.stop)
        settings_store._cache.clear()
        self.addCleanup(settings_store._cache.clear)

    def test_full_flow_saves_gif_file_id(self):
        ctx = FakeContext()
        q = FakeQuery("admin_welcome_set")
        run(admin_panel.ask_welcome_media(FakeUpdate(query=q), ctx))
        self.assertEqual(common.get_state(ctx), admin_panel.ST_WELCOME)
        msg = FakeMessage()
        msg.animation, msg.video, msg.photo = types.SimpleNamespace(file_id="GIF1"), None, None
        self.assertTrue(run(admin_panel.handle_media_step(FakeUpdate(message=msg), ctx)))
        self.assertEqual(self.saved, {settings_store.WELCOME_MEDIA: "animation:GIF1"})
        self.assertIsNone(common.get_state(ctx))

    def test_wrong_content_keeps_waiting(self):
        ctx = FakeContext()
        common.set_state(ctx, admin_panel.ST_WELCOME)
        msg = FakeMessage()
        msg.animation = msg.video = msg.photo = None
        self.assertTrue(run(admin_panel.handle_media_step(FakeUpdate(message=msg), ctx)))
        self.assertEqual(common.get_state(ctx), admin_panel.ST_WELCOME)
        self.assertEqual(self.saved, {})

    def test_ignored_without_state_or_for_non_admin(self):
        self.assertFalse(run(admin_panel.handle_media_step(FakeUpdate(message=FakeMessage()), FakeContext())))
        with mock.patch.object(admin_panel, "is_admin", lambda u: False):
            ctx = FakeContext()
            common.set_state(ctx, admin_panel.ST_WELCOME)
            self.assertFalse(run(admin_panel.handle_media_step(FakeUpdate(message=FakeMessage()), ctx)))

    def test_reset_removes_custom(self):
        self.saved[settings_store.WELCOME_MEDIA] = "video:X"
        q = FakeQuery("admin_welcome_reset")
        run(admin_panel.reset_welcome_media(FakeUpdate(query=q), FakeContext()))
        self.assertEqual(self.saved, {})


class TestStartWelcome(unittest.TestCase):
    def test_free_and_vip_welcome(self):
        for left, vip in ((2, False), (0, False), (None, True)):
            with mock.patch.object(start.users, "is_vip", mock.AsyncMock(return_value=vip)), \
                    mock.patch.object(common.users, "quota_left", mock.AsyncMock(return_value=left)), \
                    mock.patch.object(common.users, "wait_remaining", mock.AsyncMock(return_value=timedelta(hours=30))), \
                    mock.patch.object(start, "is_admin", lambda u: False):
                body, markup = run(start._welcome(FakeUpdate(user=FakeUser(first_name="<i>x")), "ar"))
            self.assertIn("&lt;i&gt;x", body)
            self.assertEqual("VIP" in body.split("حسابك")[1][:30], vip)
            vip_btn = markup.inline_keyboard[1][1]
            self.assertEqual(vip_btn.callback_data, "vip_sub")
            self.assertEqual(vip_btn.style, "primary" if vip else "success")
            if left == 0:
                self.assertIn("🔒", body)
            if vip:
                self.assertIn("∞", body)
                self.assertNotIn("لا تنتظر", body)


if __name__ == "__main__":
    unittest.main()
