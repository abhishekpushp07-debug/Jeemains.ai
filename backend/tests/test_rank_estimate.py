# Rank predictor (iteration84): POST /api/rank/estimate -> rank + percentile only, JEE (all 3 paper types) and COMEDK.
import os

import pytest
import requests

BASE = os.environ.get("EXPO_BACKEND_URL").rstrip("/") + "/api/rank"


@pytest.fixture(scope="module")
def s():
    x = requests.Session()
    x.headers.update({"Content-Type": "application/json"})
    return x


def est(s, **kw):
    r = s.post(f"{BASE}/estimate", json=kw)
    assert r.status_code == 200, r.text
    return r.json()


def test_jee_matches_college_predictor_card(s):
    d = est(s, exam="jee", marks=180, level="normal", category="GEN")
    p = s.post(f"{BASE}/predict", json={"marks": 180, "level": "normal", "category": "GEN"}).json()["result"]
    assert d["result"]["percentile"] == p["percentile"] and d["result"]["crl"] == p["crl"]
    assert [l["level"] for l in d["levels"]] == ["tough", "normal", "easy"] and d["candidates"] > 1_000_000


def test_jee_tough_paper_gives_better_rank_for_same_marks(s):
    lv = {l["level"]: l for l in est(s, exam="jee", marks=150)["levels"]}
    assert lv["tough"]["crl"][1] < lv["normal"]["crl"][0] < lv["normal"]["crl"][1] < lv["easy"]["crl"][0]
    assert lv["tough"]["percentile"][0] > lv["easy"]["percentile"][1]


def test_jee_category_and_pwd_ranks(s):
    d = est(s, exam="jee", marks=180, category="OBC-NCL", pwd=True)
    assert d["result"]["cat_rank"]["label"] == "OBC-NCL rank" and d["result"]["pwd_rank"]["label"] == "OBC-NCL-PwD rank"
    assert all(l["cat_rank"] and l["pwd_rank"] for l in d["levels"])
    assert d["result"]["cat_rank"]["range"][1] < d["result"]["crl"][0]


def test_comedk_rank_and_percentile(s):
    d = est(s, exam="comedk", marks=100)
    assert d["rank"][0] <= d["mid"] <= d["rank"][1] and len(d["sources"]) == 3
    assert 0 < d["percentile"][0] <= d["percentile"][1] < 100
    hi = est(s, exam="comedk", marks=150)
    assert hi["rank"][1] < d["rank"][0]


def test_validation(s):
    assert s.post(f"{BASE}/estimate", json={"exam": "comedk", "marks": 181}).status_code == 422
    assert s.post(f"{BASE}/estimate", json={"exam": "jee", "marks": 301}).status_code == 422
    assert s.post(f"{BASE}/estimate", json={"exam": "bitsat", "marks": 200}).status_code == 422
