# Trigger notify() on a server via create(invite)+join (no WebSocket), then report rf_events capped status.
import os
import sys
import time
import uuid

import requests

base = sys.argv[1].rstrip("/")
a, b = "TEST-cap-" + uuid.uuid4().hex[:10], "TEST-cap-" + uuid.uuid4().hex[:10]
r = requests.post(f"{base}/api/rf/duels", json={"subject": "Physics", "mode": "invite", "name": "CapA", "request_id": uuid.uuid4().hex}, headers={"X-RF-User": a}, timeout=20)
print("create", r.status_code)
d = r.json()
j = requests.post(f"{base}/api/rf/duels/join", json={"code": d["code"], "name": "CapB"}, headers={"X-RF-User": b}, timeout=20)
print("join", j.status_code, j.json().get("status"))
for u in (a, b):
    requests.post(f"{base}/api/rf/duels/{d['id']}/forfeit", headers={"X-RF-User": u}, timeout=20)
time.sleep(2)
print("duel", d["id"])
