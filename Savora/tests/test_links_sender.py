import asyncio
import os
import tempfile
import unittest

from tests import _stubs  # noqa: F401
from tests._fakes import FakeMessage

from app import settings_store as ss
from app import sender
from app.links import extract_links
from app.mediaprep import OutFile


def run(c):
    return asyncio.run(c)


class TestExtractLinks(unittest.TestCase):
    def test_multiple_telegram_links_in_order_no_duplicates(self):
        t = "https://t.me/chan_one/5  https://t.me/chan_two/s/9\nhttps://t.me/chan_one/5"
        links = extract_links(t)
        self.assertEqual([l.url for l in links], ["https://t.me/chan_one/5", "https://t.me/chan_two/s/9"])
        self.assertEqual([l.parsed.kind for l in links], ["message", "story"])

    def test_non_telegram_links_are_ignored(self):
        links = extract_links("https://youtu.be/abc123 https://t.me/c/123456/7 https://example.com/x")
        self.assertEqual([l.url for l in links], ["https://t.me/c/123456/7"])
        self.assertEqual(links[0].parsed.chat, -100123456)

    def test_punctuation_around_links_is_stripped(self):
        links = extract_links("شوف (https://t.me/abcde/12)، وهذا: <https://t.me/abcde/13>.")
        self.assertEqual(len(links), 2)

    def test_no_links(self):
        self.assertEqual(extract_links("مرحبا"), [])
        self.assertEqual(extract_links(""), [])

    def test_other_sites_are_never_links(self):
        for url in ("https://evil.com/?u=youtube.com", "https://youtu.be/x", "https://www.tiktok.com/@a/video/1"):
            self.assertEqual(extract_links(url), [])

    def test_limit(self):
        text = " ".join(f"https://t.me/chan_x/{i}" for i in range(1, 80))
        self.assertEqual(len(extract_links(text, limit=10)), 10)


class TestCaption(unittest.TestCase):
    def setUp(self):
        ss._cache.clear()

    def test_default_footer_with_bot_name(self):
        cap = sender.build_caption("مرحبا", "ar", "MyBot")
        self.assertIn("مرحبا", cap)
        self.assertIn("@MyBot", cap)

    def test_owner_footer_overrides_and_is_escaped(self):
        ss._cache[ss.CAPTION_FOOTER] = "via <me> & co"
        cap = sender.build_caption("x", "ar", "MyBot")
        self.assertIn("via &lt;me&gt; &amp; co", cap)
        self.assertNotIn("@MyBot", cap)

    def test_footer_disabled_with_dash(self):
        ss._cache[ss.CAPTION_FOOTER] = "-"
        self.assertEqual(sender.build_caption("hello", "ar", "MyBot"), "hello")

    def test_original_caption_is_escaped(self):
        self.assertIn("&lt;script&gt;", sender.build_caption("<script>", "en", "B"))

    def test_caption_never_exceeds_telegram_limit_even_with_heavy_escaping(self):
        nasty = "<&>" * 2000
        cap = sender.build_caption(nasty, "ar", "MyBot", extra="note")
        self.assertLessEqual(len(cap), sender.CAPTION_LIMIT)
        self.assertNotIn("&am…", cap)
        self.assertNotRegex(cap, r"&[a-z#0-9]*$")

    def test_blocked_words_removed_case_insensitively(self):
        ss._cache[ss.BLOCKED_WORDS] = "@Channel, www.site.com"
        cap = sender.build_caption("شوف @channel و WWW.SITE.COM الآن", "ar", "")
        self.assertNotIn("channel", cap.lower())
        self.assertNotIn("site.com", cap.lower())
        self.assertIn("الآن", cap)

    def test_filename_cleaning_keeps_extension_and_part_suffix(self):
        ss._cache[ss.BLOCKED_WORDS] = "@promo"
        self.assertEqual(sender.clean_filename("/tmp/video @promo.mp4"), "video.mp4")
        self.assertEqual(sender.clean_filename("/tmp/@promo.mp4"), "@promo.mp4")
        self.assertEqual(sender.clean_filename("/tmp/file.bin.part001"), "file.bin.part001")

    def test_build_text_fits_4096(self):
        self.assertLessEqual(len(sender.build_text("&" * 9000)), sender.TEXT_LIMIT)


class TestSendFiles(unittest.TestCase):
    def _files(self, d, spec):
        out = []
        for i, (kind, size) in enumerate(spec):
            p = os.path.join(d, f"f{i}.bin")
            open(p, "wb").write(b"z" * size)
            out.append(OutFile(p, kind))
        return out

    def test_photos_and_videos_go_as_one_album_with_caption_on_first_only(self):
        with tempfile.TemporaryDirectory() as d:
            msg = FakeMessage()
            files = self._files(d, [("photo", 10), ("video", 20), ("photo", 30)])
            run(sender.send_files(msg, files, caption="CAP"))
            kind, items, kw = msg.replies[0]
            self.assertEqual(kind, "group")
            self.assertEqual([i[0] for i in items], ["InputMediaPhoto", "InputMediaVideo", "InputMediaPhoto"])
            self.assertEqual([i[2] for i in items], ["CAP", None, None])
            self.assertEqual(kw["write_timeout"], sender.UPLOAD_TIMEOUT)
            self.assertEqual([os.path.exists(f.path) for f in files], [False] * 3)

    def test_mixed_kinds_fall_back_to_individual_sends(self):
        with tempfile.TemporaryDirectory() as d:
            msg = FakeMessage()
            run(sender.send_files(msg, self._files(d, [("photo", 5), ("audio", 6)]), caption="C"))
            self.assertEqual([r[0] for r in msg.replies], ["photo", "audio"])
            self.assertEqual(msg.replies[0][2]["caption"], "C")
            self.assertIsNone(msg.replies[1][2]["caption"])

    def test_album_larger_than_ten_is_chunked(self):
        with tempfile.TemporaryDirectory() as d:
            msg = FakeMessage()
            run(sender.send_files(msg, self._files(d, [("photo", 3)] * 11), caption="C"))
            self.assertEqual([r[0] for r in msg.replies], ["group", "photo"])
            self.assertIsNone(msg.replies[1][2]["caption"])

    def test_split_parts_are_sent_in_order_with_part_notes(self):
        with tempfile.TemporaryDirectory() as d:
            msg = FakeMessage()
            files = self._files(d, [("document", 4), ("document", 4)])
            files[0].part, files[1].part = (1, 2), (2, 2)
            run(sender.send_files(msg, files, caption="CAP", part_caption=lambda i, n, k: f"part {i}/{n}"))
            self.assertEqual([r[0] for r in msg.replies], ["document", "document"])
            self.assertEqual(msg.replies[0][2]["caption"], "CAP\n\npart 1/2")
            self.assertEqual(msg.replies[1][2]["caption"], "part 2/2")

    def test_files_removed_even_when_sending_fails(self):
        class Boom(FakeMessage):
            async def reply_document(self, fh, **kw):
                raise RuntimeError("network")
        with tempfile.TemporaryDirectory() as d:
            files = self._files(d, [("document", 4)])
            with self.assertRaises(RuntimeError):
                run(sender.send_files(Boom(), files, caption=""))
            self.assertFalse(os.path.exists(files[0].path))

    def test_failed_sticker_is_resent_as_document(self):
        class StickerFails(FakeMessage):
            async def reply_sticker(self, fh, **kw):
                raise RuntimeError("STICKER_INVALID")
        with tempfile.TemporaryDirectory() as d:
            msg = StickerFails()
            run(sender.send_files(msg, self._files(d, [("sticker", 7)]), caption=""))
            self.assertEqual(msg.replies[0][0], "document")
            self.assertEqual(msg.replies[0][1], 7)


if __name__ == "__main__":
    unittest.main()
