# Rapid Fire iteration 20: free auto-applied entry effect (entry_spark) + PLAY vs AI flow (invite + /bot)
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
    for u in UIDS:
        DB.rf_profiles.delete_many({"uid": u})
        DB.rf_duels.delete_many({"players.uid": u})


@pytest.fixture(scope="module")
def s():
    return requests.Session()


# ---------- Free entry: profile + shop ----------
class TestFreeEntry:
    def test_new_profile_has_spark(self, s):
        u = new_uid()
        r = s.get(f"{API}/profile", headers=H(u))
        assert r.status_code == 200, r.text
        p = r.json()
        assert "entry_spark" in p["owned"]
        assert p["equipped"]["entry"] == "entry_spark"

    def test_shop_spark_item_and_defaults(self, s):
        u = new_uid()
        r = s.get(f"{API}/shop", headers=H(u))
        assert r.status_code == 200
        d = r.json()
        spark = [i for i in d["items"] if i["id"] == "entry_spark"]
        assert len(spark) == 1 and spark[0]["price"] == 0 and spark[0]["title"] == "Neon Spark" and spark[0]["slot"] == "entry"
        assert "entry_spark" in d["owned"] and d["equipped"]["entry"] == "entry_spark"
        assert d["owned"].count("entry_spark") == 1
        assert "_id" not in d

    def test_buy_spark_409(self, s):
        u = new_uid()
        DB.rf_profiles.update_one({"uid": u}, {"$set": {"coins": 5000}}, upsert=True)
        r = s.post(f"{API}/shop/buy", json={"item_id": "entry_spark"}, headers=H(u))
        assert r.status_code == 409, r.text
        assert DB.rf_profiles.find_one({"uid": u})["coins"] == 5000

    def test_equip_spark_new_user(self, s):
        u = new_uid()
        r = s.post(f"{API}/shop/equip", json={"slot": "entry", "item_id": "entry_spark"}, headers=H(u))
        assert r.status_code == 200 and r.json()["ok"] is True
        assert s.get(f"{API}/shop", headers=H(u)).json()["equipped"]["entry"] == "entry_spark"

    def test_equip_spark_wrong_slot_403(self, s):
        u = new_uid()
        r = s.post(f"{API}/shop/equip", json={"slot": "frame", "item_id": "entry_spark"}, headers=H(u))
        assert r.status_code == 403

    def test_bought_entry_kept(self, s):
        u = new_uid()
        DB.rf_profiles.update_one({"uid": u}, {"$set": {"coins": 1000}}, upsert=True)
        assert s.post(f"{API}/shop/buy", json={"item_id": "entry_rocket"}, headers=H(u)).status_code == 200
        assert s.post(f"{API}/shop/equip", json={"slot": "entry", "item_id": "entry_rocket"}, headers=H(u)).status_code == 200
        sh = s.get(f"{API}/shop", headers=H(u)).json()
        assert sh["equipped"]["entry"] == "entry_rocket"
        assert {"entry_spark", "entry_rocket"} <= set(sh["owned"])
        assert s.get(f"{API}/profile", headers=H(u)).json()["equipped"]["entry"] == "entry_rocket"
        # switching back to spark still allowed
        assert s.post(f"{API}/shop/equip", json={"slot": "entry", "item_id": "entry_spark"}, headers=H(u)).status_code == 200
        assert s.get(f"{API}/shop", headers=H(u)).json()["equipped"]["entry"] == "entry_spark"

    def test_unequip_none_falls_back_to_spark(self, s):
        u = new_uid()
        r = s.post(f"{API}/shop/equip", json={"slot": "entry", "item_id": None}, headers=H(u))
        assert r.status_code == 200
        assert s.get(f"{API}/profile", headers=H(u)).json()["equipped"]["entry"] == "entry_spark"


# ---------- PLAY vs AI (frontend mode=ai -> invite + /bot) ----------
class TestAiDuel:
    def _ai(self, s, u, subject="Physics", chapter=None):
        r = s.post(f"{API}/duels", json={"subject": subject, "chapter": chapter, "mode": "invite", "name": "TEST_ai", "request_id": uuid.uuid4().hex}, headers=H(u))
        assert r.status_code == 200, r.text
        d = r.json()
        assert d["status"] == "waiting"
        t0 = time.time()
        b = s.post(f"{API}/duels/{d['id']}/bot", json={}, headers=H(u))
        return d, b, t0

    def test_ai_duel_ready_immediately(self, s):
        u = new_uid()
        d, b, t0 = self._ai(s, u)
        assert b.status_code == 200, b.text
        v = b.json()
        assert v["status"] == "ready" and v["vs_bot"] is True
        assert len(v["players"]) == 2 and any(p["bot"] for p in v["players"])
        lead = v["start_at"] - v["server_now"]
        assert 3.5 <= lead <= 5.0, lead
        assert len(v.get("cards") or []) == 30 or v.get("total", 30) == 30

    def test_ai_duel_my_entry_is_spark(self, s):
        u = new_uid()
        _, b, _ = self._ai(s, u, "Chemistry")
        me = [p for p in b.json()["players"] if p["you"]][0]
        assert me["entry"] == "entry_spark"
        bot = [p for p in b.json()["players"] if p["bot"]][0]
        assert bot["entry"] and bot["entry"].startswith("entry_")

    def test_ai_duel_bought_entry_used(self, s):
        u = new_uid()
        DB.rf_profiles.update_one({"uid": u}, {"$set": {"coins": 1000, "owned": ["entry_rocket"], "equipped": {"entry": "entry_rocket"}}}, upsert=True)
        _, b, _ = self._ai(s, u, "Mathematics")
        me = [p for p in b.json()["players"] if p["you"]][0]
        assert me["entry"] == "entry_rocket"

    def test_ai_duel_second_bot_409(self, s):
        u = new_uid()
        d, b, _ = self._ai(s, u)
        assert b.status_code == 200
        assert s.post(f"{API}/duels/{d['id']}/bot", json={}, headers=H(u)).status_code == 409

    def test_ai_duel_code_not_joinable(self, s):
        u = new_uid()
        d, b, _ = self._ai(s, u)
        assert b.status_code == 200
        u2 = new_uid()
        r = s.post(f"{API}/duels/join", json={"code": d["code"], "name": "TEST_x"}, headers=H(u2))
        assert r.status_code == 404

    def test_ai_duel_answer_card1(self, s):
        u = new_uid()
        _, b, _ = self._ai(s, u)
        v = b.json()
        time.sleep(max(0, v["start_at"] - v["server_now"]) + 0.6)
        g = s.get(f"{API}/duels/{v['id']}", headers=H(u)).json()
        assert g["status"] in ("ready", "live"), g["status"]
        r = s.post(f"{API}/duels/{v['id']}/answer", json={"index": 0, "choice": 0, "outcome": "answer"}, headers=H(u))
        assert r.status_code == 200, r.text
        g = s.get(f"{API}/duels/{v['id']}", headers=H(u)).json()
        me = [p for p in g["players"] if p["you"]][0]
        assert me["answered"] == 1

    def test_ai_duel_chapter(self, s):
        u = new_uid()
        cards = s.get(f"{API}/cards", params={"subject": "Physics", "limit": 1}).json()
        ch = (cards.get("items") or cards.get("cards") or [{}])[0].get("chapter")
        if not ch:
            pytest.skip("no chapter")
        _, b, _ = self._ai(s, u, "Physics", ch)
        assert b.status_code == 200 and b.json()["chapter"] == ch

    def test_invite_and_random_still_work(self, s):
        u = new_uid()
        r = s.post(f"{API}/duels", json={"subject": "Physics", "chapter": None, "mode": "invite", "name": "TEST_i", "request_id": uuid.uuid4().hex}, headers=H(u))
        assert r.status_code == 200 and r.json()["mode"] == "invite" and len(r.json()["code"]) == 6
        u2 = new_uid()
        r2 = s.post(f"{API}/duels", json={"subject": "Mathematics", "chapter": None, "mode": "random", "name": "TEST_r", "request_id": uuid.uuid4().hex}, headers=H(u2))
        assert r2.status_code == 200 and r2.json()["mode"] == "random"

    def test_mode_ai_rejected_by_api(self, s):
        # backend accepts only random/invite; frontend maps ai -> invite+bot
        u = new_uid()
        r = s.post(f"{API}/duels", json={"subject": "Physics", "chapter": None, "mode": "ai", "name": "TEST_a", "request_id": uuid.uuid4().hex}, headers=H(u))
        assert r.status_code == 422
