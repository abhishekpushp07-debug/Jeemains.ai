# Rapid Fire iteration 4: AI Rival duels, coin shop, equip/avatar, daily quests, streak freeze
import os
import uuid
import pytest
import requests
from dotenv import load_dotenv
from pymongo import MongoClient

load_dotenv("/app/frontend/.env")
load_dotenv("/app/backend/.env")
BASE_URL = os.environ.get("EXPO_PUBLIC_BACKEND_URL").rstrip("/")
API = f"{BASE_URL}/api/rf"


def H(u):
    return {"X-RF-User": u}


@pytest.fixture(scope="module")
def s():
    return requests.Session()


@pytest.fixture(scope="module")
def uid():
    u = "TEST-" + uuid.uuid4().hex[:16]
    yield u
    db = MongoClient(os.environ["MONGO_URL"])[os.environ["DB_NAME"]]
    db.rf_profiles.delete_many({"uid": u})
    db.rf_awards.delete_many({"uid": u})
    db.rf_sessions.delete_many({"user_id": u})
    db.rf_duels.delete_many({"players.uid": u})


def solo_all_correct(s, uid):
    r = s.post(f"{API}/sessions", json={"subject": "Physics", "count": 30, "request_id": uuid.uuid4().hex}, headers=H(uid))
    assert r.status_code == 200, r.text
    d = r.json()
    res = [{"card_id": c["id"], "outcome": "correct", "choice": c["answer"], "ms": 2000} for c in d["cards"]]
    r = s.post(f"{API}/sessions/{d['id']}/complete", json={"results": res}, headers=H(uid))
    assert r.status_code == 200, r.text
    return r.json()["reward"]


# ---------- AI rival duel ----------
class TestBotDuel:
    def test_bot_duel_full(self, s, uid):
        import time
        r = s.post(f"{API}/duels", json={"subject": "Physics", "mode": "random", "name": "TEST_Bot", "request_id": uuid.uuid4().hex}, headers=H(uid))
        assert r.status_code == 200, r.text
        d = r.json()
        assert d["status"] == "waiting"
        did = d["id"]
        r = s.post(f"{API}/duels/{did}/bot", headers=H(uid))
        assert r.status_code == 200, r.text
        d = r.json()
        assert d["status"] == "ready" and d["vs_bot"] is True
        bot = d["players"][1]
        assert bot["bot"] is True and bot["name"] and bot["avatar"]
        print("bot:", bot["name"], bot["avatar"], bot.get("frame"), bot.get("entry"))
        # second bot call rejected
        assert s.post(f"{API}/duels/{did}/bot", headers=H(uid)).status_code == 409
        wait = d["start_at"] - d["server_now"]
        time.sleep(max(0, wait) + 0.2)
        total = d["total"]
        my = 0
        max_bot = 0
        for i in range(total):
            # pick choice 0, learn answer, so first is random; then subsequent cards use 0 too -> mixed
            r = s.post(f"{API}/duels/{did}/answer", json={"index": i, "choice": 0, "outcome": "answer", "ms": 1000}, headers=H(uid))
            assert r.status_code == 200, (i, r.text)
            a = r.json()
            assert "answer" in a
            my = a["score"]
            if i % 6 == 0 or i == total - 1:
                time.sleep(0.5)
                g = s.get(f"{API}/duels/{did}", headers=H(uid)).json()
                b = next(p for p in g["players"] if p["bot"])
                me = next(p for p in g["players"] if p["you"])
                max_bot = max(max_bot, b["score"])
                print(f"i={i} me={me['score']} bot={b['score']} status={g['status']}")
                assert b["score"] < me["score"] or (me["score"] == 0 and b["score"] == 0), "bot must stay below human"
        g = s.get(f"{API}/duels/{did}", headers=H(uid)).json()
        assert g["status"] == "finished", g["status"]
        print("final my", my, "winner", g["winner"], "reward", g["reward"])
        if my > 0:
            assert g["winner"] == uid
            assert g["reward"]["coins"] >= my * 2 + 50  # iter22: seated-opponent wins pay like a normal duel (+50 win bonus)
        b = next(p for p in g["players"] if p["bot"])
        assert b["score"] < my or my == 0

    def test_bot_on_foreign_duel_rejected(self, s, uid):
        r = s.post(f"{API}/duels", json={"subject": "Chemistry", "mode": "random", "name": "TEST_Bot", "request_id": uuid.uuid4().hex}, headers=H(uid))
        did = r.json()["id"]
        r2 = s.post(f"{API}/duels/{did}/bot", headers=H("TEST-other-" + uuid.uuid4().hex[:8]))
        assert r2.status_code == 409
        s.post(f"{API}/duels/{did}/cancel", headers=H(uid))


# ---------- shop / quests ----------
class TestShop:
    def test_shop_list(self, s, uid):
        r = s.get(f"{API}/shop", headers=H(uid))
        assert r.status_code == 200
        d = r.json()
        slots = {i["slot"] for i in d["items"]}
        assert slots == {"powerup", "frame", "entry", "theme"}
        assert len(d["avatars"]) >= 10

    def test_buy_insufficient_409(self, s):
        u = "TEST-poor-" + uuid.uuid4().hex[:8]
        r = s.post(f"{API}/shop/buy", json={"item_id": "streak_freeze"}, headers=H(u))
        assert r.status_code == 409, r.text
        assert "Not enough coins" in r.json()["detail"]

    def test_buy_unknown_404(self, s, uid):
        assert s.post(f"{API}/shop/buy", json={"item_id": "nope"}, headers=H(uid)).status_code == 404

    def test_earn_claim_buy_equip(self, s, uid):
        rw = solo_all_correct(s, uid)
        print("reward1", rw)
        p = s.get(f"{API}/profile", headers=H(uid)).json()
        assert {"quests", "equipped", "avatar", "freezes"} <= set(p)
        q = {x["id"]: x for x in p["quests"]}
        assert q["q_sprint"]["done"] and q["q_correct"]["done"] and not q["q_sprint"]["claimed"]
        coins0 = p["coins"]
        # claim duel quest only if done (depends on bot duel result above)
        r = s.post(f"{API}/quests/claim", json={"id": "q_sprint"}, headers=H(uid))
        assert r.status_code == 200 and r.json()["coins"] == 30
        assert s.post(f"{API}/quests/claim", json={"id": "q_sprint"}, headers=H(uid)).status_code == 409
        assert s.post(f"{API}/quests/claim", json={"id": "q_correct"}, headers=H(uid)).status_code == 200
        p = s.get(f"{API}/profile", headers=H(uid)).json()
        assert p["coins"] == coins0 + 70
        assert {x["id"]: x for x in p["quests"]}["q_sprint"]["claimed"] is True
        # make sure enough for frame_gold(250) + freeze(120)
        while p["coins"] < 400:
            solo_all_correct(s, uid)
            p = s.get(f"{API}/profile", headers=H(uid)).json()
        c = p["coins"]
        # equip unowned -> 403
        assert s.post(f"{API}/shop/equip", json={"slot": "frame", "item_id": "frame_gold"}, headers=H(uid)).status_code == 403
        r = s.post(f"{API}/shop/buy", json={"item_id": "frame_gold"}, headers=H(uid))
        assert r.status_code == 200, r.text
        assert r.json()["coins"] == c - 250 and "frame_gold" in r.json()["owned"]
        r = s.post(f"{API}/shop/buy", json={"item_id": "frame_gold"}, headers=H(uid))
        assert r.status_code == 409 and "already own" in r.json()["detail"]
        f0 = r_f = s.get(f"{API}/shop", headers=H(uid)).json()["freezes"]
        r = s.post(f"{API}/shop/buy", json={"item_id": "streak_freeze"}, headers=H(uid))
        assert r.status_code == 200 and r.json()["freezes"] == f0 + 1
        # equip owned / wrong slot
        assert s.post(f"{API}/shop/equip", json={"slot": "entry", "item_id": "frame_gold"}, headers=H(uid)).status_code == 403
        assert s.post(f"{API}/shop/equip", json={"slot": "bogus", "item_id": "frame_gold"}, headers=H(uid)).status_code == 400
        assert s.post(f"{API}/shop/equip", json={"slot": "frame", "item_id": "frame_gold"}, headers=H(uid)).status_code == 200
        assert s.get(f"{API}/profile", headers=H(uid)).json()["equipped"]["frame"] == "frame_gold"
        # unequip
        assert s.post(f"{API}/shop/equip", json={"slot": "frame", "item_id": None}, headers=H(uid)).status_code == 200
        assert s.get(f"{API}/profile", headers=H(uid)).json()["equipped"]["frame"] is None
        _ = r_f

    def test_avatar(self, s, uid):
        assert s.post(f"{API}/profile/avatar", json={"avatar": "av_panda"}, headers=H(uid)).status_code == 200  # free starter
        assert s.get(f"{API}/profile", headers=H(uid)).json()["avatar"] == "av_panda"
        assert s.post(f"{API}/profile/avatar", json={"avatar": "av_galaxy"}, headers=H(uid)).status_code == 403  # paid, not owned
        assert s.post(f"{API}/profile/avatar", json={"avatar": "hacker"}, headers=H(uid)).status_code == 400

    def test_claim_not_done(self, s):
        u = "TEST-new-" + uuid.uuid4().hex[:8]
        assert s.post(f"{API}/quests/claim", json={"id": "q_duel"}, headers=H(u)).status_code == 409
        assert s.post(f"{API}/quests/claim", json={"id": "bogus"}, headers=H(u)).status_code == 409
