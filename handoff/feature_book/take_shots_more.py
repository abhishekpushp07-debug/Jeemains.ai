#!/usr/bin/env python3
"""The pictures of Parts 4, 5 and 6 of the hand-off (Misfire, Rapid Fire in a browser, one account), from the app's WEB
PREVIEW. Reads only: signing in is the one write; every other request to the website that is not a read is answered by
the browser itself and never sent. Nothing is started, tried or marked.

    cd /app/handoff/feature_book && QA_PHONE=... QA_PIN=... python3 take_shots_more.py      -> shots/x*.jpg, r*.jpg, a*.jpg"""
import json
import os
import re
from pathlib import Path

from playwright.sync_api import sync_playwright

OUT = Path(__file__).resolve().parent / "shots"
ENV = dict(line.split("=", 1) for line in Path("/app/frontend/.env").read_text().splitlines() if "=" in line and not line.startswith("#"))
URL = ENV["EXPO_PUBLIC_BACKEND_URL"].strip().strip('"').rstrip("/")
PHONE, PIN = os.environ["QA_PHONE"], os.environ["QA_PIN"]
OK = json.dumps({"data": {}, "error": None, "meta": {"api_version": "1"}})
taken, writes = [], []


def guard(route):
    req = route.request
    if req.method in ("GET", "HEAD", "OPTIONS") or "/api/jl/" not in req.url or "/api/jl/auth/" in req.url:
        return route.continue_()
    writes.append(f"{req.method} {req.url.split('/api/', 1)[-1][:70]}")
    route.fulfill(status=200, content_type="application/json", body=OK)


def page_of(browser, width=390, height=844):
    page = browser.new_context(viewport={"width": width, "height": height}, device_scale_factor=2, locale="en-IN").new_page()
    page.set_default_timeout(60000)
    page.route("**/api/**", guard)
    return page


def seen(page, testid):
    loc = page.locator(f'[data-testid="{testid}"]:visible').first
    loc.wait_for()
    return loc


def shot(page, name, wait=1200):
    page.wait_for_timeout(wait)
    page.screenshot(path=str(OUT / f"{name}.jpg"), type="jpeg", quality=72)
    taken.append(name)


def sign_in(page, start):
    page.goto(start)
    seen(page, "entry-phone-input")
    page.fill('[data-testid="entry-phone-input"]', PHONE)
    page.fill('[data-testid="entry-pin-input"]', PIN)
    page.wait_for_selector('[data-testid="entry-continue-button"]:not([aria-disabled="true"])')
    page.click('[data-testid="entry-continue-button"]')


def scroll_to(page, testid, top=120):
    page.evaluate("""([id, top]) => { const e = [...document.querySelectorAll(`[data-testid="${id}"]`)].find(x => x.offsetParent);
        let sc = e.parentElement; while (sc && !(sc.scrollHeight > sc.clientHeight + 4 && /auto|scroll/.test(getComputedStyle(sc).overflowY))) sc = sc.parentElement;
        if (sc) sc.scrollTop += e.getBoundingClientRect().top - top; }""", [testid, top])


with sync_playwright() as p:
    b = p.chromium.launch(executable_path="/usr/bin/chromium", args=["--no-sandbox"])
    # One account: the sign-in screen (the same phone + PIN as on jeelive.ai).
    page = page_of(b)
    page.goto(URL + "/entry")
    seen(page, "entry-phone-input")
    shot(page, "a01_signin", 2500)
    # Misfire: Home's card, the website's own list, a family tab.
    sign_in(page, URL + "/entry")
    seen(page, "home-misfire")
    scroll_to(page, "home-misfire", 260)
    shot(page, "x01_home_misfire", 2500)
    seen(page, "home-misfire").click()
    seen(page, "misfire-screen")
    page.wait_for_selector('[data-testid^="misfire-row-"]:visible, [data-testid="misfire-empty"]:visible')
    shot(page, "x02_misfire_all", 2000)
    seen(page, "misfire-tab-jee-chapter").click()
    page.wait_for_selector('[data-testid^="misfire-paper-"]:visible, [data-testid="misfire-papers-empty"]:visible')
    shot(page, "x03_misfire_papers", 2000)
    page.context.close()
    # Rapid Fire in a browser: the arena at a laptop's width (a phone-wide column on the red stage).
    page = page_of(b, 1280, 800)
    sign_in(page, URL + "/api/arena")
    page.wait_for_timeout(9000)
    shot(page, "r01_arena_laptop", 1500)
    page.context.close()
    b.close()
print("taken:", taken)
print("answered by the browser instead of being sent:", writes)
