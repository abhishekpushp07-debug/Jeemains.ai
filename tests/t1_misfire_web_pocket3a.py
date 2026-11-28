# T1 independent checks, Misfire Mock Pocket 3a (website contract of 28 Nov 2026), READ ONLY for the QA learner.
#   python3 /app/tests/t1_misfire_web_pocket3a.py
# Every website answer for the Misfire Mock is played in the browser; every non-GET /api/jl/* (outside /auth) is stopped
# (418) and listed, every non-GET /api/rf/dream** is faked. Nothing is started.
import asyncio
import json
import re
import sys

sys.path.insert(0, "/app/tests")
from dotenv import dotenv_values  # noqa: E402
from playwright.async_api import async_playwright  # noqa: E402
from shine_helpers import sign_in  # noqa: E402

BASE = dotenv_values("/app/frontend/.env")["EXPO_PUBLIC_BACKEND_URL"].rstrip("/")
FINISHED = "1ea510f2-1d2a-41f7-9bb4-a8b28c16f98f"
RES, BLOCKED, DREAM, ASKS, ERRORS = [], [], [], [], []
ST = {"switch": None, "papers": "ok", "pool": False, "result": None, "fewer": 0, "bank_extra": {}, "bank_fail": False, "list": "ok"}
SHOTS = "/app/test_reports/artifacts/t1_pocket3a"
SENT = {"422a": (422, "Chune hue chapters mein abhi koi khula sawaal nahi hai. Doosre chapter chuno."),
        "422b": (422, "Har subject mein 25 tak sawaal chuno, kul kam se kam 1."),
        "409a": (409, "Misfire Mock abhi band hai."),
        "409b": (409, "Yeh mock pehle hi ban chuka hai. Misfire ke Mock tab mein dekho."),
        "429": (429, "Aaj ke Misfire Mock poore ho gaye. Kal naya mock banao.")}
DOWN = "jeelive.ai abhi jawab nahi de raha"
NOTYET = "Paper banana abhi jeelive.ai se jud raha hai"


def check(name, ok, info=""):
    RES.append((name, bool(ok)))
    print(("PASS " if ok else "FAIL ") + name + (" :: " + str(info)[:300] if info != "" else ""), flush=True)


def tid(t):
    return f'[data-testid="{t}"]'


def env(d):
    return json.dumps({"data": d, "error": None, "meta": {"api_version": "1"}})


def env_err(msg, code="x"):
    return json.dumps({"data": None, "error": {"code": code, "message": msg}, "meta": {"api_version": "1"}})


async def vis(page, t, timeout=8000):
    try:
        await page.wait_for_selector(tid(t), state="visible", timeout=timeout); return True
    except Exception:
        return False


async def txt(page, t):
    loc = page.locator(tid(t))
    return (await loc.first.inner_text()).strip() if await loc.count() else ""


async def tabs(page):
    return await page.locator('[data-testid^="misfire-tab-"]').evaluate_all(
        "els => els.filter(e => /^misfire-tab-[a-z-]+$/.test(e.dataset.testid)).map(e => e.innerText.trim())")


def item(sid, n, att=None, given=10, minutes=21, asked=None):
    return {"set_id": sid, "title": f"Misfire Mock #{n}", "number": n, "created_at": 1764400000 - n * 1000,
            "asked": asked if asked is not None else given, "given": given, "minutes": minutes, "attempt": att}


PAGE1 = [item("t1-unstarted-01", 9), item("t1-running-0001", 8, {"id": "t1-att-run", "status": "active", "resumable": True, "started_at": 1764300000, "submitted_at": None, "summary": None}),
         item("t1-waiting-0001", 7, {"id": "t1-att-wait", "status": "submitted", "resumable": False, "started_at": 1764200000, "submitted_at": 1764203000, "summary": None}),
         item("t1-done-res-001", 6, {"id": "t1-att-resum", "status": "active", "resumable": True, "started_at": 1764100000, "submitted_at": None,
                                     "summary": {"score": 12, "maximum": 60, "correct": 4, "incorrect": 4, "skipped": 7}}, given=15, minutes=32),
         {"set_id": "bad id!", "title": "broken", "attempt": None}]
PAGE2 = [item("t1-older-00001", 1, given=None, asked=12)]


async def setup(ctx):
    async def jl(route):
        r = route.request
        if r.method in ("GET", "HEAD", "OPTIONS") or "/api/jl/auth" in r.url:
            await route.fallback(); return
        path = r.url.split("?")[0].replace(BASE, "")
        if path.endswith("/api/jl/choice/papers") and r.method == "POST":
            body = json.loads(r.post_data or "{}"); ASKS.append(body)
            m = ST["papers"]
            asked = sum((body.get("counts") or {}).values())
            if m in SENT:
                c, t = SENT[m]; await route.fulfill(status=c, content_type="application/json", body=env_err(t, m))
            elif m == "500html":
                await route.fulfill(status=500, content_type="text/html", body="<html>Internal Server Error</html>")
            elif m == "abort":
                await route.abort()
            elif m == "405":
                await route.fulfill(status=405, content_type="application/json", body='{"detail":"Method Not Allowed"}')
            else:
                given = asked - ST["fewer"]
                await route.fulfill(status=201, content_type="application/json", body=env({"set_id": "t1-made-set-01", "title": "Misfire Mock #10", "number": 10, "asked": asked, "given": given, "minutes": 12}))
            return
        BLOCKED.append(r.method + " " + path)
        await route.fulfill(status=418, content_type="application/json", body=env_err("blocked by test", "blocked"))
    await ctx.route(re.compile(r".*/api/jl/.*"), jl)

    async def dream(route):
        if route.request.method in ("GET", "HEAD", "OPTIONS"):
            await route.fallback(); return
        DREAM.append(route.request.method + " " + route.request.url.replace(BASE, ""))
        await route.fulfill(status=200, content_type="application/json", body='{"ok":true}')
    await ctx.route(re.compile(r".*/api/rf/dream.*"), dream)

    async def bank(route):
        if ST["bank_fail"]:
            await route.fulfill(status=500, content_type="application/json", body='{"detail":"boom"}'); return
        resp = await route.fetch()
        try:
            j = await resp.json()
            if ST["switch"] is not None:
                j["misfire"] = ST["switch"]; j["pick"] = False; j["random"] = False
            j.update(ST["bank_extra"])
            await route.fulfill(response=resp, body=json.dumps(j))
        except Exception:
            await route.fulfill(response=resp)
    await ctx.route(re.compile(r".*/api/choice/bank.*"), bank)

    async def mocks(route):
        page = int(re.search(r"page=(\d+)", route.request.url).group(1)) if "page=" in route.request.url else 1
        items = PAGE1 if page == 1 else PAGE2
        if ST["list"] == "500":
            await route.fulfill(status=500, content_type="application/json", body=env_err("Internal error", "server")); return
        if ST["list"] == "empty":
            await route.fulfill(status=200, content_type="application/json", body=env({"items": [], "page": 1, "pages": 1, "total": 0})); return
        await route.fulfill(status=200, content_type="application/json", body=env({"items": items, "page": page, "pages": 2, "total": 5}))
    await ctx.route(re.compile(r".*/api/jl/my/misfire/mocks\?.*"), mocks)

    async def a_set(route):
        sid = route.request.url.split("/my/sets/")[1].split("?")[0].split("/")[0]
        await route.fulfill(status=200, content_type="application/json", body=env({
            "id": sid, "title": "Misfire Mock #10", "exam": "JEE Main", "test_kind": "misfire", "count": 5, "maximum": 20,
            "rules": {"correct": 4, "wrong": -1, "skipped": 0, "minutes": 12}, "types": {"mcq": 5, "integer": 0}, "attempt": None, "saved": False}))
    await ctx.route(re.compile(r".*/api/jl/my/sets/t1-.*"), a_set)

    async def results(route):
        resp = await route.fetch()
        try:
            j = await resp.json()
            if ST["result"] is not None and isinstance(j.get("data"), dict):
                j["data"]["test_kind"] = "misfire"
                if ST["result"] != "retry":
                    j["data"]["misfire"] = ST["result"]
            await route.fulfill(response=resp, body=json.dumps(j))
        except Exception:
            await route.fulfill(response=resp)
    await ctx.route(re.compile(r".*/api/jl/attempts/[^/]+/results.*"), results)

    async def pool(route):
        if not ST["pool"] or "subject=Physics" not in route.request.url or "status=open" not in route.request.url:
            await route.fallback(); return
        await route.fulfill(status=200, content_type="application/json", body=env({
            "items": [], "total": 14, "page": 1, "pages": 1, "waiting": 0, "chapters": [{"name": "01 Units and Measurement", "count": 8}, {"name": "02 Kinematics", "count": 6}]}))
    await ctx.route(re.compile(r".*/api/jl/my/misfire\?.*"), pool)


async def new_page(b):
    ctx = await b.new_context(viewport={"width": 375, "height": 667})
    await setup(ctx)
    page = await ctx.new_page()
    page.on("pageerror", lambda e: ERRORS.append(str(e)[:200]))
    await page.goto(BASE + "/", wait_until="domcontentloaded")
    await sign_in(page, width=375, height=667)
    return ctx, page


async def goto(page, path, t, timeout=45000):
    await page.goto(BASE + path, wait_until="domcontentloaded")
    return await vis(page, t, timeout)


async def make_with(page, mode, wait="mock-making-error"):
    ST["papers"] = mode
    n = len(ASKS)
    if await page.locator(tid("mock-making-retry")).count():
        await page.click(tid("mock-making-retry"))
    else:  # the website's own "no" (4xx): the sheet offers to change the choice, then Mock banao again
        if await page.locator(tid("mock-making-close")).count():
            await page.click(tid("mock-making-close"))
            await page.wait_for_timeout(600)
        await page.click(tid("mock-new-bar-go"))
    await vis(page, wait, 10000)
    await page.wait_for_timeout(400)
    return ASKS[n:] if len(ASKS) > n else []


async def main():
    async with async_playwright() as p:
        b = await p.chromium.launch(executable_path="/usr/bin/chromium", args=["--no-sandbox"])
        # ---------- A. switch as the real server says (off) + not-exact values ----------
        ctx, page = await new_page(b)
        await goto(page, "/misfire", "misfire-tab-all")
        await page.wait_for_timeout(3000)
        t = await tabs(page)
        check("A1 switch off: tabs Sab, Offline Misfire, … (no Mock)", t[:2] == ["Sab", "Offline Misfire"] and "Mock" not in t, t)
        await goto(page, "/choice", "choice-screen")
        await page.wait_for_timeout(4000)
        choice_off = await txt(page, "choice-screen")
        for val in ["true", 1, None]:
            ST["switch"] = val if val is not None else None
            if val is None:
                continue
            await page.evaluate("() => { try { Object.keys(localStorage).filter(k => /bank/i.test(k)).forEach(k => localStorage.removeItem(k)) } catch (e) {} }")
            await goto(page, "/misfire?tab=web", "misfire-tab-all")
            await page.wait_for_timeout(3500)
            t = await tabs(page)
            check(f"A2 misfire={val!r} (not exact true): no Mock tab, Sab shown", "Mock" not in t and await page.locator(tid("misfire-web-mocks")).count() == 0, t)
        ST["switch"] = None
        check("A3 switch off: no POST /choice/papers", not ASKS, ASKS)
        await ctx.close()

        # ---------- B. switch on (website: pick false, random false, misfire true) ----------
        ST["switch"] = True
        ctx, page = await new_page(b)
        await goto(page, "/choice", "choice-screen")
        await page.wait_for_timeout(4000)
        choice_on = await txt(page, "choice-screen")
        check("B1 Student Choice same with only misfire on", choice_on == choice_off, [choice_off[:200], choice_on[:200]])
        await goto(page, "/misfire", "misfire-tab-all")
        await vis(page, "misfire-tab-web", 15000)
        t = await tabs(page)
        check("B2 Mock tab right after Sab", t[:3] == ["Sab", "Mock", "Offline Misfire"], t)
        await page.click(tid("misfire-tab-web"))
        await vis(page, "misfire-web-t1-unstarted-01", 15000)
        ids = await page.locator('[data-testid^="misfire-web-"]').evaluate_all(
            "els => els.map(e => e.dataset.testid).filter(t => /^misfire-web-t1-[a-z0-9-]+$/.test(t))")
        check("B3 list order newest first; broken set_id skipped", ids == ["misfire-web-t1-unstarted-01", "misfire-web-t1-running-0001", "misfire-web-t1-waiting-0001", "misfire-web-t1-done-res-001"], ids)
        cards = {k: await txt(page, f"misfire-web-{k}") for k in ["t1-unstarted-01", "t1-running-0001", "t1-waiting-0001", "t1-done-res-001"]}
        check("B4 unstarted: SHURU NAHI HUA + Shuru karo", "SHURU NAHI HUA" in cards["t1-unstarted-01"] and "Shuru karo" in cards["t1-unstarted-01"], cards["t1-unstarted-01"])
        check("B5 running: CHAL RAHA HAI + Resume", "CHAL RAHA HAI" in cards["t1-running-0001"] and "Resume" in cards["t1-running-0001"], cards["t1-running-0001"])
        check("B6 submitted no summary: RESULT AA RAHA HAI + Result dekho", "RESULT AA RAHA HAI" in cards["t1-waiting-0001"] and "Result dekho" in cards["t1-waiting-0001"], cards["t1-waiting-0001"])
        c = cards["t1-done-res-001"]
        check("B7 resumable WITH summary: result (score 12/60, 15 sawaal · 32 min, Result dekho)", "12" in c and "/60" in c and "15 sawaal · 32 min" in c and "Result dekho" in c and "Resume" not in c, c)
        await page.screenshot(path=f"{SHOTS}_list.jpg", quality=40, full_page=False)
        more = await vis(page, "misfire-web-more", 8000)
        if more:
            await page.click(tid("misfire-web-more"))
        ok2 = await vis(page, "misfire-web-t1-older-00001", 10000)
        check("B8 page 2 via 'Aur mocks dikhao' (given missing -> asked 12)", more and ok2 and "12 sawaal" in await txt(page, "misfire-web-t1-older-00001"), await txt(page, "misfire-web-t1-older-00001"))
        box = await page.locator(tid("misfire-web-new")).bounding_box()
        check("B9 'Naya mock banao' touch target >= 44 high", box and box["height"] >= 44, box)
        await page.click(tid("misfire-web-t1-waiting-0001"))
        await page.wait_for_timeout(1500)
        check("B10 waiting result opens /result/<attempt>", "/result/t1-att-wait" in page.url, page.url)
        await goto(page, "/misfire?tab=web", "misfire-web-t1-done-res-001", 30000)
        await page.click(tid("misfire-web-t1-done-res-001"))
        await page.wait_for_timeout(1500)
        check("B11 resumable+summary opens /result/<attempt>", "/result/t1-att-resum" in page.url, page.url)

        # Door C from ?web=1
        ST["pool"] = True
        await goto(page, "/misfire/mock/new?web=1", "mock-new-bar-go", 45000)
        await page.wait_for_timeout(1500)
        hdr = await txt(page, "mock-new-header")
        check("C1 ?web=1 with switch on: 'Misfire Mock banao'", "Misfire Mock banao" in hdr, hdr)
        await page.click(tid("mock-count-physics-5"))
        await page.click(tid("mock-subject-chemistry"))
        await page.click(tid("mock-count-chemistry-10"))
        got = await make_with(page, "429")
        k1 = got[0].get("request_key") if got else None
        body = got[0] if got else {}
        check("C2 body exact (exam, mode, counts, uuid key, no chapters)", body.get("exam") == "jee-main" and body.get("mode") == "misfire"
              and body.get("counts") == {"Physics": 5, "Chemistry": 10, "Mathematics": 0} and "chapters" not in body
              and re.fullmatch(r"[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}", k1 or "") and set(body) == {"exam", "mode", "counts", "request_key"}, body)
        e = await txt(page, "mock-making-error")
        check("C3 429 sentence word for word", SENT["429"][1] in e, e)
        keys = [k1]
        for m in ["409a", "409b", "422a", "422b"]:
            got = await make_with(page, m)
            keys += [g.get("request_key") for g in got]
            e = await txt(page, "mock-making-error")
            check(f"C4 {m} sentence word for word (retry)", SENT[m][1] in e, e)
        for m, want in [("500html", DOWN), ("abort", DOWN), ("405", NOTYET)]:
            got = await make_with(page, m)
            keys += [g.get("request_key") for g in got]
            e = await txt(page, "mock-making-error")
            check(f"C5 {m} -> '{want[:25]}…'", want in e, e)
        check("C6 one request_key for every retry of the same ask", len(keys) == 8 and len(set(keys)) == 1, keys)
        await page.click(tid("mock-making-cancel"))
        await page.wait_for_timeout(500)
        # chapters: Physics only 'Kinematics'
        await page.click(tid("mock-subject-physics"))
        await page.click(tid("mock-chapter-0"))
        await page.wait_for_timeout(300)
        got = await make_with(page, "409b")
        body = got[0] if got else {}
        check("C7 chapters sent only for ticked subject, new key", body.get("chapters") == {"Physics": ["02 Kinematics"]} and body.get("request_key") not in keys, body)
        k_ch = body.get("request_key")
        await page.click(tid("mock-making-cancel"))
        # Chemistry count changed -> new key; Mathematics count 0 with partial chapters -> not sent
        await page.click(tid("mock-subject-chemistry"))
        await page.click(tid("mock-count-chemistry-5"))
        ST["fewer"] = 2
        got = await make_with(page, "ok", "mock-making-fewer-note")
        body = got[0] if got else {}
        check("C8 count change -> new key", body.get("request_key") not in keys + [k_ch] and body.get("counts") == {"Physics": 5, "Chemistry": 5, "Mathematics": 0}, body)
        note = await txt(page, "mock-making-fewer-note")
        check("C9 fewer note 'Aapne 10 sawaal maange the, 8 mile: …'", note.startswith("Aapne 10 sawaal maange the, 8 mile:"), note)
        await page.screenshot(path=f"{SHOTS}_fewer.jpg", quality=40, full_page=False)
        await page.click(tid("mock-making-open"))
        await page.wait_for_timeout(2500)
        check("C10 'Paper kholo' opens /set/<id>", "/set/t1-made-set-01" in page.url, page.url)
        # given == asked -> straight, double tap sends one ask (or the same key)
        ST["fewer"] = 0
        await goto(page, "/misfire/mock/new?web=1", "mock-new-bar-go", 45000)
        await page.wait_for_timeout(1000)
        await page.click(tid("mock-count-physics-5"))
        n = len(ASKS)
        await page.click(tid("mock-new-bar-go"))
        try:
            await page.click(tid("mock-new-bar-go"), force=True, timeout=800, no_wait_after=True)
        except Exception:
            pass
        await page.wait_for_timeout(3000)
        sent = ASKS[n:]
        check("C11 given==asked: straight to /set/<id>", "/set/t1-made-set-01" in page.url, page.url)
        check("C12 double tap: never two different keys", len({s.get("request_key") for s in sent}) == 1, [s.get("request_key") for s in sent])
        ST["pool"] = False
        # Offline Misfire setup (no ?web) with switch on: no door C
        await goto(page, "/misfire/mock/new", "mock-new-screen", 45000)
        await page.wait_for_timeout(2500)
        check("C13 setup without ?web while on: Offline Misfire banao", "Offline Misfire banao" in await txt(page, "mock-new-header"))
        n = len(ASKS)
        if await vis(page, "mock-count-physics-5", 15000):
            await page.click(tid("mock-count-physics-5"))
            await page.click(tid("mock-new-bar-go"))
            await page.wait_for_timeout(8000)
        check("C14 Offline Misfire make: no POST /choice/papers", len(ASKS) == n, page.url)
        await ctx.close()

        # ---------- D. result card, fresh browser each ----------
        for label, val, want in [("0/15", {"understood": 0, "total": 15}, "0 / 15 sawaal “Samajh gaya” mein chale gaye"),
                                 ("bad total", {"understood": 3, "total": 2}, "3 sawaal “Samajh gaya” mein chale gaye"),
                                 ("retry", "retry", None)]:
            ST["result"] = val
            ctx, page = await new_page(b)
            await goto(page, f"/result/{FINISHED}", "result-header", 60000)
            if await vis(page, "result-tab-analysis", 30000):
                await page.click(tid("result-tab-analysis"))
            await vis(page, "result-analysis-panel", 30000)
            await page.wait_for_timeout(2500)
            head = await txt(page, "result-header")
            card = await txt(page, "result-misfire-understood-count")
            check(f"D eyebrow JEE Main · Misfire Mock ({label})", "JEE MAIN · MISFIRE MOCK" in head.upper(), head)
            if want:
                check(f"D card {label}", card == want, card)
                if label == "0/15":
                    body = await txt(page, "result-misfire-understood")
                    check("D 0 understood: 'Is baar koi sawaal list se nahi hata' body", "Is baar koi sawaal list se nahi hata" in body, body)
                    await page.screenshot(path=f"{SHOTS}_card.jpg", quality=40, full_page=False)
                    await page.click(tid("result-misfire-open"))
                    ok = await vis(page, "misfire-web-mocks", 20000)
                    check("D 'Misfire kholo' opens the Mock tab", ok, page.url)
            else:
                check("D retry: NO card", await page.locator(tid("result-misfire-understood")).count() == 0, card)
            await ctx.close()
        check("Z no page errors", not ERRORS, ERRORS[:4])
        check("Z nothing written to the website", not BLOCKED, BLOCKED)
        print("INFO dream writes faked:", DREAM, flush=True)
        await b.close()
    print(f"\n{sum(1 for _, ok in RES if ok)}/{len(RES)} passed", flush=True)


if __name__ == "__main__":
    asyncio.run(main())
