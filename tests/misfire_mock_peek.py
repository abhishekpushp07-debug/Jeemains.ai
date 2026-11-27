# Read-only: what the QA learner's Misfire and finished results carry, for the Misfire Mock (sign in, then GETs only).
# Which fields a Misfire item has (answer? exam? question?), the page size, and what a released result's question
# carries (answer, accepted_answers, disposition, scoring, type, subject, solution). Never starts a paper, never POSTs a try.
import json, os, sys, time, uuid, urllib.request
from collections import Counter

BACKEND = os.environ.get("BACKEND") or [l.split("=", 1)[1].strip().strip('"') for l in open("/app/frontend/.env") if l.startswith("EXPO_PUBLIC_BACKEND_URL=")][0]
sys.path.insert(0, "/app/tests")
from shine_helpers import PHONE, PIN  # noqa: E402

SID = str(uuid.uuid4())


def call(path, body=None):
    req = urllib.request.Request(BACKEND + "/api/jl" + path, data=None if body is None else json.dumps(body).encode(),
                                 method="GET" if body is None else "POST",
                                 headers={"Accept": "application/json", "Content-Type": "application/json", "X-JL-Sid": SID})
    t = time.perf_counter()
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            return r.status, r.read(), (time.perf_counter() - t) * 1000
    except urllib.error.HTTPError as e:
        return e.code, e.read(), (time.perf_counter() - t) * 1000


def data(raw):
    j = json.loads(raw) if raw else {}
    return j.get("data", j) if isinstance(j, dict) else j


print("sign-in", call("/auth/phone", {"phone": PHONE, "pin": PIN})[0])
s, raw, ms = call("/my/misfire/summary")
print("summary", s, round(ms), json.dumps(data(raw))[:600])
s, raw, ms = call("/my/misfire?status=open&subject=&chapter=&page=1")
page = data(raw)
items = page.get("items") or []
print("page1", s, round(ms), "items", len(items), "total", page.get("total"), "pages", page.get("pages"), "chapters", len(page.get("chapters") or []))
if items:
    it = items[0]
    print("item keys:", sorted(it.keys()))
    print("question keys:", sorted((it.get("question") or {}).keys()))
    print("exam values:", Counter(i.get("exam") for i in items), "subjects:", Counter(i.get("subject") for i in items), "types:", Counter(i.get("type") for i in items))
    print("answer present:", sum(1 for i in items if i.get("answer")), "id sample:", it.get("id"), "attempt", it.get("attempt_id"), "qid", it.get("question_id"))
    print("chapters sample:", (page.get("chapters") or [])[:6])
    att = it["attempt_id"]
    s, raw, ms = call(f"/attempts/{att}/results?score_version=original")
    r = data(raw)
    qs = r.get("questions") or []
    print("result", s, round(ms), len(raw), "B", "q", len(qs), "status", r.get("status"), "exam", r.get("exam"), "rules", r.get("rules"))
    if qs:
        print("result question keys:", sorted(qs[0].keys()))
        for typ in ("mcq", "integer", "numerical", "decimal"):
            q = next((q for q in qs if q.get("type") == typ), None)
            if q:
                print(f"  {typ}: answer={q.get('answer')!r} accepted={q.get('accepted_answers')!r} disposition={q.get('disposition')!r} scoring={q.get('scoring')!r} "
                      f"options={list((q.get('options') or {}).keys())} render={q.get('render_mode')} pieces={bool(q.get('pieces'))} assets={q.get('asset_count')} sol_assets={q.get('solution_asset_count')} "
                      f"sol_text={bool(q.get('solution_text'))} subject={q.get('subject')!r} topic={q.get('topic')!r} outcome={q.get('outcome')} response={q.get('response')!r}")
        print("types:", Counter(q.get("type") for q in qs), "dispositions:", Counter(q.get("disposition") for q in qs))
        print("answer kinds:", Counter(type(q.get("answer")).__name__ for q in qs), "accepted lens:", Counter(len(q.get("accepted_answers") or []) for q in qs))
        print("integer answers sample:", [ (q.get("answer"), q.get("accepted_answers")) for q in qs if q.get("type") != "mcq"][:8])
        mid = next((q for q in qs if q.get("id") == it.get("question_id")), None)
        print("misfire q found in result:", bool(mid))
