"""Wrong-PIN limit (login_guard.py), tested on the guard itself so no sign-in reaches the real website.
Uses only TEST hashes in the preview database and removes them afterwards."""
import asyncio
import json
import os
import secrets

import pytest
from motor.motor_asyncio import AsyncIOMotorClient
from starlette.requests import Request

import login_guard as lg


def request(ip: str) -> Request:
    # The real shape behind the preview: a forged entry, the student (added by the CDN edge), the edge, the balancer.
    chain = f"203.0.113.9, {ip}, 104.22.64.183, 34.160.127.70"
    return Request({"type": "http", "method": "POST", "path": "/api/jl/auth/phone", "headers": [(b"x-forwarded-for", chain.encode())],
                    "client": ("10.201.0.66", 1234), "query_string": b""})


def body(phone: str) -> bytes:
    return json.dumps({"phone": phone, "pin": "0000"}).encode()


@pytest.fixture()
def db():
    loop = asyncio.new_event_loop()
    mdb = AsyncIOMotorClient(os.environ["MONGO_URL"], io_loop=loop)[os.environ["DB_NAME"]]
    made = []
    yield loop, mdb, made
    loop.run_until_complete(mdb.login_fails.delete_many({"$or": [{"phone": {"$in": [m[0] for m in made]}}, {"ip": {"$in": [m[1] for m in made]}}]}))
    loop.close()


def test_eight_wrong_pins_pause_that_number_only(db):
    loop, mdb, made = db
    phone, other, ip = "9" + str(secrets.randbelow(10**9)).zfill(9), "8" + str(secrets.randbelow(10**9)).zfill(9), f"198.51.100.{secrets.randbelow(250)}"
    made.append((lg._hash(phone), lg._hash(ip)))
    made.append((lg._hash(other), lg._hash(ip)))
    for _ in range(lg.PHONE_LIMIT):
        keys, paused = loop.run_until_complete(lg.check(mdb, request(ip), lg.SIGN_IN, body(phone)))
        assert paused is None
        loop.run_until_complete(lg.record(mdb, keys, 401))
    keys, paused = loop.run_until_complete(lg.check(mdb, request(ip), lg.SIGN_IN, body(phone)))
    assert keys is None and paused.status_code == 429
    assert 1 <= int(paused.headers["retry-after"]) <= 15 * 60 + 1
    assert json.loads(paused.body)["error"]["code"] == "rate_limited"
    # Another number from the same address still signs in; a spoofed left-hand X-Forwarded-For changes nothing.
    keys, paused = loop.run_until_complete(lg.check(mdb, request(ip), lg.SIGN_IN, body(other)))
    assert paused is None and keys["ip"] == lg._hash(ip)


def test_correct_pin_clears_the_count(db):
    loop, mdb, made = db
    phone, ip = "7" + str(secrets.randbelow(10**9)).zfill(9), f"198.51.100.{secrets.randbelow(250)}"
    made.append((lg._hash(phone), lg._hash(ip)))
    for _ in range(lg.PHONE_LIMIT - 1):
        keys, _ = loop.run_until_complete(lg.check(mdb, request(ip), lg.SIGN_IN, body(phone)))
        loop.run_until_complete(lg.record(mdb, keys, 401))
    keys, _ = loop.run_until_complete(lg.check(mdb, request(ip), lg.SIGN_IN, body(phone)))
    loop.run_until_complete(lg.record(mdb, keys, 200))
    assert loop.run_until_complete(mdb.login_fails.count_documents({"phone": lg._hash(phone)})) == 0


def test_other_paths_and_bad_bodies_pass_through(db):
    loop, mdb, _ = db
    assert loop.run_until_complete(lg.check(mdb, request("198.51.100.1"), "auth/session", b"")) == (None, None)
    keys, paused = loop.run_until_complete(lg.check(mdb, request("198.51.100.1"), lg.SIGN_IN, b"not json"))
    assert paused is None and keys["phone"] == ""
