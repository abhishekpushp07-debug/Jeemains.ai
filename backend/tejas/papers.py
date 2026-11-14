"""Per-process cache of question-derived paper data keyed by (set id, revision, version).
Every question edit bumps the set revision with a CAS, so an entry can never serve edited questions.
Status, live windows and permissions are never cached: callers re-read the header on every request."""
import asyncio, json
from collections import OrderedDict
from dataclasses import dataclass, field
from fastapi import HTTPException
from .db import sets

HEADER = {'_id': 0, 'questions': 0}
_MAX = 24
_cache = OrderedDict()
_flights = {}


@dataclass
class Paper:
    questions: list
    refs: list
    pack_id: str | None = None
    response_schema: dict | None = None
    public: list | None = None
    profile: dict | None = None
    validated: bool = False
    lock: asyncio.Lock = field(default_factory=asyncio.Lock)

    @property
    def count(self):
        return len(self.questions)


def unique_refs(questions):
    seen, out = set(), []
    for q in questions:
        for kind in ('q_refs', 's_refs'):
            for ref in q.get(kind, []):
                identity = json.dumps(ref, sort_keys=True, separators=(',', ':'))
                if identity not in seen:
                    seen.add(identity)
                    out.append(ref)
    return out


async def load(header):
    doc = await sets.find_one({'id': header['id'], 'revision': header['revision']}, {'_id': 0, 'questions': 1})
    if doc is None:
        raise HTTPException(409, 'This test was updated a moment ago. Reload and try again; no timer has started.')
    questions = doc.get('questions', [])
    for q in questions:
        q.pop('ai_solution', None)
    return Paper(questions, unique_refs(questions))


async def paper(header):
    key = (header['id'], header['revision'], header.get('version'))
    hit = _cache.get(key)
    if hit is not None:
        _cache.move_to_end(key)
        return hit
    task = _flights.get(key)
    if task is None:
        task = asyncio.ensure_future(load(header))
        _flights[key] = task
        task.add_done_callback(lambda done, k=key: _flights.pop(k, None))
    entry = await asyncio.shield(task)
    _cache[key] = entry
    _cache.move_to_end(key)
    while len(_cache) > _MAX:
        _cache.popitem(last=False)
    return entry


async def start_data(entry, s, deliver):
    """Seal the shared pack/profile once per paper revision instead of once per student."""
    if entry.pack_id is None:
        async with entry.lock:
            if entry.pack_id is None:
                from .packs import seal
                from .profiles import seal_profile
                profile = await seal_profile({**s, 'questions': entry.questions})
                entry.response_schema = {q['id']: {'type': q['type'], 'options': list(q.get('options', {})), **({'bonus': True} if q.get('bonus') else {})}
                                         for q in entry.questions}
                entry.public = [deliver(q) for q in entry.questions]
                entry.profile = profile
                entry.pack_id = await seal(entry.questions)
    return entry
