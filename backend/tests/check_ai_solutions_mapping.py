# AI solutions mapping: compare results questions (number/id/key/stem) with ai-solutions items by question_id
import os, uuid, requests, json

BASE = os.environ["EXPO_PUBLIC_BACKEND_URL"].rstrip("/")
ATTEMPT = "8501cf9c-6ade-4d3c-b06c-75c6b488a1c0"
s = requests.Session()
s.headers["X-JL-Sid"] = uuid.uuid4().hex
s.post(f"{BASE}/api/jl/auth/phone", json={"phone": "9000000001"})
r = s.get(f"{BASE}/api/jl/attempts/{ATTEMPT}/results?score_version=")
print("results", r.status_code)
d = r.json(); d = d.get("data", d)
qs = d.get("questions", [])
print("questions", len(qs), "keys:", list(qs[0].keys()) if qs else None)
a = s.get(f"{BASE}/api/jl/attempts/{ATTEMPT}/ai-solutions").json(); a = a.get("data", a)
by = {x["question_id"]: x for x in a["items"]}
missing = [q["number"] for q in qs if q["id"] not in by]
print("questions without ai item:", missing)
keymis = []
for q in qs:
    it = by.get(q["id"])
    if not it or not it.get("solution"): continue
    key = q.get("answer_key") or q.get("correct") or q.get("key")
    fa = it["solution"].get("final_answer")
    if key is not None and str(fa).strip().upper() != str(key).strip().upper():
        keymis.append((q["number"], key, fa))
print("final_answer != answer key:", keymis[:20], len(keymis))
for n in [91, 92, 93, 94, 95, 96, 97, 98, 99]:
    q = next(x for x in qs if x["number"] == n)
    it = by.get(q["id"], {})
    sol = it.get("solution") or {}
    print(n, q["id"][:8], "key", q.get("answer_key") or q.get("correct"), "| AI final", sol.get("final_answer"), "| concept:", (sol.get("concept") or "")[:90])
for n in [91, 98, 1, 31, 71]:
    q = next(x for x in qs if x["number"] == n)
    print("\n#", n, "text:", (q.get("text") or "")[:160].replace("\n", " "), "| acc:", (q.get("accessible_text") or "")[:160].replace("\n", " "), "| q_refs:", json.dumps(q.get("q_refs"))[:200])
