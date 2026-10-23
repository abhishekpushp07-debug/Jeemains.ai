# Iteration 127 TEST-ONLY fixture. Wraps iter126 fixture but fixes the Player state model:
# useAttempt.visit() does `data.current.visited = r.visited` from POST /attempts/:id/visit, so the fixture
# MUST return {"visited": [...]} (126 returned {"ok": true} -> visited wiped to undefined -> no 'visited' class).
# answers is a map {qid: {value, marked, revision}}. PUT /answers is delayed so the 'pending-answer' state is observable.
# Usage: ns={}; exec(open('/app/tests/frontend_iter127_fixture.py').read(), ns); log = await ns['install127'](page)
import asyncio
exec(open('/app/tests/frontend_iter126_fixture.py').read(), globals())


def attempt_fixture_127(state):
    a = attempt_fixture()
    a["answers"] = {
        "p2": {"value": "A", "marked": False, "revision": 1},
        "p4": {"value": "", "marked": True, "revision": 1},
        "p5": {"value": "B", "marked": True, "revision": 1},
    }
    a["visited"] = list(state["visited"])
    return a


async def install127(page, put_delay=8):
    from urllib.parse import urlparse
    state = {"visited": ["p1", "p2", "p3", "p4", "p5"]}
    log = {"non_get": [], "get": [], "unmocked": []}
    base_log = await install(page)

    async def handle(route):
        req = route.request
        path = urlparse(req.url).path
        if path == '/api/attempts/play1' and req.method == 'GET':
            log["get"].append(path)
            return await route.fulfill(status=200, content_type='application/json', body=json.dumps(attempt_fixture_127(state)))
        if path == '/api/attempts/play1/visit' and req.method == 'POST':
            qid = json.loads(req.post_data or '{}').get('question_id')
            if qid and qid not in state["visited"]:
                state["visited"].append(qid)
            log["non_get"].append('POST ' + path + ' ' + str(qid))
            return await route.fulfill(status=200, content_type='application/json', body=json.dumps({"visited": state["visited"], "server_now": time.time()}))
        if re.search(r'/attempts/play1/answers/', path) and req.method == 'PUT':
            log["non_get"].append('PUT ' + path)
            await asyncio.sleep(put_delay)
            body = json.loads(req.post_data or '{}')
            acc = {**body, "normalized_value": body.get("value", ""), "revision": body.get("revision", 1)}
            try:
                return await route.fulfill(status=200, content_type='application/json', body=json.dumps({"accepted": acc, "current_revision": acc["revision"], "server_now": time.time()}))
            except Exception:
                return
        return await route.fallback()
    await page.route('**/api/**', handle)  # registered last -> runs first; fallback goes to 126 handler
    return {"own": log, "base": base_log, "state": state}
