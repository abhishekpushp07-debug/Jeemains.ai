# Iteration 202: app-server connector (Rank proxy, Mission/Dream 401 signed-out, share-link redirects, local files gone)
import os
import pytest
import requests

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL").rstrip("/")
API = f"{BASE_URL}/api"


@pytest.fixture
def s():
    return requests.Session()


# Rank GET proxies
@pytest.mark.parametrize("path", ["meta", "colleges", "target/bitsat"])
def test_rank_get(s, path):
    r = s.get(f"{API}/rank/{path}", timeout=30)
    assert r.status_code == 200, r.text[:200]
    assert isinstance(r.json(), (dict, list))


def test_rank_estimate_jee_180(s):
    r = s.post(f"{API}/rank/estimate", json={"exam": "jee", "marks": 180, "level": "normal", "category": "GEN", "pwd": False}, timeout=30)
    assert r.status_code == 200, r.text[:300]
    body = r.text
    assert "13029" in body and "14029" in body, body[:500]


def test_rank_estimate_missing_marks_422(s):
    r = s.post(f"{API}/rank/estimate", json={"exam": "jee", "level": "normal", "category": "GEN", "pwd": False}, timeout=30)
    assert r.status_code == 422
    assert "detail" in r.json()


def test_rank_college_unknown_404(s):
    r = s.post(f"{API}/rank/college", json={"inst": 999999, "exam": "jee", "marks": 200, "level": "normal", "category": "GEN", "pwd": False}, timeout=30)
    assert r.status_code == 404, r.text[:300]
    assert "College nahi mila." in r.text


def test_rank_pdf_bitsat(s):
    r = s.post(f"{API}/rank/pdf/bitsat", json={"score": 280}, timeout=60)
    assert r.status_code == 200, r.text[:300]
    assert r.headers["content-type"].startswith("application/pdf")
    assert "filename" in r.headers.get("content-disposition", "")
    assert r.content[:4] == b"%PDF"


def test_rank_unknown_404(s):
    assert s.get(f"{API}/rank/unknown", timeout=30).status_code == 404
    assert s.post(f"{API}/rank/unknown", json={}, timeout=30).status_code == 404


def test_rank_body_too_large(s):
    r = s.post(f"{API}/rank/estimate", data=b'{"x":"' + b"a" * 17000 + b'"}', headers={"Content-Type": "application/json"}, timeout=30)
    assert r.status_code == 413, r.status_code


# Signed-out Mission/Dream -> 401 envelope
@pytest.mark.parametrize("method,path", [("GET", "mission/me"), ("GET", "dream"), ("PUT", "dream/dreams"),
                                         ("POST", "dream/mocks"), ("POST", "dream/cheered"),
                                         ("GET", "dream/celebration/abc123")])
def test_signed_out_401(s, method, path):
    r = s.request(method, f"{API}/{path}", json={} if method != "GET" else None, timeout=30)
    assert r.status_code == 401, (r.status_code, r.text[:200])


def test_share_link_good(s):
    r = s.get(f"{API}/j/AB2CDEF", allow_redirects=False, timeout=30)
    assert r.status_code == 302
    assert r.headers["location"] == "https://jeelive-mobile.emergent.host/api/j/AB2CDEF"


def test_share_link_bad(s):
    r = s.get(f"{API}/j/bad!", allow_redirects=False, timeout=30)
    assert r.status_code == 302
    assert r.headers["location"].rstrip("/") == "https://jeelive.ai"


def test_local_files_gone():
    d = "/app/backend/tejas"
    for f in ["rank_predictor.py", "rank_tools.py", "rank_pdf.py", "rank_bitsat.py", "rank_comedk.py", "mission.py"]:
        assert not os.path.exists(os.path.join(d, f)), f
    assert not os.path.exists(os.path.join(d, "rank_data"))
