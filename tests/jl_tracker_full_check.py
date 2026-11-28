# JLive Command tracker: full client-event check in the browser preview, READ ONLY (iteration: analytics).
# Collector answered by the browser (nothing reaches the real dashboard); every non-GET /api/jl outside /auth stopped (guards);
# every non-GET /api/rf write stopped and listed too. Never presses Start / Solutions / claims / buys.
import asyncio
import json
import re
import sys

sys.path.insert(0, "/app/tests")
from playwright.async_api import async_playwright  # noqa: E402
from shine_helpers import sign_in, PHONE, PIN  # noqa: E402
from misfire_mock_check import BASE, BLOCKED, ERRORS, RES, check, guards  # noqa: E402

SENT, HEADERS, RFW, COMPLETED, NAMES = [], [], [], [], []
UUID = re.compile(r"[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}")
FORBIDDEN = re.compile(r"^(account_created|(test|attempt)_(started|submitted|resumed|expired))$")
NOTICE = "We use first-party analytics (no ads, no third-party trackers) to understand how JLive is used and to improve it. You can turn this off any time in Settings > Privacy."


async def collector(ctx):
    async def g(route):
        r = route.request
        if r.method == "POST":
            HEADERS.append(dict(r.headers))
            try:
                SENT.extend(json.loads(r.post_data or "{}").get("events") or [])
            except Exception:
                pass
        await route.fulfill(status=200, content_type="application/json", body='{"ok":true}',
                            headers={"Access-Control-Allow-Origin": "*", "Access-Control-Allow-Headers": "*", "Access-Control-Allow-Methods": "POST, OPTIONS"})
    await ctx.route(re.compile(r"https://student-radar-5\.emergent\.host/.*"), g)

    async def rf(route):
        if route.request.method in ("GET", "HEAD", "OPTIONS") or route.request.url.split("?")[0].endswith("/api/rf/access"):
            await route.fallback(); return
        RFW.append(route.request.method + " " + route.request.url.split("?")[0].replace(BASE, ""))
        await route.fulfill(status=418, content_type="application/json", body='{"detail":"blocked by test"}')
    await ctx.route(re.compile(r".*/api/rf/.*"), rf)


def since(i, name=None):
    return [(e["event_name"], e.get("props")) for e in SENT[i:] if name is None or e["event_name"] == name]


async def on_resp(resp):
    try:
        u = resp.url
        if "/api/jl/my/tests" in u and "completed" in u and resp.status == 200:
            j = await resp.json()
            for it in (j.get("data") or {}).get("items") or []:
                COMPLETED.append(it)
        if "/api/jl/auth/me" in u and resp.status == 200:
            j = await resp.json()
            d = j.get("data") or {}
            u2 = d.get("user") or d
            for k in ("name", "full_name", "display_name"):
                if isinstance(u2.get(k), str) and len(u2[k]) > 2:
                    NAMES.append(u2[k])
    except Exception:
        pass


async def goto(page, path, wait=8000):
    i = len(SENT)
    await page.goto(BASE + path, wait_until="domcontentloaded")
    await page.wait_for_timeout(wait)
    return i


async def main():
    async with async_playwright() as pw:
        b = await pw.chromium.launch(executable_path="/usr/bin/chromium", args=["--no-sandbox"])
        ctx = await b.new_context(viewport={"width": 390, "height": 844})
        await ctx.add_init_script("Object.defineProperty(navigator, 'webdriver', { get: () => false })")
        await guards(ctx)
        await collector(ctx)
        page = await ctx.new_page()
        page.on("pageerror", lambda e: ERRORS.append(str(e)[:200]))
        page.on("response", lambda r: asyncio.ensure_future(on_resp(r)))
        await page.goto(BASE + "/", wait_until="domcontentloaded")
        await sign_in(page, width=390)
        await page.wait_for_timeout(9000)
        n = [e["event_name"] for e in SENT]
        print("A signin events:", n)
        for w in ("app_open", "session_start", "screen_view", "identify"):
            check(f"A {w} sent", w in n)
        ids = [e for e in SENT if e["event_name"] == "identify"]
        uid = ids[-1].get("uid") if ids else ""
        check("A identify uid lowercase UUID", bool(uid) and UUID.fullmatch(uid or "") is not None, uid)
        check("A X-JL-Key pk_ and no Authorization", bool(HEADERS) and all(h.get("x-jl-key", "").startswith("pk_") and "authorization" not in h for h in HEADERS))

        # B feature entries (fresh loads)
        for path, feat in (("/misfire", "misfire"), ("/choice", "choice"), ("/mission", "mission"), ("/performance", "performance")):
            i = await goto(page, path)
            f = since(i, "feature_entry_viewed")
            check(f"B {path} feature_entry_viewed once {{feature:{feat}}}", f == [("feature_entry_viewed", {"feature": feat})], f)
        # B2 sub-page of the same feature (client navigation) -> no second entry
        i = await goto(page, "/misfire")
        way = page.locator('[data-testid="misfire-mock-cta"]').first  # the CTA opens a sub-page (the Mock tab stays on /misfire)
        if await way.count():
            j = len(SENT)
            await way.click(force=True)
            await page.wait_for_timeout(6500)
            print("B2 url after tap:", page.url, since(j))
            check("B2 /misfire -> /misfire/<sub> no 2nd feature_entry_viewed", not since(j, "feature_entry_viewed") and "/misfire/" in page.url, since(j))
        else:
            print("B2 misfire-mock-cta not present, skipped")

        # C Rapid tab store / trophy / gang
        i = await goto(page, "/", 6000)
        await page.click('[data-testid="tab-rapid"]', force=True)
        await page.wait_for_timeout(4000)
        if await page.locator('[data-testid="rf-daily-popup-exit"]').count():  # All India Rapid's daily popup covers the tab
            await page.click('[data-testid="rf-daily-popup-exit"]', force=True)
            await page.wait_for_timeout(1500)
        for key, feat in (("store", "store"), ("trophy", "leagues"), ("gang", "gangs")):
            j = len(SENT)
            loc = page.locator(f'[data-testid="arena-tab-{key}"]').first
            if await loc.count():
                await loc.click(force=True)
                await page.wait_for_timeout(6500)
                f = since(j, "feature_entry_viewed")
                check(f"C arena-tab-{key} -> {{feature:{feat}}}", ("feature_entry_viewed", {"feature": feat}) in f and len(f) == 1, f)
            else:
                check(f"C arena-tab-{key} present", False)
        await page.screenshot(path="/tmp/jl_gang_tab.png", quality=40, type="jpeg")
        ng = page.locator('[data-testid="rf-new-gang"]').first
        if await ng.count():
            j = len(SENT)
            await ng.click(force=True)
            await page.wait_for_timeout(6500)
            check("C2 gang tab -> /rapid/gang/new no 2nd gangs entry", not since(j, "feature_entry_viewed"), (page.url, since(j, "feature_entry_viewed")))
        else:
            print("C2 rf-new-gang not present, skipped")

        # D live
        i = await goto(page, "/live", 9000)
        s = since(i, "series_slot_viewed")
        check("D /live series_slot_viewed {series_id, slot}", bool(s) and set(s[0][1] or {}) == {"series_id", "slot"}, s)

        # E My Tests completed -> set page + result page
        await goto(page, "/tests", 9000)
        print("E completed items:", len(COMPLETED), json.dumps(COMPLETED[:1])[:600])
        att = next((c for c in COMPLETED if c.get("status") == "completed" and c.get("set_id")), None)
        if att:
            aid, sid = att["id"], att["set_id"]
            i = await goto(page, f"/set/{sid}", 9000)
            s = since(i, "test_card_viewed")
            check("E /set/<id> test_card_viewed {set_id}", s and s[0][1] == {"set_id": str(sid)}, s)
            i = await goto(page, f"/result/{aid}", 12000)
            rv, ao = since(i, "result_viewed"), since(i, "analysis_opened")
            print("E result events:", since(i))
            check("E result_viewed {set_id}", len(rv) == 1 and set(rv[0][1]) == {"set_id"}, rv)
            check("E analysis_opened {set_id}", len(ao) == 1 and set(ao[0][1]) == {"set_id"}, ao)
        else:
            check("E found a completed attempt", False)

        # F Rank tools + catalogue search
        i = await goto(page, "/rank", 8000)
        for t in ("cutoff", "compare"):
            loc = page.locator(f'[data-testid="rank-tool-{t}"]').first
            if await loc.count():
                await loc.click(force=True)
                await page.wait_for_timeout(1500)
        r = since(i, "rank_tool_opened")
        check("F rank_tool_opened {tool} for cutoff+compare", ("rank_tool_opened", {"tool": "cutoff"}) in r and ("rank_tool_opened", {"tool": "compare"}) in r, r)
        i = await goto(page, "/catalogue?slug=jee-main&kind=mocks", 9000)
        inp = page.locator('[data-testid="catalogue-search-input"]').first
        if await inp.count():
            await inp.fill("JEE")
            await page.wait_for_timeout(5000)
            await inp.fill("zqxjvkwq")
            await page.wait_for_timeout(7000)
            sp, sz = since(i, "search_performed"), since(i, "search_zero_results")
            print("F search:", sp, sz)
            check("F search_performed {area, results}", bool(sp) and all(set(p) <= {"area", "results"} for _, p in sp), sp)
            check("F search_zero_results {area}", bool(sz) and all(set(p) == {"area"} for _, p in sz), sz)
            check("F area is papers", all(p.get("area") == "papers" for _, p in sp + sz), sp + sz)
            check("F typed text not in any event", "zqxjvkwq" not in json.dumps(SENT) and '"JEE"' not in json.dumps([e.get("props") for e in SENT]))
        else:
            check("F catalogue-search-input present", False)

        # G Privacy switch
        await goto(page, "/account", 8000)
        row = page.locator('[data-testid="account-analytics"]')
        await row.scroll_into_view_if_needed()
        check("G label", (await page.locator('[data-testid="account-analytics-label"]').inner_text()).strip() == "Share usage analytics")
        check("G notice exact", (await page.locator('[data-testid="account-analytics-notice"]').inner_text()).strip() == NOTICE)
        sw = page.locator('[data-testid="account-analytics-switch"] input, input[role="switch"]').first
        check("G switch default ON", await sw.is_checked())
        box = await page.locator('[data-testid="account-analytics-switch"]').bounding_box()
        print("G switch box", box)
        await page.screenshot(path="/tmp/jl_account_privacy.png", quality=40, type="jpeg")
        j = len(SENT)
        await sw.click(force=True)
        await page.wait_for_timeout(3000)
        check("G OFF sends opt_out", "opt_out" in [x for x, _ in since(j)], since(j))
        check("G jl_optout='1' stored", await page.evaluate("localStorage.getItem('jl_optout')") == "1")
        k = len(SENT); kh = len(HEADERS)
        for p in ("/misfire", "/choice", "/live"):
            await goto(page, p, 6000)
        await page.wait_for_timeout(6000)
        check("G nothing POSTed while OFF", len(SENT) == k and len(HEADERS) == kh, since(k))
        await goto(page, "/account", 8000)
        sw = page.locator('[data-testid="account-analytics-switch"] input, input[role="switch"]').first
        check("G OFF survives reload", not await sw.is_checked())
        j = len(SENT)
        await sw.click(force=True)
        await page.wait_for_timeout(7000)
        check("G ON sends opt_in", "opt_in" in [x for x, _ in since(j)], since(j))
        j = await goto(page, "/misfire", 9000)
        check("G events resume after ON", len(since(j)) > 0, since(j))
        check("G restored ON (jl_optout cleared)", await page.evaluate("localStorage.getItem('jl_optout')") is None)

        # H privacy page
        await goto(page, "/privacy", 6000)
        sec = page.locator('[data-testid="privacy-section-analytics"]')
        txt = await sec.inner_text() if await sec.count() else ""
        check("H /privacy analytics section with notice", NOTICE in " ".join(txt.split()), txt[:200])

        # S sign-out reset: later events carry no uid and a new anon_id
        before_anon = SENT[-1]["anon_id"] if SENT else ""
        await goto(page, "/account", 7000)
        so = page.locator('[data-testid="account-signout-button"]')
        await so.scroll_into_view_if_needed(); await so.click(force=True)
        await page.wait_for_timeout(3000)
        for t in ("signout-keep-drafts",):
            c = page.locator(f'[data-testid="{t}"]')
            if await c.count():
                await c.first.click(force=True); await page.wait_for_timeout(2000)
        j = len(SENT)
        await page.wait_for_timeout(2000)
        j = await goto(page, "/privacy", 9000)
        after = SENT[j:]
        print("S after sign-out:", [(e["event_name"], e.get("uid"), e["anon_id"][:8]) for e in after][:6], "url", page.url)
        check("S after sign-out: no uid and new anon_id", bool(after) and all(not e.get("uid") for e in after) and all(e["anon_id"] != before_anon for e in after))

        # Z global checks
        blob = json.dumps([{"p": e.get("props"), "c": e.get("context")} for e in SENT])
        bad = [x for x in [PHONE, PHONE[-4:] if False else None, *NAMES] if x and x in blob]
        pin_hit = re.search(rf"(?<![0-9a-f-]){PIN}(?![0-9a-f-])", blob)
        check("Z no phone/name/PIN/token in props/context", not bad and not pin_hit and not re.search(r"token|bearer|authorization", blob, re.I), (bad, pin_hit and pin_hit.group(0)))
        allnames = sorted(set(e["event_name"] for e in SENT))
        check("Z no forbidden event names", not any(FORBIDDEN.match(x) for x in allnames), allnames)
        check("Z uid on events all same lowercase UUID", len({e.get("uid") for e in SENT if e.get("uid")}) == 1)
        print("ALL EVENT NAMES", allnames)
        await b.close()
    print("BLOCKED jl", BLOCKED)
    print("BLOCKED rf", RFW)
    print("PAGEERRORS", ERRORS[:5])
    print(f"{sum(1 for _, ok in RES if ok)}/{len(RES)} passed")

if __name__ == "__main__":
    asyncio.run(main())
