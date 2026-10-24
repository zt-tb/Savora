from __future__ import annotations

import logging

from .db import Session
from .models import AppSetting

logger = logging.getLogger(__name__)

MAINTENANCE = "maintenance"
CAPTION_FOOTER = "caption_footer"
BLOCKED_WORDS = "blocked_words"
WELCOME_MEDIA = "welcome_media"

_cache: dict[str, str] = {}


async def load() -> None:
    from sqlalchemy import select

    try:
        async with Session() as s:
            rows = await s.scalars(select(AppSetting))
            _cache.clear()
            _cache.update({row.key: row.value for row in rows})
    except Exception:
        logger.exception("تعذّر تحميل الإعدادات — تُستخدم القيم الافتراضية")


def get(key: str, default: str = "") -> str:
    return _cache.get(key, default)


async def set_value(key: str, value: str) -> None:
    async with Session() as s:
        row = await s.get(AppSetting, key)
        if row is None:
            s.add(AppSetting(key=key, value=value))
        else:
            row.value = value
        await s.commit()
    _cache[key] = value


async def delete(key: str) -> None:
    async with Session() as s:
        row = await s.get(AppSetting, key)
        if row is not None:
            await s.delete(row)
            await s.commit()
    _cache.pop(key, None)


def maintenance_on() -> bool:
    return get(MAINTENANCE) == "1"


def blocked_words() -> list[str]:
    raw = get(BLOCKED_WORDS)
    if not raw or raw == "-":
        return []
    return [w.strip() for w in raw.split(",") if w.strip()]
