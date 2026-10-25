# Rapid Fire iteration 21: PLAY (mode=random) auto-seats an arena opponent; invite has no auto-seat; catalog for chapter picker
import os
import time
import uuid
import pytest
import requests
from dotenv import load_dotenv
from pymongo import MongoClient

load_dotenv("/app/frontend/.env")
load_dotenv("/app/backend/.env")
BASE_URL = os.environ.get("EXPO_PUBLIC_BACKEND_URL").rstrip("/")
API = f"{BASE_URL}/api/rf"
DB = MongoClient(os.environ["MONGO_URL"])[os.environ["DB_NAME"]]
UIDS = []


def H(u):
    return {"X-RF-User": u}


def new_uid():
    u = "TEST-" + uuid.uuid4().hex[:16]
    UIDS.append(u)
    return u


@pytest.fixture(scope="module", autouse=True)
def cleanup():
    yield
    DB.rf_duels.delete_many({"players.uid": {"$in": UIDS}})
    for c in ("rf_profiles", "rf_sessions", "rf_rewards", "rf_game"):
        DB[c].delete_many({"$or": [{"uid": {"$in": UIDS}}, {"user_id": {"$in": UIDS}}]})


@pytest.fixture
def s():
    return requests.Session()


# Catalog feeds the chapter picker (subjects, chapters with counts)
class TestCatalog:
    def test_catalog_three_subjects_with_chapters(self, s):
        r = s.get(f"{API}/catalog", headers=H(new_uid()))
        assert r.status_code == 200
        subs = r.json()["subjects"]
        names = {x["name"] for x in subs}
        assert {"Physics", "Chemistry", "Mathematics"} <= names
        for x in subs:
            assert x["total"] > 0 and len(x["chapters"]) > 0
            assert all(isinstance(c["count"], int) for c in x["chapters"])


# Random PLAY: waiting then a seat via /bot (what the client does after 5-7.5 s)
class TestRandomAutoSeat:
    def test_random_waiting_then_seat(self, s):
        u = new_uid()
        # use a unique chapter-less subject; another tester might match us, so accept ready too
        r = s.post(f"{API}/duels", headers=H(u), json={"subject": "Chemistry", "chapter": None, "mode": "random", "name": "TEST_me", "request_id": uuid.uuid4().hex})
        assert r.status_code == 200, r.text
        d = r.json()
        assert d["mode"] == "random"
        if d["status"] == "waiting":
            b = s.post(f"{API}/duels/{d['id']}/bot", headers=H(u), json={})
            assert b.status_code == 200, b.text
            d = b.json()
        assert d["status"] == "ready"
        assert len(d["players"]) == 2
        opp = [p for p in d["players"] if not p["you"]][0]
        assert opp["name"] and "ai" not in opp["name"].lower().split() and "bot" not in opp["name"].lower()
        assert d["start_at"] > d["server_now"] - 1
        assert len(d["cards"]) == 30 or len(d.get("card_ids", d["cards"])) > 0

    def test_random_seat_twice_409(self, s):
        u = new_uid()
        d = s.post(f"{API}/duels", headers=H(u), json={"subject": "Mathematics", "chapter": None, "mode": "random", "name": "TEST_me", "request_id": uuid.uuid4().hex}).json()
        s.post(f"{API}/duels/{d['id']}/bot", headers=H(u), json={})
        assert s.post(f"{API}/duels/{d['id']}/bot", headers=H(u), json={}).status_code == 409

    def test_random_seat_answer_and_result(self, s):
        u = new_uid()
        d = s.post(f"{API}/duels", headers=H(u), json={"subject": "Physics", "chapter": None, "mode": "random", "name": "TEST_me", "request_id": uuid.uuid4().hex}).json()
        if d["status"] == "waiting":
            d = s.post(f"{API}/duels/{d['id']}/bot", headers=H(u), json={}).json()
        wait = d["start_at"] - d["server_now"]
        if wait > 0:
            time.sleep(min(wait + 0.3, 6))
        c = d["cards"][0]
        a = s.post(f"{API}/duels/{d['id']}/answer", headers=H(u), json={"index": 0, "choice": 0, "outcome": "answer"})
        assert a.status_code == 200, a.text
        # forfeit to finish and inspect result
        assert s.post(f"{API}/duels/{d['id']}/forfeit", headers=H(u), json={}).status_code == 200
        g = s.get(f"{API}/duels/{d['id']}", headers=H(u)).json()
        assert g["status"] == "finished"
        assert g.get("winner")
        print("winner:", g["winner"], "you:", g.get("you"), "reward:", g.get("reward"), "vs_bot:", g.get("vs_bot"))

    def test_invite_stays_waiting(self, s):
        u = new_uid()
        d = s.post(f"{API}/duels", headers=H(u), json={"subject": "Physics", "chapter": None, "mode": "invite", "name": "TEST_me", "request_id": uuid.uuid4().hex}).json()
        assert d["status"] == "waiting" and len(d["code"]) == 6
        time.sleep(8)
        g = s.get(f"{API}/duels/{d['id']}", headers=H(u)).json()
        assert g["status"] == "waiting" and len(g["players"]) == 1
