"""A phone that goes away while it is still sending a request (app closed, network dropped) is not a server error.

Before this guard every such request logged "Exception in ASGI application ... ClientDisconnect" and the server tried
to answer 500 to nobody. Real errors must still reach the error handler.
"""
import asyncio
import sys
from pathlib import Path

import pytest
from starlette.requests import ClientDisconnect, Request

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from load_guard import InflightCounter, load  # noqa: E402

SCOPE = {"type": "http", "method": "POST", "path": "/api/jl/attempts/x/answers", "headers": [], "query_string": b""}


async def gone():
    return {"type": "http.disconnect"}


def run(app, receive=gone):
    sent = []

    async def send(message):
        sent.append(message)

    asyncio.run(InflightCounter(app)(dict(SCOPE), receive, send))
    return sent


def test_disconnect_while_reading_the_body_is_swallowed():
    async def reads_body(scope, receive, send):
        await Request(scope, receive).body()  # what the website proxy does first

    before = load.inflight
    assert run(reads_body) == []  # nothing is answered: nobody is listening
    assert load.inflight == before  # and the request no longer counts as in flight


def test_disconnect_raised_deeper_in_the_app_is_swallowed():
    async def raises(scope, receive, send):
        raise ClientDisconnect()

    before = load.inflight
    assert run(raises) == []
    assert load.inflight == before


def test_real_errors_still_reach_the_error_handler():
    async def broken(scope, receive, send):
        raise RuntimeError("a real bug")

    before = load.inflight
    with pytest.raises(RuntimeError):
        run(broken)
    assert load.inflight == before


def test_a_normal_request_is_untouched():
    async def ok(scope, receive, send):
        await send({"type": "http.response.start", "status": 200, "headers": []})
        await send({"type": "http.response.body", "body": b"ok"})

    assert [m["type"] for m in run(ok)] == ["http.response.start", "http.response.body"]
