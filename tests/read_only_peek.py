# Read-only look at the live website through the app's own server (QA learner): sign in, then GETs only.
# Prints: the raw auth answers (phone masked, for the website's "naam nahi aata" question), one finished paper's
# AI solutions (shape and size), and whether the chapter list honours per_page=100.
import json, os, sys, uuid, urllib.request

BACKEND = os.environ.get("BACKEND") or [l.split("=", 1)[1].strip().strip('"') for l in open("/app/frontend/.env") if l.startswith("EXPO_PUBLIC_BACKEND_URL=")][0]
sys.path.insert(0, "/app/tests")
from shine_helpers import PHONE, PIN  # noqa: E402

SID = str(uuid.uuid4())

def call(path, body=None):
    req = urllib.request.Request(BACKEND + "/api/jl" + path, data=None if body is None else json.dumps(body).encode(),
                                 method="GET" if body is None else "POST",
                                 headers={"Accept": "application/json", "Content-Type": "application/json", "X-JL-Sid": SID})
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            return r.status, r.read()
    except urllib.error.HTTPError as e:
        return e.code, e.read()

def mask(text):
    return text.replace(PHONE, "XXXXXX" + PHONE[-4:])

status, raw = call("/auth/phone", {"phone": PHONE, "pin": PIN})
print("sign-in", status)
for path in ["/auth/me", "/auth/session"]:
    s, raw = call(path)
    print(f"\n=== GET {path} -> {s}\n" + mask(raw.decode()[:1500]))

s, raw = call("/my/tests?tab=completed&page=1&q=&status=all&exam=")
tests = (json.loads(raw).get("data") or {}).get("items") or []
print("\ncompleted:", [(t.get("id"), t.get("exam"), t.get("title")) for t in tests][:12])
for t in tests[:12]:
    s, raw = call(f"/attempts/{t['id']}/ai-solutions")
    body = json.loads(raw) if raw else {}
    data = body.get("data", body)
    items = (data or {}).get("items") or []
    states = {}
    for it in items:
        states[it.get("state")] = states.get(it.get("state"), 0) + 1
    print(f"ai {t['id'][:8]} {t.get('title','')[:40]!r}: {s} {len(raw)} bytes, keys={list((data or {}).keys())}, states={states}")
    if items and "--sample" in sys.argv:
        ready = next((x for x in items if x.get("state") == "ready"), items[0])
        print(json.dumps(ready)[:1500])
        sys.argv.remove("--sample")

for q in ["per_page=100", ""]:
    s, raw = call("/exam-navigation/jee-main/catalogue?kind=chapters&subject=Physics&q=&page=1" + ("&" + q if q else ""))
    d = (json.loads(raw).get("data") or {})
    print(f"\ncatalogue {q or '(default)'}: {s} total={d.get('total')} pages={d.get('pages')} rows={len(d.get('items') or [])} per_page={d.get('per_page')}")
