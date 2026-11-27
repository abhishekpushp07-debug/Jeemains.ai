# iter159: sign-in screen ErrorBox (entry-session-error) layout + Retry hit area after hitSlop -> padding change.
# READ ONLY: /auth/session answered 403 in the browser only; all non-GET under /api/jl blocked. usage: python3 iter159_entry_errorbox_check.py [width]
import asyncio
import sys

from dotenv import dotenv_values
from playwright.async_api import async_playwright

BASE = dotenv_values("/app/frontend/.env")["EXPO_PUBLIC_BACKEND_URL"].rstrip("/")
W = int(sys.argv[1]) if len(sys.argv) > 1 else 390
RES, BLOCKED, CALLS = [], [], {"n": 0}

JS = """() => {
  const b = document.querySelector('[data-testid="entry-session-error-retry"]');
  const box = document.querySelector('[data-testid="entry-session-error"]');
  const texts = box.querySelectorAll('div[dir="auto"]');
  const r = e => { const x = e.getBoundingClientRect(); return [Math.round(x.left), Math.round(x.top), Math.round(x.width), Math.round(x.height)]; };
  const nxt = box.parentElement && box.nextElementSibling ? r(box.nextElementSibling) : null;
  return {btn: r(b), word: r(b.querySelector('div[dir="auto"]')), msg: r(texts[0]), box: r(box), next: nxt,
          overflow: getComputedStyle(box).overflow, text: box.innerText};
}"""


def check(name, ok, info=""):
    RES.append(ok); print(("PASS " if ok else "FAIL ") + name + (f" :: {info}" if info != "" else ""))


async def main():
    async with async_playwright() as pw:
        b = await pw.chromium.launch(executable_path="/usr/bin/chromium", args=["--no-sandbox"])
        ctx = await b.new_context(viewport={"width": W, "height": 844})

        async def guard(route):
            r = route.request
            if r.method in ("GET", "HEAD", "OPTIONS"):
                await route.fallback(); return
            BLOCKED.append(r.method + " " + r.url); await route.abort()

        async def session(route):
            CALLS["n"] += 1
            await route.fulfill(status=403, content_type="application/json", body='{"data":null,"error":{"code":"forbidden","message":"test"},"meta":{}}')

        await ctx.route("**/api/jl/**", guard)
        await ctx.route("**/api/jl/auth/session*", session)  # registered last -> runs first
        page = await ctx.new_page()
        await page.goto(BASE + "/", wait_until="domcontentloaded")
        try:
            await page.wait_for_selector('[data-testid="entry-session-error-retry"]', state="visible", timeout=60000)
        except Exception as e:
            check("entry ErrorBox shows", False, str(e)[:120]); await page.screenshot(path="/tmp/iter159_entry_fail.png"); return
        await page.wait_for_timeout(800)
        i = await page.evaluate(JS)
        print("INFO", i)
        bx, wd, mg, nb = i["btn"], i["word"], i["msg"], i["box"]
        check("Couldn't check your session text", "Couldn't check your session" in i["text"], i["text"][:90])
        check("Retry word below message (no overlap)", wd[1] >= mg[1] + mg[3] - 1, (mg, wd))
        check("Retry word fully inside Notice (no clipping)", wd[0] >= nb[0] and wd[1] + wd[3] <= nb[1] + nb[3] and wd[0] + wd[2] <= nb[0] + nb[2], (nb, wd))
        check("Retry word left-aligned with message", abs(wd[0] - mg[0]) <= 1, (mg[0], wd[0]))
        check("button >= 44 tall", bx[3] >= 44, bx)
        check("Notice height sane (< 140px)", nb[3] < 140, nb)
        if i["next"]:
            check("next sibling not overlapped by Notice", i["next"][1] >= nb[1] + nb[3] - 1, (nb, i["next"]))
        el = await page.query_selector('[data-testid="entry-session-error"]')
        await el.screenshot(path=f"/tmp/iter159_entry_errorbox_{W}.png")
        await page.screenshot(path=f"/tmp/iter159_entry_{W}.png")
        for label, x, y in [("below+8", wd[0] + wd[2] / 2, wd[1] + wd[3] + 8), ("right+10", wd[0] + wd[2] + 10, wd[1] + wd[3] / 2)]:
            before = CALLS["n"]
            await page.mouse.click(x, y)
            await page.wait_for_timeout(1500)
            check(f"tap {label} of word retries session", CALLS["n"] > before, (before, CALLS["n"]))
            await page.wait_for_selector('[data-testid="entry-session-error-retry"]', state="visible", timeout=10000)
            wd = (await page.evaluate(JS))["word"]
        before = CALLS["n"]
        await page.mouse.click(wd[0] + wd[2] + 60, wd[1] + wd[3] / 2)
        await page.wait_for_timeout(1500)
        check("control: tap 60px right does not retry", CALLS["n"] == before, (before, CALLS["n"]))
        await b.close()
    print("BLOCKED", BLOCKED)
    print(f"RESULT {sum(RES)}/{len(RES)} passed")

asyncio.run(main())
