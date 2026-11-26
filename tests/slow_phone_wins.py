# Slow-phone check, part 4 (26 Nov 2026): the celebrations of a win in their calm form on a phone at Smooth Mode's lowest
# level (STILL), next to the same screens with everything moving:
#   1. the crown celebration of a Knockout Cup          (a made-up finished cup, answered by the browser)
#   2. the diamond flare after 3 correct in a row       (a 4-card sprint whose cards are answered by the browser)
#   3. the reward panel and the level-up moment at the end of that sprint
# Nothing is written: starting and finishing the sprint are answered by the browser, and every other write under
# /api/rf/sessions or /api/rf/cups is stopped and counted (there must be none). One sign-in per run.
#   python3 /app/tests/slow_phone_wins.py
import asyncio
import json
import re
import sys
import time
from pathlib import Path

from dotenv import dotenv_values
from playwright.async_api import async_playwright

sys.path.insert(0, "/app/tests")
from shine_helpers import sign_in  # noqa: E402

BASE = dotenv_values("/app/frontend/.env")["EXPO_PUBLIC_BACKEND_URL"].rstrip("/")
OUT = Path("/tmp/slow_phone"); OUT.mkdir(exist_ok=True)
KEY = "shine.level.v1"
checks = []
REST = ("none", "matrix(1, 0, 0, 1, 0, 0)")  # a layer that is not turned, moved or scaled

CARDS = [{"id": f"standin-card-{i}", "exam": "JEE", "subject": "Physics", "chapter": "Stand-in chapter", "topic": "Stand-in topic",
          "prompt": f"Stand-in card {i + 1}: which option is B?", "formula": "", "options": ["Option A", "Option B", "Option C", "Option D"],
          "answer": 1, "explain": "B is the stand-in answer."} for i in range(4)]
SPRINT = {"id": "standin-sprint", "exam": "JEE", "mode": "fresh", "subject": "Physics", "chapter": None, "status": "active",
          "cards": CARDS, "card_ids": [c["id"] for c in CARDS]}
REWARD = {"xp": 90, "coins": 45, "streak": 1, "level_before": 3, "level_after": 4, "level_up": True, "new_badges": [], "xp_total": 1090,
          "coins_total": 545, "level_floor": 1000, "next_level_xp": 1500, "played": True, "quest_ready": False, "diamonds": {"red": 1}, "phoenix_streak": 4}


def seat(name, you=False, out=True):
    return {"pid": None, "name": name, "avatar": None, "frame": None, "level": 3, "bot": not you, "you": you, "out": out}


def match(a, b, winner, score):
    return {"a": a, "b": b, "winner": winner, "score": score, "duel_id": None, "live": False, "starts_in": 0, "mine": a == 0}


CUP = {"status": "finished", "size": 4, "kind": "open", "label": "Physics · Mixed chapters", "cards": 10, "code": "STAND1", "night": False,
       "players": [seat("Stand-in learner", you=True, out=False), seat("Rival one"), seat("Rival two"), seat("Rival three")],
       "champion": 0, "round": 1, "rounds": [{"name": "Semi-finals", "matches": [match(0, 1, 0, [8, 5]), match(2, 3, 2, [6, 4])]},
                                              {"name": "Final", "matches": [match(0, 2, 0, [9, 7])]}],
       "title_no": 2, "my_crown": {"won": 2, "real": 1}, "real_players": 2, "prize": 100, "gems_won": {}, "spectators": 0, "max_spectators": 100,
       "spectating": False, "expires_in": 0, "my_duel": None, "joined": True, "is_host": False, "can_start": False, "invited": False, "invited_players": []}

RAYS = """() => { const svg = document.querySelector('[data-testid="crown-celebration"] svg'); if (!svg) return null;
  const s = getComputedStyle(svg.parentElement); return { transform: s.transform, opacity: s.opacity }; }"""
LOOK = """(id) => { const el = document.querySelector(`[data-testid="${id}"]`); if (!el) return null;
  const s = getComputedStyle(el); return { transform: s.transform, opacity: s.opacity }; }"""
# Watches the diamond flare from the moment it appears to the moment it is gone: [ms, the colour wash's opacity, the diamond's transform, its opacity].
FLARE = """() => new Promise((resolve) => {
  const t0 = performance.now(), out = { mounted: null, appeared: null, lasted: null, samples: [] };
  // `mounted` = the flare was put on the page at all, even if it came and went between two looks.
  const seen = new MutationObserver((list) => { for (const m of list) for (const n of m.addedNodes)
    if (n.nodeType === 1 && (n.matches('[data-testid="rf-gem-flare"]') || n.querySelector('[data-testid="rf-gem-flare"]'))) out.mounted = Math.round(performance.now() - t0); });
  seen.observe(document.body, { childList: true, subtree: true });
  const end = () => { seen.disconnect(); resolve(out); };
  const tick = () => {
    const el = document.querySelector('[data-testid="rf-gem-flare"]'), now = performance.now() - t0;
    if (el && out.appeared === null) out.appeared = Math.round(now);
    if (el && el.children.length >= 3) {
      const wash = getComputedStyle(el.children[1]), body = getComputedStyle(el.children[2]);
      out.samples.push([Math.round(now - out.appeared), Number(wash.opacity), body.transform, Number(body.opacity)]);
    }
    if (!el && out.appeared !== null) { out.lasted = Math.round(now - out.appeared); return end(); }
    if (!el && out.mounted !== null && now - out.mounted > 400) return end();
    if (now > 8000) return end();
    setTimeout(tick, 40);
  };
  tick();
})"""
# Watches the reward panel from the moment it appears: the XP number as it counts, the burst's pieces, the level-up moment.
REWARD_WATCH = """() => new Promise((resolve) => {
  const t0 = performance.now(), out = { first: null, texts: [], burst_panel: null, burst_level_up: 0, level_up: false };
  const pieces = (root) => root ? [...root.querySelectorAll('div')].filter((d) => { const s = getComputedStyle(d);
    return s.position === 'absolute' && s.width === '10px' && s.height === '10px'; }).length : 0;
  const tick = () => {
    const xp = document.querySelector('[data-testid="reward-xp"]'), now = performance.now() - t0;
    if (xp) {
      if (out.first === null) { out.first = Math.round(now); out.burst_panel = pieces(document.querySelector('[data-testid="reward-panel"]')); }
      const over = document.querySelector('[data-testid="level-up-overlay"]');
      if (over) { out.level_up = true; out.burst_level_up = Math.max(out.burst_level_up, pieces(over)); }
      out.texts.push([Math.round(now - out.first), xp.textContent]);
      if (now - out.first > 1500) return resolve(out);
    }
    if (now > 25000) return resolve(out);
    setTimeout(tick, 50);
  };
  tick();
})"""


def check(name, ok, detail=""):
    checks.append(ok)
    print(("PASS " if ok else "FAIL ") + name + (" | " + str(detail) if detail != "" else ""))


async def count(page, test_id):
    return await page.locator(f'[data-testid="{test_id}"]').count()


async def text(page, test_id):
    return (await page.locator(f'[data-testid="{test_id}"]').first.inner_text()).replace("\n", " ")


async def stand_ins(page, cid, seen):
    """`seen` gets: answered = what the browser answered, stopped = writes that were stopped, sent = the results the app sent."""
    async def cups(route):
        req = route.request
        path = req.url.split("/api/rf/cups", 1)[1].split("?")[0]
        if req.method == "GET" and path == "/" + cid:
            seen["answered"].append("GET /cups/<stand-in>")
            await route.fulfill(status=200, content_type="application/json", body=json.dumps({**CUP, "id": cid}))
        elif req.method == "GET":
            await route.continue_()  # the learner's own cup list: read only
        else:
            seen["stopped"].append(req.method + " /cups" + path)
            await route.abort()

    async def sessions(route):
        req = route.request
        path = req.url.split("/api/rf/sessions", 1)[1].split("?")[0]
        if req.method == "POST" and path == "":
            seen["answered"].append("POST /sessions")
            await route.fulfill(status=200, content_type="application/json", body=json.dumps(SPRINT))
        elif req.method == "POST" and path == "/standin-sprint/complete":
            rows = json.loads(req.post_data or "{}").get("results", [])
            seen["sent"].append([[r.get("card_id"), r.get("outcome"), r.get("choice")] for r in rows])
            n = lambda k: sum(r.get("outcome") == k for r in rows)  # noqa: E731
            summary = {"total": len(CARDS), "correct": n("correct"), "incorrect": n("incorrect"), "skipped": n("skipped") + len(CARDS) - len(rows), "timed_out": n("timed_out"),
                       "answered": n("correct") + n("incorrect"), "score": n("correct"),
                       "accuracy": round(100 * n("correct") / (n("correct") + n("incorrect")), 1) if n("correct") + n("incorrect") else None, "revise_topics": []}
            seen["answered"].append("POST /sessions/<stand-in>/complete")
            await route.fulfill(status=200, content_type="application/json",
                                body=json.dumps({**SPRINT, "status": "completed", "results": rows, "summary": summary, "reward": REWARD}))
        elif req.method == "GET":
            await route.continue_()
        else:
            seen["stopped"].append(req.method + " /sessions" + path)
            await route.abort()

    await page.route(re.compile(r".*/api/rf/cups(/|\?|$).*"), cups)
    await page.route(re.compile(r".*/api/rf/sessions(/|\?|$).*"), sessions)


RULES = ("Rendered more hooks", "Rendered fewer hooks", "order of Hooks", "Cannot update a component", "Maximum update depth", "state update on an unmounted", "state update on a component that")
# Does the page scroll sideways, and is any of these parts cut off at the left or right edge of the phone?
FITS = """(ids) => ({ sideways: document.scrollingElement.scrollWidth > window.innerWidth + 1,
  cut: ids.filter((id) => { const el = document.querySelector(`[data-testid="${id}"]`); if (!el) return true;
    const b = el.getBoundingClientRect(); return b.left < -1 || b.right > window.innerWidth + 1 || b.width < 2; }) })"""
FLARE_COUNT = """() => { window.__flares = 0; new MutationObserver((list) => { for (const m of list) for (const n of m.addedNodes)
  if (n.nodeType === 1 && (n.matches('[data-testid="rf-gem-flare"]') || n.querySelector('[data-testid="rf-gem-flare"]'))) window.__flares++; })
  .observe(document.body, { childList: true, subtree: true }); }"""


async def card_no(page, n):
    # The counter reads "Card 2 of 4" on a usual phone and "2 / 4" on a narrow one (the app's own short form).
    await page.wait_for_function(f"/(^|\\D){n} (of|\\/) 4$/.test((document.querySelector('[data-testid=\"rf-card-counter\"]')?.textContent || '').trim())", timeout=15000)


async def wins(p, tag, kept=None, reduce=False, width=390, height=844):
    browser = await p.chromium.launch(executable_path="/usr/bin/chromium", args=["--no-sandbox"])
    ctx = await browser.new_context(viewport={"width": width, "height": height}, reduced_motion="reduce" if reduce else "no-preference")
    if kept:
        await ctx.add_init_script(f"localStorage.setItem('{KEY}', {json.dumps(json.dumps(kept))});")
    page = await ctx.new_page()
    errors, seen, got, console = [], {"answered": [], "stopped": [], "sent": []}, {"fits": {}}, []
    page.on("pageerror", lambda e: errors.append(str(e)[:200]))
    page.on("console", lambda m: console.append(m.text[:300]) if m.type in ("error", "warning") else None)
    cid = f"standin-{tag}-{int(time.time())}"
    await stand_ins(page, cid, seen)
    await page.goto(BASE + "/entry", wait_until="domcontentloaded", timeout=90000)
    await sign_in(page, aits=None, board=False, width=width, height=height)

    # 1. The crown celebration of a cup just won
    await page.goto(BASE + "/rapid/cup/" + cid, wait_until="domcontentloaded", timeout=90000)
    await page.wait_for_selector('[data-testid="crown-celebration"]', timeout=60000)
    await page.wait_for_timeout(2800)  # the crown has landed by now
    got["crown_parts"] = [await count(page, "crown-celebration-" + t) for t in ("crown", "kicker", "title", "chip", "line", "see", "close")]
    got["crown_words"] = [await text(page, "crown-celebration-kicker"), await text(page, "crown-celebration-chip")]
    got["crown_confetti"] = await count(page, "rf-confetti")
    one = await page.evaluate(RAYS)
    await page.wait_for_timeout(600)
    got["rays"] = await page.evaluate(RAYS)
    got["rays_move"] = one != got["rays"]
    got["crown"] = await page.evaluate(LOOK, "crown-celebration-crown")
    got["fits"]["crown"] = await page.evaluate(FITS, ["crown-celebration-" + t for t in ("crown", "kicker", "title", "chip", "line", "see", "close")])
    await page.screenshot(path=str(OUT / f"{tag}_crown.jpeg"), type="jpeg", quality=40)
    await page.click('[data-testid="crown-celebration-close"]')
    await page.wait_for_selector('[data-testid="crown-celebration"]', state="detached", timeout=15000)
    got["cup_after"] = [await count(page, "cup-champion"), await text(page, "cup-champion-name"), await count(page, "cup-bracket")]
    got["crown_seen_kept"] = await page.evaluate(f"Object.keys(localStorage).filter((k) => k.includes('rf.crown.{cid}')).length")

    # 2. A sprint of 4 stand-in cards, every answer correct: the red diamond lights after the third
    await page.goto(BASE + "/rapid/session?subject=Physics&n=10", wait_until="domcontentloaded", timeout=90000)
    await page.wait_for_selector('[data-testid="rf-card"]', timeout=60000)
    got["streak_counts"], flare = [], None
    for k in range(3):
        await card_no(page, k + 1)
        got["streak_counts"].append(await text(page, "rf-streak-count"))
        if k == 2:
            flare = asyncio.create_task(page.evaluate(FLARE))
        await page.click('[data-testid="rf-option-1"]')
    got["flare"] = await flare
    await card_no(page, 4)
    got["streak_counts"].append(await text(page, "rf-streak-count"))
    got["fits"]["sprint"] = await page.evaluate(FITS, ["rf-card", "rf-option-0", "rf-option-3", "rf-skip-button", "rf-next-button", "rf-streak-gem"])
    await page.screenshot(path=str(OUT / f"{tag}_sprint.jpeg"), type="jpeg", quality=40)

    # 3. The last card ends the sprint: the reward panel and the level-up moment
    watch = asyncio.create_task(page.evaluate(REWARD_WATCH))
    await page.click('[data-testid="rf-option-1"]')
    got["reward"] = await watch
    await page.screenshot(path=str(OUT / f"{tag}_reward.jpeg"), type="jpeg", quality=40)
    if await count(page, "level-up-overlay"):
        await page.click('[data-testid="level-up-overlay"]')
        await page.wait_for_selector('[data-testid="level-up-overlay"]', state="detached", timeout=15000)
    got["summary"] = [await text(page, "rf-summary-score"), await text(page, "reward-xp"), await text(page, "reward-coins"), await count(page, "reward-level-up"),
                      await count(page, "reward-xp-bar"), await count(page, "rf-diamonds-won-red")]
    got["fits"]["reward"] = await page.evaluate(FITS, ["reward-panel", "reward-xp", "reward-coins", "reward-streak", "reward-level-up", "reward-xp-bar", "rf-diamonds-won", "rf-summary-score"])
    await page.screenshot(path=str(OUT / f"{tag}_summary.jpeg"), type="jpeg", quality=40)
    await page.click('[data-testid="rf-done"]')
    await page.wait_for_selector('[data-testid="rapid-fire-home"]', timeout=30000)
    got["lobby_after"] = await count(page, "rapid-fire-home")

    # 4. A second sprint the ordinary way: right, wrong, skip, right. No three in a row, so no diamond and no flare.
    mixed = {}
    await page.goto(BASE + "/rapid/session?subject=Physics&n=10&r=mixed", wait_until="domcontentloaded", timeout=90000)
    await page.wait_for_selector('[data-testid="rf-card"]', timeout=60000)
    await page.evaluate(FLARE_COUNT)
    await card_no(page, 1)
    await page.click('[data-testid="rf-option-1"]')
    await card_no(page, 2)
    mixed["after_right"] = await text(page, "rf-streak-count")
    await page.click('[data-testid="rf-option-0"]')
    began = time.monotonic()
    await page.wait_for_selector('[data-testid="rf-feedback"]', timeout=5000)
    mixed["feedback"] = (await text(page, "rf-feedback"))[:11]
    await card_no(page, 3)
    mixed["wrong_stays_ms"] = round((time.monotonic() - began) * 1000)
    mixed["after_wrong"] = await text(page, "rf-streak-count")
    await page.click('[data-testid="rf-skip-button"]')
    await card_no(page, 4)
    mixed["after_skip"] = await text(page, "rf-streak-count")
    await page.click('[data-testid="rf-option-1"]')
    await page.wait_for_selector('[data-testid="reward-panel"]', timeout=20000)
    if await count(page, "level-up-overlay"):
        await page.click('[data-testid="level-up-overlay"]')
        await page.wait_for_selector('[data-testid="level-up-overlay"]', state="detached", timeout=15000)
    mixed["score"] = (await text(page, "rf-summary-score")).replace(" ", "")
    mixed["review_missed"] = await count(page, "rf-review-missed")
    mixed["flares"] = await page.evaluate("window.__flares")
    got["mixed"] = mixed
    await page.click('[data-testid="rf-done"]')
    await page.wait_for_selector('[data-testid="rapid-fire-home"]', timeout=30000)
    got["react_rules"] = sorted({c[:160] for c in console if any(r in c for r in RULES)})
    got["console"] = sorted({c[:110] for c in console})[:10]
    got["kept"] = await page.evaluate(f"localStorage.getItem('{KEY}')")
    await browser.close()
    return got, errors, seen


def common(tag, got, errors, seen, skipped=False):
    check(f"{tag}: no page error and no React rule warning in the console", not errors and not got["react_rules"], (errors, got["react_rules"]))
    check(f"{tag}: both sprints were started and finished by the browser, no write was stopped or sent on",
          seen["answered"].count("POST /sessions") == 2 and seen["answered"].count("POST /sessions/<stand-in>/complete") == 2 and not seen["stopped"], (sorted(set(seen["answered"])), seen["stopped"]))
    check(f"{tag}: the app sent the four answers as given (all correct, option B)", seen["sent"][:1] == [[[c["id"], "correct", 1] for c in CARDS]], seen["sent"][:1])
    ids = [c["id"] for c in CARDS]
    check(f"{tag}: the second sprint sent right, wrong (A), skipped, right, exactly as pressed",
          seen["sent"][1:] == [[[ids[0], "correct", 1], [ids[1], "incorrect", 0], [ids[2], "skipped", None], [ids[3], "correct", 1]]], seen["sent"][1:])
    m = got["mixed"]
    check(f"{tag}: in it the streak goes 1/3, back to 0/3 after the wrong answer and stays 0/3 after the skip; the wrong answer stays to be read; 2 / 4; no flare",
          [m["after_right"], m["after_wrong"], m["after_skip"]] == ["1/3", "0/3", "0/3"] and m["feedback"] == "✗ Incorrect" and 2200 <= m["wrong_stays_ms"] <= 3600 and m["score"] == "2/4"
          and m["review_missed"] == 1 and m["flares"] == 0, m)
    check(f"{tag}: nothing scrolls sideways and nothing is cut at the edges (crown celebration, card, result)",
          all(not v["sideways"] and not v["cut"] for v in got["fits"].values()), got["fits"])
    check(f"{tag}: every part of the crown celebration is there, with its words", all(n == 1 for n in got["crown_parts"]) and got["crown_words"][0] == "CROWN #2" and "2 CUPS" in got["crown_words"][1],
          (got["crown_parts"], got["crown_words"]))
    check(f"{tag}: the crown is drawn at its place", got["crown"] is not None and float(got["crown"]["opacity"]) == 1.0 and got["crown"]["transform"] in REST, got["crown"])
    check(f"{tag}: Continue closes the celebration, the cup and its bracket are under it, and it counts as seen", got["cup_after"] == [1, "YOU WON THE CUP!", 1] and got["crown_seen_kept"] == 1, (got["cup_after"], got["crown_seen_kept"]))
    check(f"{tag}: the streak counts up beside the card (0/3, 1/3, 2/3, then 3/5)", got["streak_counts"] == ["0/3", "1/3", "2/3", "3/5"], got["streak_counts"])
    f = got["flare"]
    if skipped:
        # Under the phone's own Reduce Motion, Reanimated ends timed motion at once, so the flare's one second is over as it starts.
        check(f"{tag}: the diamond flare is put up and is over at once", f["mounted"] is not None and (f["lasted"] is None or f["lasted"] < 250), (f["mounted"], f["appeared"], f["lasted"], len(f["samples"])))
    else:
        check(f"{tag}: the diamond flare plays for its one second and the diamond is fully drawn in it", f["appeared"] is not None and f["lasted"] is not None and 850 <= f["lasted"] <= 1500
              and max(s[3] for s in f["samples"]) == 1.0, (f["appeared"], f["lasted"], len(f["samples"])))
    check(f"{tag}: the result shows 4 / 4, +90 XP, +45 coins, the level-up line, the XP bar and the red diamond; Done goes to the lobby",
          got["summary"][0].replace(" ", "") == "4/4" and got["summary"][1].startswith("+90") and got["summary"][2].startswith("+45") and got["summary"][3:] == [1, 1, 1] and got["lobby_after"] == 1,
          (got["summary"], got["lobby_after"]))
    check(f"{tag}: the level-up moment is shown", got["reward"]["level_up"] is True, got["reward"]["level_up"])


def calm(tag, got):
    check(f"{tag}: no confetti, the sunburst rests and is drawn", got["crown_confetti"] == 0 and not got["rays_move"] and got["rays"] is not None and got["rays"]["transform"] in REST
          and float(got["rays"]["opacity"]) == 1.0, (got["crown_confetti"], got["rays_move"], got["rays"]))
    f = got["flare"]
    if f["samples"]:
        check(f"{tag}: the flare has no colour wash and the diamond does not pop", max(s[1] for s in f["samples"]) == 0 and all(s[2] in REST for s in f["samples"]), (max(s[1] for s in f["samples"]), sorted({s[2] for s in f["samples"]})[:3]))
    r = got["reward"]
    check(f"{tag}: the XP shows its final number at once and no burst flies", all(t[1].startswith("+90") for t in r["texts"]) and r["burst_panel"] == 0 and r["burst_level_up"] == 0, (r["texts"][0], r["burst_panel"], r["burst_level_up"]))


def moving(tag, got):
    check(f"{tag}: confetti falls (the cup's and the celebration's) and the sunburst turns", got["crown_confetti"] == 2 and got["rays_move"], (got["crown_confetti"], got["rays_move"], got["rays"]))
    f = got["flare"]
    check(f"{tag}: the flare washes the screen in the diamond's colour and the diamond pops", max(s[1] for s in f["samples"]) > 0.05 and any(s[2] not in REST for s in f["samples"]),
          (max(s[1] for s in f["samples"]), sorted({s[2] for s in f["samples"]})[:3]))
    r = got["reward"]
    check(f"{tag}: the XP counts up, the burst flies in the panel and in the level-up moment", r["texts"][0][1] != r["texts"][-1][1] and r["texts"][-1][1].startswith("+90") and r["burst_panel"] == 16 and r["burst_level_up"] == 16,
          (r["texts"][0], r["texts"][-1], r["burst_panel"], r["burst_level_up"]))


async def main():
    async with async_playwright() as p:
        if sys.argv[1:] == ["reduce"]:  # `slow_phone_wins.py reduce` = the phone's own Reduce Motion alone (nothing kept by Smooth Mode)
            got, e, s = await wins(p, "W_reduce", reduce=True)
            print("Reduce Motion:   ", json.dumps(got)[:1800])
            common("reduce motion", got, e, s, skipped=True)
            calm("reduce motion", got)
            check("reduce motion: Smooth Mode kept nothing (the calm form comes from the phone's setting alone)", got["kept"] is None, got["kept"])
            return
        if sys.argv[1:] == ["calm"]:  # `slow_phone_wins.py calm` = Smooth Mode's middle level: only the Shine calms, the celebrations still move
            got, e, s = await wins(p, "W_calm", kept=f"1:{int(time.time() * 1000)}")
            print("CALM kept:       ", json.dumps(got)[:1800])
            common("calm level", got, e, s)
            check("calm level: the level is still CALM at the end", (got["kept"] or "").strip('"').startswith("1:"), got["kept"])
            if (got["kept"] or "").strip('"').startswith("1:"):
                moving("calm level", got)
            return
        if sys.argv[1:] == ["narrow"]:  # `slow_phone_wins.py narrow` = the calm forms on a 320-wide phone
            got, e, s = await wins(p, "W_narrow", kept=f"2:{int(time.time() * 1000)}", width=320, height=700)
            print("STILL, 320 wide: ", json.dumps(got)[:1800])
            common("still, 320 wide", got, e, s)
            calm("still, 320 wide", got)
            return
        full, e1, s1 = await wins(p, "W_full")
        print("everything moves:", json.dumps(full)[:1800])
        still, e2, s2 = await wins(p, "W_still", kept=f"2:{int(time.time() * 1000)}")
        print("STILL kept:      ", json.dumps(still)[:1800])
    common("moving", full, e1, s1)
    if full["kept"]:
        print("note: this browser was itself too slow, Smooth Mode kept", full["kept"], "- the 'everything moves' run is not clean, its motion is not judged")
    else:
        moving("moving", full)
    common("still", still, e2, s2)
    calm("still", still)
    check("still: the level stays STILL to the end", (still["kept"] or "").strip('"').startswith("2:"), still["kept"])


asyncio.run(main())
print(f"\n{sum(checks)} of {len(checks)} checks passed; pictures in {OUT}")
sys.exit(0 if all(checks) else 1)
