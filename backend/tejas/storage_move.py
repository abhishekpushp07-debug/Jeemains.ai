"""Old files from Emergent storage copied into Supabase, one at a time. A file switches to Supabase only after Supabase gives back
exactly the same bytes (same hash): the app sees the same picture, ETag and asset_revision and downloads nothing again.
The Emergent copy is never deleted. A file that cannot be copied keeps working from Emergent and is listed for the owner."""
import asyncio, hashlib
from anyio import from_thread
from fastapi import APIRouter, Depends, HTTPException
from pymongo import ReturnDocument
from pymongo.errors import DuplicateKeyError
from starlette.concurrency import run_in_threadpool
import tejas_storage as store
from .auth import owner
from .db import db, now, uid

router = APIRouter(prefix='/api/admin/storage/move', tags=['Storage move'])
OP, LEASE, BATCH = 'storage-move', 180, 20
PLAIN = {'$type': 'string', '$ne': '', '$not': {'$regex': '^sb://'}}
NAMES = {'files': 'Picture/PDF', 'books': 'Book ki original PDF', 'chapter_books': 'Chapter book PDF', 'imports': 'Import source'}
_tasks = set()


def ops():
    return db.tejas_operations


# (name, collection, id field, path field, hash field, title field)
def places():
    return (('files', db.tejas_files, 'id', 'path', 'sha256', 'filename'),
            ('books', db.tejas_books, '_id', 'payload.source_path', 'payload.sha256', 'payload.title'),
            ('chapter_books', db.tejas_chapter_books, 'id', 'source.path', 'source.sha256', 'title'))


def _get(doc, dotted):
    for part in dotted.split('.'):
        doc = (doc or {}).get(part) if isinstance(doc, dict) else None
    return doc


async def next_items(skip):
    """Up to BATCH files still on Emergent: (key, collection, filter, path field, moved field, old ref, hash, label)."""
    out = []
    for name, col, key, field, sha, title in places():
        async for d in col.find({field: PLAIN}, {key: 1, field: 1, sha: 1, title: 1}).limit(BATCH + len(skip)):
            k = f'{name}:{d[key]}'
            if k not in skip:
                out.append((k, col, {key: d[key], field: _get(d, field)}, field, field.rsplit('.', 1)[0] + '.moved_from' if '.' in field else 'moved_from',
                            _get(d, field), _get(d, sha), f"{NAMES[name]} · {(_get(d, title) or str(d[key])[:8])}"[:120]))
            if len(out) >= BATCH:
                return out
    async for d in db.tejas_imports.find({'sources': {'$elemMatch': {'path': PLAIN}}}, {'id': 1, 'title': 1, 'sources': 1}).limit(BATCH):
        for i, s in enumerate(d.get('sources') or []):
            k = f"imports:{d['id']}:{i}"
            if isinstance(s.get('path'), str) and s['path'] and not s['path'].startswith(store.SB) and k not in skip:
                f = f'sources.{i}.path'
                out.append((k, db.tejas_imports, {'id': d['id'], f: s['path']}, f, f'sources.{i}.moved_from', s['path'], s.get('sha256'), f"{NAMES['imports']} · {d.get('title', '')}"[:120]))
    return out[:BATCH]


async def remaining():
    counts = {name: await col.count_documents({field: PLAIN}) for name, col, _, field, _, _ in places()}
    counts['imports'] = await db.tejas_imports.count_documents({'sources': {'$elemMatch': {'path': PLAIN}}})
    return counts


def _kind(raw):
    return 'image/png' if raw[:4] == b'\x89PNG' else 'application/pdf' if raw[:5] == b'%PDF-' else 'application/octet-stream'


def copy(old, sha, resume, progress):
    """Emergent bytes -> Supabase -> read back. Returns the Supabase ref only when every byte came back the same."""
    raw = store.request('GET', old).content
    got = hashlib.sha256(raw).hexdigest()
    if sha and got != sha:
        raise ValueError('Emergent wali file ke bytes uske save hash se match nahi karte. Isliye copy nahi ki; file Emergent se hi chalti rahegi.')
    ref = store.put_object(old, raw, _kind(raw), resume, progress)
    bucket, path = ref[len(store.SB):].split('/', 1)
    if hashlib.sha256(store.sb_get(bucket, path)).hexdigest() != got:
        raise ValueError('Supabase ne alag bytes lautaye. Isliye switch nahi kiya; file Emergent se hi chalti rahegi.')
    return ref


async def _note(token, change):
    return await ops().update_one({'_id': OP, 'lease': token}, change)


async def one(token, item, op):
    key, col, match, field, moved, old, sha, label = item
    cur = op.get('current') or {}
    resume = cur.get('transfer') if cur.get('key') == key else None
    await _note(token, {'$set': {'current': {'key': key, 'label': label, 'transfer': resume}}})

    async def keep(info):
        await _note(token, {'$set': {'current.transfer': info}})

    def progress(info):  # a big PDF saves its place every 6 MB, so a later try carries on
        from_thread.run(keep, info)
    try:
        ref = await run_in_threadpool(copy, old, sha, resume, progress)
    except store.StorageWaiting as exc:
        await _note(token, {'$set': {'state': 'waiting', 'lease': '', 'last_error': str(exc)[:300], 'waiting_since': now()}})
        return False
    except Exception as exc:  # noqa: BLE001  this one file stays on Emergent and is listed; the rest carry on
        reason = str(exc)[:240] if isinstance(exc, (ValueError, store.StorageError)) else 'Copy beech mein ruk gayi.'
        await _note(token, {'$inc': {'failed': 1}, '$set': {'current': None},
                            '$push': {'skip': key, 'failures': {'$each': [{'label': label, 'reason': reason, 'at': now()}], '$slice': -50}}})
        return True
    done = await col.update_one(match, {'$set': {field: ref, moved: old}})
    await _note(token, {'$inc': {'moved' if done.modified_count else 'skipped': 1}, '$set': {'current': None}, **({} if done.modified_count else {'$push': {'skip': key}})})
    return True


async def run(token):
    while True:
        op = await ops().find_one_and_update({'_id': OP, 'lease': token, 'state': 'running'}, {'$set': {'lease_until': now() + LEASE, 'updated_at': now()}},
                                             return_document=ReturnDocument.AFTER)
        if not op:
            return
        items = await next_items(set(op.get('skip') or []))
        if not items:
            await _note(token, {'$set': {'state': 'done', 'lease': '', 'current': None, 'finished_at': now()}})
            return
        for item in items:
            if not await ops().find_one({'_id': OP, 'lease': token, 'state': 'running'}, {'_id': 1}):
                return
            if not await one(token, item, op):
                return
            op = await ops().find_one({'_id': OP}) or {}


async def begin(fresh):
    """Claims the single run (one at a time on every server) and starts it in the background. None = already running."""
    t, token = now(), uid()
    change = {'state': 'running', 'lease': token, 'lease_until': t + LEASE, 'updated_at': t, 'last_error': ''}
    if fresh:
        change.update(started_at=t, finished_at=None, moved=0, failed=0, skipped=0, failures=[], skip=[], current=None,
                      total=sum((await remaining()).values()))
    try:
        await ops().find_one_and_update({'_id': OP, '$or': [{'state': {'$ne': 'running'}}, {'lease_until': {'$lt': t}}]}, {'$set': change}, upsert=True)
    except DuplicateKeyError:
        return None
    task = asyncio.create_task(run(token))
    _tasks.add(task)
    task.add_done_callback(_tasks.discard)
    return token


async def resume():
    """Supabase is back, or the server restarted mid-copy: carry on where it stopped (nothing is copied twice)."""
    op = await ops().find_one({'_id': OP}, {'state': 1, 'lease_until': 1})
    if op and store.supabase_on() and (op['state'] == 'waiting' or (op['state'] == 'running' and op.get('lease_until', 0) < now())):
        await begin(False)


def view(op, left):
    cur = (op.get('current') or {})
    transfer = cur.get('transfer') or {}
    state = op.get('state', 'idle')
    if state == 'running' and op.get('lease_until', 0) < now():
        state = 'interrupted'
    return {'state': state, 'remaining': left, 'remaining_total': sum(left.values()), 'total': op.get('total', 0), 'moved': op.get('moved', 0),
            'failed': op.get('failed', 0), 'skipped': op.get('skipped', 0), 'failures': (op.get('failures') or [])[-20:],
            'current': {'label': cur.get('label', ''), 'sent': transfer.get('sent', 0), 'size': transfer.get('size', 0)} if cur else None,
            'started_at': op.get('started_at'), 'finished_at': op.get('finished_at'), 'updated_at': op.get('updated_at'),
            'last_error': op.get('last_error', ''), 'supabase_ready': store.configured() and store.supabase_on()}


@router.get('/status')
async def status(u=Depends(owner)):
    return view(await ops().find_one({'_id': OP}) or {}, await remaining())


@router.post('/start')
async def start(u=Depends(owner)):
    if not store.configured():
        raise HTTPException(409, 'Supabase set nahi hai, isliye purani files copy nahi ho sakti.')
    if not store.supabase_on():
        raise HTTPException(409, 'Supabase abhi jawab nahi de raha. Thodi der baad Copy dabaiye.')
    op = await ops().find_one({'_id': OP}, {'state': 1, 'lease_until': 1}) or {}
    if op.get('state') == 'running' and op.get('lease_until', 0) >= now():
        raise HTTPException(409, 'Copy pehle se chal rahi hai.')
    await begin(op.get('state') not in ('waiting', 'interrupted', 'running', 'stopped'))
    return await status(u)


@router.post('/stop')
async def stop(u=Depends(owner)):
    """Stops after the file in hand; Start carries on from there."""
    await ops().update_one({'_id': OP, 'state': {'$in': ['running', 'waiting']}}, {'$set': {'state': 'stopped', 'lease': '', 'updated_at': now()}})
    return await status(u)
