import copy
import uuid
from fastapi import APIRouter, Depends, HTTPException, Response, BackgroundTasks
from pydantic import BaseModel, Field
from pymongo import ReturnDocument
from pymongo.errors import DuplicateKeyError
from starlette.concurrency import run_in_threadpool
from .db import attempts, sets, files, db, uid, now, get, audit, clean
from .auth import current
from .packs import hydrate, insert_attempt
from .profiles import seal_profile
from .catalog import page as catalogue_page
from .content import summary, permitted, validate_refs
from tejas_core import public_question, score_attempt, crop_png
from tejas_storage import get_object

from .idempotency import fingerprint, verify_start, bind_start_alias
from .contracts import EnvelopeResponse
from .derivatives import render_crop
from .canonical import EPOCH_NOW, clocked_one, verify_ledger, database_now
from pydantic import ConfigDict

router = APIRouter(prefix="/api", tags=["Practice"])


class Start(BaseModel):
    model_config = ConfigDict(extra="forbid")
    start_key: str = Field(min_length=8, max_length=100)
    device_checked: bool = False
    preview: bool = False


def delivered(q):
    p = public_question(q)
    if q.get('source_option_labels'):
        p['source_option_labels'] = q['source_option_labels']
    p["asset_count"] = len(q.get("q_refs", []))
    p.pop("q_refs", None)
    # Native extracted text can be inaccurate. Only reviewed source alt text is exposed in image mode.
    if q.get("render_mode") == "source":
        p["text"] = q.get("accessible_text", "")
    return p


async def owned(id, u):
    a = await clocked_one(attempts, {"id": id, "user_id": u["id"]}, {"_id": 0, "command_receipts": 0, "response_schema": 0})
    if not a:
        raise HTTPException(404, "Attempt not found.")
    if a["status"] == "completed":
        ledger = await db.tejas_ledgers.find_one({"id": id}, {"_id": 0})
        if ledger:
            a["ledger"] = ledger
    a = await hydrate(a)
    verify_ledger(a)
    return a


async def ensure_grade(a, bg=None):
    """Embedded grading_status is the durable outbox if enqueue crashes."""
    if a.get("status") != "completed" or a.get("ledger") or a.get("grading_status") == "ready":
        return None
    from .jobs import enqueue, run_job
    j = await enqueue("grade", a["user_id"], a["set_id"], {"attempt_id": a["id"]})
    if j['status'] == 'failed':
        await attempts.update_one({'id': a['id'], 'grading_status': {'$ne': 'ready'}}, {'$set': {'grading_status': 'failed'}})
    if bg and j["status"] in ("queued", "running"):
        bg.add_task(run_job, j["id"])
    return j


async def finalize(id, reason="submitted", *, projection=None):
    t = EPOCH_NOW
    expired = {"$and": [{"$gt": ["$deadline", 0]}, {"$lte": ["$deadline", t]}]}
    fields = projection or {"_id": 0, "command_receipts": 0, "response_schema": 0}
    guard = {"id": id, "status": "active"}
    if reason == 'time_limit':
        guard['$expr'] = expired
    a = await attempts.find_one_and_update(
        guard,
        [{"$set": {
            "status": "completed", "submitted_at": {"$cond": [expired, "$deadline", t]},
            "sealed_at": t, "sealed_seq": {"$ifNull": ["$server_seq", 0]},
            "reason": {"$cond": [expired, "time_limit", reason]},
            "receipt": id, "grading_status": "queued",
        }}],
        projection=fields,
        return_document=ReturnDocument.AFTER,
    )
    if not a:
        a = await clocked_one(attempts, {"id": id}, fields)
    elif a.get('sealed_at'):
        a['_database_now'] = a['sealed_at']
    if not a:
        raise HTTPException(404, "Attempt not found.")
    return clean(a)


async def expire(a):
    if a['status'] == 'active' and a.get('deadline'):
        if '_database_now' not in a:
            state = await clocked_one(attempts, {'id': a['id'], 'user_id': a['user_id']}, {'_id': 0, 'id': 1, 'status': 1, 'deadline': 1})
            if not state:
                raise HTTPException(404, 'Attempt not found.')
            if state['status'] != 'active':
                a = await get(attempts, a['id'])
            a['_database_now'] = state['_database_now']
        if a['status'] == 'active' and a['_database_now'] >= a['deadline']:
            a = await finalize(a['id'], 'time_limit')
    return await hydrate(a)


def attempt_view(a):
    fields = [
        "id",
        "set_id",
        "title",
        "exam",
        "mode",
        "version",
        "rules",
        "started_at",
        "deadline",
        "status",
        "answers",
        "submitted_at",
        "receipt",
        "reason",
        "summary",
        "profile",
        "visited",
        "test_kind",
        "bonus_unlocked_at",
        "series_id", "series_date",
    ]
    return {
        **{k: a.get(k) for k in fields},
        "summary": a.get('summary') if a.get('competition_end', 0) <= a.get('_database_now', now()) else None,
        "competition_end": a.get('competition_end'),
        'confidence_observations': {qid: {'probability': x.get('confidence'), 'response': x.get('normalized_value', x.get('value',''))} for qid,x in a.get('first_answers',{}).items()},
        'confidence_changed_questions': a.get('confidence_changed_questions', []),
        "questions": [delivered(q) for q in a["questions"]],
        "server_now": a.get('_database_now', now()),
        "count": len(a["questions"]),
    }


@router.get("/my/sets")
async def my_sets(exam: str = "", q: str = "", page: int = 1, u=Depends(current)):
    from .catalog import available

    data = await catalogue_page(available(u, exam, q), page)
    return {"items": [summary(s) for s in data], "page": page}


@router.get("/my/sets/{id}")
async def my_set(id: str, u=Depends(current)):
    s = await get(sets, id)
    if s["status"] != "published" or not permitted(s, u, at=await database_now()):
        raise HTTPException(404, "This set is not available to your account.")
    return summary(s)


@router.post("/sets/{id}/preflight")
async def preflight(id: str, data: dict, u=Depends(current)):
    s = await get(sets, id)
    preview = data.get("preview") and u["role"] in ["owner", "reviewer"]
    t = await database_now()
    if not preview and (s["status"] != "published" or not permitted(s, u, at=t)):
        raise HTTPException(404, "This set is not available.")
    if not s["questions"]:
        raise HTTPException(400, "This set has no questions yet.")
    source_map = {}
    # The same supplied key crop may be referenced by all 50 questions. Validate
    # each exact source region once per request, never cache across users/releases.
    unique_refs = []
    seen_refs = set()
    import json
    for q in s['questions']:
        for kind in ('q_refs', 's_refs'):
            for ref in q.get(kind, []):
                identity = json.dumps(ref, sort_keys=True, separators=(',', ':'))
                if identity not in seen_refs:
                    seen_refs.add(identity)
                    unique_refs.append(ref)
    await validate_refs(s, {'q_refs': unique_refs, 's_refs': []}, source_map)
    await db.tejas_preflight.update_one(
        {"user_id": u["id"], "set_id": id},
        {
            "$set": {
                "revision": s["revision"],
                "at": t,
                "test_response": str(data.get("test_response", ""))[:30],
            }
        },
        upsert=True,
    )
    return {
        "ok": True,
        "message": "Connection, source assets and test response verified. No attempt or timer has started.",
        "server_now": t,
    }


@router.post("/sets/{id}/start")
async def start(id: str, data: Start, u=Depends(current)):
    existing = await attempts.find_one(
        {"user_id": u["id"], "$or": [{"start_key": data.start_key}, {"start_request_keys": data.start_key}]}, {"_id": 0, "command_receipts": 0, "response_schema": 0}
    )
    if existing:
        verify_start(existing, id, data)
        return attempt_view(await expire(existing))
    s = await clocked_one(sets, {'id': id}, {'_id': 0, 'questions.ai_solution': 0})
    if not s:
        raise HTTPException(404, 'This set is not available.')
    started_at = s.pop('_database_now')
    preview = data.preview and u["role"] in ["owner", "reviewer"]
    from .live_series import series_mode, guard_start, window, valid_paper
    mode = "preview" if preview else (series_mode(s, started_at) or "practice")
    series_live = mode == 'series_live'
    competition_id = str(uuid.uuid5(uuid.NAMESPACE_URL, 'competition:' + id + ':' + u['id'])) if (s.get('competition') or series_live) and not preview else None
    if competition_id:
        first = await attempts.find_one({'id': competition_id}, {'_id': 0, 'command_receipts': 0, 'response_schema': 0})
        if first:
            await bind_start_alias(first, id, data)
            return attempt_view(await expire(first))
    active = await attempts.find_one(
        {"user_id": u["id"], "set_id": id, "mode": mode, "status": "active"}, {"_id": 0}
    )
    if active:
        active = await expire(active)
        if active["status"] == "active":
            await bind_start_alias(active, id, data)
            return attempt_view(active)
    if not preview and (s["status"] != "published" or not permitted(s, u, at=started_at)):
        raise HTTPException(404, "This set is not available to start.")
    if not preview:
        guard_start(s, started_at)
        if s.get('series_id') and not valid_paper(s):
            raise HTTPException(409, 'This series paper needs owner review before new attempts can start.')
    if not data.device_checked:
        raise HTTPException(400, "Complete the device and content check first.")
    pf = await db.tejas_preflight.find_one(
        {
            "user_id": u["id"],
            "set_id": id,
            "revision": s["revision"],
            "at": {"$gt": started_at - 1800},
        }
    )
    if not pf:
        raise HTTPException(
            400, "Run the connection and content check again before starting."
        )
    if not s["questions"]:
        raise HTTPException(400, "No questions are available.")
    from .exam_navigation import classify_set
    a = {
        "test_kind": classify_set(s),
        "id": competition_id or uid(),
        "user_id": u["id"],
        "set_id": id,
        "start_key": data.start_key,
        "start_request_keys": [data.start_key],
        "start_receipts": {fingerprint(data.start_key): fingerprint({"operation": "start", "set_id": id, **data.model_dump(exclude={"start_key"})})},
        "start_fingerprint": fingerprint({"operation": "start", "set_id": id, **data.model_dump(exclude={"start_key"})}),
        "server_seq": 0,
        "command_count": 0,
        "title": s["title"],
        "exam": s["exam"],
        "version": s["version"],
        "rules": copy.deepcopy(s["rules"]),
        "profile": await seal_profile(s),
        "visited": [],
        "questions": copy.deepcopy(s["questions"]),
        "attribution": s.get("attribution", ""),
        "report_allowed": bool(s.get("rights_report")),
        "mode": mode,
        "status": "active",
        "answers": {},
        'first_answers': {},
        'answer_history_version': 1,
        'solution_events_version': 1,
        'solution_opened': [],
        "started_at": started_at,
        "_database_now": started_at,
        "deadline": 0,
        "parent_attempt": None,
    }
    if not preview and s.get('series_id'):
        guard_start(s, a['started_at'])
        if series_mode(s, a['started_at']) != mode:
            raise HTTPException(409, 'The series day changed. Reload before starting.')
        a.update(series_id=s['series_id'], series_date=s['series_date'], test_kind='mock')
        if series_live:
            a['competition_end'] = window(s['series_date'])['closes_at']
            a['competition_ranked'] = False
    if s.get('competition') and not preview:
        a['competition_end'] = s['end_at']
        a['competition_ranked'] = u.get('role') == 'student' and u.get('access_type') == 'unverified_phone'
    if a["rules"]["minutes"]:
        a["deadline"] = a["started_at"] + a["rules"]["minutes"] * 60
        if a.get('competition_end'):
            a['deadline'] = min(a['deadline'], a['competition_end'])
    try:
        await insert_attempt(a)
    except DuplicateKeyError:
        a = await attempts.find_one({'id': competition_id}, {'_id': 0}) if competition_id else None
        if not a:
            a = await attempts.find_one(
                {"user_id": u["id"], "set_id": id, "mode": mode, "status": "active"}
            )
        if not a:
            a = await attempts.find_one(
                {"user_id": u["id"], "start_key": data.start_key}, {"_id": 0, "command_receipts": 0, "response_schema": 0}
            )
            if a:
                verify_start(a, id, data)
        if not a:
            raise HTTPException(409, "Another start is being resolved. Retry with the same identifier.")
        await bind_start_alias(a, id, data)
    await audit(u["id"], "Attempt started", a["id"], mode)
    return attempt_view(await hydrate(a))


@router.get("/attempts")
async def history(page: int = 1, u=Depends(current)):
    fields = {k: 1 for k in ("id", "set_id", "title", "exam", "mode", "version", "rules", "started_at", "deadline", "status", "submitted_at", "receipt", "reason", "summary", "profile", "count", "grading_status", "competition_end")}
    data = await attempts.find({"user_id": u["id"]}, {"_id": 0, **fields, '_database_now': EPOCH_NOW}).sort("started_at", -1).skip((max(1, min(page, 10000)) - 1) * 20).limit(20).to_list(20)
    for a in data:
        t = a.pop('_database_now')
        if a["status"] == "active" and a["deadline"] and t >= a["deadline"]:
            closed = await finalize(a["id"], "time_limit", projection={'_id': 0, **fields})
            a.update({k: v for k, v in closed.items() if k in fields})
        a["server_now"] = t
        if a.get('competition_end', 0) > t: a['summary'] = None
    return {"items": data, "page": page}


@router.get("/attempts/{id}")
async def read_attempt(id: str, u=Depends(current)):
    return attempt_view(await expire(await owned(id, u)))


class Visit(BaseModel):
    question_id: str = Field(min_length=36, max_length=36)


@router.post("/attempts/{id}/visit")
async def visit_question(id: str, data: Visit, u=Depends(current)):
    from uuid import UUID
    qid = data.question_id
    try:
        UUID(qid)
    except ValueError:
        raise HTTPException(400, "Unknown question identity.")
    a = await clocked_one(attempts, {"id": id, "user_id": u["id"]}, {"_id": 0, "status": 1, "deadline": 1, "visited": 1, f"response_schema.{qid}": 1, "questions.id": 1})
    if not a:
        raise HTTPException(404, "Attempt not found.")
    if a["status"] != "active" or (a["deadline"] and a['_database_now'] >= a["deadline"]):
        if a["status"] == "active":
            await finalize(id, "time_limit")
        raise HTTPException(409, "The attempt has ended.")
    if qid not in a.get("response_schema", {}) and not any(q["id"] == qid for q in a.get("questions", [])):
        raise HTTPException(400, "Unknown question identity.")
    t = {"$divide": [{"$toLong": "$$NOW"}, 1000]}
    updated = await attempts.find_one_and_update({"id": id, "user_id": u["id"], "status": "active", "$expr": {"$or": [{"$eq": ["$deadline", 0]}, {"$gt": ["$deadline", t]}]}}, {"$addToSet": {"visited": qid}}, projection={"_id": 0, "visited": 1}, return_document=ReturnDocument.AFTER)
    if not updated:
        raise HTTPException(409, "The attempt has ended.")
    return updated


class BonusEntry(BaseModel):
    id: str
    bonus_unlocked_at: float
    server_now: float


@router.post("/attempts/{id}/bonus", response_model=BonusEntry)
async def unlock_bonus(id: str, u=Depends(current)):
    a = await clocked_one(attempts, {"id": id, "user_id": u["id"]}, {"_id": 0, "status": 1, "deadline": 1, "rules": 1, "answers": 1,
                                "response_schema": 1, "server_seq": 1, "bonus_unlocked_at": 1})
    if not a:
        raise HTTPException(404, "Attempt not found.")
    if not (a.get("rules") or {}).get("bonus_rule"):
        raise HTTPException(400, "This test has no bonus section.")
    if a.get("bonus_unlocked_at"):
        return {"id": id, "bonus_unlocked_at": a["bonus_unlocked_at"], "server_now": a['_database_now']}
    if a["status"] != "active" or (a["deadline"] and a['_database_now'] >= a["deadline"]):
        if a["status"] == "active":
            await finalize(id, "time_limit")
        raise HTTPException(409, "The attempt has ended.")
    main = [qid for qid, s in a.get("response_schema", {}).items() if not s.get("bonus")]
    missing = sum(not str(a.get("answers", {}).get(qid, {}).get("normalized_value", "")).strip() for qid in main)
    if missing:
        raise HTTPException(409, f"Answer all {len(main)} main questions first. {missing} still unanswered.")
    t = {"$divide": [{"$toLong": "$$NOW"}, 1000]}
    # server_seq CAS: no main answer may change between the completeness check and the lock.
    updated = await attempts.find_one_and_update(
        {"id": id, "user_id": u["id"], "status": "active", "bonus_unlocked_at": {"$exists": False},
         "server_seq": a.get("server_seq", 0), "$expr": {"$or": [{"$eq": ["$deadline", 0]}, {"$gt": ["$deadline", t]}]}},
        [{"$set": {"bonus_unlocked_at": t}}], projection={"_id": 0, "bonus_unlocked_at": 1}, return_document=ReturnDocument.AFTER)
    if not updated:
        raise HTTPException(409, "Your answers changed or time ended. Reload and try again.")
    await audit(u["id"], "Bonus section entered", id, "Main answers locked")
    return {"id": id, "bonus_unlocked_at": updated["bonus_unlocked_at"], "server_now": updated["bonus_unlocked_at"]}


class SubmissionReceipt(BaseModel):
    id: str
    receipt: str
    status: str
    submitted_at: float
    sealed_seq: int = 0
    grading_status: str
    command_state: str = "applied"


@router.post("/attempts/{id}/submit", response_model=SubmissionReceipt)
async def submit(id: str, bg: BackgroundTasks, response: Response, u=Depends(current)):
    a = await attempts.find_one({"id": id, "user_id": u["id"]}, {"_id": 0, "id": 1})
    if not a:
        raise HTTPException(404, "Attempt not found.")
    from .attempt_status import HEADER
    a = await finalize(id, projection=HEADER)
    # Dispatch is best effort; the seal/outbox survives a failure here.
    try:
        await ensure_grade(a, bg)
    except Exception:
        import logging
        logging.getLogger(__name__).error("Grade dispatch delayed; durable outbox retained")
    grading = a.get("grading_status", "ready" if a.get("summary") else "queued")
    response.status_code = 200 if grading == "ready" else 202
    response.headers["Location"] = f"/api/attempts/{id}/results"
    response.headers["Retry-After"] = "2"
    return {"id": id, "receipt": a["receipt"], "status": a["status"], "submitted_at": a["submitted_at"], "sealed_seq": a.get("sealed_seq", 0), "grading_status": grading}


@router.get("/attempts/{id}/results")
async def results(id: str, bg: BackgroundTasks, score_version: str = "original", u=Depends(current), confidence_threshold: float = 0.2):
    if not 0 <= confidence_threshold <= 1:
        raise HTTPException(422, 'Confidence threshold must be between 0 and 1.')
    from .corrections import with_grade

    a = await expire(await owned(id, u))
    if a['status'] == 'completed' and a.get('competition_end', 0) > a.get('_database_now', now()):
        return {'id': id, 'title': a['title'], 'status': 'embargoed', 'release_at': a['competition_end'], 'receipt': a.get('receipt'), 'server_now': a.get('_database_now', now()), 'series_id': a.get('series_id')}
    if a["status"] == "completed":
        if not a.get("ledger"):
            job = await ensure_grade(a, bg)
            return EnvelopeResponse({"id": id, "receipt": a.get("receipt"), "status": "grading", "grading_status": (job or {}).get("status", "queued"), "job_id": (job or {}).get("id"), "retry_after_ms": 2000}, status_code=202, headers={"Retry-After": "2"})
        a = await with_grade(a, score_version)
    if a["status"] != "completed":
        raise HTTPException(403, "Solutions are released only after submission.")
    result = score_attempt(a)
    for q in result["questions"]:
        q["asset_count"] = len(q.get("q_refs", []))
        q["solution_asset_count"] = len(q.get("s_refs", []))
    from .insights import insights
    from .reviews import states_for, review_summary
    a['review_states'] = await states_for(a)
    a['review_tracking_enabled'] = True
    from .analytics import build_analytics
    return {
        **attempt_view(a),
        **result,
        'analytics': build_analytics(a, result, confidence_threshold),
        'review': review_summary(a, result['questions']),
        'insights': insights(result),
        "grade_versions": await db.tejas_score_versions.find(
            {"attempt_id": id, "user_id": u["id"]},
            {"_id": 0, "ledger": 0, "pack_id": 0},
        )
        .sort("created_at", -1)
        .to_list(50),
        "score_version": a.get("score_version", "original"),
        "change_note": a.get(
            "change_note", "Original scoring, preserved as submitted."
        ),
        "report_allowed": a.get("report_allowed", False),
        "attribution": a.get("attribution", ""),
    }


@router.get("/attempts/{id}/questions/{qid}/asset/{kind}/{index}")
async def asset(
    id: str,
    qid: str,
    kind: str,
    index: int,
    score_version: str = "original",
    u=Depends(current),
):
    from .attempt_status import owned_header
    from .packs import question
    a = await owned_header(id, u)
    if kind not in ['question', 'solution'] or kind == 'solution' and (a['status'] != 'completed' or a.get('competition_end', 0) > a['_database_now']):
        raise HTTPException(403, 'Solution assets remain private until submission.')
    pack_id = a.get('pack_id')
    if a['status'] == 'completed' and score_version and score_version != 'original':
        grade = await db.tejas_score_versions.find_one({'id': score_version, 'attempt_id': id, 'user_id': u['id']}, {'_id': 0, 'pack_id': 1})
        if not grade:
            raise HTTPException(404, 'This score version is not available for this attempt.')
        pack_id = grade['pack_id']
    if pack_id:
        q = await question(pack_id, qid)
    else:
        legacy = await attempts.find_one({'id': id, 'user_id': u['id']}, {'_id': 0, 'questions': {'$elemMatch': {'id': qid}}})
        q = next(iter((legacy or {}).get('questions', [])), None)
    if not q or (a['status'] == 'active' and q.get('bonus') and not a.get('bonus_unlocked_at')):
        raise HTTPException(404, 'Question not found.')
    refs = q.get("q_refs" if kind == "question" else "s_refs", [])
    if not 0 <= index < len(refs):
        raise HTTPException(404, "Asset not found.")
    f = await get(files, refs[index]["file_id"])
    return Response(
        await run_in_threadpool(render_crop, f, refs[index]), media_type="image/png",
        headers={"Cache-Control": "private, no-store"},
    )


class SolutionConsulted(BaseModel):
    question_id: str
    recorded: bool


@router.post('/attempts/{id}/questions/{qid}/solution-open', response_model=SolutionConsulted)
async def solution_consulted(id: str, qid: str, u=Depends(current)):
    a = await owned(id, u)
    if a['status'] != 'completed' or a.get('competition_end', 0) > a.get('_database_now', now()):
        raise HTTPException(403, 'Solutions are not released for this attempt yet.')
    if not any(q['id'] == qid for q in a['questions']):
        raise HTTPException(404, 'Question not found.')
    await attempts.update_one({'id':id,'user_id':u['id'],'status':'completed'}, {'$addToSet':{'review_solution_opened':qid}})
    if a.get('solution_events_version') != 1:
        return SolutionConsulted(question_id=qid, recorded=False)
    await attempts.update_one({'id':id,'user_id':u['id'],'status':'completed'}, {'$addToSet':{'solution_opened':qid}})
    return SolutionConsulted(question_id=qid, recorded=True)


@router.post("/attempts/{id}/retry")
async def retry(id: str, data: dict, u=Depends(current)):
    from .corrections import with_grade

    a = await expire(await owned(id, u))
    if a.get('competition_end', 0) > a.get('_database_now', now()):
        raise HTTPException(403, 'Revision attempts unlock when the competition window closes.')
    if a["status"] == "completed" and not a.get("ledger"):
        raise HTTPException(409, "Your answers are sealed. Wait for grading before starting a retry.", headers={"Retry-After": "2"})
    if a["status"] == "completed":
        a = await with_grade(a, data.get("score_version"))
    if a["status"] != "completed":
        raise HTTPException(400, "Complete the original attempt first.")
    qs = [
        q
        for q in score_attempt(a)["questions"]
        if q["outcome"] in ["incorrect", "skipped"]
    ]
    if not qs:
        raise HTTPException(
            400, "There are no incorrect or skipped questions to retry."
        )
    start_key = str(data.get("start_key", ""))
    if not 8 <= len(start_key) <= 100:
        raise HTTPException(400, "A retry request identifier of 8–100 characters is required.")
    retry_hash = fingerprint({"operation": "retry", "parent_attempt": id, "score_version": data.get("score_version") or "original"})
    existing = await attempts.find_one({"user_id": u["id"], "$or": [{"start_key": start_key}, {"start_request_keys": start_key}]}, {"id": 1, "parent_attempt": 1, "retry_fingerprint": 1})
    if existing:
        if existing.get("parent_attempt") != id or (existing.get("retry_fingerprint") and existing["retry_fingerprint"] != retry_hash):
            raise HTTPException(409, "This retry identifier belongs to a different request.")
        return {"id": existing["id"]}
    active = await attempts.find_one(
        {"user_id": u["id"], "set_id": a["set_id"], "mode": "retry", "status": "active"}
    )
    if active:
        if active.get("parent_attempt") != id or (active.get("retry_fingerprint") and active["retry_fingerprint"] != retry_hash):
            raise HTTPException(409, "Finish your existing revision attempt before starting a different one.")
        from .idempotency import bind_retry_alias
        await bind_retry_alias(active, start_key, retry_hash)
        return {"id": active["id"]}
    a.update(
        {
            "id": uid(),
            "title": a["title"] + " — Mistake retry",
            "parent_attempt": id,
            "start_key": start_key,
            "retry_fingerprint": retry_hash,
            "server_seq": 0,
            "command_count": 0,
            "questions": qs,
            "rules": {k: v for k, v in {**a["rules"], "minutes": 0}.items() if k != "bonus_rule"},
            "mode": "retry",
            "status": "active",
            "answers": {},
            'first_answers': {},
            'answer_history_version': 1,
            'solution_events_version': 1,
            'solution_opened': [],
            "started_at": now(),
            "deadline": 0,
        }
    )
    for k in [
        "_id",
        "summary",
        "submitted_at",
        "receipt",
        "reason",
        "ledger",
        "score_version",
        "change_note",
        "visited",
        "start_fingerprint",
        "start_request_keys",
        "start_receipts",
        "grading_status",
        "sealed_at",
        "sealed_seq",
        "command_receipts",
        'confidence_changed_questions',
        'review_states',
        'review_tracking_enabled',
        'review_solution_opened',
        'competition_end',
        'competition_ranked',
        'bonus_unlocked_at',
        'series_id',
        'series_date',
    ]:
        a.pop(k, None)
    a['start_request_keys'] = [start_key]
    a['retry_receipts'] = {fingerprint(start_key): retry_hash}
    a["visited"] = []
    a["profile"] = await seal_profile(
        {
            "exam": a["exam"],
            "year": a.get("profile", {}).get("year", ""),
            "source": "Untimed revision of an existing attempt; repeated exposure, not a readiness estimate.",
            "rules": a["rules"],
            "questions": qs,
        }
    )
    try:
        await insert_attempt(a)
    except DuplicateKeyError:
        a = await attempts.find_one(
            {"user_id": u["id"], "$or": [
                {"start_key": start_key},
                {"start_request_keys": start_key},
                {"set_id": a["set_id"], "mode": "retry", "status": "active"},
            ]}, {"_id": 0, "id": 1, "parent_attempt": 1, "retry_fingerprint": 1},
        )
        if not a or a.get("parent_attempt") != id or a.get("retry_fingerprint") != retry_hash:
            raise HTTPException(409, "A different start or revision request already used this identifier.")
        from .idempotency import bind_retry_alias
        await bind_retry_alias(a, start_key, retry_hash)
    await audit(
        u["id"],
        "Mistake retry started",
        a["id"],
        f"Original {id}; untimed; repeated exposure",
    )
    return {"id": a["id"]}


@router.post("/attempts/{id}/report")
async def report(id: str, bg: BackgroundTasks, data: dict, u=Depends(current)):
    from .corrections import with_grade

    a = await expire(await owned(id, u))
    if a.get('competition_end', 0) > a.get('_database_now', now()):
        raise HTTPException(403, 'Reports unlock when the competition window closes.')
    version = str(data.get("score_version", "original"))
    if a["status"] == "completed" and not a.get("ledger"):
        await ensure_grade(a, bg)
        raise HTTPException(409, "Your answers are sealed. The report becomes available after grading.", headers={"Retry-After": "2"})
    if a["status"] == "completed":
        a = await with_grade(a, version)
    if a["status"] != "completed":
        raise HTTPException(403, "Submit before generating your report.")
    if not a.get("report_allowed"):
        raise HTTPException(
            403,
            "Personal report redistribution rights have not been confirmed for this source.",
        )
    from .jobs import enqueue, run_job

    j = await enqueue(
        "report", u["id"], a["set_id"], {"attempt_id": id, "score_version": version, "template_version": "jeemains-ai-v1"}
    )
    bg.add_task(run_job, j["id"])
    return j
