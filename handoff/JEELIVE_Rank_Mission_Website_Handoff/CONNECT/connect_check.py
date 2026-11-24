#!/usr/bin/env python3
"""One command that proves the website can talk to the JEELIVE.AI app server (Rank with the new Cut off, Mission,
Dream college).

    python connect_check.py                                   # the live app server
    python connect_check.py https://<host>/api                # any other address (preview, staging)
    python connect_check.py https://<website>/api --website   # the website's own backend, once the connector is mounted
    python connect_check.py --pdf                             # also draws the PDFs (slower)

Signed-in checks (Mission, Dream college) run only when a real website session is supplied:

    JEELIVE_ACCESS_COOKIE='<value of the access_token cookie of a signed-in student>' python connect_check.py

The cookie is never printed. Only read requests are made, except one "Mission link" row that the app server creates the
first time any student asks for their link (that is the feature itself). Python 3.8+, no packages needed.
Exit code 0 = everything passed. WAIT = the server is fine but does not have the new Cut off part yet.
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


class Waiting(Exception):
    """The server is fine but does not have this (new) part yet."""


def check(name, fn):
    t0 = time.time()
    try:
        note = fn() or ""
        ok = True
    except Waiting as e:
        ok, note = None, str(e)
    except AssertionError as e:
        ok, note = False, f"unexpected answer: {e}"
    except Exception as e:  # noqa: BLE001 - a network error is a failed check, not a crash
        ok, note = False, f"{type(e).__name__}: {e}"
    ms = round((time.time() - t0) * 1000)
    results.append(ok)
    print(f"  {'PASS' if ok else 'WAIT' if ok is None else 'FAIL'}  {name:<46} {ms:>5} ms  {note}")


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


# ------------------------------------------------------------------ Cut off (NEW) and the scorecard rank
TAGS = ("safe", "likely", "borderline")
NOT_YET = "this server does not have Cut off yet: the app project has to publish it. Until then test the development address"


def opts():
    if seen.get("no_cutoff"):
        raise Waiting("needs Cut off on this server (see the line above)")
    assert "cut" in seen, "GET /rank/cutoff/options did not answer (see above)"
    return seen["cut"]


def cut(body, want=200):
    opts()
    s, _, d = call("POST", "/rank/cutoff", body)
    expect(s, want, d)
    return d


def cutoff_options():
    s, _, d = call("GET", "/rank/cutoff/options")
    if s == 404:
        seen["no_cutoff"] = True
        raise Waiting(NOT_YET)
    expect(s, 200, d)
    assert d["limit"] == 100 and all(d[e]["colleges"] and d[e]["branches"] for e in ("jee", "comedk", "bitsat")), "three exams, two lists each"
    assert d["jee"]["score"] == ["marks", "percentile", "rank"] and d["comedk"]["score"] == ["marks", "rank"] and d["bitsat"]["score"] == ["marks"]
    seen["cut"] = d
    return " · ".join(f"{d[e]['name']} {len(d[e]['colleges'])} colleges + {len(d[e]['branches'])} branches" for e in ("jee", "comedk", "bitsat"))


def cutoff_college():
    d = cut({"exam": "jee", "by": "college", "key": opts()["jee"]["colleges"][0]["key"]})
    assert d["rows"] and d["you"] is None and d["eligible"] is None and d["near"] == [] and d["limit"] is None
    assert all(r["tag"] is None and len(r["cells"]) == len(d["columns"]) for r in d["rows"]), "every row has one cell per column and no tag"
    assert all(r["save"]["id"].startswith("jee-") and "trend" in r for r in d["rows"]), "every row carries save (shortlist item) and trend (last-year arrow or null)"
    arrows = sum(1 for r in d["rows"] if r["trend"])
    return f"{d['title']}: {d['total']} branches, {', '.join(d['columns'])}; {arrows} with a last-year arrow"


def cutoff_branch():
    a = cut({"exam": "jee", "by": "branch", "key": "Computer Science"})
    assert a["limit"] == 100 and len(a["rows"]) == min(100, a["total"]) and a["you"] is None, "a branch list is the first 100"
    b = cut({"exam": "jee", "by": "branch", "key": "Computer Science", "marks": 200, "level": "normal"})
    you = b["you"]
    assert you["source"] == "marks" and sum(you["counts"].values()) == b["eligible"] <= b["total"] == a["total"], "counts add up to eligible"
    assert len(b["rows"]) == min(100, b["eligible"]) and all(r["tag"] in TAGS for r in b["rows"]), "with a score every row has a tag"
    assert len(b["near"]) <= 3 and all(n["tag"] is None and n["gap"] for n in b["near"]), "near misses carry a gap sentence and no tag"
    return f"Computer Science: top {len(a['rows'])} of {a['total']}; at 200 marks {b['eligible']} eligible ({you['counts']['safe']} Safe, {you['counts']['likely']} Likely, {you['counts']['borderline']} Borderline)"


def cutoff_score_order():
    key = opts()["jee"]["colleges"][0]["key"]
    d = cut({"exam": "jee", "by": "college", "key": key, "rank": 7500, "percentile": 90, "marks": 100})
    assert d["you"]["source"] == "rank" and d["you"]["rank"]["range"] == [7500, 7500], "a scorecard rank wins"
    d = cut({"exam": "jee", "by": "college", "key": key, "percentile": 99.5, "marks": 100})
    assert d["you"]["source"] == "percentile", "a percentile wins over marks"
    return "rank, then percentile, then marks"


def cutoff_comedk():
    d = cut({"exam": "comedk", "by": "branch", "key": "Computer Science", "rank": 30000})
    assert d["columns"] == ["R1", "R2", "R3", "R4"] and d["metric"] == "rank" and d["eligible"] == sum(d["you"]["counts"].values())
    return f"rank 30,000: {d['eligible']} of {d['total']} Computer Science college-courses eligible"


def cutoff_bitsat():
    d = cut({"exam": "bitsat", "by": "college", "key": "Pilani", "marks": 280})
    assert len(d["columns"]) == 5 and d["metric"] == "score" and d["you"]["rank"] is None and d["you"]["percentile"] is None
    assert all(c.get("state") is None for r in d["rows"] for c in r["cells"][:-1]), "only the newest year is green or amber"
    return f"280 / 390: {d['eligible']} of {d['total']} Pilani programs eligible; years {d['columns'][0]}-{d['columns'][-1]}, no rounds"


def cutoff_refusals():
    d = cut({"exam": "comedk", "by": "branch", "key": "Computer Science", "percentile": 90}, 422)
    assert isinstance(d["detail"], str), "a rule error is a short sentence"
    cut({"exam": "bitsat", "by": "college", "key": "Pilani", "rank": 5}, 422)
    n = cut({"exam": "jee", "by": "college", "key": "99999"}, 404)
    return f"422 \"{d['detail']}\" · 404 \"{n['detail']}\""


def predict_rank():
    s, _, d = call("POST", "/rank/predict", {"rank": 7500, "level": "normal", "category": "OBC-NCL", "female": False, "pwd": False,
                                             "state": None, "branches": [], "segment": "all", "page": 1})
    if s == 422 and seen.get("no_cutoff"):
        raise Waiting("the scorecard rank arrives with the same publish")
    expect(s, 200, d)
    r = d["result"]
    assert r["crl"] == [7500, 7500] and r.get("source") == "rank" and not r["from_marks"] and d["items"], "the card shows the rank itself"
    return f"{r['summary']} -> {d['reach']['all']} college-branches in reach"


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


def cutoff_pdf():
    """The Cut off list as a PDF: the same body as POST /rank/cutoff, with and without a score."""
    key = opts()["jee"]["colleges"][0]["key"]
    sizes = []
    for body, part in (({"exam": "jee", "by": "college", "key": key, "marks": 200, "level": "normal", "category": "GEN", "female": False, "pwd": False, "state": None}, "cutoff-jee-college-200-marks"),
                       ({"exam": "bitsat", "by": "college", "key": "Pilani"}, "cutoff-bitsat-college-all")):
        s, head, raw = call("POST", "/rank/pdf/cutoff", body, headers={"Accept": "application/pdf"}, timeout=60)
        if s == 404:
            raise Waiting("this server has Cut off but not its PDF yet: it comes with the app project's next publish")
        expect(s, 200, raw)
        assert isinstance(raw, bytes) and raw[:5] == b"%PDF-", "not a PDF"
        assert part in {k2.lower(): v for k2, v in head.items()}.get("content-disposition", ""), f"file name should contain {part}"
        sizes.append(len(raw) // 1024)
    return f"2 PDFs, {min(sizes)}-{max(sizes)} KB"


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
print("\nCut off (NEW) and the scorecard rank (public)")
for name, fn in (("GET  /rank/cutoff/options", cutoff_options), ("POST /rank/cutoff  (college, every round)", cutoff_college),
                 ("POST /rank/cutoff  (branch, top 100, score)", cutoff_branch), ("POST /rank/cutoff  (which score wins)", cutoff_score_order),
                 ("POST /rank/cutoff  (COMEDK)", cutoff_comedk), ("POST /rank/cutoff  (BITSAT)", cutoff_bitsat),
                 ("422 / 404 on a wrong Cut off request", cutoff_refusals), ("POST /rank/predict  (scorecard rank)", predict_rank)):
    check(name, fn)
if "--pdf" in flags:
    print("\nPDFs")
    check("POST /rank/pdf/*  (7 files)", pdfs)
    check("POST /rank/pdf/cutoff  (NEW)", cutoff_pdf)
print("\nMission")
check("GET  /j/{code}  (share link)", share_link)
check("signed-out request is refused", signed_out)
if COOKIE:
    check("GET  mission/me  (signed in)", mission)
    check("GET  dream  (signed in)", dream)
    check("pass handed back", revoke)
else:
    print("  SKIP  signed-in checks: set JEELIVE_ACCESS_COOKIE to run them")
bad, waiting = results.count(False), results.count(None)
if bad:
    print(f"\n{bad} OF {len(results)} CHECKS FAILED\n")
elif waiting:
    print(f"\n{results.count(True)} CHECKS PASSED, {waiting} WAIT: this server does not have Cut off yet (new). It will after the app project's next publish.\n")
else:
    print(f"\nALL {len(results)} CHECKS PASSED\n")
sys.exit(1 if bad or waiting else 0)
