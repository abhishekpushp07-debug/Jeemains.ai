#!/usr/bin/env python3
"""Student Choice's sentence about a whole chapter test's time, with the BROWSER answering the chapter list as if the
website had already set the owner's rule (the ratio, three hours at most). Reads only; signing in is the one write.

    python3 /app/tests/choice_cap_sentence_look.py"""
import json
import math
import re
from pathlib import Path

from playwright.sync_api import sync_playwright

ENV = dict(line.split("=", 1) for line in Path("/app/frontend/.env").read_text().splitlines() if "=" in line and not line.startswith("#"))
URL = ENV["EXPO_PUBLIC_BACKEND_URL"].strip().strip('"').rstrip("/")
PHONE, PIN = re.search(r"QA learner (\d{10}) / (\d{4})", Path("/app/memory/test_credentials.md").read_text()).groups()
OK = json.dumps({"data": {}, "error": None, "meta": {"api_version": "1"}})
seen = {}


def guard(route):
    req = route.request
    if req.method in ("GET", "HEAD", "OPTIONS") or "/api/jl/" not in req.url or "/api/jl/auth/" in req.url:
        return route.continue_()
    route.fulfill(status=200, content_type="application/json", body=OK)


def bank(top):
    def answer(route):
        data = route.fetch().json()
        times = []
        for s in data.get("subjects", []):
            for c in s["chapters"]:
                if c.get("test"):
                    c["test"]["minutes"] = min(top, math.ceil(round(c["count"] * data["minutes"][s["name"]], 4)))
                    times.append(c["test"]["minutes"])
        seen[top] = (len(times), max(times), min(times))
        route.fulfill(status=200, content_type="application/json", body=json.dumps(data))
    return answer


def note(browser, top=None):
    page = browser.new_context(viewport={"width": 390, "height": 844}, locale="en-IN").new_page()
    page.set_default_timeout(60000)
    page.route("**/api/**", guard)
    if top:
        page.route("**/api/choice/bank", bank(top))
    page.goto(URL + "/entry")
    page.locator('[data-testid="entry-phone-input"]:visible').first.wait_for(timeout=90000)
    page.fill('[data-testid="entry-phone-input"]', PHONE)
    page.fill('[data-testid="entry-pin-input"]', PIN)
    page.wait_for_selector('[data-testid="entry-continue-button"]:not([aria-disabled="true"])')
    page.click('[data-testid="entry-continue-button"]')
    page.locator('[data-testid="home-tile-choice"]:visible').first.wait_for()
    page.goto(URL + "/choice")
    text = page.locator('[data-testid="choice-time-note"]:visible').first
    text.wait_for(timeout=90000)
    page.wait_for_timeout(2500)  # the phone's kept copy is shown first, then the fresh answer
    out = text.inner_text()
    page.context.close()
    return out[out.index("3 hr.") + 5:].strip() if "3 hr." in out else out


with sync_playwright() as p:
    b = p.chromium.launch(executable_path="/usr/bin/chromium", args=["--no-sandbox"])
    print("the website as it is today      :", note(b))
    print("the rule (ratio, 180 at most)   :", note(b, 180), "| tests, longest, shortest:", seen.get(180))
    print("the ratio alone (no longest time):", note(b, 10 ** 6), "| tests, longest, shortest:", seen.get(10 ** 6))
    b.close()
