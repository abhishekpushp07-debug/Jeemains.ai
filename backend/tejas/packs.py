"""Content-addressed, immutable private question packs shared across attempts.
Students never receive this payload directly: delivered-question allowlists gate all reads.
"""

import asyncio, copy, json, zlib, hashlib, sys
from collections import OrderedDict
from dataclasses import dataclass
from pydantic import Field
from pymongo.errors import DuplicateKeyError
from starlette.concurrency import run_in_threadpool
from .db import db, now
from .documents import BaseDocument
from .canonical import CanonicalIntegrityError
from .runtime import PACK_CACHE_BYTES, PACK_MAX_BYTES


class FrozenPack(BaseDocument):
    schema_version: int = Field(alias='schema')
    payload: bytes
    sha256: str
    count: int
    raw_bytes: int = Field(alias='bytes')
    created_at: float


@dataclass(frozen=True)
class PackEntry:
    questions: list
    by_id: dict
    size: int


_cache = OrderedDict()
_CACHE_MAX_BYTES = PACK_CACHE_BYTES
_cache_bytes = 0
_loading = {}
_stats = {'hits': 0, 'misses': 0, 'coalesced': 0, 'loads': 0, 'evictions': 0}


def object_bytes(value, seen=None):
    seen = set() if seen is None else seen
    if id(value) in seen:
        return 0
    seen.add(id(value))
    size = sys.getsizeof(value)
    if isinstance(value, dict):
        size += sum(object_bytes(k, seen) + object_bytes(v, seen) for k, v in value.items())
    elif isinstance(value, (list, tuple)):
        size += sum(object_bytes(v, seen) for v in value)
    return size


def decode_pack(raw):
    questions = json.loads(raw)
    if not isinstance(questions, list) or any(not isinstance(q, dict) or not isinstance(q.get('id'), str) for q in questions):
        raise CanonicalIntegrityError('Frozen question pack has an invalid structure')
    by_id = {q['id']: q for q in questions}
    if len(by_id) != len(questions):
        raise CanonicalIntegrityError('Frozen question identities are ambiguous')
    return PackEntry(questions, by_id, object_bytes((questions, by_id)))


def remember(key, entry):
    global _cache_bytes
    if entry.size > _CACHE_MAX_BYTES:
        return
    if key in _cache:
        _cache_bytes -= _cache.pop(key).size
    _cache[key] = entry
    _cache_bytes += entry.size
    while _cache_bytes > _CACHE_MAX_BYTES and _cache:
        _, old = _cache.popitem(last=False)
        _cache_bytes -= old.size
        _stats['evictions'] += 1


def decode_stored(record, key):
    try:
        p = FrozenPack.from_mongo(record)
        if p.sha256 != key or p.raw_bytes > PACK_MAX_BYTES:
            raise ValueError()
        stream = zlib.decompressobj()
        raw = stream.decompress(p.payload, PACK_MAX_BYTES + 1)
        if len(raw) > PACK_MAX_BYTES or not stream.eof or stream.unused_data or len(raw) != p.raw_bytes:
            raise ValueError()
        if hashlib.sha256(raw).hexdigest() != key:
            raise ValueError()
        entry = decode_pack(raw)
        if len(entry.questions) != p.count:
            raise ValueError()
        return entry
    except (ValueError, TypeError, zlib.error, KeyError) as exc:
        raise CanonicalIntegrityError('Frozen content integrity check failed') from exc


async def load_entry(key, raw=None):
    if raw is not None:
        record = FrozenPack(id=key, schema=1, payload=zlib.compress(raw, 6), sha256=key,
                            count=len(json.loads(raw)), bytes=len(raw), created_at=now())
        try:
            inserted = await db.tejas_packs.update_one({'_id': key}, {'$setOnInsert': record.to_mongo()}, upsert=True)
        except DuplicateKeyError:
            inserted = None
        if inserted is not None and inserted.upserted_id is not None:
            entry = await run_in_threadpool(decode_pack, raw)
            remember(key, entry)
            _stats['loads'] += 1
            return entry
    record = await db.tejas_packs.find_one({'_id': key})
    if not record:
        raise CanonicalIntegrityError('Frozen content pack is missing; substitution is forbidden')
    entry = await run_in_threadpool(decode_stored, record, key)
    remember(key, entry)
    _stats['loads'] += 1
    return entry


async def entry_for(key, raw=None):
    if key in _cache:
        _stats['hits'] += 1
        _cache.move_to_end(key)
        return _cache[key]
    flight_key = (asyncio.get_running_loop(), key)
    task = _loading.get(flight_key)
    if task is None:
        _stats['misses'] += 1
        task = asyncio.create_task(load_entry(key, raw))
        _loading[flight_key] = task
        def completed(done):
            _loading.pop(flight_key, None)
            if not done.cancelled():
                done.exception()
        task.add_done_callback(completed)
    else:
        _stats['coalesced'] += 1
    return await asyncio.shield(task)


def cache_stats():
    return {**_stats, 'bytes': _cache_bytes, 'limit_bytes': _CACHE_MAX_BYTES,
            'entries': len(_cache), 'loading': len(_loading)}


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
                "source_option_labels", "source_warning", "source_evidence", "pairing_evidence",
            }
        }
        for q in questions
    ]
    raw = json.dumps(
        safe, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    ).encode()
    if len(raw) > PACK_MAX_BYTES:
        raise CanonicalIntegrityError('Frozen question pack exceeds the configured content budget')
    key = hashlib.sha256(raw).hexdigest()
    await entry_for(key, raw)
    return key


async def unpack(key):
    return copy.deepcopy((await entry_for(key)).questions)


async def question(key, qid):
    value = (await entry_for(key)).by_id.get(qid)
    return copy.deepcopy(value) if value is not None else None


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
    record = {k: v for k, v in a.items() if k not in ["questions", "_id", "_database_now"]}
    await attempts.insert_one(record)
