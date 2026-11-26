#!/usr/bin/env python3
"""A look at Home's All India bar under the Matched card (web preview, phone size). Reads only; signing in is the one
write. Nothing is started. Pictures 2 to 4 answer the series' schedule IN THE BROWSER (as a day of the series; as the day
after its last day), and picture 5 answers the switch as "Matched off"; nothing on any server is changed.

    python3 /app/tests/home_series_bar_look.py        -> /tmp/bar/*.jpg"""
import json
import re
from pathlib import Path

from playwright.sync_api import sync_playwright

ENV = dict(line.split("=", 1) for line in Path("/app/frontend/.env").read_text().splitlines() if "=" in line and not line.startswith("#"))
URL = ENV["EXPO_PUBLIC_BACKEND_URL"].strip().strip('"').rstrip("/")
PHONE, PIN = re.search(r"QA learner (\d{10}) / (\d{4})", Path("/app/memory/test_credentials.md").read_text()).groups()
OUT = Path("/tmp/bar")
OK = json.dumps({"data": {}, "error": None, "meta": {"api_version": "1"}})


def guard(route):
    req = route.request
    if req.method in ("GET", "HEAD", "OPTIONS") or "/api/jl/" not in req.url or "/api/jl/auth/" in req.url:
        return route.continue_()
    print("answered by the browser, not sent:", req.method, req.url.split("/api/", 1)[-1][:60])
    route.fulfill(status=200, content_type="application/json", body=OK)


def live_day(route):
    """The real schedule, moved so that today is its 46th day with the paper ready."""
    res = route.fetch()
    body = res.json()
    data = body["data"] if isinstance(body, dict) and "data" in body and "meta" in body else body
    slot = data["slots"][45]
    slot.update(state="live", ready=True, can_start=True, set_id=slot.get("set_id") or "00000000-0000-4000-8000-000000000000")
    for s in data["slots"][:45]:
        s.update(state="archive", ready=True)
    data.update(today=slot["date"], today_slot=slot)
    route.fulfill(status=200, content_type="application/json", body=json.dumps(body))


def over(route):
    """The real schedule, read on the day after its last day."""
    res = route.fetch()
    body = res.json()
    data = body["data"] if isinstance(body, dict) and "data" in body and "meta" in body else body
    y, m, d = (int(x) for x in data["last_date"].split("-"))
    data.update(today=f"{y}-{m:02d}-{d + 1:02d}", today_slot=None)
    for s in data["slots"]:
        s.update(state="archive", ready=True)
    route.fulfill(status=200, content_type="application/json", body=json.dumps(body))


def off(route):
    route.fulfill(status=200, content_type="application/json", body=json.dumps({"pictures": 5, "matched": False}))


def home(browser, width, name, schedule=None, switches=None):
    page = browser.new_context(viewport={"width": width, "height": 844}, device_scale_factor=2, locale="en-IN").new_page()
    page.set_default_timeout(60000)
    page.route("**/api/**", guard)
    if schedule:
        page.route(re.compile(r"/api/jl/series/all-india-jee(\?.*)?$"), schedule)
    if switches:
        page.route("**/api/app/switches", switches)
    page.goto(URL + "/entry")
    page.locator('[data-testid="entry-phone-input"]:visible').first.wait_for(timeout=90000)
    page.fill('[data-testid="entry-phone-input"]', PHONE)
    page.fill('[data-testid="entry-pin-input"]', PIN)
    page.wait_for_selector('[data-testid="entry-continue-button"]:not([aria-disabled="true"])')
    page.click('[data-testid="entry-continue-button"]')
    page.locator('[data-testid="home-tile-choice"]:visible').first.wait_for()
    page.wait_for_timeout(3000)
    count = lambda testid: page.locator(f'[data-testid="{testid}"]:visible').count()  # noqa: E731
    text = lambda testid: page.locator(f'[data-testid="{testid}"]:visible').first.inner_text()  # noqa: E731
    has = count("home-series-bar")
    if has:
        page.evaluate("""() => { const e = [...document.querySelectorAll('[data-testid="home-series-bar"]')].find(x => x.offsetParent);
            let sc = e.parentElement; while (sc && !(sc.scrollHeight > sc.clientHeight + 4 && /auto|scroll/.test(getComputedStyle(sc).overflowY))) sc = sc.parentElement;
            if (sc) sc.scrollTop += e.getBoundingClientRect().top - 330; }""")
        page.wait_for_timeout(1200)
    print(name, "| matched card:", count("home-matched"), "| big series card:", count("all-india-series-banner"), "| bar:", has,
          *((("| day:", text("home-series-bar-day"), "| line:", text("home-series-bar-line"))) if has else ()))
    page.screenshot(path=str(OUT / f"{name}.jpg"), type="jpeg", quality=70)
    if has and not schedule:  # before the series: the bar leads to the series hub (a read)
        page.locator('[data-testid="home-series-bar"]:visible').first.click()
        page.wait_for_url("**/live*")
        print(name, "| tap ->", page.url.split("/")[-1])
    page.context.close()


OUT.mkdir(exist_ok=True)
with sync_playwright() as p:
    b = p.chromium.launch(executable_path="/usr/bin/chromium", args=["--no-sandbox"])
    home(b, 390, "1_today")
    home(b, 390, "2_live_day", live_day)
    home(b, 320, "3_live_day_narrow", live_day)
    home(b, 390, "4_series_over", over)
    home(b, 390, "5_matched_off", switches=off)
    b.close()
