# Offline Misfire (Pocket 1) — extra checks by the testing agent, READ ONLY for the QA learner.
#   python3 /app/tests/iter_offline_misfire_extra.py
# Beyond offline_misfire_check.py: a WRONG answer in an offline mock is never sent; a right answer the website REFUSES
# (try -> correct:false) shows as refused and no "done" is sent for it; the 7-day confirmed-sign-in rule (stamp aged
# 8 days -> shut); My Tests card title "Offline Misfire #n"; read-only regression spot-check of other screens.
# Every website write outside /auth is stopped (418) and listed; try/done are faked in the browser.
import asyncio
import json
import os
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
STATE = {"last": time.time(), "kept": 0, "refuse_first": True, "refused_id": None}
SHOTS = "/app/test_reports/artifacts/offline_misfire_extra"


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
            if m.group(2) == "try":
                ok = True
                if STATE["refuse_first"] and STATE["refused_id"] is None:
                    STATE["refused_id"] = m.group(1); ok = False
                body = {"correct": ok, "item": {"id": m.group(1), "status": "open", "tries": 1, "last_correct": ok}}
            else:
                body = {}
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
            if d.get("questions"):
                STATE["kept"] += 1; STATE["last"] = time.time()
            await route.fulfill(response=resp, body=json.dumps(j))
        except Exception:
            await route.fulfill(response=resp)
    await ctx.route(re.compile(r".*/api/jl/attempts/[^/]+/results.*"), results)


async def cut(route):
    u = urlparse(route.request.url)
    if u.hostname != HOST or u.path.startswith("/api/"):
        if "/my/misfire/" in u.path and route.request.method == "POST":
            CUT_MISFIRE.append(u.path)
        await route.abort(); return
    await route.fallback()


async def answer_all(page):
    """First option question answered B (wrong, key is A), every other option A, numbers a wrong value."""
    opt = num = wrong = 0
    for _ in range(80):
        if await page.locator(tid("mock-integer-input")).count():
            await page.fill(tid("mock-integer-input"), "123456789"); num += 1
        else:
            pick = "B" if not wrong else "A"
            for pre in ("mock-option-", "mock-option-math-"):
                if await page.locator(tid(pre + pick)).count():
                    await page.click(tid(pre + pick))
                    if pick == "B":
                        wrong += 1
                    else:
                        opt += 1
                    break
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
    return opt, wrong, num


async def main():
    os.makedirs(SHOTS, exist_ok=True)
    async with async_playwright() as pw:
        b = await pw.chromium.launch(executable_path="/usr/bin/chromium", args=["--no-sandbox"])
        ctx = await b.new_context(viewport={"width": 390, "height": 844})
        await setup(ctx)
        page = await ctx.new_page()
        page.on("pageerror", lambda e: ERRORS.append(str(e)[:200]))
        await page.goto(BASE + "/", wait_until="domcontentloaded")
        await sign_in(page, width=390)

        t0 = time.time()
        while time.time() - t0 < 300 and (not STATE["kept"] or time.time() - STATE["last"] < 30):
            await page.wait_for_timeout(2000)
        check("X0 keeper kept papers", STATE["kept"] > 0, f"{STATE['kept']} results in {round(time.time() - t0)} s")

        # R. Read-only regression spot check (no paper started).
        for path, want in (("/misfire", "misfire-tab-all"), ("/choice", None), ("/tests", "my-tests-tab-completed"), ("/pyq", None), ("/catalogue", None), ("/mission", None)):
            before = len(ERRORS)
            await page.goto(BASE + path, wait_until="domcontentloaded")
            await page.wait_for_timeout(5000)
            ok = await visible(page, want, 30000) if want else True
            err = await page.evaluate("""() => [...document.querySelectorAll('[data-testid*="error"]')].filter(e => e.offsetParent).map(e => e.innerText.slice(0,80)).join(' | ')""")
            check(f"R {path} opens without errors", ok and len(ERRORS) == before and not err, err or ERRORS[before:][:2])
        await page.goto(BASE + "/misfire", wait_until="domcontentloaded")
        if await visible(page, "misfire-mode-fixed", 30000):
            await page.click(tid("misfire-mode-fixed")); await page.wait_for_timeout(3000)
            check("R misfire 'Samajh gaya' pill opens", True)
        else:
            check("R misfire 'Samajh gaya' pill opens", False)

        # E. No line: offline door -> setup -> mock with one WRONG option answer.
        await ctx.route("**/*", cut)
        await page.goto(BASE + "/", wait_until="domcontentloaded")
        check("E1 offline door", await visible(page, "offline-door-button", 90000))
        await page.click(tid("offline-door-button"))
        await visible(page, "offline-misfire-open", 20000)
        await page.click(tid("offline-misfire-open"))
        await visible(page, "misfire-mock-new", 20000)
        await page.click(tid("misfire-mock-new"))
        ok = await visible(page, "mock-new-phone", 60000)
        note = await txt(page, "mock-new-phone")
        check("E2 setup note 'Sirf phone par rakhe N papers se · M sawaal mile'", ok and re.match(r"^Sirf phone par rakhe \d+ papers? se · \d+ sawaal mile", note), note)
        await page.click(tid("mock-subject-physics"))
        await page.click(tid("mock-count-physics-5"))
        await page.wait_for_timeout(300)
        await page.click(tid("mock-new-bar-go"))
        check("E3 ready screen offline", await visible(page, "mock-ready-screen", 60000))
        title = (await txt(page, "mock-ready-header")).split("\n")[-1]
        await page.click(tid("mock-start"))
        await visible(page, "mock-player-screen", 20000)
        opt, wrong, num = await answer_all(page)
        await page.click(tid("mock-submit-top"))
        await visible(page, "mock-confirm-submit", 8000)
        await page.click(tid("mock-confirm-submit"))
        await visible(page, "mock-result-screen", 20000)
        correct, incorrect = await txt(page, "mock-result-correct"), await txt(page, "mock-result-incorrect")
        check("E4 wrong option counted wrong", correct == str(opt) and incorrect == str(wrong + num), f"correct {correct} incorrect {incorrect} (A {opt}, B {wrong}, num {num})")
        waiting = await txt(page, "mock-result-waiting")
        check("E5 waiting counts only the right ones; no send button", waiting.startswith(f"{opt} sahi") and not await page.locator(tid("mock-result-send")).count(), waiting)
        await page.screenshot(path=f"{SHOTS}/e_result.jpg", type="jpeg", quality=40)
        mid = page.url.split("/offline/misfire/")[1].split("?")[0]

        # S. 7-day rule: the confirmed stamp aged 8 days shuts Offline Misfire (then put back).
        stamp = await page.evaluate("() => localStorage.getItem('kept.confirmed.v1')")
        key = "kept.confirmed.v1"
        if stamp is None:  # storage helper may prefix keys
            key = await page.evaluate("() => Object.keys(localStorage).find(k => k.includes('kept.confirmed.v1')) || ''")
            stamp = await page.evaluate("(k) => localStorage.getItem(k)", key) if key else None
        if stamp:
            raw = json.loads(stamp); inner = json.loads(raw) if isinstance(raw, str) else raw
            old = dict(inner); old["at"] = int(time.time() * 1000) - 8 * 86400000
            val = json.dumps(json.dumps(old)) if isinstance(raw, str) else json.dumps(old)
            await page.evaluate("([k, v]) => localStorage.setItem(k, v)", [key, val])
            await page.goto(BASE + "/offline/misfire", wait_until="domcontentloaded")
            check("S1 stamp 8 days old -> mock-closed", await visible(page, "mock-closed", 30000), await txt(page, "mock-closed"))
            await page.goto(BASE + f"/offline/misfire/{mid}", wait_until="domcontentloaded")
            await page.wait_for_timeout(6000)
            check("S2 the mock itself shut too", not await page.locator(tid("mock-result-screen")).count())
            await page.evaluate("([k, v]) => localStorage.setItem(k, v)", [key, stamp])
            await page.goto(BASE + "/offline/misfire", wait_until="domcontentloaded")
            check("S3 stamp fresh again -> open", await visible(page, "misfire-mock-hero", 30000))
        else:
            check("S1 confirmed stamp found in localStorage", False, await page.evaluate("() => Object.keys(localStorage).join(',')"))
        check("E6 nothing sent while offline", not CUT_MISFIRE and not FAKED, (CUT_MISFIRE[:3], FAKED[:3]))

        # F. Line back: right answers sent; the first is REFUSED by the (faked) website; the wrong one never sent.
        await ctx.unroute("**/*", cut)
        await page.goto(BASE + "/", wait_until="domcontentloaded")
        t1 = time.time()
        while time.time() - t1 < 90 and len([f for f in FAKED if f.startswith("try")]) < opt:
            await page.wait_for_timeout(1500)
        await page.wait_for_timeout(4000)
        tries, dones = [f for f in FAKED if f.startswith("try")], [f for f in FAKED if f.startswith("done")]
        check("F1 try only for right answers, done for all but the refused one", len(tries) == opt and len(dones) == opt - 1
              and not any(STATE["refused_id"] in d for d in dones), f"try {len(tries)} done {len(dones)} right {opt} ({round(time.time() - t1)} s)")
        await page.goto(BASE + f"/misfire/mock/{mid}", wait_until="domcontentloaded")
        await visible(page, "mock-result-screen", 30000)
        moved, refused = await txt(page, "mock-result-moved"), await txt(page, "mock-result-refused")
        check("F2 result shows moved (n-1) and refused", moved.startswith(f"{opt - 1} sawaal") and bool(refused), f"moved='{moved}' refused='{refused[:100]}'")
        check("F3 refused answer re-marked wrong", await txt(page, "mock-result-correct") == str(opt - 1), await txt(page, "mock-result-correct"))
        await page.screenshot(path=f"{SHOTS}/f_result.jpg", type="jpeg", quality=40)
        await page.goto(BASE + "/tests", wait_until="domcontentloaded")
        await visible(page, "my-tests-tab-completed", 45000)
        await page.click(tid("my-tests-tab-completed"))
        await page.wait_for_timeout(2500)
        t = await txt(page, f"mock-title-{mid}")
        check("F4 My Tests card title 'Offline Misfire #n'", re.match(r"^Offline Misfire #\d+$", t) is not None and t == title, f"'{t}' vs ready '{title}'")
        check("F5 nothing else written", not BLOCKED, BLOCKED[:5])
        check("Z no page errors", not ERRORS, ERRORS[:3])
        await b.close()
    print(f"\n{sum(1 for _, ok in RES if ok)}/{len(RES)} passed", flush=True)


asyncio.run(main())
