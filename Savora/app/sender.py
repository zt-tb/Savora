from __future__ import annotations

import logging
import os
from contextlib import ExitStack
from typing import Sequence

from telegram import InputFile, InputMediaAudio, InputMediaDocument, InputMediaPhoto, InputMediaVideo

from . import settings_store
from .mediaprep import OutFile
from .texts import text
from .ui import esc

logger = logging.getLogger(__name__)

UPLOAD_TIMEOUT = 300
_TIMEOUTS = dict(read_timeout=UPLOAD_TIMEOUT, write_timeout=UPLOAD_TIMEOUT, connect_timeout=30, pool_timeout=30)
ALBUM_MAX = 10
CAPTION_LIMIT = 1024
TEXT_LIMIT = 4096


def clean_words(value: str) -> str:
    for word in settings_store.blocked_words():
        if not word:
            continue
        lowered, w, out, i = value.lower(), word.lower(), [], 0
        while True:
            j = lowered.find(w, i)
            if j < 0:
                out.append(value[i:])
                break
            out.append(value[i:j])
            i = j + len(w)
        value = "".join(out)
    return value


def clean_filename(path: str) -> str:
    base = os.path.basename(path)
    root, ext = os.path.splitext(base)
    if root.endswith(".part") or ".part" in ext:
        return base
    cleaned = clean_words(root).strip(" _-.")
    return (cleaned or root) + ext


def _fit(raw: str, budget: int) -> str:
    escaped = esc(raw)
    if len(escaped) <= budget:
        return escaped
    cut = raw
    while cut and len(esc(cut)) + 1 > budget:
        excess = len(esc(cut)) + 1 - budget
        cut = cut[: -max(1, excess)].rstrip()
    return (esc(cut) + "…") if cut else ""


def build_caption(original: str, language: str, bot_username: str, extra: str = "") -> str:
    footer_setting = settings_store.get(settings_store.CAPTION_FOOTER)
    if footer_setting == "-":
        footer = ""
    elif footer_setting:
        footer = esc(footer_setting)
    else:
        footer = text(language, "default_footer", bot=esc(bot_username)) if bot_username else ""
    tail = "".join(f"\n\n{part}" for part in (extra, footer) if part)
    if len(tail) > CAPTION_LIMIT - 20:
        tail = "".join(f"\n\n{part}" for part in (extra,) if part)
    body = _fit(clean_words(original or "").strip(), CAPTION_LIMIT - len(tail))
    return (body + tail).strip()


def build_text(original: str) -> str:
    return _fit(clean_words(original or "").strip(), TEXT_LIMIT)


def _groupable(files: Sequence[OutFile]) -> bool:
    if len(files) < 2:
        return False
    kinds = {f.kind for f in files}
    return kinds <= {"photo", "video"} or kinds == {"document"} or kinds == {"audio"}


async def _send_single(message, f: OutFile, fh, caption: str) -> None:
    name = clean_filename(f.path)
    common = dict(caption=caption or None, parse_mode="HTML", filename=name, **_TIMEOUTS)
    kind = f.kind
    if kind == "photo":
        await message.reply_photo(fh, **common)
    elif kind == "animation":
        await message.reply_animation(fh, **common)
    elif kind == "video":
        await message.reply_video(fh, supports_streaming=True, **common)
    elif kind == "voice":
        await message.reply_voice(fh, **common)
    elif kind == "audio":
        await message.reply_audio(fh, **common)
    elif kind == "sticker":
        try:
            await message.reply_sticker(InputFile(fh, filename=name), **_TIMEOUTS)
        except Exception:
            logger.info("تعذّر إرسال الملصق كملصق — يُرسل كملف", exc_info=True)
            fh.seek(0)
            await message.reply_document(fh, **common)
    else:
        await message.reply_document(fh, **common)


def _media_item(f: OutFile, fh, caption: str | None):
    name = clean_filename(f.path)
    kwargs = dict(caption=caption, parse_mode="HTML" if caption else None, filename=name)
    if f.kind == "photo":
        return InputMediaPhoto(fh, **kwargs)
    if f.kind == "video":
        return InputMediaVideo(fh, supports_streaming=True, **kwargs)
    if f.kind == "audio":
        return InputMediaAudio(fh, **kwargs)
    return InputMediaDocument(fh, **kwargs)


async def send_files(message, files: Sequence[OutFile], *, caption: str, part_caption=None) -> None:
    try:
        if _groupable(files) and not any(f.part for f in files):
            for start in range(0, len(files), ALBUM_MAX):
                chunk = files[start:start + ALBUM_MAX]
                if len(chunk) == 1:
                    with open(chunk[0].path, "rb") as fh:
                        await _send_single(message, chunk[0], fh, caption if start == 0 else "")
                    continue
                with ExitStack() as stack:
                    handles = [stack.enter_context(open(f.path, "rb")) for f in chunk]
                    media = [_media_item(f, fh, caption if (start == 0 and i == 0) else None)
                             for i, (f, fh) in enumerate(zip(chunk, handles))]
                    await message.reply_media_group(media, **_TIMEOUTS)
            return
        for i, f in enumerate(files):
            cap = caption if i == 0 else ""
            if f.part and part_caption is not None:
                note = part_caption(f.part[0], f.part[1], f.kind)
                cap = f"{caption}\n\n{note}".strip() if i == 0 else note
            with open(f.path, "rb") as fh:
                await _send_single(message, f, fh, cap)
    finally:
        for f in files:
            try:
                os.remove(f.path)
            except OSError:
                pass
