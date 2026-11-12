# Iteration57: test-only Playwright fixtures for All India series live states (no real data).
import datetime, json, time

COMPLETED = [1, 2, 4, 5, 7, 8, 9]
MISSED = [3, 6]
SCORES = {1: 120, 2: 140, 4: 95, 5: 160, 7: 180, 8: 150, 9: 205}


def build(variant="live", now=None):
    now = int(now or time.time())
    first = datetime.date(2026, 12, 1)
    slots, days = [], []
    for i in range(62):
        d = i + 1
        date = (first + datetime.timedelta(days=i)).isoformat()
        if d < 10:
            st = "archive"
        elif d == 10:
            st = "live"
        else:
            st = "upcoming"
        slots.append({"day": d, "date": date, "state": st, "ready": d <= 10, "set_id": f"fixture-set-{d}" if d <= 10 else None,
                      "title": f"All India JEE Mains · Test {d:02d}", "can_start": d <= 10, "opens_at": now - 3600,
                      "last_start_at": now + 3 * 3600, "closes_at": now + 6 * 3600})
        ds = "completed" if d in COMPLETED else "missed" if d in MISSED else "today" if d == 10 else "upcoming"
        days.append({"day": d, "date": date, "state": ds, "attempt_id": f"fx-live-{d}" if d in COMPLETED else None})
    series = {"id": "all-india-jee", "title": "All India JEE Mains", "first_date": "2026-12-01", "last_date": "2027-01-31",
              "total": 62, "today": "2026-12-10", "server_now": now, "slots": slots, "today_slot": slots[9]}
    streak = {"stage": "live", "completed_count": 7, "current_streak": 3, "best_streak": 5, "total_days": 62, "today_state": "today",
              "days": days, "milestones": [{"days": 7, "title": "Bronze", "earned": True}, {"days": 15, "title": "Silver", "earned": False},
                                           {"days": 30, "title": "Gold", "earned": False}, {"days": 45, "title": "Platinum", "earned": False},
                                           {"days": 62, "title": "Legend", "earned": False}]}
    items = [{"id": f"fx-live-{d}", "title": f"All India JEE Mains · Test {d:02d}", "mode": "series_live", "series_date": days[d - 1]["date"],
              "status": "completed", "resumable": False, "summary": {"score": SCORES[d], "maximum": 300}} for d in reversed(COMPLETED)]
    items.append({"id": "fx-practice-3", "title": "All India JEE Mains · Test 03", "mode": "series_practice", "series_date": days[2]["date"],
                  "status": "completed", "resumable": False, "summary": {"score": 88, "maximum": 300}})
    today_date = days[9]["date"]
    if variant == "resume":
        items.insert(0, {"id": "fx-live-10", "title": "All India JEE Mains · Test 10", "mode": "series_live", "series_date": today_date, "status": "active", "resumable": True, "remaining_seconds": 5000, "summary": None})
        days[9]["state"] = "in_progress"
    elif variant == "done":
        items.insert(0, {"id": "fx-live-10", "title": "All India JEE Mains · Test 10", "mode": "series_live", "series_date": today_date, "status": "completed", "resumable": False, "summary": {"score": 222, "maximum": 300}})
        days[9]["state"] = "completed"
    elif variant == "embargoed":
        items.insert(0, {"id": "fx-live-10", "title": "All India JEE Mains · Test 10", "mode": "series_live", "series_date": today_date, "status": "embargoed", "resumable": False, "summary": None})
        days[9]["state"] = "pending"
    history = {"items": items, "total": len(items)}
    return series, streak, history


async def install(page, variant="live"):
    s, st, h = build(variant)

    async def handler(route):
        url = route.request.url
        if "/history" in url:
            body = h
        elif url.split("?")[0].endswith("/streak"):
            body = st
        else:
            body = s
        await route.fulfill(status=200, content_type="application/json", body=json.dumps(body))

    await page.route("**/api/jl/series/all-india-jee**", handler)

    async def set_handler(route):
        if route.request.method != "GET":
            await route.fulfill(status=403, body="{}")
            return
        await route.fulfill(status=200, content_type="application/json", body=json.dumps({
            "id": "fixture-set-10", "title": "All India JEE Mains · Test 10", "exam": "jee-main", "test_kind": "series", "count": 75,
            "maximum": 300, "rules": {"correct": 4, "wrong": -1, "minutes": 180}, "questions": 75, "saved": False, "attempt": None}))

    await page.route("**/api/jl/my/sets/fixture-set-**", set_handler)
    # Block any writes (POST/PUT/DELETE) to attempts/sets during fixture tests
    async def block_writes(route):
        if route.request.method in ("POST", "PUT", "DELETE", "PATCH"):
            print("BLOCKED WRITE", route.request.method, route.request.url)
            await route.fulfill(status=403, content_type="application/json", body='{"detail":"blocked by test"}')
        else:
            await route.continue_()
    await page.route("**/api/jl/sets/**", block_writes)
