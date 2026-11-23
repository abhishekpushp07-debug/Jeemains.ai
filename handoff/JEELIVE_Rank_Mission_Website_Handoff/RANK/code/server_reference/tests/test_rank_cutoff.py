# Cut off tool (POST /api/rank/cutoff, GET /api/rank/cutoff/options) and the scorecard rank as a JEE score.
# The Cut off answers must agree with the tools that were already there: Target marks (the list without a score),
# College predictor (the chance tags) for JEE Main, COMEDK and BITSAT. Read-only, no auth, no DB writes.
# Run:  cd /app/backend && python -m pytest tests/test_rank_cutoff.py -q
import os

import pytest
import requests

BASE_URL = os.environ.get("EXPO_PUBLIC_BACKEND_URL") or os.environ.get("EXPO_BACKEND_URL")
if not BASE_URL:
    for line in open("/app/frontend/.env"):
        if line.startswith("EXPO_PUBLIC_BACKEND_URL="):
            BASE_URL = line.split("=", 1)[1].strip().strip('"')
R = f"{BASE_URL.rstrip('/')}/api/rank"
TAGS = ("safe", "likely", "borderline")
JOSAA = ["R1", "R2", "R3", "R4", "R5", "CSAB 1", "CSAB 2"]


@pytest.fixture(scope="module")
def s():
    x = requests.Session()
    x.headers.update({"Content-Type": "application/json"})
    return x


@pytest.fixture(scope="module")
def opts(s):
    r = s.get(f"{R}/cutoff/options", timeout=30)
    assert r.status_code == 200
    return r.json()


def cut(s, **body):
    r = s.post(f"{R}/cutoff", json=body, timeout=30)
    assert r.status_code == 200, r.text[:200]
    return r.json()


def key_of(opts, exam, title):
    return next(c["key"] for c in opts[exam]["colleges"] if c["title"] == title)


# ---------- options ----------
def test_options_shape(opts):
    assert opts["limit"] == 100
    assert (len(opts["jee"]["colleges"]), len(opts["comedk"]["colleges"]), len(opts["bitsat"]["colleges"])) == (115, 148, 3)
    assert opts["jee"]["score"] == ["marks", "percentile", "rank"] and opts["comedk"]["score"] == ["marks", "rank"] and opts["bitsat"]["score"] == ["marks"]
    assert opts["jee"]["marks"] == [-75, 300] and opts["comedk"]["marks"] == [0, 180] and opts["bitsat"]["marks"] == [-130, 390]
    assert opts["jee"]["profile"] and not opts["comedk"]["profile"] and not opts["bitsat"]["profile"]
    for exam in ("jee", "comedk", "bitsat"):
        for o in opts[exam]["colleges"] + opts[exam]["branches"]:
            assert o["key"] and o["title"] and "sub" in o
    cs = next(b for b in opts["jee"]["branches"] if b["key"] == "Computer Science")
    assert "CSE" in cs["find"] and "Cyber Security" in cs["find"]  # what a student types finds the group


@pytest.mark.parametrize("exam", ["jee", "comedk", "bitsat"])
def test_every_tenth_option_answers(s, opts, exam):
    for by in ("college", "branch"):
        for o in opts[exam]["colleges" if by == "college" else "branches"][::10]:
            d = cut(s, exam=exam, by=by, key=o["key"])
            assert d["rows"] and d["you"] is None and d["eligible"] is None and d["near"] == []
            assert all(r["tag"] is None and len(r["cells"]) == len(d["columns"]) for r in d["rows"])
            assert d["limit"] == (100 if by == "branch" else None) and len(d["rows"]) == (min(100, d["total"]) if by == "branch" else d["total"])


# ---------- JEE Main ----------
@pytest.mark.parametrize("profile", [{}, {"category": "OBC-NCL", "female": True, "state": "Tamil Nadu"}, {"category": "SC", "pwd": True, "state": "Bihar"}])
def test_jee_college_without_score_is_target_marks(s, opts, profile):
    inst = key_of(opts, "jee", "NIT Trichy")
    d = cut(s, exam="jee", by="college", key=inst, **profile)
    t = s.post(f"{R}/target/jee", json={"inst": int(inst), "category": "GEN", "female": False, "pwd": False, "state": None, **profile}).json()
    assert d["columns"] == JOSAA and d["prev_label"] == "2025 R6" and d["metric"] == "rank"
    want = {f"jee-{r['prog']}": r for r in t["rows"]}
    assert {r["id"] for r in d["rows"]} == set(want)
    for r in d["rows"]:
        w = want[r["id"]]
        assert r["path"] == w["path"] and r["rank_type"] == w["rank_type"] and r["seats"] == w["seats"]
        assert r["final"] == {"label": w["final"]["label"], "close": w["final"]["close"]}
        assert r["need"]["marks"] == w["final"]["marks"]["normal"] and r["need"]["level"] == "normal"
        assert [c["close"] for c in r["cells"]] == [c["close"] for c in w["cells"]]


def test_jee_tags_match_college_predictor(s):
    form = {"marks": 200, "level": "normal", "category": "GEN", "female": False, "pwd": False, "state": None, "branches": []}
    p = s.post(f"{R}/predict", json={**form, "segment": "all", "page": 1}).json()
    assert len(p["items"]) == 25
    seen = {}
    for it in p["items"][:12]:
        if it["inst"] not in seen:
            seen[it["inst"]] = cut(s, exam="jee", by="college", key=str(it["inst"]), marks=200)
        row = next(r for r in seen[it["inst"]]["rows"] if r["id"] == f"jee-{it['prog']}")
        assert (row["tag"], row["final"]["close"], row["final"]["label"], row["path"]) == (it["tag"], it["close"], it["round"], it["path"])
    one = next(iter(seen.values()))
    assert one["you"]["rank"]["range"] == p["result"]["crl"] and one["you"]["percentile"] == p["result"]["percentile"]


def test_jee_branch_top_100_and_filter(s):
    a = cut(s, exam="jee", by="branch", key="Computer Science")
    assert a["limit"] == 100 and len(a["rows"]) == 100 and a["total"] > 100 and a["rows"][0]["college"] == "NIT Trichy"
    b = cut(s, exam="jee", by="branch", key="Computer Science", marks=200)
    you = b["you"]
    assert you["source"] == "marks" and sum(you["counts"].values()) == b["eligible"] <= b["total"] == a["total"]
    assert len(b["rows"]) == min(100, b["eligible"]) and all(r["tag"] in TAGS for r in b["rows"])
    assert 0 < len(b["near"]) <= 3 and all(n["tag"] is None and n["gap"] for n in b["near"])
    order = [r["id"] for r in a["rows"]]  # the filtered list keeps the most-wanted-first order
    kept = [r["id"] for r in b["rows"] if r["id"] in order]
    assert kept == [i for i in order if i in set(kept)]


def test_jee_cells_follow_the_tag(s, opts):
    d = cut(s, exam="jee", by="branch", key="Computer Science", rank=7500)
    for r in d["rows"]:
        states = [c.get("state") for c in r["cells"] if c["close"]]
        assert any(x in ("in", "edge") for x in states)  # an eligible row is inside at least one round
        assert all(c.get("state") != "in" for c in r["cells"] if c["label"].startswith("CSAB"))  # CSAB is never a sure seat
        if r["tag"] in ("safe", "likely"):
            assert "in" in states
    jac = cut(s, exam="jee", by="college", key=key_of(opts, "jee", "DTU Delhi"), percentile=99.2, state="Delhi")
    assert jac["columns"] == ["R1", "R2", "R3", "R4"] and jac["prev_label"] is None and all(r["prev"] is None for r in jac["rows"])
    mixed = cut(s, exam="jee", by="branch", key="Computer Science")
    row = next(r for r in mixed["rows"] if r["college"] == "DTU Delhi")
    assert [c.get("na", False) for c in row["cells"]] == [False] * 4 + [True] * 3


def test_jee_score_order_rank_then_percentile_then_marks(s, opts):
    inst = key_of(opts, "jee", "NIT Trichy")
    assert cut(s, exam="jee", by="college", key=inst, rank=7500, percentile=90, marks=100)["you"]["source"] == "rank"
    assert cut(s, exam="jee", by="college", key=inst, percentile=99.5, marks=100)["you"]["source"] == "percentile"
    d = cut(s, exam="jee", by="college", key=inst, rank=7500)
    assert d["you"]["rank"] == {"label": "CRL", "range": [7500, 7500]} and d["you"]["line"].startswith("Rank 7,500")
    easy, tough = (cut(s, exam="jee", by="college", key=inst, marks=200, level=lv)["you"]["rank"]["range"][0] for lv in ("easy", "tough"))
    assert tough < easy  # the same marks on a tough paper are a better rank


def test_jee_category_changes_the_seat_path(s, opts):
    inst = key_of(opts, "jee", "NIT Trichy")
    gen = cut(s, exam="jee", by="college", key=inst)["rows"][0]
    obc = cut(s, exam="jee", by="college", key=inst, category="OBC-NCL")["rows"][0]
    home = cut(s, exam="jee", by="college", key=inst, state="Tamil Nadu")["rows"][0]
    assert gen["path"] == "Other state · Open" and obc["path"] == "Other state · OBC-NCL" and obc["rank_type"] == "OBC-NCL rank"
    assert home["path"].startswith("Home state") and home["final"]["close"] != gen["final"]["close"]


def test_predict_accepts_scorecard_rank(s):
    form = {"level": "normal", "category": "OBC-NCL", "female": False, "pwd": False, "state": None, "branches": [], "segment": "all", "page": 1}
    d = s.post(f"{R}/predict", json={**form, "rank": 7500}).json()
    assert d["result"]["crl"] == [7500, 7500] and d["result"]["summary"].startswith("Rank 7,500") and not d["result"]["from_marks"]
    assert d["result"]["cat_rank"]["label"] == "OBC-NCL rank" and d["items"]
    r = s.post(f"{R}/predict", json=form)
    assert r.status_code == 422 and r.json()["detail"] == "Marks, percentile ya rank mein se koi ek daalo."
    assert s.post(f"{R}/predict", json={**form, "rank": 0}).status_code == 422


# ---------- COMEDK ----------
def test_comedk_tags_match_college_predictor(s):
    p = s.post(f"{R}/comedk", json={"rank": 30000, "branches": ["Computer Science"], "area": "all", "page": 1}).json()
    d = cut(s, exam="comedk", by="branch", key="Computer Science", rank=30000)
    assert d["columns"] == ["R1", "R2", "R3", "R4"] and d["eligible"] == p["result"]["in_reach"] == sum(d["you"]["counts"].values())
    rows = {r["id"]: r for r in d["rows"]}
    hit = [it for it in p["items"] if it["id"] in rows]
    assert hit
    for it in hit:
        r = rows[it["id"]]
        assert (r["tag"], r["final"]["close"], r["final"]["label"], r["fee"], r["seats"]) == (it["tag"], it["close"], it["round"], it["fee"], it["seats"])
        assert [c["close"] for c in r["cells"]] == it["rounds"]


def test_comedk_marks_and_college(s, opts):
    code = opts["comedk"]["colleges"][0]["key"]
    d = cut(s, exam="comedk", by="college", key=code, marks=150)
    assert d["you"]["source"] == "marks" and d["you"]["check"] and d["you"]["percentile"] and d["eligible"] == d["total"] == len(d["rows"])
    assert all(r["need"]["marks"] <= 150 for r in d["rows"])


# ---------- BITSAT ----------
def test_bitsat_tags_match_college_predictor(s):
    p = s.post(f"{R}/bitsat", json={"score": 250, "campus": "Pilani", "degree": "all"}).json()
    d = cut(s, exam="bitsat", by="college", key="Pilani", marks=250)
    assert d["columns"] == [str(y) for y in p["years"]] and d["metric"] == "score" and d["you"]["rank"] is None and d["you"]["percentile"] is None
    assert {r["id"]: r["tag"] for r in d["rows"]} == {i["id"]: i["tag"] for i in p["items"]}
    for r in d["rows"]:
        assert [c.get("state") for c in r["cells"][:-1]] == [None] * 4 and r["cells"][-1]["state"] == ("edge" if r["tag"] == "borderline" else "in")
    cs = cut(s, exam="bitsat", by="branch", key="cs")
    assert [r["place"] for r in cs["rows"]] == ["Pilani", "Goa", "Hyderabad"] and cs["rows"][0]["final"]["close"] >= cs["rows"][1]["final"]["close"]


# ---------- what the server refuses ----------
@pytest.mark.parametrize("body, status, detail", [
    ({"exam": "jee", "by": "college", "key": "9999"}, 404, "College nahi mila."),
    ({"exam": "jee", "by": "branch", "key": "Nope"}, 404, "Branch nahi mili."),
    ({"exam": "comedk", "by": "college", "key": "E000"}, 404, "College nahi mila."),
    ({"exam": "bitsat", "by": "branch", "key": "nope"}, 404, "Program nahi mila."),
    ({"exam": "jee", "by": "college", "key": "25", "marks": 350}, 422, "JEE Main marks −75 se 300 ke beech daalo."),
    ({"exam": "comedk", "by": "branch", "key": "Computer Science", "percentile": 90}, 422, "COMEDK mein percentile nahi chalta. Marks ya rank daalo."),
    ({"exam": "comedk", "by": "branch", "key": "Computer Science", "marks": 181}, 422, "COMEDK marks 0 se 180 ke beech daalo."),
    ({"exam": "bitsat", "by": "college", "key": "Pilani", "rank": 5}, 422, "BITSAT mein sirf score chalta hai (390 mein se)."),
])
def test_refusals_are_sentences(s, body, status, detail):
    r = s.post(f"{R}/cutoff", json=body, timeout=30)
    assert r.status_code == status and r.json()["detail"] == detail


def test_wrong_field_is_a_list(s):
    r = s.post(f"{R}/cutoff", json={"exam": "neet", "by": "college", "key": "1"})
    assert r.status_code == 422 and isinstance(r.json()["detail"], list)
