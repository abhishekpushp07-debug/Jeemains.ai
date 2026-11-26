# The start waits for the database setup, but never longer than its limit (db_setup.run_before_serving).
# No database and no server are used: run_once is replaced by a stand-in for each case.
import asyncio
import logging
import time

import pytest

import db_setup


def _stand_in(monkeypatch, seconds, fail=False):
    seen = {"ended": False}

    async def run_once(db, cups):
        await asyncio.sleep(seconds)
        if fail:
            raise RuntimeError("index build failed")
        seen["ended"] = True

    monkeypatch.setattr(db_setup, "run_once", run_once)
    return seen


def test_quick_setup_ends_before_the_server_answers(monkeypatch):
    seen = _stand_in(monkeypatch, 0.05)

    async def main():
        task = await db_setup.run_before_serving(None, None, wait=2)
        assert task is None and seen["ended"] is True  # exactly as before: setup first, then the server

    asyncio.run(main())


def test_quick_setup_that_fails_stops_the_start(monkeypatch):
    _stand_in(monkeypatch, 0.01, fail=True)

    async def main():
        with pytest.raises(RuntimeError, match="index build failed"):
            await db_setup.run_before_serving(None, None, wait=2)

    asyncio.run(main())


def test_long_setup_goes_on_while_the_server_answers(monkeypatch, caplog):
    seen = _stand_in(monkeypatch, 0.4)

    async def main():
        began = time.monotonic()
        with caplog.at_level(logging.WARNING, logger="jeelive"):
            task = await db_setup.run_before_serving(None, None, wait=0.05)
            waited = time.monotonic() - began
            assert task is not None and not task.done() and seen["ended"] is False
            assert waited < 0.3, waited  # the start did not wait for the whole setup
            await task  # the setup was not cut off: it runs to its end
            await asyncio.sleep(0)  # lets the task's "ended" note run
        assert seen["ended"] is True
        words = [r.getMessage() for r in caplog.records]
        assert any("still running" in w for w in words) and any("finished after" in w for w in words), words

    asyncio.run(main())


def test_long_setup_that_fails_is_logged_and_the_server_keeps_running(monkeypatch, caplog):
    _stand_in(monkeypatch, 0.2, fail=True)

    async def main():
        with caplog.at_level(logging.WARNING, logger="jeelive"):
            task = await db_setup.run_before_serving(None, None, wait=0.05)
            assert task is not None
            await asyncio.wait({task})
            await asyncio.sleep(0)
        assert isinstance(task.exception(), RuntimeError)  # read here, so nothing is left "never retrieved"
        assert any("failed after the server started" in r.getMessage() for r in caplog.records)

    asyncio.run(main())


def test_the_limit_is_the_same_as_for_a_copy_that_waits():
    assert db_setup.SETUP_WAIT == 30
