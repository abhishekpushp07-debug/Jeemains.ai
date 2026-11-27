# Rapid Fire's chapter picker in a browser (27 Nov 2026): nothing ticked for the student, PCM tab first, Select all / Clear,
# any number of chapters, and the mode tiles always ask. Physics, Chemistry and Maths list Class 11 first, then Class 12.
#   python3 /app/tests/rf_picker_check.py            the app (web preview)
#   python3 /app/tests/rf_picker_check.py arena      the browser copy of Rapid Fire (/api/arena)
#   ... small                                        the same on a 360 x 640 phone
# The QA learner is the owner's real account, so NOTHING is written: starting a sprint or a match is answered by the browser
# (a refusal, after the request has been read), and every other write under /api/rf/{sessions,duels,challenges,cups} is
# stopped and counted (there must be none). One sign-in per run.
import asyncio
import json
import re
import sys
from pathlib import Path

from dotenv import dotenv_values
from playwright.async_api import async_playwright

sys.path.insert(0, "/app/tests")
sys.path.insert(0, "/app/backend")
import class_levels  # noqa: E402  (which class a chapter belongs to: the server's own list)
from shine_helpers import sign_in  # noqa: E402

BASE = dotenv_values("/app/frontend/.env")["EXPO_PUBLIC_BACKEND_URL"].rstrip("/")
ARENA, SMALL = "arena" in sys.argv[1:], "small" in sys.argv[1:]
if ARENA:
    BASE += "/api/arena"
W, H = (360, 640) if SMALL else (390, 844)
TAG = ("arena" if ARENA else "app") + ("_small" if SMALL else "")
OUT = Path("/tmp/picker_runs"); OUT.mkdir(exist_ok=True)
checks, seen, popup_waited = [], {"sessions": [], "duels": [], "stopped": []}, False
RULES = ("Rendered more hooks", "Rendered fewer hooks", "order of Hooks", "Cannot update a component", "Maximum update depth", "state update on an unmounted", "Each child in a list")

ROWS = """() => [...document.querySelectorAll('[data-testid^="rf-scope-chapter-"]')].map((el) => el.getAttribute('aria-checked'))"""
STATE = """() => { const plain = (x) => (x || '').replace(/[\\u{F0000}-\\u{FFFFD}]/gu, '').trim().replace(/\\s*\\n\\s*/g, ' · ').replace(/^ · | · $/g, '');
  const q = (id) => document.querySelector(`[data-testid="${id}"]`), t = (id) => plain(q(id)?.innerText),
  off = (id) => q(id)?.getAttribute('aria-disabled') === 'true', y = (id) => { const el = q(id); return el ? Math.round(el.getBoundingClientRect().top) : null; };
  const rows = [...document.querySelectorAll('[data-testid^="rf-scope-chapter-"]')];
  return { tab: [...document.querySelectorAll('[data-testid^="rf-scope-tab-"]')].filter((el) => el.getAttribute('aria-selected') === 'true').map((el) => el.getAttribute('data-testid').replace('rf-scope-tab-', '')),
    tabs: [...document.querySelectorAll('[data-testid^="rf-scope-tab-"]')].map((el) => plain(el.innerText).replace(/ · /g, ' ')),
    names: rows.map((el) => plain(el.innerText).split(' · ')[0]), rows: rows.length, on: rows.filter((el) => el.getAttribute('aria-checked') === 'true').length,
    all: q('rf-scope-select-all')?.getAttribute('aria-checked'), allText: t('rf-scope-select-all'), clearOff: off('rf-scope-clear-all'),
    empty: !!q('rf-scope-empty'), chips: [...document.querySelectorAll('[data-testid^="rf-scope-picked-"]')].map((el) => plain(el.innerText)),
    done: t('rf-scope-done'), doneOff: off('rf-scope-done'), play: t('rf-scope-play'), playOff: off('rf-scope-play'), hasPlay: !!q('rf-scope-play'),
    heads: [...document.querySelectorAll('[data-testid="rf-scope-sheet"] div')].map((el) => el.innerText || '').filter((s) => /^(CLASS \\d+ · )?[A-Z]+ · \\d+ CHAPTERS( · BITSAT 2026)?$/.test(s)).filter((s, i, a) => a.indexOf(s) === i),
    y: { tabs: y('rf-scope-tabs'), all: y('rf-scope-select-all'), row: rows[0] ? Math.round(rows[0].getBoundingClientRect().top) : null, tray: y('rf-scope-tray') },
    text: (q('rf-scope-sheet')?.innerText || '') }; }"""
FITS = """() => { const w = window.innerWidth, cut = [];
  for (const id of ['rf-scope-tabs', 'rf-scope-select-all', 'rf-scope-clear-all', 'rf-scope-done', 'rf-scope-play', 'rf-scope-search', 'rf-scope-tray']) {
    const el = document.querySelector(`[data-testid="${id}"]`); if (!el) continue; const b = el.getBoundingClientRect();
    if (b.left < -1 || b.right > w + 1 || b.bottom > window.innerHeight + 1 || b.width < 2) cut.push(id); }
  // every key a thumb needs is really on top at its own middle (not squeezed flat, not under another part) and tall enough
  const hidden = ['rf-scope-tab-pcm', 'rf-scope-tab-physics', 'rf-scope-select-all', 'rf-scope-clear-all', 'rf-scope-done'].filter((id) => {
    const el = document.querySelector(`[data-testid="${id}"]`); if (!el) return true; const b = el.getBoundingClientRect();
    const top = document.elementFromPoint(b.left + b.width / 2, b.top + b.height / 2);
    return b.height < 43.5 || !top || !(el === top || el.contains(top)); });
  return { wide: document.scrollingElement.scrollWidth > w + 1, cut, hidden }; }"""


def check(name, ok, detail=""):
    checks.append(bool(ok))
    print(("PASS " if ok else "FAIL ") + name + (" | " + str(detail) if detail != "" else ""))


async def stand_ins(page):
    """Starting a round is read and then refused by the browser; no other write may leave it."""
    def handler(kind):
        async def run(route):
            req = route.request
            path = req.url.split(f"/api/rf/{kind}", 1)[1].split("?")[0]
            if req.method == "GET":
                await route.continue_()
            elif req.method == "POST" and path == "" and kind in ("sessions", "duels"):
                seen[kind].append({"body": json.loads(req.post_data or "{}"), "page": page.url})
                await route.fulfill(status=400, content_type="application/json", body=json.dumps({"detail": "Stand-in: this check does not start a round."}))
            else:
                seen["stopped"].append(f"{req.method} /{kind}{path}")
                await route.abort()
        return run
    for kind in ("sessions", "duels", "challenges", "cups"):
        await page.route(re.compile(rf".*/api/rf/{kind}(/|\?|$).*"), handler(kind))


async def lobby(page):
    await page.wait_for_selector('[data-testid="rapid-fire-home"]', timeout=60000)
    await page.wait_for_selector('[data-testid="rf-chapter-picker"]', timeout=30000)
    global popup_waited
    if not popup_waited:  # today's All India offer comes up a moment after the lobby, once: EXIT stays in the lobby, nothing is sent
        popup_waited = True
        try:
            await page.wait_for_selector('[data-testid="rf-daily-popup-exit"]', timeout=5000)
        except Exception:
            pass
    if await page.locator('[data-testid="rf-daily-popup-exit"]').count():
        await page.click('[data-testid="rf-daily-popup-exit"]')
        await page.wait_for_selector('[data-testid="rf-daily-popup"]', state="detached", timeout=15000)


async def open_sheet(page, tile="rf-chapter-picker"):
    await lobby(page)
    await page.click(f'[data-testid="{tile}"]')
    await page.wait_for_selector('[data-testid="rf-scope-sheet"]', timeout=15000)
    await page.wait_for_selector('[data-testid^="rf-scope-chapter-"]', timeout=30000)  # the bank's chapters are in
    await page.wait_for_timeout(500)  # the sheet has slid up
    return await page.evaluate(STATE)


async def state(page, wait=250):
    await page.wait_for_timeout(wait)
    return await page.evaluate(STATE)


async def close_sheet(page):
    await page.click('[data-testid="rf-scope-sheet-close"]')
    await page.wait_for_selector('[data-testid="rf-scope-sheet"]', state="detached", timeout=15000)


async def back_to_lobby(page):
    await page.wait_for_timeout(1200)  # the round's page has asked, and has its refusal
    await page.go_back()
    await lobby(page)


def fresh(s):
    return s["tab"] == ["pcm"] and s["on"] == 0 and s["empty"] and s["chips"] == [] and s["all"] == "false" and s["clearOff"] and s["doneOff"]


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
        if not ARENA:
            await page.click('[data-testid="tab-rapid"]')
        cat = await page.evaluate("fetch('/api/rf/catalog?exam=JEE').then((r) => r.json())")
        n = {s["name"]: len([c for c in s["chapters"] if c["count"]]) for s in cat["subjects"]}
        pcm = n["Physics"] + n["Chemistry"] + n["Mathematics"]
        # Which class each chapter belongs to (the server's list), and the order a tab must list them in: Class 11, then Class 12.
        level = {s["name"]: [class_levels.level_of("jee-main", s["name"], c["name"]) for c in s["chapters"]] for s in cat["subjects"]}
        c11, c12 = {k: v.count(11) for k, v in level.items()}, {k: v.count(12) for k, v in level.items()}
        order = {s["name"]: [c["name"] for want in (11, 12) for c, got in zip(s["chapters"], level[s["name"]]) if got == want] for s in cat["subjects"]}
        jee = ("Physics", "Chemistry", "Mathematics")

        # A. Quick Play opens plain: PCM tab, nothing ticked, Select all under the tabs and above the chapters
        s = await open_sheet(page)
        await page.screenshot(path=str(OUT / f"{TAG}_1_opens_plain.jpeg"), type="jpeg", quality=45)
        check("A1 Quick Play opens on the PCM tab", s["tab"] == ["pcm"], s["tabs"])
        check("A2 no chapter is ticked, nothing is picked", s["rows"] >= 3 and s["on"] == 0 and s["empty"] and s["chips"] == [], f'{s["rows"]} rows drawn, {s["on"]} ticked')
        check("A3 Select all is there, unticked; Clear rests", s["all"] == "false" and s["allText"] == f"Select all · PCM · {pcm} chapters" and s["clearOff"], s["allText"])
        check("A4 the old Quick Mix tiles are gone", "QUICK MIX" not in s["text"] and not await page.locator('[data-testid="rf-scope-pcm"], [data-testid^="rf-scope-mixed-"]').count())
        check("A5 tabs, then Select all, then the chapters, top to bottom", s["y"]["tabs"] < s["y"]["all"] < s["y"]["row"] < s["y"]["tray"], s["y"])
        check("A6 SAVE and PLAY rest until something is ticked", s["doneOff"] and s["playOff"] and s["play"] == "PLAY · Tick chapters first", [s["done"], s["play"]])
        check("A7 the list begins with Class 11 of PCM, Physics' chapters first", s["heads"][:1] == [f'CLASS 11 · PCM · {sum(c11[k] for k in jee)} CHAPTERS'] and s["names"][:3] == order["Physics"][:3], [s["heads"], s["names"][:3]])
        first_row = (await page.locator('[data-testid^="rf-scope-chapter-"]').nth(0).inner_text()).replace("\n", " · ")
        check("A10 on the PCM tab every chapter says its subject", bool(re.search(r" · Physics · \d+ cards$", first_row)), first_row)
        check("A8 no 'up to 5' anywhere", "Up to 5" not in s["text"] and "/5" not in s["text"])
        fit = await page.evaluate(FITS)
        check("A9 everything fits the screen, and every key is in full view and at least 44 high", not fit["wide"] and not fit["cut"] and not fit["hidden"], fit)

        # B. Select all
        await page.click('[data-testid="rf-scope-select-all"]')
        s = await state(page)
        await page.screenshot(path=str(OUT / f"{TAG}_2_select_all.jpeg"), type="jpeg", quality=45)
        check("B1 Select all ticks every chapter in view", s["rows"] >= 3 and s["on"] == s["rows"] and s["all"] == "true" and s["allText"].startswith("All selected"), f'{s["on"]} of {s["rows"]} drawn rows')
        check("B2 the tray says all of the three subjects", s["chips"] == ["Physics · all", "Chemistry · all", "Maths · all"] and not s["empty"], s["chips"])
        check("B3 SAVE counts the chapters, PLAY is a 30-card Quick Match", s["done"] == f"SAVE · {pcm} chapters" and s["play"] == "PLAY · Quick Match · 30 cards" and not s["doneOff"] and not s["playOff"], [s["done"], s["play"]])
        check("B4 the PCM tab shows the number ticked", s["tabs"][0] == f"PCM {pcm}" and s["tabs"][1] == f'Physics {n["Physics"]}', s["tabs"][:4])

        # C. one chapter unticked after Select all
        first = page.locator('[data-testid^="rf-scope-chapter-"]').nth(1)
        name = (await first.inner_text()).split("\n")[0]
        await first.click()
        s = await state(page)
        rows = await page.evaluate(ROWS)
        await page.screenshot(path=str(OUT / f"{TAG}_3_one_unticked.jpeg"), type="jpeg", quality=45)
        check("C1 a ticked chapter can be unticked after Select all", rows[1] == "false" and rows.count("false") == 1 and s["all"] == "false" and s["allText"].startswith("Select all"), f"unticked: {name}")
        check("C2 the counts follow", s["chips"] == [f'Physics · {n["Physics"] - 1}', "Chemistry · all", "Maths · all"] and s["done"] == f"SAVE · {pcm - 1} chapters", [s["chips"], s["done"]])
        await first.click()
        s = await state(page)
        check("C3 ticking it again is All selected again", s["all"] == "true" and s["chips"][0] == "Physics · all")

        # D. Clear
        await page.click('[data-testid="rf-scope-clear-all"]')
        s = await state(page)
        check("D1 Clear unticks everything in view", fresh(s) and s["playOff"], [s["on"], s["chips"]])

        # E. a subject's tab, and ticks that stay when the tab changes
        await page.click('[data-testid="rf-scope-tab-physics"]')
        s = await state(page)
        heads = [f'CLASS 11 · PHYSICS · {c11["Physics"]} CHAPTERS', f'CLASS 12 · PHYSICS · {c12["Physics"]} CHAPTERS']
        check("E1 the Physics tab lists Physics only, Class 11 first, nothing ticked", s["tab"] == ["physics"] and s["heads"] == heads[:len(s["heads"])] and s["heads"][:1] == heads[:1] and s["names"] == order["Physics"][:len(s["names"])]
              and s["on"] == 0 and s["allText"] == f'Select all · Physics · {n["Physics"]} chapters', [s["heads"], s["names"][:2], s["allText"]])
        # to the end of the list: Class 12 has its own heading, and the last chapter is the last of Class 12
        await page.evaluate("""() => { let el = document.querySelector('[data-testid^="rf-scope-chapter-"]');
          while (el && !(el.scrollHeight > el.clientHeight + 4 && getComputedStyle(el).overflowY !== 'visible')) el = el.parentElement;
          if (el) el.scrollTop = el.scrollHeight; }""")
        s = await state(page, 700)
        check("E1b lower down: the Class 12 heading, then Class 12's chapters to the end", heads[1] in s["heads"] and s["names"][-1:] == order["Physics"][-1:]
              and await page.locator('[data-testid="rf-scope-head-class-12"]').count() == 1, [s["heads"], s["names"][-2:]])
        await page.click('[data-testid="rf-scope-tab-pcm"]')
        await page.click('[data-testid="rf-scope-tab-physics"]')  # back at the top of the Physics list
        s = await state(page)
        await page.click('[data-testid="rf-scope-select-all"]')
        await page.click('[data-testid="rf-scope-tab-chemistry"]')
        s = await state(page)
        check("E2 Chemistry opens unticked, Physics stays picked", s["tab"] == ["chemistry"] and s["on"] == 0 and s["chips"] == ["Physics · all"] and s["all"] == "false", s["chips"])
        for k in (0, 2):
            await page.locator('[data-testid^="rf-scope-chapter-"]').nth(k).click()
        s = await state(page)
        check("E3 two chapters of Chemistry ticked next to all of Physics", s["on"] == 2 and s["chips"] == ["Physics · all", "Chemistry · 2"] and s["done"] == f'SAVE · {n["Physics"] + 2} chapters', [s["chips"], s["done"]])
        await page.click('[data-testid="rf-scope-picked-physics"]')
        s = await state(page)
        check("E4 a subject's chip in the tray clears that subject only", s["chips"] == ["Chemistry · 2"] and s["on"] == 2, s["chips"])
        await page.click('[data-testid="rf-scope-tab-logical-reasoning"]')
        s = await state(page)
        check("E5 Reasoning (BITSAT) has its own tab and Select all", s["heads"] == [f'REASONING · {n["Logical Reasoning"]} CHAPTERS · BITSAT 2026'] and s["allText"] == f'Select all · Reasoning · {n["Logical Reasoning"]} chapters', s["heads"])

        # F. search across every subject
        await page.fill('[data-testid="rf-scope-search"]', "ther")
        s = await state(page, 500)
        hits = [(await r.inner_text()).replace("\n", " · ") for r in await page.locator('[data-testid^="rf-scope-chapter-"]').all()]
        check("F1 a search lists chapters of every subject, with the subject's name", len(hits) >= 2 and all(re.search(r" · (Physics|Chemistry|Maths|English|Reasoning) · \d+ cards$", h) for h in hits) and s["tab"] == [], hits[:4])
        await page.locator('[data-testid^="rf-scope-chapter-"]').nth(0).click()
        await page.click('[data-testid="rf-scope-clear"]')
        s = await state(page)
        check("F2 a chapter ticked in the search stays ticked", len(s["chips"]) >= 1 and s["done"] == "SAVE · 3 chapters", [s["chips"], s["done"]])

        # G. closing and opening again: plain again
        await close_sheet(page)
        s = await open_sheet(page)
        check("G1 closed without saving and opened again: nothing ticked, PCM tab", fresh(s), [s["tab"], s["on"], s["chips"]])

        # H. PLAY (Quick Match) on PCM with one chapter unticked: what is sent
        await page.click('[data-testid="rf-scope-select-all"]')
        row = page.locator('[data-testid^="rf-scope-chapter-"]').nth(2)
        gone = (await row.inner_text()).split("\n")[0]
        await row.click()
        await page.click('[data-testid="rf-scope-play"]')
        await page.wait_for_timeout(2500)
        sent = seen["duels"][-1] if seen["duels"] else None
        picks = sent["body"].get("picks", []) if sent else []
        check("H1 PLAY asks for a Quick Match on every ticked chapter", bool(sent) and sent["body"].get("mode") == "random" and len(picks) == pcm - 1 and all(p.get("chapter") for p in picks)
              and not any(p["chapter"] == gone and p["subject"] == "Physics" for p in picks) and sent["body"].get("count") == 30, f'{len(picks)} chapters, without "{gone}", count {sent["body"].get("count") if sent else None}')
        check("H2 the address of that round stays short", bool(sent) and len(sent["page"]) < 4000, f'{len(sent["page"]) if sent else 0} characters')
        await back_to_lobby(page)

        # I. the lobby remembers nothing for the picker: Quick Play is plain again
        s = await open_sheet(page)
        check("I1 after a round was started, Quick Play still opens with nothing ticked", fresh(s), [s["tab"], s["on"], s["chips"]])
        await close_sheet(page)

        # J. Solo Sprint always asks, and starts on exactly what is ticked
        before = len(seen["sessions"])
        s = await open_sheet(page, "rf-start-button")
        await page.screenshot(path=str(OUT / f"{TAG}_4_solo_asks.jpeg"), type="jpeg", quality=45)
        check("J1 Solo Sprint opens the picker (it does not start on an old choice)", len(seen["sessions"]) == before and fresh(s) and not s["hasPlay"] and s["done"].startswith("START SOLO SPRINT"), s["done"])
        await page.click('[data-testid="rf-scope-tab-physics"]')
        two = []
        for k in (0, 1):
            r = page.locator('[data-testid^="rf-scope-chapter-"]').nth(k)
            two.append((await r.inner_text()).split("\n")[0])
            await r.click()
        s = await state(page)
        check("J2 two chapters ticked: the button says what will be played", not s["doneOff"] and s["done"].startswith(f"START SOLO SPRINT · {sorted(two)[0]} +1 more · 2 chapters · "), s["done"])
        await page.click('[data-testid="rf-scope-done"]')
        await page.wait_for_timeout(2500)
        sent = seen["sessions"][-1] if len(seen["sessions"]) > before else None
        check("J3 the sprint is asked for on those two chapters, 30 cards", bool(sent) and sorted(p["chapter"] for p in sent["body"].get("picks", [])) == sorted(two)
              and all(p["subject"] == "Physics" for p in sent["body"]["picks"]) and sent["body"].get("count") == 30, sent["body"].get("picks") if sent else None)
        await back_to_lobby(page)
        before = len(seen["sessions"])
        s = await open_sheet(page, "rf-start-button")
        check("J4 Solo Sprint a second time asks again, with nothing ticked", len(seen["sessions"]) == before and fresh(s), [s["on"], s["chips"]])
        await close_sheet(page)

        # K. Practice Rival always asks too
        before = len(seen["duels"])
        s = await open_sheet(page, "rf-duel-ai")
        check("K1 Practice Rival opens the picker, nothing ticked", len(seen["duels"]) == before and fresh(s) and s["done"].startswith("PLAY PRACTICE RIVAL"), s["done"])
        await page.click('[data-testid="rf-scope-tab-chemistry"]')
        await page.click('[data-testid="rf-scope-select-all"]')
        s = await state(page)
        check("K2 all of Chemistry: named Mixed Chemistry", s["done"].startswith(f'PLAY PRACTICE RIVAL · Mixed Chemistry · {n["Chemistry"]} chapters · '), s["done"])
        await page.click('[data-testid="rf-scope-done"]')
        await page.wait_for_timeout(2500)
        sent = seen["duels"][-1] if len(seen["duels"]) > before else None
        check("K3 the rival match is asked for on the whole subject, as before", bool(sent) and sent["body"].get("mode") == "invite" and sent["body"].get("picks") == [{"subject": "Chemistry", "chapter": None}], sent["body"].get("picks") if sent else None)
        await back_to_lobby(page)

        # L. Play Friends: the ribbon shows the last choice, and its picker opens ON that choice (it is there to change it)
        await page.click('[data-testid="rf-play-friends"]')
        await page.wait_for_selector('[data-testid="challenge-chapter"]', timeout=30000)
        ribbon = (await page.locator('[data-testid="challenge-chapter"]').inner_text()).replace("\n", " · ")
        await page.click('[data-testid="challenge-chapter"]')
        await page.wait_for_selector('[data-testid^="rf-scope-chapter-"]', timeout=30000)
        s = await state(page, 600)
        await page.screenshot(path=str(OUT / f"{TAG}_5_play_friends.jpeg"), type="jpeg", quality=45)
        check("L1 Play Friends shows the last battleground and opens its picker on it", ribbon.startswith("Mixed Chemistry") and s["chips"] == ["Chemistry · all"] and s["tab"] == ["pcm"] and not s["hasPlay"], [ribbon, s["chips"]])
        await page.click('[data-testid="rf-scope-tab-chemistry"]')
        await page.locator('[data-testid^="rf-scope-chapter-"]').nth(0).click()
        s = await state(page)
        check("L2 there too a chapter can be unticked", s["chips"] == [f'Chemistry · {n["Chemistry"] - 1}'] and s["done"].startswith(f'{n["Chemistry"] - 1} CHAPTERS · CHEMISTRY'), [s["chips"], s["done"]])
        await close_sheet(page)

        check("Z1 no write left the browser", seen["stopped"] == [], seen["stopped"])
        check("Z2 rounds asked for and refused by the browser: 2 matches, 1 sprint", [len(seen["duels"]), len(seen["sessions"])] == [2, 1], [len(seen["duels"]), len(seen["sessions"])])
        check("Z3 no React rule was broken", errors == [], errors[:3])
        await browser.close()
    print(f"{sum(checks)} of {len(checks)} checks passed; pictures in {OUT}")
    sys.exit(0 if all(checks) else 1)


asyncio.run(main())
