# T1 extra checks for Misfire Mock (Pocket 2), READ ONLY for the QA learner. Complements tests/misfire_web_check.py.
#   python3 /app/tests/misfire_web_t1_extra.py
# Every non-GET under /api/jl (outside /auth) is answered by the browser (door C faked) or stopped (418). Nothing started.
import asyncio
import json
import re
import sys

sys.path.insert(0, "/app/tests")
from dotenv import dotenv_values  # noqa: E402
from playwright.async_api import async_playwright  # noqa: E402
from shine_helpers import sign_in  # noqa: E402

BASE = dotenv_values("/app/frontend/.env")["EXPO_PUBLIC_BACKEND_URL"].rstrip("/")
RES, BLOCKED, ASKS, ERRORS, DREAM = [], [], [], [], []
FIN = "1ea510f2-1d2a-41f7-9bb4-a8b28c16f98f"
SET_ID = "misfire-set-t1-0001"
S = {"switch": True, "papers": "422", "hist": "two", "res": "full", "pool": True}
SHOTS = "/app/test_reports/artifacts/misfire_t1"


def check(name, ok, info=""):
    RES.append((name, bool(ok)))
    print(("PASS " if ok else "FAIL ") + name + (" :: " + str(info) if info != "" else ""), flush=True)


def tid(t):
    return f'[data-testid="{t}"]'


def env(data):
    return json.dumps({"data": data, "error": None, "meta": {"api_version": "1"}})


async def vis(page, t, timeout=15000):
    try:
        await page.wait_for_selector(tid(t), state="visible", timeout=timeout); return True
    except Exception:
        return False


async def txt(page, t):
    loc = page.locator(tid(t))
    return (await loc.first.inner_text()).strip() if await loc.count() else ""


async def box(page, t):
    b = await page.locator(tid(t)).first.bounding_box()
    return (round(b["width"]), round(b["height"])) if b else None


async def setup(ctx):
    async def guard(route):
        r = route.request
        if r.method in ("GET", "HEAD", "OPTIONS") or "/api/jl/auth" in r.url:
            await route.fallback(); return
        if r.url.split("?")[0].endswith("/api/jl/choice/papers") and r.method == "POST":
            ASKS.append(json.loads(r.post_data or "{}"))
            m = S["papers"]
            if m == "422":
                await route.fulfill(status=422, content_type="application/json", body=json.dumps({"data": None, "error": {"code": "too_few", "message": "TEST_ Itne open sawaal nahi hain."}, "meta": {}}))
            elif m == "500":
                await route.fulfill(status=500, content_type="application/json", body=json.dumps({"data": None, "error": {"code": "x", "message": "Internal Server Error"}, "meta": {}}))
            elif m == "bad":
                await route.fulfill(status=201, content_type="application/json", body=env({"set_id": "a b"}))
            else:
                await route.fulfill(status=201, content_type="application/json", body=env({"set_id": SET_ID}))
            return
        BLOCKED.append(r.method + " " + r.url)
        await route.fulfill(status=418, content_type="application/json", body='{"data":null,"error":{"code":"blocked","message":"blocked"},"meta":{}}')
    await ctx.route(re.compile(r".*/api/jl/.*"), guard)

    async def dream(route):
        if route.request.method != "GET":
            DREAM.append(route.request.method + " " + route.request.url.split("/api/")[1][:60])
        await route.fulfill(status=200, content_type="application/json", body='{"ok":true,"mocks":[],"dreams":[]}')
    await ctx.route(re.compile(r".*/api/rf/dream.*"), dream)

    async def bank(route):
        resp = await route.fetch()
        try:
            j = await resp.json()
            if S["switch"] is not None:
                j["misfire"] = S["switch"]
            await route.fulfill(response=resp, body=json.dumps(j))
        except Exception:
            await route.fulfill(response=resp)
    await ctx.route(re.compile(r".*/api/choice/bank.*"), bank)

    async def history(route):
        if S["hist"] == "500":
            await route.fulfill(status=500, content_type="application/json", body='{"data":null,"error":{"code":"x","message":"busy"},"meta":{}}'); return
        items = [] if S["hist"] == "empty" else [{"id": FIN, "title": "TEST_ Misfire Mock 15 Q", "status": "completed", "started_at": 1764200000, "submitted_at": 1764203000,
                                                  "summary": {"score": 20, "maximum": 60, "correct": 6, "incorrect": 5, "skipped": 4}}]
        await route.fulfill(status=200, content_type="application/json", body=env({"items": items, "pages": 1}))
    await ctx.route(re.compile(r".*/api/jl/exam-navigation/jee-main/history\?kind=misfire.*"), history)

    async def results(route):
        resp = await route.fetch()
        try:
            j = await resp.json()
            if isinstance(j.get("data"), dict) and S["res"] != "plain":
                j["data"]["test_kind"] = "misfire"
                if S["res"] == "full":
                    j["data"]["misfire"] = {"understood": 3, "total": 15}
                else:
                    j["data"].pop("misfire", None)
            await route.fulfill(response=resp, body=json.dumps(j))
        except Exception:
            await route.fulfill(response=resp)
    await ctx.route(re.compile(r".*/api/jl/attempts/[^/]+/results.*"), results)

    async def a_set(route):
        await route.fulfill(status=200, content_type="application/json", body=env({
            "id": SET_ID, "title": "TEST_ Misfire Mock 5 Q", "exam": "JEE Main", "test_kind": "misfire", "count": 5, "maximum": 20,
            "rules": {"correct": 4, "wrong": -1, "skipped": 0, "minutes": 12}, "types": {"mcq": 5}, "attempt": None, "saved": False}))
    await ctx.route(re.compile(rf".*/api/jl/my/sets/{SET_ID}.*"), a_set)

    async def pool(route):
        u = route.request.url
        if not S["pool"] or "status=open" not in u or "subject=" not in u:
            await route.fallback(); return
        ch = {"Physics": [{"name": "01 Units and Measurement", "count": 8}, {"name": "02 Kinematics", "count": 6}],
              "Chemistry": [{"name": "05 Thermodynamics", "count": 7}, {"name": "06 Equilibrium", "count": 4}]}
        sub = next((s for s in ("Physics", "Chemistry", "Mathematics") if f"subject={s}" in u), "Mathematics")
        c = ch.get(sub, [])
        await route.fulfill(status=200, content_type="application/json", body=env({"items": [], "total": sum(x["count"] for x in c), "page": 1, "pages": 1, "waiting": 0, "chapters": c}))
    await ctx.route(re.compile(r".*/api/jl/my/misfire\?.*"), pool)


async def tabs(page):
    return await page.locator('[data-testid^="misfire-tab-"]').evaluate_all(
        "els => els.filter(e => /^misfire-tab-[a-z-]+$/.test(e.dataset.testid)).map(e => e.dataset.testid.slice(12))")


async def main():
    async with async_playwright() as pw:
        b = await pw.chromium.launch(executable_path="/usr/bin/chromium", args=["--no-sandbox"])
        ctx = await b.new_context(viewport={"width": 390, "height": 844})
        await setup(ctx)
        page = await ctx.new_page()
        page.on("pageerror", lambda e: ERRORS.append(str(e)[:200]))
        await page.goto(BASE + "/", wait_until="domcontentloaded")
        await sign_in(page, width=390)

        # G0 deep link straight to the setup with switch on (cold load)
        await page.goto(BASE + "/misfire/mock/new?web=1", wait_until="domcontentloaded")
        await vis(page, "mock-new-header", 45000); await vis(page, "mock-new-open-physics", 30000)
        h = await txt(page, "mock-new-header")
        check("G0 cold deep link ?web=1 with switch on = Misfire Mock banao", "Misfire Mock banao" in h, h.replace("\n", " | "))
        hero = await txt(page, "mock-new-hero-body")
        print("INFO hero body:", hero)

        # G1 422 with message shown; 500 -> message; bad set_id -> error
        await page.click(tid("mock-subject-physics")); await page.click(tid("mock-count-physics-5"))
        await page.click(tid("mock-new-bar-go"))
        await vis(page, "mock-making-error", 20000)
        e = await txt(page, "mock-making-error")
        check("G1 422 shows the website's error.message", "TEST_ Itne open sawaal nahi hain." in e, e)
        S["papers"] = "500"; await page.click(tid("mock-making-retry")); await page.wait_for_timeout(2500)
        e = await txt(page, "mock-making-error")
        check("G2 500 keeps an error on the sheet", bool(e), e)
        S["papers"] = "bad"; await page.click(tid("mock-making-retry")); await page.wait_for_timeout(2500)
        e = await txt(page, "mock-making-error")
        check("G3 malformed set_id refused", "Paper ban nahi paaya" in e and "/set/" not in page.url, e)
        check("G4 same key across 3 retries", len(ASKS) == 3 and len({a["request_key"] for a in ASKS}) == 1, [len(ASKS)])
        await page.screenshot(path=f"{SHOTS}_err.jpg", quality=40, type="jpeg")
        # cancel, tick only Kinematics in Physics, 2 Chemistry with all chapters
        if await page.locator(tid("mock-making-cancel")).count():
            await page.click(tid("mock-making-cancel")); await page.wait_for_timeout(600)
        await page.click(tid("mock-subject-physics")); await page.wait_for_timeout(400)
        await page.click(tid("mock-chapter-0")); await page.wait_for_timeout(400)  # untick the first (Units)
        await page.click(tid("mock-subject-chemistry")); await page.wait_for_timeout(400)
        await page.click(tid("mock-count-chemistry-5")); await page.wait_for_timeout(400)
        S["papers"] = "ok"
        await page.click(tid("mock-new-bar-go"))
        ok = await vis(page, "set-detail-screen", 30000)
        a = ASKS[-1]
        check("G5 chapters only for the restricted subject; counts follow", a.get("chapters") == {"Physics": ["02 Kinematics"]} and a["counts"] == {"Physics": 5, "Chemistry": 5, "Mathematics": 0}
              and a["request_key"] != ASKS[0]["request_key"], a)
        await page.wait_for_timeout(1500)
        eb = await page.locator("#root").inner_text()
        check("G6 set page eyebrow 'JEE Main · Misfire Mock' (shown upper-case)", ok and "JEE MAIN · MISFIRE MOCK" in eb.upper() and SET_ID in page.url, page.url)
        check("G7 nothing started on set page", not BLOCKED, BLOCKED)

        # G8 Mock tab: touch targets, card -> result, result 'Misfire kholo' -> tab web
        await page.goto(BASE + "/misfire?tab=web", wait_until="domcontentloaded")
        await vis(page, f"misfire-web-{FIN}", 45000)
        check("G8 ?tab=web with switch on opens the Mock list", await page.locator(tid("misfire-web-hero")).count() == 1)
        sizes = {t: await box(page, t) for t in ("misfire-tab-web", "misfire-web-new", f"misfire-web-{FIN}")}
        check("G9 touch targets >= 44 high", all(s and s[1] >= 44 for s in sizes.values()), sizes)
        await page.screenshot(path=f"{SHOTS}_list.jpg", quality=40, type="jpeg")
        await page.click(tid(f"misfire-web-{FIN}"))
        ok = await vis(page, "result-misfire-understood", 60000)
        check("G10 card opens /result/<id> with count", ok and f"/result/{FIN}" in page.url and (await txt(page, "result-misfire-understood-count")).startswith("3 / 15"), page.url)
        print("INFO result-misfire-open size", await box(page, "result-misfire-open"))
        await page.screenshot(path=f"{SHOTS}_result.jpg", quality=40, type="jpeg")
        check("G11 Dream meter: a misfire result is taken out (DELETE faked), never added", not any(x.startswith("POST") and FIN in x for x in DREAM), DREAM)
        await page.click(tid("result-misfire-open"))
        await page.wait_for_timeout(5000)
        ok = await page.locator(tid("misfire-web-hero") + " >> visible=true").count() >= 1  # the older Misfire screen stays mounted (hidden) in the stack
        check("G12 'Misfire kholo' -> Misfire Mock tab", ok and "/misfire" in page.url, page.url)

        # G13 result w/o misfire field -> general sentence; plain result -> no card
        S["res"] = "kind"
        await page.goto(BASE + f"/result/{FIN}", wait_until="domcontentloaded")
        await vis(page, "result-misfire-understood", 60000)
        n = await txt(page, "result-misfire-understood-count")
        check("G13 no misfire field -> general sentence", n.startswith("Sahi kiye sawaal"), n)
        S["res"] = "plain"
        await page.goto(BASE + f"/result/{FIN}", wait_until="domcontentloaded")
        await vis(page, "result-tab-analysis", 60000); await page.wait_for_timeout(4000)
        check("G14 ordinary result: no Misfire card", await page.locator(tid("result-misfire-understood")).count() == 0)

        # G15 empty list and error list
        S["hist"] = "empty"
        await page.goto(BASE + "/misfire?tab=web", wait_until="domcontentloaded")
        check("G15 empty state", await vis(page, "misfire-web-empty", 45000))
        S["hist"] = "500"
        await page.goto(BASE + "/misfire?tab=web", wait_until="domcontentloaded")
        await vis(page, "misfire-web-hero", 45000); await page.wait_for_timeout(4000)
        body = await page.locator("#root").inner_text()
        check("G16 list error after a cached (empty) list: the cached list stays (cold error case: tests/misfire_web_t1_debug.py D1)", await page.locator('[data-testid^="misfire-web-error"]').count() > 0 or await page.locator(tid("misfire-web-empty")).count() > 0, body[-200:].replace("\n", " | "))
        await page.screenshot(path=f"{SHOTS}_err_list.jpg", quality=40, type="jpeg")

        # G17 switch as string "true" -> shut (frontend strict)
        await ctx.close()
        S["switch"] = "true"; S["hist"] = "two"
        ctx = await b.new_context(viewport={"width": 390, "height": 844})
        await setup(ctx)
        page = await ctx.new_page()
        page.on("pageerror", lambda e: ERRORS.append(str(e)[:200]))
        await page.goto(BASE + "/", wait_until="domcontentloaded")
        await sign_in(page, width=390)
        await page.goto(BASE + "/misfire", wait_until="domcontentloaded")
        await vis(page, "misfire-tab-all", 45000); await page.wait_for_timeout(4000)
        t = await tabs(page)
        check("G17 misfire:'true' (string) keeps the tab shut", "web" not in t and t[:2] == ["all", "mock"], t)
        await ctx.close(); await b.close()
    check("Z no page errors", not ERRORS, ERRORS)
    check("Z nothing written", not BLOCKED, BLOCKED)
    print(f"\n{sum(ok for _, ok in RES)}/{len(RES)} passed")


if __name__ == "__main__":
    asyncio.run(main())
