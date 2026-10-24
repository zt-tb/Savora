from __future__ import annotations

import asyncio
import logging
from contextlib import asynccontextmanager, suppress
from typing import Callable

logger = logging.getLogger(__name__)

INTERVAL = 2.5


class Progress:
    def __init__(self, render: Callable[[int, int | None], str]) -> None:
        self._render = render
        self.cur = 0
        self.total: int | None = None

    def callback(self, cur, total) -> None:
        self.cur = int(cur or 0)
        self.total = int(total) if total else None

    async def _ticker(self, status, interval: float) -> None:
        last = None
        while True:
            await asyncio.sleep(interval)
            snapshot = (self.cur, self.total)
            if snapshot == last or self.cur <= 0:
                continue
            last = snapshot
            try:
                await status.edit_text(self._render(self.cur, self.total))
            except Exception:
                logger.debug("تعذّر تحديث رسالة التقدّم", exc_info=True)

    @asynccontextmanager
    async def watching(self, status, interval: float = INTERVAL):
        task = asyncio.create_task(self._ticker(status, interval))
        try:
            yield self
        finally:
            task.cancel()
            with suppress(asyncio.CancelledError):
                await task
