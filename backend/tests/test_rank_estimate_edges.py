# Rank predictor edge cases (iteration84): boundaries, monotonicity, GEN-PwD label, levels vs result consistency.
import os

import pytest
import requests

BASE = os.environ.get("EXPO_BACKEND_URL").rstrip("/") + "/api/rank"


@pytest.fixture(scope="module")
def s():
    x = requests.Session()
    x.headers.update({"Content-Type": "application/json"})
    return x


def post(s, body):
    return s.post(f"{BASE}/estimate", json=body)


@pytest.mark.parametrize("body,code", [
    ({"exam": "comedk", "marks": 0}, 200), ({"exam": "comedk", "marks": 180}, 200), ({"exam": "comedk", "marks": -1}, 422),
    ({"exam": "jee", "marks": -75}, 200), ({"exam": "jee", "marks": 300}, 200), ({"exam": "jee", "marks": -76}, 422),
    ({"exam": "jee"}, 422), ({"exam": "jee", "marks": 150, "level": "hard"}, 422), ({"exam": "jee", "marks": 150, "category": "OBC"}, 422),
])
def test_boundaries(s, body, code):
    r = post(s, body)
    assert r.status_code == code, r.text


def test_comedk_monotonic(s):
    mids = [post(s, {"exam": "comedk", "marks": m}).json()["mid"] for m in range(0, 181, 20)]
    assert all(a >= b for a, b in zip(mids, mids[1:])), mids


def test_jee_monotonic_normal(s):
    crl = [post(s, {"exam": "jee", "marks": m}).json()["result"]["crl"][0] for m in range(0, 301, 30)]
    assert all(a >= b for a, b in zip(crl, crl[1:])), crl


def test_jee_result_equals_selected_level_row(s):
    for lvl in ("tough", "normal", "easy"):
        d = post(s, {"exam": "jee", "marks": 180, "level": lvl, "category": "OBC-NCL"}).json()
        row = next(l for l in d["levels"] if l["level"] == lvl)
        assert row["crl"] == d["result"]["crl"] and row["percentile"] == d["result"]["percentile"]
        assert row["cat_rank"] == d["result"]["cat_rank"]


def test_gen_pwd_label_and_no_cat_rank_for_gen(s):
    d = post(s, {"exam": "jee", "marks": 180, "category": "GEN", "pwd": True}).json()["result"]
    assert d.get("pwd_rank") and "PwD" in d["pwd_rank"]["label"]
    g = post(s, {"exam": "jee", "marks": 180, "category": "GEN"}).json()["result"]
    assert not g.get("cat_rank") and not g.get("pwd_rank")


def test_comedk_percentile_consistent_with_rank(s):
    d = post(s, {"exam": "comedk", "marks": 100}).json()
    assert all(d["rank"][0] <= x["rank"] <= d["rank"][1] for x in d["sources"])
    assert d["summary"].startswith("100 / 180 marks")
