# Iteration 156: the browser copy's "PLAY IN THE APP" card at the end of a finished match result (and the daily result),
# per phone (desktop / iPhone / Android user agents), the store link, an iOS store from switches, and its absence in the app.
# Read-only for the QA learner: the finished duel is answered by the browser; every Rapid Fire / website write is stopped.
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
PLAY = "https://play.google.com/store/apps/details?id=com.emergent.jeelivemobile.kt2g15"
DID = "TEST-duel-getapp-156"
IPHONE_UA = "Mozilla/5.0 (iPhone; CPU iPhone OS 17_5 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.5 Mobile/15E148 Safari/604.1"
ANDROID_UA = "Mozilla/5.0 (Linux; Android 14; Pixel 8) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Mobile Safari/537.36"
RES, BLOCKED = [], []


def check(name, ok, info=""):
    RES.append((name, bool(ok)))
    print(("PASS " if ok else "FAIL ") + name + (f"  [{info}]" if info != "" else ""))


def duel():
    now = time.time()
    cards = [{"id": f"TEST-c{i}", "chapter": "Kinematics", "subject": "physics", "prompt": f"TEST card {i}: speed?", "options": ["1 m/s", "2 m/s", "3 m/s", "4 m/s"], "answer": 1, "explain": "v = d/t"} for i in range(5)]
    return {"id": DID, "status": "finished", "mode": "friend", "exam": "JEE", "subject": "physics", "chapter": "kinematics",
            "picks": [{"subject": "physics", "chapter": "kinematics"}], "you": "TEST-me", "winner": "TEST-friend", "server_now": now,
            "finished_at": "2026-11-28T10:00:00Z", "cards": cards,
            "players": [{"uid": "TEST-me", "you": True, "pid": "PBB5A55DB", "name": "You", "score": 3, "rank": 2, "level": 4,
                         "answers": [{"outcome": "correct"}, {"outcome": "incorrect", "choice": 0}, {"outcome": "correct"}, {"outcome": "correct"}, {"outcome": "timeout"}]},
                        {"uid": "TEST-friend", "pid": "TESTFRND1", "name": "TEST_Friend", "score": 5, "rank": 1, "level": 6, "wins": 2,
                         "answers": [{"outcome": "correct"}] * 5}]}


async def guards(ctx, ios=""):
    async def g(route):
        r = route.request
        u = r.url
        if r.method in ("GET", "HEAD", "OPTIONS") or "/api/jl/auth/" in u or re.search(r"/api/rf/access(\?|$)", u):
            await route.fallback(); return
        if re.search(r"/api/(jl|rf)/", u):
            BLOCKED.append(r.method + " " + u); await route.fulfill(status=418, body="{}"); return
        await route.fallback()
    await ctx.route(re.compile(r".*/api/(jl|rf)/.*"), g)
    await ctx.route(re.compile(r".*/api/rf/duels/" + DID + r"(\?.*)?$"),
                    lambda route: route.fulfill(status=200, content_type="application/json", body=json.dumps(duel())) if route.request.method == "GET" else route.abort())
    await ctx.route("https://play.google.com/**", lambda route: route.fulfill(status=200, content_type="text/html", body="<html>play stand-in</html>"))
    await ctx.route("https://apps.apple.com/**", lambda route: route.fulfill(status=200, content_type="text/html", body="<html>apple stand-in</html>"))
    if ios:
        async def sw(route):
            resp = await route.fetch(); j = await resp.json(); j["stores"] = {**j.get("stores", {}), "ios": ios}
            await route.fulfill(response=resp, body=json.dumps(j))
        await ctx.route(re.compile(r".*/api/app/switches(\?.*)?$"), sw)


async def vis(page, tid):
    return await page.locator(f'[data-testid="{tid}"]').count() > 0 and await page.locator(f'[data-testid="{tid}"]').first.is_visible()


async def txt(page, tid):
    loc = page.locator(f'[data-testid="{tid}"]')
    return (await loc.first.inner_text()).strip() if await loc.count() else None


async def open_review(page, root):
    await page.goto(f"{BASE}{root}/rapid/duel?review={DID}", wait_until="domcontentloaded")
    await page.wait_for_selector('[data-testid="duel-result"]', timeout=60000)
    await page.wait_for_timeout(3000)


async def card_order(page):
    return await page.evaluate("""() => {
      const s = document.querySelector('[data-testid="duel-result"]'); const c = document.querySelector('[data-testid="arena-get-app"]');
      const n = document.querySelector('[data-testid="duel-practice-note"]');
      if (!s || !c) return {found: !!c};
      let inner = s.firstElementChild; while (inner && inner.children.length === 1 && !inner.contains(n)) inner = inner.firstElementChild;
      const content = n ? n.parentElement : inner; const kids = [...content.children];
      const ci = kids.findIndex(k => k === c || k.contains(c));
      return {found: true, last: ci === kids.length - 1, afterNote: !!n && !!(n.compareDocumentPosition(c) & Node.DOCUMENT_POSITION_FOLLOWING)};
    }""")


async def phone_ctx(b, ua, state, ios=""):
    ctx = await b.new_context(viewport={"width": 390, "height": 844}, user_agent=ua, storage_state=state, has_touch=ua is not None)
    await guards(ctx, ios)
    return ctx, await ctx.new_page()


async def main():
    async with async_playwright() as pw:
        b = await pw.chromium.launch(executable_path="/usr/bin/chromium", args=["--no-sandbox"])
        # 1. Desktop user agent, sign in once in the browser copy.
        ctx = await b.new_context(viewport={"width": 390, "height": 844})
        await guards(ctx)
        page = await ctx.new_page()
        await page.goto(BASE + "/api/arena/entry", wait_until="domcontentloaded")
        await sign_in(page, aits=None, board=False, landing="rapid-fire-home")
        state = await ctx.storage_state()
        await open_review(page, "/api/arena")
        check("D1 card present in browser copy", await vis(page, "arena-get-app"))
        check("D2 title PLAY IN THE APP", (await txt(page, "arena-get-app-title") or "").upper() == "PLAY IN THE APP", await txt(page, "arena-get-app-title"))
        ticks = await page.locator('[data-testid="arena-get-app"]').get_by_text("✓", exact=True).count()
        check("D3 three tick lines", ticks == 3, ticks)
        check("D4 Google Play button", await vis(page, "arena-get-app-android"), await txt(page, "arena-get-app-android"))
        check("D4b label GOOGLE PLAY", "GOOGLE PLAY" in (await txt(page, "arena-get-app-android") or "").upper())
        check("D5 iOS soon note (desktop)", (await txt(page, "arena-get-app-ios-soon")) == "iPhone app coming soon.", await txt(page, "arena-get-app-ios-soon"))
        check("D6 no App Store button", not await vis(page, "arena-get-app-ios"))
        o = await card_order(page)
        check("D7 card is last item of result scroll, after practice note", o.get("last") and o.get("afterNote"), o)
        check("D8 practice note still there", await vis(page, "duel-practice-note"))
        check("D9 scores unchanged (3 – 5)", (await txt(page, "duel-final-mine"), await txt(page, "duel-final-theirs")) == ("3", "5"))
        check("D10 BADLA LO button", "BADLA LO" in (await txt(page, "duel-rematch") or "").upper(), await txt(page, "duel-rematch"))
        check("D11 Done button", await vis(page, "duel-done"))
        await page.locator('[data-testid="arena-get-app"]').scroll_into_view_if_needed()
        await page.wait_for_timeout(800)
        await page.screenshot(path="/tmp/iter156_desktop_card.jpg", quality=40, type="jpeg")
        bb = await page.locator('[data-testid="arena-get-app-android"]').bounding_box()
        check("D12 button touch target >= 44px", bb and bb["height"] >= 44, bb)
        # Press: the store page opens.
        opened = []
        ctx.on("page", lambda p: opened.append(p))
        await page.evaluate("() => { window.__opened = []; const o = window.open; window.open = function(u, ...r){ window.__opened.push(String(u)); return o.call(window, u, ...r); }; }")
        await page.locator('[data-testid="arena-get-app-android"]').click()
        await page.wait_for_timeout(2500)
        urls = await page.evaluate("() => window.__opened")
        purls = [p.url for p in opened]
        check("D13 press opens Play store URL", PLAY in urls or PLAY in purls or page.url == PLAY, {"window.open": urls, "pages": purls, "page": page.url})
        # Daily result (optional) via stand-in.
        try:
            from rf_daily_fixture import fake_daily_done
            dp = await ctx.new_page()
            await fake_daily_done(dp, posts=[], asked=[])
            await dp.goto(BASE + "/api/arena/rapid/daily", wait_until="domcontentloaded")
            await dp.wait_for_selector('[data-testid="rf-daily-back"]', timeout=60000)
            await dp.wait_for_timeout(2500)
            pos = await dp.evaluate("""() => { const c = document.querySelector('[data-testid="arena-get-app"]'), k = document.querySelector('[data-testid="rf-daily-back"]');
              return {c: !!c, before: !!c && !!k && !!(c.compareDocumentPosition(k) & Node.DOCUMENT_POSITION_FOLLOWING)}; }""")
            check("E1 daily result: card just before rf-daily-back", pos["c"] and pos["before"], pos)
            await dp.locator('[data-testid="arena-get-app"]').scroll_into_view_if_needed()
            await dp.screenshot(path="/tmp/iter156_daily_card.jpg", quality=40, type="jpeg")
        except Exception as e:  # optional
            check("E1 daily result reached (optional)", False, str(e)[:200])
        await ctx.close()

        # 2. iPhone / Android user agents.
        for label, ua, ios, exp in [("iPhone", IPHONE_UA, "", dict(play=False, ios=False, soon="The iPhone app is coming soon. Till then, play right here in the browser.")),
                                    ("Android", ANDROID_UA, "", dict(play=True, ios=False, soon=None)),
                                    ("iPhone+ios", IPHONE_UA, "https://apps.apple.com/app/id000000", dict(play=False, ios=True, soon=None)),
                                    ("Android+ios", ANDROID_UA, "https://apps.apple.com/app/id000000", dict(play=True, ios=False, soon=None))]:
            c2, p2 = await phone_ctx(b, ua, state, ios)
            await open_review(p2, "/api/arena")
            check(f"{label}: card present", await vis(p2, "arena-get-app"))
            check(f"{label}: Google Play button {'shown' if exp['play'] else 'hidden'}", await vis(p2, "arena-get-app-android") == exp["play"])
            check(f"{label}: App Store button {'shown' if exp['ios'] else 'hidden'}", await vis(p2, "arena-get-app-ios") == exp["ios"], await txt(p2, "arena-get-app-ios"))
            check(f"{label}: ios-soon note = {exp['soon']!r}", (await txt(p2, "arena-get-app-ios-soon")) == exp["soon"], await txt(p2, "arena-get-app-ios-soon"))
            check(f"{label}: no 'link on its way' note", not await vis(p2, "arena-get-app-soon"))
            if exp["ios"]:
                check(f"{label}: label APP STORE", "APP STORE" in (await txt(p2, "arena-get-app-ios") or "").upper())
                await p2.evaluate("() => { window.__opened = []; const o = window.open; window.open = function(u, ...r){ window.__opened.push(String(u)); return o.call(window, u, ...r); }; }")
                await p2.locator('[data-testid="arena-get-app-ios"]').click()
                await p2.wait_for_timeout(2000)
                check(f"{label}: App Store press opens apple URL", "https://apps.apple.com/app/id000000" in (await p2.evaluate("() => window.__opened")))
            await p2.locator('[data-testid="arena-get-app"]').scroll_into_view_if_needed()
            await p2.wait_for_timeout(600)
            await p2.screenshot(path=f"/tmp/iter156_{label.replace('+', '_')}.jpg", quality=40, type="jpeg")
            await c2.close()

        # 3. Normal app preview (root, not /api/arena): no card.
        for label, ua in [("app desktop", None), ("app Android", ANDROID_UA)]:
            c3, p3 = await phone_ctx(b, ua, state)
            try:
                await open_review(p3, "")
                check(f"{label}: result rendered", await vis(p3, "duel-practice-note"))
                check(f"{label}: NO arena-get-app", await p3.locator('[data-testid="arena-get-app"]').count() == 0)
                if label == "app desktop":
                    await p3.screenshot(path="/tmp/iter156_app_preview.jpg", quality=40, type="jpeg")
            except Exception as e:
                check(f"{label}: review opened", False, str(e)[:200])
                await p3.screenshot(path="/tmp/iter156_app_err.jpg", quality=40, type="jpeg")
            await c3.close()
        check("Z no blocked writes", not BLOCKED, BLOCKED)
        await b.close()
    print(f"RESULT {sum(1 for _, o in RES if o)}/{len(RES)}")


if __name__ == "__main__":
    asyncio.run(main())
