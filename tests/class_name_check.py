# Chapter-wise by class (All | Class 11 | Class 12) and the student's own name on the Account screen, in a browser (27 Nov 2026).
#   python3 /app/tests/class_name_check.py            the app (web preview): Chapter-wise, then Account
#   python3 /app/tests/class_name_check.py small      the same on a 360 x 640 phone
#   python3 /app/tests/class_name_check.py arena      the browser copy of Rapid Fire (/api/arena): Account only (it has no papers)
# The QA learner is the owner's real account, so NOTHING is written and no paper is started:
#   - a chapter row is tapped only when it says "Start", which opens the test's own page (looked at, never begun);
#   - saving a name (PUT /profile/display-name) is answered by the browser in the website's own words (shine_helpers.fake_name),
#     and GET /api/rf/name by the browser too, so the real name is never changed;
#   - every other write to the website is stopped and counted (there must be none). One sign-in per run.
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
from shine_helpers import fake_name, sign_in  # noqa: E402

BASE = dotenv_values("/app/frontend/.env")["EXPO_PUBLIC_BACKEND_URL"].rstrip("/")
ARENA, SMALL = "arena" in sys.argv[1:], "small" in sys.argv[1:]
if ARENA:
    BASE += "/api/arena"
W, H = (360, 640) if SMALL else (390, 844)
TAG = ("arena" if ARENA else "app") + ("_small" if SMALL else "")
OUT = Path("/tmp/class_runs"); OUT.mkdir(exist_ok=True)
checks, stopped, writes, asked = [], [], [], []
RULES = ("Rendered more hooks", "Rendered fewer hooks", "order of Hooks", "Cannot update a component", "Maximum update depth", "state update on an unmounted", "Each child in a list")
PCM = ("Physics", "Chemistry", "Mathematics")
WEBSITE = json.load(open("/app/tests/data/website_chapters_27nov2026.json"))["jee-main"]  # the lists as the website gave them that day

STATE = """() => { const plain = (x) => (x || '').replace(/[\\u{F0000}-\\u{FFFFD}]/gu, '').trim().replace(/\\s*\\n\\s*/g, ' ');
  const q = (id) => document.querySelector(`[data-testid="${id}"]`), list = q('catalogue-list');
  const tabs = ['all', '11', '12'].map((k) => { const el = q('catalogue-class-' + k); if (!el) return null; const b = el.getBoundingClientRect();
    const top = document.elementFromPoint(b.left + b.width / 2, b.top + b.height / 2);
    return { on: el.getAttribute('aria-selected') === 'true', text: plain(el.innerText), h: Math.round(b.height), seen: !!top && (el === top || el.contains(top)), inside: b.left >= -1 && b.right <= window.innerWidth + 1 }; });
  return { tabs, bar: !!q('catalogue-class-tabs'), count: plain(q('catalogue-count')?.innerText), pager: !!q('catalogue-next-page'),
    emptyClass: plain(q('catalogue-empty-class')?.innerText), empty: !!q('catalogue-empty'), loading: !!q('catalogue-loading'), wide: document.scrollingElement.scrollWidth > window.innerWidth + 1,
    subject: [...document.querySelectorAll('[data-testid^="catalogue-subject-"]')].map((el) => plain(el.innerText)),
    order: [...document.querySelectorAll('[data-testid^="set-title-"], [data-testid^="catalogue-head-"]')].map((el) => plain(el.innerText)),
    y: { bar: q('catalogue-class-tabs') ? Math.round(q('catalogue-class-tabs').getBoundingClientRect().top) : null, search: Math.round(q('catalogue-search-input')?.getBoundingClientRect().top ?? -1),
         chips: Math.round(q('catalogue-subject-physics')?.getBoundingClientRect().top ?? -1), list: list ? Math.round(list.getBoundingClientRect().top) : null },
    end: !list || list.scrollTop + list.clientHeight >= list.scrollHeight - 2 }; }"""


def check(name, ok, detail=""):
    checks.append(bool(ok))
    print(("PASS " if ok else "FAIL ") + name + (" | " + str(detail) if detail != "" else ""))


async def state(page, wait=300):
    await page.wait_for_timeout(wait)
    return await page.evaluate(STATE)


async def settled(page):
    """The list in view has arrived (or says it is empty)."""
    await page.wait_for_function("""() => !document.querySelector('[data-testid="catalogue-loading"]') && (document.querySelector('[data-testid^="set-title-"]')
      || document.querySelector('[data-testid="catalogue-empty"]') || document.querySelector('[data-testid="catalogue-empty-class"]'))""", timeout=45000)
    return await state(page)


async def whole_list(page):
    """Every heading and chapter of the list in view, top to bottom (the list draws a few rows at a time)."""
    seen = []
    await page.evaluate("""() => { const el = document.querySelector('[data-testid="catalogue-list"]'); if (el) el.scrollTop = 0; }""")
    for _ in range(60):
        s = await state(page, 220)
        seen += [x for x in s["order"] if x not in seen]
        if s["end"]:
            break
        await page.evaluate("""() => { const el = document.querySelector('[data-testid="catalogue-list"]'); el.scrollTop += el.clientHeight * 0.7; }""")
    await page.evaluate("""() => { const el = document.querySelector('[data-testid="catalogue-list"]'); if (el) el.scrollTop = 0; }""")
    return seen


def expected(subject):
    """The website's chapters of a subject by class, in the website's own order."""
    rows = [(r["title"], class_levels.level_of("jee-main", subject, r["title"])) for r in WEBSITE[subject]]
    return {level: [t for t, got in rows if got == level] for level in (11, 12, None)}


async def guards(page):
    """Writes to the website: the sign-in passes, the name is answered by the browser (fake_name), anything else is stopped."""
    async def website(route):
        req = route.request
        path = req.url.split("/api/jl/", 1)[1].split("?")[0]
        if req.method == "GET" or path in ("auth/phone", "auth/refresh"):
            await route.continue_()
        else:
            stopped.append(f"{req.method} {path}")
            await route.abort()
    await page.route(re.compile(r".*/api/jl/.*"), website)

    def note(req):
        if "/exam-navigation/" in req.url:
            asked.append(req.url.split("/api/jl/", 1)[1])
        if req.method != "GET" and "/api/" in req.url:
            writes.append(f'{req.method} /api/{req.url.split("/api/", 1)[1].split("?")[0]}')
    page.on("request", note)


async def chapter_wise(page):
    await page.goto(BASE + "/catalogue?slug=jee-main&kind=chapters", wait_until="domcontentloaded", timeout=90000)
    await page.wait_for_selector('[data-testid="catalogue-jee-main-chapters"]', timeout=60000)
    early = await page.evaluate(STATE)
    s = await settled(page)
    await page.screenshot(path=str(OUT / f"{TAG}_1_chapterwise_all.jpeg"), type="jpeg", quality=45)
    want = expected("Physics")
    n11, n12 = len(want[11]), len(want[12])
    check("C1 Chapter-wise has three tabs on top: All, Class 11, Class 12; it opens on All", s["bar"] and [t["on"] for t in s["tabs"]] == [True, False, False]
          and [t["text"] for t in s["tabs"]] == [f"All {n11 + n12}", f"Class 11 {n11}", f"Class 12 {n12}"], [t["text"] for t in s["tabs"]])
    check("C2 the tabs are there from the first moment (the list does not jump when it arrives)", early["bar"] or not early["loading"], early["tabs"])
    check("C3 from top to bottom: search, class tabs, subjects, list", s["y"]["search"] < s["y"]["bar"] < s["y"]["chips"] < s["y"]["list"], s["y"])
    check("C4 every tab is in full view, on top, and at least 44 high; nothing is wider than the screen", all(t["h"] >= 44 and t["seen"] and t["inside"] for t in s["tabs"]) and not s["wide"], [t["h"] for t in s["tabs"]])
    rows = await whole_list(page)
    check("C5 All: Class 11's chapters under their heading, then Class 12's, in the website's own order",
          rows == [f"CLASS 11 · {n11} CHAPTERS", *want[11], f"CLASS 12 · {n12} CHAPTERS", *want[12]], rows[:2] + rows[n11 + 1:n11 + 3])
    check("C6 the whole subject is one list: no Previous / Next, and the count is the subject's", not s["pager"] and s["count"] == f"{n11 + n12} LIVE CHAPTER TESTS", s["count"])
    pages = sorted(re.search(r"page=(\d+)", u).group(1) for u in asked if "subject=Physics" in u and "q=&" in u)
    check("C7 the website was asked for each page of Physics once", pages == ["1", "2", "3"], pages)

    await page.click('[data-testid="catalogue-class-12"]')
    s = await state(page)
    rows = await whole_list(page)
    await page.screenshot(path=str(OUT / f"{TAG}_2_chapterwise_class12.jpeg"), type="jpeg", quality=45)
    check("C8 Class 12: only Class 12's chapters, no heading, its own count", [t["on"] for t in s["tabs"]] == [False, False, True] and rows == want[12] and s["count"] == f"{n12} LIVE CHAPTER TESTS · CLASS 12", [rows[:2], s["count"]])
    before = len(asked)
    await page.click('[data-testid="catalogue-class-11"]')
    s = await state(page)
    rows = await whole_list(page)
    check("C9 Class 11: only Class 11's chapters; changing the tab asks the website for nothing", rows == want[11] and s["count"] == f"{n11} LIVE CHAPTER TESTS · CLASS 11" and len(asked) == before, [rows[:2], s["count"], len(asked) - before])

    # another subject keeps the class in view
    await page.click('[data-testid="catalogue-subject-chemistry"]')
    s = await settled(page)
    want = expected("Chemistry")
    rows = await whole_list(page)
    check("C10 Chemistry opens on the same class", [t["on"] for t in s["tabs"]] == [False, True, False] and rows == want[11]
          and [t["text"] for t in s["tabs"]] == [f"All {len(WEBSITE['Chemistry'])}", f"Class 11 {len(want[11])}", f"Class 12 {len(want[12])}"], [t["text"] for t in s["tabs"]])
    await page.click('[data-testid="catalogue-class-all"]')
    rows = await whole_list(page)
    check("C11 a chapter that is in no class is still listed in All, after the two classes",
          rows == [f"CLASS 11 · {len(want[11])} CHAPTERS", *want[11], f"CLASS 12 · {len(want[12])} CHAPTERS", *want[12], f"OTHER · {len(want[None])} CHAPTER", *want[None]] and len(want[None]) == 1, rows[-3:])
    await page.click('[data-testid="catalogue-subject-mathematics"]')
    s = await settled(page)
    want = expected("Mathematics")
    check("C12 Maths has its own numbers", [t["text"] for t in s["tabs"]] == [f"All {len(WEBSITE['Mathematics'])}", f"Class 11 {len(want[11])}", f"Class 12 {len(want[12])}"], [t["text"] for t in s["tabs"]])

    # a search inside a class
    await page.click('[data-testid="catalogue-subject-physics"]')
    await settled(page)
    await page.click('[data-testid="catalogue-class-11"]')
    await page.fill('[data-testid="catalogue-search-input"]', "electro")
    await page.wait_for_timeout(900)  # the search waits a moment after the last letter
    s = await settled(page)
    check("C13 a search that finds chapters only in the other class says so, and offers all chapters", s["bar"] and "No Class 11 chapter matches." in s["emptyClass"] and "Show all chapters" in s["emptyClass"] and not s["order"], s["emptyClass"])
    await page.click('[data-testid="catalogue-class-show-all"]')
    s = await state(page)
    found = [t for t in expected("Physics")[12] if "electro" in t.lower()]
    check("C14 …which shows them under Class 12", [t["on"] for t in s["tabs"]] == [True, False, False] and s["order"] == [f"CLASS 12 · {len(found)} CHAPTERS", *found] and len(found) >= 2, s["order"])
    await page.fill('[data-testid="catalogue-search-input"]', "zzzz")
    await page.wait_for_timeout(900)
    s = await settled(page)
    check("C15 a search that finds nothing keeps the tabs and says so as before", s["bar"] and s["empty"] and not s["emptyClass"], [s["bar"], s["empty"]])
    await page.click('[data-testid="catalogue-clear-search"]')
    await page.wait_for_timeout(900)
    await settled(page)

    # one chapter at a time: a tap on a row opens that chapter's test (its own page; never begun here)
    await page.click('[data-testid="catalogue-class-12"]')
    await state(page)
    row = page.locator('[data-testid^="set-row-"][aria-label$=". Start"]').first
    if await row.count():
        label = await row.get_attribute("aria-label")
        await row.click()
        await page.wait_for_url(re.compile(r".*/set/[0-9a-f-]+"), timeout=30000)
        await page.wait_for_timeout(1500)
        check("C16 a tap on one chapter opens that chapter's test page (single choice, as before)", "/set/" in page.url, label)
        await page.go_back()
        s = await settled(page)
        check("C17 Back returns to the same class and subject", [t["on"] for t in s["tabs"]] == [False, False, True] and s["order"][:1] == expected("Physics")[12][:1], [t["text"] for t in s["tabs"]])
    else:
        check("C16 a tap on one chapter opens that chapter's test page (single choice, as before)", False, "no row says Start: not checked")

    # an exam whose chapters are not split into classes is exactly as it was: no class tabs, a page at a time
    await page.goto(BASE + "/catalogue?slug=bitsat&kind=chapters", wait_until="domcontentloaded", timeout=90000)
    await page.wait_for_selector('[data-testid="catalogue-bitsat-chapters"]', timeout=60000)
    await page.wait_for_selector('[data-testid^="catalogue-subject-"]', timeout=45000)
    if await page.locator('[data-testid="catalogue-subject-mathematics"]').count():
        await page.click('[data-testid="catalogue-subject-mathematics"]')
    s = await settled(page)
    check("C18 BITSAT chapter-wise is untouched: no class tabs, no class headings, pages as before", not s["bar"] and not any(x.startswith("CLASS ") for x in s["order"]) and (s["pager"] or len(s["order"]) < 12), [s["bar"], s["pager"], len(s["order"])])


async def account(page):
    held, calls = {"name": ""}, []  # the name our server would say, and what the browser was asked to save

    async def my_name(route):
        await route.fulfill(status=200, content_type="application/json", body=json.dumps({"name": held["name"]}))
    await page.route(re.compile(r".*/api/rf/name(\?.*)?$"), my_name)
    await fake_name(page, calls, state=held)
    await page.goto(BASE + "/account", wait_until="domcontentloaded", timeout=90000)
    await page.wait_for_selector('[data-testid="account-name-button"]', timeout=60000)
    await page.wait_for_timeout(1200)
    plain = lambda t: re.sub(r"[\U000F0000-\U000FFFFD]", "", t or "").strip()  # noqa: E731
    account_name = plain(await page.locator('[data-testid="account-name"]').inner_text())
    row = plain(await page.locator('[data-testid="account-name-button"]').inner_text()).replace("\n", " · ")
    await page.screenshot(path=str(OUT / f"{TAG}_3_account.jpeg"), type="jpeg", quality=45)
    check("N1 Account has a place for the name; without one it says the account's own name", row.startswith("Add your name") and account_name.startswith("Learner"), [account_name[:7], row])
    box = await page.locator('[data-testid="account-name-button"]').bounding_box()
    check("N2 the row is a full thumb's height and inside the screen", box["height"] >= 44 and box["x"] >= 0 and box["x"] + box["width"] <= W + 1, box)

    await page.click('[data-testid="account-name-button"]')
    await page.wait_for_selector('[data-testid="aits-name-input"]', timeout=15000)
    about = await page.locator('[data-testid="aits-name-about"]').inner_text()
    check("N3 the name sheet opens empty and says where the name is shown", await page.input_value('[data-testid="aits-name-input"]') == "" and "Rapid Fire" in about and "Leaderboard" in about
          and not await page.locator('[data-testid="aits-name-remove"]').count(), about[:60])
    await page.fill('[data-testid="aits-name-input"]', "!")
    await page.click('[data-testid="aits-name-save"]')
    await page.wait_for_selector('[data-testid="aits-name-error"]', timeout=15000)
    check("N4 a name the website refuses: its own words are shown and nothing changes", "2 se 20" in await page.locator('[data-testid="aits-name-error"]').inner_text()
          and plain(await page.locator('[data-testid="account-name"]').inner_text()) == account_name)
    await page.fill('[data-testid="aits-name-input"]', "  Asha   Rao ")
    await page.click('[data-testid="aits-name-save"]')
    await page.wait_for_selector('[data-testid="aits-name-sheet"]', state="detached", timeout=15000)
    await page.wait_for_timeout(500)
    row = plain(await page.locator('[data-testid="account-name-button"]').inner_text()).replace("\n", " · ")
    await page.screenshot(path=str(OUT / f"{TAG}_4_account_named.jpeg"), type="jpeg", quality=45)
    check("N5 a saved name is shown at once, and the row now says Change", calls[-1] == "Asha Rao" and plain(await page.locator('[data-testid="account-name"]').inner_text()) == "Asha Rao" and row.startswith("Change your name"), [calls, row])

    # coming back later: the name is the one our server says (the browser stands in for it here)
    await page.goto(BASE + "/account", wait_until="domcontentloaded", timeout=90000)
    await page.wait_for_selector('[data-testid="account-name-button"]', timeout=60000)
    await page.wait_for_function("""() => document.querySelector('[data-testid="account-name"]')?.innerText.trim() === 'Asha Rao'""", timeout=30000)
    check("N6 opened again later, the name is still there", True)
    await page.click('[data-testid="account-name-button"]')
    await page.wait_for_selector('[data-testid="aits-name-input"]', timeout=15000)
    check("N7 the sheet opens on the name, with a way to take it away", await page.input_value('[data-testid="aits-name-input"]') == "Asha Rao" and await page.locator('[data-testid="aits-name-remove"]').count() == 1)
    await page.click('[data-testid="aits-name-remove"]')
    await page.wait_for_selector('[data-testid="aits-name-sheet"]', state="detached", timeout=15000)
    await page.wait_for_timeout(500)
    row = plain(await page.locator('[data-testid="account-name-button"]').inner_text()).replace("\n", " · ")
    check("N8 taking the name away brings the account's own name back", calls[-1] == "" and plain(await page.locator('[data-testid="account-name"]').inner_text()) == account_name and row.startswith("Add your name"), [calls, row])
    for known in ("account-change-pin-button", "account-privacy", "account-deletion", "account-signout-button"):
        if not await page.locator(f'[data-testid="{known}"]').count():
            check(f"N9 the rest of Account is as it was ({known})", False)
            break
    else:
        check("N9 the rest of Account is as it was (PIN, privacy, delete, sign out)", True)


async def main():
    async with async_playwright() as pw:
        browser = await pw.chromium.launch(executable_path="/usr/bin/chromium", args=["--no-sandbox"])
        page = await (await browser.new_context(viewport={"width": W, "height": H})).new_page()
        errors = []
        page.on("console", lambda m: errors.append(m.text[:200]) if m.type == "error" and any(r in m.text for r in RULES) else None)
        page.on("pageerror", lambda e: errors.append("pageerror: " + str(e)[:200]))
        await guards(page)
        await page.goto(BASE + "/entry", wait_until="domcontentloaded", timeout=90000)
        await sign_in(page, aits=None, board=False, width=W, height=H, landing="rapid-fire-home" if ARENA else "home-tile-choice")
        if not ARENA:
            await chapter_wise(page)
        await account(page)
        check("Z1 no write to the website was stopped (none was tried)", stopped == [], stopped)
        odd = sorted({w for w in writes if not re.fullmatch(r"(POST /api/jl/auth/(phone|refresh)|POST /api/rf/access|PUT /api/jl/profile/display-name)", w)})
        check("Z2 the only requests that were not reads: the sign-in, our own pass, and the name (answered by the browser)", odd == [], odd)
        check("Z3 no React rule was broken", errors == [], errors[:3])
        await browser.close()
    print(f"{sum(checks)} of {len(checks)} checks passed; pictures in {OUT}")
    sys.exit(0 if all(checks) else 1)


asyncio.run(main())
