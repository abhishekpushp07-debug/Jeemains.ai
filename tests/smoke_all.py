# Whole-app smoke run (test-only; nothing here changes the app, nothing is written to the website).
# Opens every main screen once as the QA learner and says, screen by screen, whether it came up, whether the red error
# screen showed, whether anything threw, whether the page scrolls sideways, and how long it took to show.
# Run it after every change, before saying "nothing broke".
#
#   import sys; sys.path.insert(0, "/app/tests"); import smoke_all as s
#   await s.run(page)                       # 390 x 844
#   await s.run(page, width=320, height=700)
#
# Rules it keeps: read only. No paper is started, answered or submitted; no name is saved; in Rapid Fire nothing is
# pressed (the All India round is one try a day and goes on the real board). All India days and the leaderboard are
# browser stand-ins (shine_helpers.sign_in), so the series screens have something to show before 9 Dec.
import time

import shine_helpers as sh
from misfire_fixture import REAL_ATTEMPT

# (what it is, the address, a testID that is on the screen once it has come up)
SCREENS = [
    ("Home", "/", "home-screen"),
    ("My Tests", "/tests", "my-tests-screen"),
    ("Rank tab", "/rank", "rank-screen"),
    ("Mission", "/mission", "mission-screen"),
    ("Rapid Fire lobby", "/rapid", "arena-screen"),
    ("All India Series", "/live", "streak-card"),
    ("AITS Leaderboard", "/series-leaderboard", "aits-board-you"),
    ("AITS Analysis", "/series-analysis", "series-analysis-screen"),
    ("Streak share", "/series-share?id=streak", "aits-share-card"),
    ("Misfire", "/misfire", "misfire-screen"),
    ("PYQ papers", "/pyq", "pyq-screen"),
    ("JEE Main hub", "/exam/jee-main", "exam-hub-title"),
    ("Catalogue", "/catalogue", "catalogue-list"),
    ("Result of a finished paper", "/result/" + REAL_ATTEMPT, "result-screen"),
    ("Account", "/account", "account-header"),
    ("Privacy", "/privacy", "privacy-version"),
    ("Change PIN (opened only)", "/change-pin", "change-pin-screen"),
    ("Loading performance", "/performance", "loading-performance-screen"),
    ("Rapid Fire: cups", "/rapid/cup", "cup-hub"),
    ("Rapid Fire: squads", "/rapid/squads", "squads-screen"),
    ("Rapid Fire: vault", "/rapid/vault", "vault-screen"),
    ("Rapid Fire: daily styles", "/rapid/daily-styles", "rf-daily-styles"),
]


async def run(page, width=390, height=844, only=None):
    errors, failed_calls = [], []
    page.on("pageerror", lambda e: errors.append(str(e)[:160]))
    # A 5xx from our own server or the website is worth seeing; 401 before sign-in and 404 for the whole-series
    # leaderboard (the website has none yet) are expected.
    page.on("response", lambda r: failed_calls.append("%d %s" % (r.status, r.url.split("/api/")[-1][:60])) if r.status >= 500 and "/api/" in r.url else None)
    await sh.sign_in(page, aits="done", board=True, width=width, height=height)
    base = page.url.split("/", 3)[0] + "//" + page.url.split("/", 3)[2]
    rows = []
    for name, path, tid in SCREENS:
        if only and name not in only:
            continue
        before, t0 = len(errors), time.time()
        state = "ok"
        try:
            await page.goto(base + path, wait_until="domcontentloaded", timeout=60000)
            await page.wait_for_selector('[data-testid="%s"]' % tid, timeout=40000)
        except Exception as e:
            state = "DID NOT COME UP (%s)" % type(e).__name__
        took = time.time() - t0
        await page.wait_for_timeout(900)
        if await page.locator('[data-testid="error-fallback"]').count():
            state = "RED ERROR SCREEN"
        sideways = await page.evaluate("() => document.scrollingElement.scrollWidth > window.innerWidth + 1")
        threw = errors[before:]
        if state == "ok" and threw:
            state = "came up, but threw"
        if state == "ok" and sideways:
            state = "came up, but scrolls sideways"
        rows.append((name, state, took, threw))
        print("%-30s %-34s %5.1f s %s" % (name, state, took, ("| " + threw[0]) if threw else ""))
    bad = [r for r in rows if r[1] != "ok"]
    print("SMOKE %dx%d: %d screens, %d not ok%s | server errors seen: %s" % (width, height, len(rows), len(bad), (" -> " + ", ".join(r[0] for r in bad)) if bad else "", failed_calls[:6] or "none"))
    return rows
