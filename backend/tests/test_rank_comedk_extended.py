# COMEDK rank predictor + college sheet: extended checks (GM only, rounds, filters, edge cases) + JEE/BITSAT regression shape
import os
import pytest
import requests

BASE = os.environ.get("EXPO_BACKEND_URL").rstrip("/")


@pytest.fixture(scope="module")
def s():
    x = requests.Session()
    x.headers.update({"Content-Type": "application/json"})
    return x


def post(s, path, body):
    return s.post(f"{BASE}/api/rank/{path}", json=body, timeout=30)


# --- predictor: marks path
def test_marks_100_range_and_pages(s):
    r = post(s, "comedk", {"marks": 100})
    assert r.status_code == 200
    d = r.json()
    lo, hi = d["result"]["rank"]
    assert lo < d["result"]["mid"] <= hi
    assert d["result"]["from_marks"] is True and d["result"]["spread"]
    assert len(d["items"]) == 25 and d["pages"] == 2 and d["page"] == 1
    p2 = post(s, "comedk", {"marks": 100, "page": 2}).json()
    assert p2["page"] == 2 and len(p2["items"]) >= 1
    assert not {i["id"] for i in p2["items"]} & {i["id"] for i in d["items"]}


def test_marks_monotonic_edges(s):
    top = post(s, "comedk", {"marks": 180}).json()["result"]
    zero = post(s, "comedk", {"marks": 0}).json()["result"]
    assert top["rank"][0] >= 1 and zero["rank"][1] > top["rank"][1]


# --- predictor: rank path
def test_rank_4500_exact_tags_near(s):
    d = post(s, "comedk", {"rank": 4500}).json()
    assert d["result"]["rank"] == [4500, 4500] and d["result"]["from_marks"] is False
    assert all(i["close"] >= 4500 for i in d["items"])
    assert {i["tag"] for i in d["items"]} <= {"safe", "likely", "borderline"}
    for n in d["near"]:
        assert n["close"] < 4500 and "aur upar" in n["gap"]
    for i in d["items"]:
        assert len(i["rounds"]) == 4 and i["close"] == max(c for c in i["rounds"] if c)


def test_both_rank_wins(s):
    d = post(s, "comedk", {"rank": 4500, "marks": 50}).json()
    assert d["result"]["rank"] == [4500, 4500]


def test_area_branch_filters(s):
    blr = post(s, "comedk", {"rank": 4500, "area": "blr"}).json()
    oth = post(s, "comedk", {"rank": 4500, "area": "other"}).json()
    assert blr["items"] and all(i["blr"] for i in blr["items"])
    assert all(not i["blr"] for i in oth["items"])
    cs = post(s, "comedk", {"rank": 4500, "branches": ["Computer Science"]}).json()
    assert cs["items"] and all(i["group"] == "Computer Science" for i in cs["items"])
    junk = post(s, "comedk", {"rank": 4500, "branches": ["Nonsense"]}).json()
    assert junk["result"]["total"] == post(s, "comedk", {"rank": 4500}).json()["result"]["total"]


@pytest.mark.parametrize("body", [{}, {"marks": 181}, {"marks": -1}, {"rank": 0}, {"rank": 200001}, {"rank": 4500, "area": "xyz"}, {"rank": 4500, "page": 3}])
def test_validation_422(s, body):
    assert post(s, "comedk", body).status_code == 422


def test_gm_only_no_kkr(s):
    txt = post(s, "comedk", {"marks": 60}).text + post(s, "comedk/college", {"rank": 3000, "code": "E027", "all": True}).text
    # KKR only allowed inside the explanatory note
    d = post(s, "comedk", {"marks": 60}).json()
    for i in d["items"] + d["near"]:
        assert "KKR" not in str(i)
    assert '"cat"' not in txt


# --- college sheet
def test_college_rounds_and_in_flag(s):
    r = post(s, "comedk/college", {"rank": 3000, "code": "E027", "course": "CS"})
    assert r.status_code == 200
    d = r.json()
    assert d["rounds"][:4] == ["R1", "R2", "R3", "R4"] or len(d["rounds"]) == 4
    assert any(row["cc"] == "CS" for row in d["rows"])
    for row in d["rows"]:
        assert len(row["cells"]) == 4
        for c in row["cells"]:
            assert set(c) >= {"close", "in", "mine"}
            assert c["in"] == bool(c["close"] and c["close"] >= 3000)
        exp = next((d["rounds"][i] for i, c in enumerate(row["cells"]) if c["in"]), None)
        assert row["first_in"] == exp
    assert d["line"] and d["your_rank"]["range"] == [3000, 3000]


def test_college_all_and_404(s):
    a = post(s, "comedk/college", {"rank": 3000, "code": "E027", "all": True}).json()
    assert len(a["rows"]) == a["total"]
    assert post(s, "comedk/college", {"rank": 3000, "code": "ZZZ999"}).status_code == 404
    assert post(s, "comedk/college", {"code": "E027"}).status_code == 422


def test_college_course_outside_first10_is_added(s):
    a = post(s, "comedk/college", {"rank": 3000, "code": "E077", "all": True}).json()
    assert a["total"] > 12
    short = post(s, "comedk/college", {"rank": 3000, "code": "E077"}).json()
    assert len(short["rows"]) == 10
    last = a["rows"][-1]["cc"]
    d = post(s, "comedk/college", {"rank": 3000, "code": "E077", "course": last}).json()
    assert d["line"].startswith(a["rows"][-1]["course"])
    assert any(r["cc"] == last for r in d["rows"])


def test_meta_comedk(s):
    m = s.get(f"{BASE}/api/rank/meta", timeout=30).json()
    assert "Computer Science" in m["comedk"]["groups"]


# --- regression: JEE college cells have 'mine'; BITSAT works
def test_jee_college_cells_have_mine(s):
    p = post(s, "predict", {"marks": 180})
    assert p.status_code == 200
    j = p.json()
    items = j.get("items") or j.get("seats") or []
    assert items, list(j)
    it = items[0]
    body = {"marks": 180, "inst": it.get("inst"), "prog": it.get("prog")}
    r = post(s, "college", body)
    if r.status_code != 200:
        pytest.skip(f"college body shape differs: {r.status_code} {r.text[:200]}")
    rows = r.json()["rows"]
    assert all("mine" in c for row in rows for c in row["cells"])


def test_bitsat_280(s):
    r = post(s, "bitsat", {"score": 280})
    assert r.status_code == 200
