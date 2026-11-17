# Rank Predictor iteration80: iter79 fixes (college eligibility block, CRL clamp, chance mix) + Phase 2 (2025 trend, BITSAT)
import os
from collections import Counter

import pytest
import requests

BASE = os.environ.get("EXPO_BACKEND_URL").rstrip("/") + "/api/rank"
UP = "Uttar Pradesh"


@pytest.fixture(scope="module")
def s():
    x = requests.Session()
    x.headers.update({"Content-Type": "application/json"})
    return x


def college(s, **kw):
    r = s.post(f"{BASE}/college", json=kw)
    assert r.status_code == 200, r.text
    return r.json()


def all_cells_out(d):
    return all(not c["in"] for row in d["rows"] for c in row["cells"])


# --- Iter79 fix 1: ineligible quota/gender paths are blocked
class TestCollegeBlock:
    def test_hs_blocked_for_other_state(self, s):
        d = college(s, marks=180, state=UP, inst=0, quota="HS")
        assert "Jalandhar" in d["college"]["name"]
        assert d["path"]["quota"] == "HS"
        assert d["blocked"] and d["line"].startswith("Ye raasta aapke liye nahi")
        assert all_cells_out(d)

    def test_female_only_blocked_for_male(self, s):
        d = college(s, marks=180, state=UP, inst=0, quota="OS", gender="F")
        assert d["path"]["gender"] == "F"
        assert d["blocked"] and "Female-only" in d["blocked"]
        assert all_cells_out(d)

    def test_os_neutral_open(self, s):
        d = college(s, marks=180, state=UP, inst=0, quota="OS", gender="N")
        assert d["blocked"] is None
        assert not d["line"].startswith("Ye raasta")
        assert d["y25_label"] == "2025 R6"
        assert all("y25" in r for r in d["rows"])

    def test_delhi_region_blocked_for_non_delhi(self, s):
        d = college(s, marks=180, state=UP, inst=112, quota="DL", gender="N")
        assert d["college"]["type"] == "DELHI" and d["path"]["quota"] == "DL"
        assert d["blocked"] and all_cells_out(d)
        assert d["y25_label"] is None

    def test_outside_delhi_blocked_for_delhi(self, s):
        d = college(s, marks=180, state="Delhi", inst=112, quota="OD", gender="N")
        assert d["path"]["quota"] == "OD"
        assert d["blocked"] and all_cells_out(d)

    def test_outside_delhi_open_for_up(self, s):
        d = college(s, marks=180, state=UP, inst=112, quota="OD", gender="N")
        assert d["blocked"] is None


# --- Iter79 fix 2: CRL upper bound clamped
def test_crl_clamped(s):
    meta = s.get(f"{BASE}/meta").json()
    for body in ({"marks": -75}, {"percentile": 0}):
        r = s.post(f"{BASE}/predict", json=body).json()
        assert r["result"]["crl"][1] <= meta["candidates"] == 1538468, (body, r["result"]["crl"])


# --- Iter79 fix 3: chance mix
@pytest.mark.parametrize("marks", [120, 180])
def test_all_list_mixed(s, marks):
    tags = []
    for page in (1, 2):
        d = s.post(f"{BASE}/predict", json={"marks": marks, "page": page}).json()
        assert all(v <= 50 for v in d["counts"].values())
        tags += [i["tag"] for i in d["items"]]
    c = Counter(tags)
    assert len(tags) == 50
    assert c["borderline"] and c["likely"] and c["safe"], c
    assert c["borderline"] >= min(20, c["borderline"]) and c["likely"] <= 50


def test_segment_lists_mixed(s):
    d = s.post(f"{BASE}/predict", json={"marks": 180, "segment": "NIT"}).json()
    d2 = s.post(f"{BASE}/predict", json={"marks": 180, "segment": "NIT", "page": 2}).json()
    c = Counter(i["tag"] for i in d["items"] + d2["items"])
    assert len(c) >= 2, c


# --- Meta
def test_meta(s):
    d = s.get(f"{BASE}/meta").json()
    assert "shifts" not in d
    assert d["y25_label"] == "2025 R6" and d["candidates"] == 1538468
    labels = " ".join(x["label"] for x in d["sources"])
    assert "JoSAA 2025" in labels and "BITS" in labels


# --- 2025 trend on items
def test_items_trend(s):
    a = s.post(f"{BASE}/predict", json={"marks": 180}).json()
    for it in a["items"]:
        assert it["y25"] is None or isinstance(it["y25"], int)
        assert isinstance(it["y26"], int)
    assert any(it["y25"] for it in a["items"])


# --- BITSAT
def bits(s, **kw):
    r = s.post(f"{BASE}/bitsat", json=kw)
    assert r.status_code == 200, r.text
    return r.json()


def test_bitsat_280(s):
    d = bits(s, score=280)
    r = d["result"]
    assert (r["cleared_all"], r["total_all"]) == (47, 50)
    assert r["best"] == {"college": "BITS Goa", "program": "B.E. Computer Science", "cutoff": 274}
    assert r["target"]["college"] == "BITS Pilani" and r["target"]["program"] == "B.E. Electronics & Communication"
    assert r["target"]["gap"] == 9
    assert {i["tag"] for i in d["items"]} <= {"safe", "likely", "borderline"}
    assert all(0 < i["gap"] <= 20 for i in d["near"]) and all(i["gap"] > 20 for i in d["rest"])
    assert d["years"] == [2022, 2023, 2024, 2025, 2026]


@pytest.mark.parametrize("campus,degree", [("Goa", "all"), ("Pilani", "all"), ("Hyderabad", "all"),
                                           ("all", "BE"), ("all", "MSc"), ("all", "BPharm")])
def test_bitsat_filters(s, campus, degree):
    full = bits(s, score=280)["result"]
    d = bits(s, score=280, campus=campus, degree=degree)
    r = d["result"]
    every = d["items"] + d["near"] + d["rest"]
    assert len(every) == r["total"] < 50
    assert all(campus in ("all", i["campus"]) and degree in ("all", i["degree"]) for i in every)
    for k in ("cleared_all", "best", "target", "total_all"):
        assert r[k] == full[k]


@pytest.mark.parametrize("score", [400, -131])
def test_bitsat_bad(s, score):
    assert s.post(f"{BASE}/bitsat", json={"score": score}).status_code == 422


def test_bitsat_official_cutoffs(s):
    d = bits(s, score=200)
    rows = {(i["campus"], i["program"]): i for i in d["items"] + d["near"] + d["rest"]}
    assert rows[("Pilani", "B.E. Computer Science")]["history"] == [320, 331, 327, 304, 308]
    assert rows[("Goa", "B.E. Computer Science")]["cutoff"] == 274
    assert rows[("Hyderabad", "B. Pharm")]["cutoff"] == 200
