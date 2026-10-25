# Iteration 24 (updated from iter23): effort rule in gamify.award() - duel win bonus (+50 coins, +60 XP, wins+1) only with correct >= 5;
# all-skip = 0 XP / 0 coins / no duels+1. Seated opponent (duels.simulate_bot) stays just below a student with >=5, else plays its natural score.
# Outcome (winner / GET /duels won flag) must agree with the reward.
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
    for c in ("rf_profiles", "rf_sessions", "rf_rewards", "rf_game", "rf_awards"):
        DB[c].delete_many({"$or": [{"uid": u}, {"user_id": u}]})


def seated_duel(u):
    d = requests.post(f"{API}/duels", headers=H(u), json={"subject": "Physics", "chapter": None, "mode": "random", "name": "TEST_me", "request_id": uuid.uuid4().hex}).json()
    if d["status"] == "waiting":
        d = requests.post(f"{API}/duels/{d['id']}/bot", headers=H(u), json={}).json()
    assert d["status"] == "ready"
    time.sleep(max(0, d["start_at"] - d["server_now"]) + 0.3)
    raw = DB.rf_duels.find_one({"id": d["id"]})
    cards = {c["id"]: c for c in DB.rf_cards.find({"id": {"$in": raw["card_ids"]}})}
    return d, raw, cards


def wrong_choice(card):
    n = len(card.get("options") or card.get("choices") or [0, 0])
    return (int(card["answer"]) + 1) % max(2, n)


def answer(u, d, raw, cards, i, kind):
    cid = raw["card_ids"][i]
    body = {"index": i, "choice": cards[cid]["answer"] if kind == "c" else wrong_choice(cards[cid]) if kind == "w" else None,
            "outcome": "skipped" if kind == "s" else "answer", "ms": 1500}
    r = requests.post(f"{API}/duels/{d['id']}/answer", headers=H(u), json=body)
    assert r.status_code == 200, r.text


def play(u, d, raw, cards, n_correct, n_wrong=0):
    for i in range(len(raw["card_ids"])):
        answer(u, d, raw, cards, i, "c" if i < n_correct else "w" if i < n_correct + n_wrong else "s")
    time.sleep(1.2)
    return requests.get(f"{API}/duels/{d['id']}", headers=H(u)).json()


def prof(u):
    return requests.get(f"{API}/profile", headers=H(u)).json()


def opp(g):
    return next(p for p in g["players"] if not p["you"])


def listed(u, did):
    return next(x for x in requests.get(f"{API}/duels", headers=H(u)).json()["items"] if x["id"] == did)


class TestEffortRule:
    def test_1_correct_29_skips_is_loss_no_bonus(self, uid):
        p0 = prof(uid)
        d, raw, cards = seated_duel(uid)
        g = play(uid, d, raw, cards, 1)
        rw, o = g["reward"], opp(g)
        print("1+29skip: winner", g["winner"], "you", g["you"], "opp score", o["score"], "reward", rw["xp"], rw["coins"])
        assert rw["coins"] == 2 and rw["xp"] == 30
        p1 = prof(uid)
        assert p1["wins"] == p0.get("wins", 0) and p1["duels"] == p0.get("duels", 0) + 1
        assert o["score"] > 1, "opponent should play its natural score"
        assert g["winner"] != g["you"], "result screen would say 'You won!' with no win bonus"
        assert listed(uid, g["id"])["won"] is False

    def test_1_correct_9_wrong_no_bonus_and_loss(self, uid):
        p0 = prof(uid)
        d, raw, cards = seated_duel(uid)
        g = play(uid, d, raw, cards, 1, 9)
        rw = g["reward"]
        print("1c+9w: winner==you", g["winner"] == g["you"], "opp", opp(g)["score"], "reward", rw["xp"], rw["coins"])
        assert rw["coins"] == 2 and rw["xp"] == 30
        assert prof(uid)["wins"] == p0.get("wins", 0)
        assert g["winner"] != g["you"]
        assert listed(uid, g["id"])["won"] is False

    def test_all_skips_zero_reward_and_loss(self, uid):
        p0 = prof(uid)
        d, raw, cards = seated_duel(uid)
        g = play(uid, d, raw, cards, 0)
        rw = g["reward"]
        print("all skip: winner", g["winner"], "opp", opp(g)["score"], "reward", rw)
        assert rw["coins"] == 0 and rw["xp"] == 0 and rw["played"] is False
        p1 = prof(uid)
        assert p1["duels"] == p0.get("duels", 0) and p1["wins"] == p0.get("wins", 0)
        assert g["winner"] != g["you"]
        assert g["winner"] != "tie", "opponent has a natural score > 0, so all-skip should be a loss, not a tie"

    def test_4_correct_boundary_no_bonus(self, uid):
        d, raw, cards = seated_duel(uid)
        g = play(uid, d, raw, cards, 4)
        rw = g["reward"]
        print("4c: winner==you", g["winner"] == g["you"], "opp", opp(g)["score"], "reward", rw["xp"], rw["coins"])
        assert rw["coins"] == 8 and rw["xp"] == 60
        assert g["winner"] != g["you"]

    def test_5_correct_boundary_wins_with_bonus(self, uid):
        p0 = prof(uid)
        d, raw, cards = seated_duel(uid)
        g = play(uid, d, raw, cards, 5)
        rw, o = g["reward"], opp(g)
        print("5c: winner==you", g["winner"] == g["you"], "opp", o["score"], "reward", rw["xp"], rw["coins"])
        assert g["winner"] == g["you"] and o["score"] == 4
        assert rw["coins"] == 10 + 50 and rw["xp"] == 50 + 60
        p1 = prof(uid)
        assert p1["wins"] == p0.get("wins", 0) + 1 and p1["duels"] == p0.get("duels", 0) + 1
        assert listed(uid, g["id"])["won"] is True

    def test_10_correct_win_pays_bonus(self, uid):
        p0 = prof(uid)
        d, raw, cards = seated_duel(uid)
        g = play(uid, d, raw, cards, 10)
        rw, o = g["reward"], opp(g)
        assert g["winner"] == g["you"] and o["score"] <= 9
        assert rw["coins"] == 70 and rw["xp"] == 185
        assert prof(uid)["wins"] == p0.get("wins", 0) + 1
        assert listed(uid, g["id"])["won"] is True

    def test_opponent_score_monotonic_when_crossing_5(self, uid):
        # Probe: opponent runs naturally while student < 5, then is clamped to student-1 -> must never visibly drop.
        d, raw, cards = seated_duel(uid)
        time.sleep(60)
        for i in range(4):
            answer(uid, d, raw, cards, i, "c")
        s1 = opp(requests.get(f"{API}/duels/{d['id']}", headers=H(uid)).json())["score"]
        answer(uid, d, raw, cards, 4, "c")
        s2 = opp(requests.get(f"{API}/duels/{d['id']}", headers=H(uid)).json())["score"]
        print("opp score before 5th correct:", s1, "after:", s2)
        requests.post(f"{API}/duels/{d['id']}/forfeit", headers=H(uid))
        assert s2 >= s1, f"opponent score dropped {s1} -> {s2} on screen"
