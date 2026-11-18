# Iteration102 read-only helper: lists the QA account's server-side dream mocks (session from /tmp/iter102_sess.json, 0600).
import json, os
import requests

BASE = os.environ["EXPO_PUBLIC_BACKEND_URL"].rstrip("/")
sid = json.load(open("/tmp/iter102_sess.json"))["jl_sid"]
for _ in range(3):
    try:
        v = json.loads(sid)
        if isinstance(v, str):
            sid = v
            continue
    except Exception:
        pass
    break
tok = requests.post(BASE + "/api/rf/access", headers={"X-JL-Sid": sid, "Content-Type": "application/json"}, data="{}", timeout=20).json()
t = tok.get("token") or tok.get("access_token") or tok.get("bearer")
d = requests.get(BASE + "/api/rf/dream", headers={"Authorization": f"Bearer {t}"}, timeout=20).json()
mocks = d.get("mocks", [])
print("dreams:", [(x.get("exam"), x.get("need")) for x in d.get("dreams", [])])
print("mocks total:", len(mocks))
for m in mocks:
    print(m.get("exam"), m.get("score"), m.get("rawMax"), m.get("title"), m.get("id", "")[:8], m.get("at"))
