from __future__ import annotations

import math
import time
from contextlib import suppress
from collections import deque
from dataclasses import dataclass

from telegram import Update
from telegram.error import TelegramError
from telegram.ext import ApplicationHandlerStop, ContextTypes

from . import users
from .config import settings
from .texts import text

WINDOW_SECONDS = 5.0
MAX_ACTIONS = 8
BLOCK_SECONDS = 60
_PRUNE_AT = 5000

_hits: dict[int, deque[float]] = {}
_blocked_until: dict[int, float] = {}
_language: dict[int, str] = {}


@dataclass(frozen=True)
class Verdict:
    allowed: bool
    wait: int = 0
    announce: bool = False


def reset() -> None:
    _hits.clear()
    _blocked_until.clear()
    _language.clear()


def _prune(now: float) -> None:
    for uid in [u for u, until in _blocked_until.items() if until <= now]:
        _blocked_until.pop(uid, None)
        _language.pop(uid, None)
    for uid in [u for u, hits in _hits.items() if not hits or now - hits[-1] > WINDOW_SECONDS]:
        _hits.pop(uid, None)


def register(user_id: int, now: float | None = None) -> Verdict:
    now = time.monotonic() if now is None else now
    until = _blocked_until.get(user_id, 0.0)
    if until > now:
        return Verdict(False, math.ceil(until - now))
    if len(_hits) + len(_blocked_until) > _PRUNE_AT:
        _prune(now)
    hits = _hits.setdefault(user_id, deque())
    while hits and now - hits[0] > WINDOW_SECONDS:
        hits.popleft()
    hits.append(now)
    if len(hits) > MAX_ACTIONS:
        hits.clear()
        _blocked_until[user_id] = now + BLOCK_SECONDS
        return Verdict(False, BLOCK_SECONDS, announce=True)
    return Verdict(True)


def _is_payment(update: Update) -> bool:
    return bool(update.pre_checkout_query or (update.message and update.message.successful_payment))


async def guard(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user
    if user is None or user.id == settings.admin_id or _is_payment(update):
        return
    if update.message is None and update.callback_query is None:
        return
    verdict = register(user.id)
    if verdict.allowed:
        return
    if verdict.announce:
        _language[user.id] = await users.get_language(user.id)
    language = _language.get(user.id, "ar")
    with suppress(TelegramError):
        if update.callback_query is not None:
            await update.callback_query.answer(text(language, "spam_alert", verdict.wait))
        elif verdict.announce:
            await update.message.reply_text(text(language, "spam_blocked", verdict.wait))
    raise ApplicationHandlerStop
