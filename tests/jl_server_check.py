"""Unit checks of backend/jl_track.py with the collector replaced by a recorder (nothing leaves this machine)."""
import asyncio
import os
import sys
import time

sys.path.insert(0, "/app/backend")
import jl_track  # noqa: E402

sent, ok, fails = [], 0, 0
REAL = "0f8fad5b-d9cb-469f-a165-70867728950e"


def check(name, cond, detail=""):
    global ok, fails
    ok, fails = (ok + 1, fails) if cond else (ok, fails + 1)
    print(("PASS " if cond else "FAIL ") + name + ("" if cond else f" :: {detail}"))


class Recorder:
    def __init__(self, delay=0.0, boom=False):
        self.delay, self.boom = delay, boom

    async def post(self, url, json=None, headers=None):
        await asyncio.sleep(self.delay)
        if self.boom:
            raise RuntimeError("collector down")
        sent.append((url, json, headers))

        class R:
            status_code = 200
        return R()


async def main():
    os.environ.pop("JLIVE_TRACKING_SECRET_KEY", None)
    jl_track._client = Recorder()
    jl_track.track_server("rapid_fire_match_completed", REAL, {"mode": "solo"})
    await asyncio.sleep(0.05)
    check("off without the secret", not sent, sent)

    os.environ["JLIVE_TRACKING_SECRET_KEY"] = "test-secret"
    jl_track.track_server("rapid_fire_match_completed", "TEST-bank-a", {"mode": "solo"})
    jl_track.track_server("rapid_fire_match_completed", REAL.upper(), {"mode": "solo"})
    await asyncio.sleep(0.05)
    check("test / non-website ids never sent", not sent, sent)

    jl_track.track_server("rapid_fire_match_completed", REAL, {"mode": "solo", "exam": "jee", "result": "completed",
                                                              "nested": {"a": 1}, "long": "x" * 500}, key="solo:abc")
    await asyncio.sleep(0.05)
    url, body, headers = sent[-1]
    e = body["events"][0]
    check("posted to the server collector", url.endswith("/api/collect/v1/server"), url)
    check("bearer secret header", headers == {"Authorization": "Bearer test-secret"}, headers)
    check("event shape", set(e) == {"event_id", "event_name", "occurred_at", "uid", "props"} and e["uid"] == REAL
          and e["occurred_at"].endswith("Z"), e)
    check("props scalars only, strings cut at 200", "nested" not in e["props"] and len(e["props"]["long"]) == 200, e["props"])
    jl_track.track_server("rapid_fire_match_completed", REAL, {"mode": "solo"}, key="solo:abc")
    await asyncio.sleep(0.05)
    check("same key -> same event_id (retry counted once)", sent[-1][1]["events"][0]["event_id"] == e["event_id"])
    jl_track.track_server("x", REAL, {f"k{i}": i for i in range(40)})
    await asyncio.sleep(0.05)
    check("at most 30 props", len(sent[-1][1]["events"][0]["props"]) == 30)

    n = len(sent)
    jl_track.track_wallet(REAL, {"coins": 40, "xp": 0, "diamonds.red": -2}, "shop_buy", key="k", item="freeze")
    await asyncio.sleep(0.05)
    w = [s[1]["events"][0]["props"] for s in sent[n:]]
    check("wallet: one event per moved currency", w == [{"currency": "coins", "delta": 40, "reason": "shop_buy", "item": "freeze"},
                                                       {"currency": "diamonds", "colour": "red", "delta": -2, "reason": "shop_buy", "item": "freeze"}], w)

    jl_track._client = Recorder(delay=5)
    t = time.monotonic()
    jl_track.track_server("slow", REAL, {})
    check("returns at once even when the collector is slow", time.monotonic() - t < 0.01)
    jl_track._client = Recorder(boom=True)
    try:
        jl_track.track_server("boom", REAL, {})
        await asyncio.sleep(0.05)
        check("a failing collector never raises", True)
    except Exception as ex:  # noqa: BLE001
        check("a failing collector never raises", False, ex)
    jl_track._client = None
    import httpx
    c = httpx.AsyncClient(timeout=2)
    check("real client timeout is 2 s", c.timeout.read == 2)
    await c.aclose()
    print(f"\n{ok}/{ok + fails} passed")


asyncio.run(main())
