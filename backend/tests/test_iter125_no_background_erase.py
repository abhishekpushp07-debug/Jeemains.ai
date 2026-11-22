"""Iteration125: deployment blocker fix (no background/startup erase) + owner 'complete' re-erase incl. 'erasing' state.

Static checks read the source. Behaviour checks reuse the scratch DB of test_account_deletion (<DB_NAME>_deletion_selftest,
never dropped); no delete calls in this file and no real account is touched.
"""
import ast
import asyncio
import hashlib
import inspect
import re
import secrets
import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path
from types import SimpleNamespace

from test_account_deletion import scratch  # noqa: F401  (loads .env too)

import account_deletion
import owner_panel

ROOT = Path(__file__).resolve().parents[1]


# --- Static: settle_late gone, erase_companion only called from request_deletion and owner decide() ---
def test_settle_late_removed_everywhere():
    hits = [p for p in ROOT.rglob("*.py") if "tests" not in p.parts and "settle_late" in p.read_text(errors="ignore")]
    assert hits == []


def test_erase_companion_callers():
    callers = []
    for p in ROOT.glob("*.py"):
        tree = ast.parse(p.read_text())
        for fn in ast.walk(tree):
            if isinstance(fn, (ast.FunctionDef, ast.AsyncFunctionDef)):
                for n in ast.walk(fn):
                    if isinstance(n, ast.Call) and getattr(n.func, "id", getattr(n.func, "attr", None)) == "erase_companion":
                        callers.append((p.name, fn.name))
    callers = [c for c in callers if c[1] != "make_router"]  # enclosing router factories contain the handlers
    assert sorted(set(callers)) == [("account_deletion.py", "request_deletion"), ("owner_panel.py", "decide")]


def test_sweep_and_startup_do_not_touch_deletions():
    for file, name in (("jobs.py", "sweep"), ("jobs.py", "sweep_loop"), ("server.py", "startup"), ("db_setup.py", "run_once")):
        src = (ROOT / file).read_text() + "\n@"
        m = re.search(rf"async def {name}\(.*?\):\n(.*?)(?=\n(?:async )?def |\n@)", src, re.S)
        assert m, name
        body = m.group(1)
        assert "erase_companion" not in body and "account_deletion." not in body.replace("account_deletion.ensure_indexes", "")


# --- Behaviour (scratch DB) ---
async def _owner(db, http):
    token = secrets.token_urlsafe(32)
    await db.owner_sessions.insert_one({"digest": hashlib.sha256(token.encode()).hexdigest(), "who": "ow***@test",
                                        "expires_at": datetime.now(timezone.utc) + timedelta(hours=1)})
    http.cookies.set("jl_owner", token)


async def _request(db, uid, state):
    now = datetime.now(timezone.utc)
    rid = account_deletion.new_id()
    await db.account_deletions.insert_one({"id": rid, "uid": uid, "phone": "917000000000", "phone_last4": "0000", "name": "TEST_iter125",
                                           "source": "web", "state": state, "active": True, "requested_at": now,
                                           "due_at": now + timedelta(days=30), "history": [{"at": now, "event": "requested", "by": "web page"}]})
    return rid


def test_owner_complete_accepts_erasing_and_erases():
    async def main():
        client, db, http = await scratch()
        uid = f"TEST-del-{uuid.uuid4().hex[:10]}"
        try:
            await db.rf_profiles.insert_one({"uid": uid, "name": "TEST_iter125", "coins": 7})
            await db.rf_feed.insert_one({"id": f"x:{uid}", "uid": uid, "kind": "level", "data": {}, "ts": 1})
            rid = await _request(db, uid, "erasing")
            await _owner(db, http)
            r = await http.post(f"/api/owner/deletion-requests/{rid}/complete", json={"note": "x"}, headers={"X-Owner-Panel": "1"})
            assert r.status_code == 200, r.text
            assert r.json()["state"] == "owner_completed"
            assert await db.rf_profiles.count_documents({"uid": uid}) == 0
            assert await db.rf_feed.count_documents({"uid": uid}) == 0
            stored = await db.account_deletions.find_one({"id": rid})
            assert [h["event"] for h in stored["history"]] == ["requested", "rapid_fire_erased_again", "website_account_deleted"]
            assert stored.get("erased_at") and stored["erased_again"]["profile"] == 1
            assert "phone" not in stored and "active" not in stored
        finally:
            await http.aclose()
            await client.close()
    asyncio.run(main())


def test_owner_cancel_does_not_erase():
    async def main():
        client, db, http = await scratch()
        uid = f"TEST-del-{uuid.uuid4().hex[:10]}"
        try:
            await db.rf_profiles.insert_one({"uid": uid, "name": "TEST_iter125", "coins": 7})
            rid = await _request(db, uid, "owner_pending")
            await _owner(db, http)
            r = await http.post(f"/api/owner/deletion-requests/{rid}/cancel", json={}, headers={"X-Owner-Panel": "1"})
            assert r.status_code == 200 and r.json()["state"] == "cancelled"
            assert await db.rf_profiles.count_documents({"uid": uid}) == 1
            stored = await db.account_deletions.find_one({"id": rid})
            assert [h["event"] for h in stored["history"]] == ["requested", "cancelled"]
            assert "erased_again" not in stored
            # Completing a cancelled request is refused and erases nothing.
            c = await http.post(f"/api/owner/deletion-requests/{rid}/complete", json={}, headers={"X-Owner-Panel": "1"})
            assert c.status_code == 409 and await db.rf_profiles.count_documents({"uid": uid}) == 1
        finally:
            await http.aclose()
            await client.close()
    asyncio.run(main())


def test_sweep_leaves_pending_request_data_alone(monkeypatch):
    """Run jobs.sweep() against the scratch DB: a pending request's RF rows must survive."""
    import jobs
    import server

    async def main():
        client, db, http = await scratch()
        uid = f"TEST-del-{uuid.uuid4().hex[:10]}"
        try:
            await db.rf_profiles.insert_one({"uid": uid, "name": "TEST_iter125", "coins": 3})
            await _request(db, uid, "owner_pending")
            async def noop():
                return None
            await jobs.sweep(db, server.duel_api["settle"], SimpleNamespace(resume_payouts=noop))
            assert await db.rf_profiles.count_documents({"uid": uid}) == 1
        finally:
            await http.aclose()
            await client.close()
    asyncio.run(main())
