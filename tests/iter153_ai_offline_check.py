# Iteration 153 (T1): AI solutions kept for offline + per_page=100 on the Class 11/12 view. READ-ONLY for the QA learner.
# ai-solutions of ONE attempt (the first the keeper asks about) is answered by the browser with a READY item for its
# real questions[0].id; every other attempt gets the live answer (all pending). keep is lowered to 3 in the browser to
# keep the run short. Writes under /api/jl outside /auth that touch attempts/start/profile are stopped.
#   python3 /app/tests/iter153_ai_offline_check.py
import asyncio
import json
import re
import sys
import time
from urllib.parse import urlparse

from dotenv import dotenv_values
from playwright.async_api import async_playwright

sys.path.insert(0, "/app/tests")
from shine_helpers import sign_in  # noqa: E402

BASE = dotenv_values("/app/frontend/.env")["EXPO_PUBLIC_BACKEND_URL"].rstrip("/")
OUT = "/tmp/iter153"
checks, written, ai_asked, catalogue, results_ids, hosts = [], [], [], [], [], set()
state = {"fake": None, "qids": [], "t": time.time()}
T = """(id) => { const el = document.querySelector(`[data-testid="${id}"]`); return el ? (el.innerText || '').replace(/[\\u{F0000}-\\u{FFFFD}]/gu, '').replace(/\\s+/g, ' ').trim() : null; }"""


def check(name, ok, detail=""):
    checks.append(bool(ok))
    print(("PASS " if ok else "FAIL ") + name + (" | " + str(detail)[:400] if detail != "" else ""), flush=True)


async def guard(route):
    req = route.request
    path = req.url.split("/api/jl", 1)[1].split("?")[0]
    if req.method in ("GET", "HEAD", "OPTIONS") or path.startswith("/auth/"):
        await route.fallback(); return
    written.append(f"{req.method} {path}")
    if re.search(r"/attempts|/start|/profile|solution-open", path):
        await route.abort()
    else:
        await route.fallback()


async def ai_route(route):
    url = route.request.url
    aid = re.search(r"/attempts/([^/]+)/ai-solutions", url).group(1)
    ai_asked.append(aid)
    if state["fake"] not in (None, aid):
        await route.fallback(); return
    res = await route.fetch(url=url.replace("/ai-solutions", "/results?score_version=original"))
    body = await res.json()
    data = body.get("data") if isinstance(body, dict) and "data" in body else body
    qs = (data or {}).get("questions") or []
    if not qs:
        await route.fallback(); return
    state["fake"], state["qids"] = aid, [q["id"] for q in qs[:1]]
    item = {"question_id": qs[0]["id"], "state": "ready", "label": "AI generated", "model": "gpt-6-astra", "flag": None,
            "solution": {"concept": "Test concept", "given": ["x = 1"], "steps": [{"title": "1. Step one", "explanation": "Because $a+b$"}], "final_answer": "A", "key_agrees": True}}
    out = {"data": {"items": [item], "ready": 1, "total": len(qs), "disclosure": "AI generated. AI can make mistakes."}, "error": None, "meta": {"api_version": "1"}}
    state["total"] = len(qs)
    await route.fulfill(status=200, content_type="application/json", body=json.dumps(out))


async def switches(route):
    res = await route.fetch()
    body = await res.json()
    body["keep"] = 3
    await route.fulfill(status=200, content_type="application/json", body=json.dumps(body))


def on_request(req):
    u = req.url
    if "/api/jl/" in u or (urlparse(u).hostname or "") != urlparse(BASE).hostname:
        state["t"] = time.time()
    if "/exam-navigation/jee-main/catalogue" in u:
        catalogue.append(u.split("/api/jl", 1)[1])
    m = re.search(r"/attempts/([^/]+)/results\?", u)
    if m:
        results_ids.append(m.group(1))
    if re.search(r"\.(webp|png|jpe?g)(\?|$)", u) or "cdn" in (urlparse(u).hostname or ""):
        if urlparse(u).hostname != urlparse(BASE).hostname:
            hosts.add(urlparse(u).hostname)


async def cut(route):
    await route.abort()


async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(executable_path="/usr/bin/chromium", args=["--no-sandbox"])
        ctx = await browser.new_context(viewport={"width": 390, "height": 844})
        page = await ctx.new_page()
        errors = []
        page.on("console", lambda m: errors.append(m.text[:200]) if m.type == "error" else None)
        page.on("pageerror", lambda e: errors.append("PAGEERROR " + str(e)[:200]))
        page.on("request", on_request)
        await page.route(re.compile(r".*/api/jl/.*"), guard)
        await page.route(re.compile(r".*/api/app/switches.*"), switches)
        await page.route(re.compile(r".*/api/jl/attempts/[^/]+/ai-solutions.*"), ai_route)
        await page.goto(BASE + "/", wait_until="domcontentloaded")
        await sign_in(page)
        check("1 signed in, Home on screen", await page.locator('[data-testid="home-tile-choice"]').count() > 0)
        await page.screenshot(path=f"{OUT}_home.jpeg", type="jpeg", quality=40)
        # wait for keeper: results asked, then quiet 30 s
        t0 = time.time()
        while time.time() - t0 < 600:
            if len(set(results_ids)) >= 2 and time.time() - state["t"] > 30:
                break
            await page.wait_for_timeout(1000)
        check("2a keeper ran (results + ai-solutions asked)", results_ids and ai_asked, f"results {results_ids} ai {ai_asked} in {round(time.time() - t0)} s")
        fake = state["fake"]
        await page.goto(BASE + "/offline/results", wait_until="domcontentloaded")
        await page.wait_for_selector('[data-testid^="kept-row-score-"]', timeout=60000)
        await page.wait_for_timeout(1500)
        await page.screenshot(path=f"{OUT}_rows.jpeg", type="jpeg", quality=40)
        rows = await page.evaluate("""() => [...document.querySelectorAll('[data-testid^="kept-row-score-"]')].map(e => e.dataset.testid.slice(15))""")
        ai_line = await page.evaluate(T, f"kept-row-ai-{fake}")
        check("2b faked row shows '1 / N AI solutions phone par'", ai_line == f"1 / {state.get('total')} AI solutions phone par", f"{ai_line} (data.total={state.get('total')}, items=1)")
        others = [r for r in rows if r != fake]
        no_ai = [r for r in others if await page.locator(f'[data-testid="kept-row-ai-{r}"]').count()]
        check("3a other rows (live = pending) show no AI line", others and not no_ai, f"rows {len(rows)}, with AI line {no_ai}")
        pics = [await page.evaluate(T, f"kept-row-pictures-{r}") for r in rows]
        check("3b kept-row-pictures still shown", all(pics), pics)
        # reader, faked paper
        await page.click(f'[data-testid="kept-row-{fake}"]')
        await page.wait_for_selector('[data-testid="kept-result-screen"]', timeout=30000)
        await page.wait_for_timeout(1500)
        note = await page.evaluate(T, "kept-result-note")
        check("2c note mentions the AI step-by-step solution (singular for one)", note and ("1 sawaal ka AI step-by-step solution bhi saath hai" in note or "AI step-by-step solution bhi saath hain" in note), note)
        nums = await page.evaluate("""() => [...document.querySelectorAll('[data-testid^="kept-question-"]')].map(e => e.dataset.testid).filter(t => /^kept-question-\\d+$/.test(t)).map(t => Number(t.slice(14)))""")
        first = min(nums) if nums else 1
        await page.click(f'[data-testid="kept-question-{first}"]')
        await page.wait_for_timeout(600)
        block = await page.evaluate(T, f"kept-ai-{first}")
        check("2d question 1 has kept-ai block with Concept / Step-by-step / Final answer", block and all(w.lower() in block.lower() for w in ("Concept", "Step-by-step", "Final answer", "Test concept")), block)
        await page.locator(f'[data-testid="kept-ai-{first}"]').scroll_into_view_if_needed()
        await page.screenshot(path=f"{OUT}_reader_ai.jpeg", type="jpeg", quality=40)
        second = sorted(nums)[1] if len(nums) > 1 else None
        if second:
            await page.click(f'[data-testid="kept-question-{second}"]')
            await page.wait_for_timeout(600)
            check("2e a question with no ready item shows no AI block", await page.locator(f'[data-testid="kept-ai-{second}"]').count() == 0)
        # reader, a paper without AI
        if others:
            await page.go_back(); await page.wait_for_selector(f'[data-testid="kept-row-{others[0]}"]', timeout=30000)
            await page.click(f'[data-testid="kept-row-{others[0]}"]')
            await page.wait_for_selector('[data-testid="kept-result-screen"]', timeout=30000)
            await page.wait_for_timeout(1500)
            note2 = await page.evaluate(T, "kept-result-note")
            check("3c paper without AI: old note, no kept-ai block", note2 == "Yeh phone par rakhi copy hai. Poora analysis, rank aur AI solution internet ke saath app mein milte hain." and await page.locator('[data-testid^="kept-ai-"]').count() == 0, note2)
            check("3d score + subject tabs + rail", bool(await page.evaluate(T, "kept-result-score")) and await page.locator('[data-testid^="kept-subject-"]').count() > 0 and await page.locator('[data-testid^="kept-question-"]').count() > 0, await page.evaluate(T, "kept-result-score"))
        # no line
        no_line = re.compile(r".*/api/(jl|rf|app)/.*")
        await page.route(no_line, cut)
        await page.route(lambda u: urlparse(u).hostname in hosts, cut)
        n_ai = len(ai_asked)
        await page.goto(BASE + "/", wait_until="domcontentloaded")
        await page.wait_for_selector('[data-testid="offline-door-button"]', timeout=75000)
        await page.click('[data-testid="offline-door-button"]')
        await page.wait_for_selector('[data-testid="offline-results-open"]', timeout=20000)
        await page.click('[data-testid="offline-results-open"]')
        await page.wait_for_selector(f'[data-testid="kept-row-{fake}"]', timeout=30000)
        off_line = await page.evaluate(T, f"kept-row-ai-{fake}")
        await page.click(f'[data-testid="kept-row-{fake}"]')
        await page.wait_for_selector('[data-testid="kept-result-screen"]', timeout=30000)
        await page.wait_for_timeout(1500)
        await page.click(f'[data-testid="kept-question-{first}"]')
        await page.wait_for_timeout(600)
        block2 = await page.evaluate(T, f"kept-ai-{first}")
        await page.screenshot(path=f"{OUT}_offline_ai.jpeg", type="jpeg", quality=40)
        check("2f NO LINE: row AI line + same AI block, nothing asked", off_line and block2 and "Test concept" in block2 and len(ai_asked) == n_ai, f"{off_line} | {block2 and block2[:80]}")
        await page.go_back(); await page.wait_for_timeout(800)
        await page.go_back(); await page.wait_for_selector('[data-testid="offline-start"]', timeout=20000)
        await page.click('[data-testid="offline-start"]')
        await page.wait_for_timeout(3000)
        await page.screenshot(path=f"{OUT}_offline_rf.jpeg", type="jpeg", quality=40)
        rf_ids = await page.evaluate("""() => [...document.querySelectorAll('[data-testid]')].map(e => e.dataset.testid).filter(t => /offline|plain|round|card|option/.test(t)).slice(0, 15)""")
        check("6 offline Rapid Fire opens from offline-start", len(rf_ids) > 0, rf_ids)
        await page.unroute(no_line, cut)
        # catalogue per_page
        catalogue.clear()
        await page.goto(BASE + "/catalogue?slug=jee-main&kind=chapters", wait_until="domcontentloaded")
        await page.wait_for_selector('[data-testid="catalogue-class-11"]', timeout=60000)
        await page.wait_for_timeout(5000)
        counts = {k: await page.evaluate(T, f"catalogue-class-{k}") for k in ("all", "11", "12")}
        phys = [u for u in catalogue if "subject=Physics" in u and "q=&" in u]
        check("4a Physics asked with per_page=100 on pages 1,2,3", phys and all("per_page=100" in u for u in phys) and sorted(re.search(r"page=(\d+)", u).group(1) for u in phys) == ["1", "2", "3"], phys)
        check("4b Physics counts All 30 / 15 / 15", counts == {"all": "All 30", "11": "Class 11 15", "12": "Class 12 15"}, counts)
        for subj, want in (("chemistry", {"all": "All 24", "11": "Class 11 11", "12": "Class 12 12"}), ("mathematics", {"all": "All 27", "11": "Class 11 17", "12": "Class 12 10"})):
            await page.click(f'[data-testid="catalogue-subject-{subj}"]')
            await page.wait_for_timeout(5000)
            c = {k: await page.evaluate(T, f"catalogue-class-{k}") for k in ("all", "11", "12")}
            check(f"4c {subj} counts", c == want, c)
        await page.click('[data-testid="catalogue-subject-chemistry"]'); await page.wait_for_timeout(3000)
        other = await page.evaluate(T, "catalogue-head-other")
        check("4d Chemistry 'Other' head with 1 chapter", other and "1" in other, other)
        bad = [u for u in catalogue if "kind=chapters" in u and "per_page=100" not in u]
        print("   catalogue requests:", len(catalogue), "without per_page:", bad[:3])
        check("5 no write touched attempts/start/profile", not [w for w in written if re.search(r"/attempts|/start|/profile", w)], written[:8])
        serious = [e for e in errors if not re.search(r"Failed to load resource|ERR_FAILED|net::|ERR_INTERNET", e)]
        print("   console errors (non-network):", serious[:8])
        await browser.close()
    print(f"RESULT {sum(checks)}/{len(checks)} passed; fake attempt {fake}")


asyncio.run(main())
