# AI solutions: fetch live items of the reference attempt (read-only) to /tmp/ai_items.json for the node render checks
import os, json, uuid, requests

BASE = os.environ.get("EXPO_PUBLIC_BACKEND_URL", "").rstrip("/")
ATTEMPT = "8501cf9c-6ade-4d3c-b06c-75c6b488a1c0"
s = requests.Session()
s.headers["X-JL-Sid"] = uuid.uuid4().hex
r = s.post(f"{BASE}/api/jl/auth/phone", json={"phone": "9000000001"}, timeout=30)
print("auth", r.status_code)
r = s.get(f"{BASE}/api/jl/attempts/{ATTEMPT}/ai-solutions", timeout=60)
print("ai-solutions", r.status_code)
d = r.json(); d = d.get("data", d)
items = d.get("items", [])
print("items", len(items), "ready", sum(1 for i in items if i.get("state") == "ready"))
json.dump(items, open("/tmp/ai_items.json", "w"))
