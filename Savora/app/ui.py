from __future__ import annotations

import html
import re
from datetime import timedelta

from . import emoji_ids as E
from .config import settings

EMOJI: dict[str, tuple[str, str]] = {
    "search": (E.SEARCH, "🔍"),
    "eye": (E.EYE, "👁"),
    "person": (E.PERSON, "👤"),
    "calendar": (E.CALENDAR, "🗓"),
    "clock": (E.CLOCK, "⏰"),
    "warning": (E.WARNING, "⚠️"),
    "medal": (E.MEDAL, "🎖"),
    "robot": (E.ROBOT, "🤖"),
    "skull": (E.SKULL, "☠️"),
    "trophy": (E.TROPHY, "🏆"),
    "heart": (E.HEART, "♥️"),
    "zap": (E.ZAP, "⚡️"),
    "thought": (E.THOUGHT, "💭"),
    "mail": (E.MAIL, "✉️"),
    "bin": (E.BIN, "🗑"),
    "forbidden": (E.FORBIDDEN, "🚫"),
    "plus": (E.PLUS, "➕"),
    "shield": (E.SHIELD, "🛡"),
    "comet": (E.COMET, "☄️"),
    "iraq": (E.IRAQ, "🇮🇶"),
    "key": (E.KEY, "🔑"),
    "spider": (E.SPIDER, "🕷"),
    "laugh": (E.LAUGH, "🤣"),
    "music": (E.MUSIC, "🎶"),
    "hacker": (E.HACKER, "🧑‍💻"),
}

_TAG_RE = re.compile(r'<tg-emoji emoji-id="\d+">(.*?)</tg-emoji>', re.S)
_animated = bool(settings.animated_emoji)


def em(name: str) -> str:
    emoji_id, fallback = EMOJI[name]
    return f'<tg-emoji emoji-id="{emoji_id}">{fallback}</tg-emoji>'


def render(s: str) -> str:
    return s if _animated else _TAG_RE.sub(r"\1", s)


def animated_enabled() -> bool:
    return _animated


def set_animated(value: bool) -> None:
    global _animated
    _animated = bool(value)


def esc(value) -> str:
    return html.escape(str(value), quote=False)


LINE = "━━━━━━━━━━━━━━"


def bar(percent: float, width: int = 10) -> str:
    percent = max(0.0, min(100.0, float(percent)))
    filled = int(round(width * percent / 100))
    return "▰" * filled + "▱" * (width - filled)


def human_size(n: float | int | None) -> str:
    if n is None:
        return "—"
    n = float(n)
    for unit in ("B", "KB", "MB", "GB"):
        if n < 1024 or unit == "GB":
            return f"{n:.0f} {unit}" if unit == "B" else f"{n:.1f} {unit}"
        n /= 1024
    return f"{n:.1f} GB"


_UNITS = {
    "ar": {"s": "ث", "m": "د", "h": "س", "d": "يوم"},
    "en": {"s": "s", "m": "m", "h": "h", "d": "d"},
}


def human_seconds(seconds: float, language: str = "ar") -> str:
    u = _UNITS.get(language, _UNITS["ar"])
    seconds = max(0.0, float(seconds))
    if seconds < 60:
        return f"{seconds:.1f} {u['s']}"
    minutes, sec = divmod(int(seconds), 60)
    return f"{minutes} {u['m']} {sec} {u['s']}"


def human_delta(delta: timedelta, language: str = "ar") -> str:
    u = _UNITS.get(language, _UNITS["ar"])
    total = max(0, int(delta.total_seconds()))
    days, rest = divmod(total, 86400)
    hours, rest = divmod(rest, 3600)
    minutes = rest // 60
    parts = []
    if days:
        parts.append(f"{days} {u['d']}")
    if hours:
        parts.append(f"{hours} {u['h']}")
    if not days and minutes:
        parts.append(f"{minutes} {u['m']}")
    return " ".join(parts) or f"1 {u['m']}"
