import asyncio
import unittest

from tests import _stubs  # noqa: F401

from app.download_queue import DownloadQueue, Job


def mkjob(q, user=1, vip=False):
    return Job(id=q.next_id(), user_id=user, language="ar", vip=vip, links=[1], message=None, status=None)


class TestQueue(unittest.TestCase):
    def test_vip_jumps_ahead_and_positions_refresh(self):
        async def go():
            q = DownloadQueue()
            gate, started, positions = asyncio.Event(), [], []

            async def processor(job):
                started.append(job.id)
                await gate.wait()
                await asyncio.sleep(0.01)

            async def on_pos(job, pos, total):
                positions.append((job.id, pos, total))
                job.shown_pos = pos

            await q.start(processor, on_pos, workers=1)
            busy = mkjob(q)
            await q.submit(busy)
            await asyncio.sleep(0.02)
            free1, free2 = mkjob(q, user=2), mkjob(q, user=3)
            vip = mkjob(q, user=4, vip=True)
            await q.submit(free1)
            await q.submit(free2)
            pos, total, waits = await q.submit(vip)
            self.assertEqual((pos, total, waits), (1, 3, True))
            self.assertEqual([q.position(j) for j in (vip, free1, free2)], [1, 2, 3])
            gate.set()
            await asyncio.sleep(0.1)
            self.assertEqual(started, [busy.id, vip.id, free1.id, free2.id])
            await q.stop()
            self.assertTrue(positions)
        asyncio.run(go())

    def test_idle_worker_means_no_wait(self):
        async def go():
            q = DownloadQueue()

            async def processor(job):
                pass

            await q.start(processor, None, workers=2)
            await asyncio.sleep(0.02)
            _pos, _total, waits = await q.submit(mkjob(q))
            self.assertFalse(waits)
            await q.stop()
        asyncio.run(go())

    def test_cancel_only_pending_and_only_owner(self):
        async def go():
            q = DownloadQueue()
            gate = asyncio.Event()

            async def processor(job):
                await gate.wait()

            await q.start(processor, None, workers=1)
            running, pending = mkjob(q, user=1), mkjob(q, user=2)
            await q.submit(running)
            await asyncio.sleep(0.02)
            await q.submit(pending)
            self.assertIsNone(q.cancel(running.id, 1))
            self.assertIsNone(q.cancel(pending.id, 999))
            self.assertIs(q.cancel(pending.id, 2), pending)
            self.assertEqual(q.size(), 0)
            gate.set()
            await q.stop()
        asyncio.run(go())

    def test_pending_for_counts_pending_and_running(self):
        async def go():
            q = DownloadQueue()
            gate = asyncio.Event()

            async def processor(job):
                await gate.wait()

            await q.start(processor, None, workers=1)
            for _ in range(3):
                await q.submit(mkjob(q, user=7))
            await asyncio.sleep(0.02)
            self.assertEqual(q.pending_for(7), 3)
            self.assertEqual(q.pending_for(8), 0)
            self.assertEqual((q.running(), q.size()), (1, 2))
            gate.set()
            await q.stop()
        asyncio.run(go())

    def test_processor_crash_does_not_kill_worker(self):
        async def go():
            q = DownloadQueue()
            done = []

            async def processor(job):
                if job.user_id == 1:
                    raise RuntimeError("boom")
                done.append(job.id)

            await q.start(processor, None, workers=1)
            await q.submit(mkjob(q, user=1))
            ok = mkjob(q, user=2)
            await q.submit(ok)
            await asyncio.sleep(0.1)
            self.assertEqual(done, [ok.id])
            await q.stop()
        asyncio.run(go())


if __name__ == "__main__":
    unittest.main()
