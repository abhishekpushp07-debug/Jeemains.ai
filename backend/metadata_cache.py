"""Bounded optional Redis/L1 cache, ONLY for explicitly public RF metadata.

No auth/authority, student information, answers, wallets or academic responses.
The source loader remains authoritative; errors/timeouts are never cached.
"""
import asyncio
from collections import Counter, OrderedDict
import json
import os
from pathlib import Path
import secrets
import time

from dotenv import load_dotenv
import redis.asyncio as redis
from redis.asyncio.retry import Retry
from redis.backoff import NoBackoff
from redis.exceptions import RedisError

load_dotenv()
CONFIG = json.loads(Path(__file__).with_name('redis_runtime.json').read_text())
_RELEASE = "if redis.call('GET',KEYS[1]) == ARGV[1] then return redis.call('DEL',KEYS[1]) else return 0 end"


class MetadataCache:
    def __init__(self, *, namespace=None, disabled=False):
        self.prefix = (namespace or CONFIG['namespace']) + ':'
        self.disabled = disabled or os.environ.get('REDIS_DISABLED') == '1' or not CONFIG['enabled']
        self.stats = Counter()
        self._l1, self._flights = OrderedDict(), {}
        self._bytes, self._epoch, self._retry_at = 0, 0, 0.0
        options = dict(socket_connect_timeout=0.04, socket_timeout=0.04,
                       retry=Retry(NoBackoff(), 0), max_connections=20,
                       decode_responses=False, health_check_interval=30, protocol=2)
        url = os.environ.get('REDIS_URL')
        self.redis = None if self.disabled else (redis.from_url(url, **options) if url else
            redis.Redis(unix_socket_path=os.environ.get('REDIS_SOCKET_PATH', CONFIG['socket_path']), **options))

    async def _redis_call(self, method, *args, **kwargs):
        if self.redis is None or time.monotonic() < self._retry_at:
            return None
        try:
            return await asyncio.wait_for(getattr(self.redis, method)(*args, **kwargs), 0.075)
        except (RedisError, OSError, asyncio.TimeoutError):
            self.stats['redis_errors'] += 1
            self._retry_at = time.monotonic() + 5
            return None

    def _remember(self, key, value, raw, ttl, shared=True):
        if len(raw) > CONFIG['max_entry_bytes']:
            return
        if key in self._l1:
            self._bytes -= self._l1.pop(key)[2]
        # Conservative JSON-to-object memory estimate, bounded independently of Redis.
        weight = len(raw) * 3
        # With Redis up, memory only bridges 2 s (Redis is the shared copy). If Redis is down, memory keeps it up to 30 s so speed holds.
        self._l1[key] = (time.monotonic() + min(ttl, 2 if shared else 30), value, weight)
        self._bytes += weight
        while self._bytes > CONFIG['l1_budget_bytes'] or len(self._l1) > 64:
            self._bytes -= self._l1.popitem(last=False)[1][2]

    async def get(self, key):
        entry = self._l1.get(key)
        if entry and entry[0] > time.monotonic():
            self._l1.move_to_end(key)
            self.stats['memory_hits'] += 1
            return entry[1], 'HIT-MEMORY'
        if entry:
            self._bytes -= self._l1.pop(key)[2]
        raw = await self._redis_call('get', self.prefix + key)
        if raw:
            try:
                value = json.loads(raw)
                remaining = await self._redis_call('pttl', self.prefix + key)
                if remaining and remaining > 0:
                    self._remember(key, value, raw, remaining / 1000)
                self.stats['redis_hits'] += 1
                return value, 'HIT-REDIS'
            except (ValueError, TypeError):
                await self._redis_call('delete', self.prefix + key)
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
        if len(self._flights) >= 64:
            return await loader(), 'BYPASS'
        task = asyncio.create_task(self._load(key, loader, ttl, self._epoch))
        self._flights[key] = task
        def release(done):
            if self._flights.get(key) is done:
                self._flights.pop(key, None)
            if not done.cancelled():
                done.exception()  # also consume a failed loader if all callers disconnected
        task.add_done_callback(release)
        try:
            return await asyncio.shield(task)
        finally:
            if task.done() and self._flights.get(key) is task:
                self._flights.pop(key, None)

    async def _load(self, key, loader, ttl, epoch):
        lock, token = self.prefix + key + ':lock', secrets.token_hex(12)
        owned = await self._redis_call('set', lock, token, nx=True, px=3000)
        try:
            if owned is None and self.redis is not None and time.monotonic() >= self._retry_at:
                for _ in range(8):
                    await asyncio.sleep(0.025)
                    hit = await self.get(key)
                    if hit is not None:
                        return hit
            value = await loader()  # never catch/cache source exceptions
            self.stats['source_loads'] += 1
            try:
                raw = json.dumps(value, ensure_ascii=False, separators=(',', ':')).encode()
            except (TypeError, ValueError):
                return value, 'BYPASS'
            if epoch == self._epoch and value is not None and len(raw) <= CONFIG['max_entry_bytes']:
                stored = await self._redis_call('set', self.prefix + key, raw, ex=ttl)
                self._remember(key, value, raw, ttl, shared=bool(stored))
            return value, 'MISS' if self.redis and time.monotonic() >= self._retry_at else 'BYPASS'
        finally:
            if owned:
                await self._redis_call('eval', _RELEASE, 1, lock, token)

    async def invalidate_prefix(self, prefix):
        self._epoch += 1
        for key in list(self._l1):
            if key.startswith(prefix):
                self._bytes -= self._l1.pop(key)[2]
        for key in list(self._flights):
            if key.startswith(prefix):
                self._flights.pop(key, None)
        cursor = 0
        while True:
            result = await self._redis_call('scan', cursor=cursor, match=self.prefix + prefix + '*', count=100)
            if not result:
                break
            cursor, keys = result
            # Don't remove a different worker's token-owned locks.
            keys = [key for key in keys if not key.endswith(b':lock')]
            if keys:
                await self._redis_call('delete', *keys)
            if not cursor:
                break

    async def close(self):
        if self.redis:
            await self.redis.aclose()


metadata_cache = MetadataCache()