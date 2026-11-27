# Rapid Fire from the phone's own cards, in a browser (27 Nov 2026): the cards come to the phone by themselves, a Solo
# Sprint starts from them when the server is not heard (no line / a slow line), a round played without a line is kept and
# goes up by itself, and the app opens a Rapid Fire door when it starts without a line.
#   python3 /app/tests/offline_rapid_check.py            the app (web preview)
#   python3 /app/tests/offline_rapid_check.py arena      the browser copy of Rapid Fire (/api/arena)
#   ... small                                            the same on a 360 x 640 phone
# The QA learner is the owner's real account, so NOTHING is written for it: a round that goes up (POST /api/rf/sessions/offline,
# POST /api/rf/sessions/<id>/complete) is read and answered by the browser, starting a sprint on the server is answered by the
# browser too, and every other write under /api/rf/{sessions,duels,challenges,cups} is stopped and counted (there must be none).
# "No line" is made by the browser: every call to /api/jl, /api/rf and /api/app is cut, the page itself still loads.
import asyncio
import json
import re
import sys
from pathlib import Path

from dotenv import dotenv_values
from playwright.async_api import async_playwright

sys.path.insert(0, "/app/tests")
from shine_helpers import sign_in  # noqa: E402

BASE = dotenv_values("/app/frontend/.env")["EXPO_PUBLIC_BACKEND_URL"].rstrip("/")
ARENA, SMALL = "arena" in sys.argv[1:], "small" in sys.argv[1:]
if ARENA:
    BASE += "/api/arena"
W, H = (360, 640) if SMALL else (390, 844)
TAG = ("arena" if ARENA else "app") + ("_small" if SMALL else "")
OUT = Path("/tmp/offline_runs"); OUT.mkdir(exist_ok=True)
RULES = ("Rendered more hooks", "Rendered fewer hooks", "order of Hooks", "Cannot update a component", "Maximum update depth", "state update on an unmounted", "Each child in a list")
checks = []
seen = {"offline": [], "complete": [], "create": [], "stopped": []}
line = {"create": "dead", "complete": "dead", "standin": None}  # how the browser answers for the server
REWARD = {"xp": 210, "coins": 44, "played": True, "level_up": False, "level_after": 3, "diamonds": {}}

T = """(id) => { const el = document.querySelector(`[data-testid="${id}"]`); return el ? (el.innerText || '').replace(/[\\u{F0000}-\\u{FFFFD}]/gu, '').trim().replace(/\\s*\\n\\s*/g, ' ') : null; }"""
KEPT = """() => { const read = (k) => { try { return JSON.parse(JSON.parse(localStorage.getItem(k) || 'null') || 'null'); } catch { return null; } };
  const user = read('jl_user'), uid = user?.id || read('kept.confirmed.v1')?.uid || '';
  const ids = read('kept.rounds.' + uid) || [];
  return { uid, bank: read('kept.bank.JEE.v1'), stamp: read('kept.confirmed.v1'), rounds: ids.map((id) => read('kept.round.' + id)), seen: (read('kept.bank.seen.v1') || []).length }; }"""
PARTS = """() => new Promise((resolve) => { const r = indexedDB.open('jeelive-kept-v1'); r.onerror = () => resolve(null);
  r.onsuccess = () => { const tx = r.result.transaction('files', 'readonly'), s = tx.objectStore('files'), keys = s.getAllKeys(), all = s.getAll();
    tx.oncomplete = () => resolve(Object.fromEntries(keys.result.map((k, i) => { const body = JSON.parse(all.result[i]);
      return [body.subject, body.cards.map((c) => ({ id: c.id, answer: c.answer, chapter: c.chapter, topic: c.topic, prompt: c.prompt, formula: c.formula, options: c.options, explain: c.explain }))]; }))); }; })"""


def check(name, ok, detail=""):
    checks.append(bool(ok))
    print(("PASS " if ok else "FAIL ") + name + (" | " + str(detail) if detail != "" else ""))


async def text(page, test_id):
    return await page.evaluate(T, test_id)


async def stand_ins(page):
    async def sessions(route):
        req = route.request
        path = req.url.split("/api/rf/sessions", 1)[1].split("?")[0]
        if req.method == "GET":
            await route.continue_()
        elif req.method == "POST" and path == "/offline":
            body = json.loads(req.post_data or "{}")
            seen["offline"].append(body)
            n = len(body.get("card_ids") or [])
            await route.fulfill(status=200, content_type="application/json", body=json.dumps({"id": "standin-" + body.get("request_id", "")[:8], "status": "completed", "mode": "fresh", "exam": "JEE",
                                "card_ids": body.get("card_ids"), "results": [], "summary": {"total": n, "correct": 0, "answered": 0}, "reward": REWARD}))
        elif req.method == "POST" and path == "":
            seen["create"].append({"body": json.loads(req.post_data or "{}"), "how": line["create"]})
            if line["create"] == "dead":
                await route.abort()
            elif line["create"] == "slow":
                await asyncio.sleep(12)
                try:
                    await route.abort()
                except Exception:
                    pass  # the page has left for the phone's cards
            elif line["create"] == "refuse":
                await route.fulfill(status=400, content_type="application/json", body=json.dumps({"detail": "Stand-in: the server says no."}))
            else:  # "standin": a sprint the server "dealt" (30 kept cards), so its end can be played
                await route.fulfill(status=200, content_type="application/json", body=json.dumps(line["standin"]))
        elif req.method == "POST" and path.endswith("/complete"):
            seen["complete"].append({"path": path, "body": json.loads(req.post_data or "{}"), "how": line["complete"]})
            if line["complete"] == "dead":
                await route.abort()
            else:
                await route.fulfill(status=200, content_type="application/json", body=json.dumps({**line["standin"], "status": "completed", "results": [], "summary": {"total": 30, "correct": 0, "answered": 0}, "reward": REWARD}))
        else:
            seen["stopped"].append(f"{req.method} /sessions{path}")
            await route.abort()

    async def others(route):
        req = route.request
        if req.method == "GET":
            await route.continue_()
        else:
            seen["stopped"].append(f"{req.method} {req.url.split('/api/rf', 1)[1].split('?')[0]}")
            await route.abort()

    await page.route(re.compile(r".*/api/rf/sessions(/|\?|$).*"), sessions)
    for kind in ("duels", "challenges", "cups"):
        await page.route(re.compile(rf".*/api/rf/{kind}(/|\?|$).*"), others)


NO_LINE = re.compile(r".*/api/(jl|rf|app)/.*")


async def cut(route):
    await route.abort()


async def lobby(page):
    await page.wait_for_selector('[data-testid="rapid-fire-home"]', timeout=60000)
    await page.wait_for_selector('[data-testid="rf-start-button"]', timeout=30000)
    try:
        await page.wait_for_selector('[data-testid="rf-daily-popup-exit"]', timeout=4000)
        await page.click('[data-testid="rf-daily-popup-exit"]')
        await page.wait_for_selector('[data-testid="rf-daily-popup"]', state="detached", timeout=15000)
    except Exception:
        pass


async def pick_and_start(page, subject, opener):
    """Opens the picker from `opener`, ticks every chapter of one subject and starts."""
    await page.click(f'[data-testid="{opener}"]')
    await page.wait_for_selector('[data-testid="rf-scope-sheet"]', timeout=15000)
    await page.wait_for_selector('[data-testid^="rf-scope-chapter-"]', timeout=30000)
    await page.wait_for_timeout(500)
    await page.click(f'[data-testid="rf-scope-tab-{subject}"]')
    await page.wait_for_timeout(300)
    await page.click('[data-testid="rf-scope-select-all"]')
    await page.wait_for_timeout(300)
    await page.click('[data-testid="rf-scope-done"]')


async def play(page, plan, counter="rf-card-counter"):
    """Plays the round in view: plan(k) = an option number, or "skip". Returns what the screen said after each card."""
    said = []
    total = int(re.search(r"(\d+)\s*$", (await text(page, counter)) or "0").group(1))
    for k in range(total):
        await page.wait_for_function(f"""() => /^(Card )?{k + 1} (of|\\/) /.test((document.querySelector('[data-testid="{counter}"]')?.innerText || '').trim())""", timeout=15000)
        move = plan(k)
        if move == "skip":
            await page.click('[data-testid="rf-skip-button"]')
            said.append("skipped")
            continue
        await page.click(f'[data-testid="rf-option-{move}"]')
        await page.wait_for_selector('[data-testid="rf-feedback"]', timeout=5000)
        said.append("correct" if "Correct" in ((await text(page, "rf-feedback")) or "") else "incorrect")
        await page.click('[data-testid="rf-next-button"]')
    return said


async def main():
    async with async_playwright() as pw:
        browser = await pw.chromium.launch(executable_path="/usr/bin/chromium", args=["--no-sandbox"])
        page = await (await browser.new_context(viewport={"width": W, "height": H})).new_page()
        errors = []
        page.on("console", lambda m: errors.append(m.text[:200]) if m.type == "error" and any(r in m.text for r in RULES) else None)
        page.on("pageerror", lambda e: errors.append("pageerror: " + str(e)[:200]))
        await stand_ins(page)
        await page.goto(BASE + "/entry", wait_until="domcontentloaded", timeout=90000)
        await sign_in(page, aits=None, board=False, width=W, height=H, landing="rapid-fire-home" if ARENA else "home-tile-choice")

        # A. The cards come to the phone by themselves after sign-in
        await page.wait_for_function("""() => { try { const b = JSON.parse(JSON.parse(localStorage.getItem('kept.bank.JEE.v1'))); return b.parts.length === 5 && b.checked > 0; } catch { return false; } }""", timeout=120000)
        kept = await page.evaluate(KEPT)
        cat = await page.evaluate("fetch('/api/rf/catalog?exam=JEE').then((r) => r.json())")
        want = {s["name"]: s["total"] for s in cat["subjects"]}
        got = {p["subject"]: p["cards"] for p in kept["bank"]["parts"]}
        check("A1 every subject's cards are on the phone, in the arena's order", list(got) == ["Physics", "Chemistry", "Mathematics", "English", "Logical Reasoning"] and got == want, got)
        parts = await page.evaluate(PARTS)
        bank = {c["id"]: {**c, "subject": subject} for subject, cards in parts.items() for c in cards}
        check("A2 the kept files hold exactly those cards", {s: len(c) for s, c in parts.items()} == want and len(bank) == sum(want.values()), len(bank))
        check("A3 the phone notes whose session was confirmed", kept["stamp"] and kept["stamp"]["uid"] == kept["uid"] and kept["uid"], "")
        uid = kept["uid"]

        # B. The Account screen says so
        await page.goto(BASE + "/account", wait_until="domcontentloaded")
        await page.wait_for_selector('[data-testid="account-offline-rapid"]', timeout=45000)
        said = await text(page, "account-offline-rapid")
        check("B1 Account: the cards on this phone", f"{sum(want.values()):,}" in (said or "") and "ready" in (said or ""), said)
        await page.screenshot(path=str(OUT / f"{TAG}_1_account.jpeg"), type="jpeg", quality=45)

        # C. A Solo Sprint whose server is not heard starts from the phone's cards
        await page.goto(BASE + "/(tabs)/rapid", wait_until="domcontentloaded")
        await lobby(page)
        line["create"] = "dead"
        await pick_and_start(page, "physics", "rf-start-button")
        await page.wait_for_selector('[data-testid="rf-plain-screen"] [data-testid="rf-card"]', timeout=20000)
        check("C1 no line at the start: the sprint is dealt on the phone", "/offline/rapid" in page.url and seen["create"][-1]["body"]["picks"] == [{"subject": "Physics", "chapter": None}], page.url[-60:])
        counter = await text(page, "rf-card-counter")
        check("C2 a full round of the chosen size", bool(re.search(r"1 (of|/) (30|50|100)$", counter or "")), counter)
        check("C3 it says what is played", (await text(page, "rf-session-exam") or "").startswith("JEE · Physics · "), await text(page, "rf-session-exam"))
        await page.screenshot(path=str(OUT / f"{TAG}_2_plain_card.jpeg"), type="jpeg", quality=45)
        said = await play(page, lambda k: "skip" if k % 10 == 9 else k % 4)
        await page.wait_for_selector('[data-testid="rf-plain-summary"]', timeout=15000)
        await page.wait_for_function("""() => /pahunch gaya/.test(document.querySelector('[data-testid="rf-plain-where"]')?.innerText || '')""", timeout=20000)
        sent = seen["offline"][-1]
        results = {r["card_id"]: r for r in sent["results"]}
        right = sum(1 for r in sent["results"] if r["outcome"] == "correct")
        check("C4 the round went up whole, once", len(seen["offline"]) == 1 and sent["exam"] == "JEE" and sent["picks"] == [{"subject": "Physics", "chapter": None}] and len(sent["card_ids"]) == len(said)
              and len(set(sent["card_ids"])) == len(said) and sent["repeat"] is False and len(sent["request_id"]) >= 8 and bool(sent.get("played_at")), len(sent["card_ids"]))
        check("C5 every card is a Physics card of the bank, no prompt twice", all(bank.get(i, {}).get("subject") == "Physics" for i in sent["card_ids"]) and len({bank[i]["prompt"].strip().lower() for i in sent["card_ids"]}) == len(sent["card_ids"]), "")
        check("C6 the phone marked each answer by the card's own key", all((r["outcome"] == "correct") == (r["choice"] == bank[r["card_id"]]["answer"]) for r in sent["results"] if r["outcome"] in ("correct", "incorrect"))
              and [results[i]["outcome"] for i in sent["card_ids"]] == said and all(0 <= r["ms"] <= 20000 for r in sent["results"]), f"{right} right")
        check("C7 the result screen says the same", (await text(page, "rf-summary-score") or "").replace(" ", "") == f"{right}/{len(said)}" and (await text(page, "rf-sum-skipped") or "").startswith(str(said.count("skipped"))), await text(page, "rf-summary-score"))
        check("C8 and what the server paid", "+210 XP" in (await text(page, "rf-plain-where") or "") and "+44 coins" in (await text(page, "rf-plain-where") or ""), await text(page, "rf-plain-where"))
        check("C9 nothing waits on the phone", (await page.evaluate(KEPT))["rounds"] == [], "")
        await page.screenshot(path=str(OUT / f"{TAG}_3_plain_summary.jpeg"), type="jpeg", quality=45)
        # the missed cards again: the same cards, marked as a repeat
        missed = [i for i in sent["card_ids"] if results[i]["outcome"] != "correct"]
        await page.click('[data-testid="rf-repeat-missed"]')
        await page.wait_for_selector('[data-testid="rf-card"]', timeout=15000)
        await play(page, lambda k: 0)
        await page.wait_for_function("""() => /pahunch gaya/.test(document.querySelector('[data-testid="rf-plain-where"]')?.innerText || '')""", timeout=20000)
        again = seen["offline"][-1]
        check("C10 Repeat missed: the same cards, sent as a repeat without picks", sorted(again["card_ids"]) == sorted(missed) and again["repeat"] is True and "picks" not in again and again["request_id"] != sent["request_id"], len(missed))
        await page.click('[data-testid="rf-done"]')
        await lobby(page)
        check("C11 Done leads back to the arena", True, "")

        # D. A slow line: the phone deals after 4 seconds
        line["create"] = "slow"
        await pick_and_start(page, "chemistry", "rf-start-button")
        t0 = asyncio.get_event_loop().time()
        await page.wait_for_selector('[data-testid="rf-plain-screen"] [data-testid="rf-card"]', timeout=20000)
        took = asyncio.get_event_loop().time() - t0
        check("D1 a slow line: the sprint starts from the phone after about 4 seconds", 3.5 <= took <= 9 and (await text(page, "rf-session-exam") or "").startswith("JEE · Chemistry · "), round(took, 1))
        await page.click('[data-testid="rf-exit-button"]')
        await page.click('[data-testid="rf-exit-discard"]')
        await lobby(page)
        check("D2 leaving without saving keeps nothing", len(seen["offline"]) == 2 and (await page.evaluate(KEPT))["rounds"] == [], "")

        # E. An answer of the server's own is not "no line": the sprint does not move to the phone
        line["create"] = "refuse"
        await pick_and_start(page, "mathematics", "rf-start-button")
        await page.wait_for_selector('[data-testid="rf-error"]', timeout=15000)
        await page.wait_for_timeout(5000)
        check("E1 the server said no: its words are shown, the phone does not deal", "/rapid/session" in page.url and "/offline/" not in page.url and "the server says no" in (await text(page, "rf-error") or ""), await text(page, "rf-error"))
        await page.click('[data-testid="rf-exit-button"]')
        await lobby(page)

        # F. The line drops at the END of a sprint the server dealt: the answers stay and go up by themselves
        cards = parts["Physics"][:30]
        line["standin"] = {"id": "standin-sprint-1", "status": "active", "mode": "fresh", "exam": "JEE", "subject": "Physics", "chapter": None, "label": "Mixed Physics", "request_id": "x", "card_ids": [c["id"] for c in cards],
                           "cards": [{**c, "exam": "JEE", "subject": "Physics"} for c in cards], "seconds_per_card": 20}
        line["create"], line["complete"] = "standin", "dead"
        await pick_and_start(page, "physics", "rf-start-button")
        await page.wait_for_selector('[data-testid="rf-session-screen"] [data-testid="rf-card"]', timeout=20000)
        await play(page, lambda k: cards[k]["answer"] if k < 12 else "skip")
        await page.wait_for_selector('[data-testid="rf-kept-note"]', timeout=20000)
        kept = await page.evaluate(KEPT)
        check("F1 the line dropped at the end: the result is shown and the answers are kept", (await text(page, "rf-summary-score") or "").replace(" ", "") == "12/30" and len(kept["rounds"]) == 1
              and kept["rounds"][0]["session"] == "standin-sprint-1" and len(kept["rounds"][0]["results"]) == 30 and kept["rounds"][0]["uid"] == uid, await text(page, "rf-summary-score"))
        check("F2 no error box, and the reward is not invented", not await page.locator('[data-testid="rf-error"]').count() and await page.locator('[data-testid="reward-panel-pending"]').count() == 1, "")
        await page.screenshot(path=str(OUT / f"{TAG}_4_kept_online.jpeg"), type="jpeg", quality=45)
        line["complete"] = "live"
        await page.wait_for_function("""() => { try { const u = JSON.parse(JSON.parse(localStorage.getItem('jl_user'))).id; return JSON.parse(JSON.parse(localStorage.getItem('kept.rounds.' + u))).length === 0; } catch { return false; } }""", timeout=70000)
        done = [c for c in seen["complete"] if c["how"] == "live"]
        check("F3 the line is back: the answers went to that sprint by themselves", len(done) == 1 and done[0]["path"] == "/standin-sprint-1/complete" and len(done[0]["body"]["results"]) == 30
              and sum(1 for r in done[0]["body"]["results"] if r["outcome"] == "correct") == 12, len(seen["complete"]))
        await page.click('[data-testid="rf-done"]')
        await lobby(page)

        # G. The app is opened with no line at all: a door to the phone's cards
        await page.route(NO_LINE, cut)
        await page.goto(BASE + "/", wait_until="domcontentloaded")
        await page.wait_for_selector('[data-testid="session-verifying"]', timeout=60000)
        check("G1 no line: the app waits for the session, the door is not there at once", not await page.locator('[data-testid="offline-door"]').count(), "")
        await page.wait_for_selector('[data-testid="offline-door-button"]', timeout=15000)
        await page.screenshot(path=str(OUT / f"{TAG}_5_door.jpeg"), type="jpeg", quality=45)
        await page.click('[data-testid="offline-door-button"]')
        await page.wait_for_selector('[data-testid="offline-start"]', timeout=20000)
        said = await text(page, "offline-cards-count")
        check("G2 the door opens the phone's Rapid Fire", f"{sum(want.values()):,}" in (said or "") and not await page.locator('[data-testid="offline-online"]').count(), said)
        await page.screenshot(path=str(OUT / f"{TAG}_6_offline_home.jpeg"), type="jpeg", quality=45)
        before = len(seen["offline"])
        await pick_and_start(page, "mathematics", "offline-start")
        await page.wait_for_selector('[data-testid="rf-plain-screen"] [data-testid="rf-card"]', timeout=20000)
        said = await play(page, lambda k: (k * 3) % 4)
        await page.wait_for_selector('[data-testid="rf-plain-summary"]', timeout=15000)
        await page.wait_for_function("""() => /phone par rakha/.test(document.querySelector('[data-testid="rf-plain-where"]')?.innerText || '')""", timeout=15000)
        kept = await page.evaluate(KEPT)
        round_ = kept["rounds"][0] if kept["rounds"] else {}
        check("G3 a round played with no line is kept on the phone, under the account", len(kept["rounds"]) == 1 and round_.get("uid") == uid and len(round_.get("card_ids", [])) == len(said) and len(seen["offline"]) == before
              and all(bank[i]["subject"] == "Mathematics" for i in round_["card_ids"]), len(kept["rounds"]))
        await page.screenshot(path=str(OUT / f"{TAG}_7_kept_round.jpeg"), type="jpeg", quality=45)
        await page.click('[data-testid="rf-done"]')
        await page.wait_for_selector('[data-testid="offline-waiting"]', timeout=15000)
        check("G4 the phone's screen says one round is waiting", (await text(page, "offline-waiting") or "").startswith("1 round"), await text(page, "offline-waiting"))
        # the session check gives up meanwhile (about 40 s): the sign-in screen has the door too, and the private app stays shut
        await page.click('[data-testid="offline-back"]')
        await page.wait_for_selector('[data-testid="entry-session-error"]', timeout=90000)
        await page.wait_for_selector('[data-testid="entry-screen"] [data-testid="offline-door-button"]', timeout=15000)
        check("G5 the sign-in screen: the session error and the same door", True, "")
        await page.goto(BASE + ("/(tabs)/rapid" if ARENA else "/(tabs)"), wait_until="domcontentloaded")
        await page.wait_for_selector('[data-testid="entry-screen"]', timeout=90000)
        check("G6 without a confirmed session the app itself stays shut", "/entry" in page.url, page.url[-40:])

        # H. The line returns: the session is confirmed, the kept round goes up by itself
        await page.unroute(NO_LINE, cut)
        await page.click('[data-testid="offline-door-button"]')
        await page.wait_for_selector('[data-testid="offline-retry"]', timeout=20000)
        await page.click('[data-testid="offline-retry"]')
        await page.wait_for_selector('[data-testid="offline-online"]', timeout=60000)
        await page.wait_for_selector('[data-testid="offline-waiting"]', state="detached", timeout=30000)
        up = seen["offline"][-1]
        check("H1 back on the line: the kept round went up once, as it was played", len(seen["offline"]) == before + 1 and up["request_id"] == round_["request_id"] and up["card_ids"] == round_["card_ids"]
              and up["results"] == round_["results"] and up["picks"] == [{"subject": "Mathematics", "chapter": None}] and (await page.evaluate(KEPT))["rounds"] == [], "")
        await page.click('[data-testid="offline-open-app"]')
        await page.wait_for_selector('[data-testid="rapid-fire-home"]' if ARENA else '[data-testid="home-tile-choice"]', timeout=45000)
        check("H2 and the whole app opens again", True, "")

        # I. Signing out shuts the door (the cards stay: they are nobody's secret)
        await page.goto(BASE + "/account", wait_until="domcontentloaded")
        await page.wait_for_selector('[data-testid="account-signout-button"]', timeout=45000)
        await page.click('[data-testid="account-signout-button"]')
        await page.wait_for_selector('[data-testid="entry-phone-input"]', timeout=45000)
        await page.route(NO_LINE, cut)
        await page.goto(BASE + "/offline", wait_until="domcontentloaded")
        await page.wait_for_selector('[data-testid="offline-closed"]', timeout=60000)
        after = await page.evaluate(KEPT)
        check("I1 signed out: the phone's Rapid Fire is shut, the cards are still there", not await page.locator('[data-testid="offline-start"]').count() and len(after["bank"]["parts"]) == 5, "")
        await page.goto(BASE + "/entry", wait_until="domcontentloaded")
        await page.wait_for_selector('[data-testid="entry-phone-input"]', timeout=60000)
        await page.wait_for_timeout(7000)
        check("I2 and the sign-in screen has no door", not await page.locator('[data-testid="offline-door"]').count(), "")
        await page.unroute(NO_LINE, cut)

        check("J1 nothing else was written for the QA learner", seen["stopped"] == [], seen["stopped"][:5])
        check("J2 no React rule was broken", errors == [], errors[:3])
        await browser.close()
    print(f"\n{sum(checks)}/{len(checks)} passed ({TAG})")
    sys.exit(0 if all(checks) else 1)


asyncio.run(main())
