#!/usr/bin/env python3
"""A look at Student Choice's colour (web preview, phone size). Reads only; signing in is the one write, ticks are kept
in the browser only. Nothing is started (never press Start / Resume).

    python3 /app/tests/choice_colour_look.py        -> /tmp/choicecolour/*.jpg"""
import json
import re
from pathlib import Path

from playwright.sync_api import sync_playwright

ENV = dict(line.split("=", 1) for line in Path("/app/frontend/.env").read_text().splitlines() if "=" in line and not line.startswith("#"))
URL = ENV["EXPO_PUBLIC_BACKEND_URL"].strip().strip('"').rstrip("/")
PHONE, PIN = re.search(r"QA learner (\d{10}) / (\d{4})", Path("/app/memory/test_credentials.md").read_text()).groups()
OUT = Path("/tmp/choicecolour")
OK = json.dumps({"data": {}, "error": None, "meta": {"api_version": "1"}})


def guard(route):
    req = route.request
    if req.method in ("GET", "HEAD", "OPTIONS") or "/api/jl/" not in req.url or "/api/jl/auth/" in req.url:
        return route.continue_()
    print("answered by the browser, not sent:", req.method, req.url.split("/api/", 1)[-1][:60])
    route.fulfill(status=200, content_type="application/json", body=OK)


def visible(page, testid):
    return page.locator(f'[data-testid="{testid}"]:visible').first


def walk(browser, width):
    page = browser.new_context(viewport={"width": width, "height": 844}, device_scale_factor=1, locale="en-IN").new_page()
    page.set_default_timeout(60000)
    page.route("**/api/**", guard)
    page.goto(URL + "/entry")
    visible(page, "entry-phone-input").wait_for(timeout=90000)
    page.fill('[data-testid="entry-phone-input"]', PHONE)
    page.fill('[data-testid="entry-pin-input"]', PIN)
    page.wait_for_selector('[data-testid="entry-continue-button"]:not([aria-disabled="true"])')
    page.click('[data-testid="entry-continue-button"]')
    visible(page, "home-tile-choice").wait_for()
    visible(page, "home-tile-choice").click()
    visible(page, "choice-hero").wait_for()
    visible(page, "choice-facts").wait_for()
    page.wait_for_timeout(2500)
    print(width, "landing | title:", visible(page, "choice-title").inner_text(), "| facts:", visible(page, "choice-facts").inner_text().replace("\n", " · "))
    page.screenshot(path=str(OUT / f"{width}_1_landing.jpg"), type="jpeg", quality=60)
    visible(page, "choice-way-chapters").click()
    visible(page, "choice-subject-physics").wait_for()
    page.wait_for_timeout(1500)
    sel = lambda t: visible(page, t).get_attribute("aria-selected")  # noqa: E731
    print(width, "pick | physics selected:", sel("choice-subject-physics"), "| count:", visible(page, "choice-subject-physics-count").inner_text())
    rows = page.locator('[role="checkbox"][data-testid^="choice-chapter-"]:visible')
    rows.nth(0).click()
    rows.nth(2).click()
    visible(page, "choice-subject-chemistry").click()
    page.wait_for_timeout(800)
    print(width, "pick | chemistry selected:", sel("choice-subject-chemistry"), "| physics count:", visible(page, "choice-subject-physics-count").inner_text())
    page.locator('[role="checkbox"][data-testid^="choice-chapter-"]:visible').nth(0).click()
    page.wait_for_timeout(800)
    page.screenshot(path=str(OUT / f"{width}_2_pick_chemistry.jpg"), type="jpeg", quality=60)
    visible(page, "choice-subject-physics").click()
    page.wait_for_timeout(1200)
    page.screenshot(path=str(OUT / f"{width}_3_pick_physics.jpg"), type="jpeg", quality=60)
    print(width, "bar:", visible(page, "choice-pick-bar-count").inner_text(), "|", visible(page, "choice-pick-bar-note").inner_text())
    page.fill('[data-testid="choice-search-input"]', "therm")
    visible(page, "choice-search-count").wait_for()
    print(width, "search:", visible(page, "choice-search-count").inner_text())
    page.fill('[data-testid="choice-search-input"]', "")
    visible(page, "choice-pick-bar-go").click()
    visible(page, "choice-tests-hero").wait_for()
    page.wait_for_function("() => [...document.querySelectorAll('[data-testid=\"choice-tests-done\"]')].some(e => e.offsetParent && e.textContent !== '–')", timeout=60000)
    page.wait_for_timeout(1500)
    print(width, "tests |", visible(page, "choice-tests-count").inner_text(), "| done", visible(page, "choice-tests-done").inner_text(),
          "running", visible(page, "choice-tests-running").inner_text(), "left", visible(page, "choice-tests-left").inner_text())
    page.screenshot(path=str(OUT / f"{width}_4_tests.jpg"), type="jpeg", quality=60)
    overflow = page.evaluate("() => document.documentElement.scrollWidth > window.innerWidth + 1")
    print(width, "sideways scroll:", overflow)
    page.context.close()


OUT.mkdir(exist_ok=True)
with sync_playwright() as p:
    b = p.chromium.launch(executable_path="/usr/bin/chromium", args=["--no-sandbox"])
    walk(b, 390)
    walk(b, 320)
    b.close()
