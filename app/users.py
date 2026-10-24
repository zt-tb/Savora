from __future__ import annotations

from datetime import datetime, timedelta, timezone

from sqlalchemy import func, select

from .db import Session
from .models import DownloadLog, Payment, User

FREE_LIMIT = 2
COOLDOWN = timedelta(days=2)
FREE_BATCH_LIMIT = 2
VIP_BATCH_LIMIT = 10


def batch_limit(vip: bool) -> int:
    return VIP_BATCH_LIMIT if vip else FREE_BATCH_LIMIT


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _window(row: User, now: datetime) -> tuple[int, datetime | None]:
    if row.locked_until is not None and row.locked_until <= now:
        return 0, None
    return row.free_used, row.locked_until


def _is_vip_row(row: User | None, now: datetime) -> bool:
    return bool(row and row.vip_until and row.vip_until > now)


async def get_or_create(user_id: int, full_name: str = "", username: str | None = None) -> User:
    async with Session() as s:
        row = await s.scalar(select(User).where(User.user_id == user_id))
        if row is None:
            row = User(user_id=user_id, full_name=full_name or str(user_id), username=username)
            s.add(row)
            await s.commit()
            await s.refresh(row)
            return row
        changed = False
        if full_name and row.full_name != full_name:
            row.full_name, changed = full_name, True
        if username != row.username:
            row.username, changed = username, True
        if changed:
            await s.commit()
            await s.refresh(row)
        return row


async def set_language(user_id: int, language: str) -> None:
    async with Session() as s:
        row = await s.scalar(select(User).where(User.user_id == user_id))
        if row is not None:
            row.language = language
            await s.commit()


async def exists(user_id: int) -> bool:
    async with Session() as s:
        return await s.scalar(select(User.id).where(User.user_id == user_id)) is not None


async def get_language(user_id: int) -> str:
    async with Session() as s:
        row = await s.scalar(select(User).where(User.user_id == user_id))
    return row.language if row else "ar"


async def is_banned(user_id: int) -> bool:
    async with Session() as s:
        row = await s.scalar(select(User).where(User.user_id == user_id))
    return bool(row and row.is_banned)


async def is_vip(user_id: int) -> bool:
    async with Session() as s:
        row = await s.scalar(select(User).where(User.user_id == user_id))
    return bool(row and row.vip_until and row.vip_until > datetime.now(timezone.utc))


async def grant_vip(user_id: int, hours: int = 24) -> bool:
    async with Session() as s:
        row = await s.scalar(select(User).where(User.user_id == user_id))
        if row is None:
            return False
        base = row.vip_until if (row.vip_until and row.vip_until > datetime.now(timezone.utc)) else datetime.now(timezone.utc)
        row.vip_until = base + timedelta(hours=hours)
        await s.commit()
    return True


async def revoke_vip(user_id: int) -> bool:
    async with Session() as s:
        row = await s.scalar(select(User).where(User.user_id == user_id))
        if row is None:
            return False
        row.vip_until = None
        await s.commit()
    return True


async def set_banned(user_id: int, banned: bool) -> bool:
    async with Session() as s:
        row = await s.scalar(select(User).where(User.user_id == user_id))
        if row is None:
            return False
        row.is_banned = banned
        await s.commit()
    return True


async def can_download(user_id: int) -> bool:
    now = _now()
    async with Session() as s:
        row = await s.scalar(select(User).where(User.user_id == user_id))
    if row is None:
        return False
    if _is_vip_row(row, now):
        return True
    return _window(row, now)[0] < FREE_LIMIT


async def quota_left(user_id: int) -> int | None:
    now = _now()
    async with Session() as s:
        row = await s.scalar(select(User).where(User.user_id == user_id))
    if _is_vip_row(row, now):
        return None
    return max(0, FREE_LIMIT - (_window(row, now)[0] if row else 0))


async def wait_remaining(user_id: int) -> timedelta | None:
    now = _now()
    async with Session() as s:
        row = await s.scalar(select(User).where(User.user_id == user_id))
    if row is None or _is_vip_row(row, now):
        return None
    used, locked = _window(row, now)
    return (locked - now) if (used >= FREE_LIMIT and locked is not None) else None


async def vip_remaining(user_id: int) -> timedelta | None:
    now = _now()
    async with Session() as s:
        row = await s.scalar(select(User).where(User.user_id == user_id))
    if _is_vip_row(row, now):
        return row.vip_until - now
    return None


async def record_download(user_id: int, kind: str, ok: bool, error: str | None = None) -> None:
    now = _now()
    async with Session() as s:
        row = await s.scalar(select(User).where(User.user_id == user_id))
        if row is not None and ok:
            row.downloads_count += 1
            if not _is_vip_row(row, now):
                used = _window(row, now)[0] + 1
                row.free_used = used
                row.locked_until = now + COOLDOWN if used >= FREE_LIMIT else None
        s.add(DownloadLog(user_id=user_id, kind=kind, ok=ok, error=None if ok else (error or "error")[:40]))
        await s.commit()


async def stats() -> dict:
    now = datetime.now(timezone.utc)
    day_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    async with Session() as s:
        total_users = await s.scalar(select(func.count(User.id))) or 0
        vip_now = await s.scalar(select(func.count(User.id)).where(User.vip_until > now)) or 0
        banned = await s.scalar(select(func.count(User.id)).where(User.is_banned.is_(True))) or 0
        today_ok = await s.scalar(select(func.count(DownloadLog.id)).where(
            DownloadLog.created_at >= day_start, DownloadLog.ok.is_(True))) or 0
        today_failed = await s.scalar(select(func.count(DownloadLog.id)).where(
            DownloadLog.created_at >= day_start, DownloadLog.ok.is_(False))) or 0
        total_ok = await s.scalar(select(func.count(DownloadLog.id)).where(DownloadLog.ok.is_(True))) or 0
        total_all = await s.scalar(select(func.count(DownloadLog.id))) or 0
        top_rows = (await s.execute(
            select(User.full_name, User.user_id, User.downloads_count)
            .where(User.downloads_count > 0).order_by(User.downloads_count.desc()).limit(5))).all()
        reason_rows = (await s.execute(
            select(DownloadLog.error, func.count(DownloadLog.id))
            .where(DownloadLog.ok.is_(False), DownloadLog.error.is_not(None))
            .group_by(DownloadLog.error).order_by(func.count(DownloadLog.id).desc()).limit(5))).all()
        pay_row = (await s.execute(
            select(func.coalesce(func.sum(Payment.stars), 0), func.count(Payment.id)))).one()
    return {
        "users": total_users, "vip": vip_now, "banned": banned,
        "today_ok": today_ok, "today_failed": today_failed, "today": today_ok + today_failed,
        "total": total_all, "total_ok": total_ok,
        "rate": round(total_ok * 100 / total_all) if total_all else 0,
        "top": [(r[0], r[1], r[2]) for r in top_rows],
        "reasons": [(r[0], r[1]) for r in reason_rows],
        "stars": int(pay_row[0] or 0), "sales": int(pay_row[1] or 0),
    }


async def all_user_ids() -> list[int]:
    async with Session() as s:
        rows = await s.scalars(select(User.user_id).where(User.is_banned.is_(False)))
    return list(rows)
