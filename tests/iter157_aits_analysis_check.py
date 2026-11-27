# iter157: AITS analysis readiness from the server answer alone. READ ONLY for the QA learner.
# The browser answers GET /api/jl/attempts/<id>/analysis with each fixture; every non-GET under /api/jl (outside /auth) is stopped.
# usage: python3 iter157_aits_analysis_check.py [width]
import asyncio
import json
import re
import sys
import time

from dotenv import dotenv_values
from playwright.async_api import async_playwright

sys.path.insert(0, "/app/tests")
from shine_helpers import sign_in  # noqa: E402

BASE = dotenv_values("/app/frontend/.env")["EXPO_PUBLIC_BACKEND_URL"].rstrip("/")
AID = "c0061f81-7ae9-432b-8ca5-312c8d39d4b5"
FIX = ["real_unrated", "aits_full", "aits_partial", "aits_no_easy"]
BODIES = {f: open(f"/app/tests/fixtures/aits_analysis/{f}.json").read() for f in FIX}
SECTIONS = ["overview", "performance", "potential", "quality", "time", "difficulty", "journey", "qs"]
W = int(sys.argv[1]) if len(sys.argv) > 1 else 390
RES, BLOCKED, ERRORS, TIMES = [], [], [], {}
S = {"fx": None, "t": None, "hits": 0}


def check(name, ok, info=""):
    RES.append((name, bool(ok)))
    print(("PASS " if ok else "FAIL ") + name + (" :: " + str(info) if info else ""), flush=True)


def tid(t):
    return f'[data-testid="{t}"]'


async def guards(ctx):
    async def g(route):
        r = route.request
        if r.method in ("GET", "HEAD", "OPTIONS") or "/api/jl/auth" in r.url:
            await route.fallback(); return
        BLOCKED.append(r.method + " " + r.url.split("?")[0].replace(BASE, ""))
        await route.fulfill(status=418, content_type="application/json", body='{"data":null,"error":{"code":"blocked","message":"blocked by test"},"meta":{}}')
    await ctx.route(re.compile(r".*/api/jl/.*"), g)

    async def an(route):
        if route.request.method != "GET" or S["fx"] is None:
            await route.fallback(); return
        S["hits"] += 1
        S["t"] = time.perf_counter()
        await route.fulfill(status=200, content_type="application/json", body=BODIES[S["fx"]])
    await ctx.route(re.compile(r".*/api/jl/attempts/" + AID + r"/analysis.*"), an)


async def visible(page, t, timeout=8000):
    try:
        await page.wait_for_selector(tid(t), state="visible", timeout=timeout); return True
    except Exception:
        return False


async def drill_count(page):
    if not await visible(page, "a2-drill-title", 4000):
        return None
    txt = await page.inner_text(tid("a2-drill-title"))
    rows = await page.locator('[data-testid^="a2-drill-q-"]').count()
    await page.click(tid("a2-drill-backdrop"), force=True, position={"x": 20, "y": 10})
    try:  # make sure the sheet is gone before the next tap (a tap on a drill row would open a solution)
        await page.wait_for_selector(tid("a2-drill-title"), state="hidden", timeout=4000)
    except Exception:
        print("WARN drill sheet still open; url", page.url, flush=True)
    await page.wait_for_timeout(150)
    return int(re.match(r"(\d+)", txt).group(1)), rows


TOASTS = []


async def no_toast(page):
    # Expo dev LogBox toast (#error-toast, dev builds only) sits over the bottom bar after any console.error; let taps through.
    n = await page.evaluate("() => { const t = document.querySelectorAll('#error-toast'); t.forEach(e => e.style.pointerEvents = 'none'); return t.length; }")
    if n:
        TOASTS.append(n)


async def nav(page, k):
    await no_toast(page)
    await page.wait_for_timeout(350)  # the bar scrolls to the open pill (animated); a tap mid-scroll hits the neighbour
    t0 = time.perf_counter()
    try:
        await page.click(tid("a2-nav-" + k), timeout=3000)
    except Exception:
        await page.click(tid("a2-nav-" + k), force=True)
    ok = await visible(page, "a2-section-" + k)
    dt = (time.perf_counter() - t0) * 1000
    return ok, dt


async def no_red(page, label):
    err = await page.locator(tid("a2-error")).count()
    body = await page.inner_text("body")
    bad = any(s in body for s in ("Something went wrong", "TypeError", "is not a function", "Cannot read prop"))
    check(f"{label}: no a2-error / red error", err == 0 and not bad)


async def cell_checks(page, fx):
    # iter158: every level cell (All subjects) drill count == its number; 0 => disabled
    bad = []
    for l in ("easy", "moderate", "tough", "unrated"):
        for o in ("correct", "incorrect", "skipped"):
            cell = page.locator(tid(f"a2-difficulty-{l}-{o}"))
            if not await cell.count():
                continue
            num = int(re.match(r"(\d+)", (await cell.inner_text()).strip()).group(1))
            dis = (await cell.get_attribute("aria-disabled")) == "true"
            if num == 0:
                if not dis: bad.append((l, o, 0, "enabled"))
                continue
            if dis:
                bad.append((l, o, num, "DISABLED")); continue
            await cell.click(force=True)
            dc = await drill_count(page)
            if not (dc and dc[0] == num == dc[1]):
                bad.append((l, o, num, dc))
    check(f"{fx}: every difficulty cell == drill count", not bad, bad)


async def difficulty_checks(page, fx):
    sec = page.locator(tid("a2-section-difficulty"))
    leak = await page.locator(tid("a2-leak")).count()
    rows_txt = await page.inner_text(tid("a2-difficulty-table"))
    note = await sec.inner_text()
    has = {l: (l in rows_txt) for l in ("Easy", "Moderate", "Tough", "Not rated")}
    if fx == "real_unrated":
        check("unrated: no a2-leak", leak == 0)
        check("unrated: only Not rated row", has == {"Easy": False, "Moderate": False, "Tough": False, "Not rated": True}, has)
        check("unrated: note not empty-list", "Level kahan se aaya: ." not in note)
    elif fx == "aits_full":
        check("full: a2-leak shown", leak == 1)
        lt = await page.inner_text(tid("a2-leak"))
        check("full: leak text", re.search(r"\d+ Easy galat aur \d+ Easy chhoote", lt), lt[:120])
        await page.click(tid("a2-leak-questions"), force=True)
        n = re.search(r"(\d+) sawaal dekho", lt)
        dc = await drill_count(page)
        check("full: leak drill count", dc and n and dc[0] == int(n.group(1)) == dc[1], (dc, n and n.group(1)))
        counts = re.findall(r"\((\d+) sawaal\)", rows_txt)
        check("full: Easy/Moderate/Tough 25/25/25", has["Easy"] and has["Moderate"] and has["Tough"] and not has["Not rated"] and counts == ["25", "25", "25"], counts)
        check("full: chart drawn", await page.locator(tid("a2-difficulty-chart")).count() == 1)
        ts = len(FXD[fx]["difficulty"].get("tough_solved") or [])
        check(f"full: tough solved block shown only if tough_solved ({ts})", await page.locator(tid("a2-block-tough-solved")).count() == (1 if ts else 0))
        before = rows_txt
        await page.click(tid("a2-pill-difficulty-subject-physics"), force=True)
        await page.wait_for_timeout(400)
        after = await page.inner_text(tid("a2-difficulty-table"))
        check("full: Physics pill switches table", after != before, re.findall(r"\((\d+) sawaal\)", after))
        await page.click(tid("a2-pill-difficulty-subject-all"), force=True)
    elif fx == "aits_partial":
        check("partial: 4 rows incl Not rated", all(has.values()), has)
        check("partial: unlock foot", await page.locator(tid("a2-difficulty-unlock")).count() == 1)
        await page.click(tid("a2-pill-difficulty-subject-chemistry"), force=True)
        await page.wait_for_timeout(400)
        ct = await page.inner_text(tid("a2-difficulty-table"))
        check("partial: Chemistry no Easy row", "Easy" not in ct and "Moderate" in ct, ct[:80].replace("\n", " "))
        await page.click(tid("a2-pill-difficulty-subject-all"), force=True)
    elif fx == "aits_no_easy":
        check("no_easy: no a2-leak", leak == 0)
        check("no_easy: Moderate+Tough rows", has["Moderate"] and has["Tough"] and not has["Easy"], has)


GENERIC = re.compile(r"previous-year paper|uncategorised", re.I)
FXD = {f: json.loads(BODIES[f])["data"] for f in FIX}
LONG = "Electromagnetic Induction and Alternating Currents with LC Oscillations"


async def overflow(page, sel):
    # any text node box wider than its parent box or past the screen edge
    return await page.evaluate("""(sel) => { const r = document.querySelector(sel); if (!r) return 'missing';
      const bad = []; for (const el of r.querySelectorAll('*')) { const b = el.getBoundingClientRect();
        if (b.right > window.innerWidth + 1 || el.scrollWidth > el.clientWidth + 2 && getComputedStyle(el).overflow !== 'visible') bad.push(el.textContent.slice(0, 40)); }
      return bad.slice(0, 3); }""", sel)


async def performance_checks(page, fx):
    # iter158: generic chapter names are hidden; real chapter names (9 per subject) listed with drills
    nochap = await page.locator(tid("a2-no-chapters")).count()
    if fx == "real_unrated":
        check("unrated: a2-no-chapters SHOWN", nochap == 1)
        txt = await page.inner_text(tid("a2-section-performance"))
        check("unrated: no 'Previous-year paper' anywhere in Performance (all)", not GENERIC.search(txt))
        for sub in ("physics", "chemistry", "mathematics"):
            await page.click(tid("a2-pill-perf-subject-" + sub), force=True); await page.wait_for_timeout(350)
            t = await page.inner_text(tid("a2-section-performance"))
            n = await page.locator('[data-testid^="a2-chapter-row-"], [data-testid^="a2-weak-"]').count()
            check(f"unrated {sub}: no chapter/weak rows, no generic name, no-chapters shown", n == 0 and not GENERIC.search(t) and await page.locator(tid("a2-no-chapters")).count() == 1, n)
        await page.click(tid("a2-pill-perf-subject-all"), force=True); await page.wait_for_timeout(300)
        return
    check(f"{fx}: a2-no-chapters absent", nochap == 0)
    check(f"{fx}: a2-weak-chapters shown", await page.locator(tid("a2-weak-chapters")).count() == 1)
    wrows = page.locator('[data-testid="a2-weak-chapters"] > [data-testid^="a2-weak-"]')
    if not await wrows.count():
        wrows = page.locator('[data-testid^="a2-weak-"]:not([data-testid="a2-weak-chapters"])')
    wn = await wrows.count()
    check(f"{fx}: weak rows 1..7", 1 <= wn <= 7, wn)
    for i in range(wn):
        r = wrows.nth(i); t = await r.inner_text()
        m = re.search(r"(\d+) galat, (\d+) chhode", t)
        await r.click(force=True)
        dc = await drill_count(page)
        check(f"{fx}: weak row {i} drill opens ({t.split(chr(10))[0][:30]})", dc and dc[0] == dc[1] > 0 and (not m or dc[0] == int(m.group(1)) + int(m.group(2))), (dc, m and m.groups()))
    for sub, name in (("physics", "Physics"), ("chemistry", "Chemistry"), ("mathematics", "Mathematics")):
        await page.click(tid("a2-pill-perf-subject-" + sub), force=True)
        ok = await visible(page, "a2-chapter-table", 4000)
        want = [c for c in next(s for s in FXD[fx]["performance"]["subjects"] if s["name"] == name)["chapters"]]
        rows = page.locator('[data-testid^="a2-chapter-row-"]')
        n = await rows.count()
        check(f"{fx} {sub}: chapter table {n} rows (want {len(want)}=9)", ok and n == len(want) == 9, n)
        if sub == "physics" and fx == "aits_full":
            body = await page.inner_text(tid("a2-chapter-table"))
            check(f"{fx}: long Physics name shown in full", LONG in body)
            ov = await overflow(page, tid("a2-chapter-table"))
            check(f"{fx} @{W}: chapter table no overflow", ov == [], ov)
        tag_bad, drill_bad = [], []
        for i in range(n):
            r = rows.nth(i); t = await r.inner_text()
            first = t.split("\n")[0]
            cnt = int(re.search(r"(\d+) sawaal", t).group(1))
            exp = want[i]
            if first.strip() != exp["name"] or cnt != exp["count"]:
                drill_bad.append(("name/count", first[:30], cnt, exp["name"][:30], exp["count"]))
            has_tag = bool(re.search(r"\b(Mazboot|Theek|Kamzor)\b", t))
            if has_tag != (cnt >= 3):
                tag_bad.append((first[:25], cnt, has_tag))
            await r.click(force=True)
            dc = await drill_count(page)
            if not (dc and dc[0] == cnt == dc[1]):
                drill_bad.append((first[:25], cnt, dc))
        check(f"{fx} {sub}: tags only for >=3 questions", not tag_bad, tag_bad)
        check(f"{fx} {sub}: every chapter row drill == N sawaal", not drill_bad, drill_bad[:3])
    await page.click(tid("a2-pill-perf-subject-all"), force=True)
    await page.wait_for_timeout(300)


async def qs_checks(page, fx):
    c1 = await page.inner_text(tid("a2-qs-card-1"))
    if fx == "real_unrated":
        check("unrated: card shows subject · — or Not rated", re.search(r"· (—|Not rated)", c1), c1.split("\n")[1:3])
    else:
        check(f"{fx}: card shows level", re.search(r"(Physics|Chemistry|Mathematics) · (Easy|Moderate|Tough|Not rated)", c1), c1.split("\n")[1:3])
    cards = page.locator('[data-testid^="a2-qs-card-"]')
    pages = 0
    while await page.locator(tid("a2-qs-more")).count() and pages < 5:
        await page.click(tid("a2-qs-more"), force=True); pages += 1; await page.wait_for_timeout(300)
    check(f"{fx}: qs paging to 75", await cards.count() == 75 and pages == 2, (await cards.count(), pages))
    names = {c["name"] for s in FXD[fx]["performance"]["subjects"] for c in s["chapters"]}
    bad = []
    for q in FXD[fx]["questions"]:
        t = await page.inner_text(tid(f"a2-qs-card-{q['number']}"))
        lines = [l.strip() for l in t.split("\n")]
        topic = (q["topic"] or "").strip()
        shown = [l for l in lines if l in names or GENERIC.fullmatch(l)]
        if GENERIC.fullmatch(topic) or not topic:
            if shown: bad.append((q["number"], "unexpected", shown))
        elif topic not in lines: bad.append((q["number"], "missing", topic[:30]))
    check(f"{fx}: Qs card chapter lines (none for generic/untagged)", not bad, bad[:4])
    await page.click(tid("a2-pill-qs-filter-wrong"), force=True)
    await page.wait_for_timeout(300)
    wl = await page.inner_text(tid("a2-pill-qs-filter-wrong"))
    want = int(re.search(r"\((\d+)\)", wl).group(1))
    check(f"{fx}: wrong filter count", await cards.count() == want, (await cards.count(), want))
    await page.click(tid("a2-pill-qs-filter-all"), force=True)
    await page.click(tid("a2-qs-sort"), force=True)
    ok = await visible(page, "a2-qs-sort-sheet", 3000)
    await page.wait_for_timeout(600)  # sheet slides in
    await page.click(tid("a2-qs-sort-time"), force=True)
    await page.wait_for_timeout(400)
    check(f"{fx}: sort sheet works", ok and "Sabse zyada time" in await page.inner_text(tid("a2-qs-sort")))


async def run_fixture(page, fx):
    S["fx"], S["t"] = fx, None
    await page.goto(f"{BASE}/result/{AID}", wait_until="domcontentloaded")
    anysec = ", ".join(tid("a2-section-" + k) for k in SECTIONS)
    await page.wait_for_selector(anysec, state="visible", timeout=45000)
    t_vis = time.perf_counter()
    first = (t_vis - S["t"]) * 1000 if S["t"] else None
    opened = await page.locator(anysec).first.get_attribute("data-testid")
    print("opened at", opened, flush=True)
    if opened != "a2-section-overview":
        ok, _ = await nav(page, "overview")
    ok = await visible(page, "a2-section-overview", 5000)
    check(f"{fx}: overview visible (answer→overview {first and round(first)} ms)", ok and S["hits"] > 0)
    TIMES[fx] = {"answer_to_overview_ms": first and round(first)}
    await no_red(page, fx + " overview")
    for k in SECTIONS[1:] + ["overview"]:
        ok, dt = await nav(page, k)
        TIMES[fx][k] = round(dt)
        txt = (await page.inner_text(tid("a2-section-" + k))) if ok else ""
        check(f"{fx}: section {k} ({round(dt)} ms)", ok and len(txt) > 40, len(txt))
        if k == "difficulty":
            await difficulty_checks(page, fx)
            await cell_checks(page, fx)
        if k == "performance":
            await performance_checks(page, fx)
        if k == "qs":
            await qs_checks(page, fx)
        await no_red(page, f"{fx} {k}")
    await page.screenshot(path=f"/tmp/shots/i157_{fx}_{W}.jpg", type="jpeg", quality=20)


async def main():
    import os
    os.makedirs("/tmp/shots", exist_ok=True)
    async with async_playwright() as pw:
        b = await pw.chromium.launch(executable_path="/usr/bin/chromium", args=["--no-sandbox"])
        ctx = await b.new_context(viewport={"width": W, "height": 844})
        await guards(ctx)
        page = await ctx.new_page()
        page.on("pageerror", lambda e: ERRORS.append(str(e)[:200]))
        await page.goto(BASE + "/", wait_until="domcontentloaded")
        await sign_in(page, width=W)
        print("signed in", flush=True)
        for fx in FIX:
            try:
                await run_fixture(page, fx)
            except Exception as e:
                check(f"{fx}: run without exception", False, repr(e)[:300] + " url=" + page.url)
                await page.screenshot(path=f"/tmp/shots/i157_err_{fx}_{W}.jpg", type="jpeg", quality=20)
        # Regression: real (not intercepted) analysis + result tabs
        S["fx"], S["hits"] = None, 0
        await page.goto(f"{BASE}/result/{AID}", wait_until="domcontentloaded")
        ok = await visible(page, "a2-bottom-bar", 45000)
        if ok and not await page.locator(tid("a2-section-overview")).count():
            ok, _ = await nav(page, "overview")
        check("real: analysis opens (not intercepted)", ok and S["hits"] == 0)
        if ok:
            ok2, _ = await nav(page, "difficulty")
            t = await page.inner_text(tid("a2-difficulty-table")) if ok2 else ""
            check("real: all Not rated", ok2 and "Not rated" in t and "Easy" not in t, t[:60].replace("\n", " "))
        for tab in ("progress", "confidence", "rank", "analysis"):
            n = await page.locator(tid("result-tab-" + tab)).count()
            if n:
                await page.click(tid("result-tab-" + tab), force=True); await page.wait_for_timeout(1500)
                await no_red(page, "tab " + tab)
            check(f"result-tab-{tab} present+tapped", n == 1)
        await b.close()
    print("TIMES", json.dumps(TIMES))
    print("DEV LOGBOX TOAST seen (navs):", len(TOASTS))
    print("BLOCKED", BLOCKED)
    print("PAGEERRORS", ERRORS[:10])
    print(f"RESULT {sum(ok for _, ok in RES)}/{len(RES)} passed")


if __name__ == "__main__":
    asyncio.run(main())
