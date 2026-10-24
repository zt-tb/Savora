from __future__ import annotations

import asyncio
import itertools
import logging
import time
from dataclasses import dataclass, field
from typing import Any, Awaitable, Callable

logger = logging.getLogger(__name__)

MAX_QUEUE = 200
MAX_PENDING_PER_USER = 3
REFRESH_LIMIT = 20


@dataclass(eq=False)
class Job:
    id: int
    user_id: int
    language: str
    vip: bool
    links: list
    message: Any
    status: Any
    bot_username: str = ""
    created: float = field(default_factory=time.monotonic)
    shown_pos: int = 0

    @property
    def priority(self) -> int:
        return 0 if self.vip else 1


class DownloadQueue:
    def __init__(self) -> None:
        self._pending: list[Job] = []
        self._running: set[Job] = set()
        self._ids = itertools.count(1)
        self._cond: asyncio.Condition | None = None
        self._workers: list[asyncio.Task] = []
        self._worker_count = 0
        self._idle = 0
        self._processor: Callable[[Job], Awaitable[None]] | None = None
        self._on_position: Callable[[Job, int, int], Awaitable[None]] | None = None
        self._bg: set[asyncio.Task] = set()

    async def start(self, processor, on_position, workers: int = 2) -> None:
        if self._workers:
            return
        self._cond = asyncio.Condition()
        self._processor, self._on_position = processor, on_position
        self._worker_count = max(1, workers)
        self._workers = [asyncio.create_task(self._worker(), name=f"ts-dl-worker-{i}")
                         for i in range(self._worker_count)]

    async def stop(self) -> None:
        for task in self._workers + list(self._bg):
            task.cancel()
        for task in self._workers + list(self._bg):
            try:
                await task
            except (asyncio.CancelledError, Exception):
                pass
        self._workers, self._bg = [], set()

    def next_id(self) -> int:
        return next(self._ids)

    def size(self) -> int:
        return len(self._pending)

    def running(self) -> int:
        return len(self._running)

    def position(self, job: Job) -> int | None:
        try:
            return self._pending.index(job) + 1
        except ValueError:
            return None

    def links_for(self, user_id: int) -> int:
        return sum(len(j.links) for j in itertools.chain(self._pending, self._running) if j.user_id == user_id)

    def pending_for(self, user_id: int) -> int:
        return (sum(1 for j in self._pending if j.user_id == user_id)
                + sum(1 for j in self._running if j.user_id == user_id))

    async def submit(self, job: Job) -> tuple[int, int, bool]:
        assert self._cond is not None, "الطابور ما بدأ (start)"
        async with self._cond:
            self._pending.append(job)
            self._pending.sort(key=lambda j: (j.priority, j.id))
            pos, total = self._pending.index(job) + 1, len(self._pending)
            waits = total > self._idle
            self._cond.notify()
        return pos, total, waits

    def cancel(self, job_id: int, user_id: int) -> Job | None:
        for job in self._pending:
            if job.id == job_id and job.user_id == user_id:
                self._pending.remove(job)
                self._schedule_refresh()
                return job
        return None

    def _schedule_refresh(self) -> None:
        if self._on_position is None:
            return
        task = asyncio.create_task(self._refresh_positions())
        self._bg.add(task)
        task.add_done_callback(self._bg.discard)

    async def _refresh_positions(self) -> None:
        total = len(self._pending)
        for index, job in enumerate(list(self._pending[:REFRESH_LIMIT]), 1):
            if job.shown_pos != index:
                try:
                    await self._on_position(job, index, total)
                except Exception:
                    logger.debug("تعذّر تحديث ترتيب الطابور", exc_info=True)

    async def _worker(self) -> None:
        assert self._cond is not None and self._processor is not None
        while True:
            async with self._cond:
                self._idle += 1
                try:
                    while not self._pending:
                        await self._cond.wait()
                finally:
                    self._idle -= 1
                job = self._pending.pop(0)
                self._running.add(job)
            self._schedule_refresh()
            try:
                await self._processor(job)
            except asyncio.CancelledError:
                raise
            except Exception:
                logger.exception("فشل غير متوقع بمعالجة طلب %s", job.id)
            finally:
                self._running.discard(job)
