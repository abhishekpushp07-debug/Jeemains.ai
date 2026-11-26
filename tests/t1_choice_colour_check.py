#!/usr/bin/env python3
"""T1 check of Student Choice colour (27 Nov 2026). Read-only: every non-GET to /api/jl (except auth) is answered by the
browser, /attempt/* navigation is aborted. Never taps Start / Resume / Solutions.
    python3 /app/tests/t1_choice_colour_check.py [width]   -> /tmp/t1choice/*.jpg"""
import json
import re
import sys
from pathlib import Path

from playwright.sync_api import sync_playwright

ENV = dict(line.split("=", 1) for line in Path("/app/frontend/.env").read_text().splitlines() if "=" in line and not line.startswith("#"))
URL = ENV["EXPO_PUBLIC_BACKEND_URL"].strip().strip('"').rstrip("/")
PHONE, PIN = re.search(r"QA learner (\d{10}) / (\d{4})", Path("/app/memory/test_credentials.md").read_text()).groups()
OUT = Path("/tmp/t1choice")
OK = json.dumps({"data": {}, "error": None, "meta": {"api_version": "1"}})
PHY, MAT, CHE = "4b4ff9a5-85ba-5325-83cd-60f2994acc57", "4eceef5a-afa4-5514-aeb2-cf3f353f1d1f", "a8f9d83e-9f0c-5b08-86db-b786dbe2d64f"
RES = {"pass": 0, "fail": 0}
blocked, errors = [], []


def check(name, cond, extra=""):
    RES["pass" if cond else "fail"] += 1
    print(("PASS " if cond else "FAIL ") + name + (f" | {extra}" if extra else ""))


def guard(route):
    req = route.request
    if req.method in ("GET", "HEAD", "OPTIONS") or "/api/jl/" not in req.url or "/api/jl/auth/" in req.url:
        return route.continue_()
    blocked.append(req.method + " " + req.url.split("/api/", 1)[-1][:80])
    route.fulfill(status=200, content_type="application/json", body=OK)


def v(page, t):
    return page.locator(f'[data-testid="{t}"]:visible').first


def style(page, t, props):
    return page.evaluate("""([t, props]) => { const e = [...document.querySelectorAll(`[data-testid="${t}"]`)].find(x => x.offsetParent); if (!e) return null;
      const s = getComputedStyle(e); const o = {}; props.forEach(p => o[p] = s[p]);
      let op = 1, n = e; while (n) { op *= parseFloat(getComputedStyle(n).opacity || 1); n = n.parentElement; } o.effOpacity = op.toFixed(2);
      const r = e.getBoundingClientRect(); o.box = [Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)]; return o; }""", [t, props])


def overflow(page):
    return page.evaluate("() => document.documentElement.scrollWidth > window.innerWidth + 1 || document.body.scrollWidth > window.innerWidth + 1")


def cut_text(page):
    """Visible text elements in the screen whose content is wider than their box (cut sideways)."""
    return page.evaluate("""() => [...document.querySelectorAll('div[dir="auto"], span')].filter(e => e.offsetParent && e.scrollWidth > e.clientWidth + 2
      && getComputedStyle(e).overflow === 'hidden' && !getComputedStyle(e).webkitLineClamp?.match(/\\d/)).map(e => e.textContent.slice(0, 40)).slice(0, 8)""")


def walk(browser, width):
    print(f"\n===== WIDTH {width} =====")
    ctx = browser.new_context(viewport={"width": width, "height": 844}, device_scale_factor=1, locale="en-IN")
    page = ctx.new_page()
    page.set_default_timeout(60000)
    page.on("pageerror", lambda e: errors.append(f"{width} pageerror: {e}"))
    page.on("console", lambda m: errors.append(f"{width} console.error: {m.text[:160]}") if m.type == "error" else None)
    page.route("**/api/**", guard)
    page.route(re.compile(r".*/attempt/.*"), lambda r: r.abort() if r.request.resource_type == "document" else r.continue_())
    page.goto(URL + "/entry")
    v(page, "entry-phone-input").wait_for(timeout=90000)
    page.fill('[data-testid="entry-phone-input"]', PHONE)
    page.fill('[data-testid="entry-pin-input"]', PIN)
    page.wait_for_selector('[data-testid="entry-continue-button"]:not([aria-disabled="true"])')
    page.click('[data-testid="entry-continue-button"]')
    v(page, "home-tile-choice").wait_for()
    page.wait_for_timeout(2000)
    check(f"{width} home tile + matched card", v(page, "home-tile-choice").is_visible() and page.locator('[data-testid="home-matched"]').count() > 0)
    page.screenshot(path=str(OUT / f"{width}_0_home.jpg"), type="jpeg", quality=40)

    # Landing
    v(page, "home-tile-choice").click()
    v(page, "choice-facts").wait_for()
    page.wait_for_timeout(2500)
    title, facts = v(page, "choice-title").inner_text(), v(page, "choice-facts").inner_text().replace("\n", " · ")
    check(f"{width} landing title", title == "Apne chapters, apni marzi.", title)
    check(f"{width} landing facts", "81 chapters" in facts and "sawaal" in facts and "+4" in facts, facts)
    print("  title colour", style(page, "choice-title", ["color"]), "| intro", style(page, "choice-intro", ["color"]))
    print("  hero box", style(page, "choice-hero", ["backgroundColor"]))
    for t in ["choice-way-chapters", "choice-soon", "choice-time", "choice-time-note"]:
        check(f"{width} landing has {t}", v(page, t).is_visible())
    print("  time-note:", v(page, "choice-time-note").inner_text()[:220])
    check(f"{width} /choice no sideways scroll", not overflow(page))
    print("  cut text /choice:", cut_text(page))
    page.screenshot(path=str(OUT / f"{width}_1_landing.jpg"), type="jpeg", quality=40)

    # Pick
    v(page, "choice-way-chapters").click()
    v(page, "choice-subject-physics").wait_for()
    page.wait_for_timeout(1500)
    for s in ["physics", "chemistry", "mathematics"]:
        e = v(page, f"choice-subject-{s}")
        print(f"  tab {s}: role={e.get_attribute('role')} selected={e.get_attribute('aria-selected')} count={v(page, f'choice-subject-{s}-count').inner_text()} box={style(page, f'choice-subject-{s}', ['backgroundColor'])['box']}")
    check(f"{width} physics tab selected", v(page, "choice-subject-physics").get_attribute("aria-selected") == "true")
    go = style(page, "choice-pick-bar-go", ["backgroundColor"])
    check(f"{width} go faded with none ticked", float(go["effOpacity"]) < 0.6, str(go))
    check(f"{width} go aria-disabled none ticked", v(page, "choice-pick-bar-go").get_attribute("aria-disabled") == "true")
    print("  bar:", v(page, "choice-pick-bar-count").inner_text(), "|", v(page, "choice-pick-bar-note").inner_text())
    # search
    page.fill('[data-testid="choice-search-input"]', "therm")
    v(page, "choice-search-count").wait_for()
    sc = v(page, "choice-search-count").inner_text()
    check(f"{width} search therm", sc == "3 chapters mile · teeno subjects mein dhoonda", sc)
    check(f"{width} tabs hidden while searching", page.locator('[data-testid="choice-subject-physics"]:visible').count() == 0)
    page.fill('[data-testid="choice-search-input"]', "zzzz")
    v(page, "choice-search-none").wait_for()
    check(f"{width} search none + reset", v(page, "choice-search-reset").is_visible())
    v(page, "choice-search-clear").click()
    page.wait_for_timeout(600)
    check(f"{width} clear empties search", v(page, "choice-search-input").input_value() == "" and v(page, "choice-subject-physics").is_visible())
    page.fill('[data-testid="choice-search-input"]', "zzzz")
    v(page, "choice-search-reset").click()
    page.wait_for_timeout(600)
    check(f"{width} reset empties search", v(page, "choice-search-input").input_value() == "")

    # tick physics row
    row = f"choice-chapter-{PHY}"
    before = style(page, row, ["borderTopColor", "backgroundColor"])
    v(page, row).click()
    page.wait_for_timeout(600)
    after = style(page, row, ["borderTopColor", "backgroundColor"])
    check(f"{width} physics tick colours row", before["borderTopColor"] != after["borderTopColor"] and v(page, row).get_attribute("aria-checked") == "true", f"{before} -> {after}")
    check(f"{width} physics count chip = 1", v(page, "choice-subject-physics-count").inner_text() == "1")
    go = style(page, "choice-pick-bar-go", ["backgroundColor"])
    check(f"{width} go red when ticked", float(go["effOpacity"]) > 0.9, str(go))
    # untick returns white, then tick again
    v(page, row).click(); page.wait_for_timeout(500)
    back = style(page, row, ["borderTopColor", "backgroundColor"])
    check(f"{width} untick returns white", back["borderTopColor"] == before["borderTopColor"] and back["backgroundColor"] == before["backgroundColor"], str(back))
    v(page, row).click(); page.wait_for_timeout(400)
    # maths tab
    v(page, "choice-subject-mathematics").click(); page.wait_for_timeout(1000)
    check(f"{width} maths tab selected", v(page, "choice-subject-mathematics").get_attribute("aria-selected") == "true")
    first = page.locator('[role="checkbox"][data-testid^="choice-chapter-"]:visible').first.inner_text()
    print("  maths first row:", first.replace("\n", " | "))
    page.fill('[data-testid="choice-search-input"]', "straight")
    page.wait_for_timeout(800)
    v(page, f"choice-chapter-{MAT}").click(); page.wait_for_timeout(400)
    page.fill('[data-testid="choice-search-input"]', "mole")
    page.wait_for_timeout(800)
    v(page, f"choice-chapter-{CHE}").click(); page.wait_for_timeout(400)
    che = style(page, f"choice-chapter-{CHE}", ["borderTopColor", "backgroundColor"])
    print("  chem ticked row style:", che)
    v(page, "choice-search-clear").click(); page.wait_for_timeout(800)
    counts = [v(page, f"choice-subject-{s}-count").inner_text() for s in ["physics", "chemistry", "mathematics"]]
    check(f"{width} count chips 1/1/1", counts == ["1", "1", "1"], str(counts))
    bar = v(page, "choice-pick-bar-count").inner_text(), v(page, "choice-pick-bar-note").inner_text()
    print("  bar:", bar, "| bar-count box:", style(page, "choice-pick-bar-count", ["lineHeight"]), "| go box:", style(page, "choice-pick-bar-go", [])["box"])
    check(f"{width} /choice/pick no sideways scroll", not overflow(page))
    print("  cut text /choice/pick:", cut_text(page))
    page.screenshot(path=str(OUT / f"{width}_2_pick.jpg"), type="jpeg", quality=40)

    # Tests
    v(page, "choice-pick-bar-go").click()
    v(page, "choice-tests-hero").wait_for()
    pre = v(page, "choice-tests-done").inner_text()
    print("  done cell right away:", pre)
    page.wait_for_function("() => [...document.querySelectorAll('[data-testid=\"choice-tests-done\"]')].some(e => e.offsetParent && e.textContent !== '–')", timeout=60000)
    page.wait_for_timeout(1500)
    cnt = v(page, "choice-tests-count").inner_text()
    d, r, l = (int(v(page, f"choice-tests-{k}").inner_text()) for k in ["done", "running", "left"])
    check(f"{width} tests count + cells add up", cnt.startswith("3 chapter tests") and d + r + l == 3 and f"{d} ho gaye" in cnt, f"{cnt} | {d}/{r}/{l}")
    for cid in [PHY, CHE, MAT]:
        a = f"choice-test-{cid}-action"
        print(f"  row {cid[:8]}: {v(page, f'choice-test-{cid}-title').inner_text()} | {v(page, a).inner_text()} | {style(page, a, ['backgroundColor', 'color'])}")
    check(f"{width} physics row says Start", v(page, f"choice-test-{PHY}-action").inner_text() == "Start")
    check(f"{width} maths row says Result", v(page, f"choice-test-{MAT}-action").inner_text() == "Result")
    check(f"{width} /choice/tests no sideways scroll", not overflow(page))
    print("  cut text /choice/tests:", cut_text(page))
    page.screenshot(path=str(OUT / f"{width}_3_tests.jpg"), type="jpeg", quality=40)

    if width == 390:
        # Result row -> Analysis (read)
        v(page, f"choice-test-{MAT}").click()
        page.wait_for_url("**/result/**", timeout=30000)
        page.wait_for_timeout(4000)
        print("  opened:", page.url)
        check("390 result row opens /result Analysis", "/result/9d3a7c06" in page.url)
        page.screenshot(path=str(OUT / "390_4_result.jpg"), type="jpeg", quality=40)
        page.go_back(); v(page, "choice-tests-hero").wait_for(); page.wait_for_timeout(1000)
        # Chapters badlo keeps ticks
        v(page, "choice-tests-change").click()
        v(page, "choice-subject-physics").wait_for(); page.wait_for_timeout(800)
        check("390 Chapters badlo -> pick with ticks", "/choice/pick" in page.url and v(page, "choice-pick-bar-count").inner_text() == "3 chapters chune", page.url)
        # back buttons
        v(page, "choice-pick-go" if False else "choice-pick-bar-go").click(); v(page, "choice-tests-hero").wait_for()
        v(page, "choice-tests-back").click(); page.wait_for_timeout(1200)
        check("390 choice-tests-back -> pick", "/choice/pick" in page.url, page.url)
        v(page, "choice-pick-back").click(); page.wait_for_timeout(1200)
        check("390 choice-pick-back -> /choice", page.url.rstrip("/").endswith("/choice"), page.url)
        check("390 landing shows choice-way-tests after ticks", v(page, "choice-way-tests").is_visible())
        v(page, "choice-back").click(); page.wait_for_timeout(1500)
        check("390 choice-back -> home", v(page, "home-tile-choice").is_visible(), page.url)
        # regressions
        page.goto(URL + "/tests"); v(page, "my-tests-tab-completed").wait_for(); page.wait_for_timeout(2500)
        for t in ["completed", "progress", "saved"]:
            print(f"  my-tests tab {t}: sel={v(page, f'my-tests-tab-{t}').get_attribute('aria-selected')} text={v(page, f'my-tests-tab-{t}').inner_text()!r}")
        v(page, "my-tests-tab-progress").click(); page.wait_for_timeout(1000)
        check("390 my-tests progress tab switch", v(page, "my-tests-tab-progress").get_attribute("aria-selected") == "true")
        page.screenshot(path=str(OUT / "390_5_mytests.jpg"), type="jpeg", quality=40)
        page.goto(URL + "/result/9d3a7c06-e885-46a2-bb12-678f57469005"); page.wait_for_timeout(8000)
        check("390 direct result page renders", page.locator('[data-testid="result-tab-solutions"]').count() > 0, page.url)
        page.screenshot(path=str(OUT / "390_6_result_direct.jpg"), type="jpeg", quality=40)

    # cleanup: untick all
    page.goto(URL + "/choice/pick"); v(page, "choice-subject-physics").wait_for(); page.wait_for_timeout(1500)
    for q, cid in [("units", PHY), ("straight", MAT), ("mole", CHE)]:
        page.fill('[data-testid="choice-search-input"]', q); page.wait_for_timeout(700)
        if v(page, f"choice-chapter-{cid}").get_attribute("aria-checked") == "true":
            v(page, f"choice-chapter-{cid}").click(); page.wait_for_timeout(300)
    page.fill('[data-testid="choice-search-input"]', ""); page.wait_for_timeout(500)
    check(f"{width} cleanup: nothing ticked", v(page, "choice-pick-bar-count").inner_text() == "Chapter chuno")
    ctx.close()


OUT.mkdir(exist_ok=True)
widths = [int(a) for a in sys.argv[1:]] or [390, 320]
with sync_playwright() as p:
    b = p.chromium.launch(executable_path="/usr/bin/chromium", args=["--no-sandbox"])
    for w in widths:
        try:
            walk(b, w)
        except Exception as e:  # noqa: BLE001
            RES["fail"] += 1
            print(f"FAIL {w} exception: {e}")
    b.close()
print("\nblocked writes:", blocked)
print("errors:", errors[:20])
print("RESULT", RES)
