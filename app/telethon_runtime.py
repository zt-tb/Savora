import asyncio
import logging

from telethon import TelegramClient
from telethon.sessions import StringSession

from .config import settings
from .downloader import SESSION_DEAD_ERRORS
from .session_vault import load_session

logger = logging.getLogger(__name__)

_client: TelegramClient | None = None
_lock = asyncio.Lock()
_boot_problem: str | None = None
HEALTH_TIMEOUT_SECONDS = 25


def _new_client(session_string: str) -> TelegramClient:
    return TelegramClient(StringSession(session_string), settings.api_id, settings.api_hash)


async def get_client() -> TelegramClient | None:
    return _client


async def is_ready() -> bool:
    return _client is not None and _client.is_connected() and await _client.is_user_authorized()


async def bootstrap() -> None:
    global _client, _boot_problem
    session_string = await load_session() or settings.downloader_session
    if not session_string:
        _boot_problem = None
        logger.warning("⚠️ ما فيه جلسة محفوظة بعد — التحميل معطّل لحد تسجيل الدخول من لوحة التحكم.")
        return
    client = _new_client(session_string)
    try:
        await client.connect()
        if not await client.is_user_authorized():
            logger.error("❌ الجلسة المحفوظة لم تعد صالحة (سُحبت/انتهت) — سجّل دخول من جديد.")
            await client.disconnect()
            _boot_problem = "unauthorized"
            return
    except SESSION_DEAD_ERRORS:
        logger.error("❌ الجلسة المحفوظة انسحبت أو استُخدمت من مكانين — سجّل دخول من جديد.")
        _boot_problem = "unauthorized"
        return
    except Exception:
        logger.exception("فشل الاتصال بحساب التحميل عند الإقلاع")
        _boot_problem = "disconnected"
        return
    async with _lock:
        _client = client
    _boot_problem = None
    me = await client.get_me()
    logger.info("✅ حساب التحميل متصل: %s (id=%s)", me.first_name, me.id)


async def health() -> str:
    client = _client
    if client is None:
        if _boot_problem == "disconnected":
            await bootstrap()
        return "ok" if _client is not None else (_boot_problem or "none")
    try:
        if not client.is_connected():
            await asyncio.wait_for(client.connect(), HEALTH_TIMEOUT_SECONDS)
        await asyncio.wait_for(client.get_me(), HEALTH_TIMEOUT_SECONDS)
        return "ok"
    except SESSION_DEAD_ERRORS:
        return "unauthorized"
    except Exception:
        logger.warning("فحص صحة حساب التحميل فشل", exc_info=True)
        return "disconnected"


async def swap(session_string: str) -> tuple[bool, str]:
    global _client, _boot_problem
    candidate = _new_client(session_string)
    try:
        await candidate.connect()
        if not await candidate.is_user_authorized():
            await candidate.disconnect()
            return False, "الجلسة غير مصرّح بها"
        me = await candidate.get_me()
    except Exception as exc:
        try:
            await candidate.disconnect()
        except Exception:
            pass
        return False, str(exc)[:120]

    async with _lock:
        old, _client = _client, candidate
    _boot_problem = None
    if old is not None:
        try:
            await old.disconnect()
        except Exception:
            logger.exception("تعذّر قطع اتصال الحساب القديم (غير خطير)")
    return True, (me.first_name or str(me.id))


async def shutdown() -> None:
    global _client, _boot_problem
    _boot_problem = None
    async with _lock:
        client, _client = _client, None
    if client is not None:
        try:
            await client.disconnect()
        except Exception:
            pass
