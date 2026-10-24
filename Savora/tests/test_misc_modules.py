import asyncio
import os
import shutil
import subprocess
import tempfile
import unittest
from unittest import mock

from tests import _stubs  # noqa: F401
from tests._fakes import FakeContext, FakeMessage, FakeQuery, FakeUpdate

from app import mediaprep, sender, settings_store
from app.handlers import admin_panel


def run(coro):
    return asyncio.run(coro)


class RowStore:
    rows = {}

    def __call__(self):
        return self

    async def __aenter__(self):
        return self

    async def __aexit__(self, *a):
        return False

    async def get(self, model, key):
        return RowStore.rows.get(key)

    def add(self, row):
        RowStore.rows[row.key] = row

    async def delete(self, row):
        RowStore.rows.pop(row.key, None)

    async def commit(self):
        pass


class TestSettingsStore(unittest.TestCase):
    def setUp(self):
        RowStore.rows = {}
        settings_store._cache.clear()
        p = mock.patch.object(settings_store, "Session", RowStore())
        p.start()
        self.addCleanup(p.stop)
        self.addCleanup(settings_store._cache.clear)

    def test_set_get_delete_and_flags(self):
        self.assertFalse(settings_store.maintenance_on())
        run(settings_store.set_value(settings_store.MAINTENANCE, "1"))
        self.assertTrue(settings_store.maintenance_on())
        run(settings_store.set_value(settings_store.BLOCKED_WORDS, "spam, Ads ,"))
        self.assertEqual(settings_store.blocked_words(), ["spam", "Ads"])
        run(settings_store.delete(settings_store.BLOCKED_WORDS))
        self.assertEqual(settings_store.blocked_words(), [])
        run(settings_store.set_value(settings_store.BLOCKED_WORDS, "-"))
        self.assertEqual(settings_store.blocked_words(), [])


@unittest.skipUnless(shutil.which("ffmpeg"), "ffmpeg غير متوفر")
class TestMediaprep(unittest.TestCase):
    def test_small_file_untouched(self):
        with tempfile.TemporaryDirectory() as d:
            p = os.path.join(d, "a.bin")
            open(p, "wb").write(b"x" * 10)
            out = run(mediaprep.prepare_for_send(p, "document"))
            self.assertEqual([(o.path, o.part) for o in out], [(p, None)])

    def test_byte_split_rejoins(self):
        with tempfile.TemporaryDirectory() as d:
            p = os.path.join(d, "a.bin")
            data = os.urandom(1000)
            open(p, "wb").write(data)
            out = run(mediaprep.prepare_for_send(p, "document", limit=300, part_target=300, compress_max=0))
            self.assertEqual(len(out), 4)
            self.assertEqual([o.part for o in out], [(i, 4) for i in range(1, 5)])
            self.assertEqual(b"".join(open(o.path, "rb").read() for o in out), data)
            self.assertFalse(os.path.exists(p))

    def test_real_video_is_compressed_or_split_under_limit(self):
        with tempfile.TemporaryDirectory() as d:
            p = os.path.join(d, "v.mp4")
            r = subprocess.run(["ffmpeg", "-y", "-f", "lavfi", "-i", "testsrc=duration=6:size=640x360:rate=25",
                                "-f", "lavfi", "-i", "sine=duration=6", "-c:v", "libx264", "-b:v", "2M", p],
                               capture_output=True)
            self.assertEqual(r.returncode, 0)
            limit = os.path.getsize(p) // 2
            out = run(mediaprep.prepare_for_send(p, "video", limit=limit, part_target=limit,
                                                 compress_max=10 * os.path.getsize(p)))
            self.assertTrue(out)
            for o in out:
                self.assertLessEqual(os.path.getsize(o.path), limit * 1.15)
                self.assertEqual(o.kind, "video")


class TestAdminPanel(unittest.TestCase):
    STATS = dict(users=5, vip=1, banned=0, today=3, today_ok=2, today_failed=1, total=10, rate=66,
                 top=[("Ali <b>", 1, 4)], reasons=[("no_video", 1)], stars=250, sales=1)

    def test_render_stats_escapes_and_has_numbers(self):
        for lang in ("ar", "en"):
            body = admin_panel.render_stats(lang, self.STATS, account_ok=True, queued=2, running=1)
            self.assertIn("Ali &lt;b&gt;", body)
            self.assertIn("250", body)
        empty = dict(self.STATS, top=[], reasons=[])
        self.assertTrue(admin_panel.render_stats("ar", empty, account_ok=False, queued=0, running=0))

    def _admin(self):
        stack = [
            mock.patch.object(admin_panel, "is_admin", lambda u: True),
            mock.patch.object(admin_panel, "lang_of", mock.AsyncMock(return_value="ar")),
            mock.patch.object(admin_panel.settings_store, "set_value", mock.AsyncMock()),
        ]
        for p in stack:
            p.start()
            self.addCleanup(p.stop)

    def test_footer_and_words_steps(self):
        self._admin()
        for state, key, value in ((admin_panel.ST_FOOTER, settings_store.CAPTION_FOOTER, "via me"),
                                  (admin_panel.ST_WORDS, settings_store.BLOCKED_WORDS, "a,b")):
            ctx = FakeContext()
            ctx.user_data["state"] = state
            with mock.patch.object(admin_panel, "get_state", lambda c, s=state: s):
                msg = FakeMessage(text=value)
                self.assertTrue(run(admin_panel.handle_text_step(FakeUpdate(message=msg), ctx)))
            admin_panel.settings_store.set_value.assert_awaited_with(key, value)
            self.assertEqual(len(msg.replies), 1)

    def test_toggle_maintenance_flips(self):
        self._admin()
        q = FakeQuery()
        with mock.patch.object(settings_store, "maintenance_on", lambda: False):
            run(admin_panel.toggle_maintenance(FakeUpdate(query=q), FakeContext()))
        admin_panel.settings_store.set_value.assert_awaited_with(settings_store.MAINTENANCE, "1")
        self.assertEqual(len(q.edits), 1)


class TestSenderFilters(unittest.TestCase):
    def test_blocked_words_in_filename_and_caption(self):
        with mock.patch.object(settings_store, "blocked_words", lambda: ["spam"]):
            self.assertEqual(sender.clean_filename("/t/My SPAM video.mp4"), "My  video.mp4")
            self.assertNotIn("spam", sender.build_caption("a Spam b", "ar", "Bot").lower().split("\n")[0])


if __name__ == "__main__":
    unittest.main()
