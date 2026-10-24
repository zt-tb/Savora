import asyncio
import logging

from telethon import TelegramClient
from telethon.errors import (
    FloodWaitError,
    PasswordHashInvalidError,
    PhoneCodeExpiredError,
    PhoneCodeInvalidError,
    PhoneNumberInvalidError,
    SessionPasswordNeededError,
)
from telethon.sessions import StringSession

from . import session_vault
from .config import settings
from .db import redis

logger = logging.getLogger(__name__)

PHONE_TRIES_KEY = "ts:login:phone_tries"
QR_TRIES_KEY = "ts:login:qr_tries"
FAIL_KEY = "ts:login:fails"
RATE_WINDOW_SECONDS = 3600
MAX_PHONE_TRIES = 15
MAX_QR_TRIES = 15
MAX_FAILS = 15
QR_TIMEOUT_SECONDS = 30
ALL_RATE_KEYS = (PHONE_TRIES_KEY, QR_TRIES_KEY, FAIL_KEY)


async def clear_rate_limits() -> None:
    for key in ALL_RATE_KEYS:
        await redis.delete(key)


class LoginError(Exception):
    pass


class NeedsPassword(Exception):
    pass


def client_factory() -> TelegramClient:
    return TelegramClient(StringSession(), settings.api_id, settings.api_hash)


class LoginSession:

    def __init__(self, make_client=client_factory) -> None:
        self._make_client = make_client
        self.client: TelegramClient | None = None
        self.phone: str | None = None
        self._phone_code_hash: str | None = None
        self.qr = None

    async def _rate_check(self, key: str, limit: int) -> None:
        n = await redis.incr(key)
        if n == 1:
            await redis.expire(key, RATE_WINDOW_SECONDS)
        if n > limit:
            ttl = await redis.ttl(key)
            minutes = max(1, (ttl if ttl and ttl > 0 else RATE_WINDOW_SECONDS) // 60 + 1)
            raise LoginError(f"⚠️ محاولات كثيرة بوقت قصير — جرّب بعد {minutes} دقيقة تقريباً.")

    async def cancel(self) -> None:
        if self.client is not None:
            try:
                await self.client.disconnect()
            except Exception:
                pass
        self.client, self.phone, self._phone_code_hash, self.qr = None, None, None, None

    async def begin_phone(self, phone: str) -> None:
        await self._rate_check(PHONE_TRIES_KEY, MAX_PHONE_TRIES)
        await self.cancel()
        client = self._make_client()
        await client.connect()
        try:
            sent = await client.send_code_request(phone)
        except PhoneNumberInvalidError as exc:
            await client.disconnect()
            raise LoginError("⚠️ رقم الهاتف غير صحيح (اكتبه بصيغة دولية، مثل +9647xxxxxxxx).") from exc
        except FloodWaitError as exc:
            await client.disconnect()
            raise LoginError(f"⚠️ تيليجرام يطلب الانتظار {exc.seconds} ثانية قبل إعادة المحاولة.") from exc
        self.client, self.phone, self._phone_code_hash = client, phone, sent.phone_code_hash

    async def submit_code(self, code: str) -> str:
        if self.client is None or self.phone is None:
            raise LoginError("⚠️ ابدأ من جديد — ما فيه عملية دخول قائمة.")
        digits = "".join(ch for ch in code if ch.isdigit())
        if not digits:
            raise LoginError("⚠️ الكود أرقام فقط.")
        try:
            await self.client.sign_in(phone=self.phone, code=digits, phone_code_hash=self._phone_code_hash)
        except SessionPasswordNeededError:
            raise NeedsPassword from None
        except (PhoneCodeInvalidError, PhoneCodeExpiredError) as exc:
            await self._rate_check(FAIL_KEY, MAX_FAILS)
            raise LoginError("⚠️ الكود خطأ أو منتهي — اطلب كوداً جديداً.") from exc
        return "ok"

    async def submit_password(self, password: str) -> str:
        if self.client is None:
            raise LoginError("⚠️ ابدأ من جديد — ما فيه عملية دخول قائمة.")
        try:
            await self.client.sign_in(password=password)
        except PasswordHashInvalidError as exc:
            await self._rate_check(FAIL_KEY, MAX_FAILS)
            raise LoginError("⚠️ كلمة السر خطأ.") from exc
        return "ok"

    async def begin_qr(self) -> str:
        await self._rate_check(QR_TRIES_KEY, MAX_QR_TRIES)
        await self.cancel()
        client = self._make_client()
        await client.connect()
        self.client = client
        self.qr = await client.qr_login()
        return self.qr.url

    async def refresh_qr(self) -> str:
        if self.qr is None:
            return await self.begin_qr()
        await self.qr.recreate()
        return self.qr.url

    async def wait_qr(self, timeout: float = QR_TIMEOUT_SECONDS) -> str:
        if self.qr is None:
            raise LoginError("⚠️ ابدأ من جديد — ما فيه رمز QR نشط.")
        try:
            await self.qr.wait(timeout=timeout)
        except SessionPasswordNeededError:
            return "need_password"
        except asyncio.TimeoutError:
            return "expired"
        return "ok"

    async def finish(self) -> dict:
        if self.client is None:
            raise LoginError("⚠️ ابدأ من جديد.")
        me = await self.client.get_me()
        session_string = self.client.session.save()
        meta = {"id": me.id, "name": " ".join(x for x in (me.first_name, me.last_name) if x) or str(me.id),
                "username": me.username, "phone_tail": (me.phone or "")[-4:] if me.phone else None}
        await session_vault.put_candidate(session_string, meta)
        await self.cancel()
        return meta


login_session = LoginSession()
