from __future__ import annotations

import logging
import time

from . import telethon_runtime, users
from .config import settings
from .texts import text

logger = logging.getLogger(__name__)

CHECK_INTERVAL_SECONDS = 300
ALERT_REPEAT_SECONDS = 6 * 3600
DEAD_ALERT_COOLDOWN_SECONDS = 600

_state: dict = {"status": None, "alerted_at": 0.0}


async def _owner_language() -> str:
    try:
        return await users.get_language(settings.admin_id)
    except Exception:
        return "ar"


async def _notify(bot, key: str, **kwargs) -> bool:
    language = await _owner_language()
    try:
        await bot.send_message(settings.admin_id, text(language, key, **kwargs))
        return True
    except Exception:
        logger.warning("تعذّر إرسال تنبيه المراقبة للمالك", exc_info=True)
        return False


async def run_check(bot) -> str:
    status = await telethon_runtime.health()
    previous, _state["status"] = _state["status"], status
    now = time.time()

    if status == "ok":
        if previous in ("unauthorized", "disconnected"):
            await _notify(bot, "alert_recovered")
        _state["alerted_at"] = 0.0
        return status
    if status == "none":
        return status

    reason = text(await _owner_language(), f"reason_{status}")
    if previous not in ("unauthorized", "disconnected"):
        if await _notify(bot, "alert_offline", reason=reason):
            _state["alerted_at"] = now
    elif now - _state["alerted_at"] > ALERT_REPEAT_SECONDS:
        if await _notify(bot, "alert_still_offline", reason=reason):
            _state["alerted_at"] = now
    return status


async def health_job(context) -> None:
    try:
        await run_check(context.bot)
    except Exception:
        logger.exception("فشل فحص صحة حساب التحميل")


async def report_session_dead(bot) -> None:
    now = time.time()
    if _state["alerted_at"] and now - _state["alerted_at"] < DEAD_ALERT_COOLDOWN_SECONDS:
        return
    if await _notify(bot, "alert_session_dead"):
        _state["alerted_at"] = now
        _state["status"] = "unauthorized"


def reset() -> None:
    _state.update({"status": None, "alerted_at": 0.0})
