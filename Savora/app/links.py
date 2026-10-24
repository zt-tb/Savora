from __future__ import annotations

import re
from dataclasses import dataclass

from .downloader import ParsedLink, parse_link

_STRIP = "<>()[]{}\"'،,؛;.:!?…«»"


@dataclass
class Link:
    url: str
    parsed: ParsedLink


def extract_links(text: str, limit: int = 50) -> list[Link]:
    found: list[Link] = []
    seen: set[str] = set()
    for token in re.split(r"\s+", (text or "").strip()):
        token = token.strip(_STRIP)
        if not token or token in seen:
            continue
        parsed = parse_link(token)
        if parsed is None:
            continue
        seen.add(token)
        found.append(Link(token, parsed))
        if len(found) >= limit:
            break
    return found
