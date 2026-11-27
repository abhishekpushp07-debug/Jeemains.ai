"""One name everywhere (27 Nov 2026): the name a student writes for themselves is the one Rapid Fire shows too.

The website keeps and checks the name (PUT /profile/display-name) but cannot be asked for it, so when that request goes
through our proxy and the website answers "saved", our server notes the name the website kept (social.name_kept).

What must hold:
  * the name comes only from the website's own answer, and is noted for the account whose session it was;
  * the student's answer from the website is passed on unchanged, whatever happens to our note;
  * a refused name, another request, or a session nobody is known for: nothing is noted;
  * the name stays when the student comes back (a new Rapid Fire pass), and goes when the website takes it away;
  * GET /api/rf/name says it, and the Rapid Fire profile shows it.

Three fixed throwaway TEST- players and made-up session handles only. Nothing is deleted: each test first puts its own
player back to a known state (an update), and ends by taking the name away again; the short-lived passes and the empty
jars go by themselves (their own expiry). The website is never called: its answer is stood in for."""
import asyncio
import hashlib
import json
import os
import secrets
import sys
import uuid
from datetime import UTC, datetime, timedelta

import httpx
from motor.motor_asyncio import AsyncIOMotorClient
from multidict import CIMultiDict
from starlette.requests import Request

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(os.path.dirname(__file__)), ".env"))
import jl_proxy
from jl_transport import Upstream
from social import name_kept, public_name, remember_identity, set_chosen_name

BASE = "http://localhost:8001/api/rf"
PATH = "profile/display-name"


def website(status, data=None, message="", raw=None):
    """The website's answer, in its own envelope."""
    body = raw if raw is not None else json.dumps({"data": data, "error": {"code": f"http_{status}", "message": message} if message else None, "meta": {"api_version": "1"}}).encode()
    return Upstream(status, CIMultiDict({"content-type": "application/json"}), body)


def asked(method, body):
    """The app's request as the proxy receives it."""
    sent = {"done": False}

    async def receive():
        if sent["done"]:
            return {"type": "http.disconnect"}
        sent["done"] = True
        return {"type": "http.request", "body": json.dumps(body).encode(), "more_body": False}
    return Request({"type": "http", "method": method, "path": "/api/jl/" + PATH, "query_string": b"", "client": ("127.0.0.1", 1),
                    "headers": [(b"content-type", b"application/json"), (b"accept", b"application/json")]}, receive)


ACCOUNT = {"name": "Learner TEST1234"}  # what the website's session answer says about the account (no phone: nothing to be found by)
# One player and one session handle per test, the same on every run, so no row is ever added twice.
SIDS = {"kept": "7e57a000-0000-4000-8000-000000000001", "noted": "7e57a000-0000-4000-8000-000000000002", "proxy": "7e57a000-0000-4000-8000-000000000003",
        "nobody": "7e57a000-0000-4000-8000-000000000004"}


async def made(db, tag):
    """This test's own player in a known state: the account's name, no name of their own, a fresh 10-minute pass."""
    uid, sid, token = f"TEST-name-{tag}", SIDS[tag], secrets.token_urlsafe(24)
    await db.rf_access.insert_one({"digest": hashlib.sha256(token.encode()).hexdigest(), "uid": uid, "sid": "", "expires_at": datetime.now(UTC) + timedelta(minutes=10)})
    await db.jl_jars.update_one({"sid": sid}, {"$set": {"uid": uid, "cookies": {}, "seen_at": datetime.now(UTC)}}, upsert=True)
    await remember_identity(db, uid, ACCOUNT)
    await set_chosen_name(db, uid, "")
    return uid, sid, {"Authorization": "Bearer " + token}


async def rested(db, uid):
    """The end of a test: the player has no name of their own again. Nothing is removed."""
    assert uid.startswith("TEST-name-"), "never a real account"
    await set_chosen_name(db, uid, "")


async def row(db, uid):
    return await db.rf_profiles.find_one({"uid": uid}, {"_id": 0, "chosen_name": 1, "display_name": 1, "name": 1})


def test_the_name_shown_is_the_students_own_then_the_accounts_then_the_hidden_phone():
    assert public_name({"chosen_name": "Asha Rao", "display_name": "Learner AB12CD34", "phone_last4": "2345"}) == "Asha Rao"
    assert public_name({"chosen_name": "", "display_name": "Learner AB12CD34", "phone_last4": "2345"}) == "Learner AB12CD34"
    assert public_name({"display_name": "", "phone_last4": "2345"}) == "••••••2345"
    assert public_name({}) == "Player" and public_name({"name": "TESTAsha"}) == "TESTAsha"


def test_a_name_the_website_kept_is_shown_and_stays():
    async def run():
        db = AsyncIOMotorClient(os.environ["MONGO_URL"])[os.environ["DB_NAME"]]
        uid, _, h = await made(db, "kept")
        try:
            async with httpx.AsyncClient(base_url=BASE, timeout=30) as s:
                assert (await row(db, uid))["name"] == "Learner TEST1234"
                assert (await s.get("/name", headers=h)).json() == {"name": ""}
                assert await set_chosen_name(db, uid, "  Asha   Rao ") == "Asha Rao"
                assert (await row(db, uid)) == {"chosen_name": "Asha Rao", "display_name": "Learner TEST1234", "name": "Asha Rao"}
                assert (await s.get("/name", headers=h)).json() == {"name": "Asha Rao"}
                assert (await s.get("/profile", headers=h)).json()["name"] == "Asha Rao"
                # Rapid Fire's older door for a name never writes over a signed-in student's name.
                assert (await s.post("/profile/name", headers=h, json={"name": "Somebody Else"})).status_code == 200
                assert (await row(db, uid))["name"] == "Asha Rao" and (await s.get("/profile", headers=h)).json()["name"] == "Asha Rao"
                # The student comes back (a new pass is made from the website's session answer, which has no such name in it).
                await remember_identity(db, uid, ACCOUNT)
                assert (await row(db, uid))["name"] == "Asha Rao" and (await row(db, uid))["chosen_name"] == "Asha Rao"
                # The website took the name away: the account's own name again.
                assert await set_chosen_name(db, uid, None) == "Learner TEST1234"
                assert (await row(db, uid))["name"] == "Learner TEST1234" and (await s.get("/name", headers=h)).json() == {"name": ""}
                # The day the website's session answer carries the name, it is taken from there (also when it is empty).
                await remember_identity(db, uid, {**ACCOUNT, "display_name": "Asha R"})
                assert (await row(db, uid))["name"] == "Asha R"
                await remember_identity(db, uid, {**ACCOUNT, "display_name": None})
                assert (await row(db, uid))["name"] == "Learner TEST1234" and (await row(db, uid))["chosen_name"] == ""
        finally:
            await rested(db, uid)
    asyncio.run(run())


def test_only_the_websites_own_saved_answer_is_noted():
    async def run():
        db = AsyncIOMotorClient(os.environ["MONGO_URL"])[os.environ["DB_NAME"]]
        uid, sid, _ = await made(db, "noted")
        nobody = SIDS["nobody"]  # a session handle whose jar does not say whose it is
        await db.jl_jars.update_one({"sid": nobody}, {"$set": {"cookies": {}, "seen_at": datetime.now(UTC)}, "$unset": {"uid": ""}}, upsert=True)
        try:
            await name_kept(db, sid, website(200, {"display_name": "Asha Rao"}))
            assert (await row(db, uid))["name"] == "Asha Rao"
            await name_kept(db, sid, website(200, {"display_name": None}))  # taken away
            assert (await row(db, uid))["name"] == "Learner TEST1234"
            await name_kept(db, sid, Upstream(200, CIMultiDict(), json.dumps({"display_name": "Plain Shape"}).encode()))  # without the envelope
            assert (await row(db, uid))["name"] == "Plain Shape"
            for answer in (website(200, {"ok": True}), website(200, None), website(200, raw=b"not json"), website(200, raw=b"[1, 2]")):
                await name_kept(db, sid, answer)  # nothing to note, and nothing raised
            assert (await row(db, uid))["name"] == "Plain Shape"
            await name_kept(db, nobody, website(200, {"display_name": "Nobody"}))
            await name_kept(db, str(uuid.uuid4()), website(200, {"display_name": "Nobody"}))
            assert await db.rf_profiles.count_documents({"chosen_name": "Nobody"}) == 0
        finally:
            await rested(db, uid)
    asyncio.run(run())


def test_the_proxy_notes_the_name_and_passes_the_answer_on_unchanged(monkeypatch):
    async def run():
        db = AsyncIOMotorClient(os.environ["MONGO_URL"])[os.environ["DB_NAME"]]
        monkeypatch.setattr(jl_proxy, "db", db)
        uid, sid, _ = await made(db, "proxy")
        calls = []

        def answers(answer):
            async def stand_in(client, method, url, *, path, params, body, headers):
                calls.append((method, path, json.loads(body or b"{}")))
                return answer
            monkeypatch.setattr(jl_proxy, "canonical_request", stand_in)
        try:
            saved = website(200, {"display_name": "Asha Rao"})
            answers(saved)
            out = await jl_proxy.forward_jeelive(PATH, asked("PUT", {"name": "Asha Rao"}), sid)
            assert out.status_code == 200 and out.body == saved.content, "the website's answer reaches the app as it is"
            assert calls[-1] == ("PUT", PATH, {"name": "Asha Rao"})
            assert (await row(db, uid))["name"] == "Asha Rao" and (await row(db, uid))["chosen_name"] == "Asha Rao"

            refused = website(422, None, "Naam 2 se 20 akshar ka rakho: sirf akshar, ank aur space.")
            answers(refused)
            out = await jl_proxy.forward_jeelive(PATH, asked("PUT", {"name": "!"}), sid)
            assert out.status_code == 422 and out.body == refused.content
            assert (await row(db, uid))["name"] == "Asha Rao", "a refused name changes nothing"

            answers(website(200, {"display_name": "Someone Else"}))  # the same words from any other request are not a saved name
            await jl_proxy.forward_jeelive(PATH, asked("POST", {"name": "Someone Else"}), sid)
            await jl_proxy.forward_jeelive("profile/other", asked("PUT", {"name": "Someone Else"}), sid)
            assert (await row(db, uid))["name"] == "Asha Rao"

            broken = website(200, raw=b"saved, but not in the shape we know")
            answers(broken)
            out = await jl_proxy.forward_jeelive(PATH, asked("PUT", {"name": "Asha"}), sid)
            assert out.status_code == 200 and out.body == broken.content, "trouble with our own note never becomes the student's trouble"
            assert (await row(db, uid))["name"] == "Asha Rao"

            answers(website(200, {"display_name": None}))
            await jl_proxy.forward_jeelive(PATH, asked("PUT", {"name": ""}), sid)
            assert (await row(db, uid))["name"] == "Learner TEST1234" and (await row(db, uid))["chosen_name"] == ""
        finally:
            await rested(db, uid)
    asyncio.run(run())
