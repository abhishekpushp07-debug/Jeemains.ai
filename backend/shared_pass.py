"""A value one pass makes for everybody (a board, a table of totals), kept in this process.

A quick pass is simply waited for when the copy is due, so a small crowd always sees fresh numbers. A slow pass (a big
crowd: thousands of rows to add up) runs in the background instead, while the copy already here keeps answering, so no
student's request waits for it. The copy is never older than `stale` times its normal keep."""
import asyncio
import logging
import time

QUICK = 0.02  # seconds: a pass faster than this is waited for
logger = logging.getLogger("jeelive")


class SharedPass:
    def __init__(self, load, keep, stale=4, size=64):
        self.load, self.keep, self.stale, self.size = load, keep, stale, size  # keep: seconds, or key -> seconds
        self.copies: dict = {}  # key -> (read_at, value)
        self.locks: dict = {}
        self.slow: set = set()
        self.tasks: dict = {}

    def lock(self, key) -> asyncio.Lock:
        return self.locks.setdefault(key, asyncio.Lock())

    def _keep(self, key) -> float:
        return self.keep(key) if callable(self.keep) else self.keep

    async def get(self, key):
        hit, keep = self.copies.get(key), self._keep(key)
        if hit and time.time() - hit[0] < keep:
            return hit[1]
        if hit and key in self.slow and time.time() - hit[0] < self.stale * keep:
            if key not in self.tasks:
                task = self.tasks[key] = asyncio.create_task(self._read(key))
                task.add_done_callback(lambda t: (self.tasks.pop(key, None), t.cancelled() or t.exception() and logger.error("shared pass failed: %r", t.exception())))
            return hit[1]
        return await self._read(key)

    async def _read(self, key):
        async with self.lock(key):
            hit = self.copies.get(key)
            if hit and time.time() - hit[0] < self._keep(key):
                return hit[1]
            began = time.monotonic()
            value = await self.load(key)
            (self.slow.add if time.monotonic() - began >= QUICK else self.slow.discard)(key)
            if len(self.copies) > self.size:
                self.copies.clear()
            self.copies[key] = (time.time(), value)
            return value
