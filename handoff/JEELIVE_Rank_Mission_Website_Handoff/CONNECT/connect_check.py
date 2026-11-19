#!/usr/bin/env python3
"""One command that proves the website can talk to the JEELIVE.AI app server (Rank, Mission, Dream college).

    python connect_check.py                                   # the live app server
    python connect_check.py https://<host>/api                # any other address (preview, staging)
    python connect_check.py https://<website>/api --website   # the website's own backend, once the connector is mounted
    python connect_check.py --pdf                             # also draws the seven PDFs (slower)

Signed-in checks (Mission, Dream college) run only when a real website session is supplied:

    JEELIVE_ACCESS_COOKIE='<value of the access_token cookie of a signed-in student>' python connect_check.py

The cookie is never printed. Only read requests are made, except one "Mission link" row that the app server creates the
first time any student asks for their link (that is the feature itself). Python 3.8+, no packages needed.
Exit code 0 = everything passed.
"""
import json
import os
import sys
import time
import urllib.error
import urllib.request

LIVE = "https://jeelive-mobile.emergent.host/api"
args = [a for a in sys.argv[1:] if not a.startswith("--")]
flags = {a for a in sys.argv[1:] if a.startswith("--")}
BASE = (args[0] if args else os.environ.get("JEELIVE_APP_API", LIVE)).rstrip("/")
WEBSITE = "--website" in flags
COOKIE = os.environ.get("JEELIVE_ACCESS_COOKIE", "").strip()
COOKIE_NAME = os.environ.get("JEELIVE_SESSION_COOKIE", "access_token")
UA = "jeelive-connect-check/1.0"
results = []


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, *a, **k):
        return None


opener = urllib.request.build_opener(NoRedirect)


def call(method, path, body=None, headers=None, timeout=40):
    """-> (status, headers, parsed JSON or raw bytes)"""
    h = {"User-Agent": UA, "Accept": "application/json", **(headers or {})}
    data = None
    if body is not None:
        data = json.dumps(body).encode()
        h["Content-Type"] = "application/json"
    req = urllib.request.Request(BASE + path, data=data, method=method, headers=h)
    try:
        with opener.open(req, timeout=timeout) as r:
            status, head, raw = r.status, dict(r.headers), r.read()
    except urllib.error.HTTPError as e:
        status, head, raw = e.code, dict(e.headers), e.read()
    try:
        return status, head, json.loads(raw)
    except ValueError:
        return status, head, raw


def check(name, fn):
    t0 = time.time()
    try:
        note = fn() or ""
        ok = True
    except AssertionError as e:
        ok, note = False, f"unexpected answer: {e}"
    except Exception as e:  # noqa: BLE001 - a network error is a failed check, not a crash
        ok, note = False, f"{type(e).__name__}: {e}"
    ms = round((time.time() - t0) * 1000)
    results.append(ok)
    print(f"  {'PASS' if ok else 'FAIL'}  {name:<46} {ms:>5} ms  {note}")


def expect(status, want, data):
    assert status == want, f"HTTP {status} (wanted {want}): {str(data)[:160]}"


FORM = {"marks": 180, "level": "normal", "category": "GEN", "female": False, "pwd": False, "state": "Bihar", "branches": []}
seen = {}


def meta():
    s, _, d = call("GET", "/rank/meta")
    expect(s, 200, d)
    assert len(d["states"]) == 36 and len(d["branches"]) == 20 and len(d["chart"]) == 50, "states / branches / chart size"
    return f"{d['candidates']:,} JEE candidates, {d['comedk']['candidates']:,} COMEDK"


def estimate_jee():
    s, _, d = call("POST", "/rank/estimate", {"exam": "jee", "marks": 180, "level": "normal", "category": "OBC-NCL", "pwd": False})
    expect(s, 200, d)
    r = d["result"]
    assert [x["level"] for x in d["levels"]] == ["tough", "normal", "easy"] and r["crl"][0] <= r["crl"][1] and "cat_rank" in r
    return f"180 marks -> CRL {r['crl'][0]:,} to {r['crl'][1]:,}, percentile {r['percentile'][0]} to {r['percentile'][1]}"


def estimate_comedk():
    s, _, d = call("POST", "/rank/estimate", {"exam": "comedk", "marks": 110, "level": "normal", "category": "GEN", "pwd": False})
    expect(s, 200, d)
    assert d["exam"] == "comedk" and len(d["sources"]) == 3 and d["rank"][0] <= d["mid"] <= d["rank"][1]
    return f"110 marks -> rank {d['rank'][0]:,} to {d['rank'][1]:,}"


def percentile():
    s, _, d = call("POST", "/rank/percentile", {"percentile": 97.4567, "category": "GEN", "pwd": False})
    expect(s, 200, d)
    assert [m["level"] for m in d["marks"]] == ["tough", "normal", "easy"] and not d["result"]["from_marks"]
    return f"97.4567 percentile -> CRL {d['result']['crl'][0]:,} to {d['result']['crl'][1]:,}"


def predict():
    s, _, d = call("POST", "/rank/predict", {**FORM, "segment": "all", "page": 1})
    expect(s, 200, d)
    assert d["items"] and len(d["items"]) <= 25 and d["pages"] in (1, 2) and set(d["counts"]) == {"all", "NIT", "IIIT", "GFTI", "DELHI"}
    assert all(i["tag"] in ("safe", "likely", "borderline") for i in d["items"])
    seen["seat"] = d["items"][0]
    return f"{d['reach']['all']} college-branches in reach, top: {d['items'][0]['college']} · {d['items'][0]['branch']}"


def predict_page2():
    s, _, d = call("POST", "/rank/predict", {**FORM, "segment": "NIT", "page": 2})
    expect(s, 200, d)
    assert d["segment"] == "NIT" and d["page"] == 2 and all(i["type"] == "NIT" for i in d["items"])


def predict_chart():
    s, _, d = call("POST", "/rank/predict", {"percentile": 99.0, "level": "normal", "category": "GEN", "female": False, "pwd": False,
                                             "state": None, "branches": [], "segment": "all", "page": 1, "page_size": 20})
    expect(s, 200, d)
    assert len(d["items"]) <= 20 and d["near"] == [] and d["pages"] == 1


def college():
    x = seen["seat"]
    s, _, d = call("POST", "/rank/college", {**FORM, "inst": x["inst"], "prog": x["prog"], "quota": x["quota"], "gender": x["gender"], "seat": x["seat"]})
    expect(s, 200, d)
    assert d["rows"] and len(d["rows"][0]["cells"]) == len(d["rounds"]) and any(r["prog"] == x["prog"] for r in d["rows"])
    return f"{d['college']['short']}: {d['total']} branches, rounds {', '.join(d['rounds'])}"


def bitsat():
    s, _, d = call("POST", "/rank/bitsat", {"score": 280, "campus": "all", "degree": "all"})
    expect(s, 200, d)
    r = d["result"]
    assert r["total_all"] == len(d["items"]) + len(d["near"]) + len(d["rest"]) and len(d["years"]) == 5
    return f"280 / {r['max']} clears {r['cleared_all']} of {r['total_all']} programs"


def comedk():
    s, _, d = call("POST", "/rank/comedk", {"marks": 110, "branches": [], "area": "all", "page": 1})
    expect(s, 200, d)
    assert d["items"] and d["rounds"] == ["R1", "R2", "R3", "R4"] and set(d["counts"]) == {"all", "blr", "other"}
    seen["comedk"] = d["items"][0]
    return f"{d['result']['in_reach']} of {d['result']['total']} GM college-courses in reach"


def comedk_college():
    x = seen["comedk"]
    s, _, d = call("POST", "/rank/comedk/college", {"marks": 110, "branches": [], "code": x["code"], "course": x["cc"]})
    expect(s, 200, d)
    assert any(r["cc"] == x["cc"] for r in d["rows"]) and len(d["rows"][0]["cells"]) == 4
    return f"{d['college']['short']}: {d['total']} GM courses"


def colleges():
    s, _, d = call("GET", "/rank/colleges")
    expect(s, 200, d)
    assert d["jee"] and d["comedk"] and [c["campus"] for c in d["bitsat"]] == ["Pilani", "Goa", "Hyderabad"]
    return f"{len(d['jee'])} JEE colleges, {len(d['comedk'])} COMEDK colleges, 3 BITS campuses"


def target_jee():
    s, _, d = call("POST", "/rank/target/jee", {"inst": seen["seat"]["inst"], "category": "GEN", "female": False, "pwd": False, "state": "Bihar"})
    expect(s, 200, d)
    f = d["rows"][0]["final"]
    assert set(f["marks"]) == {"tough", "normal", "easy"} and f["marks"]["tough"] <= f["marks"]["normal"] <= f["marks"]["easy"]
    return f"{d['college']['short']} · {d['rows'][0]['branch']}: {f['marks']['normal']}+ marks on a normal paper"


def target_comedk():
    s, _, d = call("POST", "/rank/target/comedk", {"code": seen["comedk"]["code"]})
    expect(s, 200, d)
    f = d["rows"][0]["final"]
    assert f["marks"][0] <= f["mid"] <= f["marks"][1]


def target_bitsat():
    s, _, d = call("GET", "/rank/target/bitsat")
    expect(s, 200, d)
    assert d["max"] == 390 and all(r["safe"] == min(390, r["cutoff"] + 10) for r in d["rows"])


def compare():
    x, k = seen["seat"], seen["comedk"]
    items = [{"exam": "jee", "id": f"jee-{x['prog']}", "prog": x["prog"], "quota": x["quota"], "gender": x["gender"], "path": x["path"]},
             {"exam": "comedk", "id": k["id"]}, {"exam": "bitsat", "id": "Pilani-cs"}]
    seen["items"] = items
    s, _, d = call("POST", "/rank/compare", {"items": items})
    expect(s, 200, d)
    assert len(d["items"]) == 3 and not any(c.get("missing") for c in d["items"])


def compare_colleges():
    s, _, d = call("POST", "/rank/compare/colleges", {"items": [{"exam": "jee", "id": str(seen["seat"]["inst"])}, {"exam": "comedk", "id": seen["comedk"]["code"]},
                                                              {"exam": "bitsat", "id": "Pilani"}], "category": "GEN", "female": False, "pwd": False, "state": "Bihar"})
    expect(s, 200, d)
    assert len(d["items"]) == 3 and all(c.get("easiest") and c.get("toughest") for c in d["items"])


def validation():
    s, _, d = call("POST", "/rank/predict", {"marks": 999})
    expect(s, 422, d)
    assert isinstance(d["detail"], list) and d["detail"][0]["loc"][-1] == "marks", "a field error is a list"
    s, _, d = call("POST", "/rank/predict", {})
    expect(s, 422, d)
    assert isinstance(d["detail"], str), "a rule error is a short sentence"
    return f"422 sentence: \"{d['detail']}\""


def not_found():
    s, _, d = call("POST", "/rank/college", {"marks": 180, "inst": 99999})
    expect(s, 404, d)
    return f"404 sentence: \"{d['detail']}\""


def pdfs():
    x, k = seen["seat"], seen["comedk"]
    jobs = (("/rank/pdf/jee", {**FORM, "segment": "all"}), ("/rank/pdf/comedk", {"marks": 110, "branches": [], "area": "all"}),
            ("/rank/pdf/bitsat", {"score": 280, "campus": "all", "degree": "all"}),
            ("/rank/pdf/target/jee", {"inst": x["inst"], "category": "GEN", "female": False, "pwd": False, "state": "Bihar"}),
            ("/rank/pdf/target/comedk", {"code": k["code"]}), ("/rank/pdf/target/bitsat", {"campus": "all"}),
            ("/rank/pdf/saved", {"items": seen["items"], "tags": ["borderline", "likely", None], "pick": [0, 1, 2]}))
    sizes = []
    for path, body in jobs:
        s, head, raw = call("POST", path, body, headers={"Accept": "application/pdf"}, timeout=60)
        expect(s, 200, raw)
        assert isinstance(raw, bytes) and raw[:5] == b"%PDF-", f"{path} is not a PDF"
        assert "filename=" in {k2.lower(): v for k2, v in head.items()}.get("content-disposition", ""), f"{path} has no file name"
        sizes.append(len(raw) // 1024)
    return f"7 PDFs, {min(sizes)}-{max(sizes)} KB"


def share_link():
    if WEBSITE:
        s, head, _ = call("GET", "/j/AAAAAAA")
        assert s == 302, f"HTTP {s}"
        return f"302 -> {head.get('Location') or head.get('location')}"
    s, head, _ = call("GET", "/j/AAAAAAA", headers={"User-Agent": "Mozilla/5.0 (connect check)"})
    where = head.get("Location") or head.get("location")
    assert s == 302 and where and where.startswith("https://"), f"HTTP {s} -> {where}"
    return f"302 -> {where} (an unknown code is not counted)"


def student_headers():
    """App server: swap the session cookie for a 15-minute pass. Website: just send the cookie."""
    if WEBSITE:
        return {"Cookie": f"{COOKIE_NAME}={COOKIE}"}
    if "token" not in seen:
        s, _, d = call("POST", "/rf/access", {"access_cookie": COOKIE})
        expect(s, 200, d)
        seen["token"] = d["token"]
    return {"Authorization": f"Bearer {seen['token']}"}


def mission():
    s, _, d = call("GET", "/mission/me" if WEBSITE else "/rf/mission/me", headers=student_headers())
    expect(s, 200, d)
    assert len(d["code"]) == 7 and d["helped"] >= 0 and 0 <= d["week"] <= d["helped"]
    return f"link code issued, helped {d['helped']}, this week {d['week']}"


def dream():
    s, _, d = call("GET", "/dream" if WEBSITE else "/rf/dream", headers=student_headers())
    expect(s, 200, d)
    assert set(d) == {"dreams", "mocks", "cheered"}
    return f"{len(d['dreams'])} dreams, {len(d['mocks'])} full mocks"


def signed_out():
    s, _, d = call("GET", "/mission/me" if WEBSITE else "/rf/mission/me")
    expect(s, 401, d)
    return "401 without a session, as it should be"


def revoke():
    if not WEBSITE and "token" in seen:
        s, _, d = call("POST", "/rf/access/revoke", headers={"Authorization": f"Bearer {seen['token']}"})
        expect(s, 200, d)


print(f"\nJEELIVE.AI connect check -> {BASE}{'  (website connector)' if WEBSITE else ''}\n")
print("Rank (public)")
for name, fn in (("GET  /rank/meta", meta), ("POST /rank/estimate  (JEE Main)", estimate_jee), ("POST /rank/estimate  (COMEDK)", estimate_comedk),
                 ("POST /rank/percentile", percentile), ("POST /rank/predict", predict), ("POST /rank/predict  (NIT, page 2)", predict_page2),
                 ("POST /rank/predict  (chart line, 20 rows)", predict_chart), ("POST /rank/college", college), ("POST /rank/bitsat", bitsat),
                 ("POST /rank/comedk", comedk), ("POST /rank/comedk/college", comedk_college), ("GET  /rank/colleges", colleges),
                 ("POST /rank/target/jee", target_jee), ("POST /rank/target/comedk", target_comedk), ("GET  /rank/target/bitsat", target_bitsat),
                 ("POST /rank/compare", compare), ("POST /rank/compare/colleges", compare_colleges),
                 ("422 on a wrong form", validation), ("404 on an unknown college", not_found)):
    check(name, fn)
if "--pdf" in flags:
    check("POST /rank/pdf/*  (7 files)", pdfs)
print("\nMission")
check("GET  /j/{code}  (share link)", share_link)
check("signed-out request is refused", signed_out)
if COOKIE:
    check("GET  mission/me  (signed in)", mission)
    check("GET  dream  (signed in)", dream)
    check("pass handed back", revoke)
else:
    print("  SKIP  signed-in checks: set JEELIVE_ACCESS_COOKIE to run them")
bad = results.count(False)
print(f"\n{'ALL ' + str(len(results)) + ' CHECKS PASSED' if not bad else str(bad) + ' OF ' + str(len(results)) + ' CHECKS FAILED'}\n")
sys.exit(1 if bad else 0)
