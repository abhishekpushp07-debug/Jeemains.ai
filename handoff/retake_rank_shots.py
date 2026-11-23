"""Retakes the Rank screenshots of the website hand-off pack that show Cut off, Meri details or the tile grid.

The app's bottom bar is hidden in every shot (the pack carries no Rapid Fire). Every state is reached by real taps,
so the run also proves the flows: it stops with an error if a screen does not appear or says something unexpected.

Run (Python with Playwright, e.g. /usr/local/bin/python3; the sign-in is the approved QA learner, see memory/test_credentials.md):

    QA_PHONE=... QA_PIN=... /usr/local/bin/python3 /app/handoff/retake_rank_shots.py

It only reads Rank cut-offs (public data) and keeps the forms in that browser; it never starts or submits a paper.
Then rebuild the pack: cd /app/backend && python ../handoff/build_pack.py
"""
import os
import sys
from pathlib import Path

from playwright.sync_api import sync_playwright

OUT = Path("/app/handoff/shots/rank")
ENV = dict(line.split("=", 1) for line in Path("/app/frontend/.env").read_text().splitlines() if "=" in line and not line.startswith("#"))
URL = ENV["EXPO_PUBLIC_BACKEND_URL"].strip().strip('"').rstrip("/")
PHONE, PIN = os.environ["QA_PHONE"], os.environ["QA_PIN"]
taken = []


def main():
    with sync_playwright() as p:
        browser = p.chromium.launch(executable_path="/usr/bin/chromium", args=["--no-sandbox"])
        page = browser.new_context(viewport={"width": 390, "height": 844}, device_scale_factor=1, locale="en-IN").new_page()
        page.set_default_timeout(45000)
        errors = []
        page.on("pageerror", lambda e: errors.append(str(e)))

        def el(testid):
            return page.locator(f'[data-testid="{testid}"]:visible').first

        def tap(testid):
            el(testid).click()

        def text(testid):
            return el(testid).inner_text().replace("\n", " ")

        def expect(testid, part):
            el(testid).wait_for()
            page.wait_for_function("([id, part]) => [...document.querySelectorAll(`[data-testid=\"${id}\"]`)].some(e => e.offsetParent && e.innerText.includes(part))",
                                   arg=[testid, part])
            return text(testid)

        def value(testid, want):
            """Waits until the input holds `want` (a tool reads its saved form a moment after it opens)."""
            el(testid).wait_for()
            page.wait_for_function("([id, want]) => [...document.querySelectorAll(`[data-testid=\"${id}\"]`)].some(e => e.offsetParent && e.value === want)", arg=[testid, want])

        def on(testid):
            return el(testid).get_attribute("aria-selected") == "true"

        def hide_bar():
            page.evaluate("""() => { const t = document.querySelector('[data-testid="tab-rank"]'); if (!t) return;
                let p = t.parentElement; while (p && !p.querySelector('[data-testid="tab-mission"]')) p = p.parentElement;
                if (p) p.style.display = 'none'; }""")

        def scroll(testid=None, at=12):
            """Brings the element's top to `at` pixels from the top of the screen (no element: the very top of the page)."""
            page.evaluate("""([id, at]) => {
                const page = document.querySelector('[data-testid="rank-title"]');
                let sc = page; while (sc && !(sc.scrollHeight > sc.clientHeight + 4 && /auto|scroll/.test(getComputedStyle(sc).overflowY))) sc = sc.parentElement;
                if (!id) { sc.scrollTop = 0; return; }
                const e = [...document.querySelectorAll(`[data-testid="${id}"]`)].find(x => x.offsetParent);
                sc.scrollTop += e.getBoundingClientRect().top - at; }""", [testid, at])

        def shot(name):
            hide_bar()
            page.wait_for_timeout(900)
            page.screenshot(path=str(OUT / f"{name}.jpg"), type="jpeg", quality=84)
            taken.append(name)
            print("shot", name, flush=True)

        def fill(testid, value):
            el(testid).fill(value)

        def open_rank():
            page.goto(URL + "/rank")
            el("rank-title").wait_for(timeout=120000)
            el("rank-tool-cutoff").wait_for()
            hide_bar()

        # ---------------------------------------------------------------- sign in (once)
        page.goto(URL)
        el("entry-phone-input").wait_for(timeout=120000)
        fill("entry-phone-input", PHONE)
        fill("entry-pin-input", PIN)
        tap("entry-continue-button")
        el("tab-rank").wait_for(timeout=90000)
        open_rank()

        # ---------------------------------------------------------------- the page: Meri details bar + six tiles
        assert "Apni details ek baar daalo" in text("rank-profile"), text("rank-profile")
        assert page.locator("text=PERCENTILE SE RANK").count() == 0, "the old tile is still there"
        assert "CUT OFF" in text("rank-tool-cutoff")
        scroll()
        shot("01_rank_tab_meri_details_bar_and_six_tools")

        # ---------------------------------------------------------------- Cut off · JEE Main · college
        tap("rank-tool-cutoff")
        el("cut-form").wait_for()
        assert on("cut-cat-GEN"), "JEE Main must start on General"
        scroll("rank-profile")
        shot("NEW_cutoff_01_tile_and_form_college_or_branch")
        tap("cut-pick")
        fill("cut-pick-sheet-search", "trichy")
        el("cut-pick-sheet-25").wait_for()
        shot("NEW_cutoff_02_college_search_sheet")
        tap("cut-pick-sheet-25")
        print(expect("cut-count", "9 branches · har round ki closing rank"))
        fill("cut-score-input", "200")
        scroll("cut-head")
        shot("NEW_cutoff_03_college_result_head_and_optional_score_box")
        scroll("cut-row-0")
        shot("NEW_cutoff_04_college_every_branch_every_round")
        tap("cut-apply")
        print(expect("cut-count", "6 / 9 branches eligible"), "|", expect("cut-you-line", "200 marks (Normal paper)"))
        assert "Safe 5" in text("cut-count-safe") and "Likely 1" in text("cut-count-likely") and "Borderline 0" in text("cut-count-borderline")
        scroll("cut-head")
        shot("NEW_cutoff_05_eligible_only_safe_likely_borderline")
        scroll("cut-row-0")
        shot("NEW_cutoff_06_eligible_cards_green_inside_amber_edge")
        scroll("cut-near")
        print(text("cut-near-0-gap"))
        shot("NEW_cutoff_07_near_misses_and_notes")
        tap("cut-edit")
        value("cut-score-input", "200")  # Score badlo keeps the typed number
        fill("cut-score-input", "500")
        tap("cut-apply")
        print(expect("cut-score-error", "300"))
        scroll("cut-head")
        shot("NEW_cutoff_17_wrong_score_message")
        fill("cut-score-input", "120")
        tap("cut-apply")
        print(expect("cut-count", "0 / 9 branches eligible"), "|", expect("cut-empty", "koi option eligible nahi"))
        scroll("cut-head")
        shot("NEW_cutoff_18_nothing_eligible_shows_how_far")
        tap("cut-clear")
        print(expect("cut-count", "9 branches · har round"))
        fill("cut-score-input", "")

        # ---------------------------------------------------------------- Cut off · JEE Main · branch
        scroll("rank-profile")
        tap("cut-by-branch")
        el("cut-hint").wait_for()
        tap("cut-pick")
        fill("cut-pick-sheet-search", "cse")
        el("cut-pick-sheet-Computer Science").wait_for()
        shot("NEW_cutoff_08_branch_search_sheet")
        tap("cut-pick-sheet-Computer Science")
        print(expect("cut-count", "Top 100 of 123 college-branch"))
        scroll("cut-head")
        shot("NEW_cutoff_09_branch_top_100_colleges_all_rounds")
        assert page.locator('[data-testid^="cut-row-"][data-testid$="-title"]:visible').count() == 25, "25 cards at a time"
        scroll("cut-more", at=760)
        print(text("cut-more"))
        shot("NEW_cutoff_10_branch_list_25_at_a_time_show_more")
        tap("cut-more")
        page.wait_for_function("() => [...document.querySelectorAll('[data-testid^=\"cut-row-\"][data-testid$=\"-title\"]')].filter(e => e.offsetParent).length === 50")
        # the college side still remembers NIT Trichy
        scroll("rank-profile")
        tap("cut-by-college")
        print(expect("cut-count", "9 branches"))
        tap("cut-by-branch")
        expect("cut-count", "Top 100 of 123")
        tap("cut-cat-OBC-NCL")
        tap("cut-state")
        tap("cut-state-picker-delhi")
        expect("cut-row-0", "OBC-NCL")
        scroll("cut-form")
        shot("NEW_cutoff_11_category_chips_and_home_state")
        tap("cut-kind-percentile")
        fill("cut-score-input", "97.4")
        tap("cut-apply")
        print(expect("cut-you-line", "97.4 percentile"), "|", text("cut-count"), "|", text("cut-you"))
        assert "OBC-NCL rank" in text("cut-you")
        scroll("cut-head")
        shot("NEW_cutoff_12_branch_eligible_with_percentile_obc_delhi")
        tap("cut-edit")
        tap("cut-kind-rank")
        fill("cut-score-input", "7500")
        tap("cut-apply")
        print(expect("cut-you-line", "Rank 7,500"))
        tap("cut-clear")
        expect("cut-count", "Top 100")
        tap("cut-kind-marks")
        scroll("cut-form")
        tap("cut-cat-GEN")
        tap("cut-state")
        tap("cut-state-picker-all")
        tap("cut-by-college")
        expect("cut-count", "9 branches")

        # ---------------------------------------------------------------- Cut off · BITSAT (years, not rounds)
        scroll("rank-profile")
        tap("cut-exam-bitsat")
        assert "Campus se" in text("cut-by-college") and "Program se" in text("cut-by-branch")
        assert page.locator('[data-testid="cut-cat-GEN"]:visible').count() == 0, "BITSAT has no category chips"
        assert "round-wise cutoff publish nahi karta" in text("cut-form")
        tap("cut-pick")
        tap("cut-pick-sheet-Pilani")
        print(expect("cut-count", "18 programs · 5 saal ke cutoff score"))
        assert page.locator('[data-testid^="cut-kind-"]:visible').count() == 0, "BITSAT takes a score only"
        row = text("cut-row-0")
        assert "2022" in row and "2026" in row and "R1" not in row, row
        scroll("cut-exam-jee", at=16)
        shot("NEW_cutoff_13_bitsat_campus_or_program_no_rounds_note")
        fill("cut-score-input", "300")
        tap("cut-apply")
        print(expect("cut-count", "17 / 18 programs eligible"), "|", text("cut-you-line"))
        scroll("cut-head")
        shot("NEW_cutoff_14_bitsat_five_year_cutoff_scores_eligible")
        tap("cut-by-branch")
        tap("cut-pick")
        tap("cut-pick-sheet-cs")
        print(expect("cut-count", "campus eligible"), "|", text("cut-near-0-gap"))
        tap("cut-by-college")
        expect("cut-count", "17 / 18 programs eligible")

        # ---------------------------------------------------------------- Cut off · COMEDK
        scroll("rank-profile")
        tap("cut-exam-comedk")
        assert page.locator('[data-testid="cut-cat-GEN"]:visible').count() == 0, "COMEDK has no category chips"
        tap("cut-pick")
        tap("cut-pick-sheet-E095")
        print(expect("cut-count", "courses · har round ki closing rank"))
        assert page.locator('[data-testid="cut-kind-percentile"]:visible').count() == 0 and el("cut-kind-rank").is_visible()
        scroll("rank-profile")
        tap("cut-by-branch")
        tap("cut-pick")
        fill("cut-pick-sheet-search", "computer")
        tap("cut-pick-sheet-Computer Science")
        expect("cut-count", "Top 100 of 162 college-course")
        tap("cut-kind-rank")
        fill("cut-score-input", "30000")
        tap("cut-apply")
        print(expect("cut-count", "142 / 162 college-course eligible · top 100 dikh rahe"), "|", text("cut-you-line"))
        scroll("cut-head")
        shot("NEW_cutoff_15_comedk_branch_eligible_with_rank")
        scroll("cut-row-0")
        print(text("cut-row-0-final"))
        shot("NEW_cutoff_16_comedk_cards_four_rounds_fee_seats")
        scroll("rank-profile")
        tap("cut-exam-jee")
        print("each exam kept its own choice:", expect("cut-count", "9 branches"))

        # ---------------------------------------------------------------- older screens that show the tile grid or the JEE form
        scroll()
        tap("rank-tool-target")
        el("tm-college").wait_for()
        scroll()
        tap("tm-college")
        fill("tm-college-sheet-search", "Trichy")
        el("tm-college-sheet-25").wait_for()
        shot("07_target_marks_college_search_sheet")
        tap("tm-college-sheet-25")
        expect("tm-list", "Computer Science and Engineering")
        scroll()
        tap("rank-tool-college")
        el("rank-input").wait_for()
        scroll()
        tap("rank-state")
        el("rank-state-picker-bihar").wait_for()
        shot("10_college_predictor_home_state_picker")
        tap("rank-state-picker-bihar")
        fill("rank-marks-input", "180")
        assert el("rank-rank-input").is_visible() and "Koi ek kaafi hai" in text("rank-score-note")
        scroll("rank-exam-jee", at=16)
        shot("11_college_predictor_jee_form")
        tap("rank-show")
        print("college predictor, marks:", expect("rank-input-collapsed", "180 marks"))
        scroll("rank-tool-rank")
        tap("rank-exam-bitsat")
        fill("bitsat-score-input", "280")
        tap("bitsat-show")
        print("bitsat:", expect("bitsat-card", "280"))
        scroll("rank-tool-rank")
        shot("19_college_predictor_bitsat_rank_card")
        tap("rank-exam-comedk")
        fill("comedk-marks-input", "110")
        tap("comedk-show")
        print("comedk:", expect("comedk-card", "110"))
        scroll("rank-tool-rank")
        shot("21_college_predictor_comedk_rank_card")
        tap("rank-exam-jee")
        scroll()
        tap("rank-tool-compare")
        for name in ("Warangal", "Rourkela"):
            tap("cmp-add-college")
            fill("cmp-college-sheet-search", name)
            page.locator(f'[data-testid^="cmp-college-sheet-"]:visible >> text=NIT {name}').first.click()
            el("cmp-college-sheet-search").wait_for(state="hidden")
        expect("cmp-college-table", "NIT Rourkela")
        scroll("rank-tool-rank")
        shot("23_college_compare_pick_colleges")

        # ---------------------------------------------------------------- Meri details
        scroll()
        tap("rank-tool-rank")
        scroll()
        tap("rank-profile")
        el("rank-profile-form").wait_for()
        assert on("rpf-cat-GEN"), "Meri details starts on General"
        fill("rpf-jee-marks", "500")
        tap("rpf-save")
        print(expect("rpf-error", "300"))
        fill("rpf-jee-marks", "200")
        fill("rpf-jee-rank", "7500")
        assert "Pehle Rank, phir Percentile, phir Marks" in text("rpf-jee-note")
        scroll()
        shot("NEW_meri_details_01_form_jee_main")
        tap("rpf-exam-comedk")
        fill("rpf-comedk-rank", "30000")
        tap("rpf-exam-bitsat")
        fill("rpf-bitsat-score", "280")
        shot("NEW_meri_details_02_form_bitsat")
        tap("rpf-save")
        el("rank-profile-saved").wait_for()
        line = text("rank-profile-summary")
        print("saved:", line)
        assert "200 marks, rank 7,500 · General" in line and "COMEDK: rank 30,000" in line and "BITSAT: 280" in line, line
        value("rp-marks-input", "200")
        scroll()
        shot("NEW_meri_details_03_saved_bar_fills_every_tool")

        # Every tool starts from the profile ...
        tap("rank-tool-college")
        value("rank-marks-input", "200")
        value("rank-rank-input", "7500")
        assert "Pehle Rank" in text("rank-score-note")
        tap("rank-show")
        print("college predictor, rank wins:", expect("rank-input-collapsed", "Rank 7,500"))
        tap("rank-exam-bitsat")
        value("bitsat-score-input", "280")
        tap("rank-exam-comedk")
        value("comedk-rank-input", "30000")
        tap("rank-exam-jee")
        scroll()
        tap("rank-tool-cutoff")
        expect("cut-count", "9 branches · har round")  # the profile score waits in the box; it is not applied by itself
        value("cut-score-input", "7500")
        assert on("cut-kind-rank")
        # ... and an edit inside one tool stays in that tool.
        scroll("rank-profile")
        tap("cut-cat-SC")
        expect("cut-row-0", "· SC")
        scroll()
        assert text("rank-profile-summary") == line, "a tool edit must not change Meri details"
        tap("rank-tool-target")
        assert on("tm-cat-GEN") and not on("tm-cat-SC"), "a tool edit must not change another tool"
        tap("rank-tool-rank")
        assert on("rp-cat-GEN")

        # After a reload the profile and each tool's own form are still there.
        open_rank()
        expect("rank-profile-summary", "200 marks")
        assert text("rank-profile-summary") == line
        tap("rank-tool-cutoff")
        expect("cut-count", "9 branches")
        value("cut-score-input", "7500")
        assert on("cut-cat-SC") and on("cut-kind-rank")
        tap("cut-cat-GEN")
        # "Meri details hatao" forgets the profile, the tools keep their values.
        scroll()
        tap("rank-profile")
        tap("rpf-clear")
        expect("rank-profile", "Apni details ek baar daalo")
        tap("rank-tool-rank")
        value("rp-marks-input", "200")

        browser.close()
        print("\npage errors:", errors or "none")
        print(len(taken), "screens retaken")


if __name__ == "__main__":
    main()
    sys.exit(0)
