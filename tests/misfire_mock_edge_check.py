# Misfire Mock edge cases (T1, iteration 160), READ ONLY for the QA learner: same guards as misfire_mock_check.py
# (every non-GET under /api/jl outside /auth -> 418 and listed; misfire try/done answered in the browser and counted;
# results rewritten in the browser so option key = "A").
# Covers: My Tests exam tab filtering + red look, chapter subset / 25 cap / disabled counts, remove mock, right answers ->
# try+done once each, result filters/rail/links, palette/mark/clear, timer expiry settle (Date shifted in browser), sign-out clears mocks.
# usage: python3 misfire_mock_edge_check.py [width]
import asyncio
import json
import re
import sys
from collections import Counter

sys.path.insert(0, "/app/tests")
from dotenv import dotenv_values  # noqa: E402
from playwright.async_api import async_playwright  # noqa: E402
from shine_helpers import sign_in  # noqa: E402

BASE = dotenv_values("/app/frontend/.env")["EXPO_PUBLIC_BACKEND_URL"].rstrip("/")
W = int(sys.argv[1]) if len(sys.argv) > 1 else 390
RES, BLOCKED, FAKED, ERRORS = [], [], [], []
SHOTS = f"/app/test_reports/artifacts/misfire_mock_edge_{W}"


def check(name, ok, info=""):
    RES.append((name, bool(ok)))
    print(("PASS " if ok else "FAIL ") + name + (" :: " + str(info) if info != "" else ""), flush=True)


def tid(t):
    return f'[data-testid="{t}"]'


def env(data):
    return json.dumps({"data": data, "error": None, "meta": {"api_version": "1"}})


async def guards(ctx):
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
            for q in (j.get("data") or {}).get("questions") or []:
                if q.get("options"):
                    q["answer"] = "A"; q["accepted_answers"] = ["A"]
            await route.fulfill(response=resp, body=json.dumps(j))
        except Exception:
            await route.fulfill(response=resp)
    await ctx.route(re.compile(r".*/api/jl/attempts/[^/]+/results.*"), results)


async def visible(page, t, timeout=8000):
    try:
        await page.wait_for_selector(tid(t), state="visible", timeout=timeout); return True
    except Exception:
        return False


async def txt(page, t):
    loc = page.locator(tid(t))
    return (await loc.first.inner_text()).strip() if await loc.count() else None


async def clipped(page, sel):
    """Labels inside `sel` whose text is wider than its box (clipped)."""
    return await page.evaluate("""(sel) => [...document.querySelectorAll(sel)].flatMap(root => [...root.querySelectorAll('div[dir="auto"]')])
        .filter(e => e.scrollWidth > e.clientWidth + 1 || e.getBoundingClientRect().right > window.innerWidth + 1).map(e => e.textContent).slice(0, 8)""", sel)


async def open_new(page):
    await page.goto(BASE + "/misfire/mock/new", wait_until="domcontentloaded")
    return await visible(page, "mock-new-count", 60000)


async def build(page, plan, label):
    """plan: {subject: count or ('chapters', [idx...], count)}"""
    for s, v in plan.items():
        await page.click(tid(f"mock-subject-{s}"))
        await page.wait_for_timeout(300)
        if isinstance(v, tuple):
            await page.click(tid("mock-chapter-all"))  # all off
            for i in v[1]:
                await page.click(tid(f"mock-chapter-{i}"))
            n = v[2]
        else:
            n = v
        for _ in range(n):
            if await page.locator(tid("mock-count-more") + '[aria-disabled="true"]').count():
                break
            await page.click(tid("mock-count-more"))
    bar = await txt(page, "mock-new-bar")
    print(label, "bar:", bar.replace("\n", " | "))
    await page.click(tid("mock-new-bar-go"))
    ok = await visible(page, "mock-ready-screen", 120000)
    check(f"{label}: built, ready screen", ok)
    return ok, bar


async def answer_all(page, value="A"):
    """Answers every question in order; returns count of option answers (right with key A) and integer answers."""
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


async def main():
    import os
    os.makedirs(SHOTS, exist_ok=True)
    async with async_playwright() as pw:
        b = await pw.chromium.launch(executable_path="/usr/bin/chromium", args=["--no-sandbox"])
        ctx = await b.new_context(viewport={"width": W, "height": 844})
        await guards(ctx)
        page = await ctx.new_page()
        page.on("pageerror", lambda e: ERRORS.append(str(e)[:200]))
        await page.goto(BASE + "/", wait_until="domcontentloaded")
        await sign_in(page, width=W)

        # ---- A. My Tests exam tabs: filtering, red look, other tabs, no clipping.
        await page.goto(BASE + "/tests", wait_until="domcontentloaded")
        await visible(page, "my-tests-exam-filters", 45000)
        await page.wait_for_timeout(2500)
        tabs = page.locator(tid("my-tests-exam-filters") + ' [role="tab"]')
        n = await tabs.count()
        for i in range(n):
            await tabs.nth(i).click()
            await page.wait_for_timeout(2500)
            lab = (await tabs.nth(i).inner_text()).strip()
            sel = await tabs.nth(i).get_attribute("aria-selected")
            bg = await tabs.nth(i).evaluate("e => getComputedStyle(e).backgroundColor")
            other = await tabs.nth((i + 1) % n).evaluate("e => getComputedStyle(e).backgroundColor")
            exams = [t.strip() for t in await page.locator('[data-testid^="attempt-exam-"]').all_inner_texts()]
            empty = await page.locator(tid("my-tests-empty")).count()
            bad = [e for e in exams if i > 0 and lab.lower() not in e.lower()]
            check(f"exam tab '{lab}' selected+filters", sel == "true" and not bad, f"bg={bg} other={other} cards={Counter(exams)} empty={empty} bad={bad[:3]}")
        await tabs.nth(0).click()
        for t in ["progress", "saved", "completed"]:
            await page.click(tid(f"my-tests-tab-{t}"))
            await page.wait_for_timeout(2000)
            cards = await page.locator('[data-testid^="attempt-"], [data-testid^="saved-paper-"], [data-testid^="mock-card-"]').count()
            check(f"My Tests tab {t} renders", await page.locator(tid("my-tests-empty")).count() or cards > 0, f"elements={cards}")
        cl = await clipped(page, tid("my-tests-exam-filters"))
        check("exam tabs not clipped", not cl, cl)
        await page.screenshot(path=f"{SHOTS}/a_tests.png", quality=40, type="jpeg")

        # ---- B. New mock: cap 25, disabled counts on a small chapter, select-all toggle back.
        check("new mock opens", await open_new(page))
        opens = {s: await txt(page, f"mock-new-open-{s}") for s in ["physics", "chemistry", "mathematics"]}
        print("open pool:", opens)
        await page.click(tid("mock-subject-physics"))
        if int(opens["physics"] or 0) >= 25:
            await page.click(tid("mock-count-physics-25"))
            await page.wait_for_timeout(200)
            more_dis = await page.locator(tid("mock-count-more")).get_attribute("aria-disabled")
            check("25 cap: count 25 and + disabled", (await txt(page, "mock-count-value")).startswith("25") and more_dis == "true", await txt(page, "mock-count-time"))
            check("25 Physics = 60 min", "60" in (await txt(page, "mock-count-time")) or "1 h" in (await txt(page, "mock-count-time")), await txt(page, "mock-count-time"))
            await page.click(tid("mock-count-physics-0"))
        # Smallest chapter only
        best = None
        for subj in ["physics", "chemistry", "mathematics"]:
            await page.click(tid(f"mock-subject-{subj}")); await page.wait_for_timeout(300)
            nrows = await page.locator('[data-testid^="mock-chapter-"]').evaluate_all("els => els.filter(e => /^mock-chapter-\\d+$/.test(e.dataset.testid)).map(e => e.innerText)")
            sz = [int(re.findall(r"(\d+)\s*$", r.strip())[0]) if re.findall(r"(\d+)\s*$", r.strip()) else 99 for r in nrows]
            print(subj, "chapter sizes:", sz)
            if sz and (best is None or min(sz) < best[2][best[1]]):
                best = (subj, min(range(len(sz)), key=lambda i: sz[i]), sz)
        subj, small, sizes = best
        await page.click(tid(f"mock-subject-{subj}")); await page.wait_for_timeout(300)
        await page.click(tid("mock-chapter-all"))
        await page.click(tid(f"mock-chapter-{small}"))
        await page.wait_for_timeout(200)
        most = await txt(page, "mock-new-most")
        dis = {k: await page.locator(tid(f"mock-count-{subj}-{k}")).get_attribute("aria-disabled") for k in ["5", "10", "25"]}
        check("small chapter: Max = chapter size, larger counts disabled", most == f"Max {min(25, sizes[small])}" and dis["25"] == "true", f"{most} size={sizes[small]} dis={dis}")
        checked = await page.locator(tid(f"mock-chapter-{small}")).get_attribute("aria-checked")
        check("chapter row ticked (aria-checked)", checked == "true", checked)
        await page.click(tid("mock-chapter-all"))
        check("select all back on", await page.locator(tid("mock-chapter-all")).get_attribute("aria-checked") == "true")
        await page.screenshot(path=f"{SHOTS}/b_new.png", quality=40, type="jpeg")
        cl = await clipped(page, tid("mock-new-screen"))
        check("new mock screen labels not clipped", not cl, cl)

        # ---- C. Build from small chapter at max (short notice expected only if keys missing) then remove it.
        await page.click(tid("mock-chapter-all"))
        await page.click(tid(f"mock-chapter-{small}"))
        for _ in range(26):
            if await page.locator(tid("mock-count-more") + '[aria-disabled="true"]').count():
                break
            await page.click(tid("mock-count-more"))
        asked = await txt(page, "mock-count-value")
        print("asked from small chapter:", asked, "bar:", (await txt(page, "mock-new-bar")).replace("\n", " | "))
        await page.click(tid("mock-new-bar-go"))
        ok = await visible(page, "mock-ready-screen", 120000)
        check("small-chapter mock built", ok)
        if ok:
            size = await txt(page, "mock-ready-size")
            short = await page.locator(tid("mock-ready-short")).count()
            print("ready size:", size, "short notice:", short, "physics:", await txt(page, "mock-ready-physics"))
            got = int(re.findall(r"\d+", size)[0])
            check("short notice iff fewer than asked", (got < int(re.findall(r'\d+', asked)[0])) == bool(short), f"asked {asked} got {size} short={short}")
            url = page.url
            mid = url.split("/mock/")[1].split("?")[0]
            await page.click(tid("mock-remove"))
            await page.wait_for_timeout(400)
            check("remove asks once more first", "Pakka" in await txt(page, "mock-remove") and await page.locator(tid("mock-ready-screen")).count() == 1)
            await page.click(tid("mock-remove"))
            await page.wait_for_timeout(1500)
            await page.goto(BASE + "/misfire?tab=mock", wait_until="domcontentloaded")
            await visible(page, "misfire-tab-mock", 45000)
            await page.click(tid("misfire-tab-mock"))
            await page.wait_for_timeout(1500)
            check("removed mock gone from Misfire > Mock", await page.locator(tid(f"misfire-mock-{mid}")).count() == 0)
            await page.goto(BASE + f"/misfire/mock/{mid}", wait_until="domcontentloaded")
            await page.wait_for_timeout(4000)
            body = await page.inner_text("body")
            check("removed mock URL shows not-found state (no crash)", "mock-ready-screen" not in body, body[:120].replace("\n", " "))

        # ---- D. Right answers -> try+done once each; player controls; result.
        await open_new(page)
        ok, bar = await build(page, {"physics": 3, "chemistry": 3, "mathematics": 2}, "right-mock")
        await page.click(tid("mock-start"))
        await visible(page, "mock-player-screen", 15000)
        await page.screenshot(path=f"{SHOTS}/d_player.png", quality=40, type="jpeg")
        cl = await clipped(page, tid("mock-player-screen"))
        check("player labels not clipped", not cl, cl)
        # mark + clear on Q1
        if await page.locator(tid("mock-option-B")).count():
            await page.click(tid("mock-option-B"))
            await page.click(tid("mock-clear-button"))
            check("Clear removes answer", (await txt(page, "mock-count-answered")).startswith("0"), await txt(page, "mock-count-answered"))
        await page.click(tid("mock-mark-button"))
        check("Mark for review counted", (await txt(page, "mock-count-marked") or "").startswith("1"), await txt(page, "mock-count-marked"))
        await page.click(tid("mock-mark-button"))
        opt, num = await answer_all(page)
        print("answered option(A):", opt, "integer:", num)
        await page.click(tid("mock-palette-button"))
        check("palette sheet opens", await visible(page, "mock-palette-sheet", 5000))
        await page.screenshot(path=f"{SHOTS}/d_palette.png", quality=40, type="jpeg")
        await page.click(tid("mock-palette-close"))
        await page.wait_for_timeout(500)
        FAKED.clear()
        await page.click(tid("mock-submit-top"))
        await page.click(tid("mock-confirm-submit"))
        check("result screen", await visible(page, "mock-result-screen", 20000))
        await page.wait_for_timeout(6000)
        tries = [f for f in FAKED if f.startswith("try")]
        dones = [f for f in FAKED if f.startswith("done")]
        corr = await txt(page, "mock-result-correct")
        check("try+done once per right answer", len(tries) == len(dones) == opt and len(set(tries)) == len(tries), f"opt={opt} tries={len(tries)} dones={len(dones)} correct={corr}")
        moved = await txt(page, "mock-result-moved")
        check("understood card says N moved", moved is not None and str(opt) in moved, moved)
        await page.screenshot(path=f"{SHOTS}/d_result.png", quality=40, type="jpeg")
        # filters
        for f in ["correct", "incorrect", "skipped", "all"]:
            loc = page.locator(tid(f"mock-result-filter-{f}"))
            if await loc.count():
                await loc.click(); await page.wait_for_timeout(400)
                railn = await page.locator('[data-testid^="mock-result-q-"]').count()
                emp = await page.locator(tid("mock-result-filter-empty")).count()
                check(f"result filter {f}", await loc.get_attribute("aria-selected") == "true", f"rail={railn} empty={emp}")
            else:
                check(f"result filter {f} exists", False)
        cl = await clipped(page, '[data-testid^="mock-result-filter-"]')
        check("result filter tabs not clipped", not cl, cl)
        rail = page.locator('[data-testid^="mock-result-q-"]')
        if await rail.count() > 1:
            await rail.nth(1).click(); await page.wait_for_timeout(500)
        yours, key = await txt(page, "mock-solution-yours"), await txt(page, "mock-solution-key")
        check("solution card yours/key", yours is not None and key is not None, f"{yours} / {key}")
        print("solution text present:", await page.locator(tid("mock-solution-text")).count(), "simages:", await page.locator('[data-testid^="mock-solution-simage-"]').count())
        await page.locator(tid("mock-solution-card")).scroll_into_view_if_needed()
        await page.screenshot(path=f"{SHOTS}/d_solution.png", quality=40, type="jpeg")
        result_url = page.url
        await page.click(tid("mock-solution-paper"))
        await page.wait_for_timeout(2500)
        check("'Asli paper ka result' opens /result/<attempt>", "/result/" in page.url, page.url)
        await page.goto(result_url, wait_until="domcontentloaded")
        await visible(page, "mock-result-screen", 30000)
        await page.click(tid("mock-result-new"))
        check("'Naya mock banao' opens new", await visible(page, "mock-new-screen", 15000))

        # ---- E. Exam filter applies to mocks in My Tests > Completed.
        await page.goto(BASE + "/tests", wait_until="domcontentloaded")
        await visible(page, "my-tests-exam-filters", 45000)
        await page.click(tid("my-tests-tab-completed"))
        await page.wait_for_timeout(1500)
        mexam = [t for t in await page.locator('[data-testid^="mock-exam-"]').all_inner_texts()]
        print("mock exam labels:", mexam)
        for i in range(n):
            await tabs.nth(i).click(); await page.wait_for_timeout(1500)
            lab = (await tabs.nth(i).inner_text()).strip()
            cnt = await page.locator('[data-testid^="mock-score-"]').count()
            print(f"  tab {lab}: mocks shown {cnt}")
        await tabs.nth(0).click()

        # ---- F. Timer expiry: tiny mock, start, answer, leave; shift browser clock past deadline; open -> settled result.
        await open_new(page)
        ok, _ = await build(page, {"physics": 1}, "expiry-mock")
        mid = page.url.split("/mock/")[1].split("?")[0]
        await page.click(tid("mock-start"))
        await visible(page, "mock-player-screen", 15000)
        await answer_all(page)
        await page.click(tid("mock-exit-button")); await page.click(tid("mock-exit-confirm"))
        await page.wait_for_timeout(1500)
        await ctx.add_init_script("(() => { const off = 4*60*1000; const N = Date.now; Date.now = () => N() + off; const D = Date; class X extends D { constructor(...a){ if(!a.length){ super(N()+off);} else super(...a);} static now(){return N()+off;} } window.Date = X; })()")
        p2 = await ctx.new_page()
        p2.on("pageerror", lambda e: ERRORS.append(str(e)[:200]))
        await p2.goto(BASE + "/tests", wait_until="domcontentloaded")
        await visible(p2, "my-tests-exam-filters", 45000)
        await p2.click(tid("my-tests-tab-completed")); await p2.wait_for_timeout(2000)
        st = await txt(p2, f"mock-status-{mid}")
        check("expired mock moves to Completed", st is not None, st)
        await p2.goto(BASE + f"/misfire/mock/{mid}", wait_until="domcontentloaded")
        check("expired mock opens as result (settled)", await visible(p2, "mock-result-screen", 30000), await txt(p2, "mock-result-line"))
        await p2.screenshot(path=f"{SHOTS}/f_expired.png", quality=40, type="jpeg")
        await p2.close()

        # ---- G. Sign out clears mocks.
        await page.goto(BASE + "/account", wait_until="domcontentloaded")
        await visible(page, "account-signout-button", 45000)
        await page.click(tid("account-signout-button"))
        await page.wait_for_timeout(1500)
        if await page.locator(tid("signout-keep-drafts")).count():
            await page.click(tid("signout-keep-drafts"))
        for t in ["signout-confirm", "account-signout-confirm"]:
            if await page.locator(tid(t)).count():
                await page.click(tid(t))
        ok = await visible(page, "entry-phone-input", 30000)
        check("signed out", ok)
        if ok:
            await sign_in(page, width=W)
            await page.goto(BASE + "/misfire", wait_until="domcontentloaded")
            await visible(page, "misfire-tab-mock", 45000)
            await page.click(tid("misfire-tab-mock")); await page.wait_for_timeout(2500)
            check("mocks cleared after sign out", await page.locator('[data-testid^="misfire-mock-score-"]').count() == 0 and await page.locator(tid("misfire-mocks-empty")).count() == 1)
        await b.close()
    print("FAKED", FAKED)
    print("BLOCKED", BLOCKED)
    print("PAGEERRORS", ERRORS)
    print(f"{sum(1 for _, ok in RES if ok)}/{len(RES)} passed")

asyncio.run(main())
