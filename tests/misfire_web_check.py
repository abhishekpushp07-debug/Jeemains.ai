# Misfire Mock made by the website (Pocket 2, 28 Nov 2026), in the browser, READ ONLY for the QA learner.
#   python3 /app/tests/misfire_web_check.py
# The website's answers are played by the browser: the switch (door A's "misfire"), the paper history of kind "misfire",
# door C (POST /choice/papers, never sent to the website), a made paper's page, and a result marked as a Misfire Mock.
# Every other write to the website is stopped (418) and listed. Nothing is started.
# A. switch not said (the real answer): no "Mock" tab, nothing changed; ?web=1 is Offline Misfire; door C never asked.
# The shapes are the contract the website agreed on 28 Nov 2026 (GET /my/misfire/mocks, door C answer with asked/given).
# B. switch on: the "Mock" tab, its list, a result's "Samajh gaya" count, the setup asking door C (404, 503, then a
#    paper) with one key for every retry, chapters sent when only some are ticked, the paper's page, My Tests' label.
import asyncio
import json
import re
import sys

sys.path.insert(0, "/app/tests")
from dotenv import dotenv_values  # noqa: E402
from playwright.async_api import async_playwright  # noqa: E402
from shine_helpers import sign_in  # noqa: E402

BASE = dotenv_values("/app/frontend/.env")["EXPO_PUBLIC_BACKEND_URL"].rstrip("/")
RES, BLOCKED, ASKS, ERRORS, BANKS = [], [], [], [], []
STATE = {"switch": False, "papers": "404", "finished": None, "pool": False, "first_test": None, "retry": False}
SET_ID = "misfire-set-0001"
RUNNING = "misfire-running-0001"
UNSTARTED = "misfire-set-0003"
SHOTS = "/app/test_reports/artifacts/misfire_web"


def check(name, ok, info=""):
    RES.append((name, bool(ok)))
    print(("PASS " if ok else "FAIL ") + name + (" :: " + str(info) if info != "" else ""), flush=True)


def tid(t):
    return f'[data-testid="{t}"]'


def env(data):
    return json.dumps({"data": data, "error": None, "meta": {"api_version": "1"}})


def env_error(message, code="x"):
    return json.dumps({"data": None, "error": {"code": code, "message": message}, "meta": {"api_version": "1"}})


async def visible(page, t, timeout=8000):
    try:
        await page.wait_for_selector(tid(t), state="visible", timeout=timeout); return True
    except Exception:
        return False


async def txt(page, t):
    loc = page.locator(tid(t))
    return (await loc.first.inner_text()).strip() if await loc.count() else ""


async def tab_labels(page):
    return await page.locator('[data-testid^="misfire-tab-"]').evaluate_all(
        "els => els.filter(e => /^misfire-tab-[a-z-]+$/.test(e.dataset.testid)).map(e => [e.dataset.testid.slice(12), e.innerText.trim()])")


async def setup(ctx):
    async def g(route):
        r = route.request
        if r.method in ("GET", "HEAD", "OPTIONS") or "/api/jl/auth" in r.url:
            await route.fallback(); return
        path = r.url.split("?")[0].replace(BASE, "")
        if path.endswith("/api/jl/choice/papers") and r.method == "POST":
            body = json.loads(r.post_data or "{}")
            ASKS.append(body)
            mode = STATE["papers"]
            asked = sum((body.get("counts") or {}).values())
            sentences = {"422a": (422, "Chune hue chapters mein abhi koi khula sawaal nahi hai. Doosre chapter chuno."),
                         "422b": (422, "Har subject mein 25 tak sawaal chuno, kul kam se kam 1."),
                         "409a": (409, "Misfire Mock abhi band hai."),
                         "409b": (409, "Yeh mock pehle hi ban chuka hai. Misfire ke Mock tab mein dekho."),
                         "429": (429, "Aaj ke Misfire Mock poore ho gaye. Kal naya mock banao.")}
            if mode == "404":
                await route.fulfill(status=404, content_type="application/json", body=env_error("Not found", "not_found"))
            elif mode == "503":
                await route.fulfill(status=503, content_type="application/json", body=env_error("Service unavailable", "busy"))
            elif mode in sentences:
                code, text = sentences[mode]
                await route.fulfill(status=code, content_type="application/json", body=env_error(text, mode))
            else:  # the agreed answer: the set, its name and number, asked and given, minutes
                given = max(1, asked - 2) if mode == "fewer" else asked
                await route.fulfill(status=201, content_type="application/json", body=env({
                    "set_id": SET_ID, "title": "Misfire Mock #4", "number": 4, "asked": asked, "given": given, "minutes": 12}))
            return
        BLOCKED.append(r.method + " " + path)
        await route.fulfill(status=418, content_type="application/json", body='{"data":null,"error":{"code":"blocked","message":"blocked by test"},"meta":{}}')
    await ctx.route(re.compile(r".*/api/jl/.*"), g)

    # T1 fix: the Dream meter is the owner's real data. A result played as test_kind "misfire" makes the app DELETE
    # /api/rf/dream/mocks/<id> (and the server then "drops" that real paper forever). The browser answers every write.
    async def dream(route):
        if route.request.method == "GET":
            await route.fallback(); return
        await route.fulfill(status=200, content_type="application/json", body='{"ok":true}')
    await ctx.route(re.compile(r".*/api/rf/dream.*"), dream)

    # Door A as our server answers it; the website's switch is played by the browser when the test says so.
    async def bank(route):
        resp = await route.fetch()
        try:
            j = await resp.json()
            BANKS.append(j.get("misfire"))
            if STATE["switch"]:
                j["misfire"] = True
            await route.fulfill(response=resp, body=json.dumps(j))
        except Exception:
            await route.fulfill(response=resp)
    await ctx.route(re.compile(r".*/api/choice/bank.*"), bank)

    # The agreed list (28 Nov 2026): GET /my/misfire/mocks, newest first, those not started too; attempt = the newest one.
    async def mocks(route):
        fin = STATE["finished"]
        items = [{"set_id": UNSTARTED, "title": "Misfire Mock #3", "number": 3, "created_at": 1764400000, "asked": 15, "given": 15, "minutes": 32, "attempt": None},
                 {"set_id": "misfire-set-0002", "title": "Misfire Mock #2", "number": 2, "created_at": 1764299000, "asked": 10, "given": 10, "minutes": 21,
                  "attempt": {"id": RUNNING, "status": "active", "resumable": True, "started_at": 1764300000, "submitted_at": None, "summary": None}}]
        if fin:
            items.append({"set_id": "misfire-set-0001b", "title": "Misfire Mock #1", "number": 1, "created_at": 1764199000, "asked": 15, "given": 15, "minutes": 32,
                          "attempt": {"id": fin, "status": "submitted", "resumable": False, "started_at": 1764200000, "submitted_at": 1764203000,
                                      "summary": {"score": 20, "maximum": 60, "correct": 6, "incorrect": 5, "skipped": 4}}})
        await route.fulfill(status=200, content_type="application/json", body=env({"items": items, "page": 1, "pages": 1, "total": len(items)}))
    await ctx.route(re.compile(r".*/api/jl/my/misfire/mocks\?.*"), mocks)

    async def results(route):
        resp = await route.fetch()
        try:
            j = await resp.json()
            if STATE["finished"] and f"/attempts/{STATE['finished']}/results" in route.request.url and isinstance(j.get("data"), dict):
                j["data"]["test_kind"] = "misfire"
                if not STATE["retry"]:  # a retry of wrong questions: no "misfire" (the website's word)
                    j["data"]["misfire"] = {"understood": 3, "total": 15}
            await route.fulfill(response=resp, body=json.dumps(j))
        except Exception:
            await route.fulfill(response=resp)
    await ctx.route(re.compile(r".*/api/jl/attempts/[^/]+/results.*"), results)

    async def a_set(route):
        await route.fulfill(status=200, content_type="application/json", body=env({
            "id": SET_ID, "title": "Misfire Mock · 5 Q · 28 Nov", "exam": "JEE Main", "test_kind": "misfire", "count": 5, "maximum": 20,
            "rules": {"correct": 4, "wrong": -1, "skipped": 0, "minutes": 12}, "types": {"mcq": 4, "integer": 1}, "attempt": None, "saved": False}))
    await ctx.route(re.compile(rf".*/api/jl/my/sets/{SET_ID}.*"), a_set)

    # My Tests: the newest finished paper is played as a Misfire Mock.
    async def tests(route):
        resp = await route.fetch()
        try:
            j = await resp.json()
            items = (j.get("data") or {}).get("items") or []
            if items and STATE["switch"]:
                items[0]["test_kind"] = "misfire"; STATE["first_test"] = items[0].get("id")
            if items and not STATE["finished"]:
                done = next((x for x in items if x.get("summary")), None)
                if done:
                    STATE["finished"] = done.get("id")
            await route.fulfill(response=resp, body=json.dumps(j))
        except Exception:
            await route.fulfill(response=resp)
    await ctx.route(re.compile(r".*/api/jl/my/tests\?.*"), tests)

    # Physics' open list with two chapters (the QA learner has one untagged one), to send a chapter choice.
    async def pool(route):
        if not STATE["pool"] or "subject=Physics" not in route.request.url or "status=open" not in route.request.url:
            await route.fallback(); return
        await route.fulfill(status=200, content_type="application/json", body=env({
            "items": [], "total": 14, "page": 1, "pages": 1, "waiting": 0, "chapters": [{"name": "01 Units and Measurement", "count": 8}, {"name": "02 Kinematics", "count": 6}]}))
    await ctx.route(re.compile(r".*/api/jl/my/misfire\?.*"), pool)


async def open_tab_list(page):
    await page.goto(BASE + "/misfire", wait_until="domcontentloaded")
    return await visible(page, "misfire-tab-all", 45000)


async def main():
    async with async_playwright() as pw:
        b = await pw.chromium.launch(executable_path="/usr/bin/chromium", args=["--no-sandbox"])

        # ---- A. The switch as the website says it today (not said): nothing changes.
        ctx = await b.new_context(viewport={"width": 390, "height": 844})
        await setup(ctx)
        page = await ctx.new_page()
        page.on("pageerror", lambda e: ERRORS.append(str(e)[:200]))
        await page.goto(BASE + "/", wait_until="domcontentloaded")
        await sign_in(page, width=390)
        await page.goto(BASE + "/tests", wait_until="domcontentloaded")
        await visible(page, "my-tests-exam-filters", 45000)
        await page.wait_for_timeout(2500)
        check("A0 a finished paper found for later", bool(STATE["finished"]), STATE["finished"])
        check("A1 My Tests has no Misfire Mock label", await page.locator('[data-testid^="attempt-exam-"]:has-text("Misfire Mock")').count() == 0)
        check("A2 Misfire opens", await open_tab_list(page))
        await page.wait_for_timeout(3000)
        labels = await tab_labels(page)
        check("A3 no 'Mock' tab while the switch is not said", not any(k == "web" for k, _ in labels) and labels[:2] == [["all", "Sab"], ["mock", "Offline Misfire"]], labels)
        check("A4 our server says misfire false today", BANKS and all(x is False for x in BANKS), BANKS)
        await page.goto(BASE + "/misfire?tab=web", wait_until="domcontentloaded")
        await visible(page, "misfire-tab-all", 45000)
        await page.wait_for_timeout(2500)
        check("A5 ?tab=web shows Sab, not a web list", await page.locator(tid("misfire-web-mocks")).count() == 0, await tab_labels(page))
        await page.goto(BASE + "/misfire/mock/new?web=1", wait_until="domcontentloaded")
        await visible(page, "mock-new-screen", 45000)
        await page.wait_for_timeout(2500)
        check("A6 ?web=1 with the switch off is Offline Misfire", "Offline Misfire banao" in await txt(page, "mock-new-header"), await txt(page, "mock-new-header"))
        await page.goto(BASE + "/choice", wait_until="domcontentloaded")
        ok = await visible(page, "choice-screen", 45000) or await visible(page, "choice-landing", 5000)
        body = await page.locator("#root").inner_text()
        check("A7 Student Choice still opens", ok or "Student Choice" in body or "Chapters chuno" in body, body[:100].replace("\n", " | "))
        check("A8 door C never asked", not ASKS, ASKS)
        await ctx.unroute_all(behavior="ignoreErrors")
        await ctx.close()

        # ---- B. The website's switch on (played by the browser).
        STATE["switch"] = True
        ctx = await b.new_context(viewport={"width": 390, "height": 844})
        await setup(ctx)
        page = await ctx.new_page()
        page.on("pageerror", lambda e: ERRORS.append(str(e)[:200]))
        await page.goto(BASE + "/", wait_until="domcontentloaded")
        await sign_in(page, width=390)
        check("B1 Misfire opens", await open_tab_list(page))
        ok = await visible(page, "misfire-tab-web", 30000)
        labels = await tab_labels(page)
        check("B2 'Mock' tab after Sab, Offline Misfire kept", ok and labels[:3] == [["all", "Sab"], ["web", "Mock"], ["mock", "Offline Misfire"]], labels)
        await page.click(tid("misfire-tab-web"))
        ok = await visible(page, "misfire-web-hero", 15000)
        check("B3 Mock tab: hero", ok and "MISFIRE MOCK" in await txt(page, "misfire-web-hero"), (await txt(page, "misfire-web-hero"))[:80])
        fin = STATE["finished"]
        ok = await visible(page, "misfire-web-misfire-set-0001b", 15000)
        card = await txt(page, "misfire-web-misfire-set-0001b")
        check("B4 finished mock listed with its score", ok and "20" in card and "/60" in card and "Result dekho" in card and "15 sawaal · 32 min" in card, card.replace("\n", " | "))
        run = await txt(page, "misfire-web-misfire-set-0002")
        check("B5 running mock says Resume", "Resume" in run and "CHAL RAHA HAI" in run, run.replace("\n", " | "))
        new = await txt(page, f"misfire-web-{UNSTARTED}")
        check("B5b a mock not started is listed (newest first)", "SHURU NAHI HUA" in new and "Shuru karo" in new and "Misfire Mock #3" in new
              and (await page.locator('[data-testid^="misfire-web-misfire-"]').first.get_attribute("data-testid")) == f"misfire-web-{UNSTARTED}", new.replace("\n", " | "))
        await page.screenshot(path=f"{SHOTS}_list.jpg", quality=40, type="jpeg")
        await page.click(tid(f"misfire-web-{UNSTARTED}"))
        await page.wait_for_timeout(2500)
        check("B5c a mock not started opens its paper's page", f"/set/{UNSTARTED}" in page.url, page.url)
        await page.goto(BASE + "/misfire?tab=web", wait_until="domcontentloaded")
        await visible(page, "misfire-web-misfire-set-0001b", 45000)
        await page.click(tid("misfire-web-misfire-set-0001b"))
        ok = await visible(page, "result-misfire-understood", 60000)
        if not ok and await page.locator('[data-testid="share-gate-open"]').count():
            await page.click('[data-testid="share-gate-open"]'); ok = await visible(page, "result-misfire-understood", 30000)
        n = await txt(page, "result-misfire-understood-count")
        check("B6 result says how many went to Samajh gaya", ok and n.startswith("3 / 15 sawaal") and f"/result/{fin}" in page.url, n or page.url)
        await page.screenshot(path=f"{SHOTS}_result.jpg", quality=40, type="jpeg")

        # Setup on the website: 404 (door not built), 503, then a paper; one key for all three.
        await page.goto(BASE + "/misfire?tab=web", wait_until="domcontentloaded")
        await visible(page, "misfire-web-new", 45000)
        await page.click(tid("misfire-web-new"))
        ok = await visible(page, "mock-new-screen", 20000)
        await visible(page, "mock-new-open-physics", 30000)
        check("B7 setup is the website's mock", ok and "Misfire Mock banao" in await txt(page, "mock-new-header") and "MISFIRE MOCK" in await txt(page, "mock-new-hero"), await txt(page, "mock-new-header"))
        check("B8 no phone note on the website's mock", await page.locator(tid("mock-new-phone")).count() == 0)
        await page.click(tid("mock-subject-physics"))
        await page.click(tid("mock-count-physics-5"))
        await page.click(tid("mock-new-bar-go"))
        ok = await visible(page, "mock-making-error", 20000)
        e404 = await txt(page, "mock-making-error")
        check("B9 door missing (404): plain sentence", ok and "Paper banana abhi jeelive.ai se jud raha hai" in e404, e404)
        STATE["papers"] = "503"
        await page.click(tid("mock-making-retry"))
        await page.wait_for_timeout(2500)
        e503 = await txt(page, "mock-making-error")
        check("B10 website busy (503): plain Hinglish sentence, sheet stays", await page.locator(tid("mock-making-error")).count() == 1 and len(ASKS) >= 2
              and "jeelive.ai abhi jawab nahi de raha" in e503, e503)
        STATE["papers"] = "ok"
        await page.click(tid("mock-making-retry"))
        ok = await visible(page, "set-detail-screen", 30000)
        body = await page.locator("#root").inner_text()
        check("B11 the made paper's page opens", ok and "Misfire Mock" in body and SET_ID in page.url, page.url)
        check("B12 nothing was started", await page.locator(tid("set-start-button")).count() == 1 and not BLOCKED, BLOCKED)
        a = ASKS[0] if ASKS else {}
        check("B13 door C body", a.get("exam") == "jee-main" and a.get("mode") == "misfire" and a.get("counts") == {"Physics": 5, "Chemistry": 0, "Mathematics": 0} and "chapters" not in a
              and re.match(r"^[0-9a-f-]{36}$", a.get("request_key", "")), a)
        keys = {x.get("request_key") for x in ASKS}
        check("B14 one key for every retry of the same ask", len(ASKS) >= 3 and len(keys) == 1, [len(ASKS), keys])
        await page.screenshot(path=f"{SHOTS}_set.jpg", quality=40, type="jpeg")

        # The website's own sentences, shown as they come (422, 409, 429), and fewer given than asked.
        await page.goto(BASE + "/misfire/mock/new?web=1", wait_until="domcontentloaded")
        await visible(page, "mock-new-open-physics", 45000)
        await page.click(tid("mock-subject-physics"))
        await page.click(tid("mock-count-physics-5"))
        said = {}
        for mode in ("422a", "422b", "409a", "409b", "429"):
            STATE["papers"] = mode
            if await page.locator(tid("mock-making-retry")).count():
                await page.click(tid("mock-making-retry"))
            else:  # the website's own "no" (4xx): the sheet offers to change the choice, then Mock banao again
                if await page.locator(tid("mock-making-close")).count():
                    await page.click(tid("mock-making-close"))
                    await page.wait_for_timeout(600)
                await page.click(tid("mock-new-bar-go"))
            await visible(page, "mock-making-error", 20000)
            await page.wait_for_timeout(800)
            said[mode] = await txt(page, "mock-making-error")
        want = {"422a": "Chune hue chapters mein abhi koi khula sawaal nahi hai. Doosre chapter chuno.", "422b": "Har subject mein 25 tak sawaal chuno, kul kam se kam 1.",
                "409a": "Misfire Mock abhi band hai.", "409b": "Yeh mock pehle hi ban chuka hai. Misfire ke Mock tab mein dekho.", "429": "Aaj ke Misfire Mock poore ho gaye. Kal naya mock banao."}
        check("B14b the website's sentences shown word for word", all(want[m] in said.get(m, "") for m in want), said)
        STATE["papers"] = "fewer"
        if await page.locator(tid("mock-making-close")).count():
            await page.click(tid("mock-making-close"))
            await page.wait_for_timeout(600)
            await page.click(tid("mock-new-bar-go"))
        else:
            await page.click(tid("mock-making-retry"))
        ok = await visible(page, "mock-making-fewer-note", 20000)
        note = await txt(page, "mock-making-fewer-note")
        check("B14c fewer given than asked: said once, before the paper", ok and "Aapne 5 sawaal maange the, 3 mile" in note and "/set/" not in page.url, note)
        await page.screenshot(path=f"{SHOTS}_fewer.jpg", quality=40, type="jpeg")
        await page.click(tid("mock-making-open"))
        ok = await visible(page, "set-detail-screen", 30000)
        check("B14d 'Paper kholo' opens the paper", ok and SET_ID in page.url, page.url)
        STATE["papers"] = "ok"

        # Only some chapters ticked: they go to the website by their Misfire names, under a new key.
        STATE["pool"] = True
        await page.goto(BASE + "/misfire/mock/new?web=1", wait_until="domcontentloaded")
        await visible(page, "mock-chapter-all", 45000)
        await page.click(tid("mock-subject-physics"))
        await page.click(tid("mock-chapter-all"))
        await page.click(tid("mock-chapter-0"))
        await page.click(tid("mock-count-physics-5"))
        before = len(ASKS)
        await page.click(tid("mock-new-bar-go"))
        await visible(page, "set-detail-screen", 30000)
        last = ASKS[-1] if len(ASKS) > before else {}
        check("B15 chosen chapters sent", last.get("chapters") == {"Physics": ["01 Units and Measurement"]} and last.get("counts", {}).get("Physics") == 5, last)
        check("B16 a new ask gets a new key", last.get("request_key") and last.get("request_key") not in keys, last.get("request_key"))
        STATE["pool"] = False

        # My Tests: a Misfire Mock row says so.
        await page.goto(BASE + "/tests", wait_until="domcontentloaded")
        await visible(page, "my-tests-exam-filters", 45000)
        await page.wait_for_timeout(2500)
        first = STATE["first_test"]
        lab = await txt(page, f"attempt-exam-{first}") if first else ""
        check("B17 My Tests labels a Misfire Mock", "Misfire Mock" in lab, lab)
        # Offline Misfire untouched.
        await page.goto(BASE + "/misfire?tab=mock", wait_until="domcontentloaded")
        ok = await visible(page, "misfire-mock-hero", 45000)
        check("B18 Offline Misfire tab as before", ok and "OFFLINE MISFIRE" in await txt(page, "misfire-mock-hero"))
        await page.goto(BASE + "/misfire/mock/new", wait_until="domcontentloaded")
        await visible(page, "mock-new-screen", 45000)
        await page.wait_for_timeout(2000)
        check("B19 Offline Misfire setup as before (no ?web)", "Offline Misfire banao" in await txt(page, "mock-new-header"))
        check("Z no page errors", not ERRORS, ERRORS[:3])
        check("Z nothing written to the website", not BLOCKED, BLOCKED)
        await ctx.unroute_all(behavior="ignoreErrors")
        await ctx.close()

        # ---- C. A retry of wrong questions (its own attempt; a fresh browser, nothing kept): its result has no
        # "misfire" (the website's word), so no "Samajh gaya" card.
        STATE["retry"] = True
        ctx = await b.new_context(viewport={"width": 390, "height": 844})
        await setup(ctx)
        page = await ctx.new_page()
        page.on("pageerror", lambda e: ERRORS.append(str(e)[:200]))
        await page.goto(BASE + "/", wait_until="domcontentloaded")
        await sign_in(page, width=390)
        await page.goto(BASE + f"/result/{STATE['finished']}", wait_until="domcontentloaded")
        await visible(page, "result-analysis-panel", 60000)
        await page.wait_for_timeout(3000)
        head = await txt(page, "result-header")
        check("C1 a retry's result: no Samajh gaya card, still a Misfire Mock", await page.locator(tid("result-misfire-understood")).count() == 0 and "MISFIRE MOCK" in head.upper(), head)
        check("Z2 no page errors, nothing written", not ERRORS and not BLOCKED, [ERRORS[:3], BLOCKED])
        await ctx.unroute_all(behavior="ignoreErrors")
        await b.close()
    print(f"\n{sum(1 for _, ok in RES if ok)}/{len(RES)} passed", flush=True)


asyncio.run(main())
