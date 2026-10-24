"""Explicit score correction versions. Original attempts, ledgers and reports are immutable."""

import copy
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from .db import db, sets, attempts, get, now, audit
from .auth import owner
from .safety import Capability, require_capability
from .packs import seal, unpack, hydrate
from pymongo.errors import DuplicateKeyError
from .canonical import FrozenLedger, source_commitment, verify_ledger
from tejas_core import score_attempt

router = APIRouter(prefix="/api", tags=["Score corrections"])


async def freeze_ledger(a):
    from starlette.concurrency import run_in_threadpool
    if a['status'] != 'completed':
        raise ValueError('Only sealed attempts may have a frozen ledger')
    verify_ledger(a)
    if a.get('ledger'):
        return a['ledger']
    result = await run_in_threadpool(score_attempt, a)
    fields = [
        "id",
        "response",
        "normalized_response",
        "accepted_answers",
        "outcome",
        "disposition",
        "marks",
        "marks_exact",
        "reason_code",
        "accepted_at",
        "content_version",
        "key_version",
        "profile_id",
        "solution_release",
        "marked",
    ]
    ledger = FrozenLedger(
        _id=a['id'], id=a['id'], attempt_id=a['id'], user_id=a['user_id'],
        summary=result['summary'], rows=[{k: q.get(k) for k in fields} for q in result['questions']],
        engine_version=1, created_at=now(), source_commitment=source_commitment(a),
        source_pack_id=a.get('pack_id'), sealed_seq=a.get('sealed_seq', 0),
    )
    try:
        await db.tejas_ledgers.update_one({'id': a['id']}, {'$setOnInsert': ledger.to_mongo()}, upsert=True)
    except DuplicateKeyError:
        pass
    stored = await db.tejas_ledgers.find_one({'id': a['id']}, {'_id': 0})
    verify_ledger({**a, 'ledger': stored})
    return stored


async def with_grade(a, version=None):
    if not version or version == "original":
        return a
    grade = await db.tejas_score_versions.find_one(
        {"id": version, "attempt_id": a["id"], "user_id": a["user_id"]}, {"_id": 0}
    )
    if not grade:
        raise HTTPException(
            404, "This score version is not available for this attempt."
        )
    out = copy.deepcopy(a)
    out['original_summary'] = a['ledger']['summary']
    out['original_ledger'] = copy.deepcopy(a['ledger'])
    out["questions"] = await unpack(grade["pack_id"])
    out["ledger"] = grade["ledger"]
    out["key_version"] = grade["key_version"]
    out["score_version"] = grade["id"]
    out["change_note"] = grade["note"]
    return out


async def run_regrade(job):
    require_capability(Capability.REGRADE)
    s = job["payload"]["set_snapshot"]
    latest = {q["id"]: q for q in s["questions"]}
    created = skipped = 0
    from .jobs import require_lease
    from starlette.concurrency import run_in_threadpool
    async for record in attempts.find(
        {"set_id": s["id"], "status": "completed", "version": {"$lt": s["version"]}},
        {"_id": 0, "command_receipts": 0, "response_schema": 0, "start_receipts": 0},
    ).batch_size(50):
        await require_lease(job)
        a = await hydrate(record)
        qs = []
        compatible = True
        for old in a["questions"]:
            q = latest.get(old["id"])
            if not q or any(
                q.get(k) != old.get(k)
                for k in ["number", "type", "text", "options", "q_refs"]
            ):
                compatible = False
                break
            revised = copy.deepcopy(old)
            for k in [
                "answer",
                "accepted_answers",
                "disposition",
                "solution",
                "s_refs",
                "solution_accessible_text",
                "review_note",
            ]:
                revised[k] = q.get(
                    k,
                    (
                        []
                        if k in ["accepted_answers", "s_refs"]
                        else "standard" if k == "disposition" else ""
                    ),
                )
            qs.append(revised)
        if not compatible or any(
            a["rules"].get(k) != s["rules"].get(k)
            for k in ["correct", "wrong", "skipped"]
        ):
            skipped += 1
            continue
        graded = copy.deepcopy(a)
        graded["questions"] = qs
        graded.pop("ledger", None)
        graded["key_version"] = s["version"]
        result = await run_in_threadpool(score_attempt, graded)
        pack_id = await seal(qs)
        gid = f"{a['id']}-key-{s['version']}"
        fields = [
            "id",
            "response",
            "normalized_response",
            "accepted_answers",
            "outcome",
            "disposition",
            "marks",
            "marks_exact",
            "reason_code",
            "accepted_at",
            "content_version",
            "key_version",
            "profile_id",
            "solution_release",
            "marked",
        ]
        ledger = {
            "summary": result["summary"],
            "rows": [{k: q.get(k) for k in fields} for q in result["questions"]],
            "engine_version": 1,
        }
        await require_lease(job)
        await db.tejas_score_versions.update_one(
            {"id": gid},
            {
                "$setOnInsert": {
                    "id": gid,
                    "attempt_id": a["id"],
                    "user_id": a["user_id"],
                    "set_id": s["id"],
                    "pack_id": pack_id,
                    "key_version": s["version"],
                    "note": job["payload"]["note"],
                    "created_at": now(),
                    "ledger": ledger,
                }
            },
            upsert=True,
        )
        created += 1
    return f"Correction versions created for {created} completed attempts. {skipped} incompatible content/rule snapshots were left unchanged. Original scores and reports are preserved."


@router.post("/studio/sets/{id}/regrade")
async def regrade(id: str, data: dict, bg: BackgroundTasks, u=Depends(owner)):
    require_capability(Capability.REGRADE)
    s = await get(sets, id)
    note = str(data.get("note", "")).strip()
    if len(note) < 10:
        raise HTTPException(
            400,
            "Provide a clear student-facing correction note of at least 10 characters.",
        )
    if s["status"] != "published" or any(not q.get("approved") for q in s["questions"]):
        raise HTTPException(
            400, "Publish the fully reviewed correction version before regrading."
        )
    from .jobs import enqueue, run_job

    j = await enqueue(
        "regrade",
        u["id"],
        id,
        {"set_snapshot": s, "note": note, "key": f"{id}-v{s['version']}"},
    )
    bg.add_task(run_job, j["id"])
    await audit(u["id"], "Score correction requested", id, note)
    return j
