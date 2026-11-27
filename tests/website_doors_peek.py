# Read-only: which website doors the app waits for answer on LIVE today (QA learner; sign-in, then GETs only).
import json, os, sys
sys.argv.append("--quiet")
os.environ.setdefault("BACKEND", "http://localhost:8001")
sys.path.insert(0, "/app/tests")
import urllib.request, uuid  # noqa: E402
from shine_helpers import PHONE, PIN  # noqa: E402

BACKEND, SID = os.environ["BACKEND"], str(uuid.uuid4())

def call(path, body=None, base="/api/jl"):
    req = urllib.request.Request(BACKEND + base + path, data=None if body is None else json.dumps(body).encode(),
                                 method="GET" if body is None else "POST",
                                 headers={"Accept": "application/json", "Content-Type": "application/json", "X-JL-Sid": SID})
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            return r.status, r.read()
    except urllib.error.HTTPError as e:
        return e.code, e.read()

print("sign-in", call("/auth/phone", {"phone": PHONE, "pin": PIN})[0])
rows = []
for subject in ["Physics", "Chemistry", "Mathematics"]:
    for page in range(1, 4):
        s, raw = call(f"/exam-navigation/jee-main/catalogue?kind=chapters&subject={subject}&q=&page={page}")
        d = json.loads(raw).get("data") or {}
        rows += d.get("items") or []
        if page >= (d.get("pages") or 1):
            break
mins = sorted({(r.get("rules") or {}).get("minutes") for r in rows}, key=str)
print(f"chapter tests: {len(rows)}, minutes seen: {mins}, class_level on rows: {sum('class_level' in r for r in rows)}")
first = rows[0]["id"] if rows else "x"
for path in ["/choice/bank?exam=jee-main", f"/choice/chapters/{first}/questions?page=1", "/matched",
             "/series/all-india-jee/leaderboard", "/series/all-india-jee/my-days", "/series/all-india-jee", 
             "/my/tests?tab=completed&page=1&per_page=100", "/account/delete", "/auth/me"]:
    s, raw = call(path)
    text = raw.decode(errors="replace")
    extra = ""
    if path.startswith("/my/tests") and s == 200:
        d = json.loads(raw).get("data") or {}
        it = (d.get("items") or [{}])[0]
        extra = f" rows={len(d.get('items') or [])} pages={d.get('pages')} test_kind_on_row={'test_kind' in it}"
    if path == "/auth/me":
        extra = f" display_name_key={'display_name' in text}"
    if path == "/series/all-india-jee" and s == 200:
        d = json.loads(raw).get("data") or {}
        extra = f" start={d.get('start_date') or d.get('first_date')} last={d.get('last_date')}"
    print(f"GET {path} -> {s}{extra}  {text[:140] if s >= 400 else ''}")
s, raw = call("/choice/bank", base="/api")
print("app server /api/choice/bank ->", s, raw.decode()[:200])
