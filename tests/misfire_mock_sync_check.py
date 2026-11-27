# Misfire Mock: right answers while the website line is down (waiting + "Abhi bhejo"), then the website refusing one
# (counted wrong). READ ONLY: every non-GET under /api/jl outside /auth is answered in the browser; results rewritten in
# the browser so option key = "A". usage: python3 misfire_mock_sync_check.py [width]
import asyncio
import json
import re
import sys

sys.path.insert(0, "/app/tests")
from dotenv import dotenv_values  # noqa: E402
from playwright.async_api import async_playwright  # noqa: E402
from shine_helpers import sign_in  # noqa: E402

BASE = dotenv_values("/app/frontend/.env")["EXPO_PUBLIC_BACKEND_URL"].rstrip("/")
W = int(sys.argv[1]) if len(sys.argv) > 1 else 390
RES, BLOCKED, CALLS, ERRORS = [], [], [], []
MODE = {"try": "down"}
REF = {}  # down | refuse_first


def check(name, ok, info=""):
    RES.append((name, bool(ok)))
    print(("PASS " if ok else "FAIL ") + name + (" :: " + str(info) if info != "" else ""), flush=True)


def tid(t):
    return f'[data-testid="{t}"]'


async def main():
    async with async_playwright() as pw:
        b = await pw.chromium.launch(executable_path="/usr/bin/chromium", args=["--no-sandbox"])
        ctx = await b.new_context(viewport={"width": W, "height": 844})

        async def g(route):
            r = route.request
            if r.method in ("GET", "HEAD", "OPTIONS") or "/api/jl/auth" in r.url:
                await route.fallback(); return
            path = r.url.split("?")[0].replace(BASE, "")
            m = re.search(r"/my/misfire/([^/]+)/(try|done)$", path)
            if m and r.method == "POST":
                CALLS.append(m.group(2))
                if MODE["try"] == "down":
                    await route.fulfill(status=503, content_type="application/json", body='{"data":null,"error":{"code":"down","message":"down"},"meta":{}}'); return
                REF.setdefault("id", m.group(1))
                ok = not (m.group(2) == "try" and REF["id"] == m.group(1) and MODE["try"] == "refuse_first")
                body = {"correct": ok, "item": {"id": m.group(1), "status": "open", "tries": 1}} if m.group(2) == "try" else {"ok": True}
                await route.fulfill(status=200, content_type="application/json", body=json.dumps({"data": body, "error": None, "meta": {"api_version": "1"}})); return
            BLOCKED.append(r.method + " " + path)
            await route.fulfill(status=418, content_type="application/json", body='{"data":null,"error":{"code":"blocked","message":"blocked"},"meta":{}}')
        await ctx.route(re.compile(r".*/api/jl/.*"), g)

        async def results(route):
            if route.request.method != "GET":
                await route.fallback(); return
            resp = await route.fetch()
            j = await resp.json()
            for q in (j.get("data") or {}).get("questions") or []:
                if q.get("options"):
                    q["answer"] = "A"; q["accepted_answers"] = ["A"]
            await route.fulfill(response=resp, body=json.dumps(j))
        await ctx.route(re.compile(r".*/api/jl/attempts/[^/]+/results.*"), results)

        page = await ctx.new_page()
        page.on("pageerror", lambda e: ERRORS.append(str(e)[:200]))
        await page.goto(BASE + "/", wait_until="domcontentloaded")
        await sign_in(page, width=W)
        await page.goto(BASE + "/misfire/mock/new", wait_until="domcontentloaded")
        await page.wait_for_selector(tid("mock-new-count"), timeout=60000)
        await page.click(tid("mock-subject-physics")); await page.wait_for_timeout(300)
        for _ in range(3):
            await page.click(tid("mock-count-more"))
        await page.click(tid("mock-new-bar-go"))
        await page.wait_for_selector(tid("mock-ready-screen"), timeout=120000)
        await page.click(tid("mock-start"))
        await page.wait_for_selector(tid("mock-player-screen"), timeout=15000)
        for i in range(3):
            if await page.locator(tid("mock-option-A")).count():
                await page.click(tid("mock-option-A"))
            if await page.locator(tid("mock-next-button")).count():
                await page.click(tid("mock-next-button")); await page.wait_for_timeout(300)
        await page.click(tid("mock-submit-top")); await page.click(tid("mock-confirm-submit"))
        await page.wait_for_selector(tid("mock-result-screen"), timeout=20000)
        await page.wait_for_timeout(4000)
        c = await page.inner_text(tid("mock-result-correct"))
        w = await page.locator(tid("mock-result-waiting")).count()
        check("line down: waiting card + Abhi bhejo", w == 1 and await page.locator(tid("mock-result-send")).count() == 1,
              (await page.inner_text(tid("mock-result-understood"))).replace("\n", " ")[:140])
        print("correct:", c, "calls while down:", CALLS)
        check("line down: stops after first failing batch (no done sent)", "done" not in CALLS, CALLS)
        await page.screenshot(path=f"/app/test_reports/artifacts/misfire_mock_waiting_{W}.png", quality=40, type="jpeg")
        CALLS.clear(); REF.clear(); MODE["try"] = "refuse_first"
        await page.click(tid("mock-result-send"))
        await page.wait_for_timeout(5000)
        refused = await page.locator(tid("mock-result-refused")).count()
        moved = await page.inner_text(tid("mock-result-moved")) if await page.locator(tid("mock-result-moved")).count() else None
        c2, w2 = await page.inner_text(tid("mock-result-correct")), await page.inner_text(tid("mock-result-incorrect"))
        check("resend: one refused -> counted wrong, rest moved", refused == 1 and moved and int(c2) == int(c) - 1, f"moved={moved} correct {c}->{c2} wrong={w2} calls={CALLS}")
        check("resend: no waiting left", await page.locator(tid("mock-result-waiting")).count() == 0)
        await b.close()
    print("BLOCKED", BLOCKED)
    print("PAGEERRORS", ERRORS)
    print(f"{sum(1 for _, ok in RES if ok)}/{len(RES)} passed")

asyncio.run(main())
