import pathlib
import re
import string
import unittest
from html.parser import HTMLParser

from tests import _stubs  # noqa: F401

from app.texts import TEXTS, text
from app import ui

ALLOWED = {"b", "strong", "i", "em", "u", "ins", "s", "strike", "del", "code", "pre", "a", "tg-emoji",
           "tg-spoiler", "blockquote"}
_BAD_AMP = re.compile(r"&(?!(?:amp|lt|gt|quot|#\d+);)")


class _Checker(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=False)
        self.stack, self.errors = [], []

    def handle_starttag(self, tag, attrs):
        if tag not in ALLOWED:
            self.errors.append(f"وسم غير مسموح <{tag}>")
        if tag == "tg-emoji" and not re.fullmatch(r"\d+", dict(attrs).get("emoji-id", "")):
            self.errors.append("tg-emoji بلا emoji-id رقمي")
        self.stack.append(tag)

    def handle_endtag(self, tag):
        if not self.stack or self.stack[-1] != tag:
            self.errors.append(f"إغلاق غير متطابق </{tag}> (المفتوح: {self.stack})")
        else:
            self.stack.pop()


def _sample(template: str) -> str:
    args, kwargs = [], {}
    for _lit, field, _spec, _conv in string.Formatter().parse(template):
        if field is None:
            continue
        if field == "":
            args.append("1")
        else:
            kwargs[field] = "X"
    return template.format(*args, **kwargs)


def check_html(html_text: str) -> list[str]:
    checker = _Checker()
    checker.feed(html_text)
    errors = list(checker.errors)
    if checker.stack:
        errors.append(f"وسوم غير مغلقة: {checker.stack}")
    if _BAD_AMP.search(html_text):
        errors.append("& خام (لازم &amp;)")
    return errors


class TestEveryTextIsValidHtml(unittest.TestCase):
    def test_all_templates_parse(self):
        for lang in ("ar", "en"):
            for key, template in TEXTS[lang].items():
                with self.subTest(lang=lang, key=key):
                    self.assertEqual(check_html(_sample(template)), [])

    def test_all_texts_valid_when_animated_disabled(self):
        ui.set_animated(False)
        try:
            for lang in ("ar", "en"):
                for key, template in TEXTS[lang].items():
                    with self.subTest(lang=lang, key=key):
                        out = ui.render(_sample(template))
                        self.assertNotIn("tg-emoji", out)
                        self.assertEqual(check_html(out), [])
        finally:
            ui.set_animated(True)

    def test_checker_catches_bad_html(self):
        self.assertTrue(check_html("<b>x"))
        self.assertTrue(check_html("a & b"))
        self.assertTrue(check_html("<div>x</div>"))


class TestKeysUsedInCodeExist(unittest.TestCase):
    def test_static_keys_exist(self):
        root = pathlib.Path(__file__).resolve().parent.parent
        pattern = re.compile(r"""text\(\s*[^,()]+?,\s*["']([a-z0-9_]+)["']""")
        missing = []
        for path in list(root.glob("app/**/*.py")) + [root / "main.py"]:
            if path.name == "texts.py":
                continue
            for key in pattern.findall(path.read_text(encoding="utf-8")):
                if key not in TEXTS["ar"]:
                    missing.append((path.name, key))
        self.assertEqual(missing, [])

    def test_dynamic_key_families_complete(self):
        for plan in ("d1", "d7", "d30"):
            self.assertIn(f"plan_{plan}", TEXTS["ar"])
        for kind in ("photo", "video", "document", "audio", "voice", "animation", "sticker", "text"):
            self.assertIn(f"kind_{kind}", TEXTS["ar"])
        for status in ("none", "unauthorized", "disconnected"):
            self.assertIn(f"reason_{status}", TEXTS["ar"])


class TestAnimatedEmojiToggle(unittest.TestCase):
    def test_render_keeps_or_strips(self):
        tag = ui.em("zap")
        self.assertIn("<tg-emoji", tag)
        ui.set_animated(False)
        try:
            self.assertEqual(ui.render(tag), "⚡️")
        finally:
            ui.set_animated(True)
        self.assertEqual(ui.render(tag), tag)

    def test_text_applies_render(self):
        ui.set_animated(False)
        try:
            self.assertNotIn("tg-emoji", text("ar", "send_link"))
        finally:
            ui.set_animated(True)
        self.assertIn("tg-emoji", text("ar", "send_link"))

    def test_welcome_formats_all_fields(self):
        body = text("ar", "welcome", name="علي", plan="عادي", quota="▰▱ 1/2", nudge="")
        self.assertIn("علي", body)
        self.assertIn("1/2", body)
        self.assertNotIn("{", body)


if __name__ == "__main__":
    unittest.main()
