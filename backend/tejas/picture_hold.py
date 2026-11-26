"""A built test that is switched on again (Off to Live or Scheduled, a series day's paper, a return from the Library) is shown to students
only after every picture of it is proven in storage, all in one store. Until then it stays Off and remembers what was asked
(`picture_wait` on the test); once proven it becomes what was asked by itself. Not proven: it stays Off, its row says why, and the proof
is tried again every 15 minutes and on "Dobara chalao". A time that passed meanwhile is never opened late.
Nothing here saves, copies or removes a picture. Verified JEE Main PYQ papers are never checked or held."""
import asyncio, logging, uuid
import tejas_storage as store
from .db import sets, now, audit
from .canonical import database_now
from .picture_proof import prove, picture_ids, remember, KINDS

log = logging.getLogger(__name__)
REFS = {'_id': 0, 'id': 1, 'test_kind': 1, 'master_pyq': 1, 'written': 1, 'questions.number': 1, **{f'questions.{k}.file_id': 1 for k in KINDS}}
# What decides whether students would see a test, without its questions.
SEEN = {**REFS, **{k: 1 for k in ('status', 'owner_unlive', 'start_at', 'end_at', 'live_enabled', 'series_import', 'series_date', 'series_window',
                                  'series_id', 'import_id', 'chapter_book_id', 'expires')}}
ARCHIVE = ('archived', 'archived_at', 'archived_by', 'archived_reason')
WAIT, RETRY, LEASE, YOUNG = 6, 840, 600, 120
THEN = {'live': 'Live ho jayega', 'scheduled': 'chune hue samay ke liye Schedule ho jayega', 'on': 'Live ho jayega', 'restore': 'apni purani haalat mein laut aayega'}
NOT = {'live': 'Live nahi hua', 'scheduled': 'Schedule nahi hua', 'on': 'Live nahi hua', 'restore': 'apni purani haalat mein nahi lauta'}
DONE = {'live': 'Pictures saabit ho gayi: yeh ab Live hai.', 'scheduled': 'Pictures saabit ho gayi: yeh chune hue samay ke liye Schedule ho gaya.',
        'on': 'Pictures saabit ho gayi: yeh ab Live hai.', 'restore': 'Pictures saabit ho gayi: yeh apni purani haalat mein laut aaya.'}
CHANGED = 'Yeh test abhi-abhi badla hai. Reload kijiye.'
_gate, _tasks, _busy = asyncio.Semaphore(2), set(), set()   # at most two tests are proven at once on a server: other work is never crowded out


def needed(s):
    from .structure import locked
    return not locked(s) and bool(picture_ids(s))


def shown(s, t):
    """Whether students see this built test, now or at its time. A series paper whose day is over is still open to them as practice."""
    from .structure import test_state
    from .content import permitted
    if s.get('status') != 'published' or s.get('owner_unlive'):
        return False
    if test_state(s, t) in ('live', 'scheduled'):
        return True
    return bool(s.get('series_id') and s.get('series_date')) and permitted({**s, 'audience': 'all'}, series_schedule=True, at=t)


async def refs(set_id):
    return await sets.find_one({'id': set_id}, REFS) or {}


def opens(s, t):
    """Its own start, when that is still ahead: a proof that ends after it does not open the test late."""
    return s['start_at'] if (s.get('start_at') or 0) > t else None


def line(outcome, words, to):
    """One plain line for the owner about a test that waits for its pictures."""
    if outcome == 'checking':
        return f'Iski pictures storage mein jaanchi ja rahi hain; saabit hote hi yeh apne aap {THEN[to]}. Tab tak Off hai.'
    if outcome == 'stuck':
        return (f'Iski pictures storage mein saabit nahi hui, isliye yeh {NOT[to]} (Off hi hai). Wajah: {words}. '
                'Har 15 minute mein apne aap phir jaanch hoti hai; abhi ke liye “Dobara chalao” dabaiye.')
    if outcome == 'missed':
        return 'Iska samay pictures saabit hone se pehle nikal gaya, isliye yeh nahi khula (Off hi hai). Yeh der se apne aap nahi khulega: “Live karo” dabaiye ya naya samay chuniye.'
    return words


def view(w):
    """What the test's row in Super Admin is given."""
    return {'state': w['state'], 'to': w['to'], 'at': w.get('at'), 'since': w['since'], 'reason': w.get('reason', ''), 'kind': w.get('kind', ''),
            'line': line(w['state'], w.get('reason', ''), w['to'])}


def new_wait(to, by, at=None, live_exam=False, held=False):
    return {'to': to, 'at': at, 'live_exam': bool(live_exam), 'since': now(), 'by': by, 'token': uuid.uuid4().hex, 'state': 'checking',
            **({'held': True} if held else {})}


def start(set_id, token):
    task = asyncio.create_task(check(set_id, token))
    _tasks.add(task)
    _busy.add(token)
    task.add_done_callback(lambda done: (_tasks.discard(done), _busy.discard(token)))
    return task


async def ask(set_id, to, by, at=None, live_exam=False):
    """Notes what was asked on the test (it stays Off) and starts its proof. Returns the running proof: see settle()."""
    wait = new_wait(to, by, at, live_exam)
    await sets.update_one({'id': set_id}, {'$set': {'picture_wait': wait}})
    return start(set_id, wait['token'])


async def settle(tasks, seconds=None):
    """Waits a little for the proofs started by this request, so a quick proof answers at once. One (outcome, words) per proof;
    a proof still running is 'checking' and carries on by itself."""
    if tasks:
        await asyncio.wait(tasks, timeout=WAIT if seconds is None else seconds)
    return [t.result() if t.done() and not t.cancelled() and not t.exception() else ('checking', '') for t in tasks]


def _named(s, bad):
    qs = [f"Q{q.get('number')}" for q in s.get('questions') or [] if any(r.get('file_id') in bad for k in KINDS for r in q.get(k) or [])]
    return ', '.join(qs[:10]) + (' aur baaki' if len(qs) > 10 else '')


def _cannot_say(exc):
    code, scope = getattr(exc, 'code', None), store.scope_of(exc)
    return store.explain(code, scope)[0] if scope in ('away', 'blocked') else 'Supabase ne is test ki pictures ki list nahi di' + (f' ({code})' if code else '')


def _unproven(s, proof):
    who = _named(s, proof['bad'])
    return proof['reason'] + (f' ({who})' if who else '')


async def refusal(s, so, named=True):
    """The older doors ask inline: why this built test cannot be shown to students now, or None. Reads only; nothing is noted on the test."""
    if not needed(s):
        return None
    try:
        proof = await prove(s, full=bool(s.get('written')))
    except store.StorageError as exc:
        return f'Is test ki pictures abhi jaanchi nahi ja saki ({_cannot_say(exc)}), {so}. Thodi der baad phir koshish kijiye.'
    if proof and not proof['ok']:
        return f"Is test ki pictures storage mein saabit nahi hui, {so}. Wajah: {_unproven(s, proof) if named else proof['reason']}."
    if proof and s.get('id'):
        await remember(s['id'], proof)
    return None


async def _stuck(mine, reason, kind):
    await sets.update_one(mine, {'$set': {'picture_wait.state': 'stuck', 'picture_wait.reason': str(reason)[:300], 'picture_wait.kind': kind, 'picture_wait.tried_at': now()},
                                 '$unset': {'picture_wait.lease': ''}})
    return 'stuck', str(reason)[:300]


async def _apply(mine, wait):
    t = await database_now()
    if wait.get('at') and t >= wait['at']:
        await sets.update_one(mine, {'$set': {'picture_wait.state': 'missed', 'picture_wait.tried_at': now()},
                                     '$unset': {'picture_wait.lease': '', 'picture_wait.reason': '', 'picture_wait.kind': ''}})
        await audit(wait['by'], 'Test missed its time', mine['id'], 'Its time passed before its pictures were proven. It stays Off and does not open late.')
        return 'missed', ''
    if wait['to'] in ('live', 'scheduled'):
        from .master import on_change
        s = await sets.find_one(mine, {'_id': 0, 'questions': 0})
        if not s:
            return 'gone', ''
        why, update = on_change(s, wait['at'] if wait['to'] == 'scheduled' else None, wait.get('live_exam'), t)
        if why:
            return await _stuck(mine, why, 'rule')
    else:
        update = {'$unset': {'owner_unlive': '', 'picture_wait': ''}}
    if not (await sets.update_one(mine, update)).modified_count:
        return 'gone', ''
    await audit(wait['by'], 'Test pictures proven', mine['id'], f"asked: {wait['to']}")
    if wait['to'] in ('live', 'scheduled'):
        from .structure import test_state
        row = await sets.find_one({'id': mine['id']}, {'_id': 0, 'questions': 0})
        if test_state(row, t) not in ('live', 'scheduled'):
            return 'done', 'It is still paused by its own upload settings. Open its upload to enable it.'
    return 'done', ''


async def _check(set_id, token):
    t = now()
    mine = {'id': set_id, 'picture_wait.token': token, 'archived': {'$ne': True}}
    # One server proves a test at a time; another that picks it up meanwhile leaves it alone.
    held = await sets.find_one_and_update({**mine, '$or': [{'picture_wait.lease': {'$exists': False}}, {'picture_wait.lease': {'$lt': t}}]},
                                          {'$set': {'picture_wait.lease': t + LEASE, 'picture_wait.state': 'checking'}}, projection={'_id': 0, 'picture_wait': 1})
    if not held:
        return ('checking' if await sets.find_one(mine, {'_id': 1}) else 'gone'), ''
    s = await refs(set_id)
    try:
        proof = await prove(s, full=bool(s.get('written')))
    except store.StorageError as exc:   # Supabase could not be asked: no picture is called missing
        return await _stuck(mine, f'Abhi jaanch nahi ho saki ({_cannot_say(exc)})', 'away')
    if proof and not proof['ok']:
        await remember(set_id, proof)   # its row no longer says "Pictures: n / n" from an older proof
        return await _stuck(mine, _unproven(s, proof), 'proof')
    out = await _apply(mine, held['picture_wait'])
    if out[0] == 'done' and proof:
        await remember(set_id, proof)
    return out


async def check(set_id, token):
    """Proves the pictures of one waiting test and, when proven, makes it what was asked. Returns (outcome, words): 'done', 'stuck',
    'missed', 'checking' (another server is on it) or 'gone' (asked again, or no longer here). Never raises."""
    try:
        async with _gate:
            return await asyncio.wait_for(_check(set_id, token), LEASE - 60)   # a read that never ends gives its place to the next test
    except Exception:  # noqa: BLE001  one test's trouble stays with that test
        log.warning('The picture proof of %s stopped midway; it is tried again.', set_id, exc_info=True)
        try:
            return await _stuck({'id': set_id, 'picture_wait.token': token}, 'Jaanch beech mein ruk gayi', 'other')
        except Exception:  # noqa: BLE001
            return 'stuck', 'Jaanch beech mein ruk gayi'


async def again(set_id):
    """The owner's "Dobara chalao" on one test. None when it does not wait for a proof."""
    w = (await sets.find_one({'id': set_id, 'archived': {'$ne': True}, 'picture_wait.state': {'$in': ['checking', 'stuck']}}, {'_id': 0, 'picture_wait': 1}) or {}).get('picture_wait')
    if not w:
        return None
    token = uuid.uuid4().hex   # a proof already running for the old asking can no longer change the test
    done = await sets.update_one({'id': set_id, 'picture_wait.token': w['token']},
                                 {'$set': {'picture_wait.token': token, 'picture_wait.state': 'checking', 'picture_wait.tried_at': now()}, '$unset': {'picture_wait.lease': ''}})
    if not done.modified_count:
        return None
    outcome, words = (await settle([start(set_id, token)]))[0]
    return {'state': outcome, 'message': CHANGED if outcome == 'gone' else line(outcome, words, w['to']) or DONE[w['to']]}


async def resume():
    """The 15-minute round: a proof that did not pass is tried again, and one whose server stopped midway is picked up.
    A proof this server is already waiting to run is not started a second time."""
    t = now()
    rows = await sets.find({'picture_wait.state': {'$in': ['checking', 'stuck']}, 'archived': {'$ne': True}}, {'_id': 0, 'id': 1, 'picture_wait': 1}).limit(500).to_list(500)
    due = [r for r in rows if r['picture_wait']['token'] not in _busy and (r['picture_wait'].get('lease') or 0) < t
           and t - (r['picture_wait'].get('tried_at') or r['picture_wait']['since']) >= (RETRY if r['picture_wait']['state'] == 'stuck' else YOUNG)]
    return [start(r['id'], r['picture_wait']['token']) for r in due]


async def back_from_library(ids, by):
    """Tests that students would see again leave the Library Off, with their proof asked. Returns {test id: token} of those."""
    t, out = await database_now(), {}
    async for s in sets.find({'id': {'$in': ids}, 'archived': True, 'status': 'published', 'owner_unlive': {'$ne': True}}, SEEN):
        if not shown(s, t) or not needed(s):
            continue
        wait = new_wait('restore', by, opens(s, t), held=True)
        done = await sets.update_one({'id': s['id'], 'archived': True}, {'$set': {'owner_unlive': True, 'picture_wait': wait}, '$unset': {k: '' for k in ARCHIVE}})
        if done.modified_count:
            out[s['id']] = wait['token']
    return out


async def forget(ids):
    """Tests that left for the Library no longer wait. One that was kept Off only for its proof is not remembered as Off."""
    if not ids:
        return
    await sets.update_many({'id': {'$in': ids}, 'archived': True, 'picture_wait.held': True}, {'$unset': {'owner_unlive': '', 'picture_wait': ''}})
    await sets.update_many({'id': {'$in': ids}, 'archived': True, 'picture_wait': {'$exists': True}}, {'$unset': {'picture_wait': ''}})
