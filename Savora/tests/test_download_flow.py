import asyncio
import unittest
from datetime import timedelta
from unittest import mock

from tests import _stubs  # noqa: F401
from tests._fakes import FakeBot, FakeContext, FakeMessage, FakeMedia, FakeTelethon, FakeTLMessage, FakeUpdate, FakeUser

from app import mediaprep, settings_store
from app.download_queue import Job
from app.downloader import DownloadError
from app.handlers import download as dl
from app.links import extract_links


def run(coro):
    return asyncio.run(coro)


class Rec:

    def __init__(self, quota=5, can=True):
        self.records, self.quota, self.can = [], quota, can

    async def record_download(self, uid, kind, ok, error=None):
        self.records.append((kind, ok, error))

    async def can_download(self, uid):
        return self.can

    async def quota_left(self, uid):
        return self.quota


def patched(rec, client, session_dead=None):
    return mock.patch.multiple(
        dl.users, record_download=rec.record_download, can_download=rec.can_download, quota_left=rec.quota_left,
    ), mock.patch.object(dl.telethon_runtime, "get_client", mock.AsyncMock(return_value=client)), \
        mock.patch.object(dl.monitor, "report_session_dead", session_dead or mock.AsyncMock())


def make_job(urls, message=None):
    message = message or FakeMessage(text=" ".join(urls))
    return Job(id=1, user_id=7, language="ar", vip=False, links=extract_links(" ".join(urls)),
               message=message, status=FakeMessage(), bot_username="TestBot")


def go(job, rec, client, session_dead=None):
    a, b, c = patched(rec, client, session_dead)
    with a, b, c:
        run(dl.process_job(job))


class TestProcessJob(unittest.TestCase):
    def test_single_photo(self):
        client = FakeTelethon({5: FakeTLMessage(5, FakeMedia(photo=object()), "hello")})
        job, rec = make_job(["https://t.me/somechan/5"]), Rec()
        go(job, rec, client)
        kinds = [r[0] for r in job.message.replies]
        self.assertEqual(kinds, ["photo"])
        self.assertIn("hello", job.message.replies[0][2]["caption"])
        self.assertEqual(rec.records, [("photo", True, None)])
        self.assertIn("5", job.status.edits[-1][0])

    def test_free_result_card_nudges_to_vip(self):
        client = FakeTelethon({5: FakeTLMessage(5, FakeMedia(photo=object()))})
        job, rec = make_job(["https://t.me/somechan/5"]), Rec(quota=1)
        go(job, rec, client)
        body, kw = job.status.edits[-1]
        self.assertIn("1/2", body)
        self.assertEqual(kw["reply_markup"].inline_keyboard[0][0].callback_data, "vip_sub")

    def test_vip_result_card_has_no_upsell(self):
        client = FakeTelethon({5: FakeTLMessage(5, FakeMedia(photo=object()))})
        job, rec = make_job(["https://t.me/somechan/5"]), Rec(quota=None)
        go(job, rec, client)
        body, kw = job.status.edits[-1]
        self.assertNotIn("VIP", body)
        self.assertIsNone(kw.get("reply_markup"))

    def test_exhausted_after_download_shows_wait(self):
        client = FakeTelethon({5: FakeTLMessage(5, FakeMedia(photo=object()))})
        job, rec = make_job(["https://t.me/somechan/5"]), Rec(quota=0)
        with mock.patch.object(dl.users, "wait_remaining", mock.AsyncMock(return_value=timedelta(days=2))):
            go(job, rec, client)
        self.assertIn("2", job.status.edits[-1][0])

    def test_text_only_message_is_sent_as_text(self):
        client = FakeTelethon({5: FakeTLMessage(5, None, "just <text>")})
        job, rec = make_job(["https://t.me/somechan/5"]), Rec()
        go(job, rec, client)
        self.assertEqual(job.message.replies[0][:2], ("text", "just &lt;text&gt;"))
        self.assertEqual(rec.records, [("text", True, None)])

    def test_story_passes_media_not_item(self):
        media = FakeMedia(photo=object())
        story = type("Story", (), {"media": media, "caption": "cap"})()
        client = FakeTelethon(stories=[story])
        job, rec = make_job(["https://t.me/somechan/s/9"]), Rec()
        go(job, rec, client)
        self.assertIs(client.downloaded[0], media)
        self.assertEqual(rec.records, [("photo", True, None)])

    def test_album_is_sent_as_one_group(self):
        msgs = {i: FakeTLMessage(i, FakeMedia(photo=object()), "c" if i == 11 else "", grouped_id=77)
                for i in (10, 11, 12)}
        client = FakeTelethon(msgs)
        job, rec = make_job(["https://t.me/somechan/11"]), Rec()
        go(job, rec, client)
        self.assertEqual(len(job.message.replies), 1)
        kind, sizes, _kw = job.message.replies[0]
        self.assertEqual(kind, "group")
        self.assertEqual(len(sizes), 3)
        self.assertIn("c", sizes[0][2])
        self.assertIsNone(sizes[1][2])
        self.assertEqual(rec.records, [("album", True, None)])

    def test_missing_message_reports_no_video(self):
        job, rec = make_job(["https://t.me/somechan/5"]), Rec()
        go(job, rec, FakeTelethon({}))
        self.assertEqual(rec.records, [("message", False, "no_video")])
        self.assertTrue(job.status.edits)

    def test_session_dead_alerts_owner(self):
        from telethon.errors import AuthKeyUnregisteredError
        client = FakeTelethon({5: FakeTLMessage(5, FakeMedia(photo=object()))})
        client.raise_on = AuthKeyUnregisteredError("x")
        alert = mock.AsyncMock()
        job, rec = make_job(["https://t.me/somechan/5"]), Rec()
        go(job, rec, client, alert)
        alert.assert_awaited_once()
        self.assertEqual(rec.records[0][2], "session_dead")

    def test_batch_card_and_partial_failure(self):
        client = FakeTelethon({5: FakeTLMessage(5, FakeMedia(photo=object())), 6: None})
        job, rec = make_job(["https://t.me/somechan/5", "https://t.me/somechan/6"]), Rec()
        go(job, rec, client)
        self.assertEqual([r[1] for r in rec.records], [True, False])
        card = job.status.edits[-1][0]
        self.assertIn("1", card)

    def test_daily_limit_stops_batch(self):
        client = FakeTelethon({5: FakeTLMessage(5, FakeMedia(photo=object()))})
        job, rec = make_job(["https://t.me/somechan/5", "https://t.me/somechan/6"]), Rec(can=False)
        go(job, rec, client)
        self.assertEqual(client.downloaded, [])
        self.assertEqual(len(rec.records), 1)
        self.assertEqual(rec.records[0][2], "quota_exhausted")

    def test_big_file_is_split_by_bytes_under_limit(self):
        doc = type("Doc", (), {"attributes": [], "size": 0})()
        client = FakeTelethon({5: FakeTLMessage(5, FakeMedia(document=doc))}, size=300)
        job, rec = make_job(["https://t.me/somechan/5"]), Rec()
        with mock.patch.object(dl, "SEND_LIMIT", 100), \
                mock.patch.object(mediaprep, "SEND_LIMIT", 100), \
                mock.patch.object(mediaprep, "PART_TARGET", 100):
            async def prep(path, kind):
                return await mediaprep.prepare_for_send(path, kind, limit=100, part_target=100, compress_max=0)
            with mock.patch.object(dl, "prepare_for_send", prep):
                go(job, rec, client)
        sent = [r for r in job.message.replies if r[0] == "document"]
        self.assertEqual(len(sent), 3)
        self.assertTrue(all(r[1] <= 100 for r in sent))
        self.assertEqual(rec.records, [("document", True, None)])

    def test_status_deleted_falls_back_to_new_message(self):
        client = FakeTelethon({5: FakeTLMessage(5, FakeMedia(photo=object()))})
        job, rec = make_job(["https://t.me/somechan/5"]), Rec()
        job.status.fail_edit = True
        go(job, rec, client)
        kinds = [r[0] for r in job.message.replies]
        self.assertEqual(kinds, ["photo", "text"])


class TestHandleLink(unittest.TestCase):
    def setUp(self):
        self.q = dl.DownloadQueue()
        self.left = 2
        self.patches = [
            mock.patch.object(dl, "queue", self.q),
            mock.patch.object(dl.users, "get_or_create", mock.AsyncMock()),
            mock.patch.object(dl, "lang_of", mock.AsyncMock(return_value="ar")),
            mock.patch.object(dl.users, "is_banned", mock.AsyncMock(return_value=False)),
            mock.patch.object(dl.users, "is_vip", mock.AsyncMock(side_effect=lambda uid: self.left is None)),
            mock.patch.object(dl.users, "quota_left", mock.AsyncMock(side_effect=lambda uid: self.left)),
            mock.patch.object(dl.users, "wait_remaining", mock.AsyncMock(return_value=timedelta(hours=40))),
            mock.patch.object(dl.telethon_runtime, "get_client",
                              mock.AsyncMock(return_value=FakeTelethon(connected=True))),
            mock.patch.object(settings_store, "maintenance_on", lambda: False),
            mock.patch.object(dl, "is_admin", lambda update: False),
        ]
        for p in self.patches:
            p.start()
        self.addCleanup(lambda: [p.stop() for p in reversed(self.patches)])

    def call(self, text, user=None):
        msg = FakeMessage(text=text)
        upd = FakeUpdate(user=user or FakeUser(), message=msg)
        ctx = FakeContext(FakeBot())

        async def go_():
            await self.q.start(mock.AsyncMock(), mock.AsyncMock(), 1)
            await dl.handle_link(upd, ctx)
            await asyncio.sleep(0.02)
            await self.q.stop()
        run(go_())
        return msg

    def test_invalid_link(self):
        msg = self.call("hello world")
        self.assertEqual(len(msg.replies), 1)

    def test_non_telegram_link_is_rejected(self):
        msg = self.call("https://youtu.be/abc123")
        self.assertEqual(len(msg.replies), 1)
        self.assertEqual(self.q.size(), 0)

    def test_maintenance_blocks_non_admin(self):
        with mock.patch.object(settings_store, "maintenance_on", lambda: True):
            msg = self.call("https://t.me/somechan/5")
        self.assertEqual(len(msg.replies), 1)
        self.assertEqual(self.q.size(), 0)

    def test_maintenance_allows_admin(self):
        with mock.patch.object(settings_store, "maintenance_on", lambda: True), \
                mock.patch.object(dl, "is_admin", lambda update: True):
            msg = self.call("https://t.me/somechan/5")
        self.assertEqual(len(msg.replies), 1)

    def test_free_batch_capped_by_remaining_balance(self):
        self.left = 1
        msg = self.call("https://t.me/somechan/5 https://t.me/somechan/6")
        self.assertEqual(len(msg.replies), 1)
        self.assertEqual(self.q.size(), 0)

    def test_vip_may_send_many_links(self):
        self.left = None
        links = " ".join(f"https://t.me/somechan/{i}" for i in range(1, 8))
        msg = self.call(links)
        self.assertEqual(len(msg.replies), 1)
        self.assertEqual(msg.replies[0][0], "text")

    def test_offline_downloader(self):
        with mock.patch.object(dl.telethon_runtime, "get_client", mock.AsyncMock(return_value=None)):
            msg = self.call("https://t.me/somechan/5")
        self.assertEqual(len(msg.replies), 1)

    def test_exhausted_free_user_gets_wait_and_upgrade_buttons(self):
        self.left = 0
        msg = self.call("https://t.me/somechan/5")
        kind, body, kw = msg.replies[0]
        self.assertIn("40", body)
        rows = kw["reply_markup"].inline_keyboard
        self.assertEqual([r[0].callback_data for r in rows], ["vip_sub", "share_earn"])
        self.assertEqual(self.q.size(), 0)

    def test_pending_jobs_reserve_the_balance(self):
        self.left = 1
        with mock.patch.object(dl.queue, "links_for", return_value=1):
            msg = self.call("https://t.me/somechan/5")
        self.assertEqual(len(msg.replies), 1)
        self.assertEqual(self.q.size(), 0)

    def test_too_many_pending(self):
        self.left = None
        with mock.patch.object(dl.queue, "pending_for", return_value=dl.MAX_PENDING_PER_USER):
            msg = self.call("https://t.me/somechan/5")
        self.assertEqual(len(msg.replies), 1)


class TestQueuedCard(unittest.TestCase):
    def test_vip_hint_only_for_free_users(self):
        for vip, expect in ((False, True), (True, False)):
            job = make_job(["https://t.me/somechan/5"])
            job.vip = vip
            run(dl._show_queued(job, 2, 3))
            body, kw = job.status.edits[-1]
            self.assertEqual("VIP" in body, expect)
            self.assertEqual(kw["reply_markup"].inline_keyboard[0][0].callback_data, "jobcancel_1")
            self.assertEqual(job.shown_pos, 2)


class TestHelpers(unittest.TestCase):
    def test_error_text_maps_codes(self):
        self.assertEqual(dl._error_text("ar", DownloadError("session_dead")), dl._error_text("ar", DownloadError("downloader_offline")))
        self.assertTrue(dl._error_text("ar", DownloadError("flood_wait", "30")))
        self.assertTrue(dl._error_text("ar", DownloadError("unknown_code")))

    def test_caption_of_story_and_message(self):
        self.assertEqual(dl._caption_of(type("S", (), {"caption": " hi "})()), "hi")
        self.assertEqual(dl._caption_of(FakeTLMessage(1, None, "yo")), "yo")


if __name__ == "__main__":
    unittest.main()
