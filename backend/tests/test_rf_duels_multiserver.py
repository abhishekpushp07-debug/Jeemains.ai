# Rapid Fire Duels multi-server shared live channel (rf_events capped collection tailed by each process).
# Needs two backend processes: RF_NODE_A (supervisor :8001) and RF_NODE_B (extra uvicorn :8002), e.g.
#   RF_NODE_A=http://127.0.0.1:8001 RF_NODE_B=http://127.0.0.1:8002 pytest test_rf_duels_multiserver.py
import json
import os
import queue
import threading
import time
import uuid

import pytest
import requests
from websockets.sync.client import connect

A = os.environ.get("RF_NODE_A", "").rstrip("/")
B = os.environ.get("RF_NODE_B", "").rstrip("/")
pytestmark = pytest.mark.skipif(not (A and B), reason="RF_NODE_A / RF_NODE_B not set")
LIMIT_MS = 200
LAT = {}


def H(u):
    return {"X-RF-User": u}


def uid():
    return "TEST-ms-" + uuid.uuid4().hex[:16]


def ws_url(base, did, u):
    return base.replace("http", "ws", 1) + f"/api/rf/duels/{did}/ws?u={u}"


class Reader:
    """Background reader that timestamps every pushed state the moment it arrives."""

    def __init__(self, base, did, u):
        self.ws = connect(ws_url(base, did, u), open_timeout=10)
        self.q = queue.Queue()
        self.t = threading.Thread(target=self._run, daemon=True)
        self.t.start()

    def _run(self):
        try:
            while True:
                m = self.ws.recv()
                self.q.put((time.perf_counter(), json.loads(m)))
        except Exception:  # noqa: BLE001
            pass

    def drain(self):
        while not self.q.empty():
            self.q.get_nowait()

    def wait(self, pred, timeout=8):
        end = time.time() + timeout
        while time.time() < end:
            try:
                ts, m = self.q.get(timeout=max(0.05, end - time.time()))
            except queue.Empty:
                break
            if pred(m):
                return ts, m
        return None, None

    def close(self):
        try:
            self.ws.close()
        except Exception:  # noqa: BLE001
            pass


def opp(m):
    return next(p for p in m["players"] if not p["you"])


def setup_duel():
    host, guest = uid(), uid()
    r = requests.post(f"{A}/api/rf/duels", json={"subject": "Physics", "mode": "invite", "name": "TEST_Host", "request_id": uuid.uuid4().hex}, headers=H(host), timeout=10)
    assert r.status_code == 200, r.text
    d = r.json()
    ra = Reader(A, d["id"], host)
    ts, m = ra.wait(lambda m: m["status"] == "waiting")
    assert m, "host socket on A got no initial state"
    t0 = time.perf_counter()
    rj = requests.post(f"{B}/api/rf/duels/join", json={"code": d["code"], "name": "TEST_Guest"}, headers=H(guest), timeout=10)
    assert rj.status_code == 200, rj.text
    t1 = time.perf_counter()
    ts, m = ra.wait(lambda m: m["status"] == "ready")
    assert m, "host socket on A never saw guest join from B"
    LAT.setdefault("join_B_to_A_ms", []).append(round((ts - t1) * 1000, 1))
    rb = Reader(B, d["id"], guest)
    ts, mb = rb.wait(lambda m: m["status"] == "ready")
    assert mb and len(mb["players"]) == 2
    wait = rj.json()["start_at"] - rj.json()["server_now"]
    time.sleep(max(0, wait) + 0.3)
    ra.drain(); rb.drain()
    return d["id"], host, guest, ra, rb


@pytest.fixture
def duel():
    did, host, guest, ra, rb = setup_duel()
    yield did, host, guest, ra, rb
    ra.close(); rb.close()


def answer(base, did, u, i):
    return requests.post(f"{base}/api/rf/duels/{did}/answer", json={"index": i, "choice": 0, "outcome": "answer", "ms": 1000}, headers=H(u), timeout=10)


# A -> B: answer on :8001 reaches the guest socket on :8002 fast; B -> A reverse
def test_answer_cross_server_both_directions(duel):
    did, host, guest, ra, rb = duel
    for i in range(3):
        t0 = time.perf_counter()
        r = answer(A, did, host, i)
        t1 = time.perf_counter()
        assert r.status_code == 200, r.text
        ts, m = rb.wait(lambda m, i=i: opp(m)["answered"] == i + 1)
        assert m, f"B socket never got host answer {i}"
        LAT.setdefault("answer_A_to_B_from_response_ms", []).append(round((ts - t1) * 1000, 1))
        LAT.setdefault("answer_A_to_B_from_request_ms", []).append(round((ts - t0) * 1000, 1))
        t0 = time.perf_counter()
        r = answer(B, did, guest, i)
        t1 = time.perf_counter()
        assert r.status_code == 200, r.text
        ts, m = ra.wait(lambda m, i=i: opp(m)["answered"] == i + 1)
        assert m, f"A socket never got guest answer {i}"
        LAT.setdefault("answer_B_to_A_from_response_ms", []).append(round((ts - t1) * 1000, 1))
        LAT.setdefault("answer_B_to_A_from_request_ms", []).append(round((ts - t0) * 1000, 1))
    print("LATENCY", json.dumps(LAT))
    assert max(LAT["answer_A_to_B_from_response_ms"]) < LIMIT_MS
    assert max(LAT["answer_B_to_A_from_response_ms"]) < LIMIT_MS
    assert max(LAT["join_B_to_A_ms"]) < LIMIT_MS


# Forfeit on :8002 -> host on :8001 sees finished + win; guest socket also gets finished
def test_forfeit_cross_server(duel):
    did, host, guest, ra, rb = duel
    assert answer(A, did, host, 0).status_code == 200
    t1 = None
    r = requests.post(f"{B}/api/rf/duels/{did}/forfeit", headers=H(guest), timeout=10)
    t1 = time.perf_counter()
    assert r.status_code == 200 and r.json() == {"ok": True}
    # PvP: a forfeit marks the leaver done; the duel stays live for the other player
    ts, m = ra.wait(lambda m: opp(m)["done"] is True)
    assert m, "host socket on A never saw the guest forfeit from B"
    LAT.setdefault("forfeit_B_to_A_ms", []).append(round((ts - t1) * 1000, 1))
    assert m["status"] == "ready"
    for i in range(1, 30):
        assert answer(A, did, host, i).status_code == 200
    ts, m = ra.wait(lambda m: m["status"] == "finished")
    assert m, "host socket on A never saw finished"
    assert m["winner"] == host
    assert m["reward"] is not None
    ts2, mb = rb.wait(lambda m: m["status"] == "finished")
    assert mb and mb["winner"] == host
    print("LATENCY", json.dumps(LAT))
    assert LAT["forfeit_B_to_A_ms"][-1] < LIMIT_MS
    # GET from the other server agrees
    g = requests.get(f"{B}/api/rf/duels/{did}", headers=H(host), timeout=10).json()
    assert g["status"] == "finished" and g["winner"] == host


# Both players finish all 30 cards on different servers -> finished on both sockets, same winner
def test_full_finish_cross_server(duel):
    did, host, guest, ra, rb = duel
    for i in range(30):
        assert answer(A, did, host, i).status_code == 200
        assert answer(B, did, guest, i).status_code == 200
    ts, ma = ra.wait(lambda m: m["status"] == "finished")
    ts2, mb = rb.wait(lambda m: m["status"] == "finished")
    assert ma and mb, "finished state missing on a socket"
    assert ma["winner"] == mb["winner"] and ma["winner"] in (host, guest, "tie")
    assert all(p["answered"] == 30 for p in ma["players"]) and all(p["answered"] == 30 for p in mb["players"])
    assert ma["reward"] is not None and mb["reward"] is not None
    assert ma["cards"][0].get("answer") is not None  # key revealed after finish
    # duplicate answer after finish stays idempotent
    r = answer(A, did, host, 29)
    assert r.status_code == 200


# rf_events channel exists and is capped (shared bus)
def test_bus_collection_is_capped():
    from pymongo import MongoClient
    from dotenv import dotenv_values
    env = dotenv_values("/app/backend/.env")
    db = MongoClient(env["MONGO_URL"])[env["DB_NAME"]]
    opts = db.rf_events.options()
    assert opts.get("capped") is True
    assert db.rf_events.estimated_document_count() > 0
