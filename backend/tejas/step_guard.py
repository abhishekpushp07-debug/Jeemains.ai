"""A PDF step that goes silent is let go (the PDF lane only; grading, scores and reports are not watched).
Every sign of life is a beat: the lock checked or renewed, the book saved, a 6 MB piece sent, a picture saved. A step with no beat
for 10 minutes is written down (where it stood), cancelled, or left behind when it cannot be cancelled; its lock is freed and the
job runs again from the saved place. The third silent step in a row stops only that PDF ("Atki hai")."""
import asyncio, io, logging, os, socket, sys, threading, time, traceback
from pymongo import ReturnDocument
from .db import db, now, uid

SILENCE, CHECK, LET_GO, DB_WAIT = 600, 5, 10, 15       # seconds
HANG_LIMIT, HUNG_RETRY, HUNG_STUCK_RETRY = 3, 20, 3600
_watched, _left = {}, set()
log = logging.getLogger(__name__)


class StepHung(Exception):
    stuck = False   # True from the third silent step in a row


def beat(book_id, what=''):
    """A sign of life from the step working on this PDF. Costs nothing when no step of it is watched (also called from worker threads)."""
    s = _watched.get(book_id)
    if s is not None:
        s['n'] += 1
        if what:
            s['what'] = what


def holds(book_id, token):
    """The watched step took the PDF's lock: the guard can free exactly this lock if the step never comes back."""
    s = _watched.get(book_id)
    if s is not None:
        s['token'] = token
        s['n'] += 1


def _chain(task, ours=False):
    """Every 'await' the task is inside of, outermost first (a waiting task shows only its first frame otherwise). ours: this app's code only."""
    out, c = [], task.get_coro()
    while c is not None and len(out) < 40:
        f = getattr(c, 'cr_frame', None) or getattr(c, 'gi_frame', None)
        if f is not None and (not ours or '/backend/' in f.f_code.co_filename):
            out.append(f'{os.path.basename(f.f_code.co_filename)}:{f.f_lineno} {f.f_code.co_name}')
        c = getattr(c, 'cr_await', None) or getattr(c, 'gi_yieldfrom', None)
    return out


def _where(task):
    """The app's own last three steps, then the innermost wait itself."""
    own = _chain(task, True)[-3:]
    return ' › '.join(own + [x for x in _chain(task)[-1:] if x not in own])[:300]


def _picture(task):
    """Where the silent step stands, the other waiting pieces of work of this server, and every thread: enough to find the cause later."""
    out = io.StringIO()
    print('--- the silent step:', ' › '.join(_chain(task)), file=out)
    shown = 0
    for other in asyncio.all_tasks():
        if other is not task and not other.done() and shown < 20:
            shown += 1
            print('--- other task', other.get_name(), ':', ' › '.join(_chain(other)[-6:]), file=out)
    names = {t.ident: t.name for t in threading.enumerate()}
    for ident, frame in list(sys._current_frames().items())[:40]:
        print('--- thread', names.get(ident, ident), file=out)
        out.write(''.join(traceback.format_stack(frame, limit=6)))
    text = out.getvalue()
    return text if len(text) <= 14000 else text[:7000] + '\n...\n' + text[-7000:]


def _bury(task):
    _left.discard(task)
    if not task.cancelled():
        task.exception()   # read, so it is not reported as never looked at


async def _try(op, what):
    """The guard's own notes must never hang with the step: each gets 15 seconds."""
    try:
        return await asyncio.wait_for(op, DB_WAIT)
    except Exception:  # noqa: BLE001
        log.warning('Step guard: %s did not finish.', what, exc_info=True)


async def let_go(job, task, state, quiet):
    id = job['payload']['book_id']
    where, picture, last = _where(task), _picture(task), state['what']
    log.error('A PDF step showed no sign of life for %d s (book=%s, job=%s, last: %s) at %s. It is let go; the job runs again from the saved place.',
              int(quiet), id, job['id'], last, where)
    task.cancel()
    done, _ = await asyncio.wait({task}, timeout=LET_GO)
    if done:
        _bury(task)
    else:
        # It cannot be cancelled (a thread that never answers): it is left behind. Its lock is taken away, so it can no longer save anything.
        _left.add(task)
        task.add_done_callback(_bury)
    if state['token']:
        await _try(db.tejas_books.update_one({'_id': id, 'lock_token': state['token']}, {'$unset': {'lock_token': '', 'lock_until': ''}}), 'freeing its lock')
    t = now()
    row = await _try(db.tejas_books.find_one_and_update({'_id': id}, [{'$set': {'payload.hang': {
        'count': {'$add': [{'$ifNull': ['$payload.hang.count', 0]}, 1]}, 'since': {'$ifNull': ['$payload.hang.since', t]}, 'at': t, 'where': {'$literal': where}}}}],
        projection={'payload.hang': 1, 'payload.title': 1}, return_document=ReturnDocument.AFTER), 'counting it')
    p = (row or {}).get('payload') or {}
    hang = p.get('hang') or {'count': 1, 'since': t}
    stuck, minutes = hang['count'] >= HANG_LIMIT, max(1, round(SILENCE / 60))
    if stuck:
        change = {'payload.storage_wait': {'since': hang['since'], 'at': t, 'kind': 'hang', 'code': None, 'stuck': True,
                                           'error': f'PDF step silent for {int(quiet)} s at {where}'[:300],
                                           'reason': f"kaam {hang['count']} baar lagataar {minutes} minute tak bina harkat ke latka raha",
                                           'next': 'Har ghante apne aap phir koshish hogi. Abhi koshish ke liye "Dobara chalao" dabaiye.'},
                  'payload.message': 'Atki hai: is PDF ka kaam baar-baar beech me latak gaya. File surakshit hai; baaki kitaabein chal rahi hain.'}
    else:
        change = {'payload.message': f"Yeh kadam {minutes} minute tak latka raha. Machine ne ise chhod kar save hui jagah se dobara shuru kiya ({hang['count']}/{HANG_LIMIT})."}
    await _try(db.tejas_books.update_one({'_id': id}, {'$set': change}), 'noting it on the PDF')
    await _try(db.tejas_step_hangs.insert_one({'_id': uid(), 'at': t, 'book_id': id, 'job_id': job['id'], 'title': (p.get('title') or '')[:160], 'silent': round(quiet, 1),
                                               'last_beat': last, 'where': where, 'stack': picture, 'count': hang['count'], 'freed': bool(done),
                                               'server': f'{socket.gethostname()}:{os.getpid()}'}), 'writing it down')
    exc = StepHung(f'PDF step silent for {int(quiet)} s at {where}')
    exc.stuck = stuck
    return exc


async def guarded(job):
    """Runs one PDF step and watches it. The step's own result or error comes back unchanged; StepHung when it had to be let go."""
    from . import book_worker
    id = job['payload']['book_id']
    state = _watched[id] = {'n': 0, 'what': 'started', 'token': None}
    task = asyncio.ensure_future(book_worker.step(job))
    quiet, last, seen = 0.0, time.monotonic(), 0
    try:
        while True:
            done, _ = await asyncio.wait({task}, timeout=CHECK)
            if done:
                return task.result()
            t = time.monotonic()
            # Only time the watcher itself saw pass is counted: a busy server is not mistaken for a silent step.
            quiet = 0.0 if state['n'] != seen else quiet + min(t - last, CHECK * 2)
            seen, last = state['n'], t
            if quiet >= SILENCE:
                break
        raise await let_go(job, task, state, quiet)
    except asyncio.CancelledError:
        task.cancel()
        raise
    finally:
        if _watched.get(id) is state:
            del _watched[id]
