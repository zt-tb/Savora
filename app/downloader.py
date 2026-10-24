from __future__ import annotations

import logging
import os
import re
from dataclasses import dataclass
from typing import Optional

from telethon.errors import (
    AuthKeyDuplicatedError,
    AuthKeyUnregisteredError,
    ChannelPrivateError,
    ChatAdminRequiredError,
    FloodWaitError,
    RPCError,
    SessionExpiredError,
    SessionRevokedError,
    UserDeactivatedBanError,
    UserDeactivatedError,
)
from telethon.tl.functions.stories import GetStoriesByIDRequest
from telethon.tl.types import (
    DocumentAttributeAnimated,
    DocumentAttributeAudio,
    DocumentAttributeSticker,
    DocumentAttributeVideo,
)

logger = logging.getLogger(__name__)

TWO_GB = 2 * 1024 * 1024 * 1024
ALBUM_SCAN_RADIUS = 9

SESSION_DEAD_ERRORS = (
    AuthKeyDuplicatedError,
    AuthKeyUnregisteredError,
    SessionExpiredError,
    SessionRevokedError,
    UserDeactivatedBanError,
    UserDeactivatedError,
)

_MSG_LINK_RE = re.compile(r"t\.me/(c/\d+|[A-Za-z0-9_]{5,32})/(\d+)(?:\?.*)?$")
_STORY_LINK_RE = re.compile(r"t\.me/([A-Za-z0-9_]{5,32})/s/(\d+)(?:\?.*)?$")


@dataclass
class ParsedLink:
    kind: str
    chat: int | str
    msg_or_story_id: int


def parse_link(text: str) -> Optional[ParsedLink]:
    text = text.strip()
    m = _STORY_LINK_RE.search(text)
    if m:
        return ParsedLink("story", m.group(1), int(m.group(2)))
    m = _MSG_LINK_RE.search(text)
    if m:
        raw_chat = m.group(1)
        chat = int(f"-100{raw_chat.split('/', 1)[1]}") if raw_chat.startswith("c/") else raw_chat
        return ParsedLink("message", chat, int(m.group(2)))
    return None


def media_kind(message) -> str:
    media = getattr(message, "media", None)
    if media is None:
        return "text"
    if getattr(media, "webpage", None) is not None:
        return "text"
    if getattr(media, "photo", None) is not None:
        return "photo"
    doc = getattr(media, "document", None)
    if doc is not None:
        attrs = getattr(doc, "attributes", []) or []
        if any(isinstance(a, DocumentAttributeSticker) for a in attrs):
            return "sticker"
        if any(isinstance(a, DocumentAttributeAnimated) for a in attrs):
            return "animation"
        if any(isinstance(a, DocumentAttributeAudio) for a in attrs):
            return "voice" if any(getattr(a, "voice", False) for a in attrs if isinstance(a, DocumentAttributeAudio)) else "audio"
        if any(isinstance(a, DocumentAttributeVideo) for a in attrs):
            return "video"
        return "document"
    return "text"


class DownloadError(Exception):

    def __init__(self, code: str, extra: str = ""):
        self.code, self.extra = code, extra
        super().__init__(code)


async def fetch_message(client, chat, message_id: int):
    try:
        message = await client.get_messages(chat, ids=message_id)
    except SESSION_DEAD_ERRORS as exc:
        raise DownloadError("session_dead") from exc
    except (ChannelPrivateError, ChatAdminRequiredError) as exc:
        raise DownloadError("private_access") from exc
    except FloodWaitError as exc:
        raise DownloadError("flood_wait", str(exc.seconds)) from exc
    except ValueError as exc:
        raise DownloadError("private_access") from exc
    if message is None:
        raise DownloadError("no_video")
    return message


async def fetch_album(client, chat, message) -> list:
    group = getattr(message, "grouped_id", None)
    if not group:
        return [message]
    ids = list(range(max(1, message.id - ALBUM_SCAN_RADIUS), message.id + ALBUM_SCAN_RADIUS + 1))
    try:
        neighbours = await client.get_messages(chat, ids=ids)
    except SESSION_DEAD_ERRORS as exc:
        raise DownloadError("session_dead") from exc
    except FloodWaitError as exc:
        raise DownloadError("flood_wait", str(exc.seconds)) from exc
    except Exception:
        logger.warning("تعذّر جلب بقية الألبوم — نكتفي بالرسالة نفسها", exc_info=True)
        return [message]
    album = [m for m in (neighbours or []) if m is not None and getattr(m, "grouped_id", None) == group]
    album.sort(key=lambda m: m.id)
    return album or [message]


async def fetch_story(client, chat, story_id: int):
    try:
        entity = await client.get_entity(chat)
    except SESSION_DEAD_ERRORS as exc:
        raise DownloadError("session_dead") from exc
    except ValueError as exc:
        raise DownloadError("private_access") from exc
    except (ChannelPrivateError, ChatAdminRequiredError) as exc:
        raise DownloadError("private_access") from exc
    except FloodWaitError as exc:
        raise DownloadError("flood_wait", str(exc.seconds)) from exc
    try:
        result = await client(GetStoriesByIDRequest(peer=entity, id=[story_id]))
    except SESSION_DEAD_ERRORS as exc:
        raise DownloadError("session_dead") from exc
    except (ChannelPrivateError, ChatAdminRequiredError) as exc:
        raise DownloadError("private_access") from exc
    except FloodWaitError as exc:
        raise DownloadError("flood_wait", str(exc.seconds)) from exc
    except RPCError as exc:
        logger.info("تعذّر جلب الستوري %s من %s: %s", story_id, chat, exc)
        raise DownloadError("story_unavailable") from exc
    stories = getattr(result, "stories", None) or []
    if not stories:
        raise DownloadError("story_unavailable")
    story = stories[0]
    if getattr(story, "media", None) is None:
        raise DownloadError("story_unavailable")
    return story


def media_size(message) -> int | None:
    doc = getattr(getattr(message, "media", None), "document", None)
    size = getattr(doc, "size", None) if doc is not None else None
    return int(size) if isinstance(size, (int, float)) else None


async def download_media_file(client, message, workdir: str, progress_callback=None) -> tuple[str, str] | None:
    kind = media_kind(message)
    if kind == "text":
        return None
    size_before = media_size(message)
    if size_before is not None and size_before > TWO_GB:
        raise DownloadError("file_too_large")
    kwargs = {"progress_callback": progress_callback} if progress_callback is not None else {}
    try:
        path = await client.download_media(message.media, file=workdir, **kwargs)
    except SESSION_DEAD_ERRORS as exc:
        raise DownloadError("session_dead") from exc
    except FloodWaitError as exc:
        raise DownloadError("flood_wait", str(exc.seconds)) from exc
    if not path or not os.path.exists(path):
        raise DownloadError("no_video")
    if os.path.getsize(path) > TWO_GB:
        os.remove(path)
        raise DownloadError("file_too_large")
    return path, kind
