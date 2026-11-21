"""Iteration 126 read-only probe: which questions of the QA attempt use cut-picture pieces / typed options / tiles."""
import os
import sys
import uuid
import requests

BASE = os.environ["EXPO_PUBLIC_BACKEND_URL"].rstrip("/")
sid = "TESTSID" + uuid.uuid4().hex[:20]
s = requests.Session()
h = {"X-JL-Sid": sid}
r = s.post(f"{BASE}/api/jl/auth/phone", json={"phone": "7004186276", "pin": "5524"}, headers=h, timeout=30)
print("login", r.status_code)
a = s.get(f"{BASE}/api/jl/attempts/{sys.argv[1]}", headers=h, timeout=60).json()
a = a.get("data", a)
print("status", a.get("status"), "deadline", a.get("deadline"), "server_now", a.get("server_now"), "answers", len(a.get("answers") or {}))
qs = a.get("questions") or []
print("questions", len(qs), "keys", sorted(qs[0].keys()) if qs else None)
kinds = {}
for i, q in enumerate(qs):
    k = [x for x in ("pieces", "option_pieces", "typed", "options_typed", "source") if q.get(x)]
    opts = q.get("options") or {}
    see = all(str(v).startswith("See original") for v in opts.values()) if opts else None
    kinds.setdefault((q.get("type"), tuple(k), see), []).append(i + 1)
for k, v in kinds.items():
    print(k, v[:12], len(v))
