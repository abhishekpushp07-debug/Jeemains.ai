"""Bounded in-process cache, ONLY for explicitly public RF metadata (catalog, card pools).

No auth/authority, student information, answers, wallets or academic responses.
The source loader remains authoritative; errors/timeouts are never cached.
"""
import asyncio
from collections import Counter, OrderedDict
import json
import time

# The budget must hold every subject's card pool at once: when it was smaller than the pools of a PCM Mixed round, each
# new round pushed one pool out and read thousands of cards from the database again (tools/db_audit.py shows it).
BUDGET_BYTES, MAX_ENTRY_BYTES, MAX_ENTRIES, MAX_FLIGHTS = 24 * 1024 * 1024, 2 * 1024 * 1024, 64, 64


class MetadataCache:
    def __init__(self, *, disabled=False):
        self.disabled = disabled
        self.stats = Counter()
        self._l1, self._flights = OrderedDict(), {}
        self._bytes, self._epoch = 0, 0

    def _remember(self, key, value, raw, ttl):
        if len(raw) > MAX_ENTRY_BYTES:
            return
        if key in self._l1:
            self._bytes -= self._l1.pop(key)[2]
        weight = len(raw) * 3  # conservative JSON-to-object memory estimate
        self._l1[key] = (time.monotonic() + ttl, value, weight)
        self._bytes += weight
        while self._bytes > BUDGET_BYTES or len(self._l1) > MAX_ENTRIES:
            self._bytes -= self._l1.popitem(last=False)[1][2]

    async def get(self, key):
        entry = self._l1.get(key)
        if entry and entry[0] > time.monotonic():
            self._l1.move_to_end(key)
            self.stats['memory_hits'] += 1
            return entry[1], 'HIT-MEMORY'
        if entry:
            self._bytes -= self._l1.pop(key)[2]
        return None

    async def get_or_load(self, key, loader, ttl=60):
        if self.disabled:
            return await loader(), 'BYPASS'
        hit = await self.get(key)
        if hit is not None:
            return hit
        pending = self._flights.get(key)
        if pending:
            self.stats['coalesced'] += 1
            return (await asyncio.shield(pending))[0], 'COALESCED'
        if len(self._flights) >= MAX_FLIGHTS:
            return await loader(), 'BYPASS'
        task = asyncio.create_task(self._load(key, loader, ttl, self._epoch))
        self._flights[key] = task

        def release(done):
            if self._flights.get(key) is done:
                self._flights.pop(key, None)
            if not done.cancelled():
                done.exception()  # also consume a failed loader if all callers disconnected
        task.add_done_callback(release)
        return await asyncio.shield(task)

    async def _load(self, key, loader, ttl, epoch):
        value = await loader()  # never catch/cache source exceptions
        self.stats['source_loads'] += 1
        try:
            raw = json.dumps(value, ensure_ascii=False, separators=(',', ':')).encode()
        except (TypeError, ValueError):
            return value, 'BYPASS'
        if epoch == self._epoch and value is not None:
            self._remember(key, value, raw, ttl)
        return value, 'MISS'

    async def invalidate_prefix(self, prefix):
        self._epoch += 1
        for key in list(self._l1):
            if key.startswith(prefix):
                self._bytes -= self._l1.pop(key)[2]
        for key in list(self._flights):
            if key.startswith(prefix):
                self._flights.pop(key, None)

    async def close(self):
        self._l1.clear()


metadata_cache = MetadataCache()
