# Iteration 154 C: result pictures in parts + one "busy" part (503 + Retry-After) answered by the browser only.
# Read-only: the keeper's list is cut (no background run), every write under /api/jl outside /auth is stopped.
# Only the Analysis view of /result/<id> is opened (never the Solutions tab).
import asyncio
import json
import re
import sys
import time

from playwright.async_api import async_playwright

sys.path.insert(0, "/app/tests")
from shine_helpers import sign_in  # noqa: E402
from iter154_name_rank_door import BASE, check, RES  # noqa: E402

CHAPTER, PYQ = "91e7b6bf-4067-41f8-9e0f-730086159307", "c0061f81-7ae9-432b-8ca5-312c8d39d4b5"
BUSY = json.dumps({"error": {"code": "vault_unavailable", "message": "Private content is temporarily unavailable. Please retry shortly."}})


async def run(b, attempt, retry_after=None, expose=True, busy_pack=True, wait=30):
    st = {"parts": [], "cdn": [], "pack": [], "one": [], "links": 0, "blocked": [], "busy_cdn": 0, "busy_pack": 0}
    t0 = time.time()
    ctx = await b.new_context(viewport={"width": 390, "height": 844})
    page = await ctx.new_page()

    async def guard(route):
        r = route.request
        if r.method in ("GET", "HEAD", "OPTIONS") or "/api/jl/auth/" in r.url:
            await route.fallback(); return
        st["blocked"].append(r.method + " " + r.url)
        await route.fulfill(status=418, body="{}")
    await page.route(re.compile(r".*/api/jl/.*"), guard)
    await page.route(re.compile(r".*/api/jl/my/tests\?.*tab=completed.*"), lambda route: route.abort())

    async def links(route):
        resp = await route.fetch()
        try:
            j = await resp.json()
            d = j.get("data", j) if isinstance(j, dict) else {}
            if attempt in route.request.url:
                st.setdefault("links_urls", []).append(route.request.url.split("/assets/")[1])
                if not st["parts"]:
                    st["parts"] = list(d.get("parts") or [])
                st["links"] += 1
                st["limit"] = d.get("limit"); st["total"] = d.get("total")
        except Exception:
            pass
        await route.fulfill(response=resp)
    await page.route(re.compile(r".*/api/jl/attempts/[^/]+/assets/links.*"), links)

    def is_part(url):
        return bool(st["parts"]) and any(url == p or url.endswith(p) for p in st["parts"][:1])

    async def part0(route):
        st["cdn"].append(round(time.time() - t0, 1))
        if retry_after is not None and st["busy_cdn"] == 0:
            st["busy_cdn"] += 1
            h = {"Retry-After": str(retry_after), "Access-Control-Allow-Origin": "*"}
            if expose:
                h["Access-Control-Expose-Headers"] = "Retry-After"
            await route.fulfill(status=503, headers=h, content_type="application/json", body=BUSY)
            return
        await route.fallback()
    await page.route(is_part, part0)

    async def pack0(route):
        u = route.request.url
        if attempt in u and re.search(r"[?&]offset=0(&|$)", u):
            st["pack"].append(round(time.time() - t0, 1))
            if retry_after is not None and busy_pack and st["busy_pack"] == 0:
                st["busy_pack"] += 1
                await route.fulfill(status=503, headers={"Retry-After": str(retry_after)}, content_type="application/json", body=BUSY)
                return
        await route.fallback()
    await page.route(re.compile(r".*/api/jl/attempts/[^/]+/assets/pack.*"), pack0)
    page.on("request", lambda r: st["one"].append(r.url) if attempt in r.url and re.search(r"/asset/(question|solution|piece)/\d+", r.url) else None)
    statuses = []
    page.on("response", lambda r: statuses.append((round(time.time() - t0, 1), r.status)) if is_part(r.url) else None)

    await page.goto(BASE + "/", wait_until="domcontentloaded")
    await sign_in(page)
    await page.wait_for_timeout(2000)
    t0 = time.time()
    await page.goto(BASE + f"/result/{attempt}", wait_until="domcontentloaded")
    await page.wait_for_timeout(wait * 1000)
    imgs = await page.evaluate("""() => new Promise(done => { const r = indexedDB.open('jeelive-private-images-v1');
      r.onerror = () => done(-1); r.onsuccess = () => { try { const c = r.result.transaction('images').objectStore('images').count();
      c.onsuccess = () => done(c.result); c.onerror = () => done(-2); } catch (e) { done(-3); } }; })""")
    red = await page.locator('text=/Something went wrong|Uncaught|ErrorBoundary/').count()
    await page.screenshot(path=f"/tmp/shots/i154_c_{attempt[:6]}_{retry_after}.jpg", type="jpeg", quality=25)
    st.update(imgs=imgs, red=red, statuses=statuses, one=len(st["one"]), part0=(st["parts"] or [""])[0][-60:])
    await ctx.close()
    print("INFO", attempt[:8], "retry_after", retry_after, "expose", expose, {k: v for k, v in st.items() if k != "parts"}, "nparts", len(st["parts"]), flush=True)
    return st


async def main():
    async with async_playwright() as pw:
        b = await pw.chromium.launch(executable_path="/usr/bin/chromium", args=["--no-sandbox"])
        base = await run(b, CHAPTER)
        check("C1 chapter test result: pictures appear (no stand-in)", base["imgs"] > 0 and not base["red"], base["imgs"])
        print("INFO parts used on /result (links asked):", base["links"] > 0, "cdn", len(base["cdn"]), "pack", len(base["pack"]), "one-by-one", base["one"])
        pyq = await run(b, PYQ)
        print("INFO PYQ: imgs", pyq["imgs"], "links", pyq["links"], "one-by-one", pyq["one"])
        if base["links"]:
            r2 = await run(b, CHAPTER, retry_after=2)
            asks = r2["cdn"] + r2["pack"]
            second = sorted(r2["cdn"])
            ok = r2["busy_cdn"] == 1 and len(second) >= 2 and 1.5 <= second[1] - second[0] <= 8
            check("C2 Retry-After 2: part 0 asked again ~2 s later", ok, {"cdn": r2["cdn"], "pack": r2["pack"], "statuses": r2["statuses"]})
            check("C3 Retry-After 2: pictures arrive", r2["imgs"] > 0, r2["imgs"])
            r3 = await run(b, CHAPTER, retry_after=60, wait=25)
            check("C4 Retry-After 60: no second ask of part 0", len(r3["cdn"]) == 1 and len(r3["pack"]) <= 1, {"cdn": r3["cdn"], "pack": r3["pack"]})
            check("C5 Retry-After 60: pictures still come (one by one)", r3["imgs"] > 0, {"imgs": r3["imgs"], "one": r3["one"]})
            r4 = await run(b, CHAPTER, retry_after=2, expose=False)
            print("INFO C6 CDN 503 without Access-Control-Expose-Headers: cdn", r4["cdn"], "pack", r4["pack"], "imgs", r4["imgs"])
            r5 = await run(b, CHAPTER, retry_after=2, expose=False, busy_pack=False)
            print("INFO C7 CDN 503 only (pack fine): cdn", r5["cdn"], "pack", r5["pack"], "imgs", r5["imgs"])
        await b.close()
    print(f"RESULT {sum(1 for _, o in RES if o)}/{len(RES)}")


asyncio.run(main())
