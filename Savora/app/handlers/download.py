from __future__ import annotations

import asyncio
import logging
import os
import tempfile
import time
from dataclasses import dataclass

from telegram import InlineKeyboardMarkup, Update
from telegram.ext import ContextTypes

from .. import emoji_ids as E
from .. import monitor, settings_store, telethon_runtime, users
from ..buttons import DANGER, btn
from ..config import settings
from ..download_queue import MAX_PENDING_PER_USER, MAX_QUEUE, DownloadQueue, Job
from ..downloader import (
    DownloadError,
    download_media_file,
    fetch_album,
    fetch_message,
    fetch_story,
)
from ..links import Link, extract_links
from ..mediaprep import SEND_LIMIT, OutFile, prepare_for_send
from ..plans import per_day_stars
from ..progress import Progress
from ..sender import build_caption, build_text, send_files
from ..texts import TEXTS, text
from ..ui import bar, human_delta, human_seconds, human_size
from .common import is_admin, lang_of, quota_view, upgrade_keyboard

logger = logging.getLogger(__name__)

queue = DownloadQueue()
CANCEL_PREFIX = "jobcancel_"


def is_download_request(value: str) -> bool:
    return bool(extract_links(value))


def _step(index: int, n: int, sub: str = "") -> str:
    base = f" · {index}/{n}" if n > 1 else ""
    return f"{base}{sub}"


def _cancel_kb(language: str, job_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([[btn(text(language, "cancel_job_btn"), f"{CANCEL_PREFIX}{job_id}",
                                      style=DANGER, emoji=E.FORBIDDEN)]])


def _limit_text(language: str, wait: str) -> str:
    return text(language, "quota_exhausted", wait=wait, vip_batch=users.VIP_BATCH_LIMIT, per_day=per_day_stars())


def _error_text(language: str, exc: DownloadError) -> str:
    if exc.code == "quota_exhausted":
        return _limit_text(language, exc.extra)
    code = "downloader_offline" if exc.code == "session_dead" else exc.code
    if code not in TEXTS["ar"]:
        code = "error"
    return text(language, code, exc.extra) if exc.extra else text(language, code)


def _kind_label(language: str, kind: str, count: int = 1) -> str:
    if count > 1:
        return text(language, "kind_album", count=count)
    return text(language, f"kind_{kind}" if f"kind_{kind}" in TEXTS["ar"] else "kind_document")


def _link_kind(link: Link) -> str:
    return "story" if link.parsed.kind == "story" else "message"


def _caption_of(obj) -> str:
    return (getattr(obj, "text", None) or getattr(obj, "message", None) or getattr(obj, "caption", None) or "").strip()


async def _edit(job: Job, body: str, markup=None) -> bool:
    try:
        await job.status.edit_text(body, reply_markup=markup)
        return True
    except Exception:
        logger.debug("تعذّر تعديل رسالة الحالة", exc_info=True)
        return False


async def _show_queued(job: Job, pos: int, total: int) -> None:
    job.shown_pos = pos
    hint = "" if job.vip else text(job.language, "queue_vip_hint")
    await _edit(job, text(job.language, "card_queued", pos=pos, total=total, n=len(job.links), hint=hint),
                _cancel_kb(job.language, job.id))


async def handle_link(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user, message = update.effective_user, update.message
    await users.get_or_create(user.id, user.full_name or str(user.id), user.username)
    language = await lang_of(update)
    if await users.is_banned(user.id):
        await message.reply_text(text(language, "you_are_banned"))
        return
    if settings_store.maintenance_on() and not is_admin(update):
        await message.reply_text(text(language, "maintenance"))
        return

    links = extract_links(message.text or "")
    if not links:
        await message.reply_text(text(language, "invalid_link"))
        return
    vip = await users.is_vip(user.id)
    left = await users.quota_left(user.id)
    if left == 0:
        wait = await users.wait_remaining(user.id) or users.COOLDOWN
        await message.reply_text(_limit_text(language, human_delta(wait, language)),
                                 reply_markup=upgrade_keyboard(language))
        return
    limit = users.batch_limit(vip) if left is None else min(users.batch_limit(vip), left)
    if len(links) > limit:
        await message.reply_text(text(language, "batch_limit", max=limit))
        return
    client = await telethon_runtime.get_client()
    if client is None or not client.is_connected():
        await message.reply_text(text(language, "downloader_offline"))
        return
    if left is not None and queue.links_for(user.id) >= left:
        await message.reply_text(text(language, "too_many_pending", max=left))
        return
    if queue.pending_for(user.id) >= MAX_PENDING_PER_USER:
        await message.reply_text(text(language, "too_many_pending", max=MAX_PENDING_PER_USER))
        return
    if queue.size() >= MAX_QUEUE:
        await message.reply_text(text(language, "queue_full"))
        return

    status = await message.reply_text(text(language, "card_fetching", step=""))
    job = Job(id=queue.next_id(), user_id=user.id, language=language, vip=vip, links=links,
              message=message, status=status, bot_username=context.bot.username or "")
    pos, total, waits = await queue.submit(job)
    if waits:
        await _show_queued(job, pos, total)


async def cancel_job(update: Update, context: ContextTypes.DEFAULT_TYPE, job_id: int) -> None:
    query = update.callback_query
    language = await lang_of(update)
    job = queue.cancel(job_id, update.effective_user.id)
    if job is None:
        await query.answer(text(language, "job_not_cancellable"), show_alert=True)
        return
    await query.answer()
    await _edit(job, text(language, "job_cancelled"))


async def start_workers() -> None:
    await queue.start(process_job, _show_queued, settings.download_workers)


async def stop_workers() -> None:
    await queue.stop()


@dataclass
class LinkInfo:
    kind: str
    size: int
    count: int = 1


@dataclass
class LinkResult:
    ok: bool
    info: LinkInfo | None = None
    error: DownloadError | None = None
    seconds: float = 0.0


@dataclass
class Fetched:
    items: list
    caption: str


async def _fetch_telegram(job: Job, link: Link, workdir: str, progress: Progress) -> Fetched:
    client = await telethon_runtime.get_client()
    if client is None or not client.is_connected():
        raise DownloadError("downloader_offline")
    parsed = link.parsed
    if parsed.kind == "story":
        messages = [await fetch_story(client, parsed.chat, parsed.msg_or_story_id)]
    else:
        first = await fetch_message(client, parsed.chat, parsed.msg_or_story_id)
        messages = await fetch_album(client, parsed.chat, first)
    caption = next((c for c in (_caption_of(m) for m in messages) if c), "")
    items = []
    async with progress.watching(job.status):
        for message in messages:
            progress.callback(0, None)
            got = await download_media_file(client, message, workdir, progress.callback)
            if got is not None:
                items.append(got)
    return Fetched(items, caption)


async def _process_link(job: Job, link: Link, index: int, n: int) -> LinkInfo:
    language = job.language
    if not await users.can_download(job.user_id):
        wait = await users.wait_remaining(job.user_id) or users.COOLDOWN
        raise DownloadError("quota_exhausted", human_delta(wait, language))
    step = _step(index, n)
    await _edit(job, text(language, "card_fetching", step=step))

    def render(cur: int, total: int | None) -> str:
        if total:
            return text(language, "card_downloading", step=step, bar=bar(cur * 100 / total),
                        pct=min(100, int(cur * 100 / total)), cur=human_size(cur), total=human_size(total))
        return text(language, "card_downloading_nototal", step=step, cur=human_size(cur))

    progress = Progress(render)
    with tempfile.TemporaryDirectory(prefix="ts_dl_") as workdir:
        fetched = await _fetch_telegram(job, link, workdir, progress)

        if not fetched.items:
            if not fetched.caption:
                raise DownloadError("no_video")
            await job.message.reply_text(build_text(fetched.caption))
            await users.record_download(job.user_id, "text", True)
            return LinkInfo("text", 0)

        outs: list[OutFile] = []
        if any(os.path.getsize(path) > SEND_LIMIT for path, _ in fetched.items):
            await _edit(job, text(language, "card_processing", step=step))
        for path, kind in fetched.items:
            outs.extend(await prepare_for_send(path, kind))
        total_size = sum(os.path.getsize(o.path) for o in outs)
        kind = fetched.items[0][1] if len(fetched.items) == 1 else "album"

        await _edit(job, text(language, "card_uploading", step=step))
        caption = build_caption(fetched.caption, language, job.bot_username)

        def part_caption(i: int, count: int, part_kind: str) -> str:
            return text(language, "split_part_video" if part_kind == "video" else "split_part", i=i, n=count)

        await send_files(job.message, outs, caption=caption, part_caption=part_caption)

    await users.record_download(job.user_id, kind, True)
    return LinkInfo(kind, total_size, len(fetched.items))


async def process_job(job: Job) -> None:
    language, n = job.language, len(job.links)
    results: list[LinkResult] = []
    for index, link in enumerate(job.links, 1):
        started = time.monotonic()
        try:
            info = await _process_link(job, link, index, n)
            results.append(LinkResult(True, info=info, seconds=time.monotonic() - started))
        except DownloadError as exc:
            results.append(LinkResult(False, error=exc, seconds=time.monotonic() - started))
            await users.record_download(job.user_id, _link_kind(link), False, exc.code)
            if exc.code == "session_dead":
                await monitor.report_session_dead(job.message.get_bot())
            if exc.code == "quota_exhausted":
                for _ in job.links[index:]:
                    results.append(LinkResult(False, error=exc))
                break
        except asyncio.CancelledError:
            raise
        except Exception:
            logger.exception("فشل تحميل غير متوقع")
            await users.record_download(job.user_id, _link_kind(link), False, "error")
            results.append(LinkResult(False, error=DownloadError("error"), seconds=time.monotonic() - started))

    quota, nudge = await quota_view(job.user_id, language)
    out_of_quota = any(r.error and r.error.code == "quota_exhausted" for r in results)
    if n == 1:
        r = results[0]
        if not r.ok:
            body = _error_text(language, r.error)
        else:
            body = text(language, "card_done", kind=_kind_label(language, r.info.kind, r.info.count),
                        size=human_size(r.info.size) if r.info.size else "—",
                        secs=human_seconds(r.seconds, language), quota=quota, nudge=nudge)
    else:
        lines = []
        for i, r in enumerate(results, 1):
            if r.ok:
                lines.append(text(language, "batch_line_ok", n=i, kind=_kind_label(language, r.info.kind, r.info.count),
                                  size=human_size(r.info.size)))
            else:
                lines.append(text(language, "batch_line_fail", n=i, reason=_error_text(language, r.error)
                                  .split("\n")[0]))
        ok = sum(1 for r in results if r.ok)
        body = text(language, "card_batch", ok=ok, failed=len(results) - ok, quota=quota,
                    lines="\n" + "\n".join(lines[:12]), nudge=nudge)
    markup = upgrade_keyboard(language) if (nudge or out_of_quota) else None
    if not await _edit(job, body, markup):
        try:
            await job.message.reply_text(body, reply_markup=markup)
        except Exception:
            logger.debug("تعذّر إرسال بطاقة النتيجة", exc_info=True)
