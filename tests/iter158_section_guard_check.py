# iter158: FIX 1 crash containment (SectionGuard). READ ONLY for the QA learner; analysis GET answered in the browser only.
# usage: cd /app/tests && python3 iter158_section_guard_check.py [width]
import asyncio
import json
import sys

sys.path.insert(0, "/app/tests")
import iter157_aits_analysis_check as M  # noqa: E402
from playwright.async_api import async_playwright  # noqa: E402

W = int(sys.argv[1]) if len(sys.argv) > 1 else 390
base = json.loads(M.BODIES["aits_full"])
CONSOLE = []


def variant(fn):
    b = json.loads(json.dumps(base)); fn(b["data"]); return json.dumps(b)


def bump(d):
    d["server_now"] = d["server_now"] + 1000


V = {
    "leak_null": lambda d: d["difficulty"].update(leak=None),
    "no_by_subject": lambda d: d["difficulty"].pop("by_subject"),
    "no_tough_solved": lambda d: d["difficulty"].pop("tough_solved"),
    "difficulty_null": lambda d: d.update(difficulty=None),
}
for k, fn in V.items():
    M.BODIES[k] = variant(fn)
M.BODIES["healthy_same_now"] = M.BODIES["aits_full"]
M.BODIES["healthy_new_now"] = variant(bump)
OTHERS = [s for s in M.SECTIONS if s != "difficulty"]
check, tid = M.check, M.tid


async def fallback(page):
    return await page.locator(tid("error-fallback")).count()


async def guard_state(page, label):
    sec = await M.visible(page, "a2-section-difficulty", 8000)
    err = await page.locator(f'{tid("a2-section-difficulty")} {tid("a2-section-error")}').count()
    retry = await page.locator(tid("a2-section-error-retry")).count()
    txt = await page.inner_text(tid("a2-section-error")) if err else ""
    bar = await page.locator(tid("a2-bottom-bar")).is_visible() if await page.locator(tid("a2-bottom-bar")).count() else False
    fb = await fallback(page)
    if retry:
        bx = await page.locator(tid("a2-section-error-retry")).bounding_box()
        print(f"  retry touch target {W}px: {round(bx['width'])}x{round(bx['height'])}", flush=True)
    check(f"{label}: guard note in Difficulty + retry, bar visible, no error-fallback",
          sec and err == 1 and retry == 1 and "Yeh hissa abhi nahi khul paaya" in txt and bar and fb == 0, (sec, err, retry, bar, fb, txt[:60]))


async def run(page, k):
    M.S["fx"], M.S["hits"] = k, 0
    await page.goto(f"{M.BASE}/result/{M.AID}", wait_until="domcontentloaded")
    anysec = ", ".join(tid("a2-section-" + s) for s in M.SECTIONS)
    await page.wait_for_selector(anysec, state="visible", timeout=45000)
    if not await page.locator(tid("a2-section-difficulty")).count():
        await M.nav(page, "difficulty")
    await guard_state(page, k)
    # pager still works from inside the broken section
    await M.no_toast(page)
    await page.click(tid("a2-next-section"), force=True)
    nxt = await M.visible(page, "a2-section-journey", 4000)
    await page.click(tid("a2-prev-section"), force=True)
    back = await M.visible(page, "a2-section-difficulty", 4000)
    check(f"{k}: pager next->journey and prev->difficulty", nxt and back)
    bad = []
    for s in OTHERS:
        ok, _ = await M.nav(page, s)
        t = await page.inner_text(tid("a2-section-" + s)) if ok else ""
        if not ok or len(t) < 40 or await page.locator(tid("a2-section-error")).count():
            bad.append(s)
    check(f"{k}: other 7 sections draw", not bad and await fallback(page) == 0, bad)
    tabs = []
    for tab in ("progress", "confidence", "rank", "analysis"):
        if await page.locator(tid("result-tab-" + tab)).count():
            await page.click(tid("result-tab-" + tab), force=True); await page.wait_for_timeout(1200)
            tabs.append(tab if await fallback(page) == 0 else tab + ":FALLBACK")
    check(f"{k}: result tabs work", len(tabs) == 4 and all(":" not in t for t in tabs), tabs)
    await M.nav(page, "difficulty")
    # reopen: last section remembered = difficulty
    await page.goto(f"{M.BASE}/result/{M.AID}", wait_until="domcontentloaded")
    await page.wait_for_selector(anysec, state="visible", timeout=45000)
    opened = await page.locator(anysec).first.get_attribute("data-testid")
    check(f"{k}: reopen remembers difficulty", opened == "a2-section-difficulty", opened)
    await guard_state(page, k + " reopened")


async def retry_flow(page, k, healthy):
    M.S["fx"] = healthy
    h0 = M.S["hits"]
    await M.no_toast(page)
    await page.click(tid("a2-section-error-retry"), force=True)
    await page.wait_for_timeout(2500)
    drawn = await page.locator(tid("a2-difficulty-table")).count()
    err = await page.locator(tid("a2-section-error")).count()
    check(f"{k}: retry -> {healthy}: new GET made", M.S["hits"] > h0, M.S["hits"] - h0)
    check(f"{k}: retry -> {healthy}: section draws", drawn == 1 and err == 0 and await fallback(page) == 0, (drawn, err))
    return drawn == 1


async def main():
    async with async_playwright() as pw:
        b = await pw.chromium.launch(executable_path="/usr/bin/chromium", args=["--no-sandbox"])
        ctx = await b.new_context(viewport={"width": W, "height": 844})
        await M.guards(ctx)
        page = await ctx.new_page()
        page.on("pageerror", lambda e: M.ERRORS.append(str(e)[:160]))
        page.on("console", lambda m: CONSOLE.append(m.text[:120]) if "[analysis]" in m.text else None)
        await page.goto(M.BASE + "/", wait_until="domcontentloaded")
        await M.sign_in(page, width=W)
        for k in V:
            try:
                await run(page, k)
                if k == "leak_null":
                    if not await retry_flow(page, k, "healthy_same_now"):
                        await retry_flow(page, k + " (2nd)", "healthy_new_now")
                else:
                    await retry_flow(page, k, "healthy_new_now")
            except Exception as e:
                check(f"{k}: run without exception", False, repr(e)[:200])
                await page.screenshot(path=f"/tmp/shots/i158_guard_err_{k}.jpg", type="jpeg", quality=20)
        # screenshot of the guard note
        M.S["fx"] = "difficulty_null"
        await page.goto(f"{M.BASE}/result/{M.AID}", wait_until="domcontentloaded")
        await M.visible(page, "a2-section-error", 45000)
        await page.screenshot(path=f"/tmp/shots/i158_guard_{W}.jpg", type="jpeg", quality=30)
        await b.close()
    print("CONSOLE[analysis]", len(CONSOLE), CONSOLE[:2])
    print("BLOCKED", M.BLOCKED)
    print("PAGEERRORS", M.ERRORS[:5])
    print(f"RESULT {sum(ok for _, ok in M.RES)}/{len(M.RES)} passed")


if __name__ == "__main__":
    asyncio.run(main())
