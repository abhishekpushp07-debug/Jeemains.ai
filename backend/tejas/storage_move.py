"""Old files from Emergent storage copied into Supabase, one at a time. A file switches to Supabase only after Supabase gives back
exactly the same bytes (same hash): the app sees the same picture, ETag and asset_revision and downloads nothing again.
The Emergent copy is never deleted. A file that cannot be copied keeps working from Emergent and is listed for the owner."""
import asyncio, hashlib
from anyio import from_thread
from fastapi import APIRouter, Depends, HTTPException
from pymongo.errors import DuplicateKeyError
from starlette.concurrency import run_in_threadpool
import tejas_storage as store
from .auth import owner
from .db import db, now, uid

router = APIRouter(prefix='/api/admin/storage/move', tags=['Storage move'])
OP, LEASE, BATCH = 'storage-move', 180, 20
PLAIN = {'$type': 'string', '$ne': '', '$not': {'$regex': '^sb://'}}
NAMES = {'files': 'Picture/PDF', 'books': 'Book ki original PDF', 'chapter_books': 'Chapter book PDF', 'imports': 'Import source'}
NOT_ON_EMERGENT = 'Emergent mein yeh file nahi mili ya padhi nahi ja saki. Reference jaisa tha waisa hai; Copy dobara dabane par phir koshish hogi.'
_tasks = set()


def ops():
    return db.tejas_operations


def unlocked(t):
    # A book a worker holds right now waits for a later run: the worker's save would put the old path back.
    return {'lock_until': {'$not': {'$gt': t}}}


# (name, collection, id field, path field, hash field, title field)
def places():
    return (('files', db.tejas_files, 'id', 'path', 'sha256', 'filename'),
            ('books', db.tejas_books, '_id', 'payload.source_path', 'payload.sha256', 'payload.title'),
            ('chapter_books', db.tejas_chapter_books, 'id', 'source.path', 'source.sha256', 'title'))


def _get(doc, dotted):
    for part in dotted.split('.'):
        doc = doc.get(part) if isinstance(doc, dict) else None
    return doc


def _moved(field):
    return field.rsplit('.', 1)[0] + '.moved_from' if '.' in field else 'moved_from'


async def next_items(skip):
    """Up to BATCH files still on Emergent that this run has not tried yet."""
    out, t = [], now()
    for name, col, key, field, sha, title in places():
        tried = [k.split(':', 1)[1] for k in skip if k.startswith(name + ':')]
        query = {field: PLAIN, **({key: {'$nin': tried}} if tried else {}), **(unlocked(t) if name == 'books' else {})}
        async for d in col.find(query, {key: 1, field: 1, sha: 1, title: 1}).limit(BATCH - len(out)):
            out.append({'key': f'{name}:{d[key]}', 'name': name, 'col': col, 'id': (key, d[key]), 'field': field, 'sha_field': sha, 'old': _get(d, field),
                        'sha': _get(d, sha), 'label': f"{NAMES[name]} · {_get(d, title) or str(d[key])[:8]}"[:120]})
        if len(out) >= BATCH:
            return out
    tried = sum(1 for k in skip if k.startswith('imports:'))
    async for d in db.tejas_imports.find({'sources': {'$elemMatch': {'path': PLAIN}}}, {'id': 1, 'title': 1, 'sources': 1}).limit(BATCH + tried):
        for i, s in enumerate(d.get('sources') or []):
            k = f"imports:{d['id']}:{i}"
            if isinstance(s.get('path'), str) and s['path'] and not s['path'].startswith(store.SB) and k not in skip:
                out.append({'key': k, 'name': 'imports', 'col': db.tejas_imports, 'id': ('id', d['id']), 'field': f'sources.{i}.path', 'sha_field': f'sources.{i}.sha256',
                            'old': s['path'], 'sha': s.get('sha256'), 'label': f"{NAMES['imports']} · {d.get('title', '')}"[:120]})
    return out[:BATCH]


async def remaining():
    counts = {name: await col.count_documents({field: PLAIN}) for name, col, _, field, _, _ in places()}
    plain = {'$and': [{'$eq': [{'$type': '$$s.path'}, 'string']}, {'$ne': ['$$s.path', '']}, {'$ne': [{'$substrCP': ['$$s.path', 0, 5]}, store.SB]}]}
    rows = await db.tejas_imports.aggregate([{'$match': {'sources': {'$elemMatch': {'path': PLAIN}}}},
                                              {'$group': {'_id': None, 'n': {'$sum': {'$size': {'$filter': {'input': '$sources', 'as': 's', 'cond': plain}}}}}}]).to_list(1)
    counts['imports'] = rows[0]['n'] if rows else 0  # every old source file, not every import
    return counts


def _kind(raw):
    if raw[:4] == b'\x89PNG':
        return 'image/png'
    if raw[:3] == b'\xff\xd8\xff':
        return 'image/jpeg'
    if raw[:4] == b'RIFF' and raw[8:12] == b'WEBP':
        return 'image/webp'
    return 'application/pdf' if raw[:5] == b'%PDF-' else 'application/octet-stream'


def copy(old, sha, resume, progress):
    """Emergent bytes -> Supabase -> read back. Returns the Supabase ref only when every byte came back the same."""
    try:
        raw = store.request('GET', old).content
    except store.StorageError:
        raise ValueError(NOT_ON_EMERGENT) from None
    got = hashlib.sha256(raw).hexdigest()
    if sha and got != sha:
        raise ValueError('Emergent wali file ke bytes uske save hash se match nahi karte. Isliye copy nahi ki; file Emergent se hi chalti rahegi.')
    ref = store.put_object(old, raw, _kind(raw), resume, progress)
    bucket, path = ref[len(store.SB):].split('/', 1)
    try:
        back = store.sb_get(bucket, path)
    except store.StorageWaiting:
        raise
    except store.StorageError:
        raise ValueError('Supabase se copy wapas padhi nahi ja saki. Isliye switch nahi kiya; file Emergent se hi chalti rahegi.') from None
    if hashlib.sha256(back).hexdigest() != got:
        raise ValueError('Supabase ne alag bytes lautaye. Isliye switch nahi kiya; file Emergent se hi chalti rahegi.')
    return ref


async def _note(token, change):
    return await ops().update_one({'_id': OP, 'lease': token}, change)


async def one(token, item, op):
    """Copies one file. False = stop the run here (Supabase away, or the project blocked).
    A file that Supabase alone returns is tried on both routes, then listed with the reason; it stays on Emergent and the rest carry on."""
    cur = op.get('current') or {}
    place = {'at': cur.get('transfer') if cur.get('key') == item['key'] else None}
    await _note(token, {'$set': {'current': {'key': item['key'], 'label': item['label'], 'transfer': place['at']}, 'lease_until': now() + LEASE}})

    async def keep(info):
        await _note(token, {'$set': {'current.transfer': info, 'lease_until': now() + LEASE}})

    def progress(info):  # a big PDF saves its place every 6 MB (and keeps the run's lease), so a later try carries on
        place['at'] = info
        from_thread.run(keep, info)
    reason = None
    for _ in range(store.STALL_LIMIT + 1):
        try:
            ref = await run_in_threadpool(copy, item['old'], item['sha'], place['at'], progress)
            reason = None
            break
        except store.StorageWaiting as exc:
            if exc.scope not in ('file', 'stuck'):
                await _note(token, {'$set': {'state': 'waiting', 'lease': '', 'last_error': str(exc)[:300], 'waiting_since': now()}})
                return False
            reason = f'Supabase ne yeh file nahi li. Wajah: {exc.reason}. File Emergent se hi chalti rahegi; Copy dobara dabane par phir koshish hogi.'[:240]
            if exc.scope == 'stuck':
                break
        except Exception as exc:  # noqa: BLE001  this one file stays on Emergent and is listed; the rest carry on
            reason = ('Supabase ne yeh file nahi li (size ya type ki rok). File Emergent se hi chalti rahegi.' if isinstance(exc, store.SupabaseRefused) else
                      str(exc)[:240] if isinstance(exc, ValueError) else 'Copy beech mein ruk gayi. File Emergent se hi chalti rahegi.')
            break
    if reason:
        await _note(token, {'$inc': {'failed': 1}, '$set': {'current': None},
                            '$push': {'skip': item['key'], 'failures': {'$each': [{'label': item['label'], 'reason': reason, 'at': now()}], '$slice': -50}}})
        return True
    key, value = item['id']
    match = {key: value, item['field']: item['old'], **({item['sha_field']: item['sha']} if item['sha'] else {}), **(unlocked(now()) if item['name'] == 'books' else {})}
    done = await item['col'].update_one(match, {'$set': {item['field']: ref, _moved(item['field']): item['old']}})
    await _note(token, {'$inc': {'moved' if done.modified_count else 'skipped': 1}, '$set': {'current': None}, '$push': {'skip': item['key']}})
    return True


async def run(token):
    while True:
        op = await ops().find_one({'_id': OP, 'lease': token, 'state': 'running'})
        if not op:
            return
        items = await next_items(set(op.get('skip') or []))
        if not items:
            await _note(token, {'$set': {'state': 'done', 'lease': '', 'current': None, 'finished_at': now()}})
            return
        for item in items:
            op = await ops().find_one({'_id': OP, 'lease': token, 'state': 'running'})
            if not op or not await one(token, item, op):
                return


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
    """Supabase is back, or the server restarted mid-copy: carry on where it stopped (a copied file is never copied again)."""
    op = await ops().find_one({'_id': OP}, {'state': 1, 'lease_until': 1})
    if op and store.supabase_on() and (op['state'] == 'waiting' or (op['state'] == 'running' and op.get('lease_until', 0) < now())):
        await begin(False)


def view(op, left):
    cur = op.get('current') or {}
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
    from .storage_health import check_now
    if (await check_now())['mode'] not in ('supabase', 'slow'):
        raise HTTPException(409, 'Supabase abhi jawab nahi de raha. Thodi der baad Copy dabaiye.')
    op = await ops().find_one({'_id': OP}, {'state': 1, 'lease_until': 1}) or {}
    if op.get('state') == 'running' and op.get('lease_until', 0) >= now():
        return await status(u)  # already copying (a healthy check may just have resumed it)
    await begin(op.get('state') not in ('waiting', 'running', 'stopped'))
    return await status(u)


@router.post('/stop')
async def stop(u=Depends(owner)):
    """Stops after the file in hand; Copy carries on from there."""
    await ops().update_one({'_id': OP, 'state': {'$in': ['running', 'waiting']}}, {'$set': {'state': 'stopped', 'lease': '', 'updated_at': now()}})
    return await status(u)
