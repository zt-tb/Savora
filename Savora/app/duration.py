from __future__ import annotations

import re

HOURS_PER = {"hour": 1, "day": 24, "week": 24 * 7, "month": 24 * 30, "year": 24 * 365}
MAX_HOURS = 24 * 365 * 10

_DIGITS = str.maketrans("٠١٢٣٤٥٦٧٨٩۰۱۲۳۴۵۶۷۸۹٫،", "01234567890123456789.,")
_UNITS = {
    "hour": {"h", "hr", "hrs", "hour", "hours", "ساعه", "ساعات"},
    "day": {"d", "day", "days", "يوم", "ايام"},
    "week": {"w", "week", "weeks", "اسبوع", "اسابيع"},
    "month": {"m", "mo", "month", "months", "شهر", "اشهر", "شهور"},
    "year": {"y", "yr", "year", "years", "سنه", "سنين", "سنوات"},
}
_DUAL = {"ساعتين": "hour", "يومين": "day", "اسبوعين": "week", "شهرين": "month", "سنتين": "year"}
_LOOKUP = {word: unit for unit, words in _UNITS.items() for word in words}
_RE = re.compile(r"^(\d+(?:\.\d+)?)?\s*([^\d\s.]+)?$")


def _normalize_word(word: str) -> str:
    word = word.lower()
    for a, b in (("أ", "ا"), ("إ", "ا"), ("آ", "ا"), ("ة", "ه"), ("ى", "ي")):
        word = word.replace(a, b)
    if word.startswith("ال") and len(word) > 3:
        word = word[2:]
    return word


def parse_hours(raw: str) -> int | None:
    cleaned = (raw or "").translate(_DIGITS).replace(",", ".").strip()
    match = _RE.match(cleaned)
    if not match or not (match.group(1) or match.group(2)):
        return None
    number = float(match.group(1)) if match.group(1) else None
    word = _normalize_word(match.group(2)) if match.group(2) else None
    if word is None:
        unit, count = "day", number
    elif word in _DUAL:
        unit, count = _DUAL[word], number if number is not None else 2
    elif word in _LOOKUP:
        unit, count = _LOOKUP[word], number if number is not None else 1
    else:
        return None
    hours = round(count * HOURS_PER[unit])
    return hours if 1 <= hours <= MAX_HOURS else None
