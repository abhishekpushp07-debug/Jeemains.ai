# Offline Misfire (Pocket 1, 28 Nov 2026), end to end in the browser, READ ONLY for the QA learner.
#   python3 /app/tests/offline_misfire_check.py
# - Every write to the website outside /auth is stopped, except Misfire's "try" and "done" (what a right answer sends):
#   those are answered by the browser and counted. Results are rewritten in the browser so every option question's key
#   is "A" (picking A is right), also in the copies the phone keeps.
# - "No line" is made by the browser: every /api call and every other host is cut.
# Covers: the tab's new name; the website list with a line; the phone's papers when the website's list does not come;
# a question the website lists as "Samajh gaya" left out of the phone's pool; the offline door -> Offline Misfire ->
# setup, mock, result with no line; nothing sent while signed out; the right answers sent once the line and the session
# are back; My Tests' label; the door shut for a phone with no confirmed session.
import asyncio
import json
import re
import sys
import time
from urllib.parse import urlparse

sys.path.insert(0, "/app/tests")
from dotenv import dotenv_values  # noqa: E402
from playwright.async_api import async_playwright  # noqa: E402
from shine_helpers import sign_in  # noqa: E402

BASE = dotenv_values("/app/frontend/.env")["EXPO_PUBLIC_BACKEND_URL"].rstrip("/")
HOST = urlparse(BASE).hostname
RES, BLOCKED, FAKED, ERRORS, CUT_MISFIRE = [], [], [], [], []
KEPT, ORDER = {}, []  # attempt id -> result data (as rewritten), in the order the keeper asked for them
STATE = {"inject": None, "last": time.time(), "down": False}
SHOTS = "/app/test_reports/artifacts/offline_misfire"


def check(name, ok, info=""):
    RES.append((name, bool(ok)))
    print(("PASS " if ok else "FAIL ") + name + (" :: " + str(info) if info != "" else ""), flush=True)


def tid(t):
    return f'[data-testid="{t}"]'


def env(data):
    return json.dumps({"data": data, "error": None, "meta": {"api_version": "1"}})


async def visible(page, t, timeout=8000):
    try:
        await page.wait_for_selector(tid(t), state="visible", timeout=timeout); return True
    except Exception:
        return False


async def txt(page, t):
    loc = page.locator(tid(t))
    return (await loc.first.inner_text()).strip() if await loc.count() else ""


async def setup(ctx):
    async def g(route):
        r = route.request
        if r.method in ("GET", "HEAD", "OPTIONS") or "/api/jl/auth" in r.url:
            await route.fallback(); return
        path = r.url.split("?")[0].replace(BASE, "")
        m = re.search(r"/my/misfire/([^/]+)/(try|done)$", path)
        if m and r.method == "POST":
            FAKED.append(m.group(2) + " " + m.group(1))
            body = {"correct": True, "item": {"id": m.group(1), "status": "open", "tries": 1, "last_correct": True}} if m.group(2) == "try" else {"ok": True}
            await route.fulfill(status=200, content_type="application/json", body=env(body)); return
        BLOCKED.append(r.method + " " + path)
        await route.fulfill(status=418, content_type="application/json", body='{"data":null,"error":{"code":"blocked","message":"blocked by test"},"meta":{}}')
    await ctx.route(re.compile(r".*/api/jl/.*"), g)

    async def results(route):
        if route.request.method != "GET":
            await route.fallback(); return
        resp = await route.fetch()
        try:
            j = await resp.json()
            d = j.get("data") or {}
            for q in d.get("questions") or []:
                if q.get("options"):
                    q["answer"] = "A"; q["accepted_answers"] = ["A"]
            aid = re.search(r"/attempts/([^/]+)/results", route.request.url).group(1)
            if d.get("questions"):
                if aid not in KEPT:
                    ORDER.append(aid)
                KEPT[aid] = d
                STATE["last"] = time.time()
            await route.fulfill(response=resp, body=json.dumps(j))
        except Exception:
            await route.fulfill(response=resp)
    await ctx.route(re.compile(r".*/api/jl/attempts/[^/]+/results.*"), results)

    # The website's "Samajh gaya" list, with one more question in it once the test says so.
    async def fixed(route):
        resp = await route.fetch()
        try:
            j = await resp.json()
            d = j.get("data") or {}
            if STATE["inject"] and "page=1" in route.request.url and isinstance(d.get("items"), list):
                d["items"] = [STATE["inject"], *[x for x in d["items"] if x.get("id") != STATE["inject"]["id"]]]
                d["total"] = int(d.get("total") or 0) + 1
            await route.fulfill(response=resp, body=json.dumps(j))
        except Exception:
            await route.fulfill(response=resp)
    await ctx.route(re.compile(r".*/api/jl/my/misfire\?.*status=fixed.*"), fixed)


async def cut(route):
    u = urlparse(route.request.url)
    if u.hostname != HOST or u.path.startswith("/api/"):
        if "/my/misfire/" in u.path and route.request.method == "POST":
            CUT_MISFIRE.append(u.path)
        await route.abort(); return
    await route.fallback()


async def answer_all(page, value="A"):
    opt = num = 0
    for _ in range(80):
        if await page.locator(tid("mock-integer-input")).count():
            await page.fill(tid("mock-integer-input"), "123456789"); num += 1
        elif await page.locator(tid(f"mock-option-{value}")).count():
            await page.click(tid(f"mock-option-{value}")); opt += 1
        elif await page.locator(tid(f"mock-option-math-{value}")).count():
            await page.click(tid(f"mock-option-math-{value}")); opt += 1
        nxt = page.locator(tid("mock-next-button"))
        if not await nxt.count():
            nxt = page.locator(tid("mock-next-subject"))
        pos = await txt(page, "mock-position")
        if not await nxt.count() or await nxt.get_attribute("aria-disabled") == "true":
            break
        await nxt.click()
        await page.wait_for_timeout(350)
        if await txt(page, "mock-position") == pos:
            break
    return opt, num


def wrong_physics(d):
    return [q for q in d.get("questions") or [] if q.get("outcome") in ("incorrect", "skipped") and q.get("disposition") not in ("bonus_all", "dropped")
            and (q.get("subject") or q.get("section")) == "Physics" and q.get("options")]


async def phone_count(page):
    """Opens the setup while the website's open list does not come: the phone's own count of Physics questions."""
    async def down(route):
        await route.fulfill(status=503, content_type="application/json", body='{"data":null,"error":{"code":"down","message":"down"},"meta":{}}')
    pat = re.compile(r".*/api/jl/my/misfire\?.*status=open.*")
    await page.route(pat, down)
    await page.goto(BASE + "/misfire/mock/new", wait_until="domcontentloaded")
    ok = await visible(page, "mock-new-phone", 90000)
    await visible(page, "mock-new-count", 30000)
    n = await txt(page, "mock-new-open-physics")
    note = await txt(page, "mock-new-phone")
    await page.unroute(pat, down)
    return ok, int(n) if n.isdigit() else -1, note


async def main():
    import os
    os.makedirs(SHOTS, exist_ok=True)
    async with async_playwright() as pw:
        b = await pw.chromium.launch(executable_path="/usr/bin/chromium", args=["--no-sandbox"])
        ctx = await b.new_context(viewport={"width": 390, "height": 844})
        await setup(ctx)
        page = await ctx.new_page()
        page.on("pageerror", lambda e: ERRORS.append(str(e)[:200]))
        await page.goto(BASE + "/", wait_until="domcontentloaded")
        await sign_in(page, width=390)

        # A. The phone keeps the finished papers by itself after sign-in (src/offline/papers.ts).
        t0 = time.time()
        while time.time() - t0 < 300 and (not KEPT or time.time() - STATE["last"] < 30):
            await page.wait_for_timeout(2000)
        check("A1 the phone kept finished papers", len(KEPT) > 0, f"{len(KEPT)} papers in {round(time.time() - t0)} s")

        # B. With a line: the tab's new name, and the setup reads the website's open list (no phone note).
        await page.goto(BASE + "/misfire", wait_until="domcontentloaded")
        await visible(page, "misfire-tab-mock", 45000)
        check("B1 Misfire tab is called 'Offline Misfire'", (await txt(page, "misfire-tab-mock")) == "Offline Misfire", await txt(page, "misfire-tab-mock"))
        await page.click(tid("misfire-tab-mock"))
        check("B2 its hero says OFFLINE MISFIRE", await visible(page, "misfire-mock-hero", 15000) and "OFFLINE MISFIRE" in await txt(page, "misfire-mock-hero"))
        await page.click(tid("misfire-mock-new"))
        ok = await visible(page, "mock-new-count", 60000)
        check("B3 with a line the setup uses the website's list (no phone note)", ok and not await page.locator(tid("mock-new-phone")).count(), await txt(page, "mock-new-header"))
        web_physics = await txt(page, "mock-new-open-physics")

        # C. The website's list does not come: the phone's papers, said so plainly, with a way to try the website again.
        ok, n0, note = await phone_count(page)
        check("C1 website list down -> phone's papers, with the note", ok and "Website se list abhi nahi aa paayi" in note and "Sirf phone par rakhe" in note, note)
        check("C2 'Website se dobara laao' offered", await page.locator(tid("mock-new-web-retry")).count() == 1)
        print("   physics: website", web_physics, "phone", n0, flush=True)
        await page.screenshot(path=f"{SHOTS}/c_phone_note.jpg", type="jpeg", quality=40)

        # D. A question the website lists as "Samajh gaya" is left out of the phone's pool.
        whole = None
        await page.goto(BASE + "/offline/results", wait_until="domcontentloaded")
        await page.wait_for_selector('[data-testid^="kept-row-score-"]', timeout=60000)
        rows = await page.evaluate("""() => [...document.querySelectorAll('[data-testid^="kept-row-pictures-"]')].map((el) => ({ id: el.dataset.testid.slice(18), whole: /Solutions aur pictures phone par/.test(el.innerText) }))""")
        for r in rows:
            if r["whole"] and KEPT.get(r["id"]) and wrong_physics(KEPT[r["id"]]):
                whole = r["id"]; break
        if whole:
            q = wrong_physics(KEPT[whole])[0]
            STATE["inject"] = {"id": f"{whole}:{q['id']}", "attempt_id": whole, "question_id": q["id"], "title": KEPT[whole].get("title"), "subject": "Physics",
                               "chapter": q.get("topic") or "", "number": q.get("number"), "outcome": q.get("outcome"), "type": q.get("type"), "question": None, "status": "fixed", "tries": 1}
            await page.goto(BASE + "/misfire", wait_until="domcontentloaded")
            await visible(page, "misfire-mode-fixed", 45000)
            await page.click(tid("misfire-mode-fixed"))
            await page.wait_for_timeout(5000)  # the page answered, and the phone's note of it written
            ok, n1, _ = await phone_count(page)
            check("D1 a question listed as 'Samajh gaya' is left out (one less on the phone)", ok and n1 == n0 - 1, f"{n0} -> {n1} ({STATE['inject']['id']})")
        else:
            n1 = n0
            check("D1 a whole kept paper with a wrong Physics option question to mark", False, rows[:4])

        # E. No line at all: the offline door -> Offline Misfire -> setup -> mock -> result.
        await ctx.route("**/*", cut)
        STATE["down"] = True
        await page.goto(BASE + "/", wait_until="domcontentloaded")
        check("E1 no line: the offline door", await visible(page, "offline-door-button", 90000))
        await page.click(tid("offline-door-button"))
        check("E2 the offline home offers Offline Misfire", await visible(page, "offline-misfire-open", 20000), await txt(page, "offline-misfire"))
        await page.screenshot(path=f"{SHOTS}/e_offline_home.jpg", type="jpeg", quality=40)
        await page.click(tid("offline-misfire-open"))
        check("E3 its list opens without a line", await visible(page, "misfire-mock-hero", 20000) and "/offline/misfire" in page.url, page.url)
        await page.click(tid("misfire-mock-new"))
        ok = await visible(page, "mock-new-phone", 60000)
        note = await txt(page, "mock-new-phone")
        check("E4 setup from the phone's papers, said so (no 'website' words)", ok and note.startswith("Sirf phone par rakhe") and "/offline/misfire/new" in page.url, note)
        n2 = await txt(page, "mock-new-open-physics")
        check("E5 the same Physics count as the phone's pool before", n2 == str(n1), f"{n2} vs {n1}")
        await page.click(tid("mock-subject-physics"))
        await page.click(tid("mock-count-physics-5"))
        await page.wait_for_timeout(300)
        await page.click(tid("mock-new-bar-go"))
        ok = await visible(page, "mock-ready-screen", 60000)
        check("E6 made with no line: the ready screen", ok and "/offline/misfire/" in page.url, page.url)
        body = await txt(page, "mock-ready-rules")
        check("E7 it says it was made from the phone's papers", "Phone par rakhe papers se bana" in body, body[:120])
        check("E8 title 'Offline Misfire #n'", (await txt(page, "mock-ready-header")).find("Offline Misfire #") >= 0, await txt(page, "mock-ready-header"))
        got = False
        for _ in range(30):
            if "Saare sawaal phone par taiyaar" in await txt(page, "mock-ready-pictures-label"):
                got = True; break
            await page.wait_for_timeout(1000)
        check("E9 every question picture is already on the phone", got, await txt(page, "mock-ready-pictures-label"))
        await page.screenshot(path=f"{SHOTS}/e_ready.jpg", type="jpeg", quality=40)
        await page.click(tid("mock-start"))
        check("E10 the mock runs with no line", await visible(page, "mock-player-screen", 20000))
        imgs = await page.evaluate("""() => [...document.querySelectorAll('[data-testid="mock-question"] img')].filter((i) => i.complete && i.naturalWidth > 0).length""")
        print("   question pictures drawn on Q1:", imgs, flush=True)
        opt, num = await answer_all(page)
        await page.click(tid("mock-submit-top"))
        await visible(page, "mock-confirm-submit", 8000)
        await page.click(tid("mock-confirm-submit"))
        ok = await visible(page, "mock-result-screen", 20000)
        correct = await txt(page, "mock-result-correct")
        check("E11 result with no line, every option answer right (key A)", ok and correct == str(opt), f"correct {correct}, option answers {opt}, numbers {num}")
        check("E12 right answers wait for the line; no 'Abhi bhejo' while signed out", await page.locator(tid("mock-result-waiting")).count() == (1 if opt else 0)
              and not await page.locator(tid("mock-result-send")).count(), await txt(page, "mock-result-waiting"))
        check("E13 no 'Misfire kholo' behind the offline door", not await page.locator(tid("mock-result-misfire")).count())
        check("E14 nothing was sent to Misfire while signed out", not CUT_MISFIRE and not FAKED, (CUT_MISFIRE[:3], FAKED[:3]))
        await page.screenshot(path=f"{SHOTS}/e_result.jpg", type="jpeg", quality=40)
        result_url = page.url
        await page.locator(tid("mock-solution-paper")).scroll_into_view_if_needed()
        await page.click(tid("mock-solution-paper"))
        check("E15 'Asli paper ka result' opens the phone's copy", await visible(page, "kept-result-screen", 20000) and "/offline/result" in page.url, page.url)
        await page.goto(result_url, wait_until="domcontentloaded")
        check("E16 the mock opens again from its link with no line", await visible(page, "mock-result-screen", 30000))

        # F. The line and the session are back: the right answers go to the website by themselves.
        await ctx.unroute("**/*", cut)
        STATE["down"] = False
        await page.goto(BASE + "/", wait_until="domcontentloaded")
        t1 = time.time()
        while time.time() - t1 < 90 and len([f for f in FAKED if f.startswith("done")]) < opt:
            await page.wait_for_timeout(1500)
        tries, dones = len([f for f in FAKED if f.startswith("try")]), len([f for f in FAKED if f.startswith("done")])
        check("F1 line back: each right answer sent once (try, then done) without opening Misfire", tries == opt and dones == opt, f"try {tries}, done {dones}, right {opt}, {round(time.time() - t1)} s")
        await page.goto(BASE + "/tests", wait_until="domcontentloaded")
        await visible(page, "my-tests-tab-completed", 45000)
        await page.click(tid("my-tests-tab-completed"))
        await page.wait_for_timeout(2500)
        labels = await page.locator('[data-testid^="mock-exam-"]').all_inner_texts()
        check("F2 My Tests calls it Offline Misfire", bool(labels) and all(t.startswith("Offline Misfire") for t in labels), labels[:3])
        mid = result_url.split("/offline/misfire/")[1].split("?")[0]
        await page.goto(BASE + f"/misfire/mock/{mid}", wait_until="domcontentloaded")
        await visible(page, "mock-result-screen", 30000)
        moved = await txt(page, "mock-result-moved")
        check("F3 the result says they went to 'Samajh gaya'", (moved.startswith(f"{opt} sawaal") if opt else not moved), moved)
        check("F4 nothing else was written for the QA learner", not BLOCKED, BLOCKED[:5])

        # G. A phone with no confirmed session: Offline Misfire stays shut.
        other = await b.new_context(viewport={"width": 390, "height": 844})
        await other.route("**/*", cut)
        p2 = await other.new_page()
        await p2.goto(BASE + "/offline/misfire", wait_until="domcontentloaded")
        check("G1 no session ever on this phone: shut, with the sign-in way", await visible(p2, "mock-closed", 60000), await txt(p2, "mock-closed"))
        await p2.goto(BASE + "/offline/misfire/new", wait_until="domcontentloaded")
        check("G2 its setup is shut too", await visible(p2, "mock-closed", 60000) and not await p2.locator(tid("mock-new-count")).count())
        await other.close()

        check("Z no page errors", not ERRORS, ERRORS[:3])
        await b.close()
    print(f"\n{sum(1 for _, ok in RES if ok)}/{len(RES)} passed", flush=True)


asyncio.run(main())
