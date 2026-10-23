import copy, hashlib
from datetime import datetime, timezone
from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    UploadFile,
    File,
    Form,
    BackgroundTasks,
    Response,
)
from pydantic import BaseModel, Field
from starlette.concurrency import run_in_threadpool
from .db import db, sets, files, audits, jobs, uid, now, get, clean, audit
from .auth import staff, owner
from .safety import Capability, require_capability
from tejas_core import validate_pdf, crop_png, normalize_answer
from tejas_storage import put_object, get_object

router = APIRouter(prefix="/api", tags=["Content"])


class SetInput(BaseModel):
    title: str = Field(min_length=3, max_length=160)
    exam: str = "JEE Main"
    year: str = Field(default="", max_length=10)
    source: str = Field(default="", max_length=500)
    attribution: str = Field(default="", max_length=300)
    audience: str = "all"
    allowed_emails: list[str] = []
    allowed_phones: list[str] = []
    profile_mode: str = "practice"
    expires: str | None = ""
    rights_upload: bool = False
    rights_publish: bool = False
    rights_report: bool = False
    rules: dict = Field(
        default_factory=lambda: {
            "minutes": 0,
            "correct": 4,
            "wrong": -1,
            "skipped": 0,
            "numeric_rule": "Exact integer value; signs and leading zeros accepted; up to 20 digits. No rounding.",
        }
    )
    expected_revision: int | None = Field(default=None, ge=1)
    change_reason: str = Field(default="", max_length=1000)


def valid_rules(r):
    try:
        for k in ["minutes", "correct", "wrong", "skipped"]:
            if not isinstance(r[k], (int, float)) or isinstance(r[k], bool):
                raise ValueError()
        if (
            not 0 <= r["minutes"] <= 1440
            or not 0 < r["correct"] <= 100
            or not -100 <= r["wrong"] <= 0
            or r["skipped"] != 0
        ):
            raise ValueError()
    except (KeyError, ValueError, TypeError):
        raise HTTPException(
            400,
            "Rules require 0–1440 minutes, positive correct marks, nonpositive wrong marks, and zero unanswered marks.",
        )
    if (
        r.get("navigation", "free") != "free"
        or r.get("numeric_policy", "integer_exact") != "integer_exact"
        or r.get("solution_release", "after_submit") != "after_submit"
    ):
        raise HTTPException(
            400,
            "Unsupported profile policy. Current practice uses free navigation, exact integers and post-submission solutions.",
        )
    return {
        **r,
        "navigation": "free",
        "numeric_policy": "integer_exact",
        "solution_release": "after_submit",
        "numeric_rule": "Exact integer value; signs, Unicode minus and leading zeros accepted; up to 20 digits. No decimals or rounding.",
    }


def permitted(s, u=None, series_schedule=False):
    if s.get('series_date') and not series_schedule:
        from .live_series import window
        if now() < window(s['series_date'])['opens_at']:
            return False
    if (s.get('import_id') or s.get('chapter_book_id')) and (not s.get('live_enabled') or now() < s.get('start_at', float('inf')) or now() >= s.get('end_at', 0)):
        return False
    if (
        s.get("expires")
        and s["expires"] < datetime.now(timezone.utc).date().isoformat()
    ):
        return False
    if s.get("audience") == "restricted":
        return bool(
            u
            and (
                (u.get("email") and u["email"] in s.get("allowed_emails", []))
                or (u.get("phone") and u["phone"] in s.get("allowed_phones", []))
            )
        )
    return s.get('audience') == 'all'


def summary(s):
    qs = s.get("questions", [])
    return {
        **{
            k: s.get(k)
            for k in [
                "id",
                "title",
                "exam",
                "year",
                "status",
                "rules",
                "version",
                "source",
                "attribution",
                "created_at",
                "test_kind", "full_length", "mock_number", "series_id", "series_date",
                "chapter_book_id", "chapter_number", "chapter_subject", "solution_kind", "start_at", "end_at", "live_enabled",
            ]
        },
        "count": len(qs),
        "approved_count": sum(q.get("approved", False) for q in qs),
        "subjects": list(dict.fromkeys(q["subject"] for q in qs if q.get("subject"))),
        "types": {t: sum(q["type"] == t for q in qs) for t in ["mcq", "integer"]},
        "maximum": sum((q.get('scoring') or s['rules'])['correct'] for q in qs if q.get('disposition', 'standard') != 'dropped'),
    }


@router.get("/sets")
async def catalogue(exam: str = "", q: str = "", page: int = 1):
    from .catalog import available, counts, page as catalogue_page

    f = available(exam=exam, search=q)
    data = await catalogue_page(f, page)
    return {
        "items": [summary(s) for s in data],
        "page": page,
        "counts": await counts(f),
    }


@router.get("/sets/{id}")
async def set_detail(id: str):
    s = await get(sets, id)
    if s["status"] != "published" or not permitted(s):
        raise HTTPException(
            404, "This practice set is not available for public practice yet."
        )
    return summary(s)


@router.get("/studio/sets")
async def studio_sets(u=Depends(staff)):
    from .catalog import page

    return [summary(s) for s in await page({"qa_only": {"$ne": True}, 'import_id': {'$exists': False}, 'chapter_book_id': {'$exists': False}}, size=100)]


@router.post("/studio/sets")
async def create_set(data: SetInput, u=Depends(staff)):
    if data.audience not in ('all', 'restricted'):
        raise HTTPException(400, 'Select a supported audience.')
    if data.exam not in ["JEE Main", "BITSAT"]:
        raise HTTPException(400, "Choose JEE Main or BITSAT.")
    if data.profile_mode != "practice":
        raise HTTPException(
            400,
            "Official simulation profiles are not activated. Create a custom practice set.",
        )
    if "rules" not in data.model_fields_set and data.exam == "BITSAT":
        data.rules = {**data.rules, "correct": 3}
    r = valid_rules(data.rules)
    s = {
        **data.model_dump(),
        "id": uid(),
        "status": "draft",
        "version": 1,
        "revision": 1,
        "questions": [],
        "file_ids": [],
        "created_at": now(),
        "rules": r,
    }
    await sets.insert_one(s)
    await audit(u["id"], "Draft created", s["id"])
    return clean(s)


@router.get("/studio/sets/{id}")
async def studio_set(id: str, u=Depends(staff)):
    s = await get(sets, id)
    s["files"] = await files.find(
        {"id": {"$in": s.get("file_ids", [])}}, {"_id": 0, "path": 0}
    ).to_list(100)
    s["audit"] = (
        await audits.find({"resource": id}, {"_id": 0})
        .sort("at", -1)
        .limit(40)
        .to_list(40)
    )
    s["jobs"] = (
        await jobs.find({"set_id": id}, {"_id": 0, "path": 0})
        .sort("created_at", -1)
        .limit(10)
        .to_list(10)
    )
    return clean(s)


@router.put("/studio/sets/{id}")
async def update_set(id: str, data: SetInput, u=Depends(staff)):
    s = await get(sets, id)
    if data.exam not in ["JEE Main", "BITSAT"] or data.audience not in [
        "all",
        "restricted",
    ]:
        raise HTTPException(400, "Select a supported exam and audience.")
    if data.expires:
        try:
            datetime.strptime(data.expires, "%Y-%m-%d")
        except ValueError:
            raise HTTPException(400, "Expiry must be a date in YYYY-MM-DD format.")
    if s["status"] == "published" and not data.change_reason.strip():
        raise HTTPException(
            400,
            "Explain this correction. The set will return to review; existing attempts remain unchanged.",
        )
    if s.get("qa_only") and data.audience != "restricted":
        raise HTTPException(400, "QA-only content cannot be published to all students.")
    if data.profile_mode != "practice":
        raise HTTPException(400, "Only nonofficial practice profiles are available.")
    if data.allowed_phones:
        from .phone import normalize_phone

        data.allowed_phones = [normalize_phone(p) for p in data.allowed_phones]
    if data.expected_revision is not None and data.expected_revision != s['revision']:
        raise HTTPException(409, 'Another editor changed this set. Reload before saving.')
    fields = {**data.model_dump(exclude={'expected_revision'}), "rules": valid_rules(data.rules), "status": "draft"}
    changed = await sets.update_one({"id": id, 'revision': s['revision']}, {"$set": fields, "$inc": {"revision": 1}})
    if not changed.modified_count:
        raise HTTPException(409, 'Another editor changed this set. Reload before saving.')
    await audit(
        u["id"],
        "Set rules / rights updated",
        id,
        data.change_reason or "Draft settings saved",
    )
    return {"ok": True}


@router.post("/studio/sets/{id}/files")
async def upload(
    id: str, kind: str = Form(...), file: UploadFile = File(...), u=Depends(staff)
):
    require_capability(Capability.SOURCE_UPLOAD)
    s = await get(sets, id)
    if not s.get("rights_upload"):
        raise HTTPException(400, "Confirm permission to upload in set settings first.")
    if kind not in ["questions", "solutions", "key", "combined"]:
        raise HTTPException(400, "Choose a source document type.")
    data = await file.read(50 * 1024 * 1024 + 1)
    try:
        doc = await run_in_threadpool(validate_pdf, data)
    except ValueError as e:
        raise HTTPException(400, str(e))
    fid = uid()
    path = await run_in_threadpool(put_object, f"tejas/sources/{id}/{fid}.pdf", data)
    f = {
        "id": fid,
        "set_id": id,
        "kind": kind,
        "name": file.filename[:180],
        "pages": len(doc),
        "size": len(data),
        "sha256": hashlib.sha256(data).hexdigest(),
        "path": path,
        "created_at": now(),
    }
    await files.insert_one(f)
    await sets.update_one(
        {"id": id},
        {
            "$push": {"file_ids": fid},
            "$set": {"status": "draft"},
            "$inc": {"revision": 1},
        },
    )
    await audit(u["id"], "Private PDF uploaded", id, kind + ": " + f["name"])
    return {k: v for k, v in clean(f).items() if k != "path"}


@router.get("/studio/files/{id}/page/{page}")
async def source_page(id: str, page: int, u=Depends(staff)):
    require_capability(Capability.SOURCE_PARSE)
    f = await get(files, id)
    raw = await run_in_threadpool(get_object, f["path"])
    d = validate_pdf(raw)
    if not 1 <= page <= len(d):
        raise HTTPException(400, "Page does not exist.")
    p = d[page - 1]
    return Response(
        await run_in_threadpool(
            crop_png, raw, {"page": page, "rect": list(p.rect)}, 1.6
        ),
        media_type="image/png",
    )


@router.get("/studio/files/{id}/text/{page}")
async def source_text(id: str, page: int, u=Depends(staff)):
    require_capability(Capability.SOURCE_PARSE)
    f = await get(files, id)
    raw = await run_in_threadpool(get_object, f["path"])
    d = validate_pdf(raw)
    if not 1 <= page <= len(d):
        raise HTTPException(400, "Page does not exist.")
    return {
        "text": d[page - 1].get_text(),
        "width": d[page - 1].rect.width,
        "height": d[page - 1].rect.height,
    }


@router.get("/studio/files/{id}/download")
async def source_download(id: str, u=Depends(staff)):
    f = await get(files, id)
    return Response(
        await run_in_threadpool(get_object, f["path"]),
        media_type="application/pdf",
        headers={"Content-Disposition": 'attachment; filename="private-source.pdf"'},
    )


@router.post("/studio/sets/{id}/extract")
async def extract(id: str, data: dict, bg: BackgroundTasks, u=Depends(staff)):
    require_capability(Capability.EXTRACTION)
    s = await get(sets, id)
    if s.get("questions") and not data.get("replace_drafts"):
        raise HTTPException(
            409,
            "Extraction replaces draft edits. Confirm replacement or keep your existing questions.",
        )
    fs = await files.find({"set_id": id}, {"_id": 0}).to_list(100)
    qf = next((f for f in reversed(fs) if f["kind"] in ["questions", "combined"]), None)
    sf = next((f for f in reversed(fs) if f["kind"] in ["solutions", "combined"]), None)
    if not qf or not sf:
        raise HTTPException(
            400, "Upload questions and solutions, or a combined PDF, first."
        )
    from .jobs import enqueue, run_job

    j = await enqueue(
        "extract",
        u["id"],
        id,
        {
            "qfile": qf["id"],
            "sfile": sf["id"],
            "known_tejas": False,
            "revision": s["revision"],
        },
    )
    bg.add_task(run_job, j["id"])
    return j


def question_issues(q, exam):
    issues = []
    if q.get("type") not in ["mcq", "integer"] or (
        exam == "BITSAT" and q.get("type") != "mcq"
    ):
        issues.append("Unsupported response format for this exam")
    if not q.get("text", "").strip():
        issues.append("Question text is required")
    if not q.get("subject", "").strip():
        issues.append("Subject is required")
    if not q.get("solution", "").strip():
        issues.append("Matched solution is required")
    if not q.get("answer", "").strip():
        issues.append("Verified answer is required")
    elif q.get("type") == "mcq" and q["answer"] not in q.get("options", {}):
        issues.append("Answer must identify an existing option")
    elif q.get("type") == "integer":
        try:
            normalize_answer(q["answer"], "integer")
        except ValueError:
            issues.append("Integer key is invalid")
    if q.get("type") == "mcq" and (
        len(q.get("options", {})) < 2
        or any(not str(v).strip() for v in q.get("options", {}).values())
    ):
        issues.append("At least two complete options are required")
    if q.get("render_mode") == "source":
        generated = q.get('solution_kind') == 'ai_generated' and bool(q.get('ai_solution_id')) and bool(q.get('ai_provenance'))
        if not q.get("q_refs") or (not q.get("s_refs") and not generated):
            issues.append("Question and solution source regions are required")
        if (
            not q.get("accessible_text", "").strip()
            or not q.get("solution_accessible_text", "").strip()
        ):
            issues.append(
                "Reviewed accessible question and solution descriptions are required"
            )
    disposition = q.get("disposition", "standard")
    if disposition not in ["standard", "dropped", "bonus_all", "multiple_accepted"]:
        issues.append("Unresolved scoring disposition: keep under review")
    if disposition == "multiple_accepted":
        accepted = q.get("accepted_answers", [])
        if not isinstance(accepted, list) or not accepted:
            issues.append("Multiple-accepted policy needs verified accepted answers")
        else:
            for value in accepted:
                try:
                    normalized = normalize_answer(value, q.get("type"))
                    if not normalized or (
                        q.get("type") == "mcq"
                        and normalized not in q.get("options", {})
                    ):
                        raise ValueError()
                except ValueError:
                    issues.append("Invalid accepted answer in scoring policy")
    if not q.get("solution_number"):
        issues.append("Confirm the matched source solution number")
    return issues


async def validate_refs(s, q, source_map=None):
    from .derivatives import render_crop
    if source_map is None:
        source_map = {}
    for key in ["q_refs", "s_refs"]:
        for r in q.get(key, []):
            if r.get("file_id") not in s.get("file_ids", []):
                raise HTTPException(400, "Source region must belong to this set.")
            if r["file_id"] not in source_map:
                source_map[r["file_id"]] = await get(files, r["file_id"])
            f = source_map[r["file_id"]]
            try:
                await run_in_threadpool(render_crop, f, r, 0.3)
            except (ValueError, KeyError, TypeError):
                raise HTTPException(
                    400, "Source region is invalid. Check page and coordinates."
                )


@router.post("/studio/sets/{id}/questions")
async def add_question(id: str, u=Depends(staff)):
    s = await get(sets, id)
    q = {
        "id": uid(),
        "number": max([q["number"] for q in s["questions"]] + [0]) + 1,
        "solution_number": None,
        "subject": "",
        "section": "",
        "type": "mcq",
        "text": "",
        "options": {"1": "", "2": "", "3": "", "4": ""},
        "answer": "",
        "solution": "",
        "topic": "",
        "difficulty": "",
        "render_mode": "typed",
        "q_refs": [],
        "s_refs": [],
        "approved": False,
        "issues": [],
        "accessible_text": "",
        "solution_accessible_text": "",
        "review_note": "",
    }
    changed = await sets.update_one(
        {"id": id, 'revision': s['revision']},
        {
            "$push": {"questions": q},
            "$set": {"status": "draft"},
            "$inc": {"revision": 1},
        },
    )
    if not changed.modified_count:
        raise HTTPException(409, 'The draft changed. Reload before adding a question.')
    await audit(u["id"], "Question draft added", id)
    return q


@router.put("/studio/sets/{id}/questions/{qid}")
async def edit_question(id: str, qid: str, data: dict, u=Depends(staff)):
    s = await get(sets, id)
    old = next((q for q in s["questions"] if q["id"] == qid), None)
    if not old:
        raise HTTPException(404, "Question not found.")
    allowed = [
        "number",
        "solution_number",
        "subject",
        "section",
        "type",
        "text",
        "options",
        "answer",
        "solution",
        "topic",
        "difficulty",
        "render_mode",
        "q_refs",
        "s_refs",
        "accessible_text",
        "solution_accessible_text",
        "review_note",
        "disposition",
        "accepted_answers",
    ]
    q = {**old, **{k: v for k, v in data.items() if k in allowed}, "approved": False}
    if any(k in data and data[k] != old.get(k) for k in ('solution', 's_refs', 'solution_accessible_text')):
        if (q.get('solution') or '').strip() or q.get('s_refs') or (q.get('solution_accessible_text') or '').strip():
            q['solution_kind'] = 'owner_provided'
    if (
        not isinstance(q["number"], int)
        or q["number"] < 1
        or q.get("render_mode") not in ["source", "typed"]
    ):
        raise HTTPException(400, "Invalid question number or rendering mode.")
    for k in ["text", "solution", "accessible_text", "solution_accessible_text"]:
        if not isinstance(q.get(k, ""), str) or len(q.get(k, "")) > 30000:
            raise HTTPException(400, "Text is too long or invalid.")
    if not isinstance(q["options"], dict) or len(q["options"]) > 8:
        raise HTTPException(400, "Provide up to eight options.")
    await validate_refs(s, q)
    q["issues"] = question_issues(q, s["exam"])
    if s["status"] == "published" and not q["review_note"].strip():
        raise HTTPException(400, "A correction note is required for published content.")
    if data.get('expected_revision') is not None and data['expected_revision'] != s['revision']:
        raise HTTPException(409, 'The draft changed. Your edits were not overwritten; reload before saving.')
    changed = await sets.update_one(
        {"id": id, "questions.id": qid, 'revision': s['revision']},
        {"$set": {"questions.$": q, "status": "review"}, "$inc": {"revision": 1}},
    )
    if not changed.modified_count:
        raise HTTPException(409, 'The draft changed while saving. Reload and reconcile your edits.')
    await audit(u["id"], f"Q{q['number']} draft corrected", id, q["review_note"])
    return q


@router.post("/studio/sets/{id}/questions/{qid}/approve")
async def approve_question(id: str, qid: str, u=Depends(staff)):
    s = await get(sets, id)
    q = next((q for q in s["questions"] if q["id"] == qid), None)
    if not q:
        raise HTTPException(404, "Question not found.")
    issues = question_issues(q, s["exam"])
    if issues:
        raise HTTPException(400, "; ".join(issues))
    if q.get("render_mode") == "typed":
        from .reports import validate_typed_math

        try:
            await run_in_threadpool(validate_typed_math, q)
        except ValueError as exc:
            raise HTTPException(400, str(exc))
    await validate_refs(s, q)
    res = await sets.update_one(
        {"id": id, "questions.id": qid, "revision": s["revision"]},
        {
            "$set": {
                "questions.$.approved": True,
                "questions.$.approved_by": u["id"],
                "questions.$.approved_at": now(),
                "questions.$.issues": [],
            },
            "$inc": {"revision": 1},
        },
    )
    if not res.modified_count:
        raise HTTPException(
            409, "Content changed during approval. Reload and review the new version."
        )
    await audit(
        u["id"],
        f"Q{q['number']} approved",
        id,
        "Question, options, key, solution pairing, figures and accessible descriptions verified by reviewer",
    )
    return {"ok": True}


@router.post("/studio/sets/{id}/publish")
async def publish(id: str, data: dict, u=Depends(owner)):
    require_capability(Capability.PUBLICATION)
    return await publish_validated(id, data, u)


async def publish_validated(id, data, u):
    """Internal publication primitive; HTTP legacy gate remains unchanged."""
    s = await get(sets, id)
    if s.get('publication_pending'):
        await archive_publication(s)
        s.pop('publication_pending', None)
    if not data.get("confirm"):
        raise HTTPException(400, "Confirm publication for the specified audience.")
    if not all(
        s.get(k)
        for k in [
            "rights_upload",
            "rights_publish",
            "rights_report",
            "source",
            "attribution",
        ]
    ):
        raise HTTPException(
            400,
            "Source, attribution, upload, publication and personal-report permissions are required.",
        )
    if s.get("audience") == "restricted" and not (
        s.get("allowed_emails") or s.get("allowed_phones")
    ):
        raise HTTPException(400, "Add the permitted student email addresses.")
    if (
        s.get("expires")
        and s["expires"] < datetime.now(timezone.utc).date().isoformat()
    ):
        raise HTTPException(400, "Content permission has expired.")
    if not s["questions"] or any(
        not q.get("approved") or question_issues(q, s["exam"]) for q in s["questions"]
    ):
        raise HTTPException(
            400,
            "Every question needs complete content, a verified key, matched solution and reviewer approval.",
        )
    identities = [(q.get("section"), q["number"]) for q in s["questions"]]
    if len(set(identities)) != len(identities):
        raise HTTPException(
            400, "Duplicate section/question identities must be resolved."
        )
    from .profiles import seal_profile

    if s.get("qa_only") and s.get("audience") != "restricted":
        raise HTTPException(400, "QA content must remain restricted.")
    await seal_profile(s)
    for q in s["questions"]:
        await validate_refs(s, q)
    s['version'] = s.get('version', 0) + 1
    snapshot = {k: copy.deepcopy(v) for k, v in s.items() if k not in ('publication_pending', '_id')}
    snapshot.update(id=uid(), set_id=id, published_at=now(), status='published')
    from bson import BSON
    if len(BSON.encode({**s, 'publication_pending': snapshot})) > 14 * 1024 * 1024:
        raise HTTPException(413, 'This publication exceeds the safe snapshot size. Split the test.')
    res = await sets.update_one(
        {'id': id, 'revision': s['revision']},
        {'$set': {'status': 'published', 'version': s['version'],
                  'published_at': snapshot['published_at'], 'publication_pending': snapshot},
         '$inc': {'revision': 1}},
    )
    if not res.modified_count:
        raise HTTPException(409, 'Content changed during publication. Review it again.')
    # Only the CAS winner can archive. Its embedded outbox survives process failure.
    await archive_publication({'id': id, 'publication_pending': snapshot})
    await audit(
        u["id"],
        "Set published",
        id,
        f"Version {s['version']} | audience {s['audience']}",
    )
    return {"ok": True, "version": s["version"]}


async def archive_publication(s):
    """Idempotent archival of a winning, durably snapshotted publication only."""
    snapshot = s.get('publication_pending')
    if not snapshot:
        return
    await db.tejas_versions.update_one({'_id': snapshot['id']}, {'$setOnInsert': snapshot}, upsert=True)
    await sets.update_one({'id': s['id'], 'publication_pending.id': snapshot['id']}, {'$unset': {'publication_pending': ''}})


@router.post("/studio/sets/{id}/withdraw")
async def withdraw(id: str, data: dict, u=Depends(owner)):
    await get(sets, id)
    if not str(data.get("reason", "")).strip():
        raise HTTPException(400, "Enter a withdrawal reason.")
    await sets.update_one(
        {"id": id}, {"$set": {"status": "withdrawn"}, "$inc": {"revision": 1}}
    )
    await audit(u["id"], "Set withdrawn", id, data["reason"])
    return {"ok": True}


@router.post("/studio/sets/{id}/subset")
async def subset(id: str, data: dict, u=Depends(staff)):
    s = await get(sets, id)
    selected = set(data.get("question_ids", []))
    qs = [q for q in s["questions"] if q["id"] in selected]
    if not qs:
        raise HTTPException(400, "Select at least one question.")
    s.update(
        {
            "id": uid(),
            "title": str(data.get("title", "Revision set"))[:160],
            "questions": qs,
            "status": "draft",
            "version": 1,
            "revision": 1,
            "created_at": now(),
            "rules": {**s["rules"], "minutes": 0},
            "parent_set": id,
        }
    )
    # Keep source identity but explicitly link the same private source files to the derived set.
    await sets.insert_one(s)
    await audit(
        u["id"],
        "Revision set assembled",
        s["id"],
        f"From {id}; untimed; independent maximum marks",
    )
    return {"id": s["id"]}


@router.get("/studio/sets/{id}/questions/{qid}/asset/{kind}/{index}")
async def preview_asset(id: str, qid: str, kind: str, index: int, u=Depends(staff)):
    require_capability(Capability.SOURCE_PARSE)
    s = await get(sets, id)
    q = next((q for q in s["questions"] if q["id"] == qid), None)
    if not q or kind not in ["question", "solution"]:
        raise HTTPException(404, "Asset not found.")
    refs = q["q_refs" if kind == "question" else "s_refs"]
    if not 0 <= index < len(refs):
        raise HTTPException(404, "Source region not found.")
    ref = refs[index]
    f = await get(files, ref["file_id"])
    raw = await run_in_threadpool(get_object, f["path"])
    return Response(await run_in_threadpool(crop_png, raw, ref), media_type="image/png")
