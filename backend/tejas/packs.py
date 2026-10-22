"""Content-addressed, immutable private question packs shared across attempts.
Students never receive this payload directly: delivered-question allowlists gate all reads.
"""

import json, zlib, hashlib
from collections import OrderedDict
from .db import db, now

_cache = OrderedDict()
_CACHE_MAX_BYTES = 32 * 1024 * 1024
_cache_bytes = 0


def remember(key, raw):
    global _cache_bytes
    if key in _cache:
        _cache_bytes -= len(_cache.pop(key))
    _cache[key] = raw
    _cache_bytes += len(raw)
    while _cache_bytes > _CACHE_MAX_BYTES and _cache:
        _, value = _cache.popitem(last=False)
        _cache_bytes -= len(value)


async def seal(questions):
    safe = [
        {
            k: v
            for k, v in q.items()
            if k
            in {
                "id",
                "number",
                "solution_number",
                "solution_kind",
                "ai_steps", "ai_solution_id", "ai_provenance", "scoring", "original_number", "bonus",
                "section",
                "subject",
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
                "approved",
                "issues",
                "accessible_text",
                "solution_accessible_text",
                "review_note",
                "approved_by",
                "approved_at",
                "disposition",
                "accepted_answers",
            }
        }
        for q in questions
    ]
    raw = json.dumps(
        safe, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    ).encode()
    key = hashlib.sha256(raw).hexdigest()
    await db.tejas_packs.update_one(
        {"_id": key},
        {
            "$setOnInsert": {
                "schema": 1,
                "payload": zlib.compress(raw, 6),
                "sha256": key,
                "count": len(safe),
                "bytes": len(raw),
                "created_at": now(),
            }
        },
        upsert=True,
    )
    remember(key, raw)
    return key


async def unpack(key):
    raw = _cache.get(key)
    if raw is None:
        p = await db.tejas_packs.find_one({"_id": key})
        if not p:
            raise RuntimeError(
                "Frozen content pack is missing; do not substitute new content."
            )
        raw = zlib.decompress(p["payload"])
        if hashlib.sha256(raw).hexdigest() != key:
            raise RuntimeError("Frozen content integrity check failed.")
        remember(key, raw)
    else:
        _cache.move_to_end(key)
    return json.loads(raw)


async def hydrate(a):
    if a and "questions" not in a and a.get("pack_id"):
        a["questions"] = await unpack(a["pack_id"])
    # Compatibility metadata derived only from the immutable source's explicit disclosure.
    # No stored pack, answer, rule, score or content hash is changed.
    for q in (a or {}).get('questions', []):
        text=q.get('solution','')
        if 'solution_kind' not in q and text.startswith('Supplied answer key: ') and text.endswith('This book does not contain a worked solution.'):
            q['solution_kind']='answer_key_only'
    return a


async def insert_attempt(a):
    from .db import attempts

    a["pack_id"] = await seal(a["questions"])
    a["count"] = len(a["questions"])
    from .learning_progress import family
    a['progress_family'] = family(a)
    a["response_schema"] = {
        q["id"]: {"type": q["type"], "options": list(q.get("options", {})), **({"bonus": True} if q.get("bonus") else {})}
        for q in a["questions"]
    }
    record = {k: v for k, v in a.items() if k not in ["questions", "_id"]}
    await attempts.insert_one(record)
