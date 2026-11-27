"""Rapid Fire, 27 Nov 2026: a student may tick any number of chapters (before: 5 picks at most).

What must hold:
  * a list of up to 5 picks is named, keyed and dealt exactly as before (old apps, "PCM Mixed", every stored match);
  * a longer list is accepted by sprints, matches, challenge rooms and cups, every ticked chapter gets an even share,
    and no chapter is left out because of its place in the alphabet;
  * two players with the same long list still meet in a Quick Match (the list is matched by a short digest).

The live part uses TEST-prefixed throwaway players (as test_rf_phase3.py does) and removes every document it made.
"""
import os
import random
import sys
import uuid
from collections import Counter

import pytest
from fastapi import HTTPException

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
sys.path.insert(0, os.path.dirname(__file__))
from test_rf_phase3 import PCM, run

from rapid_deck import choose
from scope import CLASSIC_PICKS, MAX_PICKS, label_of, normalise, scope_fields


def old_key(picks):
    """The key of a match exactly as it was written before this change."""
    return "|".join(f"{p['subject']}:{p['chapter'] or '*'}" for p in picks)


def chapters(subject, n, start=0):
    return [{"subject": subject, "chapter": f"{subject[:2]} chapter {k:02d}"} for k in range(start, start + n)]


# ---------- the rules, without a server ----------
def test_a_list_of_up_to_five_is_named_and_keyed_as_before():
    lists = [normalise(PCM), normalise([{"subject": "Physics"}]), normalise(chapters("Physics", 1)), normalise(chapters("Physics", 3) + chapters("Chemistry", 2)),
             normalise([{"subject": "Mathematics"}] + chapters("Chemistry", 4)), normalise([{"subject": "English"}, {"subject": "Logical Reasoning"}])]
    assert [label_of(p) for p in lists] == ["PCM Mixed", "Mixed Physics", "Ph chapter 00", "Ph chapter 00 +4 more", "Mixed Maths +4 more", "Mixed English + Reasoning"]
    for picks in lists:
        assert len(picks) <= CLASSIC_PICKS and scope_fields(picks)["scope_key"] == old_key(picks)


def test_a_longer_list_has_its_own_name_and_a_short_key():
    many = normalise(chapters("Physics", 20) + chapters("Chemistry", 13))
    assert label_of(many) == "33 chapters · Physics + Chemistry"
    assert label_of(normalise(chapters("Physics", 2) + chapters("Chemistry", 2) + chapters("Mathematics", 2))) == "6 chapters · PCM"
    assert label_of(normalise(chapters("Logical Reasoning", 6))) == "6 chapters · Reasoning"
    assert label_of(normalise([{"subject": "Physics"}] + chapters("Chemistry", 6))) == "Mixed Physics +6 more"  # a whole subject first: the old wording
    key = scope_fields(many)["scope_key"]
    assert key.startswith("#") and len(key) == 41 and len(old_key(many)) > 600
    shuffled = many[:]
    random.shuffle(shuffled)
    assert scope_fields(normalise(shuffled))["scope_key"] == key  # the same chapters in any order are the same battleground
    assert scope_fields(normalise(many[:-1]))["scope_key"] != key


def test_the_ceiling_is_above_the_whole_bank_and_is_enforced():
    assert MAX_PICKS >= 110 and len(normalise(chapters("Physics", MAX_PICKS))) == MAX_PICKS
    with pytest.raises(HTTPException) as err:
        normalise(chapters("Physics", MAX_PICKS + 1))
    assert err.value.status_code == 400


def pools(sizes):
    """{subject: {chapter: [[card id, prompt fingerprint], ...]}} with `sizes[subject]` chapters of 40 cards each."""
    return {s: {f"{s[:2]} chapter {k:02d}": [[f"{s}-{k}-{i}", f"{s}-{k}-{i}"] for i in range(40)] for k in range(n)} for s, n in sizes.items()}


def dealt(picks, count, bank):
    """How many cards each chapter got in one round."""
    return Counter(card.rsplit("-", 1)[0] for card in choose(bank, picks, count))


def test_the_old_lists_are_dealt_in_the_old_order():
    bank = pools({"Physics": 8, "Chemistry": 8, "Mathematics": 8})
    four = normalise(chapters("Physics", 2) + chapters("Chemistry", 2))
    for _ in range(20):  # 30 cards over 4 picks: 8, 8, 7, 7, the extra card always to the first picks, as before
        assert [n for _, n in sorted(dealt(four, 30, bank).items(), key=lambda kv: (kv[0].split("-")[0] != "Physics", kv[0]))] == [8, 8, 7, 7]
        ids = choose(bank, normalise(PCM), 30)
        assert [i.split("-")[0] for i in ids] == ["Physics", "Chemistry", "Mathematics"] * 10  # PCM Mixed: the same turn-taking, 10 cards each


def test_every_ticked_chapter_gets_an_even_share():
    bank = pools({"Physics": 30, "Chemistry": 23, "Mathematics": 26})
    twelve = normalise(chapters("Physics", 12))
    for _ in range(20):
        got = dealt(twelve, 30, bank)
        assert len(got) == 12 and set(got.values()) == {2, 3} and sum(got.values()) == 30
    six = normalise(chapters("Physics", 3) + chapters("Chemistry", 3))
    assert set(dealt(six, 30, bank).values()) == {5}


def test_no_chapter_is_left_out_for_its_place_in_the_alphabet():
    """40 chapters and a 30-card round: one card each for 30 of them. Before the lanes were mixed, the last ten never got one."""
    bank = pools({"Physics": 30, "Chemistry": 23, "Mathematics": 26})
    forty = normalise(chapters("Physics", 20) + chapters("Mathematics", 20))
    seen, runs = Counter(), 400
    for _ in range(runs):
        got = dealt(forty, 30, bank)
        assert len(got) == 30 and set(got.values()) == {1}
        seen.update(got.keys())
    assert len(seen) == 40
    # each chapter is expected in 3 rounds out of 4 (300 of 400); 240 to 360 is far outside chance (sd about 9)
    assert min(seen.values()) > 240 and max(seen.values()) < 360, (min(seen.values()), max(seen.values()))
    last_ten = sum(seen[f"Mathematics-{k}"] for k in range(10, 20))
    assert 2700 < last_ten < 3300  # the ten that used to get nothing


def test_a_chapter_that_has_no_cards_does_not_stop_the_round():
    bank = pools({"Physics": 8})
    picks = normalise(chapters("Physics", 7) + [{"subject": "Physics", "chapter": "No such chapter"}])
    assert sum(dealt(picks, 30, bank).values()) == 30
    with pytest.raises(HTTPException) as err:
        choose(bank, normalise([{"subject": "Physics", "chapter": f"No such chapter {k}"} for k in range(7)]), 30)
    assert err.value.status_code == 400 and "0 unique" in err.value.detail


# ---------- the same through the running server ----------
def test_long_lists_live():
    run(_long_lists)


async def _long_lists(db, api, u, tag):
    a, b, c, d = u["a"], u["b"], u["c"], u["d"]
    cat = (await api.s.get("/catalog", params={"exam": "JEE"})).json()
    names = {s["name"]: [c["name"] for c in s["chapters"] if c["count"]] for s in cat["subjects"]}
    assert sum(len(v) for v in names.values()) <= MAX_PICKS  # every chapter of the bank ticked one by one still fits in one request

    async def sprint(picks, count=30):
        return await api.post("/sessions", a, {"picks": picks, "count": count, "request_id": uuid.uuid4().hex})

    # every chapter of Physics but one, and two chapters of Chemistry: 31 picks
    left_out = names["Physics"][0]
    picks = [{"subject": "Physics", "chapter": c} for c in names["Physics"][1:]] + [{"subject": "Chemistry", "chapter": c} for c in names["Chemistry"][:2]]
    r = await sprint(picks)
    assert r.status_code == 200, r.text
    s = r.json()
    got = Counter((c["subject"], c["chapter"]) for c in s["cards"])
    assert s["label"] == f"{len(picks)} chapters · Physics + Chemistry" and len(s["picks"]) == len(picks) and len(s["cards"]) == 30
    assert set(got) <= {(p["subject"], p["chapter"]) for p in picks} and ("Physics", left_out) not in got and set(got.values()) == {1}
    assert len({c["prompt"] for c in s["cards"]}) == 30

    # every chapter of the bank ticked one by one (the longest list the app can send) is played, on 100 cards too
    everything = [{"subject": subject, "chapter": c} for subject, rows in names.items() for c in rows]
    r = await sprint(everything, 100)
    assert r.status_code == 200, r.text
    assert len(r.json()["cards"]) == 100 and r.json()["label"] == f"{len(everything)} chapters · Physics + Chemistry + Maths + English + Reasoning"
    assert (await sprint(everything + [{"subject": "Physics", "chapter": f"Extra {k}"} for k in range(MAX_PICKS - len(everything) + 1)])).status_code == 422

    # a match: the long list is stored, named and given back; its key in the database is the short digest
    duel = (await api.post("/duels", a, {"picks": picks, "mode": "invite", "name": "x", "exam": "JEE", "request_id": uuid.uuid4().hex})).json()
    assert duel["label"] == s["label"] and len(duel["picks"]) == len(picks) and duel["status"] == "waiting"
    stored = await db.rf_duels.find_one({"id": duel["id"]}, {"_id": 0, "scope_key": 1, "label": 1})
    assert stored["scope_key"].startswith("#") and len(stored["scope_key"]) == 41
    await api.post(f"/duels/{duel['id']}/cancel", a)

    # a challenge room and a knockout cup take the long list as well
    await api.befriend(c, d)
    room = (await api.post("/challenges", c, {"pids": [d["pid"]], "picks": picks})).json()
    assert room["label"] == s["label"] and len(room["picks"]) == len(picks)
    cup = await api.post("/cups", d, {"kind": "open", "size": 4, "picks": picks})
    assert cup.status_code == 200, cup.text
    assert cup.json()["label"] == s["label"] and len(cup.json()["picks"]) == len(picks)

    # nothing changed for the lists that existed before
    s = (await sprint(PCM)).json()
    assert s["label"] == "PCM Mixed" and Counter(c["subject"] for c in s["cards"]) == {"Physics": 10, "Chemistry": 10, "Mathematics": 10}
    assert [c["subject"] for c in s["cards"]] == ["Physics", "Chemistry", "Mathematics"] * 10

    # Quick Match: two players with the same chapters (sent in a different order) meet; a different list does not
    body = {"mode": "random", "exam": "JEE", "count": 30}
    first = (await api.post("/duels", a, {**body, "picks": picks, "name": "A", "request_id": uuid.uuid4().hex})).json()
    assert first["status"] == "waiting"
    other = (await api.post("/duels", b, {**body, "picks": picks[:-1], "name": "B", "request_id": uuid.uuid4().hex})).json()
    assert other["status"] == "waiting" and other["id"] != first["id"]
    await api.post(f"/duels/{other['id']}/cancel", b)
    met = (await api.post("/duels", b, {**body, "picks": picks[::-1], "name": "B", "request_id": uuid.uuid4().hex})).json()
    assert met["id"] == first["id"] and met["status"] == "ready" and len(met["players"]) == 2
