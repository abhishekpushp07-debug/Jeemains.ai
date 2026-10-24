# AI solutions (Result > Solutions): scan live /api/jl/attempts/{id}/ai-solutions for LaTeX that plainMath can't flatten
import os, re, requests

BASE = os.environ.get("EXPO_PUBLIC_BACKEND_URL", "").rstrip("/")
ATTEMPT = "8501cf9c-6ade-4d3c-b06c-75c6b488a1c0"

import uuid
s = requests.Session()
s.headers["X-JL-Sid"] = uuid.uuid4().hex
r = s.post(f"{BASE}/api/jl/auth/phone", json={"phone": "9000000001"})
print("auth", r.status_code)
r = s.get(f"{BASE}/api/jl/attempts/{ATTEMPT}/ai-solutions")
print("ai-solutions", r.status_code)
d = r.json(); d = d.get("data", d)
items = d.get("items", [])
print("total", d.get("total"), "ready", d.get("ready"), "items", len(items))
print("disclosure:", d.get("disclosure"))

def texts(sol):
    out = [sol.get("concept"), sol.get("shortcut"), sol.get("time_tip"), sol.get("insight")]
    out += sol.get("given") or []
    out += sol.get("common_mistakes") or []
    for st in sol.get("steps") or []:
        out += [st.get("title"), st.get("explanation")]
    return [x for x in out if x]

pat_frac = re.compile(r"\\[dt]?frac(?!\{)")
pat_cmds = re.compile(r"\\([A-Za-z]+)")
bare_frac, cmds, missing = 0, {}, 0
for it in items:
    sol = it.get("solution") or {}
    if it.get("state") != "ready":
        missing += 1
        continue
    for t in texts(sol):
        if pat_frac.search(t):
            bare_frac += 1
        for c in pat_cmds.findall(t):
            cmds[c] = cmds.get(c, 0) + 1
print("non-ready", missing, "strings with brace-less \\frac / \\dfrac / \\tfrac:", bare_frac)
print("top latex cmds:", sorted(cmds.items(), key=lambda x: -x[1])[:60])
import json
json.dump(items, open("/tmp/ai_items.json", "w"))
