#!/usr/bin/env python3
"""Takes the pictures for the Student Choice and Matched book from the app's WEB PREVIEW.

    cd /app/handoff/feature_book && QA_PHONE=... QA_PIN=... python3 take_shots.py [a] [b] [c]
    ONLY=m08,m10 ... python3 take_shots.py b      only these pictures of a walk (a picture that needs the screen of the
                                                  one before it must be asked for together with it)

Three walks, each in its own browser (no letter = all three):
  a  signed out: the sign-in screen's Matched bar, the Matched page, a shift, a question's card, the sign-up sheet
  b  signed in:  Home (Matched card, the All India bar under it, Student Choice tile), Student Choice as it works today, a paper's page (Start is
     NOT pressed), and the JEE Main question under ours in a finished paper's solutions
  c  signed in, with the BROWSER answering for doors the website does not have yet: Student Choice with question picking
     and the random mock open (made-up questions marked "(Sample)"). Nothing on any server is changed for it.

What it needs on the preview database: the three sample Matched shifts published and Home's card on
(python3 /app/backend/tests/matched_sample.py show). It never starts, resumes or submits a paper; every request to the
website that is not a read is answered by the browser itself, except signing in.
The sign-in is the QA learner (memory/test_credentials.md), which is the owner's own account on the preview."""
import json
import os
import sys
from pathlib import Path

from playwright.sync_api import sync_playwright

OUT = Path(__file__).resolve().parent / "shots"
ENV = dict(line.split("=", 1) for line in Path("/app/frontend/.env").read_text().splitlines() if "=" in line and not line.startswith("#"))
URL = ENV["EXPO_PUBLIC_BACKEND_URL"].strip().strip('"').rstrip("/")
PHONE, PIN = os.environ["QA_PHONE"], os.environ["QA_PIN"]
SHIFT = "2027-01-22-s1"
RESULT = "2bbc7035-abdd-4f95-9c87-e72a700e1cac"  # the QA learner's finished "01 Sets and Relations": the sample shift's stand-in paper
OK = json.dumps({"data": {}, "error": None, "meta": {"api_version": "1"}})
STEMS = {
    "Physics": ["A ball is thrown vertically up with speed $u$. The time it takes to come back to the thrower's hand is",
                "A particle moves in a circle of radius $r$ with constant speed $v$. Its acceleration is",
                "Two resistors $R_1$ and $R_2$ are joined in parallel across a cell. The ratio of the heat produced in them is",
                "The escape speed from the surface of a planet of mass $M$ and radius $R$ is"],
    "Chemistry": ["The hybridisation of the central atom in SF4 is", "The pH of a 0.001 M solution of HCl is",
                  "For a first order reaction the half-life is 20 min. The rate constant is", "The number of sigma bonds in benzene is"],
    "Mathematics": ["If the roots of $x^2 - 5x + k = 0$ differ by 1, then $k$ is", "The number of ways of arranging the letters of the word MATHS is",
                    "The sum of the first $n$ odd natural numbers is", "The slope of the tangent to $y = x^3$ at $x = 2$ is"],
}
ONLY = set(filter(None, os.environ.get("ONLY", "").split(",")))
taken, skipped, writes = [], [], []


def walk(browser, later=False):
    page = browser.new_context(viewport={"width": 390, "height": 844}, device_scale_factor=2, locale="en-IN").new_page()
    page.set_default_timeout(45000)
    state = {}

    def guard(route):
        """Reads go through, and so does signing in. Any other request to the website (a start, an answer, "solution
        opened", a paper to be made) is answered here and never sent. The app's own server keeps its usual traffic."""
        req = route.request
        if req.method in ("GET", "HEAD", "OPTIONS") or "/api/jl/" not in req.url or "/api/jl/auth/" in req.url:
            return route.continue_()
        writes.append(f"{req.method} {req.url.split('/api/', 1)[-1][:70]}")
        route.fulfill(status=200, content_type="application/json", body=OK)
    page.route("**/api/**", guard)

    if later:
        def bank(route):
            res = route.fetch()
            data = res.json()
            data.update(pick=True, random=True)
            state["subject"] = {c["id"]: s["name"] for s in data.get("subjects", []) for c in s["chapters"]}
            route.fulfill(status=200, content_type="application/json", body=json.dumps(data))

        def chapter(route):
            cid = route.request.url.rstrip("/").rsplit("/", 1)[-1].split("?")[0]
            stems = STEMS[state.get("subject", {}).get(cid, "Physics")]
            items = [{"id": f"sample-{cid[:8]}-q{k:02d}", "n": k, "type": "integer" if k % 5 == 0 else "mcq", "text": f"(Sample) {stems[k % len(stems)]}", "stem": []} for k in range(1, 13)]
            route.fulfill(status=200, content_type="application/json", body=json.dumps({"id": cid, "title": "", "subject": "", "total": len(items), "items": items}))
        page.route("**/api/choice/bank", bank)
        page.route("**/api/choice/chapters/*", chapter)
    return page


def tools(page):
    def el(testid):
        return page.locator(f'[data-testid="{testid}"]:visible').first

    def top(testid, at=96):
        """Brings the element's top to `at` pixels from the top of the screen."""
        el(testid).wait_for()
        page.evaluate("""([id, at]) => { const e = [...document.querySelectorAll(`[data-testid="${id}"]`)].find(x => x.offsetParent); if (!e) return;
            let sc = e.parentElement; while (sc && !(sc.scrollHeight > sc.clientHeight + 4 && /auto|scroll/.test(getComputedStyle(sc).overflowY))) sc = sc.parentElement;
            if (sc) sc.scrollTop += e.getBoundingClientRect().top - at; }""", [testid, at])
        page.wait_for_timeout(500)

    def shot(name, settle=900):
        page.wait_for_timeout(settle)
        page.screenshot(path=str(OUT / f"{name}.jpg"), type="jpeg", quality=84, full_page=False)
        taken.append(name)

    def step(name, fn):
        """One picture; a step that fails is written down and the walk goes on."""
        try:
            fn()
        except Exception as e:  # noqa: BLE001
            skipped.append(f"{name}: {type(e).__name__} {str(e)[:160]}")

    def sign_in():
        page.goto(URL + "/entry")
        el("entry-phone-input").wait_for(timeout=90000)
        page.fill('[data-testid="entry-phone-input"]', PHONE)
        page.fill('[data-testid="entry-pin-input"]', PIN)
        page.wait_for_selector('[data-testid="entry-continue-button"]:not([aria-disabled="true"])')
        page.click('[data-testid="entry-continue-button"]')
        el("home-tile-choice").wait_for(timeout=60000)

    def tick(word, title):
        """Finds a chapter with the search box and ticks it."""
        page.fill('[data-testid="choice-search-input"]', word)
        row = page.locator('[role="checkbox"][data-testid^="choice-chapter-"]:visible', has_text=title).first
        row.wait_for()
        row.click()
        page.wait_for_timeout(250)
    return el, top, shot, step, sign_in, tick


def signed_out(browser):
    page = walk(browser)
    el, top, shot, step, _, _ = tools(page)

    def bar():
        page.goto(URL + "/entry")
        el("entry-matched").wait_for(timeout=90000)
        shot("m01_signin_bar")

    def matched_page():
        page.goto(URL + "/matched")
        el(f"matched-shift-{SHIFT}").wait_for(timeout=90000)
        shot("m02_matched_page")

    def shift_top():
        el(f"matched-shift-{SHIFT}").click()
        el("matched-attempt").wait_for()
        shot("m03_shift_top")

    def pair():
        top("matched-pair-0")
        shot("m04_question_card")

    def solution():
        el("matched-pair-0-tab-solution").click()
        el("matched-pair-0-jee-solution").wait_for()
        top("matched-pair-0-tab-solution", 80)
        shot("m05_solution_tab")

    def sheet():
        top("matched-shift-count", 150)
        el("matched-attempt").click()
        el("matched-signup-yes").wait_for()
        shot("m06_signup_sheet")

    def after_sheet():
        el("matched-signup-yes").click()
        el("entry-matched-note").wait_for()
        shot("m07_signup_screen")
    for name, fn in (("m01", bar), ("m02", matched_page), ("m03", shift_top), ("m04", pair), ("m05", solution), ("m06", sheet), ("m07", after_sheet)):
        if not ONLY or name in ONLY:
            step(name, fn)
    page.context.close()


def signed_in(browser):
    page = walk(browser)
    el, top, shot, step, sign_in, tick = tools(page)
    sign_in()

    def home_card():
        el("home-matched").wait_for()
        el("home-matched-total").wait_for()
        shot("m08_home_card", 1500)

    def home_bar():
        # The All India series' bar right under the Matched card, with the four exam boxes below it.
        top("home-series-bar", 330)
        shot("m10_home_series_bar")

    def home_tile():
        top("home-tile-choice", 420)
        shot("s01_home_tile")

    def landing():
        page.goto(URL + "/choice")
        el("choice-way-chapters").wait_for(timeout=90000)
        shot("s02_landing")
        top("choice-soon", 110)
        shot("s03_soon_and_time")

    def pick():
        page.goto(URL + "/choice/pick")
        el("choice-subject-physics").wait_for(timeout=90000)
        page.locator('[role="checkbox"][data-testid^="choice-chapter-"]:visible').first.wait_for()
        shot("s04_chapters")

    def search():
        page.fill('[data-testid="choice-search-input"]', "therm")
        el("choice-search-count").wait_for()
        shot("s05_search")
        page.fill('[data-testid="choice-search-input"]', "kinametics")
        page.locator('[data-testid="choice-search-count"]:visible', has_text="Milte-julte").wait_for()
        shot("s06_search_near_spelling")

    def ticked():
        tick("units", "Units, Dimensions and Errors")
        tick("solutions", "Solutions")
        tick("straight", "Straight Lines")
        page.fill('[data-testid="choice-search-input"]', "")
        el("choice-subject-physics").wait_for()
        shot("s07_chapters_ticked")

    def tests():
        el("choice-pick-bar-go").click()
        el("choice-tests-count").wait_for()
        page.locator('[data-testid$="-action"]:visible').first.wait_for()
        shot("s08_chapter_tests", 1500)

    def paper_page():
        page.locator('[data-testid^="choice-test-"]:visible', has_text="Units, Dimensions and Errors").first.click()
        el("set-detail-screen").wait_for()
        shot("s09_paper_page", 1500)  # Start is never pressed

    def under_ours():
        page.goto(URL + "/result/" + RESULT)
        el("result-tab-solutions").wait_for(timeout=90000)
        el("result-tab-solutions").click()
        el("matched-with").wait_for()
        top("matched-with", 150)
        shot("m09_under_ours_in_solutions", 1500)
    for name, fn in (("m08", home_card), ("m10", home_bar), ("s01", home_tile), ("s02", landing), ("s04", pick), ("s05", search), ("s07", ticked), ("s08", tests), ("s09", paper_page), ("m09", under_ours)):
        if not ONLY or name in ONLY:
            step(name, fn)
    page.context.close()


def later(browser):
    page = walk(browser, later=True)
    el, top, shot, step, sign_in, tick = tools(page)
    sign_in()

    def landing():
        page.goto(URL + "/choice")
        el("choice-way-pick").wait_for(timeout=90000)
        shot("s10_later_landing")

    def random_sheet():
        el("choice-way-random").click()
        el("choice-random-makeup").wait_for()
        shot("s11_later_random_mock", 1200)

    def questions():
        page.goto(URL + "/choice/pick")
        el("choice-search-input").wait_for(timeout=90000)
        tick("kinematics", "Kinematics")
        tick("mole", "Mole Concept")
        tick("quadratic", "Quadratic Equations")
        page.fill('[data-testid="choice-search-input"]', "")
        el("choice-pick-bar-go").click()
        rows = page.locator('[role="checkbox"][data-testid^="choice-q-"]:visible')
        rows.first.wait_for()
        for i in (0, 1, 2):
            rows.nth(i).click()
        for subject, n in (("chemistry", 2), ("maths", 2), ("mathematics", 2)):
            pill = page.locator(f'[data-testid="choice-q-subject-{subject}"]:visible')
            if not pill.count():
                continue
            pill.first.click()
            page.wait_for_timeout(700)
            rows = page.locator('[role="checkbox"][data-testid^="choice-q-"]:visible')
            rows.first.wait_for()
            for i in range(n):
                rows.nth(i).click()
        page.wait_for_timeout(400)
        shot("s12_later_questions")

    def review():
        el("choice-questions-bar-go").click()
        el("choice-review-makeup").wait_for()
        shot("s13_later_review", 1200)  # "Haan, paper banao" is never pressed
    for name, fn in (("s10", landing), ("s11", random_sheet), ("s12", questions), ("s13", review)):
        if not ONLY or name in ONLY:
            step(name, fn)
    page.context.close()


def main():
    which = set(sys.argv[1:]) or {"a", "b", "c"}
    OUT.mkdir(exist_ok=True)
    with sync_playwright() as p:
        browser = p.chromium.launch(executable_path="/usr/bin/chromium", args=["--no-sandbox"])
        for letter, fn in (("a", signed_out), ("b", signed_in), ("c", later)):
            if letter in which:
                try:
                    fn(browser)
                except Exception as e:  # noqa: BLE001 - a walk that cannot even begin is written down
                    skipped.append(f"walk {letter}: {type(e).__name__} {str(e)[:200]}")
        browser.close()
    print("taken:", taken)
    print("skipped:", skipped)
    print("answered by the browser instead of being sent:", sorted(set(writes)))


if __name__ == "__main__":
    main()
