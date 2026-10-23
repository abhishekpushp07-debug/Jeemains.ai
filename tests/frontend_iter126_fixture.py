# Iteration 126 TEST-ONLY Playwright API fixture (not shipped, not under frontend/public).
# Usage inside browser_automation: ns={}; exec(open('/app/tests/frontend_iter126_fixture.py').read(), ns); log = await ns['install'](page)
# Every /api/** request is fulfilled locally: fake session, mocked GETs, all non-GET recorded and answered locally. No real backend/DB/AI.
import json, time, re

SUBJ = [('Physics', 1, 25), ('Chemistry', 26, 50), ('Mathematics', 51, 75)]


def _outcome(n):
    if n == 74: return 'dropped'
    if n == 75: return 'bonus'
    return ['correct', 'incorrect', 'skipped'][n % 3]


def result_fixture(version='original'):
    qs = []
    for name, a, b in SUBJ:
        for n in range(a, b + 1):
            o = _outcome(n)
            qs.append({"id": f"q{n}", "number": n, "subject": name, "outcome": o, "marked": n % 7 == 0, "bonus": o == 'bonus',
                       "type": "mcq", "options": {"A": f"opt A{n}", "B": f"opt B{n}", "C": f"opt C{n}", "D": f"opt D{n}"},
                       "response": None if o == 'skipped' else ("A" if o == 'correct' else "B"), "answer": "A", "accepted_answers": ["A"],
                       "marks": 4 if o == 'correct' else (-1 if o == 'incorrect' else 0), "marks_exact": "4", "reason_code": "ok",
                       "key_version": 2 if version == 'gv2' else 1, "solution_kind": "supplied_worked", "render_mode": "text",
                       "text": f"FIXTURE stem {n}", "solution": f"FIXTURE worked solution {n} ({version})", "solution_number": n})
    score = 120 if version == 'gv2' else 100
    subjects = {s: {"score": 30, "correct": 8, "attempted": 16, "count": 25} for s, _, _ in SUBJ}
    return {"id": "att1", "exam": "JEE Main", "title": "FIXTURE JEE Main Mock 01", "mode": "practice", "status": "completed",
            "score_version": version, "change_note": "FIXTURE key correction for Q12.",
            "grade_versions": [{"id": "gv2", "key_version": 2, "created_at": 1736000000}],
            "summary": {"score": score, "maximum": 300, "percentage": round(score / 3, 1), "correct": 24, "incorrect": 24, "skipped": 25,
                        "attempt_rate": 66, "attempted": 48, "eligible_count": 75, "accuracy": 50, "penalties": 24, "total_seconds": 9000,
                        "subjects": subjects, "topics": {}},
            "rules": {"correct": 4, "wrong": -1, "minutes": 180}, "count": 75, "version": 1, "submitted_at": 1736000000,
            "receipt": None, "insights": None, "reason": None, "confidence_observations": {}, "confidence_changed_questions": [],
            "questions": qs, "review": {"states": {}, "categories": ["Concept", "Calculation"], "assigned": ["q1"]}, "analytics": None}


def attempt_fixture():
    now = time.time()
    qs = []
    for name, a, b in SUBJ:
        for n in range(a, b + 1):
            qs.append({"id": f"p{n}", "number": n, "subject": name, "type": "integer" if n in (21, 46, 71) else "mcq", "render_mode": "text",
                       "text": f"FIXTURE player stem {n}: a particle moves with v = {n} m/s. Find the displacement.",
                       "options": {"A": f"{n} m", "B": f"{2*n} m", "C": f"{3*n} m", "D": f"{4*n} m"}})
    return {"id": "play1", "exam": "JEE Main", "title": "FIXTURE JEE Main Mock 01", "mode": "practice", "status": "active", "count": 75,
            "rules": {"correct": 4, "wrong": -1, "minutes": 180}, "deadline": now + 3 * 3600, "server_now": now,
            "questions": qs, "answers": {}, "visited": [], "confidence_observations": {}, "series_id": None}


def _set(i, subj, status=None):
    s = {"id": f"set{i}", "title": f"FIXTURE {subj} Chapter {i}", "exam": "JEE Main", "subjects": [subj], "chapter_subject": subj,
         "chapter_number": i, "count": 25, "maximum": 100, "rules": {"correct": 4, "wrong": -1, "minutes": 60}, "source": "FIXTURE source",
         "saved": False, "end_at": None}
    if status: s["attempt"] = {"id": "att1" if status == 'completed' else "play1", "status": status}
    return s


def catalogue(qs):
    subject = (qs.get('subject') or [''])[0]
    kind = (qs.get('kind') or ['chapters'])[0]
    counts = {"Physics": 4, "Chemistry": 3, "Mathematics": 5}
    if kind == 'mocks':
        items = [_set(90 + i, 'Physics', st) for i, st in enumerate([None, 'active', 'completed'])]
    else:
        items = [_set(i, subject or 'Physics', st) for i, st in enumerate([None, 'active', 'completed', None][:counts.get(subject, 3)], 1)]
    return {"subject_counts": counts, "items": items if (subject or kind == 'mocks') else [], "total": len(items), "pages": 1}


def my_tests(qs):
    tab = (qs.get('tab') or ['progress'])[0]
    paper = {"count": 75, "rules": {"correct": 4, "wrong": -1, "minutes": 180}}
    if tab == 'progress':
        items = [{"id": "play1", "set_id": "set91", "title": "FIXTURE JEE Main Mock 01", "exam": "JEE Main", "mode": "practice", "status": "active",
                  "resumable": True, "saved_answers": 12, "remaining_seconds": 5400, "deadline": time.time() + 5400, "last_saved_at": time.time() - 60,
                  "started_at": time.time() - 3600, "paper": paper, "version": 1}]
    elif tab == 'completed':
        items = [{"id": "att1", "set_id": "set92", "title": "FIXTURE JEE Main Mock 01", "exam": "JEE Main", "mode": "practice", "status": "completed",
                  "resumable": False, "compare_eligible": True, "report_allowed": True, "started_at": time.time() - 86400, "paper": paper, "version": 1,
                  "summary": {"score": 100, "maximum": 300, "percentage": 33.3, "correct": 24, "incorrect": 24, "skipped": 25}},
                 {"id": "att2", "set_id": "set92", "title": "FIXTURE JEE Main Mock 01 (retry)", "exam": "JEE Main", "mode": "retry", "status": "expired",
                  "resumable": False, "compare_eligible": True, "report_allowed": True, "started_at": time.time() - 3 * 86400, "paper": paper, "version": 1,
                  "summary": {"score": 64, "maximum": 300, "percentage": 21.3, "correct": 18, "incorrect": 8, "skipped": 49}}]
    else:
        items = [{"id": "set93", "set_id": "set93", "title": "FIXTURE Saved Paper", "exam": "JEE Main", "available": True, "saved_at": time.time() - 500, "paper": paper}]
    return {"counts": {"progress": 1, "saved": 1, "completed": 2}, "items": items, "total": len(items), "pages": 1}


async def install(page, logged_in=True):
    from urllib.parse import urlparse, parse_qs
    log = {"non_get": [], "get": [], "unmocked": []}

    async def handle(route):
        req = route.request
        u = urlparse(req.url)
        path, qs = u.path, parse_qs(u.query)
        method = req.method

        def ok(body, status=200):
            return route.fulfill(status=status, content_type='application/json', body=json.dumps(body))
        if method != 'GET':
            log["non_get"].append(method + ' ' + path)
            if re.search(r'/attempts/[^/]+/answers/', path):
                body = json.loads(req.post_data or '{}')
                acc = {**body, "normalized_value": body.get("value", ""), "revision": body.get("revision", 1)}
                return await ok({"accepted": acc, "current_revision": acc["revision"], "server_now": time.time()})
            if path.endswith('/auth/refresh'):
                return await ok({"detail": "fixture"}, 401)
            return await ok({"ok": True, "server_now": time.time()})
        log["get"].append(path + ('?' + u.query if u.query else ''))
        if path == '/api/auth/session':
            return await ok({"user": {"id": "u_fixture", "role": "student", "name": "Fixture Student", "phone": "9900000199"}} if logged_in else {"user": None})
        if path == '/api/attempts/att1/results':
            return await ok(result_fixture((qs.get('score_version') or ['original'])[0]))
        if path.endswith('/question-reports'):
            return await ok([])
        if path == '/api/attempts/play1':
            return await ok(attempt_fixture())
        if '/exam-navigation/' in path and path.endswith('/catalogue'):
            return await ok(catalogue(qs))
        if path == '/api/my/tests':
            return await ok(my_tests(qs))
        log["unmocked"].append(path)
        return await ok({"detail": "Not found (fixture)"}, 404)
    await page.route('**/api/**', handle)
    return log
