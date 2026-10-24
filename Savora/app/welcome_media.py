from __future__ import annotations

import html
import logging
import os
import re

from telegram import InlineKeyboardMarkup

from . import settings_store

logger = logging.getLogger(__name__)

DEFAULT_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "assets", "welcome.mp4")
CAPTION_LIMIT = 1024
KINDS = ("animation", "video", "photo")
_default_file_id: str | None = None
_TAG_RE = re.compile(r"<[^>]+>")


def parse(value: str) -> tuple[str, str] | None:
    kind, _, file_id = (value or "").partition(":")
    return (kind, file_id) if kind in KINDS and file_id else None


def custom() -> tuple[str, str] | None:
    return parse(settings_store.get(settings_store.WELCOME_MEDIA))


def extract(message) -> tuple[str, str] | None:
    if getattr(message, "animation", None):
        return "animation", message.animation.file_id
    if getattr(message, "video", None):
        return "video", message.video.file_id
    if getattr(message, "photo", None):
        return "photo", message.photo[-1].file_id
    return None


def _visible_len(body: str) -> int:
    return len(html.unescape(_TAG_RE.sub("", body)))


async def _send_by_id(message, kind: str, file_id: str, caption: str | None, markup):
    sender = {"animation": message.reply_animation, "video": message.reply_video, "photo": message.reply_photo}[kind]
    return await sender(file_id, caption=caption, reply_markup=markup)


async def _send_default(message, caption: str | None, markup):
    global _default_file_id
    if _default_file_id:
        try:
            return await message.reply_animation(_default_file_id, caption=caption, reply_markup=markup)
        except Exception:
            logger.info("file_id الافتراضي لم يعد صالحاً — إعادة رفع الملف", exc_info=True)
            _default_file_id = None
    with open(DEFAULT_PATH, "rb") as fh:
        sent = await message.reply_animation(fh, caption=caption, reply_markup=markup, filename="welcome.mp4",
                                             width=640, height=360, duration=4, write_timeout=60)
    media = getattr(sent, "animation", None) or getattr(sent, "document", None)
    _default_file_id = getattr(media, "file_id", None)
    return sent


async def send_welcome(message, body: str, markup: InlineKeyboardMarkup) -> None:
    fits = _visible_len(body) <= CAPTION_LIMIT
    caption, caption_markup = (body, markup) if fits else (None, None)
    attempts = []
    chosen = custom()
    if chosen is not None:
        attempts.append(lambda: _send_by_id(message, chosen[0], chosen[1], caption, caption_markup))
    if os.path.exists(DEFAULT_PATH) or _default_file_id:
        attempts.append(lambda: _send_default(message, caption, caption_markup))
    for attempt in attempts:
        try:
            await attempt()
        except Exception:
            logger.warning("تعذّر إرسال وسائط الترحيب", exc_info=True)
            continue
        if not fits:
            await message.reply_text(body, reply_markup=markup)
        return
    await message.reply_text(body, reply_markup=markup)
