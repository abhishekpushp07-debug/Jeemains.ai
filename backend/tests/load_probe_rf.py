# Light load probe (NOT a 5-lakh test): concurrent reads on cached Rapid Fire endpoints via the public URL
import asyncio
import os
import statistics
import time
import httpx
from dotenv import load_dotenv

load_dotenv("/app/frontend/.env")
BASE = os.environ.get("RF_PROBE_BASE") or os.environ.get("EXPO_PUBLIC_BACKEND_URL").rstrip("/")
UID = "db0c62b8-eeaf-41be-b8b1-05f5f34ac1d8"


async def run(path, n=400, conc=50):
    sem = asyncio.Semaphore(conc)
    lat, codes = [], {}
    async with httpx.AsyncClient(timeout=30, headers={"X-RF-User": UID}) as c:
        async def one():
            async with sem:
                t = time.perf_counter()
                try:
                    r = await c.get(BASE + path)
                    codes[r.status_code] = codes.get(r.status_code, 0) + 1
                except Exception as e:
                    codes[type(e).__name__] = codes.get(type(e).__name__, 0) + 1
                lat.append((time.perf_counter() - t) * 1000)
        t0 = time.perf_counter()
        await asyncio.gather(*[one() for _ in range(n)])
        el = time.perf_counter() - t0
    lat.sort()
    print(f"{path}: n={n} conc={conc} rps={n / el:.0f} p50={statistics.median(lat):.0f}ms p95={lat[int(len(lat) * .95)]:.0f}ms max={lat[-1]:.0f}ms codes={codes}")


async def main():
    for p in ["/api/rf/leaderboard", "/api/rf/catalog", "/api/rf/profile"]:
        await run(p)


asyncio.run(main())
