# All India Rapid (daily round) UI checks: test-only Playwright helpers (import into browser automation).
# Nothing here changes the app and nothing reaches the server: the browser itself answers the daily round's calls, so the
# QA learner's real daily round is never started, answered or finished.
#
#     await fake_daily_done(page)        # /rapid/daily opens straight on a finished round: #1 in India, 9/45, with a reward
#                                        # (its Misfires tab gets MISSES: 6 cards shown, 30 never reached)
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


def _miss(i, subject, chapter, prompt, options, outcome, choice, answer, explain, formula=""):
    return {"i": i, "subject": subject, "chapter": chapter, "prompt": prompt, "options": options, "outcome": outcome, "choice": choice,
            "answer": answer, "explain": explain, "formula": formula}


# The Misfires tab's stand-in answer: 9 right of 45, so 36 not right = 6 cards that were shown + 30 never reached.
MISSES = {"day": DAY, "total": 45, "correct": 9, "sealed": 30, "items": [
    _miss(0, "Physics", "Kinematics", "A ball is thrown up at 20 m/s. Time to reach the top (g = 10 m/s^2) is", ["1 s", "2 s", "3 s", "4 s"], "incorrect", 2, 1, "At the top v = 0, so t = u/g = 2 s.", "v = u - gt"),
    _miss(1, "Chemistry", "Chemical Bonding", "Hybridisation of S in SF_6 is", ["sp^3", "sp^3d", "sp^3d^2", "sp^3d^3"], "incorrect", 1, 2, "Six bond pairs and no lone pair: octahedral."),
    _miss(2, "Mathematics", "Limits", "The value of lim x->0 (sin x)/x is", ["0", "1", "infinity", "does not exist"], "timed_out", None, 1, "A standard limit."),
    _miss(4, "Chemistry", "Mole Concept", "Number of molecules in 18 g of water is", ["3.011 x 10^23", "6.022 x 10^23", "1.2 x 10^24", "18"], "skipped", None, 1, "18 g is one mole."),
    _miss(6, "Physics", "Units and Dimensions", "Dimensional formula of force is", ["MLT^-2", "ML^2T^-2", "MLT^-1", "ML^-1T^-2"], "incorrect", 3, 0, "F = ma."),
    _miss(8, "Mathematics", "Quadratic Equations", "The sum of the roots of x^2 - 5x + 6 = 0 is", ["5", "6", "-5", "1"], "timed_out", None, 0, "Sum of roots = -b/a = 5."),
]}


async def fake_daily_done(page, posts=None, rank=1, result=None, misses=MISSES, asked=None):
    """`result` = fields to change in the finished round (e.g. {"correct": 45}); `misses` = the Misfires tab's answer, or an
    HTTP status to answer with instead; `asked` = a list that gets one entry per request for the Misfires."""
    result = {**RESULT, "rank": rank, **(result or {})}

    async def handler(route):
        req = route.request
        path = req.url.split("/api/rf/daily", 1)[1].split("?")[0]
        if posts is not None and req.method == "POST":
            posts.append(path)
        if path == "/board":
            body = {**BOARD, "you": {**BOARD["you"], "rank": rank}}
        elif path in ("/start", "/answer", "/finish"):
            body = {"status": "done", "result": result}
        elif path == "/misses":
            if asked is not None:
                asked.append(req.url)
            if isinstance(misses, int):
                await route.fulfill(status=misses, content_type="application/json", body=json.dumps({"detail": "Could not load the cards. Try again."}))
                return
            body = misses
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
