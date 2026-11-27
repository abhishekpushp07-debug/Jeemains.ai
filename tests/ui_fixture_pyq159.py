# Browser-only read-only fixtures for JEE PYQ catalogue UI QA (iteration 159). Paste into browser_automation.
# Uses the actual exported 30-paper metadata (public evidence) + minutes 180 / maximum 300. Blocks all writes.
import json
BASE = 'https://jlive-ceo-inspect--0x57uoje.preview.emergentagent.com'
EVID = BASE + '/downloads/app-pin-integration/evidence/canonical-pyq.json'
writes, pyq_calls = [], []
MODE = {'v': 'normal'}  # normal | empty | error | slow
USER = {"id": "pyq-readonly-visual-fixture", "name": "Test Learner", "role": "student", "exam": "JEE Main", "access_type": "unverified_phone", "pin_configured": True}

def build_catalogue(evidence):
    items = []
    for p in evidence['papers']:
        items.append({**{k: p[k] for k in ('id', 'title', 'year', 'exam_date', 'shift', 'count')}, 'minutes': 180, 'maximum': 300, 'attempt': None, 'latest_result_id': None, 'attempt_count': 0})
    # active + older result, plural attempts
    items[0].update(attempt={"id": "att-fixture-active-1", "status": "active", "deadline": 0, "score": None}, latest_result_id='res-fixture-old-1', attempt_count=2)
    # completed + result, singular
    items[1].update(attempt={"id": "att-fixture-done-2", "status": "completed", "deadline": 0, "score": 120}, latest_result_id='res-fixture-done-2', attempt_count=1)
    # items[2] unattempted; items[3] completed many
    items[3].update(attempt={"id": "att-fixture-done-4", "status": "completed", "deadline": 0, "score": 200}, latest_result_id='res-fixture-done-4', attempt_count=3)
    years = sorted({i['year'] for i in items}, reverse=True)
    return {"items": items, "years": years, "total": len(items), "server_now": 1790000000, "source_note": "Original PDF questions with matched supplied explanations or answer keys; independent practice, not an NTA service."}

def wrap(d):
    return json.dumps({"data": d, "error": None, "meta": {"api_version": 1}})
