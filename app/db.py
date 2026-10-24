import logging

from redis.asyncio import Redis
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from .config import settings
from .models import LEGACY_SHARE_CONSTRAINT, SHARE_PENDING_INDEX, Base

logger = logging.getLogger(__name__)


def _fix_db_url(raw_url: str) -> str:
    url = raw_url.strip().strip('"').strip("'")
    if url.startswith("postgres://"):
        url = "postgresql+asyncpg://" + url[len("postgres://"):]
    elif url.startswith("postgresql://"):
        url = "postgresql+asyncpg://" + url[len("postgresql://"):]
    elif not url.startswith("postgresql+asyncpg://"):
        raise ValueError(f"DATABASE_URL بصيغة غير معروفة: {url[:60]}")
    return url


engine = create_async_engine(_fix_db_url(settings.database_url), pool_pre_ping=True)
Session = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)

redis = Redis.from_url(settings.redis_url, decode_responses=True)


async def init_db() -> None:
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        await conn.execute(text(
            f"ALTER TABLE ts_share_requests DROP CONSTRAINT IF EXISTS {LEGACY_SHARE_CONSTRAINT}"))
        await conn.execute(text(
            f"CREATE UNIQUE INDEX IF NOT EXISTS {SHARE_PENDING_INDEX} "
            "ON ts_share_requests (user_id) WHERE status = 'pending'"))
        await conn.execute(text("ALTER TABLE ts_downloads ADD COLUMN IF NOT EXISTS error VARCHAR(40)"))
        await conn.execute(text(
            "DO $$ BEGIN IF EXISTS (SELECT 1 FROM information_schema.columns WHERE table_schema = current_schema() "
            "AND table_name = 'ts_users' AND column_name = 'downloads_today') THEN "
            "ALTER TABLE ts_users RENAME COLUMN downloads_today TO free_used; "
            "UPDATE ts_users SET free_used = 0; END IF; END $$"))
        await conn.execute(text("ALTER TABLE ts_users ADD COLUMN IF NOT EXISTS free_used INTEGER NOT NULL DEFAULT 0"))
        await conn.execute(text("ALTER TABLE ts_users ADD COLUMN IF NOT EXISTS locked_until TIMESTAMPTZ"))
        await conn.execute(text("ALTER TABLE ts_users DROP COLUMN IF EXISTS today_date"))
    try:
        await redis.ping()
    except Exception:
        logger.exception("تعذّر الاتصال بـ Redis عند الإقلاع")

