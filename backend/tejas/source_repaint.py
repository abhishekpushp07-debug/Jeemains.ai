"""Pictures saved before the printed address ('Source: AITS Mock 04 / Q68') was hidden still show that line. Here the whole-question and
solution pictures of the tests made from PDFs are cut once more from the same PDF with the line painted out. A picture is switched only
when the new one differs from the saved one inside that line alone and the store gives the new one back byte for byte. The new picture is
saved beside the old one, in the same store; the old one is never removed or overwritten, and its place stays on the record.
A picture that cannot be proven stays as it is and is listed for the owner. One run at a time on every server; it carries on after a restart."""
import asyncio, hashlib, io, logging
from fastapi import APIRouter, Depends
from pymongo import ReturnDocument
from pymongo.errors import DuplicateKeyError
from starlette.concurrency import run_in_threadpool
import tejas_storage as store
from .auth import owner
from .db import db, sets, files, now, uid, audit
from .book_pdf import inspect_many
from .book_store import cached
from .png_small import shrink_many

router = APIRouter(prefix='/api/admin/pictures/source-line', tags=['Source line'])
log = logging.getLogger(__name__)
OP, LEASE, CHUNK, AT_ONCE = 'source-repaint', 600, 20, 3
KINDS = (('q_refs', 'sawaal'), ('s_refs', 'solution'))
BOOK_SETS = {'book_import_id': {'$type': 'string'}}
SAVED = {'kind': 'rendered_png', 'is_deleted': {'$ne': True}, 'path': {'$type': 'string', '$ne': ''}}
WAITS = {'source_mask.state': {'$nin': ['painted', 'none', 'cut']}}
ROW = {'_id': 0, 'id': 1, 'path': 1, 'sha256': 1, 'size': 1, 'book_import_id': 1, 'source_sha256': 1, 'original_page': 1, 'original_rect': 1}
SET = {'_id': 0, 'id': 1, 'title': 1, 'book_import_id': 1, 'test_kind': 1, 'master_pyq': 1, 'questions.number': 1,
       **{f'questions.{k}.file_id': 1 for k, _ in KINDS}}
KEPT = 'Picture jaisi thi waisi hi chal rahi hai.'
NO_PDF = 'Is test ki original PDF nahi mili ya padhi nahi ja saki. ' + KEPT
OTHER_PDF = 'Yeh picture kisi aur PDF se kati thi. ' + KEPT
CUT = 'PDF se yeh hissa dobara nahi kat saka. ' + KEPT
UNREAD = 'Purani picture storage se padhi nahi ja saki. ' + KEPT
CHANGED = 'Storage wali picture apne save hash se match nahi karti. ' + KEPT
DIFFERENT = "Nayi picture 'Source' line ke bahar bhi purani se alag nikli, isliye badli nahi. " + KEPT
OTHER_STORE = 'Yeh picture kisi aur bucket mein hai, isliye badli nahi. ' + KEPT
OTHER_PLACE = 'Yeh picture is upload ke apne folder mein nahi hai, isliye badli nahi. ' + KEPT
NOT_BACK = 'Storage ne nayi picture ke alag bytes lautaye, isliye switch nahi kiya. ' + KEPT
REFUSED = 'Storage ne nayi picture nahi li. ' + KEPT
RACE = 'Yeh picture isi beech badal gayi. “Line hatao” dobara dabane par phir koshish hogi.'
STOPPED = 'Kaam beech mein ruk gaya. ' + KEPT
_tasks = set()


def ops():
    return db.tejas_operations


def _ids(s):
    """file id -> where it is shown, for the whole-question and solution pictures of one test (never its cut pieces)."""
    out = {}
    for q in s.get('questions') or []:
        for key, word in KINDS:
            for r in q.get(key) or []:
                if r.get('file_id'):
                    out.setdefault(r['file_id'], f"{(s.get('title') or '')[:60]} · Q{q.get('number')} · {word}")
    return out


async def waiting():
    """How many saved pictures have not been looked at yet (or could not be proven last time)."""
    from .structure import locked
    ids = set()
    async for s in sets.find(BOOK_SETS, {k: v for k, v in SET.items() if k not in ('title', 'questions.number')}):
        if not locked(s):
            ids.update(_ids(s))
    return await files.count_documents({'id': {'$in': list(ids)}, **SAVED, **WAITS}) if ids else 0


def _read(path):
    """The saved picture straight from its store, never from this server's memory."""
    if path.startswith(store.SB):
        bucket, inner = path[len(store.SB):].split('/', 1)
        return store.sb_get(bucket, inner)
    return store.request('GET', path).content


def _only_line(old, new, boxes):
    """'' when the new picture differs from the saved one inside the painted line alone; 'same' when no pixel differs; else the reason."""
    import numpy as np
    from PIL import Image
    try:
        a, b = (np.asarray(Image.open(io.BytesIO(x)).convert('RGB')) for x in (old, new))
    except Exception:  # noqa: BLE001  not a readable picture: it is left alone
        return DIFFERENT
    if a.shape != b.shape:
        return DIFFERENT
    diff = (a != b).any(axis=2)
    if not diff.any():
        return 'same'
    for box in boxes:
        if len(box) == 4 and all(isinstance(v, int) for v in box):
            diff[max(0, box[1]):max(0, box[3]), max(0, box[0]):max(0, box[2])] = False
    return DIFFERENT if diff.any() else ''


def judge(row, crop):
    try:
        old = _read(row['path'])
    except store.StorageWaiting:
        raise
    except store.StorageError:
        return UNREAD
    if hashlib.sha256(old).hexdigest() != row.get('sha256'):
        return CHANGED
    return _only_line(old, crop['image_bytes'], crop.get('mask_boxes') or [])


def keep(row, png):
    """The new picture goes beside the old one, into the same store, and is read back. Returns its reference."""
    folder, old = f"jeelive/books/{row['book_import_id']}/crops/", row['path']
    name = f"{folder}{row['id']}.clean.png"
    if folder not in old:
        raise ValueError(OTHER_PLACE)   # the new picture must lie beside the old one, in the upload's own folder
    if old.startswith(store.SB):
        bucket = old[len(store.SB):].split('/', 1)[0]
        if not store.configured() or bucket != store.bucket_name():
            raise ValueError(OTHER_STORE)
        ref = store.put_object(name, png, 'image/png')
        back = store.sb_get(bucket, name)
    else:
        ref = store.request('PUT', name, png, 'image/png').json()['path']
        back = store.request('GET', ref).content
    if back != png:
        raise ValueError(NOT_BACK)
    return ref


def _away(exc):
    return isinstance(exc, store.StorageWaiting) and store.scope_of(exc) in ('away', 'blocked')


def _why(exc):
    if isinstance(exc, ValueError):
        return str(exc)[:240]
    if isinstance(exc, store.StorageWaiting):
        return f'Storage ne nayi picture nahi li. Wajah: {exc.reason or exc.raw or exc}. {KEPT}'[:240]
    if isinstance(exc, store.StorageError):
        return REFUSED
    log.warning('A picture could not be repainted; it is left as it is.', exc_info=exc)
    return STOPPED


async def _alive(token):
    return await ops().find_one_and_update({'_id': OP, 'lease': token, 'state': 'running'}, {'$set': {'lease_until': now() + LEASE}}, projection={'run': 1, 'skip': 1})


async def _mark(ids, run, state, reason=''):
    if ids:
        await files.update_many({'id': {'$in': ids}, 'source_mask.state': {'$ne': 'painted'}},
                                {'$set': {'source_mask': {'state': state, 'at': now(), 'run': run, **({'reason': reason} if reason else {})}}})


async def _tally(run, where, painted=0, clean=(), failed=()):
    """What one group came to: the pictures' own records first, then the run's counts and its list of pictures left as they are."""
    await _mark(list(clean), run, 'none')
    for reason in {why for _, why in failed if why != RACE}:
        await _mark([r['id'] for r, why in failed if why == reason], run, 'left', reason)
    change = {'$inc': {'painted': painted, 'painted_ever': painted, 'clean': len(clean), 'left': len(failed)}}
    if painted:
        change['$set'] = {'dirty': True}
    if failed:
        change['$push'] = {'failures': {'$each': [{'label': where.get(r['id'], ''), 'reason': why, 'at': now()} for r, why in failed], '$slice': -50}}
    await ops().update_one({'_id': OP, 'run': run}, change)


async def _pause(token, exc):
    await ops().update_one({'_id': OP, 'lease': token}, {'$set': {'state': 'waiting', 'lease': '', 'last_error': str(exc)[:300], 'waiting_since': now()}})
    return False


async def chunk(token, run, pdf, rows, where):
    """One group of pictures. False = the run stops here because Supabase is away; what was not done stays as it is and is done later."""
    try:
        crops = await run_in_threadpool(inspect_many, pdf, [{'action': 'crop', 'page': r.get('original_page'), 'rect': r.get('original_rect'), 'mask': 'source'} for r in rows], 10)
    except ValueError:
        await _tally(run, where, failed=[(r, CUT) for r in rows])
        return True
    gate = asyncio.Semaphore(AT_ONCE)

    async def each(fn, *args):
        async with gate:
            return await run_in_threadpool(fn, *args)
    clean, failed, pairs, good, away, painted = [], [], [], [], None, 0
    for r, c in zip(rows, crops):
        if c.get('error') or not c.get('image_bytes'):
            failed.append((r, CUT))
        elif not c.get('masked'):
            clean.append(r['id'])   # no printed address in this picture
        else:
            pairs.append((r, c))
    for (r, c), v in zip(pairs, await asyncio.gather(*(each(judge, r, c) for r, c in pairs), return_exceptions=True)):
        if isinstance(v, BaseException):
            away = v if _away(v) else away
            if not _away(v):
                failed.append((r, _why(v)))
        elif v == 'same':
            clean.append(r['id'])
        elif v:
            failed.append((r, v))
        else:
            good.append((r, c['image_bytes']))
    if good and not away:
        small = await run_in_threadpool(shrink_many, [png for _, png in good])
        for (r, _), png, ref in zip(good, small, await asyncio.gather(*(each(keep, r, png) for (r, _), png in zip(good, small)), return_exceptions=True)):
            if isinstance(ref, BaseException):
                away = ref if _away(ref) else away
                if not _away(ref):
                    failed.append((r, _why(ref)))
                continue
            was = {'path': r['path'], 'sha256': r['sha256'], **({'size': r['size']} if isinstance(r.get('size'), int) else {})}
            done = await files.update_one({'id': r['id'], 'path': r['path'], 'sha256': r['sha256'], 'source_mask.state': {'$ne': 'painted'}}, {'$set': {
                'path': ref, 'sha256': hashlib.sha256(png).hexdigest(), 'size': len(png), 'source_mask': {'state': 'painted', 'at': now(), 'run': run, 'from': was}}})
            if done.modified_count:
                painted += 1
            else:
                failed.append((r, RACE))
    await _tally(run, where, painted, clean, failed)
    return await _pause(token, away) if away else True


async def one_set(token, s, run):
    from .structure import locked
    where = {} if locked(s) else _ids(s)
    todo = {'$or': [{'source_mask': {'$exists': False}}, {'source_mask.state': 'left', 'source_mask.run': {'$ne': run}}]}
    rows = await files.find({'id': {'$in': list(where)}, **SAVED, **todo}, ROW).to_list(None) if where else []
    if not rows:
        return True
    await ops().update_one({'_id': OP, 'lease': token}, {'$set': {'current': {'label': (s.get('title') or '')[:80]}}})
    p = (await db.tejas_books.find_one({'_id': s['book_import_id']}, {'payload.sha256': 1, 'payload.size': 1, 'payload.source_path': 1}) or {}).get('payload') or {}
    if not (p.get('source_path') and p.get('sha256') and p.get('size')):
        await _tally(run, where, failed=[(r, NO_PDF) for r in rows])
        return True
    other = [r for r in rows if r.get('source_sha256') != p['sha256']]
    if other:
        await _tally(run, where, failed=[(r, OTHER_PDF) for r in other])
    rows = [{**r, 'book_import_id': s['book_import_id']} for r in rows if r.get('source_sha256') == p['sha256']]
    for i in range(0, len(rows), CHUNK):
        if not await _alive(token):
            return False
        try:
            pdf = await run_in_threadpool(cached, p['sha256'], p['size'], p['source_path'])
        except Exception as exc:  # noqa: BLE001  the PDF could not be had: Supabase away = wait; anything else = these pictures stay
            if _away(exc):
                return await _pause(token, exc)
            await _tally(run, where, failed=[(r, NO_PDF) for r in rows[i:]])
            return True
        if not await chunk(token, run, pdf, rows[i:i + CHUNK], where):
            return False
    return True


async def _told():
    """Pictures were switched: every server now forgets the parts and revisions it built from the old ones. Never raises."""
    try:
        if await ops().find_one({'_id': OP, 'dirty': True}, {'_id': 1}):
            from .pictures import EPOCH, epoch
            told = await ops().find_one_and_update({'_id': EPOCH}, {'$inc': {'n': 1}, '$set': {'at': now()}}, upsert=True, return_document=ReturnDocument.AFTER)
            await epoch(told['n'])
            await ops().update_one({'_id': OP}, {'$set': {'dirty': False}})  # last: a stop in between only tells once more
    except Exception:  # noqa: BLE001  the mark stays: the next test or the next run tells
        log.warning('The servers could not be told about the replaced pictures yet.', exc_info=True)


async def run(token):
    try:
        while True:
            op = await _alive(token)
            if not op:
                return
            s = await sets.find_one({**BOOK_SETS, 'id': {'$nin': op.get('skip') or []}}, SET)
            if not s:
                await ops().update_one({'_id': OP, 'lease': token}, {'$set': {'state': 'done', 'lease': '', 'current': None, 'finished_at': now()}})
                return
            try:
                if not await one_set(token, s, op['run']):
                    return
                note = {}
            except Exception:  # noqa: BLE001  one test's trouble stays with that test: its pictures stay as they are, the next test is done
                log.warning("The 'Source' line could not be painted out of the pictures of %s; they are left as they are.", s['id'], exc_info=True)
                note = {'failures': {'$each': [{'label': (s.get('title') or '')[:60], 'reason': STOPPED, 'at': now()}], '$slice': -50}}
            await ops().update_one({'_id': OP, 'lease': token}, {'$push': {'skip': s['id'], **note}, '$set': {'current': None}})
            await _told()  # a finished test is clean for its students at once, not at the end of the whole run
    except Exception:  # noqa: BLE001  the run ends here; its lease runs out and the next check carries on from the same place
        log.warning("Painting the 'Source' line out of older pictures stopped midway; it carries on later.", exc_info=True)
    finally:
        await _told()


async def begin(fresh):
    """Claims the single run (one at a time on every server) and starts it in the background. None = already running."""
    t, token = now(), uid()
    change = {'state': 'running', 'lease': token, 'lease_until': t + LEASE, 'updated_at': t, 'last_error': ''}
    if fresh:
        change.update(run=uid(), started_at=t, finished_at=None, painted=0, clean=0, left=0, failures=[], skip=[], current=None, total=await waiting())
    try:
        await ops().find_one_and_update({'_id': OP, '$or': [{'state': {'$ne': 'running'}}, {'lease_until': {'$lt': t}}]}, {'$set': change}, upsert=True)
    except DuplicateKeyError:
        return None
    task = asyncio.create_task(run(token))
    _tasks.add(task)
    task.add_done_callback(_tasks.discard)
    return token


async def resume():
    """Supabase is back, or the server restarted midway: the run carries on where it stopped. Never raises."""
    try:
        op = await ops().find_one({'_id': OP}, {'state': 1, 'lease_until': 1})
        if not op:
            return
        back = not store.configured() or store.supabase_on()
        if (op['state'] == 'waiting' and back) or (op['state'] == 'running' and op.get('lease_until', 0) < now()):
            await begin(False)
    except Exception:  # noqa: BLE001
        log.warning("Painting the 'Source' line out of older pictures could not be carried on; the next check tries.", exc_info=True)


async def view(op):
    state, done = op.get('state', 'idle'), op.get('painted', 0) + op.get('clean', 0) + op.get('left', 0)
    if state == 'running' and op.get('lease_until', 0) < now():
        state = 'interrupted'
    active = state in ('running', 'waiting')
    left = max(0, op.get('total', 0) - done) if active else await waiting()
    return {'state': state, 'waiting': left, 'total': op.get('total', 0), 'painted': op.get('painted', 0), 'clean': op.get('clean', 0), 'left': op.get('left', 0),
            'painted_ever': op.get('painted_ever', 0),
            'failures': [{'label': f.get('label', ''), 'reason': f.get('reason', '')} for f in (op.get('failures') or [])[-20:]],
            'current': (op.get('current') or {}).get('label') or '', 'started_at': op.get('started_at'), 'finished_at': op.get('finished_at'),
            'last_error': op.get('last_error', '')}


@router.get('/status')
async def status(u=Depends(owner)):
    return await view(await ops().find_one({'_id': OP}) or {})


@router.post('/start')
async def start(u=Depends(owner)):
    op = await ops().find_one({'_id': OP}, {'state': 1, 'lease_until': 1}) or {}
    if not (op.get('state') == 'running' and op.get('lease_until', 0) >= now()):
        fresh = op.get('state') not in ('waiting', 'running', 'stopped')
        if await begin(fresh) and fresh:
            await audit(u['id'], "Older pictures: 'Source' line repaint started", OP, 'Saved pictures are never removed; each switch is proven first.')
    return await status(u)


@router.post('/stop')
async def stop(u=Depends(owner)):
    """Stops after the pictures in hand; "Line hatao" carries on from there."""
    await ops().update_one({'_id': OP, 'state': {'$in': ['running', 'waiting']}}, {'$set': {'state': 'stopped', 'lease': '', 'updated_at': now()}})
    return await status(u)
