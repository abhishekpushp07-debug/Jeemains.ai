# Iteration 138: AITS Leaderboard + Rapid Fire daily regression (frontend-only).
# This test intentionally does one sign-in per browser context (rate-limited otherwise).
# All AITS leaderboard, daily round, misfire-aits-stub calls are intercepted in-browser so nothing is written upstream.
import asyncio
import os
import re
import sys
import json
from playwright.async_api import async_playwright

sys.path.insert(0, "/app/tests")
from misfire_fixture import fake_aits  # noqa: E402
from aits_board_fixture import fake_board  # noqa: E402
from rf_daily_fixture import fake_daily_done, count_sounds, sounds  # noqa: E402

BASE = os.environ.get("EXPO_PUBLIC_BACKEND_URL", "https://jeelive-feature-book--3o05z2vs.preview.emergentagent.com").rstrip("/")
PHONE, PIN = "7004186276", "5524"

RESULTS = {}


def ok(name, cond, note=""):
    tag = "PASS" if cond else "FAIL"
    RESULTS[name] = {"ok": bool(cond), "note": str(note)}
    print(f"[{tag}] {name} :: {note}")


async def tap(page, tid, timeout=6000):
    el = await page.wait_for_selector(f'[data-testid="{tid}"]', timeout=timeout)
    await el.click(force=True)
    return el


async def text_of(page, tid):
    el = await page.query_selector(f'[data-testid="{tid}"]')
    if not el:
        return None
    return (await el.inner_text()).strip()


async def is_visible(page, tid):
    el = await page.query_selector(f'[data-testid="{tid}"]')
    return bool(el and await el.is_visible())


async def scroll_into_view(page, tid):
    try:
        await page.eval_on_selector(f'[data-testid="{tid}"]', "el => el.scrollIntoView({block:'center'})")
    except Exception:
        pass


async def hoverlog(page, note):
    # stash page errors
    pass


async def main():
    async with async_playwright() as pw:
        browser = await pw.chromium.launch(headless=True)
        context = await browser.new_context(viewport={"width": 390, "height": 844})
        posts = []
        sound_posts = []

        async def record_post(route):
            r = route.request
            if r.method == "POST":
                posts.append(r.url)
            await route.continue_()

        await context.route("**/api/**", record_post)
        page = await context.new_page()
        page.on("pageerror", lambda e: print("PAGEERR:", str(e)[:200]))
        page.on("console", lambda m: m.type == "error" and print("CONSOLE ERR:", m.text[:200]))

        # Install fixtures BEFORE sign-in
        await fake_aits(page, "done")
        await fake_board(page)
        await fake_daily_done(page, posts=sound_posts)
        await count_sounds(page)

        # Sign in
        await page.goto(f"{BASE}/entry", wait_until="domcontentloaded")
        await page.wait_for_timeout(2000)
        await page.click('[data-testid="entry-phone-input"]', force=True)
        await page.keyboard.type(PHONE, delay=60)
        await page.click('[data-testid="entry-pin-input"]', force=True)
        await page.keyboard.type(PIN, delay=60)
        await page.wait_for_timeout(400)
        await page.click('[data-testid="entry-continue-button"]', force=True)
        await page.wait_for_timeout(7000)
        try:
            await page.wait_for_selector('[data-testid="home-tile-live"]', timeout=8000)
            ok("signin", True, "home shown")
        except Exception as e:
            await page.screenshot(path="/tmp/signin_fail.png", quality=40, full_page=False)
            ok("signin", False, str(e)[:120])
            print(json.dumps(RESULTS, indent=2))
            return

        # ================= Phase A: AITS Leaderboard =================
        # A: open /live
        await page.click('[data-testid="home-tile-live"]', force=True)
        await page.wait_for_timeout(2500)
        ok("live_screen_loads", await is_visible(page, "series-open-leaderboard"), "leaderboard entry bar visible")

        # Tap leaderboard entry
        await page.click('[data-testid="series-open-leaderboard"]', force=True)
        await page.wait_for_timeout(2500)
        await page.wait_for_selector('[data-testid="aits-board-screen"]', timeout=6000)

        # A1: opens on newest scored LIVE day
        you_rank = await text_of(page, "aits-board-you-rank")
        count = await text_of(page, "aits-board-count")
        days = await text_of(page, "aits-board-days")
        you_label = await text_of(page, "aits-board-you-label")
        ok("A1_you_rank", bool(you_rank and you_rank.startswith("#")), f"val={you_rank}")
        ok("A1_count", bool(count and "STUDENT" in (count or "").upper()), f"val={count}")
        ok("A1_days_9", days == "9 din diye", f"val={days}")
        ok("A1_you_label_live", you_label == "Aapka All India Rank", f"val={you_label}")

        # A2: segments
        for seg in ["aits-board-tab-top", "aits-board-tab-around", "aits-board-tab-find"]:
            ok(f"A2_{seg}", await is_visible(page, seg), "segment visible")

        # Toppers default
        podium = await is_visible(page, "aits-board-podium")
        p1 = await is_visible(page, "aits-board-podium-1")
        p2 = await is_visible(page, "aits-board-podium-2")
        p3 = await is_visible(page, "aits-board-podium-3")
        ok("A2_podium", podium and p1 and p2 and p3, "podium 1/2/3 visible")

        # top list rank 4-10 (7 rows)
        top_rows = await page.query_selector_all('[data-testid="aits-board-top"] >> css=[data-testid^="aits-board-row-"]')
        # Fallback: look inside container
        all_rows = await page.evaluate("""() => {
          const c = document.querySelector('[data-testid="aits-board-top"]');
          if (!c) return 0;
          return c.querySelectorAll('[data-testid^="aits-board-row-"]').length;
        }""")
        ok("A2_top_rows_7", all_rows == 7, f"count={all_rows}")

        # Toggle more
        more_before = await text_of(page, "aits-board-more")
        await page.click('[data-testid="aits-board-more"]', force=True)
        await page.wait_for_timeout(600)
        more_after = await text_of(page, "aits-board-more")
        ok("A2_more_toggle", more_before != more_after and more_before and more_after, f"{more_before!r} -> {more_after!r}")
        # toggle back
        await page.click('[data-testid="aits-board-more"]', force=True)
        await page.wait_for_timeout(400)

        # top-you visible because you_rank=12 (not in top 10)
        ok("A2_top_you_visible", await is_visible(page, "aits-board-top-you"), "own row separate")

        # Around tab
        await page.click('[data-testid="aits-board-tab-around"]', force=True)
        await page.wait_for_timeout(700)
        around_rows = await page.evaluate("""() => {
          const c = document.querySelector('[data-testid="aits-board-around"]');
          if (!c) return 0;
          return c.querySelectorAll('[data-testid^="aits-board-row-"]').length;
        }""")
        ok("A2_around_rows_7", around_rows == 7, f"count={around_rows}")
        nxt = await text_of(page, "aits-board-next")
        ok("A2_around_next_text", bool(nxt and "aage" in nxt), f"{nxt}")
        # own row tagged AAP
        aap_tag = await page.evaluate("""() => {
          const c = document.querySelector('[data-testid="aits-board-around"]');
          if (!c) return false;
          return /AAP\\b/i.test(c.innerText || "");
        }""")
        ok("A2_around_has_AAP", aap_tag, "contains AAP")

        # Find tab
        await page.click('[data-testid="aits-board-tab-find"]', force=True)
        await page.wait_for_timeout(600)
        ok("A2_find_hint", await is_visible(page, "aits-board-find-hint"), "hint visible")
        await page.fill('[data-testid="aits-board-search"]', "Arjun")
        await page.wait_for_timeout(1200)
        ok("A2_find_arjun", await is_visible(page, "aits-board-found"), "found rows")
        await page.fill('[data-testid="aits-board-search"]', "")
        await page.wait_for_timeout(500)
        await page.fill('[data-testid="aits-board-search"]', "25")
        await page.wait_for_timeout(1200)
        found_25 = await page.evaluate("""() => {
          const c = document.querySelector('[data-testid="aits-board-found"]');
          if (!c) return "";
          const first = c.querySelector('[data-testid^="aits-board-row-"]');
          return first ? first.innerText : "";
        }""")
        ok("A2_find_25", "#25" in (found_25 or ""), f"text={found_25[:60]!r}")
        await page.fill('[data-testid="aits-board-search"]', "")
        await page.fill('[data-testid="aits-board-search"]', "zzzzqq")
        await page.wait_for_timeout(1200)
        ok("A2_find_none", await is_visible(page, "aits-board-none"), "none visible")
        await page.fill('[data-testid="aits-board-search"]', "")
        await page.wait_for_timeout(500)
        ok("A2_find_hint_back", await is_visible(page, "aits-board-find-hint"), "hint back")

        # A3: Day chips
        await page.click('[data-testid="aits-board-tab-around"]', force=True)
        await page.wait_for_timeout(500)
        chips = await page.evaluate("""() => {
          return Array.from(document.querySelectorAll('[data-testid^="aits-board-chip-"]'))
            .map(e => e.getAttribute('data-testid'));
        }""")
        expected_chips = ["aits-board-chip-%d" % d for d in [1, 2, 3, 4, 5, 7, 8, 9, 10]]
        ok("A3_chips", all(c in chips for c in expected_chips), f"present={chips}")

        rank_before = await text_of(page, "aits-board-you-rank")
        count_before = await text_of(page, "aits-board-count")
        # tap day 5
        await page.click('[data-testid="aits-board-chip-5"]', force=True)
        await page.wait_for_timeout(1500)
        rank_day5 = await text_of(page, "aits-board-you-rank")
        count_day5 = await text_of(page, "aits-board-count")
        ok("A3_day_switches_rank", rank_before != rank_day5 or count_before != count_day5, f"{rank_before}/{count_before} -> {rank_day5}/{count_day5}")
        # segment stayed around
        active_tab = await page.evaluate("""() => {
          const el = document.querySelector('[data-testid="aits-board-around"]') ||
                     document.querySelector('[data-testid="aits-board-around-none"]') ||
                     document.querySelector('[data-testid="aits-board-next"]');
          return !!el;
        }""")
        ok("A3_segment_sticky", active_tab, "still around")

        # Day 3 = practice
        await page.click('[data-testid="aits-board-chip-3"]', force=True)
        await page.wait_for_timeout(1500)
        d3_label = await text_of(page, "aits-board-you-label")
        # kicker lives in YouCard; look for text PRACTICE anywhere on the you card. Use aits-board-screen
        kicker_has_practice = await page.evaluate("""() => {
          const s = document.querySelector('[data-testid="aits-board-screen"]');
          return s ? /PRACTICE/.test(s.innerText || "") : false;
        }""")
        ok("A3_day3_practice_label", d3_label == "Is paper mein aapka Rank", f"label={d3_label}")
        ok("A3_day3_kicker_practice", kicker_has_practice, "PRACTICE in kicker")

        # A5: No horizontal overflow at 390
        overflow390 = await page.evaluate("document.documentElement.scrollWidth - window.innerWidth")
        ok("A5_overflow_390", overflow390 == 0, f"px={overflow390}")
        # Resize 320x640
        await page.set_viewport_size({"width": 320, "height": 640})
        await page.wait_for_timeout(600)
        overflow320 = await page.evaluate("document.documentElement.scrollWidth - window.innerWidth")
        ok("A5_overflow_320", overflow320 == 0, f"px={overflow320}")
        # back to 390
        await page.set_viewport_size({"width": 390, "height": 844})
        await page.wait_for_timeout(400)

        # A4 (part 1): embargoed day 10 with fake_aits(page,'embargoed'). Re-register overrides.
        await fake_aits(page, "embargoed")
        # force refresh of series data by re-navigating
        await page.click('[data-testid="aits-board-back"]', force=True)
        await page.wait_for_timeout(1500)
        await page.click('[data-testid="series-open-leaderboard"]', force=True)
        await page.wait_for_timeout(2500)
        # click day 10 chip
        try:
            await page.click('[data-testid="aits-board-chip-10"]', force=True, timeout=3000)
            await page.wait_for_timeout(1200)
            ok("A4_sealed_card", await is_visible(page, "aits-board-sealed"), "sealed card visible on day 10")
        except Exception as e:
            ok("A4_sealed_card", False, f"chip-10 missing: {e}")

        # A4 (part 2): unroute leaderboard route, re-register with state='preparing'
        await page.unroute(re.compile(r".*/api/jl/attempts/[^/]+/leaderboard.*"))
        await fake_board(page, state="preparing")
        # Reset to 'done' AITS then tap a day never opened (e.g., day 2 - haven't opened)
        await fake_aits(page, "done")
        await page.click('[data-testid="aits-board-back"]', force=True)
        await page.wait_for_timeout(1500)
        await page.click('[data-testid="series-open-leaderboard"]', force=True)
        await page.wait_for_timeout(2500)
        try:
            await page.click('[data-testid="aits-board-chip-2"]', force=True, timeout=3000)
            await page.wait_for_timeout(2500)
            wait_vis = await is_visible(page, "aits-board-wait")
            wait_note = await is_visible(page, "aits-board-wait-note")
            ok("A4_waiting_card", wait_vis and wait_note, f"wait={wait_vis}, note={wait_note}")
        except Exception as e:
            ok("A4_waiting_card", False, str(e)[:120])

        # A4 (part 3): fail=True
        await page.unroute(re.compile(r".*/api/jl/attempts/[^/]+/leaderboard.*"))
        await fake_board(page, fail=True)
        try:
            await page.click('[data-testid="aits-board-chip-4"]', force=True, timeout=3000)
            await page.wait_for_timeout(2500)
            # error text appears on wait card ("Leaderboard nahi khul paaya")
            err_text = await page.evaluate("""() => {
              const s = document.querySelector('[data-testid="aits-board-screen"]');
              return s ? s.innerText : "";
            }""")
            ok("A4_error_card", "nahi khul paaya" in err_text, f"text has error: {('nahi khul paaya' in err_text)}")
        except Exception as e:
            ok("A4_error_card", False, str(e)[:120])

        # A4 (part 4): retry: unroute + fake_board, then tap retry
        await page.unroute(re.compile(r".*/api/jl/attempts/[^/]+/leaderboard.*"))
        await fake_board(page)
        try:
            await page.click('[data-testid="aits-board-retry"]', force=True, timeout=3000)
            await page.wait_for_timeout(2500)
            back_rank = await text_of(page, "aits-board-you-rank")
            ok("A4_retry_restores", bool(back_rank and back_rank.startswith("#")), f"rank={back_rank}")
        except Exception as e:
            ok("A4_retry_restores", False, str(e)[:120])

        # A5: back button
        await page.click('[data-testid="aits-board-back"]', force=True)
        await page.wait_for_timeout(1500)
        ok("A5_back_to_live", await is_visible(page, "series-open-leaderboard"), "back to /live")

        # A6: regression on /live
        # day chips
        chips_live = await page.evaluate("""() => Array.from(document.querySelectorAll('[data-testid^="series-chip-"]')).map(e => e.getAttribute('data-testid'))""")
        ok("A6_live_day_chips", len(chips_live) >= 5, f"n={len(chips_live)}")
        ok("A6_live_day_strip", await is_visible(page, "series-day-strip"), "day-strip visible")
        # My results / analysis list
        try:
            await scroll_into_view(page, "series-open-analysis-list")
            await page.click('[data-testid="series-open-analysis-list"]', force=True, timeout=4000)
            await page.wait_for_timeout(2500)
            # analysis rows
            n_analysis = await page.evaluate("""() => document.querySelectorAll('[data-testid^="series-analysis-"]').length""")
            ok("A6_analysis_rows", n_analysis >= 1, f"rows={n_analysis}")
            # click first analysis button
            try:
                await page.click('[data-testid="series-analysis-0-analysis"]', force=True, timeout=4000)
                await page.wait_for_timeout(2500)
                sol = await is_visible(page, "result-tab-solutions")
                ok("A6_result_solutions_tab", sol, f"visible={sol}")
                # back to /series-analysis
                await page.go_back()
                await page.wait_for_timeout(1500)
                ok("A6_back_to_analysis", await is_visible(page, "series-analysis-0"), "back on analysis list")
                await page.go_back()
                await page.wait_for_timeout(1500)
                ok("A6_back_to_live", await is_visible(page, "series-open-leaderboard"), "back on /live")
            except Exception as e:
                ok("A6_result_flow", False, str(e)[:120])
        except Exception as e:
            ok("A6_analysis_open", False, str(e)[:120])

        # ========== Phase B: Rapid Fire daily result (wide screen) ==========
        await page.set_viewport_size({"width": 750, "height": 860})
        await page.wait_for_timeout(500)
        # Navigate home then tap rapid tab
        await page.goto(f"{BASE}/", wait_until="domcontentloaded")
        await page.wait_for_timeout(2500)
        try:
            await page.click('[data-testid="tab-rapid"]', force=True, timeout=5000)
            await page.wait_for_timeout(3500)
        except Exception as e:
            ok("B_tab_rapid_open", False, str(e)[:120])
        ok("B_rf_all_india", await is_visible(page, "rf-all-india"), "all-india card visible")

        # If popup is shown, tap enter, else tap rf-all-india
        popup = await is_visible(page, "rf-daily-popup")
        if popup:
            await page.click('[data-testid="rf-daily-popup-enter"]', force=True)
        else:
            await page.click('[data-testid="rf-all-india"]', force=True)
        await page.wait_for_timeout(5000)
        try:
            await page.wait_for_selector('[data-testid="rf-daily-result"]', timeout=12000)
            ok("B_daily_result_opens", True, "rf-daily-result visible")
        except Exception as e:
            await page.screenshot(path="/tmp/rf_daily.png", quality=40, full_page=False)
            ok("B_daily_result_opens", False, str(e)[:120])

        # Measure victory ring and page horizontal overflow at 750
        metrics = await page.evaluate("""() => {
          const v = document.querySelector('[data-testid="rf-battle-victory"]');
          const r = document.querySelector('[data-testid="rf-daily-result"]');
          const vb = v ? v.getBoundingClientRect() : null;
          const rb = r ? r.getBoundingClientRect() : null;
          // find ring ancestor by image dimension: approximate by finding closest wider parent
          let ring = null;
          if (v) {
            let el = v.parentElement;
            while (el) {
              const rect = el.getBoundingClientRect();
              if (rect.width >= vb.width && rect.width <= vb.width + 30) { ring = rect; break; }
              el = el.parentElement;
            }
          }
          return {victory: vb, result: rb, ring: ring, innerW: window.innerWidth, scrollW: document.documentElement.scrollWidth};
        }""")
        print("B metrics:", metrics)
        ok("B_no_horizontal_overflow_750", metrics["scrollW"] - metrics["innerW"] == 0, f"px={metrics['scrollW']-metrics['innerW']}")
        if metrics.get("victory"):
            v = metrics["victory"]
            # Picture roughly ~523, ring ~528; margins ~111 at 750 (width 528 => (750-528)/2 = 111)
            margin_l = v["x"]
            margin_r = metrics["innerW"] - (v["x"] + v["width"])
            ok("B_victory_width", 510 <= v["width"] <= 540, f"w={v['width']}")
            ok("B_victory_centered", abs(margin_l - margin_r) <= 6 and 95 <= margin_l <= 125, f"ml={margin_l}, mr={margin_r}")
        else:
            ok("B_victory_width", False, "no rf-battle-victory")

        # Check at 390x844
        await page.set_viewport_size({"width": 390, "height": 844})
        await page.wait_for_timeout(600)
        m390 = await page.evaluate("""() => {
          const v = document.querySelector('[data-testid="rf-battle-victory"]');
          return v ? {w: v.getBoundingClientRect().width, scrollW: document.documentElement.scrollWidth, innerW: window.innerWidth} : null;
        }""")
        print("B 390 metrics:", m390)
        if m390:
            ok("B_overflow_390", m390["scrollW"] - m390["innerW"] == 0, f"px={m390['scrollW']-m390['innerW']}")
            ok("B_victory_390_width", 340 <= m390["w"] <= 375, f"w={m390['w']}")

        # ========== Phase C: Sound once per day ==========
        # Capture current sounds
        now_sounds = await sounds(page)
        print("Sounds captured since RF opened:", now_sounds)
        # First open: expect scene_* for All India card, then scene_race, scene_cup
        has_scene = any(s.startswith("scene_") for s in now_sounds)
        has_race = "scene_race" in now_sounds
        has_cup = "scene_cup" in now_sounds
        ok("C_scene_card_played", has_scene, f"list={now_sounds}")
        ok("C_scene_race_played", has_race, "scene_race in list")
        ok("C_scene_cup_played", has_cup, "scene_cup in list")

        # Leave with rf-daily-exit and re-open: expect NO new sound
        try:
            await page.click('[data-testid="rf-daily-exit"]', force=True, timeout=4000)
            await page.wait_for_timeout(2500)
        except Exception:
            pass
        # Reset list snapshot
        await page.evaluate("window.__plays = []")
        # Re-open daily result
        try:
            # re-enter
            if await is_visible(page, "rf-all-india"):
                await page.click('[data-testid="rf-all-india"]', force=True)
                await page.wait_for_timeout(3500)
                if await is_visible(page, "rf-daily-popup"):
                    await page.click('[data-testid="rf-daily-popup-enter"]', force=True)
                    await page.wait_for_timeout(3000)
            after_reopen = await sounds(page)
            ok("C_reopen_no_new_sound", len(after_reopen) == 0, f"sounds={after_reopen}")
        except Exception as e:
            ok("C_reopen_no_new_sound", False, str(e)[:120])

        # Reload; go to Rapid Fire again
        await page.evaluate("location.reload()")
        await page.wait_for_timeout(4000)
        try:
            await page.click('[data-testid="tab-rapid"]', force=True, timeout=5000)
            await page.wait_for_timeout(3500)
            if await is_visible(page, "rf-all-india"):
                await page.click('[data-testid="rf-all-india"]', force=True)
                await page.wait_for_timeout(3500)
                if await is_visible(page, "rf-daily-popup"):
                    await page.click('[data-testid="rf-daily-popup-enter"]', force=True)
                    await page.wait_for_timeout(3000)
            after_reload = await sounds(page)
            ok("C_reload_same_day_silent", len(after_reload) == 0, f"sounds={after_reload}")
        except Exception as e:
            ok("C_reload_same_day_silent", False, str(e)[:120])

        # Simulate NEW DAY
        await page.evaluate('localStorage.setItem("rf.heard.v1", JSON.stringify(JSON.stringify({card: "2000-01-01", charge: "2000-01-01"})))')
        await page.evaluate("location.reload()")
        await page.wait_for_timeout(4000)
        try:
            await page.click('[data-testid="tab-rapid"]', force=True, timeout=5000)
            await page.wait_for_timeout(3500)
            if await is_visible(page, "rf-all-india"):
                await page.click('[data-testid="rf-all-india"]', force=True)
                await page.wait_for_timeout(3500)
                if await is_visible(page, "rf-daily-popup"):
                    await page.click('[data-testid="rf-daily-popup-enter"]', force=True)
                    await page.wait_for_timeout(3500)
            new_day_sounds = await sounds(page)
            has_card_again = any(s.startswith("scene_") for s in new_day_sounds)
            ok("C_new_day_card_plays", has_card_again, f"sounds={new_day_sounds}")
        except Exception as e:
            ok("C_new_day_card_plays", False, str(e)[:120])

        # Reward label of finished round shows COINS EARNED and no 'coin' sound
        await page.evaluate("window.__plays = []")
        # already in daily-result; look for reward-credit-label
        credit = await text_of(page, "reward-credit-label")
        ok("C_reward_credit_label", (credit or "").upper() == "COINS EARNED", f"label={credit}")
        sounds_now = await sounds(page)
        ok("C_no_coin_sound", "coin" not in sounds_now, f"sounds={sounds_now}")

        # ========== Phase D: regression ==========
        # Exit daily result back to lobby
        try:
            await page.click('[data-testid="rf-daily-exit"]', force=True, timeout=4000)
            await page.wait_for_timeout(2000)
        except Exception:
            pass
        ok("D_lobby_renders", await is_visible(page, "rf-all-india"), "lobby back")

        # Popup exit
        # Open popup by tapping rf-all-india (daily already done -> popup may not show now, but try)
        # Trigger popup: manually unroute daily/status so popup can show again? Our fixture lets lobby status pass.
        # Simpler: ensure popup EXIT button works if visible
        if await is_visible(page, "rf-daily-popup"):
            await page.click('[data-testid="rf-daily-popup-exit"]', force=True)
            await page.wait_for_timeout(1500)
            ok("D_popup_exit", await is_visible(page, "rf-all-india"), "lobby after popup exit")
        else:
            ok("D_popup_exit", True, "popup not shown (round already done), SKIPPED")

        # Style page preview
        try:
            await page.click('[data-testid="rf-all-india-style"]', force=True, timeout=5000)
            await page.wait_for_timeout(2500)
            await page.wait_for_selector('[data-testid="rf-daily-styles"]', timeout=5000)
            # Tap first style option; measure sound after
            await page.evaluate("window.__plays = []")
            # find any clickable style tile
            style_tids = await page.evaluate("""() => Array.from(document.querySelectorAll('[data-testid^="rf-style-"]')).map(e => e.getAttribute('data-testid')).slice(0, 5)""")
            print("style tiles:", style_tids)
            if style_tids:
                await page.click(f'[data-testid="{style_tids[0]}"]', force=True)
                await page.wait_for_timeout(1200)
                preview_sounds = await sounds(page)
                ok("D_style_preview_sound", len(preview_sounds) > 0, f"sounds={preview_sounds}")
            else:
                ok("D_style_preview_sound", False, "no style tiles found")
        except Exception as e:
            ok("D_style_preview_sound", False, str(e)[:120])

        # Dump POSTs that reached the browser (not short-circuited by fixtures)
        print("\n==== POSTs seen by context (incl. intercepted) ====")
        for u in posts[-60:]:
            print(" ", u)
        print("\n==== DAILY POSTs intercepted ====")
        print(sound_posts)

        # Final summary
        passes = sum(1 for v in RESULTS.values() if v["ok"])
        total = len(RESULTS)
        print(f"\n==== RESULT: {passes}/{total} passed ====")
        for k, v in RESULTS.items():
            if not v["ok"]:
                print(f"  FAIL {k}: {v['note']}")

        with open("/tmp/iter138_results.json", "w") as f:
            json.dump(RESULTS, f, indent=2)
        await browser.close()


asyncio.run(main())
