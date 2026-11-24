# Misfire UI checks: test-only Playwright helpers (paste / import into browser automation). Nothing here changes the app.
#
# Rules for the QA learner (7004186276 / 5524) on the live website:
#   - Never start, answer or submit a paper.
#   - "Check karo", "Samajh gaya" and "Wapas list mein" are REAL writes to the learner's Misfire list
#     (POST /api/jl/my/misfire/<id>/try|done|reopen). Call `await fake_misfire_writes(page)` first, so the browser answers
#     them itself and nothing reaches the website. The first try is answered wrong (right answer "B"), later tries right.
#   - The learner has no All India attempt (the series opens on 9 Dec). `await fake_aits(page)` shows seven scored live
#     days + one archive practice in this browser only; each of those days opens the learner's one real finished paper.
import json
import sys

REAL_ATTEMPT = "1ea510f2-1d2a-41f7-9bb4-a8b28c16f98f"  # JEE Main PYQ 22 Jan 2025 S2: 75 skipped, result released
META = '"error":null,"meta":{"api_version":"1","request_id":"fixture"}'


async def fake_misfire_writes(page, posts=None):
    state = {"tries": 0}

    async def handler(route):
        req = route.request
        if req.method != "POST":
            await route.continue_()
            return
        if posts is not None:
            posts.append(req.url.rsplit("/", 1)[-1] + " " + (req.post_data or ""))
        if req.url.endswith("/try"):
            state["tries"] += 1
            right = "true" if state["tries"] >= 2 else "false"
            body = '{"data":{"correct":%s,"item":{"tries":%d,"answer":"B","solution_text":"","solution_count":1,"last_correct":%s}},%s}' % (right, state["tries"], right, META)
        else:
            body = '{"data":{"ok":true},%s}' % META
        await route.fulfill(status=200, content_type="application/json", body=body)

    await page.route("**/api/jl/my/misfire/*/*", handler)


async def fake_aits(page, variant="done"):
    sys.path.insert(0, "/app/tests/fixtures")
    import iter57_series_fixture as fx
    series, streak, history = fx.build(variant)
    for i, item in enumerate(history["items"]):
        if item.get("summary"):
            item["summary"].update({"incorrect": 6 + i, "skipped": 3 + i, "correct": 40})

    async def series_handler(route):
        url = route.request.url
        body = history if "/history" in url else streak if url.split("?")[0].endswith("/streak") else series
        await route.fulfill(status=200, content_type="application/json", body=json.dumps(body))

    async def attempt_handler(route):
        req = route.request
        if req.method != "GET":
            await route.fulfill(status=403, content_type="application/json", body="{}")
            return
        fake = req.url.split("/attempts/")[1].split("/")[0].split("?")[0]
        await route.fulfill(response=await route.fetch(url=req.url.replace(fake, REAL_ATTEMPT)))

    await page.route("**/api/jl/series/all-india-jee**", series_handler)
    await page.route("**/api/jl/attempts/fx-*/**", attempt_handler)
