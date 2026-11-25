"""Proof that every picture of a paper exists, all in one store, before students can see the paper (Live or Scheduled).
Supabase: each picture is in Supabase's own list of its folder, with the size noted when it was saved. Emergent storage has no list:
each picture is read back and its fingerprint compared. The full check reads every picture back from either store.
The proof itself only reads: nothing is saved, copied or removed here. Verified JEE Main PYQ papers are never checked."""
import asyncio, hashlib, logging
from starlette.concurrency import run_in_threadpool
import tejas_storage as store
from .db import db, files, now

KINDS = ('q_refs', 's_refs', 'c_refs')
READS, GIVE_UP = 8, 8
GONE, CHANGED = ('missing', 'record'), ('size', 'bytes')
PROOF_TEXT = 'Is paper ki pictures storage mein saabit nahi hui, isliye yeh Live nahi hua. Baaki kaam chal raha hai.'


def picture_ids(s):
    return list(dict.fromkeys(r['file_id'] for q in s.get('questions') or [] for k in KINDS for r in q.get(k) or [] if r.get('file_id')))


def _place(path):
    """(bucket, folder, name) of a file saved in Supabase."""
    bucket, inner = path[len(store.SB):].split('/', 1)
    folder, _, name = inner.rpartition('/')
    return bucket, folder, name


def _differs(f, raw):
    return (isinstance(f.get('size'), int) and f['size'] != len(raw)) or (bool(f.get('sha256')) and hashlib.sha256(raw).hexdigest() != f['sha256'])


def _read_supabase(f):
    bucket, inner = f['path'][len(store.SB):].split('/', 1)
    try:
        raw = store.sb_get(bucket, inner)
    except store.StorageWaiting:
        raise   # Supabase itself is away: nothing can be said about this picture
    except store.StorageError:
        return 'unread'
    return 'bytes' if _differs(f, raw) else ''


def _read_emergent(f):
    store._quick.on = True   # two tries, as the storage check does: a picture that does not come back is named, not waited for
    try:
        raw = store.request('GET', f['path']).content
    except store.StorageError:
        return 'unread'
    finally:
        store._quick.on = False
    return 'bytes' if _differs(f, raw) else ''


async def _read_all(rows, reader, alive=None):
    """Reads pictures back, 8 at a time, never from this server's memory. When the first 8 all fail, the rest are not waited for."""
    gate, seen = asyncio.Semaphore(READS), {'ok': 0, 'failed': 0, 'away': None}

    async def one(f):
        async with gate:
            if seen['away']:
                return f['id'], ''
            if seen['failed'] >= GIVE_UP and not seen['ok']:
                return f['id'], 'unread'
            try:
                why = await run_in_threadpool(reader, f)
            except store.StorageWaiting as exc:
                seen['away'] = exc
                return f['id'], ''
            seen['failed' if why == 'unread' else 'ok'] += 1
            if alive:
                alive()
            return f['id'], why
    found = await asyncio.gather(*(one(f) for f in rows))
    if seen['away']:
        raise seen['away']
    return {fid: why for fid, why in found if why}


def _reason(bad, stores):
    def line(kinds, text):
        n = sum(1 for why in bad.values() if why in kinds)
        return f"{n} picture{'s' if n != 1 else ''} {text}" if n else ''
    parts = [line(GONE, 'storage me nahi mili'), line(CHANGED, 'storage me badli hui mili (size ya fingerprint alag)'), line(('unread',), 'storage se wapas padhi nahi ja saki')]
    if stores['supabase'] and stores['emergent']:
        parts.append(f"Pictures do storage me bati hain ({stores['supabase']} Supabase me, {stores['emergent']} Emergent me)")
    return '; '.join(p for p in parts if p)


async def prove(s, full=False, alive=None):
    """None for a verified JEE Main PYQ paper. Otherwise what was found; ok only when every picture is proven and all are in one store.
    Raises StorageError when Supabase itself cannot answer (away, or the project blocked): then nothing can be said about any picture."""
    from .structure import locked
    if locked(s):
        return None
    ids = picture_ids(s)
    rows = await files.find({'id': {'$in': ids}, 'path': {'$type': 'string', '$ne': ''}}, {'_id': 0, 'id': 1, 'path': 1, 'sha256': 1, 'size': 1}).to_list(None) if ids else []
    known = {f['id'] for f in rows}
    bad = {fid: 'record' for fid in ids if fid not in known}
    in_supabase = [f for f in rows if f['path'].startswith(store.SB)]
    in_emergent = [f for f in rows if not f['path'].startswith(store.SB)]
    folders, listed = {}, []
    for f in in_supabase:
        bucket, folder, name = _place(f['path'])
        folders.setdefault((bucket, folder), []).append((f, name))
    for (bucket, folder), items in folders.items():
        there = dict((await run_in_threadpool(store.sb_list, folder, bucket))[0])
        if alive:
            alive()
        for f, name in items:
            if name not in there:
                bad[f['id']] = 'missing'
            elif isinstance(f.get('size'), int) and isinstance(there[name], int) and there[name] != f['size']:
                bad[f['id']] = 'size'
            else:
                listed.append(f)
    if full:
        bad.update(await _read_all(listed, _read_supabase, alive))
    bad.update(await _read_all(in_emergent, _read_emergent, alive))
    stores = {'supabase': len(in_supabase), 'emergent': len(in_emergent)}
    mixed = bool(stores['supabase'] and stores['emergent'])
    return {'ok': not bad and not mixed, 'store': 'mixed' if mixed else 'supabase' if in_supabase else 'emergent' if in_emergent else '',
            'total': len(ids), 'proven': len(ids) - len(bad), 'stores': stores, 'bad': bad, 'reason': _reason(bad, stores), 'full': full}


# ---------- What the caller that makes a paper Live does with the proof ----------
def _only_this_paper(text, code, raw, said):
    out = store._wait(store.StorageStuck, text, code, 'stuck', raw, said)
    out.proof = True   # the paper's row says "pictures not proven", not "a picture does not go into Supabase"
    return out


def cannot_say(exc):
    """Supabase could not answer the proof's question. Away or blocked: the work waits for Supabase like any other (the proof does not
    rest Supabase for everyone). Any other answer: only this paper waits."""
    code, scope, raw = getattr(exc, 'code', None), store.scope_of(exc), str(exc)[:200]
    if scope in ('away', 'blocked'):
        return store._wait(store.StorageWaiting, f'{store.WAIT_TEXT} Wajah: {raw}', code, scope, raw)
    return _only_this_paper(f'{PROOF_TEXT} Wajah: {raw}', code, raw, 'Supabase ne is paper ki pictures ki list nahi di' + (f' ({code})' if code else ''))


def unproven(proof):
    """The paper stays Draft and only it waits ("Atki hai"): the reason, a try every 15 minutes, Dobara chalao."""
    return _only_this_paper(f"{PROOF_TEXT} Wajah: {proof['reason']}", None, proof['reason'], proof['reason'])


async def checked(s, alive=None, full=False):
    """prove(), with Supabase's own trouble turned into the wait the workers already understand."""
    try:
        return await prove(s, full, alive)
    except store.StorageWaiting:
        raise
    except store.StorageError as exc:
        raise cannot_say(exc) from None


async def remember(set_id, proof):
    """What the proof found, kept beside the test for its row in Super Admin. Never raises: a note must not stop a paper."""
    try:
        await db.tejas_picture_proofs.update_one({'_id': set_id}, {'$set': {**{k: proof[k] for k in ('ok', 'store', 'total', 'proven', 'reason', 'full')}, 'at': now()}}, upsert=True)
    except Exception:  # noqa: BLE001
        logging.getLogger(__name__).warning('The picture proof of %s could not be noted.', set_id, exc_info=True)
