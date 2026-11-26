# Iteration 139 — AITS leaderboard VISUAL restyle verification.
# Signs in ONCE, uses fake_aits + fake_board fixtures, then checks colours and animations.
import asyncio, json, os, sys, time
sys.path.insert(0, "/app/tests")
from aits_board_fixture import fake_board
from misfire_fixture import fake_aits

BASE = os.environ.get("PUBLIC_URL") or "https://jeelive-feature-book--3o05z2vs.preview.emergentagent.com"
PHONE = "7004186276"
PIN = "5524"

RESULTS = []
def rec(name, ok, details=""):
    RESULTS.append({"name": name, "ok": bool(ok), "details": details})
    print(("PASS " if ok else "FAIL ") + name + (": " + details if details else ""))


async def _gradients_at(page, testid):
    """Return list of backgroundImage values on descendants with gradients inside the testid root."""
    return await page.evaluate(
        """(tid) => {
            const root = document.querySelector(`[data-testid="${tid}"]`);
            if (!root) return null;
            const out = [];
            root.querySelectorAll('*').forEach(el => {
                const bi = getComputedStyle(el).backgroundImage;
                if (bi && bi.includes('gradient')) out.push(bi);
            });
            return out;
        }""", testid)


async def _anims_in(page, testid):
    return await page.evaluate(
        """(tid) => {
            const root = document.querySelector(`[data-testid="${tid}"]`);
            if (!root) return null;
            const names = new Set();
            root.querySelectorAll('*').forEach(el => {
                const n = getComputedStyle(el).animationName;
                if (n && n !== 'none') n.split(',').forEach(x => names.add(x.trim()));
            });
            return [...names];
        }""", testid)


async def run(page):
    # Console hooks
    errs = []
    page.on("pageerror", lambda e: errs.append("pageerror: " + str(e)))

    await page.set_viewport_size({"width": 390, "height": 844})
    await page.goto(BASE + "/entry", wait_until="domcontentloaded")
    await page.wait_for_selector('[data-testid="entry-phone-input"]', timeout=20000)

    await fake_aits(page, "done")
    await fake_board(page)

    await page.fill('[data-testid="entry-phone-input"]', PHONE)
    await page.fill('[data-testid="entry-pin-input"]', PIN)
    await page.click('[data-testid="entry-continue-button"]', force=True)
    await page.wait_for_selector('[data-testid="home-tile-live"]', timeout=30000)
    rec("sign_in", True)

    # ---- A. Home banner ----
    try:
        await page.wait_for_selector('[data-testid="all-india-series-banner"]', timeout=15000)
        home_grads = await _gradients_at(page, "all-india-series-banner")
        joined = " ".join(home_grads or [])
        onyx_face = "rgb(11, 11, 13)" in joined and "rgb(23, 9, 13)" in joined and "rgb(58, 9, 18)" in joined
        rec("A_home_onyx_face", onyx_face, f"n_grads={len(home_grads or [])}")
        edge_ok = all(c in joined for c in ("rgb(255, 45, 74)", "rgb(255, 200, 87)", "rgb(255, 122, 147)"))
        rec("A_home_edge_colours", edge_ok)
        anims = await _anims_in(page, "all-india-series-banner")
        rec("A_home_animations", bool(anims) and len(anims) >= 2, f"anims={anims}")
        await page.wait_for_selector('[data-testid="series-open-hub-button"]', timeout=5000)
        rec("A_home_cta_present", True)
    except Exception as e:
        rec("A_home_exception", False, str(e)[:200])

    # Navigate to /live
    try:
        await page.click('[data-testid="home-tile-live"]', force=True)
        await page.wait_for_url("**/live**", timeout=15000)
        await page.wait_for_selector('[data-testid="streak-card"]', timeout=20000)
    except Exception as e:
        rec("B_nav_live", False, str(e)[:200])
        return

    # ---- B. Streak card baby pink ----
    try:
        streak_grads = await _gradients_at(page, "streak-card")
        j = " ".join(streak_grads or [])
        pink_face = "rgb(255, 220, 232)" in j and "rgb(255, 181, 206)" in j
        rec("B_streak_face_pink", pink_face)
        edge_ok = all(c in j for c in ("rgb(255, 45, 122)", "rgb(180, 92, 255)", "rgb(255, 138, 107)"))
        rec("B_streak_edge", edge_ok)

        # Leaderboard bar
        await page.wait_for_selector('[data-testid="series-open-leaderboard"]', timeout=15000)
        bar_grads = await _gradients_at(page, "series-open-leaderboard")
        bj = " ".join(bar_grads or [])
        bar_onyx = "rgb(11, 11, 13)" in bj and "rgb(58, 9, 18)" in bj
        rec("B_bar_onyx", bar_onyx)
        bar_edge = all(c in bj for c in ("rgb(255, 45, 74)", "rgb(255, 200, 87)", "rgb(255, 122, 147)"))
        rec("B_bar_edge", bar_edge)
    except Exception as e:
        rec("B_exception", False, str(e)[:200])

    # Open leaderboard
    try:
        await page.click('[data-testid="series-open-leaderboard"]', force=True)
        await page.wait_for_selector('[data-testid="aits-board-screen"]', timeout=20000)
        await page.wait_for_selector('[data-testid="aits-board-you"]', timeout=20000)
    except Exception as e:
        rec("C_open_board", False, str(e)[:200])
        return

    # ---- C. Rank card baby pink ----
    try:
        you_grads = await _gradients_at(page, "aits-board-you")
        yj = " ".join(you_grads or [])
        pink = "rgb(255, 220, 232)" in yj and "rgb(255, 181, 206)" in yj
        rec("C_rank_pink_face", pink, f"n={len(you_grads or [])}")
        edge = all(c in yj for c in ("rgb(255, 45, 122)", "rgb(180, 92, 255)", "rgb(255, 138, 107)"))
        rec("C_rank_edge", edge)
        anims = await _anims_in(page, "aits-board-you")
        rec("C_rank_anims", bool(anims) and len(anims) >= 2, f"anims={anims}")
        for sub in ("aits-board-you-rank", "aits-board-you-label", "aits-board-you-name", "aits-board-count"):
            vis = await page.is_visible(f'[data-testid="{sub}"]')
            rec(f"C_rank_has_{sub}", vis)
    except Exception as e:
        rec("C_rank_exc", False, str(e)[:200])

    # ---- D. Podium matches Home ----
    try:
        p_grads = await _gradients_at(page, "aits-board-podium")
        pj = " ".join(p_grads or [])
        pface = "rgb(11, 11, 13)" in pj and "rgb(23, 9, 13)" in pj and "rgb(58, 9, 18)" in pj
        rec("D_podium_onyx_face", pface)
        pedge = all(c in pj for c in ("rgb(255, 45, 74)", "rgb(255, 200, 87)", "rgb(255, 122, 147)"))
        rec("D_podium_edge", pedge)
        panims = await _anims_in(page, "aits-board-podium")
        rec("D_podium_anims", bool(panims) and len(panims) >= 2, f"anims={panims}")
        for n in (1, 2, 3):
            rec(f"D_podium_step_{n}", await page.is_visible(f'[data-testid="aits-board-podium-{n}"]'))
    except Exception as e:
        rec("D_podium_exc", False, str(e)[:200])

    # ---- E. Tabs colouring ----
    try:
        # The three tabs should exist. Aas-paas (around) must be ORANGE, not pink.
        around_grads = await _gradients_at(page, "aits-board-tab-around")
        aj = " ".join(around_grads or [])
        # resting face (not currently active):
        rest_orange = "rgb(255, 216, 176)" in aj and "rgb(255, 192, 136)" in aj
        rec("E_around_resting_orange", rest_orange, f"first100={aj[:200]}")
        # It must NOT be baby pink any more:
        not_pink = not ("rgb(255, 220, 232)" in aj and "rgb(255, 181, 206)" in aj)
        rec("E_around_not_pink", not_pink)

        # Activate 'around' and check open face
        await page.click('[data-testid="aits-board-tab-around"]', force=True)
        await page.wait_for_timeout(600)
        around_grads2 = await _gradients_at(page, "aits-board-tab-around")
        aj2 = " ".join(around_grads2 or [])
        open_orange = "rgb(255, 169, 77)" in aj2 and "rgb(255, 122, 26)" in aj2
        rec("E_around_open_orange", open_orange, f"first100={aj2[:200]}")

        # Rows under Aas-paas, check 'aits-board-next' text visible
        await page.wait_for_selector('[data-testid="aits-board-around"]', timeout=10000)
        nxt_vis = await page.is_visible('[data-testid="aits-board-next"]')
        rec("F_around_next_text", nxt_vis)
    except Exception as e:
        rec("E_tabs_exc", False, str(e)[:200])

    # ---- G. Search visible text inside input ----
    try:
        await page.click('[data-testid="aits-board-tab-find"]', force=True)
        await page.wait_for_selector('[data-testid="aits-board-search"]', timeout=10000)
        box = await page.locator('[data-testid="aits-board-search"]').bounding_box()
        await page.fill('[data-testid="aits-board-search"]', "ar")
        await page.wait_for_timeout(600)
        # elementFromPoint at the input returns the input itself
        hit = await page.evaluate(
            """(b) => {
                const el = document.elementFromPoint(b.x + 20, b.y + b.height/2);
                if (!el) return null;
                return {tag: el.tagName.toLowerCase(), tid: el.getAttribute('data-testid'), val: el.value || ''};
            }""", {"x": box["x"], "y": box["y"], "width": box["width"], "height": box["height"]})
        rec("G_search_hit_is_input", (hit or {}).get("tid") == "aits-board-search", f"hit={hit}")
        # Check <input> has value or fallback: queryselector value
        val = await page.evaluate("""()=>{const i=document.querySelector('[data-testid="aits-board-search"]');return i? i.value: null;}""")
        rec("G_search_value_present", (val or "").startswith("ar"), f"val={val}")
        found = await page.is_visible('[data-testid="aits-board-found"]')
        rec("G_search_found_rows", found)
        # numeric
        await page.fill('[data-testid="aits-board-search"]', "25")
        await page.wait_for_timeout(500)
        rec("G_search_numeric", await page.is_visible('[data-testid="aits-board-found"]'))
        # no match
        await page.fill('[data-testid="aits-board-search"]', "zzzzqq")
        await page.wait_for_timeout(500)
        rec("G_search_none", await page.is_visible('[data-testid="aits-board-none"]'))
        # clear
        await page.fill('[data-testid="aits-board-search"]', "")
        await page.wait_for_timeout(400)
        rec("G_search_hint", await page.is_visible('[data-testid="aits-board-find-hint"]'))
    except Exception as e:
        rec("G_search_exc", False, str(e)[:200])

    # ---- Back to Toppers for ROWS yellow family check ----
    try:
        await page.click('[data-testid="aits-board-tab-top"]', force=True)
        await page.wait_for_selector('[data-testid="aits-board-top"]', timeout=10000)
        top_grads = await _gradients_at(page, "aits-board-top")
        tj = " ".join(top_grads or [])
        rec("F_top_has_gradients", len(top_grads or []) >= 3, f"n={len(top_grads or [])}")
        # yellow family check (some soft yellow face expected)
        has_warm = any(x in tj for x in ("255, 212", "255, 221", "255, 230", "255, 240", "255, 200"))
        rec("F_top_warm_family_present", has_warm)
    except Exception as e:
        rec("F_top_exc", False, str(e)[:200])

    # ---- H. Top 50 toggle ----
    try:
        more = page.locator('[data-testid="aits-board-more"]')
        if await more.count() > 0:
            await more.first.click(force=True)
            await page.wait_for_timeout(1200)
            # scroll to bottom and back
            await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
            await page.wait_for_timeout(500)
            await page.evaluate("window.scrollTo(0, 0)")
            await page.wait_for_timeout(400)
            rec("H_top50_toggle_ok", True)
        else:
            rec("H_top50_missing_pill", False)
    except Exception as e:
        rec("H_top50_exc", False, str(e)[:200])

    # ---- I. Day switch ----
    try:
        chip9 = page.locator('[data-testid="aits-board-chip-9"]')
        if await chip9.count():
            await chip9.first.click(force=True)
            await page.wait_for_timeout(1500)
            label9 = await page.locator('[data-testid="aits-board-you-label"]').first.inner_text()
            chip3 = page.locator('[data-testid="aits-board-chip-3"]')
            if await chip3.count():
                await chip3.first.click(force=True)
                await page.wait_for_timeout(1500)
                label3 = await page.locator('[data-testid="aits-board-you-label"]').first.inner_text()
                rec("I_day_label_changes", label9 != label3, f"d9='{label9}' d3='{label3}'")
            else:
                rec("I_chip3_missing", False)
        else:
            rec("I_chip9_missing", False)
    except Exception as e:
        rec("I_day_exc", False, str(e)[:200])

    # ---- K. 320 viewport no horizontal scroll ----
    try:
        await page.set_viewport_size({"width": 320, "height": 700})
        await page.wait_for_timeout(600)
        ov = await page.evaluate("()=>document.documentElement.scrollWidth <= window.innerWidth + 1")
        rec("K_no_hscroll_320_toppers", ov)
        await page.click('[data-testid="aits-board-tab-around"]', force=True)
        await page.wait_for_timeout(800)
        ov2 = await page.evaluate("()=>document.documentElement.scrollWidth <= window.innerWidth + 1")
        rec("K_no_hscroll_320_around", ov2)
    except Exception as e:
        rec("K_320_exc", False, str(e)[:200])

    # ---- J. notice cards: preparing/fail ----
    try:
        await page.set_viewport_size({"width": 390, "height": 844})
        await page.unroute("**/api/jl/attempts/*/leaderboard*")
        await fake_board(page, state="preparing")
        await page.reload()
        await page.wait_for_selector('[data-testid="aits-board-wait"]', timeout=15000)
        rec("J_preparing_wait_card", True)
        rec("J_preparing_wait_note", await page.is_visible('[data-testid="aits-board-wait-note"]'))
        rec("J_preparing_retry_btn", await page.is_visible('[data-testid="aits-board-retry"]'))

        await page.unroute("**/api/jl/attempts/*/leaderboard*")
        await fake_board(page, fail=True)
        await page.click('[data-testid="aits-board-retry"]', force=True)
        await page.wait_for_timeout(1500)
        wait_still = await page.is_visible('[data-testid="aits-board-wait"]')
        rec("J_fail_shows_wait_card", wait_still)

        await page.unroute("**/api/jl/attempts/*/leaderboard*")
        await fake_board(page)
        await page.click('[data-testid="aits-board-retry"]', force=True)
        await page.wait_for_selector('[data-testid="aits-board-you"]', timeout=15000)
        rec("J_recover_ready", True)
    except Exception as e:
        rec("J_notice_exc", False, str(e)[:200])

    # ---- L. Regression: back button to /live ----
    try:
        await page.click('[data-testid="aits-board-back"]', force=True)
        await page.wait_for_url("**/live**", timeout=10000)
        rec("L_back_to_live", True)
    except Exception as e:
        rec("L_back_exc", False, str(e)[:200])

    rec("no_page_errors", len(errs) == 0, f"errs={errs[:3]}")

    # Save results
    with open("/tmp/iter139_results.json", "w") as f:
        json.dump(RESULTS, f, indent=2)
    passed = sum(1 for r in RESULTS if r["ok"])
    print(f"\n==== {passed}/{len(RESULTS)} PASS ====")

# Entry
await run(page)
