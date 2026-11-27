# Read-only: the QA learner's real analysis answers through the app's own server (sign in, then GETs only).
# For the AITS readiness check: which question fields come back (topic, difficulty, difficulty_source), whether chapters
# are filled, the size of the answer and how long it takes (3 tries each). Never opens Solutions, never starts a paper.
import json, os, sys, time, uuid, urllib.request

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


print("sign-in", call("/auth/phone", {"phone": PHONE, "pin": PIN})[0])
s, raw, _ = call("/my/tests?tab=completed&page=1&q=&status=all&exam=")
tests = (json.loads(raw).get("data") or {}).get("items") or []
seen = set()
for t in tests:
    kind = (t.get("test_kind") or t.get("kind") or "?", t.get("mode") or "")
    ms = []
    for _ in range(3):
        s, raw, dt = call(f"/attempts/{t['id']}/analysis?mode=personal&compare=topper&score_version=original")
        ms.append(round(dt))
    a = (json.loads(raw).get("data") if raw else None) or {}
    qs = a.get("questions") or []
    d = a.get("difficulty") or {}
    topics = sum(1 for q in qs if q.get("topic"))
    levels = {}
    for q in qs:
        levels[q.get("difficulty")] = levels.get(q.get("difficulty"), 0) + 1
    print(f"{t['id'][:8]} {str(t.get('title'))[:38]!r} kind={kind} -> {s} {len(raw)} B ms={ms} v={a.get('analysis_version')}/{a.get('rules_version')} "
          f"q={len(qs)} topic={topics} has_chapters={(a.get('performance') or {}).get('has_chapters')} levels={levels} sources={d.get('sources')} class={(a.get('class') or {}).get('state')}")
    if qs and kind not in seen:
        seen.add(kind)
        print("   question keys:", sorted(qs[0].keys()))
