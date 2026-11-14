"""Iteration 69: Cheer Squads (levels by cup wins, buy with diamonds, equip), squad on the player profile, squad art route,
and the diamonds paid to Knockout Cup champions / runners-up. Throwaway TEST-i65-* players (iteration 65 helper)."""
import os
import sys

sys.path.insert(0, os.path.dirname(__file__))
from test_iter65_cup_night_badla import _run  # noqa: E402

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from cups import cup_gems  # noqa: E402
from squads import squad_of  # noqa: E402


def test_cup_gems_table():
    real8 = {"players": [{}] * 8}
    assert cup_gems(real8, 1, 1) == {"red": 1} and cup_gems(real8, 1, 2) == {}  # practice cup: one red for the champion
    assert cup_gems(real8, 3, 1) == {"red": 3, "blue": 2} and cup_gems(real8, 3, 2) == {"red": 2}
    assert cup_gems({"players": [{}] * 4}, 2, 1) == {"red": 3}
    night = cup_gems({"players": [{}] * 16, "night": "2026-11-14"}, 9, 1)
    assert night == {"blue": 3, "emerald": 2, "gold": 1}  # Cup Night pays the most
    assert cup_gems({"players": [{}] * 16, "night": "x"}, 9, 2) == {"blue": 2, "red": 2}


def test_squad_of_levels():
    assert squad_of({})["level"] == 1
    assert squad_of({"cups_won": 3})["id"] == "squad_gold"  # best one opened by wins
    assert squad_of({"cups_won": 16})["id"] == "squad_legend"
    assert squad_of({"cups_won": 16, "squad": "squad_royal"})["id"] == "squad_royal"  # the one they picked
    assert squad_of({"cups_won": 1, "squad": "squad_legend"})["id"] == "squad_rookie"  # picked but not theirs: best they have
    assert squad_of({"cups_won": 1, "owned": ["squad_legend"]})["id"] == "squad_legend"  # bought early


def test_squads_api():
    _run(_squads, 2)


async def _squads(db, api, u):
    a, b = u[0], u[1]
    r = await api.get("/squads", a)
    assert r.status_code == 200
    d = r.json()
    assert [s["level"] for s in d["items"]] == [1, 2, 3, 4] and d["equipped"] == "squad_rookie" and d["cups_won"] == 0
    assert not any(s["unlocked"] for s in d["items"]) and d["items"][1]["need"] == 3
    # equip needs the squad to be opened
    assert (await api.post("/squads/equip", a, {"id": "squad_gold"})).status_code == 409
    # buying needs the diamonds
    r = await api.post("/squads/buy", a, {"id": "squad_gold"})
    assert r.status_code == 409 and "Not enough diamonds" in r.json()["detail"]
    assert (await api.post("/squads/buy", a, {"id": "squad_rookie"})).status_code == 404  # not for sale
    await db.rf_profiles.update_one({"uid": a["uid"]}, {"$set": {"diamonds": {"red": 9, "blue": 2}}})
    r = await api.post("/squads/buy", a, {"id": "squad_gold"})
    assert r.status_code == 200
    d = r.json()
    gold = next(s for s in d["items"] if s["id"] == "squad_gold")
    assert gold["unlocked"] and gold["bought"] and d["equipped"] == "squad_gold" and d["diamonds"]["red"] == 1 and d["diamonds"]["blue"] == 0
    assert (await api.post("/squads/buy", a, {"id": "squad_gold"})).status_code == 409  # bought once
    p = await db.rf_profiles.find_one({"uid": a["uid"]})
    assert p["diamonds_spent"]["red"] == 8 and "squad_gold" in p["owned"]
    # wins open levels; equip any opened one
    await db.rf_profiles.update_one({"uid": a["uid"]}, {"$set": {"cups_won": 8, "cups_real": 2}})
    d = (await api.post("/squads/equip", a, {"id": "squad_royal"})).json()
    assert d["equipped"] == "squad_royal" and next(s for s in d["items"] if s["id"] == "squad_royal")["unlocked"]
    # the profile shows the squad that dances for this champion
    prof = (await api.get(f"/players/{a['pid']}", b)).json()
    assert prof["squad"] == {"id": "squad_royal", "level": 3, "title": "Royal Sapphire"}
    assert "squad" not in (await api.get(f"/players/{b['pid']}", a)).json()  # no crown, no squad


def test_squad_art_route():
    import httpx
    from test_rf_phase3 import BASE
    with httpx.Client(base_url=BASE, timeout=30) as s:
        r = s.get("/art/squad3_a1.webp")  # public: art only
        assert r.status_code == 200 and r.headers["content-type"] == "image/webp" and "immutable" in r.headers["cache-control"]
        assert s.get("/art/squad1_a1.webp").status_code == 404  # level 1 ships inside the app
        assert s.get("/art/server.py").status_code == 404
