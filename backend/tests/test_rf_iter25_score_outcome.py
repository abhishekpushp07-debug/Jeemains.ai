# Iteration 25: seated-opponent duels decided by score (duels.winner) + monotonic opponent score (duels.simulate_bot).
# Result (winner), list flag (GET /duels won/tie), reward (+50 bonus) and profile wins must all agree.
import os, time, uuid, requests
from test_rf_iter23_anti_farming import API, DB, H, seated_duel, answer, opp, prof, listed, uid  # noqa: F401


def get(u, d):
    return requests.get(f"{API}/duels/{d['id']}", headers=H(u)).json()


def me_of(g):
    return next(p for p in g["players"] if p["you"])


class TestScoreOutcome:
    # Opponent ahead when student hits 5 -> held (never drops), student overtakes -> opponent stays one behind; student wins with bonus
    def test_hold_then_overtake_win(self, uid):
        p0 = prof(uid)
        d, raw, cards = seated_duel(uid)
        time.sleep(55)
        series = []
        total = len(raw["card_ids"])
        for i in range(total):
            answer(uid, d, raw, cards, i, "c")
            g = get(uid, d)
            series.append((me_of(g)["score"], opp(g)["score"]))
        time.sleep(1.2)
        g = get(uid, d)
        print("series (me, opp):", series, "final", me_of(g)["score"], opp(g)["score"], "winner==you", g["winner"] == g["you"])
        opps = [s[1] for s in series] + [opp(g)["score"]]
        assert all(b >= a for a, b in zip(opps, opps[1:])), f"opponent score dropped: {opps}"
        # once the student is ahead with >=5, opponent never exceeds me-1
        for m, o in series:
            if m >= 5 and o < m:
                assert o <= m - 1
        assert g["status"] == "finished"
        assert me_of(g)["score"] > opp(g)["score"]
        assert g["winner"] == g["you"]
        assert g["reward"]["coins"] == total * 2 + 50 + (30 if total >= 10 else 0)
        assert listed(uid, g["id"])["won"] is True
        assert prof(uid)["wins"] == p0.get("wins", 0) + 1

    # Opponent ahead, student gets exactly 5 then skips the rest -> opponent holds its lead -> loss, no bonus, record agrees
    def test_five_correct_but_behind_is_loss(self, uid):
        p0 = prof(uid)
        d, raw, cards = seated_duel(uid)
        time.sleep(55)
        for i in range(5):
            answer(uid, d, raw, cards, i, "c")
        o_mid = opp(get(uid, d))["score"]
        for i in range(5, len(raw["card_ids"])):
            answer(uid, d, raw, cards, i, "s")
        time.sleep(1.2)
        g = get(uid, d)
        o = opp(g)["score"]
        print("5c then skips: opp at 5th", o_mid, "opp final", o, "winner", "you" if g["winner"] == g["you"] else g["winner"], "reward", g["reward"]["xp"], g["reward"]["coins"])
        assert o >= o_mid
        it = listed(uid, g["id"])
        if o > 5:
            assert g["winner"] != g["you"] and g["winner"] != "tie"
            assert g["reward"]["coins"] == 10 and g["reward"]["xp"] == 70
            assert it["won"] is False and it["tie"] is False
            assert prof(uid)["wins"] == p0.get("wins", 0)
        elif o == 5:
            assert g["winner"] == "tie" and it["tie"] is True and g["reward"]["coins"] == 10
        else:
            assert g["winner"] == g["you"] and it["won"] is True and g["reward"]["coins"] == 60

    # Forfeit -> opponent wins regardless of score
    def test_forfeit_is_loss(self, uid):
        p0 = prof(uid)
        d, raw, cards = seated_duel(uid)
        for i in range(6):
            answer(uid, d, raw, cards, i, "c")
        requests.post(f"{API}/duels/{d['id']}/forfeit", headers=H(uid))
        time.sleep(1.2)
        g = get(uid, d)
        print("forfeit: status", g["status"], "winner==you", g["winner"] == g["you"], "reward", g.get("reward"))
        assert g["status"] == "finished"
        assert g["winner"] != g["you"]
        assert listed(uid, g["id"])["won"] is False
        assert prof(uid)["wins"] == p0.get("wins", 0)
