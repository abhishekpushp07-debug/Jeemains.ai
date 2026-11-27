# iter158: ErrorBox Retry hitSlop — a tap a few px OUTSIDE the visible "Retry" text still retries (new GET).
# READ ONLY for the QA learner; analysis GET answered in the browser only. usage: python3 iter158_retry_hitslop_check.py [width]
import asyncio
import json
import sys

sys.path.insert(0, "/app/tests")
import iter157_aits_analysis_check as M  # noqa: E402
from playwright.async_api import async_playwright  # noqa: E402

W = int(sys.argv[1]) if len(sys.argv) > 1 else 390
base = json.loads(M.BODIES["aits_full"])
b2 = json.loads(json.dumps(base)); b2["data"]["difficulty"] = None
M.BODIES["broken"] = json.dumps(b2)
tid = M.tid
# (label, dx from the visible text's edge, dy) points outside the word "Retry" but inside the button's padding
POINTS = [("center", "center", 0), ("right+10", "right", 10), ("bottom+8", "bottom", 8), ("top-8", "top", -8), ("left-5", "left", -5)]


async def open_broken(page):
    M.S["fx"] = "broken"
    await page.goto(f"{M.BASE}/result/{M.AID}", wait_until="domcontentloaded")
    anysec = ", ".join(tid("a2-section-" + s) for s in M.SECTIONS)
    await page.wait_for_selector(anysec, state="visible", timeout=45000)
    if not await page.locator(tid("a2-section-difficulty")).count():
        await M.nav(page, "difficulty")
    return await M.visible(page, "a2-section-error-retry", 8000)


async def main():
    async with async_playwright() as pw:
        b = await pw.chromium.launch(executable_path="/usr/bin/chromium", args=["--no-sandbox"])
        ctx = await b.new_context(viewport={"width": W, "height": 844})
        await M.guards(ctx)
        page = await ctx.new_page()
        page.on("pageerror", lambda e: M.ERRORS.append(str(e)[:160]))
        await page.goto(M.BASE + "/", wait_until="domcontentloaded")
        await M.sign_in(page, width=W)
        for label, edge, d in POINTS:
            try:
                ok = await open_broken(page)
                note = page.locator(tid("a2-section-error"))
                txt = await note.inner_text()
                # Measure from the visible word "Retry" (the button itself now carries the padding that makes it 44 px tall).
                bx = await page.locator(tid("a2-section-error-retry")).get_by_text("Retry", exact=True).bounding_box()
                full = await page.locator(tid("a2-section-error-retry")).bounding_box()
                print("BUTTON", round(full["width"]), "x", round(full["height"]), "TEXT", round(bx["width"]), "x", round(bx["height"]))
                nb = await note.bounding_box()
                if edge == "right": x, y = bx["x"] + bx["width"] + d, bx["y"] + bx["height"] / 2
                elif edge == "left": x, y = bx["x"] + d, bx["y"] + bx["height"] / 2
                elif edge == "bottom": x, y = bx["x"] + bx["width"] / 2, bx["y"] + bx["height"] + d
                elif edge == "center": x, y = bx["x"] + bx["width"] / 2, bx["y"] + bx["height"] / 2
                else: x, y = bx["x"] + bx["width"] / 2, bx["y"] + d
                M.S["fx"] = "aits_full"; h0 = M.S["hits"]
                await M.no_toast(page)
                await page.mouse.click(x, y)
                await page.wait_for_timeout(2500)
                drawn = await page.locator(tid("a2-difficulty-table")).count()
                err = await page.locator(tid("a2-section-error")).count()
                M.check(f"{label}: tap outside text ({round(x)},{round(y)}) box={round(bx['width'])}x{round(bx['height'])} retries",
                        ok and M.S["hits"] > h0 and drawn == 1 and err == 0,
                        (ok, M.S["hits"] - h0, drawn, err, txt[:80].replace("\n", " | "), nb and round(nb["height"])))
            except Exception as e:
                M.check(f"{label}: no exception", False, repr(e)[:200])
        # control: a tap far away (inside the note, 60px left of Retry's text start... only if room) must NOT retry
        ok = await open_broken(page)
        nb = await page.locator(tid("a2-section-error")).bounding_box()
        bx = await page.locator(tid("a2-section-error-retry")).bounding_box()
        M.S["fx"] = "aits_full"; h0 = M.S["hits"]
        await page.mouse.click(bx["x"] + bx["width"] + 60, bx["y"] + bx["height"] / 2)
        await page.wait_for_timeout(1500)
        M.check("control: tap 60px right of Retry does not retry", M.S["hits"] == h0 and await page.locator(tid("a2-section-error")).count() == 1, M.S["hits"] - h0)
        dom = await page.evaluate("""() => { const e = document.querySelector('[data-testid="a2-section-error-retry"]'); return e ? e.outerHTML.slice(0, 400) + ' || parent pad: ' + getComputedStyle(e).padding : null; }""")
        print("RETRY DOM", dom)
        await page.screenshot(path=f"/tmp/shots/i158_hitslop_{W}.jpg", type="jpeg", quality=30)
        await b.close()
    print("BLOCKED", M.BLOCKED)
    print("PAGEERRORS", M.ERRORS[:5])
    print(f"RESULT {sum(ok for _, ok in M.RES)}/{len(M.RES)} passed")


if __name__ == "__main__":
    asyncio.run(main())
