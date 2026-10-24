# Real 2-server repro: socket on server X, X publishes its own event, then server Y publishes within the same second.
# If X's ObjectId random part > Y's, X's tailable cursor filter {_id > last_id} drops Y's event; push falls back to the 2 s ticker.
#   RF_NODE_A=http://127.0.0.1:8001 RF_NODE_B=http://127.0.0.1:8002 python repro_rf_same_second_drop.py
import json
import os
import time
import uuid

import requests
from test_rf_duels_multiserver import Reader, H, uid, opp, answer

A = os.environ["RF_NODE_A"].rstrip("/")
B = os.environ["RF_NODE_B"].rstrip("/")


def run(X, Y, rounds=6):
    host, guest = uid(), uid()
    d = requests.post(f"{X}/api/rf/duels", json={"subject": "Physics", "mode": "invite", "name": "TEST_Host", "request_id": uuid.uuid4().hex}, headers=H(host), timeout=10).json()
    rx = Reader(X, d["id"], host)
    rx.wait(lambda m: m["status"] == "waiting")
    rj = requests.post(f"{Y}/api/rf/duels/join", json={"code": d["code"], "name": "TEST_Guest"}, headers=H(guest), timeout=10).json()
    rx.wait(lambda m: m["status"] == "ready")
    time.sleep(max(0, rj["start_at"] - rj["server_now"]) + 0.3)
    lat = []
    for i in range(rounds):
        rx.drain()
        assert answer(X, d["id"], host, i).status_code == 200  # X publishes its own event (X tail last_id moves)
        r = answer(Y, d["id"], guest, i)  # Y publishes in the same second
        t1 = time.perf_counter()
        assert r.status_code == 200, r.text
        ts, m = rx.wait(lambda m, i=i: opp(m)["answered"] == i + 1, timeout=5)
        lat.append(round((ts - t1) * 1000, 1) if ts else None)
        time.sleep(0.3)
    for u in (host, guest):
        requests.post(f"{X}/api/rf/duels/{d['id']}/forfeit", headers=H(u), timeout=10)
    rx.close()
    return lat


for name, X, Y in (("socket_on_A(8001)_event_from_B", A, B), ("socket_on_B(8002)_event_from_A", B, A)):
    print(name, json.dumps(run(X, Y)))
