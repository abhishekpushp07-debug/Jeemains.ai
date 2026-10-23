# Rapid Fire Duels live WebSocket (/api/rf/duels/{id}/ws?u=uid) + GZip regression tests
import json
import os
import time
import uuid

import pytest
import requests
from dotenv import load_dotenv
from websockets.sync.client import connect
from websockets.exceptions import ConnectionClosed

load_dotenv("/app/frontend/.env")
BASE_URL = os.environ.get("EXPO_PUBLIC_BACKEND_URL").rstrip("/")
API = f"{BASE_URL}/api/rf"
WS = API.replace("https://", "wss://").replace("http://", "ws://")


def H(u):
    return {"X-RF-User": u}


def new_uid():
    return "TEST-ws-" + uuid.uuid4().hex[:16]


def create(s, uid, mode="invite", subject="Physics"):
    r = s.post(f"{API}/duels", json={"subject": subject, "mode": mode, "name": "TEST_WS", "request_id": uuid.uuid4().hex}, headers=H(uid))
    assert r.status_code == 200, r.text
    return r.json()


def recv_until(ws, pred, timeout=12):
    """Read pushed states until pred(state) is true; returns (state, all_msgs)."""
    end = time.time() + timeout
    msgs = []
    while time.time() < end:
        try:
            m = json.loads(ws.recv(timeout=max(0.1, end - time.time())))
        except TimeoutError:
            break
        msgs.append(m)
        if pred(m):
            return m, msgs
    return None, msgs


@pytest.fixture(scope="module")
def s():
    return requests.Session()


# ---------- membership / close codes ----------
class TestWsAuth:
    def _close_code(self, url):
        with connect(url, open_timeout=10) as ws:
            try:
                ws.recv(timeout=5)
            except ConnectionClosed as e:
                return e.rcvd.code if e.rcvd else None
        return ws.close_code

    def test_non_member_4404(self, s):
        d = create(s, new_uid())
        assert self._close_code(f"{WS}/duels/{d['id']}/ws?u={new_uid()}") == 4404

    def test_invalid_uid_4404(self, s):
        d = create(s, new_uid())
        assert self._close_code(f"{WS}/duels/{d['id']}/ws?u=bad!") == 4404
        assert self._close_code(f"{WS}/duels/{d['id']}/ws") == 4404

    def test_unknown_duel_4404(self):
        assert self._close_code(f"{WS}/duels/{uuid.uuid4()}/ws?u={new_uid()}") == 4404


# ---------- pushes ----------
class TestWsPush:
    def test_initial_state_and_bot_push(self, s):
        uid = new_uid()
        d = create(s, uid)
        with connect(f"{WS}/duels/{d['id']}/ws?u={uid}", open_timeout=10) as ws:
            first = json.loads(ws.recv(timeout=8))
            assert first["id"] == d["id"] and first["status"] == "waiting" and first["you"] == uid
            assert "_id" not in first
            r = s.post(f"{API}/duels/{d['id']}/bot", json={}, headers=H(uid))
            assert r.status_code == 200, r.text
            st, _ = recv_until(ws, lambda m: m["status"] == "ready" and len(m["players"]) == 2, 8)
            assert st is not None, "no push after /bot"
            bot = [p for p in st["players"] if p["bot"]][0]
            assert bot["name"] and "answers" not in bot and "uid" not in bot
            assert len(st["cards"]) == 30 and "answer" not in st["cards"][0]

    def test_bot_progress_and_answer_push(self, s):
        uid = new_uid()
        d = create(s, uid)
        s.post(f"{API}/duels/{d['id']}/bot", json={}, headers=H(uid))
        with connect(f"{WS}/duels/{d['id']}/ws?u={uid}", open_timeout=10) as ws:
            st = json.loads(ws.recv(timeout=8))
            wait = st["start_at"] - st["server_now"]
            if wait > 0:
                time.sleep(wait + 0.3)
            # answer 3 cards over HTTP, confirm each is pushed back on the socket
            for i in range(3):
                r = s.post(f"{API}/duels/{d['id']}/answer", json={"index": i, "choice": 0, "outcome": "answer", "ms": 1000}, headers=H(uid))
                assert r.status_code == 200, r.text
                got, _ = recv_until(ws, lambda m, i=i: [p for p in m["players"] if p["you"]][0]["answered"] >= i + 1, 6)
                assert got is not None, f"no push after answer {i}"
            # bot paces 4-6.5 s/card: answered count must grow on the socket without any HTTP call
            b0 = [p for p in got["players"] if p["bot"]][0]["answered"]
            grown, msgs = recv_until(ws, lambda m: [p for p in m["players"] if p["bot"]][0]["answered"] > b0, 12)
            assert grown is not None, f"bot progress not pushed ({len(msgs)} msgs)"
            # bot never ahead of human
            me = [p for p in grown["players"] if p["you"]][0]
            bot = [p for p in grown["players"] if p["bot"]][0]
            assert bot["score"] <= max(0, me["score"] - 1) or bot["score"] == 0

    def test_forfeit_push_finished(self, s):
        uid = new_uid()
        d = create(s, uid)
        s.post(f"{API}/duels/{d['id']}/bot", json={}, headers=H(uid))
        with connect(f"{WS}/duels/{d['id']}/ws?u={uid}", open_timeout=10) as ws:
            st = json.loads(ws.recv(timeout=8))
            time.sleep(max(0, st["start_at"] - st["server_now"]) + 0.3)
            assert s.post(f"{API}/duels/{d['id']}/forfeit", json={}, headers=H(uid)).status_code == 200
            fin, _ = recv_until(ws, lambda m: m["status"] == "finished", 8)
            assert fin is not None, "no finished push after forfeit"
            assert fin["winner"] != uid and fin["reward"] is not None
            assert "answer" in fin["cards"][0]

    def test_join_push_to_host(self, s):
        a, b = new_uid(), new_uid()
        d = create(s, a, mode="invite", subject="Chemistry")
        with connect(f"{WS}/duels/{d['id']}/ws?u={a}", open_timeout=10) as ws:
            assert json.loads(ws.recv(timeout=8))["status"] == "waiting"
            r = s.post(f"{API}/duels/join", json={"code": d["code"], "name": "TEST_B"}, headers=H(b))
            assert r.status_code == 200, r.text
            st, _ = recv_until(ws, lambda m: m["status"] == "ready" and len(m["players"]) == 2, 6)
            assert st is not None, "host not notified of join"
            opp = [p for p in st["players"] if not p["you"]][0]
            assert opp["name"] == "TEST_B" and not opp["bot"]
        # B can connect too; A's uid hidden from B
        with connect(f"{WS}/duels/{d['id']}/ws?u={b}", open_timeout=10) as ws2:
            st2 = json.loads(ws2.recv(timeout=8))
            assert st2["you"] == b and all("uid" not in p for p in st2["players"])
        s.post(f"{API}/duels/{d['id']}/forfeit", json={}, headers=H(a))


# ---------- GZip ----------
class TestGzip:
    def test_rf_cards_gzip(self, s):
        r = s.get(f"{API}/cards", headers={"Accept-Encoding": "gzip"})
        assert r.status_code == 200 and r.json()["total"] >= 4100
        assert r.headers.get("content-encoding") == "gzip"

    def test_jl_proxy_with_gzip(self, s):
        sid = "TESTSID" + uuid.uuid4().hex[:20]
        r = s.post(f"{BASE_URL}/api/jl/auth/phone", json={"phone": "9000000001"}, headers={"X-JL-Sid": sid, "Accept-Encoding": "gzip"})
        assert r.status_code == 200, r.text[:300]
        me = s.get(f"{BASE_URL}/api/jl/auth/me", headers={"X-JL-Sid": sid, "Accept-Encoding": "gzip"})
        assert me.status_code == 200 and me.json()["data"], me.text[:300]
        big = s.get(f"{BASE_URL}/api/jl/series/all-india-jee", headers={"X-JL-Sid": sid, "Accept-Encoding": "gzip"})
        assert big.status_code in (200, 404) and big.headers.get("content-type", "").startswith("application/json")
        big.json()
