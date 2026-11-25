"""Storage health for Super Admin. What is known about the stores is ONE record in the database, so every server shows the same:
Supabase's small-file route (pictures), Supabase's big-file route (PDFs), Emergent storage (fallback), the last 20 failures and
the last 20 check timings of each store. The storage code only notes what happened; this module writes the notes down."""
import asyncio, hashlib, logging, re, statistics, time
from fastapi import APIRouter, Depends, HTTPException, Query
from pymongo.errors import DuplicateKeyError
from starlette.concurrency import run_in_threadpool
import tejas_storage as store
from .auth import owner
from .db import db

router = APIRouter(prefix="/api/admin/storage", tags=["Storage health"])
log = logging.getLogger(__name__)
FRESH, SLOW_MS, ALERT_AFTER = 60, 5000, 600   # a healthy check (new file written, read back) was measured at 1.7 to 3.1 s; 5 s is slow
HELD, KEEP, BIG_EVERY, BIG_AGAIN, WATCH = 600, 20, 86400, 900, 30
BIG_LEASE, BIG_ANSWER = 600, 45   # a big-file test may take minutes on a bad line; the button gets its answer within 45 s either way
ID = 'state'
CHECK_FILE, BIG_FILE = 'Jaanch file', 'Badi test file (7 MB)'
NOT_SET = 'Supabase set nahi hai. Nayi files Emergent storage mein save ho rahi hain.'
GREEN = 'Supabase ke dono raaste theek hain aur koi file ruki nahi hai.'
BOOK = re.compile(r'(?:^|/)jeelive/books/([0-9a-f-]{36})/(.+)$')
KINDS = (('tejas/reports/', 'Report PDF'), ('tejas/imports/', 'Paper upload ki file'), ('tejas/chapter-books/', 'Chapter book PDF'), ('tejas/sources/', 'Source PDF'),
         ('jeelive/written/', 'Likhe hue sawaal ki picture'), ('jeemains/smart/', 'Smart import ki file'))
_running = {'check': None, 'flush': None}
_tasks = set()
_mem = {'ok_at': 0.0, 'loop': None}


def col():
    return db.tejas_storage_state


async def record():
    doc = await col().find_one({'_id': ID})
    if doc is None:
        try:
            await col().insert_one({'_id': ID, 'rev': 0})
        except DuplicateKeyError:
            pass
        doc = await col().find_one({'_id': ID})
    return doc


# ---------- Writing down what the storage code noted ----------
async def labels(events):
    """For each failed file: a plain name (the upload's title and what the file is) and a private group, so the same failure of the
    many files of one upload is one line with a count. No storage path leaves the server."""
    hits = {e['path']: BOOK.search(e['path']) for e in events if e['kind'] == 'error' and e.get('path')}
    ids = list({m[1] for m in hits.values() if m})
    titles = {b['_id']: (b.get('payload') or {}).get('title', '') async for b in db.tejas_books.find({'_id': {'$in': ids}}, {'payload.title': 1})} if ids else {}
    out = {}
    for path, m in hits.items():
        if m:
            what = 'original PDF' if m[2] == 'original.pdf' else 'picture' if m[2].startswith('crops/') else 'file'
            name = f"{(titles.get(m[1]) or 'Hataya gaya upload')[:80]} · {what}"
        else:
            what, name = '', next((n for start, n in KINDS if start in path), 'File')
        out[path] = (name, hashlib.sha1(('/'.join(path.split('/')[:3]) + '|' + what).encode()).hexdigest()[:12])
    return out


def why(s, big=False):
    """One plain line for a route that failed."""
    if s.get('said'):
        return s['said']
    code, scope = s.get('code'), s.get('scope') or 'away'
    if scope in ('away', 'blocked') or big:
        return store.explain(code, scope if scope in ('away', 'blocked') else 'file')[0]
    return 'Supabase ne jaanch file nahi li' + (f' ({code})' if code else '')


def said(e):
    """The reason of one failed real file."""
    if e.get('reason'):
        return e['reason']
    raw = e.get('raw') or ''
    code = (re.search(r'\((\d{3})\)', raw) or [None, ''])[1]
    tail = f' ({code})' if code else ''
    if e['store'] == 'emergent':
        return {'save': 'Emergent storage ne file save nahi ki', 'check': 'Emergent storage ne jaanch file nahi li ya nahi lautayi'}.get(e['route'], 'Emergent storage ne file nahi di') + tail
    if e['route'] == 'read':
        return ('Supabase mein yeh file nahi mili' if code in ('400', '404') else 'Supabase ne file nahi di') + tail
    return raw


def merge(doc, events, names):
    """The record after these notes, oldest first. A note older than what the record knows about a route does not change it."""
    small, big, em = (dict(doc.get(k) or {}) for k in ('small', 'big', 'emergent'))
    errors = list(doc.get('errors') or [])
    reads = {k: list((doc.get('readings') or {}).get(k) or []) for k in ('supabase', 'emergent')}
    out = {}

    def failed(at, k, file, where, route, reason, code):
        # The same failure of the files of one upload is one line with a count, so one stuck mock cannot push the others out of the list.
        key = (k, where, route, code, reason[:240])
        same = next((x for x in errors if (x.get('k'), x['store'], x['route'], x.get('code'), x['reason']) == key), None)
        if same:
            errors.remove(same)
        errors.append({'at': at, 'k': k, 'file': file, 'store': where, 'route': route, 'reason': reason[:240], 'code': code, 'n': (same or {}).get('n', 0) + 1})

    def bad(prev, at, how, e, handed=0):
        went = prev.get('ok') is False
        return {'ok': False, 'at': at, 'how': how, 'error': (e.get('error') or '')[:240], 'code': e.get('code'), 'scope': e.get('scope') or 'away', 'said': e.get('said') or '',
                'bad_since': prev.get('bad_since') or at if went else at, 'waits': (prev.get('waits', 0) if went else 0) + handed}

    for e in sorted(events, key=lambda x: x['at']):
        at, kind, ok = e['at'], e['kind'], bool(e.get('ok'))
        timing = {'at': at, 'write_ms': e.get('write_ms') or 0, 'read_ms': e.get('read_ms') or 0}
        if kind == 'check' and e['store'] == 'supabase':
            if at >= small.get('at', 0):
                small = {'ok': True, 'how': 'check', **timing} if ok else bad(small, at, 'check', e)
                if ok:
                    out['ok_at'] = at
            if ok:
                reads['supabase'].append(timing)
            else:
                failed(at, 'check-supabase', CHECK_FILE, 'supabase', 'check', why(bad({}, at, 'check', e)), e.get('code'))
        elif kind == 'check':
            if at >= em.get('at', 0):
                em = {'ok': ok, **timing, 'error': (e.get('error') or '')[:240]}
            if ok:
                reads['emergent'].append(timing)
            else:
                failed(at, 'check-emergent', CHECK_FILE, 'emergent', 'check', said({'store': 'emergent', 'route': 'check', 'raw': e.get('error')}), None)
        elif kind == 'small':
            if ok:
                if small.get('ok') is False and at >= small.get('at', 0):   # a real file went through after a failure
                    small = {'ok': True, 'how': 'file', 'at': at}
                    out['ok_at'] = at
            elif at >= small.get('at', 0):
                small = bad(small, at, 'file', e, 1)
        elif kind == 'big':
            if e.get('how') == 'test':
                out['big_test_at'] = at
            # Supabase itself not answering is not a fault of the big-file route: what is known about that route stays.
            if (ok or e.get('scope') not in ('away', 'blocked')) and at >= big.get('at', 0):
                big = {'ok': ok, 'at': at, **{k: e.get(k) for k in ('how', 'via', 'ms', 'size', 'code', 'scope', 'said')}, 'error': (e.get('error') or '')[:240]}
            if not ok and e.get('how') == 'test':
                failed(at, 'big-test', BIG_FILE, 'supabase', 'big', why(e, True), e.get('code'))
        elif kind == 'error':
            name, k = names.get(e.get('path')) or ('File', 'file')
            failed(at, k, name, e['store'], e['route'], said(e), e.get('code'))
    out.update(small=small, big=big, emergent=em, errors=errors[-KEEP:], readings={k: v[-KEEP:] for k, v in reads.items()})
    return out


async def flush():
    """Writes the notes of this server into the shared record. A record another server changed meanwhile is read again, so no line is lost."""
    events = []
    while store.EVENTS:
        try:
            events.append(store.EVENTS.popleft())
        except IndexError:
            break
    if not events:
        return 0
    try:
        names = await labels(events)
        for _ in range(5):
            doc = await record()
            done = await col().update_one({'_id': ID, 'rev': doc.get('rev', 0)}, {'$set': merge(doc, events, names), '$inc': {'rev': 1}})
            if done.modified_count:
                return len(events)
    except Exception:
        store.EVENTS.extendleft(reversed(events))   # the database did not take them: they are kept for the next try
        raise
    store.EVENTS.extendleft(reversed(events))   # five other writers were quicker: the notes are kept for the next try
    log.warning('Storage notes could not be written this time (%s notes are kept for the next try).', len(events))
    return 0


def _poke():
    """Called by the storage code from any thread: the notes are written within two seconds, one write at a time."""
    loop = _mem['loop']
    if loop is not None and not loop.is_closed():
        try:
            loop.call_soon_threadsafe(_soon)
        except RuntimeError:
            pass


def _soon():
    if _running['flush'] is None or _running['flush'].done():
        _running['flush'] = asyncio.ensure_future(_later())


async def _later():
    await asyncio.sleep(2)
    try:
        await flush()
    except Exception:  # noqa: BLE001
        log.warning('Storage notes could not be written; they are tried again.', exc_info=True)


store.on_event = _poke


# ---------- What the badge shows ----------
async def facts():
    """Files that are held right now, counted from the database: stuck in Supabase, and waiting for more than 10 minutes."""
    late = time.time() - HELD
    # A row the owner is trying again right now ("Dobara chalao") is not counted; if that try never ends, the Machine list shows it after 15 minutes.
    held = {'removed': False, 'archived': {'$ne': True}, 'paused': {'$ne': True}, 'payload.storage_wait': {'$exists': True}, 'payload.storage_wait.kind': {'$ne': 'hang'},
            'payload.storage_wait.retrying': {'$ne': True}}
    stuck = await db.tejas_books.count_documents({**held, 'payload.storage_wait.stuck': True})
    waiting = await db.tejas_books.count_documents({**held, 'payload.storage_wait.stuck': {'$ne': True}, 'payload.storage_wait.since': {'$lte': late}})
    big_waiting = await db.tejas_books.count_documents({**held, 'payload.transfer': {'$exists': True}})
    # A PDF whose own work went silent again and again is "Atki hai" too, though no store is at fault: it is counted apart and said so.
    hung = await db.tejas_books.count_documents({**held, 'payload.storage_wait.kind': 'hang', 'payload.storage_wait.stuck': True})
    for c in (db.tejas_imports, db.tejas_chapter_books):
        stuck += await c.count_documents({'status': 'queued', 'stuck': True})
        waiting += await c.count_documents({'status': 'queued', 'stuck': {'$ne': True}, 'storage_wait_since': {'$lte': late}})
    other = {'status': 'queued', 'kind': {'$ne': 'book_step'}, 'storage_waits': {'$gt': 0}, 'next_run_at': {'$gt': 0}}
    stuck += await db.tejas_jobs.count_documents({**other, 'stuck': True})
    waiting += await db.tejas_jobs.count_documents({**other, 'stuck': {'$ne': True}, 'storage_wait_since': {'$lte': late}})
    return {'stuck': stuck, 'waiting': waiting, 'big_waiting': big_waiting, 'hung': hung}


def speed(rows):
    took = [r['write_ms'] + r['read_ms'] for r in rows]
    return {'n': len(took), 'median_ms': round(statistics.median(took)), 'min_ms': min(took), 'max_ms': max(took), 'last_ms': took[-1]} if took else {'n': 0}


async def summary(doc=None):
    """Green: both Supabase routes work and nothing is held. Yellow: slow, a file stuck or held 10 minutes, the big-file route failed
    or was never tried, or Emergent (fallback) does not answer. Red: Supabase does not answer, or the project is blocked."""
    doc = doc or await record()
    t, on, st = time.time(), store.configured(), store.STATE
    small, big, em = doc.get('small') or {}, doc.get('big') or {}, doc.get('emergent') or {}
    took = (small.get('write_ms') or 0) + (small.get('read_ms') or 0)
    away = bool(small) and not small.get('ok') and (small.get('scope') or 'away') in ('away', 'blocked')   # Supabase itself is away or blocked
    red, yellow, held = [], [], {'stuck': 0, 'waiting': 0, 'hung': 0}
    if not on and not em:
        mode = 'unknown'
        yellow.append('Storage ki jaanch chal rahi hai.')
    elif not on:
        mode = 'emergent' if em.get('ok') else 'down'
        (yellow if em.get('ok') else red).append(NOT_SET if em.get('ok') else 'Dono storage abhi jawab nahi de rahe. Upload ke baad book save nahi ho payegi.')
    else:
        f = await facts()
        held = {'stuck': f['stuck'], 'waiting': f['waiting'], 'hung': f['hung']}
        if not small:
            mode = 'unknown'
            yellow.append('Storage ki jaanch chal rahi hai.')
        elif small.get('ok'):
            mode = 'slow' if took > SLOW_MS else 'supabase'
            if mode == 'slow':
                yellow.append(f'Supabase dheema hai: jaanch mein {took} ms lage. Files phir bhi Supabase mein ja rahi hain.')
        elif away:
            mode, line = 'waiting', why(small)
            if small.get('scope') == 'blocked':
                red.append(f"Supabase project par rok hai: {line}. {store.explain(small.get('code'), 'blocked')[1]}")
            else:
                red.append(f'Supabase abhi file nahi le raha. Wajah: {line}. Naya kaam ruka hai aur surakshit hai; Supabase lautte hi apne aap aage chalega.')
        else:
            # Supabase answers, only the check file did not go or came back wrong: nothing is rested, real files are still tried one by one.
            mode = 'supabase'
            yellow.append(f'Supabase jawab de raha hai, par jaanch file theek nahi gayi. Wajah: {why(small)}. Asli files abhi bhi bheji ja rahi hain; jo rukegi woh neeche list mein dikhegi.')
        if f['stuck']:
            yellow.append(f"{f['stuck']} file Supabase mein atki hai. Wajah aur \"Dobara chalao\" neeche Machine ki list mein hai.")
        if f['waiting']:
            yellow.append(f"{f['waiting']} file 10 minute se zyada se ruki hai.")
        if f['hung']:
            yellow.append(f"{f['hung']} PDF ka kaam baar-baar latak kar ruk gaya hai (Atki hai). Yeh storage ki galti nahi hai; \"Dobara chalao\" neeche Machine ki list mein hai.")
        if big.get('ok') is False:
            yellow.append(f'Badi file (PDF) ka raasta pichhli baar nahi chala. Wajah: {why(big, True)}.')
        elif not big.get('at'):
            yellow.append('Badi file (PDF) ka raasta abhi tak jaancha nahi gaya. "Badi file ka test" dabaiye; warna agli 15-minute jaanch ise khud jaanch legi.')
        if em and not em.get('ok'):
            yellow.append('Emergent (fallback) jawab nahi de raha. Nayi files Supabase mein ja rahi hain, isliye kaam chal raha hai.')
    since = small.get('bad_since') if away else None
    readings = doc.get('readings') or {}
    return {'mode': mode, 'level': 'red' if red else 'yellow' if yellow else 'green', 'reasons': red + yellow or [GREEN], 'checked_at': doc.get('checked_at') or 0,
            'supabase': {'ok': bool(small.get('ok')), 'state': 'ok' if small.get('ok') else 'bad' if away or not small else 'warn', 'at': small.get('at') or 0, 'how': small.get('how', ''),
                         'write_ms': small.get('write_ms') or 0, 'read_ms': small.get('read_ms') or 0,
                         'error': ('' if small.get('ok') or not small else why(small)) if on else 'Supabase set nahi hai (project URL ya secret key nahi mili).',
                         'code': small.get('code'), 'configured': on, 'bucket': store.bucket_name() if on else '', 'resting_until': 0},
            'big': {'state': 'ok' if big.get('ok') else 'bad' if big.get('ok') is False else 'unknown', 'at': big.get('at') or 0, 'how': big.get('how') or '', 'via': big.get('via') or '',
                    'ms': big.get('ms') or 0, 'size': big.get('size') or 0, 'error': why(big, True) if big.get('ok') is False else '', 'running': (doc.get('big_lease') or 0) > t},
            'emergent': {'ok': bool(em.get('ok')), 'at': em.get('at') or 0, 'write_ms': em.get('write_ms') or 0, 'read_ms': em.get('read_ms') or 0, 'error': em.get('error', '')},
            'speed': {k: speed(readings.get(k) or []) for k in ('supabase', 'emergent')}, 'held': held,
            'writes': dict(st['writes']), 'failovers': st['failovers'], 'last_failover': st['last_failover'],
            'backup': {'since': since, 'writes': small.get('waits', 0) if since else 0, 'alert': bool(on and since and t - since >= ALERT_AFTER)}}


async def errors():
    """The last 20 storage failures, newest first: when, which file, which store, which route, why."""
    doc = await col().find_one({'_id': ID}, {'errors': 1}) or {}
    return [{k: v for k, v in e.items() if k != 'k'} for e in reversed(doc.get('errors') or [])]


async def current():
    """What the record says now, without checking the stores (None before the first check)."""
    doc = await col().find_one({'_id': ID})
    return await summary(doc) if doc and doc.get('checked_at') else None


# ---------- Checking ----------
async def _check():
    await record()
    t = time.time()
    held = await col().update_one({'_id': ID, 'check_lease': {'$not': {'$gt': t}}}, {'$set': {'check_lease': t + 120}})
    if not held.modified_count:
        return 0   # another server is checking this very moment: its answer is in the record
    try:
        result = await run_in_threadpool(store.probe)
        await flush()
        await col().update_one({'_id': ID}, {'$set': {'checked_at': time.time()}})
        if not result['supabase'].get('ok'):
            return 0
        _mem['ok_at'] = ((await col().find_one({'_id': ID}, {'ok_at': 1})) or {}).get('ok_at') or time.time()
        from .jobs import wake_storage
        return await wake_storage()
    finally:
        await col().update_one({'_id': ID}, {'$set': {'check_lease': 0}})


async def check():
    """Both stores are checked now, by one server at a time. Returns how many waiting jobs it woke."""
    task = _running['check']
    if task is None or task.done():
        task = _running['check'] = asyncio.ensure_future(_check())
    return await asyncio.shield(task)


async def check_now():
    """Checks Supabase now, not from the last minute's answer (an owner pressed a button)."""
    await check()
    return await summary()


async def big_test():
    """The big-file route is tried with a test file of about 7 MB, by one server at a time. None while another test is running."""
    await record()
    t = time.time()
    held = await col().update_one({'_id': ID, 'big_lease': {'$not': {'$gt': t}}}, {'$set': {'big_lease': t + BIG_LEASE}})
    if not held.modified_count:
        return None
    try:
        out = await run_in_threadpool(store.probe_big)
        await flush()
        return out
    finally:
        await col().update_one({'_id': ID}, {'$set': {'big_lease': 0}})


def due_big(doc, f, t):
    """The big-file route is tried by itself: when it was never proven, when it failed or a PDF waits on it (every 15 minutes), and once a day."""
    big, last = doc.get('big') or {}, doc.get('big_test_at') or 0
    if not store.configured() or not (doc.get('small') or {}).get('ok'):
        return False
    if not big.get('at') or big.get('ok') is False or f['big_waiting']:
        return t - last > BIG_AGAIN
    return t - big['at'] > BIG_EVERY


async def routine():
    """The scheduled check (every 15 minutes): the record stays fresh when nobody is looking, the big-file route is tried when it
    is due, and check files left behind are swept once a day."""
    if _mem['loop'] is None:
        return   # not a started server (a script, a test): the stores are checked only when someone asks
    try:
        doc, t = await record(), time.time()
        if t - (doc.get('checked_at') or 0) > HELD:
            await check()
            doc = await record()
        else:
            await flush()
        if not store.configured():
            return
        if due_big(doc, await facts(), t):
            await big_test()
        if t - (doc.get('swept_at') or 0) > BIG_EVERY and (doc.get('small') or {}).get('ok'):
            await col().update_one({'_id': ID}, {'$set': {'swept_at': t}})
            gone = await run_in_threadpool(store.sweep_checks)
            if gone:
                log.info('Storage check files left behind were removed: %s', gone)
    except Exception:  # noqa: BLE001  a storage check must never stop anything else
        log.warning('The scheduled storage check did not finish; the next one tries again.', exc_info=True)


async def watch_once():
    """This server writes its notes; and a check on ANY server that found Supabase well ends this server's own rest and wakes its lanes."""
    await flush()
    small = ((await col().find_one({'_id': ID}, {'small.ok': 1, 'small.at': 1})) or {}).get('small') or {}
    if small.get('ok') is False and store.STATE['last_ok'] > small.get('at', 0):
        # The record says Supabase failed, but this server saved a file after that: it says so, and the record is right again.
        store._note('small', ok=True, at=store.STATE['last_ok'])
        await flush()
    seen = ((await col().find_one({'_id': ID}, {'ok_at': 1})) or {}).get('ok_at') or 0
    if seen <= _mem['ok_at']:
        return False
    _mem['ok_at'] = seen
    if seen > store.STATE.get('struck_at', 0) and (store.STATE['strikes'] or store.STATE['down_until']):
        store._ok()
    from .jobs import wake_local
    await wake_local()
    return True


async def watch():
    """Runs on every server from its start, every half minute."""
    _mem['loop'] = asyncio.get_running_loop()
    while True:
        await asyncio.sleep(WATCH)
        try:
            await watch_once()
        except Exception:  # noqa: BLE001
            log.warning('The storage watch missed a round; it carries on.', exc_info=True)


@router.post("/retry")
async def retry(u=Depends(owner)):
    """'Abhi phir try karo': checks Supabase now; if it answers, every job waiting for it runs at once."""
    woke = await check()
    return {**await summary(), 'woke': woke}


@router.post("/big-test")
async def run_big_test(u=Depends(owner)):
    """'Badi file ka test': about 7 MB by the real piece route, read back, removed. Says how long it took, or why it failed."""
    if not store.configured():
        raise HTTPException(409, 'Supabase set nahi hai, isliye badi file ka test nahi chal sakta.')
    task = asyncio.ensure_future(big_test())
    _tasks.add(task)   # kept until it is over: a test that outlives its request must not be dropped half way
    task.add_done_callback(_tasks.discard)
    try:
        out = await asyncio.wait_for(asyncio.shield(task), BIG_ANSWER)
    except asyncio.TimeoutError:
        # A slow Supabase: the test carries on behind and writes its result into the record; the badge shows it when it is over.
        return {**await summary(), 'big_test': None}
    if out is None:
        raise HTTPException(409, 'Badi file ka test abhi chal raha hai. Nateeja thodi der mein yahin dikhega.', headers={'Retry-After': '10'})
    return {**await summary(), 'big_test': {'ok': out['ok'], 'ms': out.get('ms') or 0, 'size': out['size'], 'reason': '' if out['ok'] else why(out, True)}}


@router.get("/health")
async def health(fresh: bool = Query(False), u=Depends(owner)):
    """Checked at most once a minute (on asking with fresh=true, at most every 10 s), so the badge never loads the stores."""
    doc = await record()
    age = time.time() - (doc.get('checked_at') or 0)
    if age > FRESH or (fresh and age > 10):
        await check()
    else:
        await flush()
    return await summary()
