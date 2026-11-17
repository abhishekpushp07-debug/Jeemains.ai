# Rank COMEDK (iteration82): marks or rank -> GM (All India) college-course list, round-wise college sheet, meta.
import os

import pytest
import requests

BASE = os.environ.get("EXPO_BACKEND_URL").rstrip("/") + "/api/rank"


@pytest.fixture(scope="module")
def s():
    x = requests.Session()
    x.headers.update({"Content-Type": "application/json"})
    return x


def post(s, path, **kw):
    r = s.post(f"{BASE}{path}", json=kw)
    assert r.status_code == 200, r.text
    return r.json()


def test_meta_has_comedk_groups(s):
    m = s.get(f"{BASE}/meta").json()["comedk"]
    assert "Computer Science" in m["groups"] and m["rounds"] == ["R1", "R2", "R3", "R4"] and m["max_marks"] == 180


def test_marks_give_a_range_from_three_analyses(s):
    d = post(s, "/comedk", marks=100)
    r = d["result"]
    assert r["from_marks"] and r["rank"][0] < r["mid"] <= r["rank"][1]
    assert "3 alag analysis" in r["spread"]
    assert d["pages"] == 2 and len(d["items"]) == 25


def test_higher_marks_better_rank(s):
    a, b = post(s, "/comedk", marks=140)["result"], post(s, "/comedk", marks=60)["result"]
    assert a["rank"][1] < b["rank"][0]


def test_rank_input_is_exact_and_tags_follow_closing(s):
    d = post(s, "/comedk", rank=4500)
    assert d["result"]["rank"] == [4500, 4500] and not d["result"]["from_marks"]
    for it in d["items"]:
        assert it["close"] >= 4500 and it["close"] == max(c for c in it["rounds"] if c)
        assert it["tag"] in ("safe", "likely", "borderline")
    for it in d["near"]:
        assert it["close"] < 4500 and "upar chahiye" in it["gap"]


def test_area_and_branch_filters(s):
    d = post(s, "/comedk", rank=20000, area="blr", branches=["Computer Science"])
    assert d["items"] and all(i["blr"] and i["group"] == "Computer Science" for i in d["items"])
    o = post(s, "/comedk", rank=20000, area="other")
    assert all(not i["blr"] for i in o["items"])


def test_validation(s):
    assert s.post(f"{BASE}/comedk", json={}).status_code == 422
    assert s.post(f"{BASE}/comedk", json={"marks": 181}).status_code == 422
    assert s.post(f"{BASE}/comedk/college", json={"rank": 10, "code": "E999"}).status_code == 404


def test_college_sheet_round_wise(s):
    d = post(s, "/comedk/college", rank=3000, code="E027", course="CS")
    assert d["college"]["short"].startswith("BMS College") and d["rounds"] == ["R1", "R2", "R3", "R4"]
    cs = next(r for r in d["rows"] if r["cc"] == "CS")
    assert len(cs["cells"]) == 4 and all(c["mine"] == 3000 for c in cs["cells"])
    assert all(c["in"] == bool(c["close"] and c["close"] >= 3000) for c in cs["cells"])
    assert cs["first_in"] and d["line"].startswith("Computer Science & Engineering")
    full = post(s, "/comedk/college", rank=3000, code="E027", all=True)
    assert len(full["rows"]) == full["total"] >= len(d["rows"])
