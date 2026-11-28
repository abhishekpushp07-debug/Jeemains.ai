# JLive Command: CEO read-only API + Mission redirect UTM (GETs only, nothing written)
import os
import httpx
import pytest

API = "http://localhost:8001/api"


def _token():
    t = os.environ.get("CEO_API_TOKEN")
    if not t:
        for line in open("/app/backend/.env"):
            if line.startswith("CEO_API_TOKEN="):
                t = line.split("=", 1)[1].strip().strip('"')
    return t


@pytest.fixture(scope="module")
def c():
    with httpx.Client(base_url=API, timeout=30, headers={"Authorization": f"Bearer {_token()}"}) as cl:
        yield cl


EPS = ["/ceo/users", "/ceo/rapid/daily", "/ceo/economy/daily", "/ceo/mission", "/ceo/mission/links", "/ceo/dream"]


# auth: 401 without / wrong bearer
@pytest.mark.parametrize("ep", EPS)
def test_401_without_token(ep):
    assert httpx.get(API + ep, timeout=30).status_code == 401
    assert httpx.get(API + ep, timeout=30, headers={"Authorization": "Bearer nope"}).status_code == 401


# 200 + Cache-Control no-store
@pytest.mark.parametrize("ep", EPS)
def test_200_no_store(c, ep):
    r = c.get(ep)
    assert r.status_code == 200, r.text[:200]
    assert "no-store" in r.headers.get("cache-control", "")


# users: is_test, stable sort last_day desc / uid asc, include_test
def test_users_sort_and_is_test(c):
    real = c.get("/ceo/users", params={"limit": 500}).json()
    allp = c.get("/ceo/users", params={"limit": 500, "include_test": 1}).json()
    assert allp["total"] >= real["total"]
    items = allp["items"]
    assert all(isinstance(i.get("is_test"), bool) for i in items)
    assert not any(i["is_test"] for i in real["items"])
    keys = [(-(0 if not i.get("last_active") else int(str(i["last_active"]).replace("-", ""))), i["uid"]) for i in items]
    assert keys == sorted(keys)
    for i in real["items"][:50]:
        for f in ("phone", "pin", "pin_hash", "token"):
            assert f not in i


def test_users_page_zero_no_500(c):
    assert c.get("/ceo/users", params={"page": 0}).status_code != 500
    assert c.get("/ceo/mission/links", params={"page": 0}).status_code != 500


@pytest.mark.parametrize("ep", ["/ceo/rapid/daily", "/ceo/economy/daily"])
def test_bad_ranges_400(c, ep):
    assert c.get(ep, params={"from": "2026-11-28", "to": "2026-11-01"}).status_code == 400
    assert c.get(ep, params={"from": "28-11-2026"}).status_code == 400
    assert c.get(ep, params={"from": "2020-01-01", "to": "2026-11-28"}).status_code == 400
    r = c.get(ep, params={"from": "2026-11-20", "to": "2026-11-22"})
    assert r.status_code == 200


def test_mission_links_limit_cap(c):
    r = c.get("/ceo/mission/links", params={"limit": 9999}).json()
    assert r["limit"] == 500 and len(r["items"]) <= 500


UA = {"User-Agent": "Mozilla/5.0 (Linux; Android 14) AppleWebKit/537.36 Chrome/130 Mobile Safari/537.36"}


# Mission redirect UTM (nonexistent code: nothing written)
def test_mission_redirect_utm():
    r = httpx.get(API + "/j/ZZZZZZ2", headers=UA, follow_redirects=False, timeout=30)
    assert r.status_code == 302
    assert r.headers["location"] == "https://jeelive.ai/?utm_source=mission&utm_medium=referral&utm_campaign=mission-ZZZZZZ2"
    assert "no-store" in r.headers.get("cache-control", "")


def test_mission_redirect_bad_code():
    r = httpx.get(API + "/j/bad!", headers=UA, follow_redirects=False, timeout=30)
    assert r.status_code == 302 and r.headers["location"] == "https://jeelive.ai"
