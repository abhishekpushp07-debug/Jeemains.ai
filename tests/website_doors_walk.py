# Which doors of the website does the app really use? (27 Nov 2026; test-only, read-only.)
# Walks the app's screens once as the QA learner and writes down every call the app makes to the website through its own
# server (/api/jl/<path>), with the answer's status. Nothing is started, answered, saved or submitted: only screens are
# opened. The All India series and its leaderboard are NOT stood in for here, so the website's real answers are seen.
#   python3 /app/tests/website_doors_walk.py            -> /tmp/website_doors_seen.json and a table on the screen
# The book's Part 7 (handoff/feature_book/parts/70_together.md) is written from this list and from the app's code.
import asyncio
import json
import re
import sys
from collections import defaultdict

from dotenv import dotenv_values
from playwright.async_api import async_playwright

sys.path.insert(0, "/app/tests")
import smoke_all  # noqa: E402
from misfire_fixture import REAL_ATTEMPT  # noqa: E402
from shine_helpers import sign_in  # noqa: E402

BASE = dotenv_values("/app/frontend/.env")["EXPO_PUBLIC_BACKEND_URL"].rstrip("/")
OUT = "/tmp/website_doors_seen.json"
MORE = [
    ("Student Choice", "/choice", "choice-screen"),
    ("Student Choice: chapters", "/choice/pick", "choice-pick-screen"),
    ("Student Choice: chapter tests", "/choice/tests", "choice-tests-screen"),
    ("Matched", "/matched", "matched-screen"),
    ("Misfire: a paper's page", "/misfire/" + REAL_ATTEMPT, "misfire-screen"),
    ("Exam hub: BITSAT", "/exam/bitsat", "exam-hub-title"),
    ("Exam hub: COMEDK", "/exam/comedk", "exam-hub-title"),
    ("My results of the series", "/live", "streak-card"),
]
ID = re.compile(r"^(?=.*\d)[0-9a-fA-F-]{8,}$|^[0-9a-f]{24}$|^\d+$")


def door(url):
    path = url.split("/api/jl/", 1)[1]
    path, _, query = path.partition("?")
    parts = []
    for i, seg in enumerate(path.split("/")):
        colon = seg.replace("%3A", ":").split(":")
        parts.append("<id>" if all(ID.match(c) for c in colon) and seg else seg)
    keys = sorted({kv.split("=")[0] for kv in query.split("&") if kv})
    return "/".join(parts), keys


async def main():
    seen = defaultdict(lambda: {"status": defaultdict(int), "query": set(), "screens": set()})
    now = {"screen": "sign-in"}

    def note(res):
        if "/api/jl/" not in res.url:
            return
        path, keys = door(res.url)
        row = seen[res.request.method + " " + path]
        row["status"][str(res.status)] += 1
        row["query"].update(keys)
        row["screens"].add(now["screen"])

    async with async_playwright() as p:
        browser = await p.chromium.launch(executable_path="/usr/bin/chromium", args=["--no-sandbox"])
        page = await (await browser.new_context(viewport={"width": 390, "height": 844})).new_page()
        page.on("response", note)
        await page.goto(BASE + "/entry", wait_until="domcontentloaded", timeout=90000)
        await sign_in(page, aits=None, board=False)
        await page.wait_for_timeout(2500)
        for name, path, tid in smoke_all.SCREENS + MORE:
            now["screen"] = name
            state = "ok"
            try:
                await page.goto(BASE + path, wait_until="domcontentloaded", timeout=60000)
                await page.wait_for_selector(f'[data-testid="{tid}"]', timeout=30000)
            except Exception as e:  # noqa: BLE001 - a screen that did not come up is said, the walk goes on
                state = "did not come up (%s)" % type(e).__name__
            await page.wait_for_timeout(2200)
            print("%-34s %s" % (name, state))
        await browser.close()
    rows = {k: {"status": dict(v["status"]), "query": sorted(v["query"]), "screens": sorted(v["screens"])} for k, v in sorted(seen.items(), key=lambda kv: kv[0].split(" ", 1)[::-1])}
    json.dump(rows, open(OUT, "w"), indent=1)
    print()
    for k, v in rows.items():
        print("%-58s %-22s %s" % (k, json.dumps(v["status"]), ("?" + "&".join(v["query"])) if v["query"] else ""))
    print("\n%d doors seen; written to %s" % (len(rows), OUT))


asyncio.run(main())
