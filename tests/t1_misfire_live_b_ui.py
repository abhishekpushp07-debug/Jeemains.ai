"""T1 (iteration 165): INDEPENDENT live Misfire Mock E2E in the web preview (390x844), TEST account B ONLY (9000004282).
  MF_PHONE=9000004282 MF_PIN=4282 MF_STATE=/tmp/mf_live_b.json python3 t1_misfire_live_b_ui.py <part>
  parts: make (tabs, empty, mock #1 made in the app, card, start, in-app back -> Resume) | take (answer right/wrong, submit,
  result card, Misfire count) | retry | tests | limit | offline
Dream meter writes are answered in the browser. State of this run: /tmp/t1_b.json."""
import asyncio, json, os, re, sys

sys.path.insert(0, "/app/tests")
from dotenv import dotenv_values  # noqa: E402
from playwright.async_api import async_playwright  # noqa: E402
import shine_helpers  # noqa: E402
import misfire_live_e2e_api as m  # noqa: E402
import misfire_live_attempt as la  # noqa: E402

assert m.PHONE == "9000004282" and m.PIN == "4282", "TEST account B only"
shine_helpers.PHONE, shine_helpers.PIN = m.PHONE, m.PIN
BASE = dotenv_values("/app/frontend/.env")["EXPO_PUBLIC_BACKEND_URL"].rstrip("/")
RES, ERRORS, ASKS, WRITES = [], [], [], []
SHOT = "/app/test_reports/artifacts/t1_mf_b"
PART = sys.argv[1]
ST = "/tmp/t1_b.json"
T = json.load(open(ST)) if os.path.exists(ST) else {}


def save():
    json.dump(T, open(ST, "w"))


def check(name, ok, info=""):
    RES.append((name, bool(ok)))
    print(("PASS " if ok else "FAIL ") + name + (" :: " + str(info)[:700] if info != "" else ""), flush=True)


def tid(t):
    return f'[data-testid="{t}"]'


async def vis(page, t, timeout=8000):
    try:
        await page.wait_for_selector(tid(t), state="visible", timeout=timeout); return True
    except Exception:
        return False


async def txt(page, t):
    loc = page.locator(tid(t))
    return (await loc.first.inner_text()).strip() if await loc.count() else ""


async def shot(page, name):
    os.makedirs(os.path.dirname(SHOT), exist_ok=True)
    await page.screenshot(path=f"{SHOT}_{name}.jpg", quality=40, type="jpeg")


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

    async def dream(route):
        if route.request.method == "GET":
            await route.fallback(); return
        WRITES.append("DREAM-BLOCKED " + route.request.method + " " + route.request.url.split("?")[0].replace(BASE, ""))
        await route.fulfill(status=200, content_type="application/json", body='{"ok":true}')
    await ctx.route(re.compile(r".*/api/rf/dream.*"), dream)


async def card_says(page, set_id, words, wait=20):
    card = ""
    for _ in range(wait * 2):
        card = await txt(page, f"misfire-web-{set_id}")
        if all(w in card for w in words):
            break
        await page.wait_for_timeout(500)
    return card


async def marker(page, set_=False):
    if set_:
        await page.evaluate("() => { window.__t1 = 'same-page'; }")
    return await page.evaluate("() => window.__t1 || ''")


async def open_count(page):
    for _ in range(30):
        t = await txt(page, "misfire-open-count")
        n = re.findall(r"\d+", t)
        if n:
            return int(n[0]), t
        await page.wait_for_timeout(500)
    return None, ""


async def part_make(page):
    await page.goto(BASE + "/misfire", wait_until="domcontentloaded")
    ok = await vis(page, "misfire-tab-web", 45000)
    tabs = [await txt(page, x) for x in ("misfire-tab-all", "misfire-tab-web", "misfire-tab-mock")]
    check("K1 Misfire tabs Sab / Mock / Offline Misfire", ok and tabs[0].startswith("Sab") and "Mock" in tabs[1] and "Offline" in tabs[2], tabs)
    n, t = await open_count(page)
    check("K2 misfire-open-count = website open (67)", n == 67, t)
    T["open0"] = n
    await page.click(tid("misfire-tab-web"))
    ok = await vis(page, "misfire-web-hero", 30000) and await vis(page, "misfire-web-empty", 30000)
    check("K3 Mock tab hero + empty state before the first mock", ok, await txt(page, "misfire-web-empty"))
    await shot(page, "1_mock_tab_empty")
    await marker(page, True)
    await page.click(tid("misfire-web-new"))
    ok = await vis(page, "mock-new-open-physics", 45000)
    check("K4 setup header 'Misfire Mock banao'", ok and "Misfire Mock banao" in await txt(page, "mock-new-header"), await txt(page, "mock-new-header"))
    opens = [await txt(page, f"mock-new-open-{s}") for s in ("physics", "chemistry", "mathematics")]
    check("K5 hero open counts P19 C27 M21", opens == ["19", "27", "21"], opens)
    rows = {}
    for s, name in (("chemistry", "07 Ionic Equilibrium"), ("mathematics", "12 Parabola"), ("physics", "10 Surface Tension")):
        await page.click(tid(f"mock-subject-{s}"))
        await vis(page, "mock-chapter-all", 15000)
        rows[s] = await page.locator('[role="checkbox"][data-testid^="mock-chapter-"]').all_inner_texts()
    check("K6 chapter rows (role=checkbox) = website's open chapters", "07 Ionic Equilibrium" in " ".join(rows["chemistry"]) and "27" in " ".join(rows["chemistry"])
          and "12 Parabola" in " ".join(rows["mathematics"]) and "21" in " ".join(rows["mathematics"]) and "10 Surface Tension" in " ".join(rows["physics"]) and "19" in " ".join(rows["physics"])
          and all(len(v) == 2 for v in rows.values()), {k: [r.replace("\n", " ") for r in v] for k, v in rows.items()})
    # untick all -> none hint -> tick the only chapter (= all again)
    await page.click(tid("mock-chapter-all"))
    none = await vis(page, "mock-chapter-none", 5000)
    checked = await page.locator(tid("mock-chapter-0")).get_attribute("aria-checked")
    await page.click(tid("mock-chapter-0"))
    all_on = await page.locator(tid("mock-chapter-all")).get_attribute("aria-checked")
    check("K7 untick all -> hint; tick the only chapter -> all ticked again", none and checked == "false" and all_on == "true", [none, checked, all_on])
    await page.click(tid("mock-count-physics-5"))
    await page.click(tid("mock-count-more"))
    v = await txt(page, "mock-count-value")
    tm = await txt(page, "mock-count-time")
    check("K8 Physics 6 (chip 5 + more), 6*2.4=14.4 -> 15 min", v.startswith("6") and "15" in tm, [v, tm])
    await page.click(tid("mock-subject-chemistry"))
    await page.click(tid("mock-count-chemistry-5"))
    bar = await txt(page, "mock-new-bar")
    check("K9 bar 11 sawaal, 14.4+8=22.4 -> 23 min", "11 sawaal" in bar and "23" in bar, bar.replace("\n", " | "))
    await shot(page, "2_setup")
    n0 = len(ASKS)
    await page.click(tid("mock-new-bar-go"))
    ok = await vis(page, "set-detail-screen", 60000)
    await page.wait_for_timeout(2000)
    body = await page.locator("#root").inner_text()
    set_id = page.url.rstrip("/").split("/set/")[-1].split("?")[0]
    a = ASKS[n0] if len(ASKS) > n0 else {}
    check("K10 POST body: mode misfire, counts P6 C5 M0, NO chapters, uuid key", a.get("mode") == "misfire" and a.get("exam") == "jee-main"
          and a.get("counts") == {"Physics": 6, "Chemistry": 5, "Mathematics": 0} and "chapters" not in a and re.match(r"^[0-9a-f-]{36}$", a.get("request_key", "")), a)
    check("K11 set page shows Misfire Mock #1, 11 questions, 23 min", ok and "Misfire Mock #1" in body and "11" in body and "23" in body, [page.url, body[:300].replace("\n", " | ")])
    await shot(page, "3_set_page")
    st, d = m.jl("GET", f"my/sets/{set_id}")
    d = d.get("data") or {}
    check("K12 website made exactly P6 C5 M0, misfire kind, 23 min", d.get("test_kind") == "misfire" and d.get("count") == 11 and (d.get("rules") or {}).get("minutes") == 23,
          [d.get("title"), d.get("count"), d.get("rules"), d.get("misfire")])
    T["set1"] = set_id; save()
    # back in the app (history) to the Mock tab
    await page.go_back()
    await vis(page, "misfire-web-hero", 20000)
    if not await vis(page, f"misfire-web-{set_id}", 5000):
        await page.click(tid("misfire-tab-web")) if await page.locator(tid("misfire-tab-web")).count() else None
    card = await card_says(page, set_id, ["SHURU NAHI HUA", "Shuru karo", "11 sawaal · 23 min"])
    check("K13 card not started: SHURU NAHI HUA + Shuru karo + '11 sawaal · 23 min'", all(w in card for w in ["SHURU NAHI HUA", "Shuru karo", "11 sawaal · 23 min", "Misfire Mock #1"]), [card.replace("\n", " | "), page.url, await marker(page)])
    await page.click(tid(f"misfire-web-{set_id}"))
    ok = await vis(page, "set-start-button", 30000)
    check("K14 card opens /set page with Start", ok and f"/set/{set_id}" in page.url, page.url)
    await page.click(tid("set-start-button"))
    if await vis(page, "get-ready-begin", 30000):
        await page.click(tid("get-ready-begin"))
    ok = await vis(page, "player-screen", 30000)
    aid = page.url.split("/attempt/")[-1].split("?")[0].split("/")[0] if "/attempt/" in page.url else None
    check("K15 Start -> get ready -> player", ok and aid, page.url)
    T["att1"] = aid; save()
    await marker(page, True)
    await page.click(tid("player-exit-button"))
    if await vis(page, "player-exit-confirm", 8000):
        await page.click(tid("player-exit-confirm"))
    await page.wait_for_timeout(2500)
    print("after exit:", page.url)
    for _ in range(4):  # in-app back until the Misfire screen
        if "/misfire" in page.url:
            break
        await page.go_back(); await page.wait_for_timeout(1500)
    if await page.locator(tid("misfire-tab-web")).count():
        await page.click(tid("misfire-tab-web"))
    await vis(page, f"misfire-web-{set_id}", 20000)
    card = await card_says(page, set_id, ["CHAL RAHA HAI", "Resume"])
    mk = await marker(page)
    check("K16 in-app back (no reload) card says CHAL RAHA HAI + Resume", "CHAL RAHA HAI" in card and "Resume" in card and mk == "same-page", [card.replace("\n", " | "), page.url, mk])
    await shot(page, "4_card_resume")
    await page.click(tid(f"misfire-web-{set_id}"))
    await page.wait_for_timeout(2000)
    if await vis(page, "get-ready-begin", 5000):
        await page.click(tid("get-ready-begin"))
    ok = await vis(page, "player-screen", 30000)
    check("K17 Resume opens the same /attempt/<id>", ok and f"/attempt/{aid}" in page.url, page.url)


async def part_take(page):
    set_id, aid = T["set1"], T["att1"]
    K = la.keys()
    st, d = m.jl("GET", f"attempts/{aid}")
    qs = (d.get("data") or {}).get("questions") or []
    known = [q for q in qs if (K.get(q["id"]) or K.get(la.body(q)))]
    check("T1 all mock questions match account B's earlier questions by text", len(known) == len(qs) == 11, [len(known), len(qs)])
    await page.goto(BASE + f"/attempt/{aid}", wait_until="domcontentloaded")
    if await vis(page, "get-ready-begin", 20000):
        await page.click(tid("get-ready-begin"))
    await vis(page, "player-screen", 30000)
    plan = {}  # index -> (kind, value)
    for i, q in enumerate(qs):
        r = K.get(q["id"]) or K.get(la.body(q))
        if r is None:
            continue
        if sum(1 for k, _ in plan.values() if k == "right") < 4:
            plan[i] = ("right", r)
        elif sum(1 for k, _ in plan.values() if k == "wrong") < 3:
            plan[i] = ("wrong", la.wrong_of(q, r))
    print("plan", {i: (k, v, qs[i].get("type"), qs[i].get("subject")) for i, (k, v) in plan.items()})
    st, d0 = m.jl("GET", f"attempts/{aid}")
    have = {k: v.get("value") for k, v in ((d0.get("data") or {}).get("answers") or {}).items()}
    for i, q in enumerate(qs):
        if i in plan and str(have.get(q["id"])) != str(plan[i][1]):  # an option tapped again could clear it
            kind, v = plan[i]
            await page.click(tid("player-palette-button"))
            await vis(page, "player-palette-sheet", 8000)
            sub = tid(f"palette-subject-{q['subject'].lower()}")
            if await page.locator(sub).count():
                await page.click(sub); await page.wait_for_timeout(500)
            await page.click(tid(f"palette-q-{q['number']}"))
            await page.wait_for_timeout(800)
            if q.get("type") == "integer":
                await page.fill(tid("player-integer-input"), v)
            else:
                await page.click(tid(f"player-option-{v}"))
            await page.wait_for_timeout(700)
            # Save & Next / Next subject saves it
            if await page.locator(tid("player-next-button")).count():
                await page.click(tid("player-next-button"))
            elif await page.locator(tid("player-next-subject")).count():
                await page.click(tid("player-next-subject"))
            await page.wait_for_timeout(800)
    saved = {}
    for _ in range(20):
        await page.wait_for_timeout(1000)
        st, d = m.jl("GET", f"attempts/{aid}")
        saved = {k: v.get("value") for k, v in ((d.get("data") or {}).get("answers") or {}).items() if v.get("value") not in (None, "")}
        if len(saved) >= len(plan):
            break
    want = {qs[i]["id"]: v for i, (k, v) in plan.items()}
    check("T2 answers typed in the player saved on the website (4 right, 3 wrong)", all(str(saved.get(k)) == str(v) for k, v in want.items()) and len(saved) == len(want), [saved, want])
    T["right"] = sum(1 for k, _ in plan.values() if k == "right"); save()
    await page.click(tid("player-submit-top"))
    await vis(page, "player-submit-sheet", 15000)
    await page.click(tid("player-confirm-submit"))
    for _ in range(60):
        await page.wait_for_timeout(1000)
        if "/result/" in page.url:
            break
    gate = await vis(page, "share-gate", 30000)
    check("T3 submit -> /result, locked by share-gate", "/result/" in page.url and gate, page.url)
    res = {}
    for _ in range(20):
        st, r = m.jl("GET", f"attempts/{aid}/results?score_version=original")
        res = r.get("data") or {}
        if st == 200 and res.get("misfire"):
            break
        await page.wait_for_timeout(3000)
    print("website result misfire:", res.get("misfire"), "summary", {k: (res.get("summary") or {}).get(k) for k in ("correct", "incorrect", "skipped")})
    T["web_misfire"] = res.get("misfire"); save()
    await page.evaluate("id => { for (const k of Object.keys(localStorage)) if (k.includes('share_gate.' + id)) localStorage.removeItem(k); }", aid)
    await page.reload(wait_until="domcontentloaded")
    ok = await vis(page, "result-misfire-understood", 60000)
    eyebrow = (await page.locator("#root").inner_text())[:400]
    cnt = await txt(page, "result-misfire-understood-count")
    u, tot = (res.get("misfire") or {}).get("understood"), (res.get("misfire") or {}).get("total")
    check("T4 header eyebrow JEE MAIN · MISFIRE MOCK", "JEE MAIN · MISFIRE MOCK" in eyebrow.upper(), eyebrow.replace("\n", " | ")[:200])
    check("T5 understood card = website misfire field (4/11)", ok and cnt == f"{u} / {tot} sawaal “Samajh gaya” mein chale gaye" and u == 4 and tot == 11, [cnt, res.get("misfire")])
    await shot(page, "5_result")
    await page.click(tid("result-misfire-open"))
    ok = await vis(page, "misfire-tab-all", 30000)
    n, t = await open_count(page)
    check("T6 'Misfire kholo' opens Misfire; open count dropped by exactly understood", ok and "/misfire" in page.url and n == 67 - (u or 0), [page.url, t, la.counts()])


async def part_retry(page):
    aid = T["att1"]
    before = la.counts()
    await page.evaluate("id => { for (const k of Object.keys(localStorage)) if (k.includes('share_gate.' + id)) localStorage.removeItem(k); }", aid)
    await page.goto(BASE + f"/result/{aid}", wait_until="domcontentloaded")
    await vis(page, "result-misfire-understood", 60000)
    ok = await vis(page, "a2-retry-mistakes", 30000)
    if not ok:
        await page.locator(tid("a2-retry-mistakes")).scroll_into_view_if_needed()
    await page.click(tid("a2-retry-mistakes"))
    await vis(page, "retry-confirm", 15000)
    await page.click(tid("retry-confirm"))
    for _ in range(40):
        await page.wait_for_timeout(1000)
        if "/attempt/" in page.url and aid not in page.url:
            break
    rid = page.url.split("/attempt/")[-1].split("?")[0].split("/")[0] if "/attempt/" in page.url else None
    check("R1 retry opens its own /attempt/<id>", rid and rid != aid, page.url)
    T["retry"] = rid; save()
    if await vis(page, "get-ready-begin", 10000):
        await page.click(tid("get-ready-begin"))
    await vis(page, "player-screen", 30000)
    st, d = m.jl("GET", f"attempts/{rid}")
    qs = (d.get("data") or {}).get("questions") or []
    K = la.keys()
    if qs:  # answer the first one right
        q = qs[0]; r = K.get(q["id"]) or K.get(la.body(q))
        if r and q.get("type") != "integer":
            await page.click(tid(f"player-option-{r}"))
        elif r:
            await page.fill(tid("player-integer-input"), r)
        await page.wait_for_timeout(2500)
    print("retry questions", len(qs))
    await page.click(tid("player-submit-top"))
    await vis(page, "player-submit-sheet", 15000)
    await page.click(tid("player-confirm-submit"))
    for _ in range(60):
        await page.wait_for_timeout(1000)
        if "/result/" in page.url:
            break
    res = {}
    for _ in range(15):
        st, r = m.jl("GET", f"attempts/{rid}/results?score_version=original")
        res = r.get("data") or {}
        if st == 200 and res.get("summary"):
            break
        await page.wait_for_timeout(3000)
    check("R2 retry result (website) has NO misfire field", st == 200 and "misfire" not in res, [st, res.get("misfire"), res.get("test_kind")])
    await page.evaluate("id => { for (const k of Object.keys(localStorage)) if (k.includes('share_gate.' + id)) localStorage.removeItem(k); }", rid)
    await page.reload(wait_until="domcontentloaded")
    await vis(page, "result-analysis-panel", 60000)
    await page.wait_for_timeout(3000)
    check("R3 retry result page has no result-misfire-understood card", "/result/" in page.url and await page.locator(tid("result-misfire-understood")).count() == 0, page.url)
    after = la.counts()
    check("R4 Misfire counts unchanged by the retry", after == before, [before, after])
    await page.goto(BASE + "/misfire?tab=web", wait_until="domcontentloaded")
    await vis(page, f"misfire-web-{T['set1']}", 45000)
    card = await card_says(page, T["set1"], ["RESULT"])
    row = la.row(T["set1"]) or {}
    check("R5 Mock tab card still shows the mock's own attempt (RESULT, 4 sahi), opens /result/<att1>", "RESULT" in card and "4 sahi" in card and (row.get("attempt") or {}).get("id") == aid, [card.replace("\n", " | "), (row.get("attempt") or {}).get("id")])
    await page.click(tid(f"misfire-web-{T['set1']}"))
    await page.wait_for_timeout(3000)
    check("R6 card opens the mock's result", f"/result/{aid}" in page.url, page.url)


async def part_tests(page):
    await page.goto(BASE + "/tests", wait_until="domcontentloaded")
    ids = [T["att1"]] + ([T["retry"]] if T.get("retry") else [])
    for i in ids:
        ok = await vis(page, f"attempt-exam-{i}", 45000)
        if not ok:
            for t in ("tests-tab-completed", "tests-tab-done"):
                if await page.locator(tid(t)).count():
                    await page.click(tid(t)); ok = await vis(page, f"attempt-exam-{i}", 20000); break
        check(f"MT My Tests row {i[:8]} labelled 'JEE Main · Misfire Mock'", ok and "JEE Main · Misfire Mock" in await txt(page, f"attempt-exam-{i}"), await txt(page, f"attempt-exam-{i}"))
    await shot(page, "6_tests")


async def part_offline(page):
    await page.goto(BASE + "/misfire", wait_until="domcontentloaded")
    await vis(page, "misfire-tab-mock", 45000)
    await page.click(tid("misfire-tab-mock"))
    ok = await vis(page, "misfire-mock-hero", 20000)
    check("O1 Offline Misfire tab hero 'OFFLINE MISFIRE'", ok and "OFFLINE MISFIRE" in (await txt(page, "misfire-mock-hero")).upper(), (await txt(page, "misfire-mock-hero"))[:120])
    await page.goto(BASE + "/misfire/mock/new", wait_until="domcontentloaded")
    ok = await vis(page, "mock-new-header", 45000)
    check("O2 /misfire/mock/new (no ?web) = 'Offline Misfire banao'", ok and "Offline Misfire banao" in await txt(page, "mock-new-header"), await txt(page, "mock-new-header"))
    await page.goto(BASE + "/choice", wait_until="domcontentloaded")
    await page.wait_for_timeout(8000)
    body = (await page.locator("#root").inner_text())[:400]
    tids = await page.locator('[data-testid^="choice-"]').evaluate_all("els => els.slice(0,15).map(e => e.dataset.testid)")
    check("O3 Student Choice /choice opens (pick/random ON)", "/choice" in page.url and len(tids) > 0, [tids, body.replace("\n", " | ")[:200]])
    await shot(page, "7_choice")


async def part_limit(page):
    await page.goto(BASE + "/misfire?tab=web", wait_until="domcontentloaded")
    await vis(page, "misfire-web-hero", 45000)
    await page.wait_for_timeout(4000)
    titles = await page.locator('[data-testid^="misfire-web-title-"]').all_inner_texts()
    check("L0 Mock tab newest first #5..#1", titles == [f"Misfire Mock #{i}" for i in (5, 4, 3, 2, 1)], titles)
    c3 = await txt(page, "misfire-web-size-881ef167-0aa3-5d10-8bda-0f32b52d033c")
    check("L0b #3 card uses given (15 of 25 asked) · 36 min", c3 == "15 sawaal · 36 min", c3)
    await shot(page, "8a_list")
    n0 = len(ASKS)
    await page.goto(BASE + "/misfire/mock/new?web=1", wait_until="domcontentloaded")
    await vis(page, "mock-new-open-physics", 45000)
    await page.click(tid("mock-subject-mathematics"))
    await page.click(tid("mock-count-mathematics-5"))
    await page.click(tid("mock-new-bar-go"))
    ok = await vis(page, "mock-making-error", 45000)
    err = await txt(page, "mock-making-error")
    check("L1 6th mock of the day -> 429 sentence word for word", ok and "Aaj ke Misfire Mock poore ho gaye. Kal naya mock banao." in err and "/misfire/mock/new" in page.url, [err, ASKS[n0:]])
    await shot(page, "8_limit")


async def part_count(page):
    aid = T["att1"]
    print("website summary:", la.counts())
    await page.evaluate("id => { for (const k of Object.keys(localStorage)) if (k.includes('share_gate.' + id)) localStorage.removeItem(k); }", aid)
    await page.goto(BASE + f"/result/{aid}", wait_until="domcontentloaded")
    await vis(page, "result-misfire-open", 60000)
    await page.click(tid("result-misfire-open"))
    seq = []
    for i in range(40):
        t = await txt(page, "misfire-open-count")
        if not seq or seq[-1][1] != t:
            seq.append((i * 0.5, t))
        await page.wait_for_timeout(500)
    print("after Misfire kholo (s, text):", seq, page.url)
    check("C1 open count after 'Misfire kholo' settles at website open", seq and str(la.counts()["open"]) in seq[-1][1], seq)
    await page.goto(BASE + "/misfire", wait_until="domcontentloaded")
    seq = []
    for i in range(40):
        t = await txt(page, "misfire-open-count")
        if not seq or seq[-1][1] != t:
            seq.append((i * 0.5, t))
        await page.wait_for_timeout(500)
    print("fresh /misfire (s, text):", seq)
    ls = await page.evaluate("() => Object.keys(localStorage).filter(k => k.includes('summary')).map(k => k + '=' + localStorage.getItem(k).slice(0, 160))")
    print("localStorage summary keys:", ls)
    check("C2 fresh /misfire open count = website open", seq and str(la.counts()["open"]) in seq[-1][1], seq)


async def part_repro(page):
    """Mock #2 in one browser session that already holds Misfire's summary: is the open count fresh after 'Misfire kholo'?"""
    await page.goto(BASE + "/misfire", wait_until="domcontentloaded")
    n, t = await open_count(page)
    print("before:", t, la.counts())
    await page.click(tid("misfire-tab-web"))
    await vis(page, "misfire-web-new", 30000)
    await page.click(tid("misfire-web-new"))
    await vis(page, "mock-new-open-physics", 45000)
    await page.click(tid("mock-subject-mathematics"))
    await page.click(tid("mock-count-mathematics-5"))
    bar = await txt(page, "mock-new-bar")
    check("P1 Maths 5 -> 16 min (3.2/q)", "5 sawaal" in bar and "16 min" in bar, bar.replace("\n", " | "))
    await page.click(tid("mock-new-bar-go"))
    await vis(page, "set-detail-screen", 60000)
    body = await page.locator("#root").inner_text()
    set_id = page.url.rstrip("/").split("/set/")[-1].split("?")[0]
    check("P2 Misfire Mock #2 page", "Misfire Mock #2" in body, body[:120].replace("\n", " | "))
    T["set2"] = set_id; save()
    await page.click(tid("set-start-button"))
    if await vis(page, "get-ready-begin", 30000):
        await page.click(tid("get-ready-begin"))
    await vis(page, "player-screen", 30000)
    aid = page.url.split("/attempt/")[-1].split("?")[0].split("/")[0]
    T["att2"] = aid; save()
    K = la.keys()
    st, d = m.jl("GET", f"attempts/{aid}")
    qs = (d.get("data") or {}).get("questions") or []
    done = 0
    for q in qs[:2]:
        r = K.get(q["id"]) or K.get(la.body(q))
        await page.click(tid("player-palette-button")); await vis(page, "player-palette-sheet", 8000)
        await page.click(tid(f"palette-q-{q['number']}")); await page.wait_for_timeout(800)
        if q.get("type") == "integer":
            await page.fill(tid("player-integer-input"), r)
        else:
            await page.click(tid(f"player-option-{r}"))
        await page.wait_for_timeout(700)
        if await page.locator(tid("player-next-button")).count():
            await page.click(tid("player-next-button"))
        await page.wait_for_timeout(1500)
        done += 1
    await page.wait_for_timeout(2500)
    await page.click(tid("player-submit-top"))
    await vis(page, "player-submit-sheet", 15000)
    await page.click(tid("player-confirm-submit"))
    for _ in range(60):
        await page.wait_for_timeout(1000)
        if "/result/" in page.url:
            break
    res = {}
    for _ in range(20):
        st, r = m.jl("GET", f"attempts/{aid}/results?score_version=original")
        res = r.get("data") or {}
        if st == 200 and res.get("misfire"):
            break
        await page.wait_for_timeout(3000)
    print("website misfire:", res.get("misfire"), "website summary now:", la.counts())
    await page.evaluate("id => { for (const k of Object.keys(localStorage)) if (k.includes('share_gate.' + id)) localStorage.removeItem(k); }", aid)
    await page.reload(wait_until="domcontentloaded")
    await vis(page, "result-misfire-open", 60000)
    cnt = await txt(page, "result-misfire-understood-count")
    check("P3 result card = website misfire", cnt.startswith(f"{(res.get('misfire') or {}).get('understood')} / {(res.get('misfire') or {}).get('total')} "), [cnt, res.get("misfire")])
    await page.click(tid("result-misfire-open"))
    seq = []
    for i in range(40):
        t = await txt(page, "misfire-open-count")
        if not seq or seq[-1][1] != t:
            seq.append((i * 0.5, t))
        await page.wait_for_timeout(500)
    web = la.counts()["open"]
    print("after Misfire kholo:", seq, "website:", web)
    check("P4 same-session open count after 'Misfire kholo' = website open (dropped by understood)", seq and seq[-1][1] == f"{web} OPEN", [seq, web])
    # in-app back to the result and forward again
    await shot(page, "9_after_open")


async def part_expire(page):
    sid, aid = "a2e2ab2b-6d98-5c1e-bf54-9df083527664", "a8b33edf-a7c7-4800-8dde-ff48cad3a876"
    row = la.row(sid) or {}
    print("website row #4:", row.get("attempt"))
    await page.goto(BASE + "/misfire?tab=web", wait_until="domcontentloaded")
    await vis(page, f"misfire-web-{sid}", 45000)
    card = await card_says(page, sid, ["Result"], 15)
    check("E1 expired mock card: not Resume, says RESULT / Result dekho", "Resume" not in card and "CHAL RAHA HAI" not in card and "Result dekho" in card, card.replace("\n", " | "))
    await page.click(tid(f"misfire-web-{sid}"))
    await page.wait_for_timeout(4000)
    check("E2 expired card opens /result/<attempt>", f"/result/{aid}" in page.url, page.url)
    await page.wait_for_timeout(6000)
    await shot(page, "10_expired_result")
    body = (await page.locator("#root").inner_text())[:300]
    print("expired result page:", body.replace("\n", " | "))


async def part_sizes(page):
    out = {}
    await page.goto(BASE + "/misfire?tab=web", wait_until="domcontentloaded")
    await vis(page, "misfire-web-hero", 45000); await page.wait_for_timeout(3000)
    for t in ("misfire-tab-all", "misfire-tab-web", "misfire-tab-mock", "misfire-web-new", "misfire-back"):
        out[t] = await page.locator(tid(t)).first.bounding_box()
    await page.goto(BASE + "/misfire/mock/new?web=1", wait_until="domcontentloaded")
    await vis(page, "mock-new-open-physics", 45000)
    for t in ("mock-subject-physics", "mock-count-physics-0", "mock-count-physics-5", "mock-count-less", "mock-count-more", "mock-chapter-all", "mock-chapter-0", "mock-new-bar-go", "mock-new-back"):
        out[t] = await page.locator(tid(t)).first.bounding_box()
    small = {k: (round(v["width"]), round(v["height"])) for k, v in out.items() if v and (v["width"] < 44 or v["height"] < 44)}
    print({k: (round(v["width"]), round(v["height"])) if v else None for k, v in out.items()})
    check("D1 touch targets >= 44px", not small, small)


async def main():
    async with async_playwright() as pw:
        b = await pw.chromium.launch(executable_path="/usr/bin/chromium", args=["--no-sandbox"])
        ctx = await b.new_context(viewport={"width": 390, "height": 844})
        await setup(ctx)
        page = await ctx.new_page()
        page.on("pageerror", lambda e: ERRORS.append(str(e)[:200]))
        await page.goto(BASE + "/", wait_until="domcontentloaded")
        await shine_helpers.sign_in(page, aits=None, board=False, width=390)
        fn = {"make": part_make, "take": part_take, "retry": part_retry, "tests": part_tests, "offline": part_offline, "limit": part_limit, "count": part_count, "repro": part_repro, "expire": part_expire, "sizes": part_sizes}[PART]
        try:
            await fn(page)
        except Exception as e:
            check(f"{PART} ran to the end", False, repr(e)[:400])
            await shot(page, f"crash_{PART}")
        check("Z no page errors", not ERRORS, ERRORS[:3])
        print("WRITES", sorted(set(WRITES))[:40])
        await b.close()
    print(f"\n{sum(1 for _, ok in RES if ok)}/{len(RES)} passed", flush=True)


asyncio.run(main())
