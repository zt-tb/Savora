import logging

from cryptography.fernet import Fernet, InvalidToken

from .config import settings
from .db import Session as DbSession
from .db import redis
from .models import SessionVault

logger = logging.getLogger(__name__)

_fernet = Fernet(settings.session_encryption_key.encode() if isinstance(settings.session_encryption_key, str)
                 else settings.session_encryption_key)

BLOB_ROW_ID = 1
CACHE_KEY = "ts:session_vault:blob"
CANDIDATE_KEY = "ts:session_vault:candidate"
CANDIDATE_TTL = 300


class VaultDecryptError(Exception):
    pass


def seal(session_string: str) -> str:
    return _fernet.encrypt(session_string.encode()).decode()


def unseal(blob: str) -> str:
    try:
        return _fernet.decrypt(blob.encode()).decode()
    except InvalidToken as exc:
        raise VaultDecryptError("تعذّر فك تشفير الجلسة المخزّنة") from exc


async def put_candidate(session_string: str, meta: dict) -> None:
    import json

    payload = json.dumps({"blob": seal(session_string), "meta": meta})
    await redis.set(CANDIDATE_KEY, payload, ex=CANDIDATE_TTL)


async def take_candidate() -> tuple[str, dict] | None:
    import json

    raw = await redis.get(CANDIDATE_KEY)
    if not raw:
        return None
    await redis.delete(CANDIDATE_KEY)
    data = json.loads(raw)
    return unseal(data["blob"]), data.get("meta", {})


async def drop_candidate() -> None:
    await redis.delete(CANDIDATE_KEY)


async def save_session(session_string: str) -> None:
    blob = seal(session_string)
    async with DbSession() as db:
        row = await db.get(SessionVault, BLOB_ROW_ID)
        if row is None:
            row = SessionVault(id=BLOB_ROW_ID, blob=blob)
            db.add(row)
        else:
            row.blob = blob
        await db.commit()
    try:
        await redis.set(CACHE_KEY, blob)
    except Exception:
        logger.exception("تعذّر تحديث كاش الجلسة بـ Redis (محفوظة بـ Postgres على أي حال)")


async def load_session() -> str | None:
    try:
        cached = await redis.get(CACHE_KEY)
        if cached:
            return unseal(cached)
    except VaultDecryptError:
        logger.warning("جلسة Redis تالفة — نرجع لقراءة Postgres")
    except Exception:
        logger.exception("تعذّرت قراءة كاش الجلسة من Redis")

    async with DbSession() as db:
        row = await db.get(SessionVault, BLOB_ROW_ID)
    if row is None:
        return None
    session_string = unseal(row.blob)
    try:
        await redis.set(CACHE_KEY, row.blob)
    except Exception:
        pass
    return session_string


async def clear_session() -> None:
    async with DbSession() as db:
        row = await db.get(SessionVault, BLOB_ROW_ID)
        if row is not None:
            await db.delete(row)
            await db.commit()
    try:
        await redis.delete(CACHE_KEY)
    except Exception:
        pass
