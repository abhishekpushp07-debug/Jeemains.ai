# Measures the app server's own Rank doors on THIS preview (one uvicorn process), 8 s each, 16 at a time.
# Pure reads: POST /api/rank/predict and POST /api/rank/cutoff compute and answer; nothing is stored.
import asyncio, json, time
import aiohttp

B = "http://localhost:8001/api/rank"
BODIES = {
    "predict": {"marks": 180},
    "cutoff (jee, college, with marks)": {"exam": "jee", "by": "college", "key": "0", "marks": 180},
    "cutoff (jee, branch, no score)": {"exam": "jee", "by": "branch", "key": None},
}

async def run(session, path, body, seconds=8, workers=16):
    ok = bad = 0; times = []; end = time.monotonic() + seconds
    async def one():
        nonlocal ok, bad
        while time.monotonic() < end:
            t = time.monotonic()
            async with session.post(f"{B}/{path}", json=body) as r:
                await r.read()
                (times.append(time.monotonic() - t), None) if r.status == 200 else None
                if r.status == 200: ok += 1
                else: bad += 1
    await asyncio.gather(*[one() for _ in range(workers)])
    times.sort()
    p = lambda q: round(times[int(len(times) * q) - 1] * 1000, 1) if times else None
    return ok / seconds, bad, p(0.5), p(0.95)

async def main():
    async with aiohttp.ClientSession() as s:
        async with s.get(f"{B}/cutoff/options") as r:
            opts = (await r.json())
        opts = opts.get("data", opts)
        BODIES["cutoff (jee, branch, no score)"]["key"] = opts["jee"]["branches"][0]["key"]
        BODIES["cutoff (jee, college, with marks)"]["key"] = opts["jee"]["colleges"][0]["key"]
        for name, body in BODIES.items():
            path = "predict" if name == "predict" else "cutoff"
            async with s.post(f"{B}/{path}", json=body) as r:
                if r.status != 200:
                    print(name, "->", r.status, (await r.text())[:200]); continue
            rps, bad, p50, p95 = await run(s, path, body)
            print(f"{name}: {rps:.0f} answers/s, {bad} not 200, p50 {p50} ms, p95 {p95} ms")

asyncio.run(main())
