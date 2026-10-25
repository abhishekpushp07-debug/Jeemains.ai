# Iteration 22: PLAY (random) vs seated arena opponent pays/counts like a normal duel; sharpshooter needs 25+ answered.
import os, time, uuid, pytest, requests
from dotenv import load_dotenv
from pymongo import MongoClient

load_dotenv("/app/frontend/.env"); load_dotenv("/app/backend/.env")
API = os.environ["EXPO_PUBLIC_BACKEND_URL"].rstrip("/") + "/api/rf"
DB = MongoClient(os.environ["MONGO_URL"])[os.environ["DB_NAME"]]


def H(u):
    return {"X-RF-User": u}


@pytest.fixture
def uid():
    u = "TEST-" + uuid.uuid4().hex[:16]
    yield u
    DB.rf_duels.delete_many({"players.uid": u})
    for c in ("rf_profiles", "rf_sessions", "rf_rewards", "rf_game"):
        DB[c].delete_many({"$or": [{"uid": u}, {"user_id": u}]})


def seated_duel(u, subject="Physics"):
    d = requests.post(f"{API}/duels", headers=H(u), json={"subject": subject, "chapter": None, "mode": "random", "name": "TEST_me", "request_id": uuid.uuid4().hex}).json()
    if d["status"] == "waiting":
        d = requests.post(f"{API}/duels/{d['id']}/bot", headers=H(u), json={}).json()
    assert d["status"] == "ready"
    time.sleep(max(0, d["start_at"] - d["server_now"]) + 0.3)
    raw = DB.rf_duels.find_one({"id": d["id"]})
    cards = {c["id"]: c for c in DB.rf_cards.find({"id": {"$in": raw["card_ids"]}})}
    return d, raw, cards


def play(u, d, raw, cards, n_correct, rest="skipped"):
    for i in range(len(raw["card_ids"])):
        if i < n_correct:
            body = {"index": i, "choice": cards[raw["card_ids"][i]]["answer"], "outcome": "answer", "ms": 1500}
        else:
            body = {"index": i, "choice": None, "outcome": rest, "ms": 300}
        r = requests.post(f"{API}/duels/{d['id']}/answer", headers=H(u), json=body)
        assert r.status_code == 200, r.text
    time.sleep(1.2)
    return requests.get(f"{API}/duels/{d['id']}", headers=H(u)).json()


class TestSeatedWinPaysLikeDuel:
    def test_full_win_bonus_record_counters(self, uid):
        p0 = requests.get(f"{API}/profile", headers=H(uid)).json()
        d, raw, cards = seated_duel(uid)
        g = play(uid, d, raw, cards, 30)
        assert g["status"] == "finished"
        assert g["winner"] == g["you"]
        rw = g["reward"]
        print("reward", rw.get("xp"), rw.get("coins"))
        # 30 correct * 2 + 50 win + 30 flawless
        assert rw["coins"] == 30 * 2 + 50 + 30
        p1 = requests.get(f"{API}/profile", headers=H(uid)).json()
        assert p1["wins"] == p0.get("wins", 0) + 1
        assert p1["duels"] == p0.get("duels", 0) + 1
        assert "first_win" in [b["id"] for b in p1.get("badges", []) if b.get("earned")]
        items = requests.get(f"{API}/duels", headers=H(uid)).json()["items"]
        assert items and items[0]["id"] == d["id"] and items[0]["won"] is True

    def test_reward_idempotent_on_repeat_get(self, uid):
        d, raw, cards = seated_duel(uid)
        g = play(uid, d, raw, cards, 3)
        c1 = requests.get(f"{API}/profile", headers=H(uid)).json()["coins"]
        requests.get(f"{API}/duels/{d['id']}", headers=H(uid))
        c2 = requests.get(f"{API}/profile", headers=H(uid)).json()["coins"]
        assert c1 == c2
        assert g["reward"]["coins"] == 3 * 2  # under 5 correct: no win bonus (anti skip-farming)

    def test_zero_score_is_not_a_win(self, uid):
        p0 = requests.get(f"{API}/profile", headers=H(uid)).json()
        d, raw, cards = seated_duel(uid)
        g = play(uid, d, raw, cards, 0)
        assert g["winner"] != g.get("you", "you")  # decided by score: 0 correct never wins (opponent plays its natural game)
        print("tie_break flag on 0-0:", g.get("tie_break"))
        p1 = requests.get(f"{API}/profile", headers=H(uid)).json()
        assert p1.get("wins", 0) == p0.get("wins", 0)
        items = requests.get(f"{API}/duels", headers=H(uid)).json()["items"]
        assert items[0]["won"] is False and items[0]["tie"] is False  # iter25: all-skip vs natural opponent score is a loss, not a tie


class TestSharpshooter:
    def _badges(self, uid):
        p = requests.get(f"{API}/profile", headers=H(uid)).json()
        return [b["id"] for b in p.get("badges", []) if b.get("earned")], p

    def test_one_correct_then_forfeit_no_badge(self, uid):
        d, raw, cards = seated_duel(uid)
        r = requests.post(f"{API}/duels/{d['id']}/answer", headers=H(uid), json={"index": 0, "choice": cards[raw["card_ids"][0]]["answer"], "outcome": "answer", "ms": 1000})
        assert r.status_code == 200
        requests.post(f"{API}/duels/{d['id']}/forfeit", headers=H(uid), json={})
        time.sleep(1.5)
        requests.get(f"{API}/duels/{d['id']}", headers=H(uid))
        b, p = self._badges(uid)
        print("badges after 1 correct + forfeit:", b, p.get("badges"))
        assert "sharpshooter" not in b

    def test_25_correct_gets_badge(self, uid):
        d, raw, cards = seated_duel(uid)
        play(uid, d, raw, cards, 25)
        b, p = self._badges(uid)
        print("badges after 25/30:", b)
        assert "sharpshooter" in b
