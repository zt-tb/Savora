from __future__ import annotations

from .config import settings

PLAN_HOURS = {"d1": 24, "d7": 24 * 7, "d30": 24 * 30}


def plan_stars(plan: str) -> int:
    return {"d1": settings.vip_stars_d1, "d7": settings.vip_stars_d7, "d30": settings.vip_stars_d30}[plan]


def per_day_stars() -> int:
    return max(1, round(plan_stars("d30") / 30))
