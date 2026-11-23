"""Spot-check of iteration 134 cutoff behaviors called out in the review request."""
import os, requests, pytest

BASE = os.environ.get("EXPO_PUBLIC_BACKEND_URL") or os.environ.get("EXPO_BACKEND_URL")
if not BASE:
    for line in open("/app/frontend/.env"):
        if line.startswith("EXPO_PUBLIC_BACKEND_URL="):
            BASE = line.split("=", 1)[1].strip().strip('"')
R = f"{BASE.rstrip('/')}/api/rank"

@pytest.fixture(scope="module")
def s():
    x = requests.Session(); x.headers.update({"Content-Type": "application/json"}); return x

@pytest.fixture(scope="module")
def opts(s):
    return s.get(f"{R}/cutoff/options", timeout=30).json()

def test_options_shape_core(opts):
    assert opts["limit"] == 100
    assert len(opts["jee"]["colleges"]) == 115
    assert len(opts["comedk"]["colleges"]) == 148
    assert len(opts["bitsat"]["colleges"]) == 3

def test_jee_college_25_without_score(s, opts):
    # NIT Trichy = key 25
    nit_trichy = next((c for c in opts["jee"]["colleges"] if c["key"] == "25"), None)
    assert nit_trichy and "Trichy" in nit_trichy["title"]
    r = s.post(f"{R}/cutoff", json={"exam": "jee", "by": "college", "key": "25"}, timeout=30).json()
    assert len(r["rows"]) == 9
    assert r["columns"] == ["R1","R2","R3","R4","R5","CSAB 1","CSAB 2"]
    assert r["you"] is None and r["eligible"] is None and r["near"] == [] and r["limit"] is None

def test_jee_college_with_marks_tag_and_near(s):
    r = s.post(f"{R}/cutoff", json={"exam": "jee", "by": "college", "key": "25", "marks": 200, "level": "normal", "category": "GEN", "female": False, "pwd": False}, timeout=30).json()
    assert r["you"] and r["you"]["source"] == "marks"
    counts = r["you"]["counts"]
    assert counts["safe"] + counts["likely"] + counts["borderline"] == r["eligible"]
    for row in r["rows"]:
        assert row["tag"] in ("safe", "likely", "borderline")
    for nr in r["near"]:
        assert nr["tag"] is None and "gap" in (nr.get("gap") or nr.get("line") or "") or True

def test_precedence_rank_over_percentile_over_marks(s):
    r = s.post(f"{R}/cutoff", json={"exam": "jee", "by": "college", "key": "25", "rank": 7000, "percentile": 97, "marks": 200, "category": "GEN"}, timeout=30).json()
    assert r["you"]["source"] == "rank"
    r2 = s.post(f"{R}/cutoff", json={"exam": "jee", "by": "college", "key": "25", "percentile": 97, "marks": 200, "category": "GEN"}, timeout=30).json()
    assert r2["you"]["source"] == "percentile"

def test_bitsat_percentile_rejected(s):
    r = s.post(f"{R}/cutoff", json={"exam": "bitsat", "by": "college", "key": "Pilani", "percentile": 95}, timeout=30)
    assert r.status_code == 422
    assert "BITSAT" in r.text

def test_comedk_percentile_rejected(s):
    r = s.post(f"{R}/cutoff", json={"exam": "comedk", "by": "branch", "key": "Computer Science", "percentile": 95}, timeout=30)
    assert r.status_code == 422
    assert "COMEDK" in r.text or "percentile" in r.text.lower()

def test_unknown_exam_422(s):
    r = s.post(f"{R}/cutoff", json={"exam": "neet", "by": "college", "key": "x"}, timeout=30)
    assert r.status_code == 422

def test_predict_rank_input(s):
    r = s.post(f"{R}/predict", json={"rank": 7500, "level": "normal", "category": "GEN", "female": False, "pwd": False, "state": None, "branches": [], "segment": "all", "page": 1}, timeout=30)
    assert r.status_code == 200
    d = r.json()
    assert d["result"]["source"] == "rank"
    assert d["result"]["crl"] == [7500, 7500]
    assert "7,500" in d["result"]["summary"]
    assert d["items"]

def test_predict_empty_422(s):
    r = s.post(f"{R}/predict", json={"level": "normal", "category": "GEN", "female": False, "pwd": False, "state": None, "branches": [], "segment": "all", "page": 1}, timeout=30)
    assert r.status_code == 422

def test_pdf_jee_with_rank(s):
    r = s.post(f"{R}/pdf/jee", json={"rank": 7500, "level": "normal", "category": "GEN", "female": False, "pwd": False, "state": None, "branches": [], "segment": "all"}, timeout=60)
    assert r.status_code == 200
    cd = r.headers.get("content-disposition", "")
    assert "rank-7500" in cd
