"""Misfire Mock END TO END on LIVE jeelive.ai, in the app (web preview), with the TEST account only (owner, 29 Nov 2026:
"Live pr hi kr lo test"; the owner turned the switch On on live). Never the owner's QA learner.
  python3 /app/tests/misfire_live_ui_check.py [part]   part = all (default) | list | make | expire | limit
Real writes go to the website for the TEST account (mocks, attempts, answers): that is the test. Only the Dream meter's
writes (/api/rf/dream**) are answered by the browser. The server side is read back through the app's server
(tests/misfire_live_e2e_api.py, its own session of the same TEST account)."""
import asyncio, json, re, sys, time, uuid

sys.path.insert(0, "/app/tests")
from dotenv import dotenv_values  # noqa: E402
from playwright.async_api import async_playwright  # noqa: E402
import shine_helpers  # noqa: E402
import misfire_live_e2e_api as m  # noqa: E402
import misfire_live_attempt as la  # noqa: E402

shine_helpers.PHONE, shine_helpers.PIN = m.PHONE, m.PIN  # the TEST account, never the owner's
BASE = dotenv_values("/app/frontend/.env")["EXPO_PUBLIC_BACKEND_URL"].rstrip("/")
RES, ERRORS, ASKS, WRITES = [], [], [], []
SHOTS = "/app/test_reports/artifacts/misfire_live"
PART = sys.argv[1] if len(sys.argv) > 1 else "all"
MOCK1 = "0383b1b9-04b0-57c9-a520-ff00db1a6653"


def check(name, ok, info=""):
    RES.append((name, bool(ok)))
    print(("PASS " if ok else "FAIL ") + name + (" :: " + str(info) if info != "" else ""), flush=True)


def tid(t):
    return f'[data-testid="{t}"]'


async def visible(page, t, timeout=8000):
    try:
        await page.wait_for_selector(tid(t), state="visible", timeout=timeout); return True
    except Exception:
        return False


async def txt(page, t):
    loc = page.locator(tid(t))
    return (await loc.first.inner_text()).strip() if await loc.count() else ""


async def setup(ctx):
    async def writes(route):
        r = route.request
        if r.method not in ("GET", "HEAD", "OPTIONS"):
            path = r.url.split("?")[0].replace(BASE, "")
            WRITES.append(r.method + " " + path)
            if path.endswith("/api/jl/choice/papers"):
                ASKS.append(json.loads(r.post_data or "{}"))
        await route.fallback()
    await ctx.route(re.compile(r".*/api/jl/.*"), writes)

    async def dream(route):  # the Dream meter never takes a test paper
        if route.request.method == "GET":
            await route.fallback(); return
        await route.fulfill(status=200, content_type="application/json", body='{"ok":true}')
    await ctx.route(re.compile(r".*/api/rf/dream.*"), dream)


async def unlock(page, attempt):
    """A fresh submission locks its result behind the share card (phone storage): the test opens it."""
    await page.evaluate("id => { for (const k of Object.keys(localStorage)) if (k.includes('share_gate.' + id)) localStorage.removeItem(k); }", attempt)


async def open_result(page, attempt):
    await unlock(page, attempt)
    await page.goto(BASE + f"/result/{attempt}", wait_until="domcontentloaded")
    for _ in range(3):
        if await visible(page, "result-analysis-panel", 40000):
            return True
        if await page.locator(tid("share-gate")).count():
            await unlock(page, attempt); await page.reload(wait_until="domcontentloaded")
        elif await page.locator(tid("result-check-again")).count():
            await page.click(tid("result-check-again"))
    return False


async def mock_tab(page):
    await page.goto(BASE + "/misfire?tab=web", wait_until="domcontentloaded")
    return await visible(page, "misfire-web-hero", 45000)


def key_for(q, K):
    return K.get(q["id"]) or K.get(la.body(q))


async def answer_in_ui(page, q, value):
    if q.get("type") == "integer":
        await page.fill(tid("player-integer-input"), value)
    else:
        await page.click(tid(f"player-option-{value}"))
    for _ in range(30):  # saved to the website (the player's own status)
        await page.wait_for_timeout(500)
        st, d = m.jl("GET", f"attempts/{q['_attempt']}")
        if ((d.get("data") or {}).get("answers") or {}).get(q["id"], {}).get("value") == value:
            return True
    return False


async def into_player(page):
    if await visible(page, "get-ready-begin", 30000):
        await page.click(tid("get-ready-begin"))
    return await visible(page, "player-screen", 30000)


async def submit_in_ui(page):
    await page.click(tid("player-submit-top"))
    await visible(page, "player-submit-sheet", 15000)
    await page.click(tid("player-confirm-submit"))
    for _ in range(60):
        await page.wait_for_timeout(1000)
        if "/result/" in page.url:
            return True
    return False


async def part_list(page):
    """Mock #1, made and taken earlier on the TEST account through the app's server (3 right, 2 wrong, 3 left)."""
    ok = await visible(page, "misfire-tab-web", 45000)
    labels = await page.locator('[data-testid^="misfire-tab-"]').evaluate_all(
        "els => els.filter(e => /^misfire-tab-[a-z-]+$/.test(e.dataset.testid)).map(e => [e.dataset.testid.slice(12), e.innerText.trim()])")
    check("L1 live switch on: Misfire shows Sab, Mock, Offline Misfire", ok and labels[:3] == [["all", "Sab"], ["web", "Mock"], ["mock", "Offline Misfire"]], labels)
    await page.click(tid("misfire-tab-web"))
    ok = await visible(page, f"misfire-web-{MOCK1}", 30000)
    card = await txt(page, f"misfire-web-{MOCK1}")
    check("L2 Mock #1 listed: per-subject asked/given read as 8 questions, 17 min", ok and "8 sawaal · 17 min" in card and "Misfire Mock #1" in card, card.replace("\n", " | "))
    row = la.row(MOCK1) or {}
    s = (row.get("attempt") or {}).get("summary") or {}
    check("L3 card shows the latest attempt's score and counts", f"{s.get('score')}" in card and f"/{s.get('maximum')}" in card and f"{s.get('correct')} sahi" in card
          and f"{s.get('incorrect')} galat" in card and f"{s.get('skipped')} chhode" in card and "Result dekho" in card and "RESULT" in card, [s, card.replace("\n", " | ")])
    await page.screenshot(path=f"{SHOTS}_list.jpg", quality=40, type="jpeg")
    latest = (row.get("attempt") or {}).get("id")
    await page.click(tid(f"misfire-web-{MOCK1}"))
    await page.wait_for_timeout(2500)
    check("L4 tap opens the latest attempt's result", f"/result/{latest}" in page.url, page.url)
    ok = await open_result(page, latest)
    st, r = m.jl("GET", f"attempts/{latest}/results?score_version=original")
    want = (r.get("data") or {}).get("misfire") or {}
    await visible(page, "result-misfire-understood", 20000)
    n = await txt(page, "result-misfire-understood-count")
    check("L5 result card = the website's misfire numbers", ok and want and n.startswith(f"{want.get('understood')} / {want.get('total')} sawaal"), [want, n])
    head = await txt(page, "result-header")
    check("L6 result header says Misfire Mock", "MISFIRE MOCK" in head.upper(), head)
    retry = next((a for a in m.S.get("mock_attempts", []) if a["set"] == MOCK1 and a["attempt"] not in (latest,)), None)
    st, j = m.jl("GET", "my/tests?tab=completed&page=1")
    rows = (j.get("data") or {}).get("items") or []
    retry_row = next((x for x in rows if "retry" in (x.get("title") or "").lower()), None)
    if retry_row:
        ok = await open_result(page, retry_row["id"])
        await page.wait_for_timeout(2500)
        check("L7 a 'Mistake retry' result: no Samajh gaya card", ok and await page.locator(tid("result-misfire-understood")).count() == 0, retry_row.get("title"))
    else:
        check("L7 a 'Mistake retry' row exists on the TEST account", False, [x.get("title") for x in rows])
    await page.goto(BASE + "/tests", wait_until="domcontentloaded")
    await visible(page, "my-tests-exam-filters", 45000)
    await page.wait_for_timeout(3000)
    lab = await txt(page, f"attempt-exam-{latest}")
    check("L8 My Tests labels the website's Misfire Mock", "Misfire Mock" in lab, lab)
    await page.screenshot(path=f"{SHOTS}_tests.jpg", quality=40, type="jpeg")


async def part_make(page):
    """Mock #2 made IN THE APP, taken in the app: 1 right in the app, 3 right + 3 wrong from 'another device', rest left."""
    before = la.counts()
    st, j = m.jl("GET", "my/misfire?status=open&subject=Physics&page=1")
    phys = sorted(((j.get("data") or {}).get("chapters") or []), key=lambda c: c["name"])
    await mock_tab(page)
    await page.click(tid("misfire-web-new"))
    ok = await visible(page, "mock-new-open-physics", 45000)
    check("M1 setup opens as the website's mock", ok and "Misfire Mock banao" in await txt(page, "mock-new-header"), await txt(page, "mock-new-header"))
    await page.click(tid("mock-subject-physics"))
    await visible(page, "mock-chapter-all", 15000)
    rows = await page.locator('[data-testid^="mock-chapter-"][role="checkbox"]').all_inner_texts()
    check("M2 Physics chapters = the website's open chapters with counts", len(rows) >= len(phys) and all(str(c["count"]) in " ".join(rows) for c in phys), [phys, rows])
    await page.click(tid("mock-chapter-all"))   # none
    await page.click(tid("mock-chapter-0"))     # only the first (05 Centre of Mass ...)
    await page.click(tid("mock-count-physics-10"))
    await page.click(tid("mock-subject-chemistry"))
    await page.click(tid("mock-count-chemistry-5"))
    t = await txt(page, "mock-count-time")
    n0 = len(ASKS)
    await page.click(tid("mock-new-bar-go"))
    ok = await visible(page, "set-detail-screen", 45000)
    body = await page.locator("#root").inner_text()
    set_id = page.url.rstrip("/").split("/set/")[-1].split("?")[0]
    a = ASKS[n0] if len(ASKS) > n0 else {}
    check("M3 door C body from the app", a.get("mode") == "misfire" and a.get("exam") == "jee-main" and a.get("counts") == {"Physics": 10, "Chemistry": 5, "Mathematics": 0}
          and a.get("chapters") == {"Physics": [phys[0]["name"]]} and re.match(r"^[0-9a-f-]{36}$", a.get("request_key", "")), a)
    check("M4 the made paper's page opens (Misfire Mock #n, 15 questions)", ok and "Misfire Mock #" in body and "15" in body, [page.url, body[:160].replace("\n", " | ")])
    st, d = m.jl("GET", f"my/sets/{set_id}")
    d = d.get("data") or {}
    check("M5 website made it from the ticked chapter only", d.get("test_kind") == "misfire" and d.get("count") == 15 and (d.get("rules") or {}).get("minutes") == 32
          and (d.get("misfire") or {}).get("given") == {"Physics": 10, "Chemistry": 5, "Mathematics": 0}, [d.get("count"), d.get("rules"), d.get("misfire"), t])
    await mock_tab(page)
    await visible(page, f"misfire-web-{set_id}", 30000)
    first = await page.locator('[data-testid^="misfire-web-"][data-testid$="' + set_id + '"]').count()
    card = await txt(page, f"misfire-web-{set_id}")
    top = await page.locator('[data-testid^="misfire-web-"]').evaluate_all("els => els.map(e => e.dataset.testid).filter(t => /^misfire-web-[0-9a-f-]{36}$/.test(t))")
    check("M6 new mock on top of the Mock tab, not started", first and top[:1] == [f"misfire-web-{set_id}"] and "SHURU NAHI HUA" in card and "Shuru karo" in card and "15 sawaal · 32 min" in card, [top[:2], card.replace("\n", " | ")])
    await page.click(tid(f"misfire-web-{set_id}"))
    ok = await visible(page, "set-start-button", 30000)
    check("M7 a mock not started opens its page with Start", ok and f"/set/{set_id}" in page.url, page.url)
    m.S["mock2"] = {"set": set_id}
    m.save(m.S)


async def card_says(page, set_id, words, wait=20):
    """The card once it says all `words` (a fresh page first paints the phone's copy, then the website's)."""
    card = ""
    for _ in range(wait * 2):
        card = await txt(page, f"misfire-web-{set_id}")
        if all(w in card for w in words):
            break
        await page.wait_for_timeout(500)
    return card


async def part_take(page):
    set_id = m.S["mock2"]["set"]
    before = la.counts()
    row = la.row(set_id) or {}
    if not (row.get("attempt") or {}).get("resumable"):
        await page.goto(BASE + f"/set/{set_id}", wait_until="domcontentloaded")
        await visible(page, "set-start-button", 45000)
        await page.click(tid("set-start-button"))
        ok = await into_player(page)
        check("M8 Start in the app opens the player", ok and "/attempt/" in page.url, page.url)
    aid = (la.row(set_id) or {}).get("attempt", {}).get("id")
    row = la.row(set_id) or {}
    check("M9 list: the attempt is active and resumable", (row.get("attempt") or {}).get("id") == aid and row["attempt"].get("status") == "active" and row["attempt"].get("resumable") is True, row.get("attempt"))
    # In the app, without a reload: from the player back to Misfire's Mock tab (the list is read again on focus).
    await page.goto(BASE + "/misfire?tab=web", wait_until="domcontentloaded")
    await visible(page, f"misfire-web-{set_id}", 45000)
    card = await card_says(page, set_id, ["CHAL RAHA HAI", "Resume"])
    check("M10 Mock tab: CHAL RAHA HAI + Resume", "CHAL RAHA HAI" in card and "Resume" in card, card.replace("\n", " | "))
    await page.click(tid(f"misfire-web-{set_id}"))
    await page.wait_for_timeout(2000)
    ok = await into_player(page)
    check("M11 Resume opens the same attempt", ok and f"/attempt/{aid}" in page.url, page.url)
    await page.click(tid("player-exit-button"))
    if await visible(page, "player-exit-confirm", 8000):
        await page.click(tid("player-exit-confirm"))
    await page.wait_for_timeout(2500)
    await page.goto(BASE + "/misfire?tab=web", wait_until="domcontentloaded")
    await visible(page, f"misfire-web-{set_id}", 45000)
    await page.click(tid(f"misfire-web-{set_id}"))
    await page.wait_for_timeout(2500)
    ok = await into_player(page)
    check("M11b leave the paper, come back by the card: still the same attempt", ok and f"/attempt/{aid}" in page.url, page.url)
    K = la.keys()
    st, d = m.jl("GET", f"attempts/{aid}")
    qs = (d.get("data") or {}).get("questions") or []
    for q in qs:
        q["_attempt"] = aid
    known = [q for q in qs if key_for(q, K)]
    check("M12 every mock question is one of the TEST account's open Misfire questions", len(known) == len(qs) == 15, [len(known), len(qs)])
    q1 = qs[0]
    ok = await answer_in_ui(page, q1, key_for(q1, K))
    check("M13 an answer given in the app reaches the website", ok, [q1.get("number"), q1.get("type")])
    plan = []
    for q in qs[1:]:
        k = key_for(q, K)
        kind = "right" if len([p for p in plan if p[1] == "right"]) < 3 else "wrong" if len([p for p in plan if p[1] == "wrong"]) < 3 else None
        if kind:
            plan.append((q, kind, k if kind == "right" else la.wrong_of(q, k)))
    for q, kind, v in plan:  # "another device" (the TEST account's other session)
        m.jl("PUT", f"attempts/{aid}/answers/{q['id']}", {"value": v, "marked": False, "revision": 1, "request_id": str(uuid.uuid4())})
    await page.reload(wait_until="domcontentloaded")
    await into_player(page)
    await page.wait_for_timeout(2500)
    answered = await txt(page, "player-count-answered")
    check("M14 the player shows all 7 answers after a reload", "7" in answered, answered)
    ok = await submit_in_ui(page)
    check("M15 Submit in the app goes to the result", ok and f"/result/{aid}" in page.url, page.url)
    gate = await visible(page, "share-gate", 20000)
    check("M16 fresh submission: the share card first (as for every paper)", gate)
    ok = await open_result(page, aid)
    await visible(page, "result-misfire-understood", 30000)
    n = await txt(page, "result-misfire-understood-count")
    check("M17 result: 4 / 15 went to Samajh gaya", ok and n.startswith("4 / 15 sawaal"), n)
    await page.screenshot(path=f"{SHOTS}_result.jpg", quality=40, type="jpeg")
    after = la.counts()
    check("M18 Misfire: 4 fewer open, 4 more Samajh gaya (wrong/left stay open)", after["open"] == before["open"] - 4 and after["fixed"] == before["fixed"] + 4, [before, after])
    st, j = m.jl("GET", "my/misfire?status=fixed&page=1")
    fixed_bodies = {la.body(i.get("question") or {}) for i in (j.get("data") or {}).get("items") or []}
    right_bodies = {la.body(q1)} | {la.body(q) for q, k, _ in plan if k == "right"}
    check("M19 exactly the right-answered questions are Samajh gaya", right_bodies <= fixed_bodies, [len(right_bodies & fixed_bodies), len(right_bodies)])
    await page.click(tid("result-misfire-open"))
    ok = await visible(page, "misfire-screen", 30000)
    cnt = ""
    for _ in range(30):  # the phone's copy paints first, the website's count follows
        cnt = await txt(page, "misfire-open-count")
        if str(after["open"]) in cnt:
            break
        await page.wait_for_timeout(500)
    check("M20 'Misfire kholo' opens Misfire with the new open count", ok and str(after["open"]) in cnt, cnt)
    await mock_tab(page)
    await visible(page, f"misfire-web-{set_id}", 30000)
    card = await card_says(page, set_id, ["RESULT", "4 sahi"])
    check("M21 Mock tab: RESULT with 13/60, 4 sahi 3 galat 8 chhode", "RESULT" in card and "13" in card and "/60" in card and "4 sahi" in card and "3 galat" in card and "8 chhode" in card, card.replace("\n", " | "))
    # "Galat + chhode dobara": the untimed retry; its result has no card and Misfire stays as it is.
    await open_result(page, aid)
    await visible(page, "a2-retry-mistakes", 30000)
    await page.click(tid("a2-retry-mistakes"))
    await visible(page, "retry-confirm", 15000)
    await page.click(tid("retry-confirm"))
    for _ in range(30):
        await page.wait_for_timeout(1000)
        if "/attempt/" in page.url:
            break
    rid = page.url.rstrip("/").split("/attempt/")[-1].split("?")[0]
    ok = await into_player(page)
    check("M22 retry opens its own attempt", ok and rid != aid, page.url)
    mid = la.counts()
    st, d = m.jl("GET", f"attempts/{rid}")
    rq = ((d.get("data") or {}).get("questions") or [])
    K = la.keys()
    if rq:
        rq[0]["_attempt"] = rid
        await answer_in_ui(page, rq[0], key_for(rq[0], K))
    ok = await submit_in_ui(page)
    ok = ok and await open_result(page, rid)
    await page.wait_for_timeout(3000)
    st, r = m.jl("GET", f"attempts/{rid}/results?score_version=original")
    check("M23 retry result: no Samajh gaya card, no misfire field", ok and await page.locator(tid("result-misfire-understood")).count() == 0 and "misfire" not in (r.get("data") or {}), (r.get("data") or {}).get("title"))
    check("M24 retry changed nothing in Misfire", la.counts() == mid, [mid, la.counts()])
    row = la.row(set_id) or {}
    check("M25 the list's attempt stays the mock's own attempt (not the retry)", (row.get("attempt") or {}).get("id") == aid, row.get("attempt"))
    m.S["mock2"] = {"set": set_id, "attempt": aid, "retry": rid}
    m.S.setdefault("mock_attempts", []).append({"set": set_id, "attempt": aid})
    m.save(m.S)


async def part_count(page):
    """From Mock #2's result, "Misfire kholo": Misfire's open count reaches the website's number (and how fast)."""
    aid, want = m.S["mock2"].get("attempt") or (la.row(m.S["mock2"]["set"]) or {}).get("attempt", {}).get("id"), la.counts()["open"]
    await open_result(page, aid)
    await visible(page, "result-misfire-open", 30000)
    t0 = time.time()
    await page.click(tid("result-misfire-open"))
    await visible(page, "misfire-screen", 30000)
    seen = []
    for _ in range(40):
        cnt = await txt(page, "misfire-open-count")
        if not seen or seen[-1][1] != cnt:
            seen.append((round(time.time() - t0, 1), cnt))
        if str(want) in cnt:
            break
        await page.wait_for_timeout(500)
    check("M20 'Misfire kholo': open count = the website's", str(want) in (seen[-1][1] if seen else ""), [want, seen])


async def part_expire(page):
    """A 1-question Chemistry mock (2 minutes) left to run out: the list says it is not resumable; the app opens its result."""
    st, j = m.jl("POST", "choice/papers", {"exam": "jee-main", "request_key": str(uuid.uuid4()), "mode": "misfire", "counts": {"Chemistry": 1}})
    made = j.get("data") or {}
    check("E1 a 1-question mock: 2 minutes", st in (200, 201) and made.get("minutes") == 2, [st, made, j.get("error")])
    sid = made.get("set_id")
    st, a = m.jl("POST", f"sets/{sid}/start", {"start_key": str(uuid.uuid4()), "device_checked": True, "preview": False, "get_ready": True})
    aid = (a.get("data") or {}).get("id")
    m.jl("POST", f"attempts/{aid}/begin", {})
    m.S["mock_expire"] = {"set": sid, "attempt": aid}; m.save(m.S)
    seen = []
    for _ in range(40):  # up to ~4 minutes
        time.sleep(6)
        at = (la.row(sid) or {}).get("attempt") or {}
        seen.append(at.get("status"))
        if at.get("status") not in ("active", None):
            break
    check("E2 after the time: not resumable", at.get("resumable") is False and at.get("status") in ("expired", "grading", "completed"), [at, sorted(set(seen), key=str)])
    await mock_tab(page)
    await visible(page, f"misfire-web-{sid}", 30000)
    card = await txt(page, f"misfire-web-{sid}")
    check("E3 card: no Resume, opens the result", "Resume" not in card and ("Result dekho" in card), card.replace("\n", " | "))
    await page.click(tid(f"misfire-web-{sid}"))
    await page.wait_for_timeout(3000)
    check("E4 tap opens /result/<attempt>", f"/result/{aid}" in page.url, page.url)
    ok = await open_result(page, aid)
    body = (await page.locator("#root").inner_text())[:300]
    check("E5 the result (or 'being graded') shows, no error", ok or "grad" in body.lower() or "ban raha" in body.lower(), body.replace("\n", " | "))


async def part_limit(page):
    """Five a day: mocks made today are counted; the sixth is refused in the website's words, shown as they are."""
    st, j = m.jl("GET", "my/misfire/mocks?page=1")
    today = [i for i in (j.get("data") or {}).get("items") or [] if i.get("created_at", 0) > time.time() - 20 * 3600]
    for _ in range(max(0, 5 - len(today))):
        m.jl("POST", "choice/papers", {"exam": "jee-main", "request_key": str(uuid.uuid4()), "mode": "misfire", "counts": {"Mathematics": 1}})
    await page.goto(BASE + "/misfire/mock/new?web=1", wait_until="domcontentloaded")
    await visible(page, "mock-new-open-physics", 45000)
    await page.click(tid("mock-subject-mathematics"))
    await page.click(tid("mock-count-mathematics-5"))
    await page.click(tid("mock-new-bar-go"))
    ok = await visible(page, "mock-making-error", 30000)
    e = await txt(page, "mock-making-error")
    check("T1 sixth mock of the day: the website's 429 sentence word for word", ok and "Aaj ke Misfire Mock poore ho gaye" in e, e)
    await page.screenshot(path=f"{SHOTS}_limit.jpg", quality=40, type="jpeg")
    await page.goto(BASE + "/misfire?tab=mock", wait_until="domcontentloaded")
    ok = await visible(page, "misfire-mock-hero", 45000)
    check("T2 Offline Misfire tab as before", ok and "OFFLINE MISFIRE" in await txt(page, "misfire-mock-hero"))
    await page.goto(BASE + "/choice", wait_until="domcontentloaded")
    await page.wait_for_timeout(6000)
    body = await page.locator("#root").inner_text()
    check("T3 Student Choice still opens with the switch on", "Student Choice" in body or await page.locator(tid("choice-facts")).count() > 0, body[:120].replace("\n", " | "))


async def main():
    async with async_playwright() as pw:
        b = await pw.chromium.launch(executable_path="/usr/bin/chromium", args=["--no-sandbox"])
        ctx = await b.new_context(viewport={"width": 390, "height": 844})
        await setup(ctx)
        page = await ctx.new_page()
        page.on("pageerror", lambda e: ERRORS.append(str(e)[:200]))
        await page.goto(BASE + "/", wait_until="domcontentloaded")
        await shine_helpers.sign_in(page, width=390)
        await page.goto(BASE + "/misfire", wait_until="domcontentloaded")
        for name, fn in (("list", part_list), ("make", part_make), ("take", part_take), ("count", part_count), ("expire", part_expire), ("limit", part_limit)):
            if PART in ("all", name) and not (PART == "all" and name == "count"):
                try:
                    await fn(page)
                except Exception as e:
                    check(f"{name} ran to the end", False, repr(e)[:300])
                    await page.screenshot(path=f"{SHOTS}_{name}_crash.jpg", quality=40, type="jpeg")
        check("Z no page errors", not ERRORS, ERRORS[:3])
        print("WRITES", sorted(set(WRITES))[:40])
        await b.close()
    print(f"\n{sum(1 for _, ok in RES if ok)}/{len(RES)} passed", flush=True)


asyncio.run(main())
