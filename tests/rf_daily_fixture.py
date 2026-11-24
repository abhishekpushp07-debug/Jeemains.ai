# All India Rapid (daily round) UI checks: test-only Playwright helpers (import into browser automation).
# Nothing here changes the app and nothing reaches the server: the browser itself answers the daily round's calls, so the
# QA learner's real daily round is never started, answered or finished.
#
#     await fake_daily_done(page)        # /rapid/daily opens straight on a finished round: #1 in India, 9/45, with a reward
#     await count_sounds(page)           # from now on every sound the app starts is listed in window.__plays (file names)
#     names = await sounds(page)         # e.g. ["scene_cup", "coin"]
#
# count_sounds() keeps counting after a reload (the list starts empty again on each load).
# The "once a day" memory is localStorage key rf.heard.v1; to pretend it is a new day:
#     await page.evaluate('localStorage.setItem("rf.heard.v1", JSON.stringify(JSON.stringify({card: "2000-01-01", charge: "2000-01-01"})))')
import json
import re
import time

DAY = time.strftime("%Y-%m-%d", time.gmtime(time.time() + 19800))  # today in India
RESULT = {"correct": 9, "total": 45, "ms": 94300, "rank": 1, "players": 1, "day": DAY,
          "reward": {"xp": 90, "coins": 45, "streak": 1, "level_before": 3, "level_after": 3, "level_up": False, "new_badges": [],
                     "xp_total": 520, "coins_total": 345, "level_floor": 400, "next_level_xp": 700, "played": True}}
BOARD = {"day": DAY, "total": 45, "players": 1, "you": {"status": "done", "correct": 9, "ms": 94300, "rank": 1},
         "items": [{"rank": 1, "name": "QA Learner", "pid": None, "avatar": None, "frame": None, "level": 3, "crown": None, "correct": 9, "ms": 94300, "you": True}]}


async def fake_daily_done(page, posts=None, rank=1):
    result = {**RESULT, "rank": rank}

    async def handler(route):
        req = route.request
        path = req.url.split("/api/rf/daily", 1)[1].split("?")[0]
        if posts is not None and req.method == "POST":
            posts.append(path)
        if path == "/board":
            body = {**BOARD, "you": {**BOARD["you"], "rank": rank}}
        elif path in ("/start", "/answer", "/finish"):
            body = {"status": "done", "result": result}
        else:  # the lobby's status: today's round is still open, so the All India card and its popup are offered
            await route.continue_()
            return
        await route.fulfill(status=200, content_type="application/json", body=json.dumps(body))

    await page.route(re.compile(r".*/api/rf/daily(/|\?|$).*"), handler)


PATCH = """
(() => {
  if (window.__plays) return;
  window.__plays = [];
  const play = HTMLMediaElement.prototype.play;
  HTMLMediaElement.prototype.play = function () {
    const src = decodeURIComponent(this.currentSrc || this.src || "");
    const m = /([a-z_]+)(?:\\.[0-9a-f]+)?\\.m4a/.exec(src);
    window.__plays.push(m ? m[1] : (src || "?").slice(-60));
    return play.apply(this, arguments);
  };
})();
"""


async def count_sounds(page):
    await page.add_init_script(PATCH)  # every later load / reload of this page
    await page.evaluate(PATCH)         # the page that is open now


async def sounds(page):
    return await page.evaluate("window.__plays || []")
