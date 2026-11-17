# Iteration 83: tapped branch always in the JEE college sheet, JAC unpublished rounds, reach totals, range-aware cells.
import os
import requests
import pytest

BASE = os.environ.get("EXPO_BACKEND_URL").rstrip("/") + "/api/rank"
s = requests.Session()


def post(path, **kw):
    r = s.post(f"{BASE}{path}", json=kw, timeout=60)
    assert r.status_code == 200, r.text
    return r.json()


# HIGH retest: NSUT prog 726 outside top 10 is in the sheet
def test_prog_726_in_rows():
    d = post("/college", marks=180, inst=112, prog=726, quota="OD", gender="N", seat="open")
    progs = [r["prog"] for r in d["rows"]]
    assert 726 in progs
    row = next(r for r in d["rows"] if r["prog"] == 726)
    assert d["rounds"][:4] == ["R1", "R2", "R3", "R4"], d["rounds"]
    assert len(row["cells"]) == len(d["rounds"])
    # Upgrade / Spot are unpublished JAC rounds
    for c in row["cells"][4:]:
        assert c["unpublished"] is True and c["close"] is None
    assert row["branch"] in d["line"]
    assert len(d["rows"]) <= 11


# Sweep: every listed item's prog is in its college sheet (all + DELHI, pages 1-2)
@pytest.mark.parametrize("seg", ["all", "DELHI"])
def test_sweep_items_in_sheet(seg):
    missing = []
    for page in (1, 2):
        p = post("/predict", marks=180, segment=seg, page=page, page_size=25)
        for it in p["items"]:
            d = post("/college", marks=180, inst=it["inst"], prog=it["prog"], quota=it["quota"], gender=it["gender"], seat=it.get("seat", "open"))
            if it["prog"] not in [r["prog"] for r in d["rows"]]:
                missing.append((it["inst"], it["prog"]))
    assert not missing, missing


# reach totals exposed and >= list counts
def test_predict_reach():
    p = post("/predict", marks=180, segment="all", page=1, page_size=25)
    assert set(p["reach"]) == {"all", "NIT", "IIIT", "GFTI", "DELHI"}
    assert p["reach"]["all"] >= p["counts"]["all"]
    assert p["total"] <= 50


def test_comedk_reach():
    d = post("/comedk", marks=60)
    assert "reach" in d, list(d)
    print(d["reach"])


# Cells carry mine (best) <= hi (worst); 'in' means mine <= close
def test_cells_range():
    d = post("/college", marks=180, inst=112, prog=726, quota="OD", gender="N", seat="open")
    for r in d["rows"]:
        for c in r["cells"]:
            if c["mine"] is not None:
                assert c["mine"] <= c["hi"]
                assert c["in"] == bool(c["close"] and c["mine"] <= c["close"])


# Blocked path: Home-state quota of another state shows the block line and no 'in'/'mine'
def test_home_state_blocked():
    p = post("/predict", marks=180, state="Bihar", segment="NIT", page=1, page_size=25)
    it = next(i for i in p["items"] if i["quota"] == "OS")
    d = post("/college", marks=180, state="Bihar", inst=it["inst"], prog=it["prog"], quota="HS", gender=it["gender"], seat="open")
    assert d["path"]["quota"] == "HS", d["path"]
    assert d["blocked"] and d["line"].startswith("Ye raasta aapke liye nahi")
    for r in d["rows"]:
        assert all(not c["in"] and c["mine"] is None for c in r["cells"])


# Unknown prog for this college: sheet still works with top rows only
def test_foreign_prog_no_crash():
    d = post("/college", marks=180, inst=112, prog=1, quota="OD", gender="N", seat="open")
    assert len(d["rows"]) == 10 and 1 not in [r["prog"] for r in d["rows"]]


def test_all_rows():
    d = post("/college", marks=180, inst=112, prog=726, quota="OD", gender="N", seat="open", all=True)
    assert len(d["rows"]) == d["total"]
