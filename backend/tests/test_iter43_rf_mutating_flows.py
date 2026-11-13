"""Iteration 43: Rapid Fire mutating gameplay/shop/duel/history regression.

Modules covered:
- solo sprint create/partial/full/replay integrity + reward idempotency
- duel invite/join, websocket first-frame auth, full 30-card completion
- malformed websocket auth payload rejection
- friends history owner scoping + read-only reopen behavior
- shop buy/equip/insufficient flows on isolated QA profiles
"""

from __future__ import annotations

import asyncio
import hashlib
import json
import os
import time
import uuid
from datetime import datetime, timedelta, timezone

import pytest
import requests
import websockets
from dotenv import load_dotenv
from pymongo import MongoClient


load_dotenv("/app/frontend/.env")
load_dotenv("/app/backend/.env")

BASE_URL = (os.environ.get("EXPO_PUBLIC_BACKEND_URL") or "").rstrip("/")
MONGO_URL = (os.environ.get("MONGO_URL") or "").strip().strip('"')
DB_NAME = (os.environ.get("DB_NAME") or "").strip().strip('"')


def _need_env() -> None:
    if not BASE_URL:
        pytest.skip("Missing EXPO_PUBLIC_BACKEND_URL")
    if not MONGO_URL or not DB_NAME:
        pytest.skip("Missing MONGO_URL/DB_NAME")


def _digest(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


@pytest.fixture(scope="module")
def mongo_db():
    _need_env()
    client = MongoClient(MONGO_URL)
    db = client[DB_NAME]
    try:
        yield db
    finally:
        client.close()


@pytest.fixture(scope="module")
def ids():
    r = uuid.uuid4().hex[:8]
    return {
        "run": r,
        "uid_a": f"TEST-RF-portrait-{r}-A",
        "uid_b": f"TEST-RF-portrait-{r}-B",
        "uid_c": f"TEST-RF-portrait-{r}-C",
        "sid_a": f"TESTSID-ITER43-{r}-A",
        "sid_b": f"TESTSID-ITER43-{r}-B",
    }


@pytest.fixture(scope="module", autouse=True)
def cleanup(mongo_db, ids):
    yield
    prefix = f"^TEST-RF-portrait-{ids['run']}-"
    mongo_db.rf_access.delete_many({"uid": {"$regex": prefix}})
    mongo_db.rf_sessions.delete_many({"user_id": {"$regex": prefix}})
    mongo_db.rf_duels.delete_many({"players.uid": {"$regex": prefix}})
    mongo_db.rf_profiles.delete_many({"uid": {"$regex": prefix}})
    mongo_db.rf_awards.delete_many({"uid": {"$regex": prefix}})
    mongo_db.rf_learning_events.delete_many({"uid": {"$regex": prefix}})
    mongo_db.jl_jars.delete_many({"sid": {"$in": [ids["sid_a"], ids["sid_b"]]}})


def _grant(mongo_db, uid: str, minutes: int = 30) -> str:
    token = "iter43-" + uuid.uuid4().hex + uuid.uuid4().hex
    mongo_db.rf_access.insert_one(
        {
            "digest": _digest(token),
            "uid": uid,
            "sid": "",
            "expires_at": datetime.now(timezone.utc) + timedelta(minutes=minutes),
        }
    )
    return token


def _h(token: str) -> dict:
    return {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}


def _create_profile(mongo_db, uid: str, coins: int) -> None:
    mongo_db.rf_profiles.update_one(
        {"uid": uid},
        {
            "$set": {
                "uid": uid,
                "name": uid,
                "coins": coins,
                "owned": [],
                "equipped": {"frame": None, "entry": None, "theme": None},
                "avatar": "av_astronaut",
                "xp": 0,
                "level": 1,
                "level_floor": 0,
                "next_level_xp": 100,
                "streak": 0,
                "best_streak": 0,
                "played_today": False,
                "sessions": 0,
                "duels": 0,
                "wins": 0,
                "cards_correct": 0,
                "badges": [],
                "freezes": 0,
                "quests": [],
            }
        },
        upsert=True,
    )


@pytest.fixture(scope="module")
def state(mongo_db, ids):
    _create_profile(mongo_db, ids["uid_a"], 250)
    _create_profile(mongo_db, ids["uid_b"], 250)
    _create_profile(mongo_db, ids["uid_c"], 1000)
    return {
        "a": {"uid": ids["uid_a"], "token": _grant(mongo_db, ids["uid_a"])},
        "b": {"uid": ids["uid_b"], "token": _grant(mongo_db, ids["uid_b"])},
        "c": {"uid": ids["uid_c"], "token": _grant(mongo_db, ids["uid_c"])},
    }


def test_solo_session_partial_then_reopen_no_duplicate_credit(state):
    """Session module: 30-card/20s contract, partial completion, reward idempotency on reopen."""
    t = state["a"]["token"]
    req_id = "iter43-solo-a-" + uuid.uuid4().hex
    create = requests.post(
        f"{BASE_URL}/api/rf/sessions",
        json={"subject": "Physics", "chapter": None, "count": 30, "request_id": req_id, "exam": "JEE", "revision": False},
        headers=_h(t),
        timeout=30,
    )
    assert create.status_code == 200
    payload = create.json()
    assert payload.get("seconds_per_card") == 15  # solo cards are 15 s since iteration 61
    cards = payload.get("cards") or []
    assert len(cards) == 30
    sid = payload["id"]

    before = requests.get(f"{BASE_URL}/api/rf/profile", headers=_h(t), timeout=20)
    assert before.status_code == 200
    coins_before = int(before.json().get("coins") or 0)

    # 5 explicit answers; remaining cards become skipped server-side.
    results = []
    for i, c in enumerate(cards[:5]):
        if i % 2 == 0:
            choice = int(c["answer"])
        else:
            choice = (int(c["answer"]) + 1) % 4
        results.append(
            {
                "card_id": c["id"],
                "outcome": "correct" if i % 2 == 0 else "incorrect",
                "choice": choice,
                "ms": 1300 + i * 120,
            }
        )
    done = requests.post(
        f"{BASE_URL}/api/rf/sessions/{sid}/complete",
        json={"results": results},
        headers=_h(t),
        timeout=30,
    )
    assert done.status_code == 200
    summary = done.json().get("summary") or {}
    assert summary.get("total") == 30
    assert summary.get("answered") == 5
    assert summary.get("correct") == 3
    assert summary.get("incorrect") == 2
    assert summary.get("skipped") == 25

    after_1 = requests.get(f"{BASE_URL}/api/rf/profile", headers=_h(t), timeout=20)
    assert after_1.status_code == 200
    coins_after_1 = int(after_1.json().get("coins") or 0)
    assert coins_after_1 >= coins_before

    reopen = requests.get(f"{BASE_URL}/api/rf/sessions/{sid}", headers=_h(t), timeout=20)
    assert reopen.status_code == 200

    # Re-complete existing completed session must not duplicate credits.
    done_again = requests.post(
        f"{BASE_URL}/api/rf/sessions/{sid}/complete",
        json={"results": results},
        headers=_h(t),
        timeout=30,
    )
    assert done_again.status_code == 200

    after_2 = requests.get(f"{BASE_URL}/api/rf/profile", headers=_h(t), timeout=20)
    assert after_2.status_code == 200
    coins_after_2 = int(after_2.json().get("coins") or 0)
    assert coins_after_2 == coins_after_1


def test_solo_fresh_play_again_creates_new_session_id(state):
    """Session module: play-again request should create fresh session id with reset card index context."""
    t = state["a"]["token"]
    req1 = "iter43-again-1-" + uuid.uuid4().hex
    req2 = "iter43-again-2-" + uuid.uuid4().hex
    s1 = requests.post(
        f"{BASE_URL}/api/rf/sessions",
        json={"subject": "Physics", "chapter": None, "count": 30, "request_id": req1, "exam": "JEE", "revision": False},
        headers=_h(t),
        timeout=30,
    )
    s2 = requests.post(
        f"{BASE_URL}/api/rf/sessions",
        json={"subject": "Physics", "chapter": None, "count": 30, "request_id": req2, "exam": "JEE", "revision": False},
        headers=_h(t),
        timeout=30,
    )
    assert s1.status_code == 200
    assert s2.status_code == 200
    p1, p2 = s1.json(), s2.json()
    assert p1["id"] != p2["id"]
    assert len(p1.get("cards") or []) == 30
    assert len(p2.get("cards") or []) == 30


def test_fresh_mode_30_unique_ids_and_normalized_prompts(state):
    """Deck module: fresh mode returns 30 unique cards with normalized-prompt uniqueness."""
    t = state["a"]["token"]
    res = requests.post(
        f"{BASE_URL}/api/rf/sessions",
        json={"subject": "Physics", "chapter": None, "count": 30, "request_id": "iter43-uniq-" + uuid.uuid4().hex, "exam": "JEE", "revision": False},
        headers=_h(t),
        timeout=30,
    )
    assert res.status_code == 200
    cards = res.json().get("cards") or []
    assert len(cards) == 30
    ids = [c["id"] for c in cards]
    assert len(set(ids)) == 30
    prompts = [" ".join((c.get("prompt") or "").strip().casefold().split()) for c in cards]
    assert len(set(prompts)) == 30


def test_sparse_chapter_not_padded_returns_400(state):
    """Deck module: sparse chapter selection cannot be padded to 30 cards."""
    t = state["a"]["token"]
    cat = requests.get(f"{BASE_URL}/api/rf/catalog?exam=JEE", timeout=20)
    assert cat.status_code == 200
    subjects = cat.json().get("subjects") or []
    sparse = None
    for s in subjects:
        if s.get("name") != "Physics":
            continue
        for c in s.get("chapters") or []:
            n = int(c.get("count") or 0)
            if 0 < n < 30:
                sparse = c.get("name")
                break
        if sparse:
            break
    if not sparse:
        pytest.skip("No sparse chapter (<30 cards) in current dataset")

    res = requests.post(
        f"{BASE_URL}/api/rf/sessions",
        json={"subject": "Physics", "chapter": sparse, "count": 30, "request_id": "iter43-sparse-" + uuid.uuid4().hex, "exam": "JEE", "revision": False},
        headers=_h(t),
        timeout=30,
    )
    assert res.status_code == 400
    assert "unique quick-recall cards" in (res.json().get("detail") or "")


def test_catalog_reports_14_diagrams():
    """Catalog module: diagram inventory remains 14 after cleanup."""
    cat = requests.get(f"{BASE_URL}/api/rf/catalog?exam=JEE", timeout=20)
    assert cat.status_code == 200
    assert int(cat.json().get("diagram_count") or -1) == 14


def test_duel_invite_join_and_full_30_cards_with_rewards(state, mongo_db):
    """Duel module: real invite/join flow, full 30-card run, score and coin rewards validated."""
    ta, tb = state["a"]["token"], state["b"]["token"]
    create = requests.post(
        f"{BASE_URL}/api/rf/duels",
        json={"subject": "Physics", "chapter": None, "mode": "invite", "name": "TEST-A", "request_id": "iter43-duel-" + uuid.uuid4().hex, "exam": "JEE"},
        headers=_h(ta),
        timeout=30,
    )
    assert create.status_code == 200
    duel_a = create.json()
    did, code = duel_a["id"], duel_a.get("code")
    assert isinstance(code, str) and len(code) == 6
    # Duel codes only work between friends (Phase 3): make A and B friends first.
    for x, y in ((state["a"]["uid"], state["b"]["uid"]), (state["b"]["uid"], state["a"]["uid"])):
        mongo_db.rf_friends.update_one({"uid": x, "fid": y}, {"$setOnInsert": {"ts": time.time()}}, upsert=True)

    join = requests.post(
        f"{BASE_URL}/api/rf/duels/join",
        json={"code": code, "name": "TEST-B", "exam": "JEE"},
        headers=_h(tb),
        timeout=30,
    )
    assert join.status_code == 200

    # Wait until ready and cards become visible.
    ready = None
    for _ in range(40):
        r = requests.get(f"{BASE_URL}/api/rf/duels/{did}", headers=_h(ta), timeout=20)
        assert r.status_code == 200
        body = r.json()
        if body.get("status") == "ready" and len(body.get("cards") or []) == 30:
            ready = body
            break
        time.sleep(0.5)
    assert ready is not None

    # Ensure first-frame token-auth websocket receives state.
    ws_url = BASE_URL.replace("https://", "wss://").replace("http://", "ws://") + f"/api/rf/duels/{did}/ws"

    async def _ws_ok(tok: str):
        async with websockets.connect(ws_url, open_timeout=8) as ws:
            await ws.send(json.dumps({"token": tok}))
            frame = json.loads(await ws.recv())
            assert frame.get("id") == did
            assert frame.get("status") in {"ready", "finished", "waiting", "expired", "cancelled"}

    asyncio.run(_ws_ok(ta))

    # Complete all 30 cards via real duel answer API.
    cards = ready.get("cards") or []
    assert len(cards) == 30
    duel_doc = mongo_db.rf_duels.find_one({"id": did}, {"_id": 0, "card_ids": 1}) or {}
    card_ids = duel_doc.get("card_ids") or []
    assert len(card_ids) == 30
    answer_docs = mongo_db.rf_cards.find({"id": {"$in": card_ids}}, {"_id": 0, "id": 1, "answer": 1})
    answer_map = {d["id"]: int(d["answer"]) for d in answer_docs}
    assert len(answer_map) == 30

    # Wait until server start gate opens for accepting answers.
    opened = False
    for _ in range(30):
        gate = requests.get(f"{BASE_URL}/api/rf/duels/{did}", headers=_h(ta), timeout=20)
        assert gate.status_code == 200
        gb = gate.json()
        if gb.get("status") == "ready" and float(gb.get("server_now") or 0) >= float(gb.get("start_at") or 0):
            opened = True
            break
        time.sleep(0.3)
    assert opened
    # B: first 4 wrong then rest correct -> exactly 26 correct (>=5).
    for i, cid in enumerate(card_ids):
        a_choice = int(answer_map[cid])
        b_choice = (int(answer_map[cid]) + 1) % 4 if i < 4 else int(answer_map[cid])

        ok_a = False
        for _ in range(6):
            ra = requests.post(
                f"{BASE_URL}/api/rf/duels/{did}/answer",
                json={"index": i, "choice": a_choice, "outcome": "answer", "ms": 900},
                headers=_h(ta),
                timeout=20,
            )
            if ra.status_code == 200:
                ok_a = True
                break
            time.sleep(0.2)
        assert ok_a

        ok_b = False
        for _ in range(6):
            rb = requests.post(
                f"{BASE_URL}/api/rf/duels/{did}/answer",
                json={"index": i, "choice": b_choice, "outcome": "answer", "ms": 1200},
                headers=_h(tb),
                timeout=20,
            )
            if rb.status_code == 200:
                ok_b = True
                break
            time.sleep(0.2)
        assert ok_b

    final_a = None
    for _ in range(50):
        r = requests.get(f"{BASE_URL}/api/rf/duels/{did}", headers=_h(ta), timeout=20)
        assert r.status_code == 200
        if r.json().get("status") == "finished":
            final_a = r.json()
            break
        time.sleep(0.5)
    assert final_a is not None
    assert final_a.get("status") == "finished"
    assert len(final_a.get("cards") or []) == 30

    me_a = next(p for p in final_a["players"] if p.get("you"))
    opp_a = next(p for p in final_a["players"] if not p.get("you"))
    assert me_a["score"] == 30
    assert opp_a["score"] == 26

    # +2 per correct and win bonus 50 (for >=5 correct) should apply at least.
    prof_a = requests.get(f"{BASE_URL}/api/rf/profile", headers=_h(ta), timeout=20)
    prof_b = requests.get(f"{BASE_URL}/api/rf/profile", headers=_h(tb), timeout=20)
    assert prof_a.status_code == 200
    assert prof_b.status_code == 200
    assert int(prof_a.json().get("coins") or 0) >= 250 + (30 * 2) + 50
    assert int(prof_b.json().get("coins") or 0) >= 250 + (26 * 2)


def test_friends_history_for_both_and_unrelated_denied(state):
    """History module: duel appears for both participants; unrelated user cannot fetch private duel."""
    ta, tb, tc = state["a"]["token"], state["b"]["token"], state["c"]["token"]
    ha = requests.get(f"{BASE_URL}/api/rf/duels?exam=JEE&friends_only=true", headers=_h(ta), timeout=20)
    hb = requests.get(f"{BASE_URL}/api/rf/duels?exam=JEE&friends_only=true", headers=_h(tb), timeout=20)
    assert ha.status_code == 200
    assert hb.status_code == 200
    items_a = ha.json().get("items") or []
    items_b = hb.json().get("items") or []
    assert len(items_a) >= 1
    assert len(items_b) >= 1
    did = items_a[0]["id"]
    assert any(x["id"] == did for x in items_b)

    # Reopen existing match is read-only: calling GET repeatedly must not error or create new matches.
    g1 = requests.get(f"{BASE_URL}/api/rf/duels/{did}", headers=_h(ta), timeout=20)
    g2 = requests.get(f"{BASE_URL}/api/rf/duels/{did}", headers=_h(ta), timeout=20)
    assert g1.status_code == 200
    assert g2.status_code == 200
    assert g1.json().get("status") == "finished"
    assert g2.json().get("status") == "finished"

    denied = requests.get(f"{BASE_URL}/api/rf/duels/{did}", headers=_h(tc), timeout=20)
    assert denied.status_code == 404


def test_duel_rematch_new_request_id_creates_fresh_duel(state):
    """Duel module: rematch intent should produce fresh duel id when request_id changes."""
    ta = state["a"]["token"]
    d1 = requests.post(
        f"{BASE_URL}/api/rf/duels",
        json={"subject": "Physics", "chapter": None, "mode": "random", "name": "TEST-A", "request_id": "iter43-rematch-1-" + uuid.uuid4().hex, "exam": "JEE"},
        headers=_h(ta),
        timeout=30,
    )
    d2 = requests.post(
        f"{BASE_URL}/api/rf/duels",
        json={"subject": "Physics", "chapter": None, "mode": "random", "name": "TEST-A", "request_id": "iter43-rematch-2-" + uuid.uuid4().hex, "exam": "JEE"},
        headers=_h(ta),
        timeout=30,
    )
    assert d1.status_code == 200
    assert d2.status_code == 200
    assert d1.json().get("id") != d2.json().get("id")


def test_malformed_ws_token_payloads_are_denied(state):
    """WebSocket module: malformed token array/int payloads denied."""
    ta = state["a"]["token"]
    created = requests.post(
        f"{BASE_URL}/api/rf/duels",
        json={"subject": "Physics", "chapter": None, "mode": "invite", "name": "TEST-A", "request_id": "iter43-wsbad-" + uuid.uuid4().hex, "exam": "JEE"},
        headers=_h(ta),
        timeout=30,
    )
    assert created.status_code == 200
    did = created.json()["id"]
    ws_url = BASE_URL.replace("https://", "wss://").replace("http://", "ws://") + f"/api/rf/duels/{did}/ws"

    async def _bad(payload):
        closed = False
        try:
            async with websockets.connect(ws_url, open_timeout=8) as ws:
                await ws.send(payload)
                await ws.recv()
        except Exception:
            closed = True
        return closed

    assert asyncio.run(_bad(json.dumps({"token": ["abc"]})))
    assert asyncio.run(_bad(json.dumps({"token": 12345})))


def test_shop_buy_confirm_equip_and_insufficient(state):
    """Shop module: purchase confirms, coin balance updates, equip works, insufficient blocked."""
    tc, tb = state["c"]["token"], state["b"]["token"]

    shop_c = requests.get(f"{BASE_URL}/api/rf/shop", headers=_h(tc), timeout=20)
    assert shop_c.status_code == 200
    body_c = shop_c.json()
    coins_before = int(body_c.get("coins") or 0)
    avatars = body_c.get("avatars") or []
    target = next((x for x in avatars if int(x.get("price") or 0) > 0), None)
    assert target is not None

    buy = requests.post(f"{BASE_URL}/api/rf/shop/buy", json={"item_id": target["id"]}, headers=_h(tc), timeout=20)
    assert buy.status_code == 200
    coins_after_buy = int(buy.json().get("coins") or coins_before)
    assert coins_after_buy == coins_before - int(target["price"])

    equip = requests.post(f"{BASE_URL}/api/rf/profile/avatar", json={"avatar": target["id"]}, headers=_h(tc), timeout=20)
    assert equip.status_code == 200
    prof_after = requests.get(f"{BASE_URL}/api/rf/profile", headers=_h(tc), timeout=20)
    assert prof_after.status_code == 200
    assert prof_after.json().get("avatar") == target["id"]

    shop_b = requests.get(f"{BASE_URL}/api/rf/shop", headers=_h(tb), timeout=20)
    assert shop_b.status_code == 200
    body_b = shop_b.json()
    avatars_b = body_b.get("avatars") or []
    pricey = next((x for x in avatars_b if int(x.get("price") or 0) > int(body_b.get("coins") or 0)), None)
    if pricey:
        denied = requests.post(f"{BASE_URL}/api/rf/shop/buy", json={"item_id": pricey["id"]}, headers=_h(tb), timeout=20)
        assert denied.status_code == 409
    else:
        # If every avatar is affordable for this profile state, force zero then assert deny.
        # (profile is test-only and cleaned in fixture teardown)
        low_uid = state["b"]["uid"]
        client = MongoClient(MONGO_URL)
        try:
            client[DB_NAME].rf_profiles.update_one({"uid": low_uid}, {"$set": {"coins": 0}})
        finally:
            client.close()
        denied = requests.post(f"{BASE_URL}/api/rf/shop/buy", json={"item_id": avatars_b[0]["id"]}, headers=_h(tb), timeout=20)
        assert denied.status_code == 409
