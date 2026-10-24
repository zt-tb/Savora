import asyncio
import os
import tempfile
import unittest

from tests import _stubs  # noqa: F401

from app import downloader as dl
from app.handlers import session_login


def run(coro):
    return asyncio.run(coro)


class MessageMediaPhoto:
    def __init__(self):
        self.photo = object()


class StoryItem:

    def __init__(self, media):
        self.media = media
        self.caption = ""


class TelethonLikeClient:

    def __init__(self, workdir):
        self.workdir = workdir
        self.received = None

    async def download_media(self, media, file=None):
        self.received = media
        if not isinstance(media, MessageMediaPhoto):
            return None
        path = os.path.join(file, "photo.jpg")
        with open(path, "wb") as fh:
            fh.write(b"\xff\xd8data")
        return path


class TestStoryMediaIsPassedDirectly(unittest.TestCase):
    def test_story_item_media_is_downloaded_not_the_item_itself(self):
        media = MessageMediaPhoto()
        story = StoryItem(media)
        with tempfile.TemporaryDirectory() as workdir:
            client = TelethonLikeClient(workdir)
            result = run(dl.download_media_file(client, story, workdir))
            self.assertIsNotNone(result, "الستوري لازم ينحمل — مو None/no_video")
            self.assertIs(client.received, media)
            path, kind = result
            self.assertEqual(kind, "photo")
            self.assertTrue(os.path.exists(path))


class TestStoryWithoutMedia(unittest.TestCase):
    def test_deleted_or_skipped_story_reports_unavailable(self):
        class Result:
            stories = [StoryItem(None)]

        class Client:
            async def get_entity(self, chat):
                return object()

            async def __call__(self, request):
                return Result()

        with self.assertRaises(dl.DownloadError) as ctx:
            run(dl.fetch_story(Client(), "chan", 1))
        self.assertEqual(ctx.exception.code, "story_unavailable")


class TestMediaKindNonFileMedia(unittest.TestCase):
    def test_webpage_preview_is_text(self):
        class WebPageMedia:
            webpage = object()

        class Msg:
            media = WebPageMedia()

        self.assertEqual(dl.media_kind(Msg()), "text")

    def test_poll_or_geo_is_text_not_document(self):
        class PollMedia:
            poll = object()

        class Msg:
            media = PollMedia()

        self.assertEqual(dl.media_kind(Msg()), "text")


class PTBLikeBot:

    def __init__(self):
        self.media_edits = []

    async def edit_message_media(self, media, chat_id=None, message_id=None, inline_message_id=None,
                                 reply_markup=None, business_connection_id=None):
        self.media_edits.append((media, chat_id, message_id, reply_markup))

    async def edit_message_caption(self, chat_id=None, message_id=None, inline_message_id=None, caption=None,
                                   reply_markup=None, parse_mode=None):
        pass


class FakeContext:
    def __init__(self, bot):
        self.bot = bot
        self.user_data = {}


class TestQrRefreshUsesPTBSignature(unittest.TestCase):
    def test_qr_refresh_edits_media_and_keeps_cancel_button(self):
        bot = PTBLikeBot()
        outcomes = iter(["expired", "error"])

        async def wait_qr():
            nxt = next(outcomes)
            if nxt == "error":
                raise session_login.LoginError("stop")
            return nxt

        async def refresh_qr():
            return "tg://login?token=new"

        orig_wait, orig_refresh = session_login.login_session.wait_qr, session_login.login_session.refresh_qr
        session_login.login_session.wait_qr = wait_qr
        session_login.login_session.refresh_qr = refresh_qr
        try:
            run(session_login._qr_watch(FakeContext(bot), 5, 77, "ar"))
        finally:
            session_login.login_session.wait_qr = orig_wait
            session_login.login_session.refresh_qr = orig_refresh
        self.assertEqual(len(bot.media_edits), 1, "تجديد رمز QR لازم ينجح (كان TypeError صامت)")
        _media, chat_id, message_id, markup = bot.media_edits[0]
        self.assertEqual((chat_id, message_id), (5, 77))
        self.assertIsNotNone(markup, "زر الإلغاء لازم يبقى بعد تجديد الرمز")


if __name__ == "__main__":
    unittest.main()
