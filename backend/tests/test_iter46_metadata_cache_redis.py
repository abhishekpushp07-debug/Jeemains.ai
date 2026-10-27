"""Iteration 46: Redis metadata cache behavior with isolated namespace keys.

Modules covered:
- MISS -> HIT-MEMORY -> HIT-REDIS path
- TTL/expiry and bad-json fail-open delete
- loader exception non-caching
- same-key concurrency coalescing
- invalidate_prefix scoped deletion only
"""

from __future__ import annotations

import asyncio
import time
import uuid
import sys
from pathlib import Path

import pytest

BACKEND_DIR = Path('/app/backend')
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from metadata_cache import MetadataCache


def _run(coro):
    return asyncio.run(coro)


async def _with_cache(assertions):
    ns = f"TEST-meta-iter46-{uuid.uuid4().hex[:10]}"
    cache = MetadataCache(namespace=ns)
    assert cache.redis is not None
    try:
        return await assertions(cache)
    finally:
        await cache.invalidate_prefix("")
        await cache.close()


def test_miss_memory_then_redis_after_l1_expiry():
    calls = {"n": 0}

    async def scenario(cache):
        async def loader():
            calls["n"] += 1
            return {"k": "v", "ts": time.time()}

        v1, s1 = await cache.get_or_load("k1", loader, ttl=15)
        assert s1 == "MISS"
        v2, s2 = await cache.get_or_load("k1", loader, ttl=15)
        assert s2 == "HIT-MEMORY"
        assert v1 == v2
        await asyncio.sleep(2.2)  # L1 is capped to <=2 seconds
        v3, s3 = await cache.get_or_load("k1", loader, ttl=15)
        assert s3 == "HIT-REDIS"
        assert v3 == v1

    _run(_with_cache(scenario))
    assert calls["n"] == 1


def test_ttl_expiry_removes_data():
    async def scenario(cache):
        async def loader():
            return {"once": True}

        _, state = await cache.get_or_load("ttl-k", loader, ttl=1)
        assert state == "MISS"
        await asyncio.sleep(1.2)
        hit = await cache.get("ttl-k")
        assert hit is None

    _run(_with_cache(scenario))


def test_bad_json_deleted_and_fails_open():
    async def scenario(cache):
        key = cache.prefix + "badjson"
        await cache.redis.set(key, b"{not-json", ex=15)
        hit = await cache.get("badjson")
        assert hit is None
        assert await cache.redis.exists(key) == 0

    _run(_with_cache(scenario))


def test_loader_exceptions_not_cached():
    calls = {"n": 0}

    async def scenario(cache):
        async def boom():
            calls["n"] += 1
            raise RuntimeError("source-failed")

        with pytest.raises(RuntimeError):
            await cache.get_or_load("err-k", boom, ttl=15)

        assert await cache.get("err-k") is None

        async def ok():
            calls["n"] += 1
            return {"ok": 1}

        value, state = await cache.get_or_load("err-k", ok, ttl=15)
        assert state == "MISS"
        assert value == {"ok": 1}

    _run(_with_cache(scenario))
    assert calls["n"] == 2


def test_same_key_concurrency_coalesces_loader_once():
    calls = {"n": 0}

    async def scenario(cache):
        gate = asyncio.Event()

        async def loader():
            calls["n"] += 1
            await gate.wait()
            return {"value": 42}

        async def one():
            return await cache.get_or_load("co-key", loader, ttl=15)

        tasks = [asyncio.create_task(one()) for _ in range(8)]
        await asyncio.sleep(0.05)
        gate.set()
        results = await asyncio.gather(*tasks)
        values = [v for v, _ in results]
        states = [s for _, s in results]
        assert all(v == {"value": 42} for v in values)
        assert "MISS" in states
        assert any(s in ("COALESCED", "HIT-MEMORY") for s in states)

    _run(_with_cache(scenario))
    assert calls["n"] == 1


def test_invalidate_prefix_scoped():
    async def scenario(cache):
        async def la():
            return {"v": "a"}

        async def lb():
            return {"v": "b"}

        await cache.get_or_load("a.one", la, ttl=30)
        await cache.get_or_load("b.one", lb, ttl=30)
        assert await cache.redis.exists(cache.prefix + "a.one") == 1
        assert await cache.redis.exists(cache.prefix + "b.one") == 1

        await cache.invalidate_prefix("a.")
        assert await cache.redis.exists(cache.prefix + "a.one") == 0
        assert await cache.redis.exists(cache.prefix + "b.one") == 1

    _run(_with_cache(scenario))
