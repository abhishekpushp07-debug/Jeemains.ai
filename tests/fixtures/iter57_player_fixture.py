# Iteration57: test-only Playwright fixture for player attempt qa-mock-1 (no real writes).
import json, time

SUBJ = ["Physics", "Chemistry", "Mathematics"]


def attempt(deadline_in=540):
    now = int(time.time())
    qs = []
    for i in range(15):
        n = i + 1
        integer = n % 5 == 0
        qs.append({"id": f"q{n}", "number": n, "subject": SUBJ[i // 5], "type": "integer" if integer else "mcq",
                   "text": f"Fixture question {n}: a body moves with velocity v. Choose the correct value.",
                   "options": {} if integer else {"A": "Option alpha", "B": "Option beta", "C": "Option gamma", "D": "Option delta"}})
    return {"id": "qa-mock-1", "title": "QA Fixture Mock", "status": "active", "deadline": now + deadline_in, "server_now": now,
            "rules": {"correct": 4, "wrong": -1, "minutes": 180}, "questions": qs,
            "answers": {"q1": {"value": "B", "marked": False, "revision": 1, "request_id": "r1"},
                        "q2": {"value": "A", "marked": True, "revision": 1, "request_id": "r2"},
                        "q3": {"value": "", "marked": True, "revision": 1, "request_id": "r3"}},
            "visited": ["q1", "q2", "q3", "q4"], "confidence_observations": {}}


async def install(page, deadline_in=540, log=None):
    data = attempt(deadline_in)
    visited = list(data["visited"])

    async def handler(route):
        req = route.request
        url = req.url.split("?")[0]
        m = req.method
        if m == "GET" and url.endswith("/attempts/qa-mock-1"):
            body = data
        elif url.endswith("/visit"):
            try:
                qid = (req.post_data_json or {}).get("question_id")
            except Exception:
                qid = None
            if qid and qid not in visited:
                visited.append(qid)
            body = {"visited": visited}
        elif "/answers/" in url and m == "PUT":
            b = req.post_data_json or {}
            body = {"accepted": b, "current_revision": b.get("revision", 1), "server_now": int(time.time())}
        elif url.endswith("/submit"):
            if log is not None:
                log.append("SUBMIT CALLED")
            body = {"detail": "blocked by test"}
            await route.fulfill(status=409, content_type="application/json", body=json.dumps(body))
            return
        else:
            body = {}
        if log is not None and m != "GET":
            log.append(f"{m} {url.split('/api/jl')[-1]}")
        await route.fulfill(status=200, content_type="application/json", body=json.dumps(body))

    await page.route("**/api/jl/attempts/qa-mock-1**", handler)
