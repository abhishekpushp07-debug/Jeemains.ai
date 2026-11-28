#!/usr/bin/env python3
"""The pictures of Parts 4.7 and 4.8 of the hand-off (Offline Misfire, the Misfire Mock), from the app's WEB PREVIEW.
Reads only. Signing in is the one write. Every other write to the website, and to the app's Dream College meter, is
answered by the browser and never sent. Nothing is started, tried or marked.
  - Offline Misfire: the phone keeps the finished papers, then the browser is cut off from the network. The mock is
    made, answered and handed in on the phone only. Its right answers are never sent (the page is closed first).
    The kept copies get MCQ key "A" in the browser, so that three answers are right for the picture.
  - The Misfire Mock: the website's answers are played by the browser (the switch, the history of kind "misfire",
    door C, the made paper's page, a real result marked as a Misfire Mock).

    cd /app/handoff/feature_book && python3 take_shots_misfire.py      -> shots/x04 … x10"""
import asyncio
import json
import re
import sys
import time
from pathlib import Path
from urllib.parse import urlparse

sys.path.insert(0, "/app/tests")
from dotenv import dotenv_values  # noqa: E402
from playwright.async_api import async_playwright  # noqa: E402
from shine_helpers import sign_in  # noqa: E402

OUT = Path(__file__).resolve().parent / "shots"
BASE = dotenv_values("/app/frontend/.env")["EXPO_PUBLIC_BACKEND_URL"].rstrip("/")
HOST = urlparse(BASE).hostname
SET_ID = "misfire-set-0001"
RUNNING = "misfire-running-0001"
OK = json.dumps({"data": {}, "error": None, "meta": {"api_version": "1"}})
taken, answered, kept = [], [], {}
state = {"finished": None, "last": 0.0}


def env(data):
    return json.dumps({"data": data, "error": None, "meta": {"api_version": "1"}})


def tid(t):
    return f'[data-testid="{t}"]'


async def seen(page, t, timeout=60000):
    await page.wait_for_selector(f"{tid(t)} >> visible=true", timeout=timeout)


async def shot(page, name, wait=1500):
    await page.wait_for_timeout(wait)
    await page.screenshot(path=str(OUT / f"{name}.jpg"), type="jpeg", quality=72)
    taken.append(name)


async def scroll_to(page, t, top=120):
    await page.evaluate("""([id, top]) => { const e = [...document.querySelectorAll(`[data-testid="${id}"]`)].find(x => x.offsetParent);
        let sc = e && e.parentElement; while (sc && !(sc.scrollHeight > sc.clientHeight + 4 && /auto|scroll/.test(getComputedStyle(sc).overflowY))) sc = sc.parentElement;
        if (sc) sc.scrollTop += e.getBoundingClientRect().top - top; }""", [t, top])


async def guards(ctx):
    async def jl(route):
        r = route.request
        if r.method in ("GET", "HEAD", "OPTIONS") or "/api/jl/auth" in r.url:
            await route.fallback(); return
        answered.append(f"{r.method} {r.url.split('/api/', 1)[-1][:70]}")
        if r.url.split("?")[0].endswith("/api/jl/choice/papers"):
            await route.fulfill(status=201, content_type="application/json", body=env({"set_id": SET_ID, "title": "Misfire Mock #4", "number": 4, "asked": 15, "given": 15, "minutes": 32})); return
        await route.fulfill(status=200, content_type="application/json", body=OK)
    await ctx.route(re.compile(r".*/api/jl/.*"), jl)

    async def dream(route):  # the Dream College meter is the owner's own data: never written from here
        if route.request.method == "GET":
            await route.fallback(); return
        answered.append(f"{route.request.method} rf/dream")
        await route.fulfill(status=200, content_type="application/json", body='{"ok":true}')
    await ctx.route(re.compile(r".*/api/rf/dream.*"), dream)


async def offline_part(b):
    ctx = await b.new_context(viewport={"width": 390, "height": 844}, device_scale_factor=2, locale="en-IN")
    await guards(ctx)

    async def results(route):  # the kept copies: MCQ key "A" (in this browser only)
        resp = await route.fetch()
        try:
            j = await resp.json()
            d = j.get("data") if isinstance(j.get("data"), dict) else j
            for q in d.get("questions") or []:
                if q.get("options"):
                    q["answer"] = "A"; q["accepted_answers"] = ["A"]
            if d.get("questions"):
                kept[route.request.url.split("/attempts/")[1].split("/")[0]] = True
                state["last"] = time.time()
            await route.fulfill(response=resp, body=json.dumps(j))
        except Exception:
            await route.fulfill(response=resp)
    await ctx.route(re.compile(r".*/api/jl/attempts/[^/]+/results.*"), results)
    page = await ctx.new_page()
    await page.goto(BASE + "/", wait_until="domcontentloaded")
    await sign_in(page, width=390)
    t0 = time.time()
    while time.time() - t0 < 300 and (not kept or time.time() - state["last"] < 30):
        await page.wait_for_timeout(2000)
    print("papers kept on the phone:", len(kept), flush=True)

    async def cut(route):  # no line at all: only the preview's own page and its bundle
        u = urlparse(route.request.url)
        if u.hostname != HOST or u.path.startswith("/api/"):
            await route.abort(); return
        await route.fallback()
    await ctx.route("**/*", cut)
    await page.goto(BASE + "/", wait_until="domcontentloaded")
    await seen(page, "offline-door-button", 90000)
    await page.click(tid("offline-door-button"))
    await seen(page, "offline-misfire-open", 20000)
    await scroll_to(page, "offline-misfire", 260)
    await shot(page, "x04_offline_home", 2000)
    await page.click(tid("offline-misfire-open"))
    await seen(page, "misfire-mock-new", 20000)
    await page.click(tid("misfire-mock-new"))
    await seen(page, "mock-new-phone", 60000)
    await page.click(tid("mock-subject-physics"))
    await page.click(tid("mock-count-physics-5"))
    await shot(page, "x05_offline_setup", 1500)
    await page.click(tid("mock-new-bar-go"))
    await seen(page, "mock-ready-screen", 60000)
    for _ in range(30):
        if "Saare sawaal phone par taiyaar" in await page.locator(tid("mock-ready-pictures-label")).inner_text():
            break
        await page.wait_for_timeout(1000)
    await page.click(tid("mock-start"))
    await seen(page, "mock-player-screen", 20000)
    for _ in range(3):  # three answers, the rest left
        if await page.locator(tid("mock-option-A")).count():
            await page.click(tid("mock-option-A"))
        elif await page.locator(tid("mock-option-math-A")).count():
            await page.click(tid("mock-option-math-A"))
        await page.click(tid("mock-next-button"))
        await page.wait_for_timeout(400)
    await page.click(tid("mock-submit-top"))
    await seen(page, "mock-confirm-submit", 8000)
    await page.click(tid("mock-confirm-submit"))
    await seen(page, "mock-result-screen", 20000)
    await shot(page, "x06_offline_result", 2000)
    await ctx.unroute_all(behavior="ignoreErrors")
    await ctx.close()  # closed with no line: its right answers were never sent


async def mock_part(b):
    ctx = await b.new_context(viewport={"width": 390, "height": 844}, device_scale_factor=2, locale="en-IN")
    await guards(ctx)

    async def bank(route):  # the website's switch, played
        resp = await route.fetch()
        try:
            j = await resp.json(); j["misfire"] = True
            await route.fulfill(response=resp, body=json.dumps(j))
        except Exception:
            await route.fulfill(response=resp)
    await ctx.route(re.compile(r".*/api/choice/bank.*"), bank)

    async def tests(route):
        resp = await route.fetch()
        try:
            j = await resp.json()
            done = next((x for x in (j.get("data") or {}).get("items") or [] if x.get("summary")), None)
            if done and not state["finished"]:
                state["finished"] = done["id"]
            await route.fulfill(response=resp, body=json.dumps(j))
        except Exception:
            await route.fulfill(response=resp)
    await ctx.route(re.compile(r".*/api/jl/my/tests\?.*"), tests)

    async def history(route):  # the agreed list: GET /my/misfire/mocks (newest first, those not started too)
        items = [{"set_id": "misfire-set-0003", "title": "Misfire Mock #3", "number": 3, "created_at": 1795860000, "asked": 15, "given": 15, "minutes": 32, "attempt": None},
                 {"set_id": "misfire-set-0002", "title": "Misfire Mock #2", "number": 2, "created_at": 1795849000, "asked": 10, "given": 10, "minutes": 21,
                  "attempt": {"id": RUNNING, "status": "active", "resumable": True, "started_at": 1795850000, "submitted_at": None, "summary": None}}]
        if state["finished"]:
            items.append({"set_id": "misfire-set-0001b", "title": "Misfire Mock #1", "number": 1, "created_at": 1795749000, "asked": 15, "given": 15, "minutes": 32,
                          "attempt": {"id": state["finished"], "status": "submitted", "resumable": False, "started_at": 1795750000, "submitted_at": 1795753000,
                                      "summary": {"score": 20, "maximum": 60, "correct": 6, "incorrect": 5, "skipped": 4}}})
        await route.fulfill(status=200, content_type="application/json", body=env({"items": items, "page": 1, "pages": 1, "total": len(items)}))
    await ctx.route(re.compile(r".*/api/jl/my/misfire/mocks\?.*"), history)

    async def results(route):
        resp = await route.fetch()
        try:
            j = await resp.json()
            if state["finished"] and f"/attempts/{state['finished']}/results" in route.request.url and isinstance(j.get("data"), dict):
                j["data"].update(test_kind="misfire", misfire={"understood": 3, "total": 15})
            await route.fulfill(response=resp, body=json.dumps(j))
        except Exception:
            await route.fulfill(response=resp)
    await ctx.route(re.compile(r".*/api/jl/attempts/[^/]+/results.*"), results)

    async def a_set(route):
        await route.fulfill(status=200, content_type="application/json", body=env({
            "id": SET_ID, "title": "Misfire Mock · 15 Q · 28 Nov", "exam": "JEE Main", "test_kind": "misfire", "count": 15, "maximum": 60,
            "rules": {"correct": 4, "wrong": -1, "skipped": 0, "minutes": 32}, "types": {"mcq": 12, "integer": 3}, "attempt": None, "saved": False}))
    await ctx.route(re.compile(rf".*/api/jl/my/sets/{SET_ID}.*"), a_set)

    page = await ctx.new_page()
    await page.goto(BASE + "/", wait_until="domcontentloaded")
    await sign_in(page, width=390)
    await page.goto(BASE + "/tests", wait_until="domcontentloaded")
    await seen(page, "my-tests-exam-filters", 45000)
    await page.wait_for_timeout(2500)
    await page.goto(BASE + "/misfire?tab=web", wait_until="domcontentloaded")
    await seen(page, "misfire-web-misfire-set-0001b", 60000)
    await shot(page, "x07_mock_tab", 2000)
    await page.click(tid("misfire-web-new"))
    await seen(page, "mock-new-open-physics", 60000)
    await page.click(tid("mock-subject-physics"))
    await page.click(tid("mock-count-physics-10"))
    await page.click(tid("mock-subject-chemistry"))
    await page.click(tid("mock-count-chemistry-5"))
    await shot(page, "x08_mock_setup", 1500)
    await page.click(tid("mock-new-bar-go"))
    await seen(page, "set-detail-screen", 30000)
    await shot(page, "x09_mock_paper", 2500)
    await page.goto(BASE + f"/result/{state['finished']}", wait_until="domcontentloaded")
    await seen(page, "result-misfire-understood", 90000)
    await scroll_to(page, "result-misfire-understood", 330)
    await shot(page, "x10_mock_result", 2000)
    await ctx.unroute_all(behavior="ignoreErrors")
    await ctx.close()


async def main():
    async with async_playwright() as pw:
        b = await pw.chromium.launch(executable_path="/usr/bin/chromium", args=["--no-sandbox"])
        if "mock" not in sys.argv[1:]:  # `python3 take_shots_misfire.py mock`: only the Misfire Mock's pictures
            await offline_part(b)
        await mock_part(b)
        await b.close()
    print("taken:", taken)
    print("answered by the browser instead of being sent:", answered)


asyncio.run(main())
