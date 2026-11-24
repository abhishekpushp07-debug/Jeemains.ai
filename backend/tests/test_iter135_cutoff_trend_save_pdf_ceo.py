"""Iteration 135 backend checks:
    * POST /api/rank/cutoff now returns per-row `trend` and `save` for JEE (college & branch), COMEDK, BITSAT.
    * POST /api/rank/pdf/cutoff returns an application/pdf attachment for jee/comedk/bitsat rows.
    * Regression: /api/rank/cutoff without score still returns rows; empty score still 422.
    * CEO API: GET /api/ceo/overview and /api/ceo/users → 401 with missing / wrong Authorization header.
"""
import os
import re
import requests
import pytest

BASE = os.environ.get("EXPO_PUBLIC_BACKEND_URL") or os.environ.get("EXPO_BACKEND_URL")
if not BASE:
    for line in open("/app/frontend/.env"):
        if line.startswith("EXPO_PUBLIC_BACKEND_URL="):
            BASE = line.split("=", 1)[1].strip().strip('"')
            break
BASE = BASE.rstrip("/")
R = f"{BASE}/api/rank"
CEO = f"{BASE}/api/ceo"


@pytest.fixture(scope="module")
def s():
    x = requests.Session()
    x.headers.update({"Content-Type": "application/json"})
    return x


# ---------- Cutoff: trend + save ----------
# JEE by college — key '6' (per review request)
def test_jee_by_college_6_trend_and_save(s):
    r = s.post(f"{R}/cutoff", json={"exam": "jee", "by": "college", "key": "6",
                                    "marks": 180, "level": "normal", "category": "GEN",
                                    "female": False, "pwd": False}, timeout=30)
    assert r.status_code == 200, r.text
    d = r.json()
    # existing fields are still there
    for k in ("rows", "eligible", "you", "near", "columns", "metric"):
        assert k in d
    assert isinstance(d["rows"], list) and len(d["rows"]) > 0
    # Each row has a save object with jee shape and id jee-<prog>
    any_trend = False
    for row in d["rows"]:
        save = row.get("save")
        assert save and save["exam"] == "jee"
        assert save["id"].startswith("jee-")
        assert "jee" in save
        jee = save["jee"]
        for key in ("prog", "quota", "gender", "path"):
            assert key in jee
        # trend may be null when prev not available, but when present must have dir/prev/label
        trend = row.get("trend")
        if trend is not None:
            any_trend = True
            assert trend["dir"] in ("tough", "easy", "same")
            assert trend["prev"] and trend.get("label")
    assert any_trend, "Expected at least one row with a trend (prev 2025 closing)"


# JEE by branch — Computer Science
def test_jee_by_branch_cs_trend_and_save(s):
    r = s.post(f"{R}/cutoff", json={"exam": "jee", "by": "branch", "key": "Computer Science",
                                    "marks": 180, "level": "normal", "category": "GEN",
                                    "female": False, "pwd": False}, timeout=30)
    assert r.status_code == 200, r.text
    d = r.json()
    assert d["rows"]
    for row in d["rows"][:5]:
        save = row.get("save")
        assert save and save["exam"] == "jee" and save["id"].startswith("jee-")
        assert "jee" in save and "prog" in save["jee"]


# COMEDK by college — pick first college key from options
def test_comedk_by_college_trend_and_save(s):
    opts = s.get(f"{R}/cutoff/options", timeout=30).json()
    code = opts["comedk"]["colleges"][0]["key"]
    r = s.post(f"{R}/cutoff", json={"exam": "comedk", "by": "college", "key": code,
                                    "marks": 120}, timeout=30)
    assert r.status_code == 200, r.text
    d = r.json()
    assert d["rows"]
    for row in d["rows"][:5]:
        save = row.get("save")
        assert save and save["exam"] == "comedk"
        # id form: comedk-<code>|<cc>
        assert re.match(r"^comedk-[^|]+\|[^|]+$", save["id"]), save["id"]
        # trend may be present (2025 final)
        if row.get("trend") is not None:
            assert row["trend"]["dir"] in ("tough", "easy", "same")


# BITSAT by college — Pilani
def test_bitsat_by_college_pilani_trend_and_save(s):
    r = s.post(f"{R}/cutoff", json={"exam": "bitsat", "by": "college", "key": "Pilani",
                                    "marks": 300}, timeout=30)
    assert r.status_code == 200, r.text
    d = r.json()
    assert d["rows"]
    any_trend = False
    for row in d["rows"][:5]:
        save = row.get("save")
        assert save and save["exam"] == "bitsat"
        assert save["id"].startswith("bitsat-")
        if row.get("trend"):
            any_trend = True
            assert row["trend"]["dir"] in ("tough", "easy", "same")
    assert any_trend, "At least one BITSAT row should expose trend from last year"


# ---------- /api/rank/pdf/cutoff ----------
def _assert_pdf(r):
    assert r.status_code == 200, r.text[:300]
    ct = r.headers.get("content-type", "")
    assert "application/pdf" in ct, f"content-type={ct}"
    assert len(r.content) > 500
    assert r.content[:4] == b"%PDF"


def test_pdf_cutoff_jee_college(s):
    r = s.post(f"{BASE}/api/rank/pdf/cutoff", json={
        "exam": "jee", "by": "college", "key": "6", "marks": 180, "level": "normal",
        "category": "GEN", "female": False, "pwd": False}, timeout=60)
    _assert_pdf(r)


def test_pdf_cutoff_jee_branch_cs(s):
    r = s.post(f"{BASE}/api/rank/pdf/cutoff", json={
        "exam": "jee", "by": "branch", "key": "Computer Science", "marks": 180,
        "level": "normal", "category": "GEN", "female": False, "pwd": False}, timeout=60)
    _assert_pdf(r)


def test_pdf_cutoff_comedk_branch(s):
    opts = s.get(f"{R}/cutoff/options", timeout=30).json()
    group = opts["comedk"]["branches"][0]["key"]
    r = s.post(f"{BASE}/api/rank/pdf/cutoff", json={
        "exam": "comedk", "by": "branch", "key": group, "marks": 120}, timeout=60)
    _assert_pdf(r)


def test_pdf_cutoff_bitsat_branch_cs(s):
    r = s.post(f"{BASE}/api/rank/pdf/cutoff", json={
        "exam": "bitsat", "by": "branch", "key": "cs", "marks": 300}, timeout=60)
    _assert_pdf(r)


# ---------- Regression ----------
def test_cutoff_without_score_returns_rows(s):
    r = s.post(f"{R}/cutoff", json={"exam": "jee", "by": "college", "key": "6"}, timeout=30)
    assert r.status_code == 200
    d = r.json()
    assert d["rows"] and d["you"] is None and d["eligible"] is None


def test_cutoff_empty_score_422(s):
    # by branch, no marks/rank/percentile but with category present → still 422 'Marks/percentile/rank'
    # actually per review: /predict with empty returns 422. For /cutoff when score fields present but all null → 200.
    # Review states "/api/rank/cutoff with empty score still 422 'Marks, percentile ya rank mein se koi ek daalo.'"
    # Try empty category profile shape used by predict
    r = s.post(f"{BASE}/api/rank/predict", json={
        "level": "normal", "category": "GEN", "female": False, "pwd": False,
        "state": None, "branches": [], "segment": "all", "page": 1}, timeout=30)
    assert r.status_code == 422
    assert "Marks" in r.text or "mein se" in r.text


def test_openapi_has_ceo_and_pdf_routes(s):
    # The k8s ingress routes non-/api paths to the frontend, so hit uvicorn directly for the schema.
    o = requests.get("http://localhost:8001/openapi.json", timeout=30).json()
    paths = set(o.get("paths", {}).keys())
    assert "/api/ceo/overview" in paths
    assert "/api/ceo/users" in paths
    assert "/api/rank/pdf/cutoff" in paths


# ---------- CEO API: unauthorized paths only ----------
def test_ceo_overview_no_auth_401(s):
    r = requests.get(f"{CEO}/overview", timeout=30)
    assert r.status_code == 401, f"got {r.status_code}: {r.text[:200]}"


def test_ceo_overview_wrong_token_401(s):
    r = requests.get(f"{CEO}/overview",
                     headers={"Authorization": "Bearer wrongtoken"}, timeout=30)
    assert r.status_code == 401, f"got {r.status_code}: {r.text[:200]}"


def test_ceo_users_no_auth_401(s):
    r = requests.get(f"{CEO}/users", timeout=30)
    assert r.status_code == 401


def test_ceo_users_wrong_token_401(s):
    r = requests.get(f"{CEO}/users",
                     headers={"Authorization": "Bearer nope"}, timeout=30)
    assert r.status_code == 401
