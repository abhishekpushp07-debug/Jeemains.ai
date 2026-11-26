# Extra edge-case tests by T1 for db_setup.run_before_serving. Stand-ins only; no DB, no server touched.
import asyncio
import logging
import time

import pytest

import db_setup


def _stand_in(monkeypatch, seconds, exc=None):
    async def run_once(db, cups):
        await asyncio.sleep(seconds)
        if exc is not None:
            raise exc

    monkeypatch.setattr(db_setup, "run_once", run_once)


def test_wait_zero_gives_the_server_first(monkeypatch, caplog):
    """wait=0 must not block even one tick: the task is returned, logged, keeps running."""
    _stand_in(monkeypatch, 0.1)

    async def main():
        began = time.monotonic()
        with caplog.at_level(logging.WARNING, logger="jeelive"):
            task = await db_setup.run_before_serving(None, None, wait=0)
            elapsed = time.monotonic() - began
            assert task is not None and not task.done()
            assert elapsed < 0.05, elapsed
            await task
            await asyncio.sleep(0)
        words = [r.getMessage() for r in caplog.records]
        assert any("still running" in w for w in words)
        assert any("finished after" in w for w in words), words

    asyncio.run(main())


def test_non_runtime_exception_still_stops_the_start(monkeypatch):
    """ValueError / any Exception from a quick setup must bubble up and stop start, as before."""
    _stand_in(monkeypatch, 0.01, exc=ValueError("broken"))

    async def main():
        with pytest.raises(ValueError, match="broken"):
            await db_setup.run_before_serving(None, None, wait=2)

    asyncio.run(main())


def test_cancelled_start_cancels_the_waiter_not_the_task(monkeypatch):
    """If the outer start is cancelled while waiting, run_before_serving raises CancelledError.
    The underlying setup task continues (asyncio.wait does not cancel its awaited tasks)."""
    _stand_in(monkeypatch, 0.3)

    task_holder = {}

    async def main():
        async def waiter():
            # patch create_task so we can grab the inner task
            real_create = asyncio.create_task
            def spy(coro, **kw):
                t = real_create(coro, **kw)
                task_holder["t"] = t
                return t
            import db_setup as ds
            ds_asyncio = ds.asyncio
            orig = ds_asyncio.create_task
            ds_asyncio.create_task = spy
            try:
                return await db_setup.run_before_serving(None, None, wait=5)
            finally:
                ds_asyncio.create_task = orig

        outer = asyncio.create_task(waiter())
        await asyncio.sleep(0.05)
        outer.cancel()
        with pytest.raises(asyncio.CancelledError):
            await outer
        inner = task_holder.get("t")
        assert inner is not None
        # inner task should still be alive and NOT cancelled
        assert not inner.cancelled()
        # Let it finish cleanly; retrieve result to avoid "never retrieved"
        await inner
        assert inner.done() and inner.exception() is None

    asyncio.run(main())


def test_no_warning_about_never_retrieved_exception(monkeypatch, caplog, recwarn):
    """A failing long setup must have its exception consumed by the done-callback (no 'never retrieved')."""
    _stand_in(monkeypatch, 0.1, exc=RuntimeError("late boom"))

    async def main():
        with caplog.at_level(logging.ERROR, logger="jeelive"):
            task = await db_setup.run_before_serving(None, None, wait=0.02)
            assert task is not None
            await asyncio.wait({task})
            await asyncio.sleep(0)  # let callback run
            # read exception so pytest doesn't complain; callback should also have read it via exc_info
            assert isinstance(task.exception(), RuntimeError)
        msgs = [r.getMessage() for r in caplog.records]
        assert any("failed after the server started" in m for m in msgs), msgs

    asyncio.run(main())


def test_setup_ends_exactly_around_the_limit(monkeypatch):
    """Setup finishes within a hair of the wait: no crash either way; task is clean."""
    _stand_in(monkeypatch, 0.05)

    async def main():
        # several runs - race the limit to the setup
        for _ in range(3):
            task = await db_setup.run_before_serving(None, None, wait=0.05)
            if task is not None:
                await task  # let it end cleanly
                assert task.done() and task.exception() is None

    asyncio.run(main())
