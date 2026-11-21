"""Crowd control must tell a crowd from a hiccup.

One late wake-up of the event loop (a long report being built, the container being paused for a moment) is not a packed
arena: students opening a match right after it must get in, not wait 5-7 seconds. A loop that stays late closes the doors
within about half a second and opens them again once it is calm. Runs in this process only (no server, no database).
"""
import asyncio
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import load_guard  # noqa: E402


def watched(steps):
    """Runs `steps` next to the real monitor on a fresh event loop and always puts the shared numbers back."""
    async def run():
        task = asyncio.create_task(load_guard.monitor())
        try:
            await asyncio.sleep(0.45)  # two calm samples first
            await steps()
        finally:
            task.cancel()
    try:
        asyncio.run(run())
    finally:
        load_guard.load.lag = 0.0
        load_guard.load.sustained = 0.0


def test_one_stall_is_not_a_crowd():
    async def steps():
        assert not load_guard.busy()
        time.sleep(0.9)  # the loop is stuck once, far longer than the limit
        await asyncio.sleep(0.05)  # the monitor wakes up late and reports it
        assert load_guard.load.lag > load_guard.LAG_LIMIT, "the stall itself must still be measured and reported"
        assert load_guard.snapshot()["lag_ms"] > load_guard.LAG_LIMIT * 1000
        assert not load_guard.busy(), "one stall turned new matches away"
        load_guard.arena_gate()  # the door itself: must not raise
        await asyncio.sleep(0.45)
        assert not load_guard.busy()
    watched(steps)


def test_a_loop_that_stays_late_closes_the_doors_and_reopens():
    async def steps():
        turned_away = load_guard.load.turned_away
        for _ in range(3):  # late again and again: this is a packed server
            time.sleep(0.5)
            await asyncio.sleep(0.05)
        assert load_guard.busy(), "a loop that stays late must make new matches wait"
        assert load_guard.snapshot()["busy"] is True and load_guard.snapshot()["lag_sustained_ms"] > load_guard.LAG_LIMIT * 1000
        try:
            load_guard.arena_gate()
            raise AssertionError("the door stayed open on a packed server")
        except load_guard.ArenaBusy:
            assert load_guard.load.turned_away == turned_away + 1
        await asyncio.sleep(0.7)  # calm again: three on-time samples
        assert not load_guard.busy(), "the doors stayed closed after the crowd had gone"
    watched(steps)
    load_guard.load.turned_away = 0


def test_two_stalls_far_apart_are_still_not_a_crowd():
    async def steps():
        for _ in range(2):
            time.sleep(0.6)
            await asyncio.sleep(0.05)
            assert not load_guard.busy()
            await asyncio.sleep(0.65)  # three calm samples in between
            assert not load_guard.busy()
    watched(steps)
