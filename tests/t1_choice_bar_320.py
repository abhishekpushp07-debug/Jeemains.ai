#!/usr/bin/env python3
"""T1: /choice/pick bottom bar at 320 with many ticks (wrap, not cut), and where the 401 console line comes from. Unticks at the end."""
import json
import re
from pathlib import Path

from playwright.sync_api import sync_playwright

ENV = dict(line.split("=", 1) for line in Path("/app/frontend/.env").read_text().splitlines() if "=" in line and not line.startswith("#"))
URL = ENV["EXPO_PUBLIC_BACKEND_URL"].strip().strip('"').rstrip("/")
PHONE, PIN = re.search(r"QA learner (\d{10}) / (\d{4})", Path("/app/memory/test_credentials.md").read_text()).groups()
OK = json.dumps({"data": {}, "error": None, "meta": {"api_version": "1"}})


def guard(route):
    req = route.request
    if req.method in ("GET", "HEAD", "OPTIONS") or "/api/jl/" not in req.url or "/api/jl/auth/" in req.url:
        return route.continue_()
    print("blocked", req.method, req.url)
    route.fulfill(status=200, content_type="application/json", body=OK)


with sync_playwright() as p:
    b = p.chromium.launch(executable_path="/usr/bin/chromium", args=["--no-sandbox"])
    page = b.new_context(viewport={"width": 320, "height": 844}).new_page()
    page.set_default_timeout(60000)
    page.on("response", lambda r: print("HTTP", r.status, r.request.method, r.url.split("/api/", 1)[-1][:70]) if r.status >= 400 else None)
    page.route("**/api/**", guard)
    page.goto(URL + "/entry")
    page.wait_for_selector('[data-testid="entry-phone-input"]', timeout=90000)
    page.fill('[data-testid="entry-phone-input"]', PHONE)
    page.fill('[data-testid="entry-pin-input"]', PIN)
    page.wait_for_selector('[data-testid="entry-continue-button"]:not([aria-disabled="true"])')
    page.click('[data-testid="entry-continue-button"]')
    page.wait_for_selector('[data-testid="home-tile-choice"]')
    page.goto(URL + "/choice/pick")
    page.wait_for_selector('[data-testid="choice-subject-physics"]')
    page.wait_for_timeout(1500)
    rows = page.locator('[role="checkbox"][data-testid^="choice-chapter-"]:visible')
    n = min(rows.count(), 10)
    for i in range(n):
        rows.nth(i).click(); page.wait_for_timeout(150)
    page.click('[data-testid="choice-subject-chemistry"]'); page.wait_for_timeout(800)
    rows = page.locator('[role="checkbox"][data-testid^="choice-chapter-"]:visible')
    for i in range(2):
        rows.nth(i).click(); page.wait_for_timeout(150)
    page.wait_for_timeout(600)
    info = page.evaluate("""() => ['choice-pick-bar-count','choice-pick-bar-note','choice-pick-bar-go'].map(t => { const e=[...document.querySelectorAll(`[data-testid="${t}"]`)].find(x=>x.offsetParent);
      const r=e.getBoundingClientRect(); return [t, e.textContent, Math.round(r.width), Math.round(r.height), e.scrollWidth, e.clientWidth, e.scrollHeight, e.clientHeight]; })""")
    for i in info:
        print("BAR", i)
    print("sideways:", page.evaluate("() => document.documentElement.scrollWidth > window.innerWidth + 1"))
    page.screenshot(path="/tmp/t1choice/320_bar_many.jpg", type="jpeg", quality=40)
    # untick all
    for s in ["physics", "chemistry"]:
        page.click(f'[data-testid="choice-subject-{s}"]'); page.wait_for_timeout(700)
        on = page.locator('[role="checkbox"][aria-checked="true"][data-testid^="choice-chapter-"]:visible')
        while on.count():
            on.first.click(); page.wait_for_timeout(200)
    page.wait_for_timeout(500)
    print("after cleanup bar:", page.locator('[data-testid="choice-pick-bar-count"]:visible').inner_text())
    b.close()
