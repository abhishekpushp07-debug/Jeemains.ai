"""Work nobody waits for (Phase 3, Level 5): a friend-feed row, a session's once-a-day touch.

It runs right after the answer has gone out instead of before it. Coins, answers and rewards are never put here: they
are always written before the answer. Bounded: when too much is already waiting, the work simply runs in place."""
import asyncio
import logging

MAX_PENDING = 2000
logger = logging.getLogger("jeelive")
_pending: set = set()


def _done(task: asyncio.Task):
    _pending.discard(task)
    if not task.cancelled() and task.exception():
        logger.warning("background work failed: %r", task.exception())


async def later(coro):
    if len(_pending) >= MAX_PENDING:
        await coro
        return
    task = asyncio.create_task(coro)
    _pending.add(task)
    task.add_done_callback(_done)


def pending() -> int:
    return len(_pending)


async def drain(timeout: float = 5.0):
    """At shutdown: let what is waiting finish (a few seconds at most)."""
    if _pending:
        await asyncio.wait(list(_pending), timeout=timeout)
