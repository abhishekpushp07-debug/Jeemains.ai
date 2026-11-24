# Iteration 141 follow-up (main agent): the checks the testing agent's run did not report. Test-only; nothing here changes
# the app and nothing is written to the website (stand-in days and class answered by the browser; no paper is started,
# no name is saved).
#
#   import sys; sys.path.insert(0, "/app/tests"); import iter141_followup as f
#   await f.run(page)                    # 320 x 700, variant "done": every check below
#   await f.variant(page, "live")        # a fresh browser context per variant: the flame bar's words and hourglass
import shine_helpers as sh

OUT = []


def check(name, ok, detail=""):
    OUT.append((name, bool(ok)))
    print(("PASS  " if ok else "FAIL  ") + name + ((" | " + str(detail)[:220]) if detail != "" else ""))


async def text(page, tid):
    return (await page.inner_text('[data-testid="%s"]' % tid)).strip()


async def gone(page, tid, ms=1200):
    try:
        await page.wait_for_selector('[data-testid="%s"]' % tid, timeout=ms)
        return False
    except Exception:
        return True


async def no_sideways(page):
    return await page.evaluate("() => { const e = document.scrollingElement; return e.scrollWidth <= window.innerWidth + 1; }")


async def clipped(page, tid):
    """True when the words of this element do not fit in the lines it is given."""
    return await page.evaluate("(t) => { const e = document.querySelector('[data-testid=\"' + t + '\"]'); return !!e && e.scrollHeight > e.clientHeight + 1; }", tid)


async def run(page, width=320, height=700):
    errors = []
    page.on("pageerror", lambda e: errors.append(str(e)[:200]))
    calls = []
    await sh.sign_in(page, aits="done", board=True, calls=calls, width=width, height=height)

    # ---- /live at this width
    await page.click('[data-testid="home-tile-live"]')
    await page.wait_for_selector('[data-testid="streak-card"]', timeout=30000)
    await page.wait_for_timeout(1200)
    check("live: no sideways scroll", await no_sideways(page))
    check("flame line fits", not await clipped(page, "streak-flame-line"), await text(page, "streak-flame-line"))
    box = await page.locator('[data-testid="streak-current"]').bounding_box()
    card = await page.locator('[data-testid="streak-card"]').bounding_box()
    check("flame bar inside the streak card", box and card and box["x"] >= card["x"] - 1 and box["x"] + box["width"] <= card["x"] + card["width"] + 1, box)
    for tid in ("streak-done", "streak-best", "streak-skipped", "streak-cup-7", "streak-cup-62", "series-calendar", "series-open-leaderboard"):
        check("live still has " + tid, await page.locator('[data-testid="%s"]' % tid).count() == 1)
    check("live day strip chips", await page.locator('[data-testid^="series-chip-"]').count() >= 10)

    # ---- Rank journey at this width; point 2 opens Day 2
    await page.locator('[data-testid="series-trend-mode-rank"]').scroll_into_view_if_needed()
    await page.click('[data-testid="series-trend-mode-rank"]')
    await page.wait_for_selector('[data-testid="series-rank-point-2"]', timeout=20000)
    await page.wait_for_timeout(1500)
    check("rank journey: 8 points", await page.locator('[data-testid^="series-rank-point-"]').count() == 8)
    check("rank journey: status fits", not await clipped(page, "series-rank-status"), await text(page, "series-rank-status"))
    check("rank journey: no sideways scroll", await no_sideways(page))
    before = len(calls)
    await page.click('[data-testid="series-trend-mode-score"]')
    await page.wait_for_selector('[data-testid="series-trend-point-2"]', timeout=8000)
    await page.click('[data-testid="series-trend-mode-rank"]')
    await page.wait_for_selector('[data-testid="series-rank-point-2"]', timeout=8000)
    await page.wait_for_timeout(800)
    check("rank journey: nothing asked again on reopening", len(calls) - before == 0, len(calls) - before)
    await page.click('[data-testid="series-rank-point-2"]')
    await page.wait_for_selector('[data-testid="aits-board-you"]', timeout=20000)
    check("point 2 opens the leaderboard on Day 2", "DAY 2" in (await text(page, "aits-board-you")).upper(), (await text(page, "aits-board-you"))[:60])
    check("leaderboard: no sideways scroll", await no_sideways(page))

    # ---- Aap vs: neighbours, own row, search, day switch
    await page.click('[data-testid="aits-board-tab-around"]')
    await page.wait_for_selector('[data-testid="aits-board-around"]', timeout=10000)
    rows = page.locator('[data-testid="aits-board-around"] [data-testid^="aits-board-row-"]')
    n = await rows.count()
    mine = [i for i in range(n) if "AAP" in (await rows.nth(i).inner_text())]
    check("aas-paas: own row is listed once", len(mine) == 1, (n, mine))
    await rows.nth(mine[0]).scroll_into_view_if_needed()
    await rows.nth(mine[0]).click(force=True)
    check("own row opens no sheet", await gone(page, "aits-versus-sheet"))
    await rows.nth(n - 1).scroll_into_view_if_needed()
    await rows.nth(n - 1).click()
    await page.wait_for_selector('[data-testid="aits-versus-sheet"]', timeout=8000)
    gap = await text(page, "aits-versus-gap")
    check("a student below: 'Aap ... aage ho.'", gap.startswith("Aap ") and gap.endswith("aage ho."), gap)
    check("versus sheet says the day", "DAY 2" in await text(page, "aits-versus-when"), await text(page, "aits-versus-when"))
    check("versus sheet: no sideways scroll", await no_sideways(page))
    await page.click('[data-testid="aits-versus-sheet-backdrop"]', position={"x": 10, "y": 10})
    check("backdrop closes the sheet", await page.locator('[data-testid="aits-versus-sheet"]').count() == 0 or await gone(page, "aits-versus-sheet", 800))
    await rows.nth(0).scroll_into_view_if_needed()
    await rows.nth(0).click()
    await page.wait_for_selector('[data-testid="aits-versus-sheet"]', timeout=8000)
    gap = await text(page, "aits-versus-gap")
    check("a student above: '... aapse N marks aage hai.'", "aapse" in gap and gap.endswith("aage hai."), gap)
    await page.click('[data-testid="aits-versus-sheet-close"]')
    await page.wait_for_selector('[data-testid="aits-versus-sheet"]', state="detached", timeout=8000)
    unnamed = [i for i in range(n) if "Learner " in (await rows.nth(i).inner_text()) and i not in mine]
    if unnamed:
        await rows.nth(unnamed[0]).scroll_into_view_if_needed()
        await rows.nth(unnamed[0]).click()
        await page.wait_for_selector('[data-testid="aits-versus-sheet"]', timeout=8000)
        check("student without a name: no follow button, the note says why", await page.locator('[data-testid="aits-versus-follow"]').count() == 0 and "naam nahi rakha" in await text(page, "aits-versus-note"))
        await page.click('[data-testid="aits-versus-close"]')
        await page.wait_for_selector('[data-testid="aits-versus-sheet"]', state="detached", timeout=8000)

    await page.click('[data-testid="aits-board-tab-find"]')
    await page.fill('[data-testid="aits-board-search"]', "Arjun")
    await page.wait_for_selector('[data-testid="aits-board-found"] [data-testid^="aits-board-row-"]', timeout=10000)
    await page.locator('[data-testid="aits-board-found"] [data-testid^="aits-board-row-"]').first.click()
    await page.wait_for_selector('[data-testid="aits-versus-sheet"]', timeout=8000)
    check("search result opens the sheet", True)
    # a student with a name: "Har din mein yahi naam dhoondo" puts the name into Dhoondo, and it stays when the day changes
    title = (await page.inner_text('[data-testid="aits-versus-sheet"]')).split("\n")[0]
    friend = title.replace("Aap vs ", "").strip()
    check("named student: follow button is offered", await page.locator('[data-testid="aits-versus-follow"]').count() == 1, friend)
    await page.click('[data-testid="aits-versus-follow"]')
    await page.wait_for_selector('[data-testid="aits-versus-sheet"]', state="detached", timeout=8000)
    await page.wait_for_selector('[data-testid="aits-board-found"] [data-testid^="aits-board-row-"]', timeout=10000)
    check("follow: the name is in the search box", (await page.input_value('[data-testid="aits-board-search"]')) == friend[:20], await page.input_value('[data-testid="aits-board-search"]'))
    check("follow: the hint about changing the day shows", await page.locator('[data-testid="aits-board-find-days"]').count() == 1)
    row_text = await page.locator('[data-testid="aits-board-found"] [data-testid^="aits-board-row-"]').first.inner_text()
    check("found rows say how far ahead or behind", ("aage" in row_text) or ("peeche" in row_text) or ("barabar" in row_text), row_text.replace("\n", " ")[:80])
    await page.locator('[data-testid="aits-board-chip-5"]').scroll_into_view_if_needed()
    await page.click('[data-testid="aits-board-chip-5"]')
    await page.wait_for_function("() => (document.querySelector('[data-testid=\"aits-board-you\"]')?.innerText || '').toUpperCase().includes('DAY 5')", timeout=15000)
    await page.wait_for_selector('[data-testid="aits-board-found"] [data-testid^="aits-board-row-"]', timeout=10000)
    check("after a day change the same name is searched in the new day", (await page.input_value('[data-testid="aits-board-search"]')) == friend[:20] and friend in await page.inner_text('[data-testid="aits-board-found"]'))
    await page.locator('[data-testid="aits-board-found"] [data-testid^="aits-board-row-"]').first.click()
    await page.wait_for_selector('[data-testid="aits-versus-sheet"]', timeout=8000)
    check("the new day's sheet is for Day 5", "DAY 5" in await text(page, "aits-versus-when"))
    await page.click('[data-testid="aits-versus-close"]')
    await page.wait_for_selector('[data-testid="aits-versus-sheet"]', state="detached", timeout=8000)
    await page.locator('[data-testid="aits-board-chip-2"]').scroll_into_view_if_needed()
    await page.click('[data-testid="aits-board-chip-2"]')
    await page.wait_for_function("() => (document.querySelector('[data-testid=\"aits-board-you\"]')?.innerText || '').toUpperCase().includes('DAY 2')", timeout=15000)
    await page.fill('[data-testid="aits-board-search"]', "25")
    await page.wait_for_selector('[data-testid="aits-board-found"] [data-testid^="aits-board-row-"]', timeout=10000)
    check("search by Rank still answers", await page.locator('[data-testid="aits-board-found"] [data-testid^="aits-board-row-"]').count() == 1)

    await page.locator('[data-testid="aits-board-chip-9"]').scroll_into_view_if_needed()
    await page.click('[data-testid="aits-board-chip-9"]')
    await page.wait_for_function("() => (document.querySelector('[data-testid=\"aits-board-you\"]')?.innerText || '').toUpperCase().includes('DAY 9')", timeout=15000)
    check("day switch: no sheet left open", await page.locator('[data-testid="aits-versus-sheet"]').count() == 0)
    await page.click('[data-testid="aits-board-tab-top"]')
    await page.wait_for_selector('[data-testid="aits-board-podium-1"]', timeout=10000)
    await page.locator('[data-testid="aits-board-podium-2"]').click()
    await page.wait_for_selector('[data-testid="aits-versus-sheet"]', timeout=8000)
    check("new day: podium step opens the sheet for Day 9", "DAY 9" in await text(page, "aits-versus-when"))
    await page.click('[data-testid="aits-versus-close"]')
    await page.wait_for_selector('[data-testid="aits-versus-sheet"]', state="detached", timeout=8000)

    # ---- what was there before: name sheet, Rank share
    await page.locator('[data-testid="aits-board-name-edit"]').scroll_into_view_if_needed()
    await page.click('[data-testid="aits-board-name-edit"]')
    await page.wait_for_selector('[data-testid="aits-name-sheet"]', timeout=8000)
    await page.click('[data-testid="aits-name-cancel"]')
    await page.wait_for_selector('[data-testid="aits-name-sheet"]', state="detached", timeout=8000)
    check("name sheet opens and closes (nothing saved)", True)
    await page.click('[data-testid="aits-board-share"]')
    await page.wait_for_selector('[data-testid="aits-share-card"]', timeout=20000)
    head = await text(page, "aits-share-header")
    card_text = await text(page, "aits-share-card")
    check("Rank share screen still opens", "Rank share karo" in head and "RANK" in card_text.upper(), head.replace("\n", " / "))
    check("Rank share: no sideways scroll", await no_sideways(page))
    await page.click('[data-testid="aits-share-back"]')
    await page.wait_for_selector('[data-testid="aits-board-you"]', timeout=15000)
    await page.click('[data-testid="aits-board-back"]')
    await page.wait_for_selector('[data-testid="streak-current"]', timeout=20000)

    # ---- Streak share: the message on the card
    await page.locator('[data-testid="streak-current"]').scroll_into_view_if_needed()
    await page.click('[data-testid="streak-current"]')
    await page.wait_for_selector('[data-testid="aits-share-card"]', timeout=20000)
    check("Streak share: no sideways scroll", await no_sideways(page))
    await page.fill('[data-testid="aits-share-message"]', "Roz ek paper")
    await page.wait_for_timeout(300)
    check("Streak card shows the typed message", "Roz ek paper" in await text(page, "aits-share-card"))
    await page.fill('[data-testid="aits-share-message"]', "")
    await page.wait_for_timeout(300)
    check("empty message: no quote on the card", "“" not in await text(page, "aits-share-card"))
    await page.click('[data-testid="aits-share-more"]')
    await page.wait_for_timeout(1500)
    check("share button on web: screen still there", await page.locator('[data-testid="aits-share-card"]').count() == 1)
    await page.click('[data-testid="aits-share-back"]')
    await page.wait_for_selector('[data-testid="streak-current"]', timeout=20000)

    # ---- AITS Analysis and the other tabs still open
    await page.locator('[data-testid="series-open-analysis-list"]').scroll_into_view_if_needed()
    await page.click('[data-testid="series-open-analysis-list"]')
    await page.wait_for_selector('[data-testid="series-analysis-screen"]', timeout=20000)
    check("AITS Analysis opens", True)
    await page.go_back()
    await page.wait_for_selector('[data-testid="streak-card"]', timeout=20000)
    await page.click('[data-testid="header-back-button"]')
    await page.wait_for_selector('[data-testid="home-screen"]', timeout=20000)
    # Rapid Fire last: its arena has its own bar (and the All India popup), so there is no Home tab to press from it.
    for tab, screen in (("tab-tests", "my-tests-screen"), ("tab-rank", "rank-screen"), ("tab-mission", "mission-screen"), ("tab-rapid", "arena-screen")):
        await page.click('[data-testid="%s"]' % tab)
        try:
            await page.wait_for_selector('[data-testid="%s"]' % screen, timeout=25000)
            await page.wait_for_timeout(1200)
            check("tab opens: " + screen, True)
        except Exception as e:
            check("tab opens: " + screen, False, repr(e)[:120])
    check("no page error in the whole run", not errors, errors[:3])
    bad = [n for n, ok in OUT if not ok]
    print("TOTAL %d checks, %d failed %s" % (len(OUT), len(bad), bad))


async def variant(page, name, width=390, height=844):
    """A fresh browser context (nothing kept from another variant): what the flame bar says for this state of today."""
    ctx = await page.context.browser.new_context(viewport={"width": width, "height": height})
    p = await ctx.new_page()
    errors = []
    p.on("pageerror", lambda e: errors.append(str(e)[:200]))
    try:
        await p.goto(page.url.split("/", 3)[0] + "//" + page.url.split("/", 3)[2] + "/entry", wait_until="domcontentloaded", timeout=60000)
        await sh.sign_in(p, aits=name, board=True, width=width, height=height)
        await p.click('[data-testid="home-tile-live"]')
        await p.wait_for_selector('[data-testid="streak-current"]', timeout=30000)
        await p.wait_for_timeout(1200)
        line = await text(p, "streak-flame-line")
        glass = await p.locator('[data-testid="streak-hourglass"]').count()
        print("variant %-9s | count %s | hourglass %d | line: %s | clipped %s | page errors %s" % (name, await text(p, "streak-flame-count"), glass, line, await clipped(p, "streak-flame-line"), errors))
        await p.locator('[data-testid="streak-current"]').scroll_into_view_if_needed()
        await p.screenshot(path="/tmp/shots/v_%s.jpg" % name, type="jpeg", quality=20, full_page=False)
        return line, glass
    finally:
        await ctx.close()
