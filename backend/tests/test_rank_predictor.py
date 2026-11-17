# Rank Predictor Phase 1 (/api/rank/meta, /predict, /college) - read-only, no auth, no DB writes
import os
import re
import pytest
import requests

BASE_URL = os.environ.get("EXPO_PUBLIC_BACKEND_URL") or os.environ.get("EXPO_BACKEND_URL")
if not BASE_URL:
    for line in open("/app/frontend/.env"):
        if line.startswith("EXPO_PUBLIC_BACKEND_URL="):
            BASE_URL = line.split("=", 1)[1].strip().strip('"')
BASE_URL = BASE_URL.rstrip("/")
R = f"{BASE_URL}/api/rank"
INDIAN = re.compile(r"^\d{1,2}(,\d{2})*(,\d{3})?$|^\d{1,3}$")


@pytest.fixture(scope="module")
def s():
    x = requests.Session()
    x.headers.update({"Content-Type": "application/json"})
    return x


def P(s, **kw):
    return s.post(f"{R}/predict", json=kw, timeout=30)


# --- meta ---
def test_meta(s):
    r = s.get(f"{R}/meta", timeout=30)
    assert r.status_code == 200
    d = r.json()
    assert len(d["states"]) == 36
    assert len(d["branches"]) == 20
    ch = d["chart"]
    assert len(ch) == 50 and ch[0]["pct"] == 99.9 and ch[-1]["pct"] == 80.0
    ranks = [c["rank"] for c in ch]
    assert all(a < b for a, b in zip(ranks, ranks[1:])), ranks
    marks = [c["marks"] for c in ch]
    assert all(a >= b for a, b in zip(marks, marks[1:])), marks


# --- predict marks ---
@pytest.fixture(scope="module")
def p180(s):
    r = P(s, marks=180)
    assert r.status_code == 200, r.text
    return r.json()


def test_predict_marks_result(p180):
    res = p180["result"]
    lo, hi = res["crl"]
    assert 1 <= lo < hi
    assert res["percentile"][0] <= res["percentile"][1] <= 100
    assert res["from_marks"] is True
    assert res["summary"] == "180 marks · Normal · General"
    assert res["spread"].startswith("Tough paper hota to rank lagbhag ") and "Easy paper hota to lagbhag" in res["spread"]
    assert "cat_rank" not in res and "pwd_rank" not in res


def test_predict_spread_order(p180):
    nums = re.findall(r"lagbhag ([\d,]*\d)", p180["result"]["spread"])
    tough, easy = [int(n.replace(",", "")) for n in nums]
    for n in nums:
        assert INDIAN.match(n), n
    assert tough < easy  # same marks on a tough paper -> better rank


def test_predict_counts_items(p180):
    c = p180["counts"]
    assert set(c) == {"all", "NIT", "IIIT", "GFTI", "DELHI"}
    assert all(0 <= v <= 50 for v in c.values())
    assert len(p180["items"]) == min(25, c["all"])
    for it in p180["items"]:
        assert it["tag"] in ("safe", "likely", "borderline")
        for k in ("prog", "inst", "college", "branch", "close", "round", "path", "quota", "gender", "seat"):
            assert k in it


def test_predict_page2_diff(s, p180):
    if p180["counts"]["all"] <= 25:
        pytest.skip("only one page")
    r = P(s, marks=180, page=2)
    assert r.status_code == 200
    p2 = r.json()
    assert p2["page"] == 2 and p2["pages"] == 2
    a = {i["prog"] for i in p180["items"]}
    b = {i["prog"] for i in p2["items"]}
    assert b and not (a & b)


def test_predict_near(p180):
    near = p180["near"]
    assert len(near) <= 5
    for n in near:
        assert re.match(r"^lagbhag \+\d+ marks aur$", n["gap"]), n["gap"]
        assert "tag" not in n


def test_predict_segments(s):
    for seg in ("NIT", "IIIT", "GFTI", "DELHI"):
        r = P(s, marks=180, segment=seg)
        assert r.status_code == 200
        d = r.json()
        assert all(i["type"] == seg for i in d["items"]), seg
        assert all(i["type"] == seg for i in d["near"]), seg


# --- predict percentile ---
def test_predict_percentile_obc_female_up(s):
    r = P(s, percentile=97.4, category="OBC-NCL", female=True, state="Uttar Pradesh")
    assert r.status_code == 200, r.text
    d = r.json()
    res = d["result"]
    assert "spread" not in res
    assert res["from_marks"] is False
    assert res["percentile"] == [97.4, 97.4]
    assert res["cat_rank"]["label"] == "OBC-NCL rank"
    a, b = res["cat_rank"]["range"]
    assert 1 <= a <= b < res["crl"][1]
    paths = [i["path"] for p in (1, 2) for i in P(s, percentile=97.4, category="OBC-NCL", female=True, state="Uttar Pradesh", page=p).json()["items"]]
    assert any("Home state" in x for x in paths) or any("Female-only" in x for x in paths), paths
    for n in d["near"]:
        assert "percentile aur" in n["gap"]


def test_predict_pwd(s):
    d = P(s, marks=150, category="SC", pwd=True).json()
    assert d["result"]["pwd_rank"]["label"] == "SC-PwD rank"
    assert d["result"]["cat_rank"]["label"] == "SC rank"


# --- validation ---
@pytest.mark.parametrize("body", [{}, {"marks": 301}, {"marks": -76}, {"percentile": 100.1}, {"marks": 180, "state": "Atlantis"},
                                  {"marks": 180, "segment": "IIT"}, {"marks": 180, "page": 3}, {"marks": 180.5}])
def test_predict_validation(s, body):
    r = s.post(f"{R}/predict", json=body, timeout=30)
    assert r.status_code == 422, (body, r.status_code, r.text[:200])


def test_predict_delhi_state(s):
    d = P(s, marks=200, state="Delhi", segment="DELHI").json()
    assert d["items"], "no Delhi items"
    assert all(i["type"] == "DELHI" for i in d["items"])
    assert any("Delhi region" in i["path"] for i in d["items"]), [i["path"] for i in d["items"]]
    assert not any("Outside Delhi" in i["path"] for i in d["items"])
    assert "delhi_note" in d["result"]


# --- college ---
@pytest.fixture(scope="module")
def first_item(p180):
    return p180["items"][0]


def C(s, **kw):
    return s.post(f"{R}/college", json=kw, timeout=30)


def test_college_basic(s, first_item):
    it = first_item
    r = C(s, marks=180, inst=it["inst"], prog=it["prog"], quota=it["quota"], gender=it["gender"], seat=it["seat"])
    assert r.status_code == 200, r.text
    d = r.json()
    assert 0 < len(d["rows"]) <= 10
    assert d["rounds"] in (["R1", "R2", "R3", "R4", "R5", "CSAB 1", "CSAB 2"], ["R1", "R2", "R3", "R4", "Upgrade", "Spot"])
    assert all(len(row["cells"]) == len(d["rounds"]) for row in d["rows"])
    assert d["line"] and ("aapki rank" in d["line"] or "aapki range" in d["line"])
    assert d["options"]["quota"] and d["path"]["quota"] == it["quota"]
    assert d["official"].startswith("https://")
    row = next((x for x in d["rows"] if x["prog"] == it["prog"]), None)
    assert row is not None, "tapped program not in top rows"
    assert row["first_in"] is not None and any(c["in"] for c in row["cells"])


def test_college_all(s, first_item):
    d1 = C(s, marks=180, inst=first_item["inst"]).json()
    d2 = C(s, marks=180, inst=first_item["inst"], all=True).json()
    assert len(d2["rows"]) == d2["total"] >= len(d1["rows"])


def test_college_switch(s, p180):
    # find a NIT item to exercise quota switching
    it = next((i for i in p180["items"] if i["type"] in ("NIT", "IIIT", "GFTI")), p180["items"][0])
    base = C(s, marks=180, category="OBC-NCL", female=True, inst=it["inst"]).json()
    for q in base["options"]["quota"]:
        d = C(s, marks=180, category="OBC-NCL", female=True, inst=it["inst"], quota=q["key"]).json()
        assert d["path"]["quota"] == q["key"]
    for g in base["options"]["gender"]:
        d = C(s, marks=180, category="OBC-NCL", female=True, inst=it["inst"], quota=base["path"]["quota"], gender=g).json()
        assert d["path"]["gender"] == g
    if "cat" in base["options"]["seat"]:
        d = C(s, marks=180, category="OBC-NCL", female=True, inst=it["inst"], quota=base["path"]["quota"], seat="cat").json()
        assert d["path"]["seat"] == "cat" and "OBC-NCL" in d["your_rank"]["label"]


def test_college_404_and_422(s):
    assert C(s, marks=180, inst=999999).status_code == 404
    assert C(s, inst=0).status_code == 422
    assert C(s, marks=180, inst=-1).status_code == 422


def test_college_every_inst_no_500(s):
    # every institute index must answer without 500
    meta_n = 0
    bad = []
    for i in range(0, 400):
        r = C(s, marks=180, inst=i)
        if r.status_code == 404:
            break
        meta_n += 1
        if r.status_code != 200:
            bad.append((i, r.status_code))
    assert not bad, bad
    assert meta_n > 50
