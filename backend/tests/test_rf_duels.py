# Rapid Fire 30-card sessions + Rapid Fire Duels (/api/rf/duels) regression tests
import os
import time
import uuid
import pytest
import requests
from dotenv import load_dotenv

load_dotenv("/app/frontend/.env")
BASE_URL = os.environ.get("EXPO_PUBLIC_BACKEND_URL").rstrip("/")
UID_A = "db0c62b8-eeaf-41be-b8b1-05f5f34ac1d8"


@pytest.fixture(scope="module")
def s():
    return requests.Session()


@pytest.fixture(scope="module")
def uid_b(s):
    sid = "TESTSID" + uuid.uuid4().hex[:20]
    r = s.post(f"{BASE_URL}/api/jl/auth/phone", json={"phone": "9000000002"}, headers={"X-JL-Sid": sid})
    assert r.status_code == 200, r.text
    me = s.get(f"{BASE_URL}/api/jl/auth/me", headers={"X-JL-Sid": sid}).json()
    u = me.get("data") or me.get("user", me)
    uid = u.get("id") or u.get("user_id")
    print("uid_b", uid)
    assert uid and uid != UID_A
    return uid


def H(u):
    return {"X-RF-User": u}


# ---------- solo session: 30 cards ----------
def test_session_default_30_and_complete_30(s):
    r = s.post(f"{BASE_URL}/api/rf/sessions", json={"subject": "Mathematics", "request_id": "TEST_" + uuid.uuid4().hex}, headers=H(UID_A))
    assert r.status_code == 200, r.text
    cards = r.json()["cards"]
    assert len(cards) == 30
    assert len({c["id"] for c in cards}) == 30
    res = [{"card_id": c["id"], "outcome": "answer" and "correct", "choice": c["answer"], "ms": 1000} for c in cards]
    rc = s.post(f"{BASE_URL}/api/rf/sessions/{r.json()['id']}/complete", json={"results": res}, headers=H(UID_A))
    assert rc.status_code == 200, rc.text
    sm = rc.json()["summary"]
    print("summary30", sm)
    assert sm["total"] == 30 and sm["correct"] == 30
    assert s.post(f"{BASE_URL}/api/rf/sessions", json={"subject": "Physics", "count": 31, "request_id": "TEST_" + uuid.uuid4().hex}, headers=H(UID_A)).status_code == 422


# ---------- duels ----------
def test_duel_auth_and_validation(s):
    body = {"subject": "Physics", "chapter": None, "mode": "invite", "name": "TEST_A", "request_id": "TEST_" + uuid.uuid4().hex}
    assert s.post(f"{BASE_URL}/api/rf/duels", json=body).status_code == 401
    assert s.post(f"{BASE_URL}/api/rf/duels", json={**body, "mode": "bogus"}, headers=H(UID_A)).status_code == 422
    assert s.post(f"{BASE_URL}/api/rf/duels", json={**body, "subject": "Biology"}, headers=H(UID_A)).status_code == 422
    assert s.post(f"{BASE_URL}/api/rf/duels/join", json={"code": "ZZZZZZ", "name": "TEST_B"}, headers=H(UID_A)).status_code == 404
    assert s.get(f"{BASE_URL}/api/rf/duels/nope", headers=H(UID_A)).status_code == 404


def test_random_match(s, uid_b):
    ra = s.post(f"{BASE_URL}/api/rf/duels", json={"subject": "Chemistry", "chapter": None, "mode": "random", "name": "TEST_A",
                                                  "request_id": "TEST_" + uuid.uuid4().hex}, headers=H(UID_A))
    assert ra.status_code == 200, ra.text
    a = ra.json()
    print("A random status", a["status"])
    if a["status"] == "ready":
        pytest.skip("A matched a pre-existing waiting duel")
    assert a["status"] == "waiting" and a["cards"] == []
    rb = s.post(f"{BASE_URL}/api/rf/duels", json={"subject": "Chemistry", "chapter": None, "mode": "random", "name": "TEST_B",
                                                  "request_id": "TEST_" + uuid.uuid4().hex}, headers=H(uid_b))
    assert rb.status_code == 200, rb.text
    b = rb.json()
    assert b["id"] == a["id"] and b["status"] == "ready"
    assert len(b["cards"]) == 30 and all("answer" not in c and "explain" not in c for c in b["cards"])
    ga = s.get(f"{BASE_URL}/api/rf/duels/{a['id']}", headers=H(UID_A)).json()
    assert ga["status"] == "ready" and [c["id"] for c in ga["cards"]] == [c["id"] for c in b["cards"]]
    assert len(ga["players"]) == 2


def test_invite_full_flow(s, uid_b):
    rid = "TEST_" + uuid.uuid4().hex
    body = {"subject": "Physics", "chapter": None, "mode": "invite", "name": "TEST_A", "request_id": rid}
    a = s.post(f"{BASE_URL}/api/rf/duels", json=body, headers=H(UID_A)).json()
    assert a["status"] == "waiting" and len(a["code"]) == 6
    # idempotent create
    assert s.post(f"{BASE_URL}/api/rf/duels", json=body, headers=H(UID_A)).json()["id"] == a["id"]
    # creator joining own code returns same duel without adding self
    selfj = s.post(f"{BASE_URL}/api/rf/duels/join", json={"code": a["code"], "name": "TEST_A"}, headers=H(UID_A)).json()
    assert selfj["status"] == "waiting" and len(selfj["players"]) == 1
    # stranger cannot view
    assert s.get(f"{BASE_URL}/api/rf/duels/{a['id']}", headers=H(uid_b)).status_code == 404
    jb = s.post(f"{BASE_URL}/api/rf/duels/join", json={"code": a["code"].lower(), "name": "TEST_B"}, headers=H(uid_b))
    assert jb.status_code == 200, jb.text
    b = jb.json()
    assert b["status"] == "ready" and len(b["cards"]) == 30 and all("answer" not in c for c in b["cards"])
    did = a["id"]
    # code now used -> third join 404 (reuse A? use random uid)
    assert s.post(f"{BASE_URL}/api/rf/duels/join", json={"code": a["code"], "name": "X"}, headers=H("TESTUSER" + uuid.uuid4().hex[:10])).status_code == 404
    # before start_at - 1 -> 409
    early = s.post(f"{BASE_URL}/api/rf/duels/{did}/answer", json={"index": 0, "choice": 0, "outcome": "answer", "ms": 500}, headers=H(UID_A))
    print("early answer", early.status_code)
    wait = b["start_at"] - b["server_now"]
    time.sleep(max(0, wait) + 0.5)
    # out of order
    assert s.post(f"{BASE_URL}/api/rf/duels/{did}/answer", json={"index": 2, "choice": 0, "outcome": "answer", "ms": 500}, headers=H(UID_A)).status_code == 409
    # A answers all 30 with choice 0, records correct answers
    answers = []
    for i in range(30):
        r = s.post(f"{BASE_URL}/api/rf/duels/{did}/answer", json={"index": i, "choice": 0, "outcome": "answer", "ms": 1000}, headers=H(UID_A))
        assert r.status_code == 200, (i, r.text)
        answers.append(r.json()["answer"])
        if i == 0:
            rep = s.post(f"{BASE_URL}/api/rf/duels/{did}/answer", json={"index": 0, "choice": 1, "outcome": "answer", "ms": 1000}, headers=H(UID_A))
            assert rep.status_code == 200 and rep.json()["outcome"] == r.json()["outcome"]
    a_score = sum(1 for x in answers if x == 0)
    mid = s.get(f"{BASE_URL}/api/rf/duels/{did}", headers=H(uid_b)).json()
    assert mid["status"] == "ready"
    opp = next(p for p in mid["players"] if not p["you"])
    assert opp["answered"] == 30 and opp["score"] == a_score and "answers" not in opp
    assert all("answer" not in c for c in mid["cards"])
    # B answers all correctly using revealed answers; mix outcomes
    for i in range(30):
        body = {"index": i, "choice": answers[i], "outcome": "answer", "ms": 2000} if i % 10 else {"index": i, "outcome": "skipped", "ms": 0}
        r = s.post(f"{BASE_URL}/api/rf/duels/{did}/answer", json=body, headers=H(uid_b))
        assert r.status_code == 200, (i, r.text)
    fin = s.get(f"{BASE_URL}/api/rf/duels/{did}", headers=H(UID_A)).json()
    print("final", fin["status"], fin["winner"], [(p["name"], p["score"]) for p in fin["players"]])
    assert fin["status"] == "finished"
    assert all("answer" in c for c in fin["cards"])
    expected = uid_b if 27 > a_score else (UID_A if a_score > 27 else UID_A)  # tie -> lower ms: A 30000 < B 54000
    assert fin["winner"] == expected
    # answer after finish -> 409
    assert s.post(f"{BASE_URL}/api/rf/duels/{did}/answer", json={"index": 0, "choice": 0, "outcome": "answer"}, headers=H(UID_A)).status_code == 200  # replay after finish returns the saved result
    hist = s.get(f"{BASE_URL}/api/rf/duels", headers=H(uid_b)).json()
    item = next(i for i in hist["items"] if i["id"] == did)
    assert item["won"] == (expected == uid_b)


def test_cancel(s, uid_b):
    a = s.post(f"{BASE_URL}/api/rf/duels", json={"subject": "Mathematics", "chapter": None, "mode": "invite", "name": "TEST_A",
                                                 "request_id": "TEST_" + uuid.uuid4().hex}, headers=H(UID_A)).json()
    # non-owner cancel is no-op
    s.post(f"{BASE_URL}/api/rf/duels/{a['id']}/cancel", headers=H(uid_b))
    assert s.post(f"{BASE_URL}/api/rf/duels/{a['id']}/cancel", headers=H(UID_A)).json()["ok"] is True
    assert s.get(f"{BASE_URL}/api/rf/duels/{a['id']}", headers=H(UID_A)).json()["status"] == "cancelled"
    assert s.post(f"{BASE_URL}/api/rf/duels/join", json={"code": a["code"], "name": "TEST_B"}, headers=H(uid_b)).status_code == 404
