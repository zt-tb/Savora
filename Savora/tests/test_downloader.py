import unittest

from tests import _stubs  # noqa: F401

from app import downloader as dl
from telethon.tl.types import (  # noqa: E402
    DocumentAttributeAnimated,
    DocumentAttributeAudio,
    DocumentAttributeSticker,
    DocumentAttributeVideo,
)


class FakeDoc:
    def __init__(self, attributes):
        self.attributes = attributes


class FakeMedia:
    def __init__(self, photo=None, document=None):
        self.photo = photo
        self.document = document


class FakeMessage:
    def __init__(self, media=None, text=""):
        self.media = media
        self.text = text


class TestParseLink(unittest.TestCase):
    def test_public_message_link(self):
        p = dl.parse_link("https://t.me/somechannel/123")
        self.assertEqual(p.kind, "message")
        self.assertEqual(p.chat, "somechannel")
        self.assertEqual(p.msg_or_story_id, 123)

    def test_private_channel_link_c_prefix(self):
        p = dl.parse_link("https://t.me/c/1234567890/42")
        self.assertEqual(p.kind, "message")
        self.assertEqual(p.chat, -1001234567890)
        self.assertEqual(p.msg_or_story_id, 42)

    def test_story_link(self):
        p = dl.parse_link("https://t.me/somechannel/s/99")
        self.assertEqual(p.kind, "story")
        self.assertEqual(p.chat, "somechannel")
        self.assertEqual(p.msg_or_story_id, 99)

    def test_link_with_query_string_still_parses(self):
        p = dl.parse_link("https://t.me/somechannel/123?single")
        self.assertIsNotNone(p)
        self.assertEqual(p.msg_or_story_id, 123)

    def test_not_a_link_returns_none(self):
        self.assertIsNone(dl.parse_link("هذا نص عادي مو رابط"))

    def test_strips_whitespace(self):
        p = dl.parse_link("   https://t.me/somechannel/5   ")
        self.assertIsNotNone(p)


class TestMediaKind(unittest.TestCase):
    def test_text_only(self):
        self.assertEqual(dl.media_kind(FakeMessage(media=None)), "text")

    def test_photo(self):
        msg = FakeMessage(media=FakeMedia(photo=object()))
        self.assertEqual(dl.media_kind(msg), "photo")

    def test_sticker(self):
        doc = FakeDoc([DocumentAttributeSticker()])
        msg = FakeMessage(media=FakeMedia(document=doc))
        self.assertEqual(dl.media_kind(msg), "sticker")

    def test_animation_gif(self):
        doc = FakeDoc([DocumentAttributeAnimated()])
        msg = FakeMessage(media=FakeMedia(document=doc))
        self.assertEqual(dl.media_kind(msg), "animation")

    def test_voice_note(self):
        doc = FakeDoc([DocumentAttributeAudio(voice=True)])
        msg = FakeMessage(media=FakeMedia(document=doc))
        self.assertEqual(dl.media_kind(msg), "voice")

    def test_audio_music(self):
        doc = FakeDoc([DocumentAttributeAudio(voice=False)])
        msg = FakeMessage(media=FakeMedia(document=doc))
        self.assertEqual(dl.media_kind(msg), "audio")

    def test_video(self):
        doc = FakeDoc([DocumentAttributeVideo()])
        msg = FakeMessage(media=FakeMedia(document=doc))
        self.assertEqual(dl.media_kind(msg), "video")

    def test_generic_document(self):
        doc = FakeDoc([])
        msg = FakeMessage(media=FakeMedia(document=doc))
        self.assertEqual(dl.media_kind(msg), "document")


if __name__ == "__main__":
    unittest.main()
