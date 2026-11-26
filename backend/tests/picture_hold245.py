"""TEST-ONLY iteration 245 (Packet E, the remaining doors): a BUILT test that is switched on again is shown to students only after
every picture of it is proven in storage, all in one store. Until then it stays Off, remembers what was asked, says why on its row,
is tried again every 15 minutes and on "Dobara chalao", and never opens late.
A. healthy: Off -> Live / Scheduled / live exam as before; a typed test asks storage nothing.
B. a photo gone: only that test stays Off with the reason; another test of the same press goes Live; row, student, badge; Dobara chalao.
C. the 15-minute round; a proof whose server stopped midway; a proof another server is on; an old asking; Off ends the wait.
D. Off -> Scheduled not proven: no time is put on it; proven later: its chosen time; time passed meanwhile: never opens late.
E. Supabase away / project blocked / list refused: nothing is called missing, Supabase is not rested; Live by itself afterwards.
F. Library: back Live when proven; back Off with the reason when not; an Off test and a Draft come back as they were; a Scheduled one.
G. a PDF mock (built by the real book worker): gone, cut short, split between the stores; the book's "resume mock".
H. All India Test Series: a day's paper switched on again; a built paper without a day; a paper back from the Library.
I. the older switch (PATCH /admin/catalog/tests).   J. a verified JEE Main PYQ paper is never checked or held.
K. older doors: a paper import (schedule, Live again), a chapter book (publish, a chapter Live again), the old All India day, the automatic import.
L. one test's trouble stays with it: a proof that breaks, a slow proof (answer comes at once, Live by itself), two proofs at a time.
Supabase faked at the wire (tests/fake_supabase239.py), Emergent in memory, disposable DB, no network.
Run: cd /app/backend && python tests/picture_hold245.py
"""
import asyncio, hashlib, re, sys, time, types, uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from storage_book229 import H, J, BM, DB, S, RESULTS, check, mkstaff, cancel_kicks  # noqa: E402
from storage_stuck231 import live, item  # noqa: E402
from picture_gate239 import book, records, inner  # noqa: E402
import picture_gate239 as PG  # noqa: E402
from book_publishing_iso170 import client  # noqa: E402
from structure_iso173 import start  # noqa: E402
from structure_imports_iso174 import pdf_import, wait_import, iso  # noqa: E402
from written_live244 import written, key_of, press, one, why_of, doc, said  # noqa: E402
import httpx  # noqa: E402
from tejas import structure, library, picture_hold as HOLD  # noqa: E402
from tejas.live_series import IST  # noqa: E402
from fake_supabase239 import Leaky, LIST  # noqa: E402

M, LIB = '/api/admin/master', '/api/admin/library'
SETS, FILES = DB.tejas_sets, DB.tejas_files
NOT = 'Iski pictures storage mein saabit nahi hui, isliye yeh {} (Off hi hai). Wajah: '
NOT_LIVE, NOT_SCHEDULED, NOT_BACK = NOT.format('Live nahi hua'), NOT.format('Schedule nahi hua'), NOT.format('apni purani haalat mein nahi lauta')
GONE1, AGAIN = '1 picture storage me nahi mili', 'Har 15 minute mein apne aap phir jaanch hoti hai; abhi ke liye “Dobara chalao” dabaiye.'
OLD = 'Is test ki pictures storage mein saabit nahi hui, '


async def wait_of(id):
    return (await SETS.find_one({'id': id}, {'_id': 0, 'picture_wait': 1}) or {}).get('picture_wait') or {}


async def take(sb, fid):
    """TEST: this photo is no longer in Supabase (its record stays). Returns what puts it back."""
    key = await key_of(fid)
    return key, sb.objects.pop(key)


async def pics(id):
    """The photo ids of a test, read from its record (the editor does not open a test that is in the Library)."""
    s = await SETS.find_one({'id': id}, {'_id': 0, 'questions.q_refs': 1}) or {}
    return [r['file_id'] for q in s.get('questions') or [] for r in q.get('q_refs') or []]


async def off(own, id):
    return await press(own, 'off', [one('set', id)])


async def was_live(own, sec, title, photo_count=1, plain=1):
    """A written mock that was Live and is Off now: `plain` typed questions, then one question per photo."""
    wid = await written(own, sec, title, photos=photo_count, plain=plain)
    sc, d = await press(own, 'live', [one('set', wid)])
    assert d.get('done') == 1, d
    sc, d = await off(own, wid)
    assert d.get('done') == 1, d
    return wid


async def gone_photo(own, sb, sec, title):
    """...and its one photo (question 2) is gone from Supabase."""
    wid = await was_live(own, sec, title)
    key, raw = await take(sb, (await pics(wid))[0])
    return wid, key, raw


async def retry(own, id):
    r = await own.post(f'{M}/pictures/{id}/retry')
    return r.status_code, J(r)


async def seen(stu, slug, id):
    """Whether a student finds this test in the list of its type (every page of the list is looked at)."""
    structure._seen['at'] = -1e9
    for page in range(1, 9):
        rows = [x['id'] for x in J(await stu.get(f'/api/exam-navigation/{slug}/catalogue', params={'section': 'mock-tests', 'page': page})).get('items', [])]
        if id in rows or not rows:
            return id in rows
    return False


def clean(s):
    """Shown to students again: not Off, nothing waits."""
    return s.get('status') == 'published' and not s.get('owner_unlive') and 'picture_wait' not in s and not s.get('archived')


def held(s, to, state='stuck'):
    w = s.get('picture_wait') or {}
    return s.get('status') == 'published' and s.get('owner_unlive') is True and w.get('to') == to and w.get('state') == state and ('lease' in w) == (state == 'checking')


async def main():
    assert not H.leftover_real_handles()
    await H.tdbmod.indexes(); await structure.seed()
    sb = Leaky(S.TUS_CHUNK); PG.sb = sb
    wire = httpx.Client(transport=httpx.MockTransport(sb))
    S._client = lambda: wire                                                 # nothing leaves this process
    S.time = types.SimpleNamespace(time=time.time, sleep=lambda s: None)     # the storage code's own waits only
    S.STATE.update(down_until=0.0, strikes=0, last_error='', auth=None, bucket=None, failovers=0, last_failover=None, backup_since=None)
    real_prove = HOLD.prove
    try:
        own, owner_id = await mkstaff('owner', 'h245'); rev, _ = await mkstaff('reviewer', 'h245r'); anon = client()
        stu = client(); await stu.post('/api/auth/phone/signup', json={'phone': '93' + str(uuid.uuid4().int)[:8], 'pin': '8261', 'confirm_pin': '8261'})
        slug = J(await own.post('/api/admin/catalog/exams', json={'name': 'HLDX', 'short': 'HL', 'subjects': ['Physics'], 'color': 'rose'})).get('slug')
        sec = J(await own.post(f'/api/admin/catalog/exams/{slug}/sections', json={'name': 'Mock Tests', 'description': '', 'layout': 'list', 'kind': 'mocks'})).get('id')
        await structure.exams.update_one({'_id': slug}, {'$set': {'shown': True}})

        async def health_says():
            return [x for x in J(await own.get('/api/admin/storage/health')).get('reasons', []) if 'isliye woh Off hain' in x]

        # ---- A. Healthy.
        ok = await was_live(own, sec, 'H healthy', photo_count=2); n = len(sb.calls)
        sc, d = await press(own, 'live', [one('set', ok)])
        s, it = await doc(ok), await item(own, sec, ok)
        lists = sum(1 for _, _, p in sb.calls[n:] if p.startswith(LIST)); reads = sum(1 for m, _, p in sb.calls[n:] if m == 'GET' and f'/written/{ok}/' in p)
        check('A. Off -> Live with its photos in storage: Live at once, nothing waits, students see it', sc == 200 and d.get('done') == 1 and not d.get('skipped') and not d.get('checking')
              and clean(s) and it.get('status') == 'live' and 'pictures_wait' not in it and await seen(stu, slug, ok), (sc, d, s.get('owner_unlive'), s.get('picture_wait'), it.get('status')))
        check("A. ...Supabase's own list was asked once and each photo was read back from it", lists == 1 and reads >= 2, (lists, reads))
        check('A. ...its row says "Pictures: 2 / 2 · Storage: Supabase"', {k: (it.get('pictures') or {}).get(k) for k in ('proven', 'total', 'store')} == {'proven': 2, 'total': 2, 'store': 'supabase'}, it.get('pictures'))
        typed = await was_live(own, sec, 'H typed only', photo_count=0, plain=2); n = len(sb.calls)
        sc, d = await press(own, 'live', [one('set', typed)])
        check('A. a typed test (no picture) Off -> Live: Live, and storage is asked nothing', d.get('done') == 1 and clean(await doc(typed)) and len(sb.calls) == n, (d, sb.calls[n:]))
        at = time.time() + 86400
        await off(own, ok)
        sc, d = await press(own, 'scheduled', [one('set', ok)], at=at)
        s = await doc(ok)
        check('A. Off -> Scheduled with its photos in storage: Scheduled for the chosen time; students do not see it yet', d.get('done') == 1 and clean(s) and abs((s.get('start_at') or 0) - at) < 1
              and (await item(own, sec, ok)).get('status') == 'scheduled' and not await seen(stu, slug, ok), (d, s.get('start_at')))
        exam = await was_live(own, sec, 'H live exam', photo_count=1)
        sc, d = await press(own, 'scheduled', [one('set', exam)], at=at, live_exam=True)
        s = await doc(exam)
        check('A. Off -> Scheduled as a live exam: its 15-minute start window is set when it is proven', d.get('done') == 1 and clean(s) and s.get('competition') is True
              and abs((s.get('last_start_at') or 0) - (at + 900)) < 1, (d, s.get('competition'), s.get('last_start_at')))

        # ---- B. A photo that is not in storage any more.
        bad, key, raw = await gone_photo(own, sb, sec, 'H photo gone')
        other = await was_live(own, sec, 'H other of the same press')
        sc, d = await press(own, 'live', [one('set', bad), one('set', other)])
        s, it, w = await doc(bad), await item(own, sec, bad), await wait_of(bad)
        why = why_of(d)
        check('B. one press, the test with the gone photo first: a normal answer; only it is skipped, the other goes Live', sc == 200 and d.get('done') == 1 and [x['id'] for x in d.get('skipped', [])] == [bad]
              and clean(await doc(other)), (sc, d))
        check('B. the reason says it is still Off, names the question, the 15-minute retry and Dobara chalao', why == f'{NOT_LIVE}{GONE1} (Q2). {AGAIN}', why)
        check('B. the test stays Off and remembers what was asked', held(s, 'live') and w.get('kind') == 'proof' and not w.get('held') and w.get('by') == owner_id and not s.get('start_at'), (s.get('owner_unlive'), w))
        check('B. its row: Off, the same reason, no "Pictures" line', it.get('status') == 'off' and (it.get('pictures_wait') or {}).get('state') == 'stuck' and it['pictures_wait'].get('line') == why
              and it['pictures_wait'].get('to') == 'live' and 'pictures' not in it, it)
        r = await start(stu, bad)
        check('B. students do not see it and cannot start it', not await seen(stu, slug, bad) and r.status_code != 200, r.status_code)
        check('B. Supabase is NOT rested for everyone', S.supabase_on() and S.STATE['strikes'] == 0, S.STATE['strikes'])
        said_badge = await health_says()
        check('B. Badge: says one test is Off because its pictures were not proven', len(said_badge) == 1 and said_badge[0].startswith('1 test ki pictures storage mein saabit nahi hui'), said_badge)
        for who, cl, code in (('a visitor', anon, 401), ('a student', stu, 403), ('a reviewer', rev, 403)):
            r = await cl.post(f'{M}/pictures/{bad}/retry')
            check(f'B. {who} cannot press Dobara chalao ({code})', r.status_code == code, r.status_code)
        sc, r = await retry(own, bad)
        check('B. Dobara chalao while the photo is still gone: the same reason, still Off', sc == 200 and r.get('state') == 'stuck' and r.get('message') == why and held(await doc(bad), 'live'), (sc, r))
        check('B. the 15-minute round leaves a test alone that was tried a moment ago', await HOLD.resume() == [])
        sb.objects[key] = raw
        sc, r = await retry(own, bad)
        s, it = await doc(bad), await item(own, sec, bad)
        check('B. the photo is back + Dobara chalao: Live now, nothing waits, students see it', sc == 200 and r.get('state') == 'done' and r.get('message') == HOLD.DONE['live'] and clean(s)
              and it.get('status') == 'live' and 'pictures_wait' not in it and await seen(stu, slug, bad), (sc, r, s.get('picture_wait')))
        check('B. ...its row says "Pictures: 1 / 1" again and the badge no longer speaks of it', (it.get('pictures') or {}).get('proven') == 1 and not await health_says(), (it.get('pictures'), await health_says()))
        sc, r = await retry(own, bad)
        check('B. Dobara chalao on a test that does not wait: 404', sc == 404, sc)

        # ---- C. The 15-minute round, servers, and Off.
        auto, key, raw = await gone_photo(own, sb, sec, 'H tried again by itself')
        await press(own, 'live', [one('set', auto)])
        sb.objects[key] = raw
        await SETS.update_one({'id': auto}, {'$set': {'picture_wait.tried_at': time.time() - 900}})
        tasks = await HOLD.resume(); out = await HOLD.settle(tasks, 30)
        check('C. 15 minutes later the round proves it again by itself: Live, nobody pressed anything', len(tasks) == 1 and out == [('done', '')] and clean(await doc(auto)) and await seen(stu, slug, auto), (len(tasks), out))
        dead = await was_live(own, sec, 'H its server stopped midway')
        await SETS.update_one({'id': dead}, {'$set': {'picture_wait': {**HOLD.new_wait('live', owner_id), 'since': time.time() - 300, 'lease': time.time() - 5}}})
        tasks = await HOLD.resume(); out = await HOLD.settle(tasks, 30)
        check('C. a proof whose server stopped midway is picked up by the round: Live', len(tasks) == 1 and out == [('done', '')] and clean(await doc(dead)), (len(tasks), out))
        busy = await was_live(own, sec, 'H another server is on it')
        token = HOLD.new_wait('live', owner_id)
        await SETS.update_one({'id': busy}, {'$set': {'picture_wait': {**token, 'since': time.time() - 300, 'lease': time.time() + 500}}})
        check('C. a proof another server is running now is left alone (not started twice)', await HOLD.resume() == [] and await HOLD.check(busy, token['token']) == ('checking', '')
              and held(await doc(busy), 'live', 'checking'), await wait_of(busy))
        check('C. an older asking can no longer change the test', await HOLD.check(busy, 'not-its-token') == ('gone', '') and (await doc(busy)).get('owner_unlive') is True)
        sc, d = await off(own, busy)
        s, it = await doc(busy), await item(own, sec, busy)
        check('C. Off karo on a test that waits ends the wait: it is plainly Off', d.get('done') == 1 and s.get('owner_unlive') is True and 'picture_wait' not in s and it.get('status') == 'off' and 'pictures_wait' not in it, (d, s.get('picture_wait')))

        # ---- D. Off -> Scheduled.
        sch, key, raw = await gone_photo(own, sb, sec, 'H scheduled while a photo is gone')
        sc, d = await press(own, 'scheduled', [one('set', sch)], at=at)
        s, w = await doc(sch), await wait_of(sch)
        check('D. Off -> Scheduled, photo gone: not scheduled, still Off, no time is put on the test; the chosen time is remembered', d.get('done') == 0 and why_of(d) == f'{NOT_SCHEDULED}{GONE1} (Q2). {AGAIN}'
              and held(s, 'scheduled') and abs((w.get('at') or 0) - at) < 1 and not s.get('start_at'), (d, w, s.get('start_at')))
        sb.objects[key] = raw
        sc, r = await retry(own, sch)
        s = await doc(sch)
        check('D. the photo is back + Dobara chalao: Scheduled for the time that was chosen', r.get('state') == 'done' and r.get('message') == HOLD.DONE['scheduled'] and clean(s) and abs((s.get('start_at') or 0) - at) < 1
              and (await item(own, sec, sch)).get('status') == 'scheduled', (r, s.get('start_at')))
        late, key, raw = await gone_photo(own, sb, sec, 'H its time passed while it waited')
        await press(own, 'scheduled', [one('set', late)], at=time.time() + 3600)
        sb.objects[key] = raw
        await SETS.update_one({'id': late}, {'$set': {'picture_wait.at': time.time() - 5}})   # TEST: the chosen time went by while it waited
        sc, r = await retry(own, late)
        s, it = await doc(late), await item(own, sec, late)
        check('D. proven only after its chosen time: it does NOT open late; still Off, and says so', r.get('state') == 'missed' and 'der se apne aap nahi khulega' in r.get('message', '') and s.get('owner_unlive') is True
              and not s.get('start_at') and (s.get('picture_wait') or {}).get('state') == 'missed' and (it.get('pictures_wait') or {}).get('state') == 'missed' and it.get('status') == 'off'
              and not await seen(stu, slug, late), (r, s.get('picture_wait'), it.get('pictures_wait')))
        sc, r = await retry(own, late)
        check('D. ...it is not tried again by itself or by Dobara chalao', sc == 404 and await HOLD.resume() == [], sc)
        sc, d = await press(own, 'live', [one('set', late)])
        s = await doc(late)
        check('D. Live karo afterwards: Live now', d.get('done') == 1 and clean(s) and not s.get('start_at') and await seen(stu, slug, late), (d, s.get('picture_wait')))

        # ---- E. Supabase cannot be asked.
        aw = await was_live(own, sec, 'H while Supabase is away'); plain2 = await was_live(own, sec, 'H typed, same press', photo_count=0, plain=2)
        sb.down = True
        sc, d = await press(own, 'live', [one('set', aw), one('set', plain2)]); why = why_of(d)
        sb.down = False
        w = await wait_of(aw)
        check('E. Supabase away: the test stays Off and says it could not be checked; no photo is called missing; the typed test goes Live', sc == 200 and d.get('done') == 1 and [x['id'] for x in d.get('skipped', [])] == [aw]
              and why.startswith(NOT_LIVE + 'Abhi jaanch nahi ho saki (Supabase') and 'nahi mili' not in why and w.get('kind') == 'away' and held(await doc(aw), 'live'), (sc, d, w))
        check('E. Supabase is NOT rested for everyone by this', S.supabase_on() and S.STATE['strikes'] == 0, S.STATE['strikes'])
        await SETS.update_one({'id': aw}, {'$set': {'picture_wait.tried_at': time.time() - 900}})
        out = await HOLD.settle(await HOLD.resume(), 30)
        check('E. Supabase answers again: the round makes it Live by itself', out == [('done', '')] and clean(await doc(aw)), out)
        await off(own, aw)
        sb.block = (402, 'TEST: billing')
        sc, d = await press(own, 'live', [one('set', aw)]); why = why_of(d)
        sb.block = None
        check('E. Supabase project blocked (402): it says it is the billing block; still Off; Supabase is not rested', d.get('done') == 0
              and why.startswith(NOT_LIVE + 'Abhi jaanch nahi ho saki (Supabase project par billing ya usage ki rok hai (402))') and S.supabase_on(), d)
        sb.list_code = 400
        sc, r = await retry(own, aw)
        sb.list_code = None
        check('E. Supabase answers but does not give the list: it says so, no photo is called missing', r.get('state') == 'stuck' and 'Supabase ne is test ki pictures ki list nahi di (400)' in r.get('message', '')
              and 'nahi mili' not in r.get('message', ''), r)
        sc, r = await retry(own, aw)
        check('E. afterwards Dobara chalao makes it Live', r.get('state') == 'done' and clean(await doc(aw)), r)

        # ---- F. The Library.
        lb = await written(own, sec, 'H to the Library and back', photos=1)
        await press(own, 'live', [one('set', lb)]); await press(own, 'library', [one('set', lb)])
        r = await own.post(LIB + '/restore', json={'ids': [lb], 'uploads': []}); d = J(r)
        check('F. a Live test comes back from the Library with its photos proven: Live again at once', r.status_code == 200 and d.get('restored') == 1 and d.get('checking') == 0 and d.get('unproven') == []
              and clean(await doc(lb)) and await seen(stu, slug, lb), (r.status_code, d))
        await press(own, 'library', [one('set', lb)])
        key, raw = await take(sb, (await pics(lb))[0])
        r = await own.post(LIB + '/restore', json={'ids': [lb], 'uploads': []}); d = J(r)
        s, it, w = await doc(lb), await item(own, sec, lb), await wait_of(lb)
        why = (d.get('unproven') or [{}])[0].get('reason', '')
        check('F. it comes back while a photo is gone: back in its type but Off, and the answer says why', r.status_code == 200 and d.get('restored') == 1 and d.get('checking') == 0
              and [x['id'] for x in d.get('unproven', [])] == [lb] and why == f'{NOT_BACK}{GONE1} (Q2). {AGAIN}' and '1 test Off hain kyunki unki pictures storage mein saabit nahi hui' in d.get('message', ''), (r.status_code, d))
        check('F. ...it left the Library, is Off only for its proof, its row says why, students do not see it', not s.get('archived') and held(s, 'restore') and w.get('held') is True and it.get('status') == 'off'
              and (it.get('pictures_wait') or {}).get('line') == why and lb not in [x['id'] for x in J(await own.get(LIB)).get('items', [])] and not await seen(stu, slug, lb), (s.get('archived'), w, it.get('pictures_wait')))
        await press(own, 'library', [one('set', lb)])
        s = await doc(lb)
        check('F. sent to the Library again while it waits: nothing waits there, and it is not remembered as Off', s.get('archived') is True and 'picture_wait' not in s and not s.get('owner_unlive'), (s.get('owner_unlive'), s.get('picture_wait')))
        r = await own.post(LIB + '/restore', json={'ids': [lb], 'uploads': []})
        sb.objects[key] = raw
        sc, r = await retry(own, lb)
        check('F. restored again, the photo is back + Dobara chalao: it is as it was before the Library (Live)', r.get('state') == 'done' and r.get('message') == HOLD.DONE['restore'] and clean(await doc(lb))
              and await seen(stu, slug, lb), r)
        was_off, _, _ = await gone_photo(own, sb, sec, 'H was Off when it went to the Library')
        await press(own, 'library', [one('set', was_off)]); n = len(sb.calls)
        r = await own.post(LIB + '/restore', json={'ids': [was_off], 'uploads': []}); d = J(r); s = await doc(was_off)
        check('F. a test that was Off comes back Off as the owner left it; storage is asked nothing', d.get('restored') == 1 and d.get('unproven') == [] and d.get('checking') == 0 and s.get('owner_unlive') is True
              and 'picture_wait' not in s and not s.get('archived') and len(sb.calls) == n, (d, s.get('picture_wait'), sb.calls[n:]))
        draft = await written(own, sec, 'H a Draft in the Library', photos=1)
        await take(sb, (await pics(draft))[0])
        await press(own, 'library', [one('set', draft)]); n = len(sb.calls)
        r = await own.post(LIB + '/restore', json={'ids': [draft], 'uploads': []}); d = J(r); s = await doc(draft)
        check('F. a Draft comes back a Draft; storage is asked nothing', d.get('restored') == 1 and d.get('unproven') == [] and s.get('status') == 'draft' and 'picture_wait' not in s and not s.get('owner_unlive')
              and len(sb.calls) == n, (d, s.get('status'), s.get('picture_wait')))
        fut = await written(own, sec, 'H Scheduled, then the Library', photos=1)
        await press(own, 'scheduled', [one('set', fut)], at=at); await press(own, 'library', [one('set', fut)])
        key, raw = await take(sb, (await pics(fut))[0])
        r = await own.post(LIB + '/restore', json={'ids': [fut], 'uploads': []}); d = J(r); s, w = await doc(fut), await wait_of(fut)
        check('F. a Scheduled test comes back while a photo is gone: Off, its own time is kept and remembered', [x['id'] for x in d.get('unproven', [])] == [fut] and held(s, 'restore')
              and abs((s.get('start_at') or 0) - at) < 1 and abs((w.get('at') or 0) - at) < 1, (d, s.get('start_at'), w))
        sb.objects[key] = raw
        sc, r = await retry(own, fut); s = await doc(fut)
        check('F. the photo is back + Dobara chalao: Scheduled for its own time again', r.get('state') == 'done' and clean(s) and abs((s.get('start_at') or 0) - at) < 1
              and (await item(own, sec, fut)).get('status') == 'scheduled', (r, s.get('start_at')))

        # ---- G. A PDF mock, built by the real book worker.
        bid, mid, _ = await book(own, sec, 'hold_pdf')
        await live(own, mid)
        pdf = (await BM.find_one({'_id': mid}))['set_id']; recs = await records(bid)
        assert pdf and recs, (pdf, len(recs))
        await off(own, pdf); n = len(sb.calls)
        sc, d = await press(own, 'live', [one('set', pdf)])
        lists = sum(1 for _, _, p in sb.calls[n:] if p.startswith(LIST)); reads = sum(1 for m, _, p in sb.calls[n:] if m == 'GET' and '/crops/' in p)
        p = await DB.tejas_picture_proofs.find_one({'_id': pdf}) or {}
        check('G. a PDF mock Off -> Live: Live; Supabase\'s list was asked once and no picture had to be read back', d.get('done') == 1 and clean(await doc(pdf)) and lists == 1 and reads == 0
              and p.get('ok') is True and p.get('proven') == p.get('total') == len(recs), (d, lists, reads, p))
        await off(own, pdf)
        key = inner(recs[0]); raw = sb.objects.pop(key)
        sc, d = await press(own, 'live', [one('set', pdf)]); why = why_of(d)
        it = await item(own, sec, pdf)
        check('G. one picture of it gone: still Off, the question is named; its row drops the old "Pictures" line', d.get('done') == 0 and re.match(re.escape(NOT_LIVE + GONE1) + r' \(Q\d+', why) is not None
              and held(await doc(pdf), 'live') and 'pictures' not in it and (it.get('pictures_wait') or {}).get('state') == 'stuck', (d, it.get('pictures')))
        sb.objects[key] = raw[:-1]
        sc, r = await retry(own, pdf)
        check('G. the picture is there but a byte short: said as changed, still Off', r.get('state') == 'stuck' and '1 picture storage me badli hui mili (size ya fingerprint alag)' in r.get('message', ''), r)
        await off(own, pdf)
        check('G. Off karo after a proof that failed: the row does not go back to the old "Pictures: n / n"', 'pictures' not in await item(own, sec, pdf), (await item(own, sec, pdf)).get('pictures'))
        sb.objects[key] = raw
        sc, d = await press(own, 'live', [one('set', pdf)])
        check('G. the picture is whole again + Live karo: Live, students see it', d.get('done') == 1 and clean(await doc(pdf)) and await seen(stu, slug, pdf)
              and ((await item(own, sec, pdf)).get('pictures') or {}).get('proven') == len(recs), d)
        await off(own, pdf)
        old = key.split('/', 1)[1]
        H.STORE[old] = sb.objects[key]
        await FILES.update_one({'id': recs[0]['id']}, {'$set': {'path': old}})
        sc, d = await press(own, 'live', [one('set', pdf)]); why = why_of(d)
        check('G. one mock, one store: one picture in Emergent, the rest in Supabase: NOT Live, both counts are said', d.get('done') == 0
              and why.startswith(f'{NOT_LIVE}Pictures do storage me bati hain ({len(recs) - 1} Supabase me, 1 Emergent me)') and held(await doc(pdf), 'live'), d)
        await FILES.update_one({'id': recs[0]['id']}, {'$set': {'path': recs[0]['path']}})
        sc, r = await retry(own, pdf)
        check('G. all in one store again + Dobara chalao: Live', r.get('state') == 'done' and clean(await doc(pdf)), r)

        async def control(action):
            view = J(await own.get(f'/api/admin/books/{bid}'))
            return await own.post(f'/api/admin/books/{bid}/control', json={'revision': view['revision'], 'action': action, 'mock_id': mid, 'reason': 'TEST ' + action})
        r = await control('pause_mock')
        s = await SETS.find_one({'id': pdf}, {'_id': 0, 'questions': 0})
        assert r.status_code == 200 and s['status'] == 'withdrawn', (r.status_code, r.text[:200], s['status'])
        raw = sb.objects.pop(key)
        r = await control('resume_mock')
        s, mk = await SETS.find_one({'id': pdf}, {'_id': 0, 'questions': 0}), await BM.find_one({'_id': mid})
        check('G. the book\'s "resume mock" while a picture is gone: refused with the reason; the mock stays paused', r.status_code == 409 and said(r).startswith(f'{OLD}isliye yeh mock dobara Live nahi hua (paused hi hai). Wajah: {GONE1} (Q')
              and s['status'] == 'withdrawn' and s.get('live_enabled') is False and mk['state'] == 'paused', (r.status_code, r.text[:300], s['status'], mk['state']))
        sb.objects[key] = raw
        r = await control('resume_mock')
        s = await SETS.find_one({'id': pdf}, {'_id': 0, 'questions': 0})
        check('G. the picture is back: "resume mock" works as before', r.status_code == 200 and s['status'] == 'published' and s.get('live_enabled') is True, (r.status_code, r.text[:200], s['status']))

        # ---- H. All India Test Series.
        first = datetime.now(IST).date() + timedelta(days=2)
        days = [(first + timedelta(days=i)).isoformat() for i in range(4)]
        made = J(await own.post(f'/api/admin/catalog/exams/{slug}/sections', json={'name': 'All India Test Series', 'description': '', 'layout': 'list', 'kind': 'aits',
                 'first_date': days[0], 'days': 4, 'open_time': '09:00', 'last_start': '11:00', 'minutes': 10, 'correct': 4, 'wrong': -1}))
        ser, sid = made.get('id'), made.get('series_id')
        await own.put(f'{M}/series/{sid}', json={'shown': True})

        async def day_of(day, public=False):
            d = J(await own.get(f'/api/series/{sid}/schedule' if public else f'{M}/series/{sid}'))
            return next((x for x in d.get('slots', []) if x['date'] == day), {})

        async def series_live(id, on):
            return await own.post(f'{M}/series/{sid}/live', json={'id': id, 'live': on})
        sp = await written(own, ser, 'H series paper', photos=1)
        r = await own.post(f'{M}/series/{sid}/assign', json={'kind': 'written', 'id': sp, 'date': days[0]})
        assert r.status_code == 200, r.text[:300]
        await series_live(sp, False)
        r = await series_live(sp, True)
        check("H. a day's paper Off -> Live with its photo in storage: Live again", r.status_code == 200 and J(r).get('message') == 'Live again. Students see it on its day.' and clean(await doc(sp))
              and (await day_of(days[0], True)).get('set_id') == sp, (r.status_code, r.text[:200]))
        await series_live(sp, False)
        key, raw = await take(sb, (await pics(sp))[0])
        r = await series_live(sp, True)
        s, w, slot = await doc(sp), await wait_of(sp), await day_of(days[0])
        check("H. a day's paper Off -> Live while its photo is gone: refused with the reason (not an error page); it stays Off", r.status_code == 409 and said(r) == f'{NOT_LIVE}{GONE1} (Q2). {AGAIN}'
              and held(s, 'on') and s.get('series_date') == days[0] and abs((w.get('at') or 0) - s.get('start_at', 0)) < 1, (r.status_code, r.text[:300], w))
        check('H. Master: the day keeps its paper, shows it Off and why; students (and the owner looking as one) get no paper that day', (slot.get('paper') or {}).get('off') is True
              and ((slot.get('paper') or {}).get('pictures_wait') or {}).get('state') == 'stuck' and (await day_of(days[0], True)).get('set_id') is None, slot.get('paper'))
        sb.objects[key] = raw
        sc, r = await retry(own, sp)
        slot = await day_of(days[0])
        check("H. the photo is back + Dobara chalao: the day's paper is Live again", r.get('state') == 'done' and r.get('message') == HOLD.DONE['on'] and clean(await doc(sp)) and (slot.get('paper') or {}).get('off') is False
              and 'pictures_wait' not in slot['paper'] and (await day_of(days[0], True)).get('set_id') == sp, (r, slot.get('paper')))
        r = await own.post(f'{M}/series/{sid}/unassign', json={'kind': 'set', 'id': sp})
        assert r.status_code == 200 and not (await doc(sp)).get('series_date'), r.text[:300]
        key, raw = await take(sb, (await pics(sp))[0])
        r = await own.post(f'{M}/series/{sid}/assign', json={'kind': 'set', 'id': sp, 'date': days[1]})
        check('H. a built paper without a day, its photo gone: it does NOT take a day; the reason is given', r.status_code == 409 and said(r) == f'{OLD}isliye is paper ko din nahi mila. Wajah: {GONE1} (Q2).'
              and not (await doc(sp)).get('series_date') and (await day_of(days[1])).get('paper') is None, (r.status_code, r.text[:300]))
        sb.down = True
        r = await own.post(f'{M}/series/{sid}/assign', json={'kind': 'set', 'id': sp, 'date': days[1]})
        sb.down = False
        check('H. Supabase away when the day is given: refused, it says it could not be checked; no day is taken', r.status_code == 409 and said(r).startswith('Is test ki pictures abhi jaanchi nahi ja saki (Supabase')
              and 'isliye is paper ko din nahi mila' in said(r) and not (await doc(sp)).get('series_date') and S.supabase_on(), (r.status_code, r.text[:300]))
        sb.objects[key] = raw
        r = await own.post(f'{M}/series/{sid}/assign', json={'kind': 'set', 'id': sp, 'date': days[1]})
        check('H. the photo is back: the built paper takes its day', r.status_code == 200 and (await doc(sp)).get('series_date') == days[1] and (await day_of(days[1], True)).get('set_id') == sp, (r.status_code, r.text[:200]))
        await library.clear_series(owner_id, 'TEST: series paper to the Library', [sp])
        key, raw = await take(sb, (await pics(sp))[0])
        r = await own.post(LIB + '/restore', json={'ids': [sp], 'uploads': []}); d = J(r); s, w = await doc(sp), await wait_of(sp)
        check('H. a series paper back from the Library while its photo is gone: back on its day but Off, with the reason', d.get('restored') == 1 and d.get('without_day') == 0 and [x['id'] for x in d.get('unproven', [])] == [sp]
              and held(s, 'restore') and s.get('series_date') == days[1] and w.get('held') is True and (await day_of(days[1], True)).get('set_id') is None, (d, s.get('series_date'), w))
        sb.objects[key] = raw
        sc, r = await retry(own, sp)
        check('H. the photo is back + Dobara chalao: the paper is on its day for students again', r.get('state') == 'done' and clean(await doc(sp)) and (await day_of(days[1], True)).get('set_id') == sp, r)

        # ---- I. The older switch.
        async def flip(id, on):
            r = await own.patch(f'/api/admin/catalog/tests/{id}', json={'live': on})
            return r.status_code, J(r)
        pt = await was_live(own, sec, 'H the older switch')
        sc, d = await flip(pt, True)
        check('I. the older Live switch, photo in storage: Live, as before', sc == 200 and d.get('state') == 'live' and 'pictures' not in d and clean(await doc(pt)), (sc, d))
        await flip(pt, False)
        key, raw = await take(sb, (await pics(pt))[0])
        sc, d = await flip(pt, True)
        check('I. the older Live switch, photo gone: a normal answer; still Off; the note says why', sc == 200 and d.get('state') == 'unlive' and d.get('pictures') == 'stuck'
              and d.get('note') == f'{NOT_LIVE}{GONE1} (Q2). {AGAIN}' and held(await doc(pt), 'on'), (sc, d))
        sc, d = await flip(pt, False)
        s = await doc(pt)
        check('I. the older switch Off ends the wait', d.get('state') == 'unlive' and s.get('owner_unlive') is True and 'picture_wait' not in s, (d, s.get('picture_wait')))
        sb.objects[key] = raw
        sc, d = await flip(pt, True)
        check('I. the photo is back + the older switch: Live', d.get('state') == 'live' and 'pictures' not in d and clean(await doc(pt)), d)

        # ---- J. A verified JEE Main PYQ paper is never checked or held.
        pyq = 'TEST_H245_pyq_' + uuid.uuid4().hex[:6]
        refs = [{'id': str(uuid.uuid4()), 'number': 1, 'type': 'mcq', 'subject': 'Physics', 'section': 'A', 'options': {'A': 'a', 'B': 'b', 'C': 'c', 'D': 'd'}, 'answer': 'A', 'text': 'q',
                 'q_refs': [{'file_id': 'no-such-picture'}], 's_refs': []}]
        paper = {'id': pyq, 'status': 'published', 'audience': 'all', 'title': 'TEST H245 PYQ', 'version': 1, 'revision': 1, 'created_at': time.time(), 'questions': refs, 'exam': 'JEE Main',
                 'rules': {'minutes': 180, 'correct': 4, 'wrong': -1, 'skipped': 0}, 'test_kind': 'pyq', 'catalog_section_id': 'jee-main:pyq', 'pyq_date': '2024-01-27', 'owner_unlive': True}
        await SETS.insert_one(dict(paper)); n = len(sb.calls)
        sc, d = await press(own, 'live', [one('set', pyq)])
        s = await doc(pyq)
        check('J. a verified PYQ paper Off -> Live: Live at once; storage is asked nothing; nothing waits', sc == 200 and d.get('done') == 1 and not s.get('owner_unlive') and 'picture_wait' not in s and len(sb.calls) == n, (d, sb.calls[n:]))
        await off(own, pyq)
        sc, d = await flip(pyq, True)
        check('J. ...the same by the older switch', d.get('state') == 'live' and 'pictures' not in d and len(sb.calls) == n and not (await doc(pyq)).get('owner_unlive'), d)
        check('J. ...and by the older doors', HOLD.needed(paper) is False and await HOLD.refusal(paper, 'x') is None and len(sb.calls) == n)
        check('J. a PYQ paper the owner typed in Master is checked like any other', (await HOLD.refusal({**paper, 'master_pyq': True}, 'isliye yeh Live nahi hua') or '') == f'{OLD}isliye yeh Live nahi hua. Wajah: {GONE1} (Q1).',
              await HOLD.refusal({**paper, 'master_pyq': True}, 'isliye yeh Live nahi hua'))

        # ---- K. Older doors: a paper import and a chapter book.
        r = await pdf_import(own, 'BITSAT Practice Paper', 'PH245', 'bitsat:mocks'); iid = (r.json() or {}).get('id')
        v = await wait_import(own, iid)
        keys = sorted(k for k in sb.objects if f'/imports/{iid}/renders/' in k)
        assert v.get('status') == 'ready' and keys, (v.get('status'), v.get('message'), len(keys))
        when = iso(datetime.now(timezone.utc) + timedelta(minutes=30))
        raw = sb.objects.pop(keys[0])
        r = await own.post(f'/api/studio/imports/{iid}/schedule', json={'start_at': when, 'revision': 0})
        check('K. a paper import scheduled while a picture of it is gone: refused with the reason; no test is made', r.status_code == 409 and f'{OLD}isliye yeh Schedule nahi hua. Wajah: {GONE1} (Q' in r.text
              and not await SETS.count_documents({'id': iid}), (r.status_code, r.text[:300]))
        sb.objects[keys[0]] = raw
        r = await own.post(f'/api/studio/imports/{iid}/schedule', json={'start_at': when, 'revision': 0})
        s = await SETS.find_one({'id': iid}, {'_id': 0, 'questions': 0}) or {}
        check('K. the picture is back: the import is scheduled as before', r.status_code == 200 and s.get('status') == 'published' and s.get('live_enabled') is True, (r.status_code, r.text[:300]))

        async def import_live(on):
            rev_now = (await SETS.find_one({'id': iid}, {'revision': 1}))['revision']
            return await own.post(f'/api/studio/imports/{iid}/live', json={'live': on, 'revision': rev_now})
        r = await import_live(False)
        assert r.status_code == 200, r.text[:300]
        raw = sb.objects.pop(keys[0])
        r = await import_live(True)
        s = await SETS.find_one({'id': iid}, {'_id': 0, 'questions': 0})
        check('K. the import switched on again while a picture is gone: refused; it stays as it was (not shown)', r.status_code == 409 and f'{OLD}isliye yeh Live nahi hua. Wajah: {GONE1} (Q' in r.text
              and s['status'] == 'withdrawn' and s.get('live_enabled') is False, (r.status_code, r.text[:300], s['status']))
        sb.objects[keys[0]] = raw
        r = await import_live(True)
        s = await SETS.find_one({'id': iid}, {'_id': 0, 'questions': 0})
        check('K. the picture is back: switched on as before', r.status_code == 200 and s['status'] == 'published' and s.get('live_enabled') is True, (r.status_code, r.text[:300]))

        cb, fid, csid, t = str(uuid.uuid4()), str(uuid.uuid4()), str(uuid.uuid4()), time.time()
        pdf_raw = b'%PDF-1.4 TEST chapter book ' + uuid.uuid4().hex.encode()
        ckey = f'{S.bucket_name()}/tejas/chapter-books/{cb}/{fid}.pdf'
        source = {'id': fid, 'path': S.SB + ckey, 'sha256': hashlib.sha256(pdf_raw).hexdigest(), 'kind': 'combined', 'name': 'TEST.pdf', 'size': len(pdf_raw), 'set_id': cb, 'created_at': t, 'is_deleted': False}
        await FILES.insert_one(dict(source))
        await DB.tejas_chapter_books.insert_one({'id': cb, 'title': 'TEST H245 chapter book', 'source': source, 'status': 'ready', 'revision': 1, 'created_at': t, 'created_by': owner_id, 'subject': 'Physics'})
        fifty = [{'id': str(uuid.uuid4()), 'number': i, 'type': 'mcq', 'subject': 'Physics', 'options': {'A': 'a', 'B': 'b', 'C': 'c', 'D': 'd'}, 'answer': 'A', 'text': f'cq{i}',
                  'q_refs': [{'file_id': fid, 'page': 1, 'rect': [0, 0, 10, 10]}], 's_refs': []} for i in range(1, 51)]
        await SETS.insert_one({'id': csid, 'chapter_book_id': cb, 'chapter_number': 1, 'chapter_subject': 'Physics', 'title': 'TEST H245 Units', 'exam': 'BITSAT', 'test_kind': 'chapter', 'year': '',
                               'questions': fifty, 'file_ids': [fid], 'rules': {'minutes': 60, 'correct': 3, 'wrong': -1, 'skipped': 0}, 'status': 'draft', 'version': 1, 'revision': 1, 'created_at': t,
                               'audience': 'all', 'competition': False, 'live_enabled': False, 'solution_kind': 'answer_key_only', 'verification': {'key_checks_agree': True},
                               'independent_check': {'status': 'PASS'}, 'start_page': 1, 'end_page': 2, 'key_page': 3, 'catalog_section_id': 'bitsat:chapters'})
        r = await own.post(f'/api/studio/chapter-books/{cb}/publish', json={'revision': 1})
        s = await SETS.find_one({'id': csid}, {'_id': 0, 'questions': 0})
        check('K. a chapter book published while its file is not in storage: refused with the reason; nothing is published', r.status_code == 409 and f'{OLD}isliye yeh chapter book Live nahi hui. Wajah: {GONE1}.' in r.text
              and s['status'] == 'draft' and not s.get('start_at'), (r.status_code, r.text[:300], s['status']))
        sb.objects[ckey] = pdf_raw
        r = await own.post(f'/api/studio/chapter-books/{cb}/publish', json={'revision': 1})
        s = await SETS.find_one({'id': csid}, {'_id': 0, 'questions': 0})
        check('K. its file is in storage: the chapter book is published as before', r.status_code == 200 and s['status'] == 'published' and s.get('live_enabled') is True and s.get('start_at'), (r.status_code, r.text[:300], s['status']))

        async def chapter_live(on):
            rev_now = (await SETS.find_one({'id': csid}, {'revision': 1}))['revision']
            return await own.post(f'/api/studio/chapter-books/{cb}/chapters/{csid}/live', json={'revision': rev_now, 'live': on})
        r = await chapter_live(False)
        assert r.status_code == 200, r.text[:300]
        sb.objects.pop(ckey)
        r = await chapter_live(True)
        s = await SETS.find_one({'id': csid}, {'_id': 0, 'questions': 0})
        check('K. a chapter switched on again while its file is gone: refused; it stays Unlive', r.status_code == 409 and f'{OLD}isliye yeh Live nahi hua. Wajah: {GONE1} (Q1, ' in r.text and 'aur baaki' in r.text
              and s.get('live_enabled') is False, (r.status_code, r.text[:300], s.get('live_enabled')))
        sb.objects[ckey] = pdf_raw
        r = await chapter_live(True)
        check('K. its file is back: the chapter is switched on as before', r.status_code == 200 and (await SETS.find_one({'id': csid}, {'live_enabled': 1}))['live_enabled'] is True, (r.status_code, r.text[:300]))

        # The old All India door (Studio): a built paper without a day is asked the same question before it takes a day.
        from tejas import live_series as LS, smart_imports as SI
        src = await written(own, sec, 'H photo for the older doors', photos=1); afid = (await pics(src))[0]

        def old_paper(fid):
            return {'id': 'TEST_H245_old_' + uuid.uuid4().hex[:6], 'status': 'published', 'series_import': True, 'audience': 'all', 'exam': 'JEE Main',
                    'questions': [{'number': 1, 'q_refs': [{'file_id': fid}], 's_refs': []}], 'rules': {'minutes': 10, 'correct': 4, 'wrong': -1},
                    'series_pattern': {'count': 1, 'minutes': 10, 'correct': 4, 'wrong': -1}}
        far = (datetime.now(IST).date() + timedelta(days=9)).isoformat()
        why = await LS.set_problem(old_paper('no-such-picture'), far)
        check('K. the old All India door: a built paper without a day whose picture is gone gets no day; the reason is given', why == f'{OLD}isliye is paper ko din nahi mila. Wajah: {GONE1} (Q1).', why)
        why = await LS.set_problem(old_paper(afid), far)
        check('K. ...its picture is in storage: nothing stands in its way', why is None, why)

        # The automatic import: a paper that is published by itself stays private when a picture of it is not proven.
        aid, pid, qid, sol = (str(uuid.uuid4()) for _ in range(4))
        record = {'id': aid, 'owner_id': owner_id, 'filename': 'TEST.pdf', 'publish_when_ready': True}
        paper = {'id': pid, 'import_id': aid, 'state': 'solving', 'rules': {'title': 'TEST H245 automatic paper', 'exam': 'BITSAT', 'test_kind': 'practice', 'subject': 'Physics',
                 'duration_minutes': 10, 'expected_questions': 1, 'correct': 3, 'wrong': -1, 'skipped': 0, 'sections': []}}
        await DB.tejas_smart_papers.insert_one(dict(paper))
        await DB.tejas_ai_solutions.insert_one({'id': sol, 'state': 'verified', 'answer': 'A', 'steps': [{'title': 'Step', 'explanation': 'because'}], 'provenance': {'model': 'TEST'}})
        await DB.tejas_smart_questions.insert_one({'id': qid, 'import_id': aid, 'paper_id': pid, 'state': 'verified', 'solution_id': sol, 'original_number': 1, 'source_page': 1,
            'question': {'id': qid, 'type': 'mcq', 'subject': 'Physics', 'text': 'TEST automatic question', 'options': {'A': 'a', 'B': 'b'}, 'q_refs': [{'file_id': afid}], 's_refs': []}})
        key, raw = await take(sb, afid)
        try:
            await SI.finalize_paper(record, paper); out = None
        except ValueError as exc:
            out = str(exc)
        s = await SETS.find_one({'id': pid}, {'_id': 0, 'questions': 0}) or {}
        check('K. the automatic import, its picture gone: not published, the reason is given; the paper stays private', out == f'{OLD}isliye yeh Live nahi hua. Wajah: {GONE1} (Q1).' and s.get('status') == 'draft', (out, s.get('status')))
        sb.objects[key] = raw
        await SI.finalize_paper(record, paper)
        s = await SETS.find_one({'id': pid}, {'_id': 0, 'questions': 0}) or {}
        check('K. ...its picture is in storage: published as before', s.get('status') == 'published' and (await DB.tejas_smart_papers.find_one({'id': pid}) or {}).get('state') == 'live', s.get('status'))

        # ---- L. One test's trouble stays with that test.
        async def broke(*args, **kw):
            raise RuntimeError('TEST: the proof itself broke')
        br = await was_live(own, sec, 'H its proof breaks'); plain3 = await was_live(own, sec, 'H typed beside it', photo_count=0, plain=2)
        HOLD.prove = broke
        sc, d = await press(own, 'live', [one('set', br), one('set', plain3)]); why = why_of(d)
        HOLD.prove = real_prove
        w = await wait_of(br)
        check('L. a proof that breaks midway: a normal answer; only that test stays Off and says so; the other goes Live', sc == 200 and d.get('done') == 1 and [x['id'] for x in d.get('skipped', [])] == [br]
              and why.startswith(NOT_LIVE + 'Jaanch beech mein ruk gayi') and w.get('kind') == 'other' and held(await doc(br), 'live') and clean(await doc(plain3)), (sc, d, w))
        sc, r = await retry(own, br)
        check('L. ...Dobara chalao afterwards: Live', r.get('state') == 'done' and clean(await doc(br)), r)

        async def slow(s, full=False, alive=None):
            await asyncio.sleep(1.2)
            return await real_prove(s, full, alive)
        sl = await was_live(own, sec, 'H its proof takes long')
        HOLD.prove, HOLD.WAIT = slow, .3
        began = time.time()
        sc, d = await press(own, 'live', [one('set', sl)])
        took = time.time() - began
        s, it = await doc(sl), await item(own, sec, sl)
        check('L. a proof that takes long: the answer comes at once and says the pictures are being checked; the test is Off meanwhile', sc == 200 and took < 1.1 and d.get('done') == 0 and d.get('checking') == 1
              and not d.get('skipped') and 'pictures storage mein jaanchi ja rahi hain' in d.get('note', '') and held(s, 'live', 'checking') and it.get('status') == 'off'
              and (it.get('pictures_wait') or {}).get('state') == 'checking' and not await seen(stu, slug, sl), (sc, round(took, 2), d, s.get('picture_wait')))
        await asyncio.gather(*list(HOLD._tasks))
        HOLD.prove, HOLD.WAIT = real_prove, 6
        check('L. ...once proven it is Live by itself', clean(await doc(sl)) and (await item(own, sec, sl)).get('status') == 'live' and await seen(stu, slug, sl), await wait_of(sl))
        at_once = {'now': 0, 'most': 0}

        async def counted(s, full=False, alive=None):
            at_once['now'] += 1; at_once['most'] = max(at_once['most'], at_once['now'])
            await asyncio.sleep(.25)
            try:
                return await real_prove(s, full, alive)
            finally:
                at_once['now'] -= 1
        four = [await was_live(own, sec, f'H one of four {i}') for i in range(4)]
        HOLD.prove = counted
        sc, d = await press(own, 'live', [one('set', x) for x in four])
        HOLD.prove = real_prove
        check('L. four tests switched on in one press: all four go Live, and never more than two are proven at a time', d.get('done') == 4 and not d.get('skipped') and at_once['most'] == 2
              and all([clean(await doc(x)) for x in four]), (d, at_once))
        check('nothing of this run waits on this server any more', not HOLD._tasks and not HOLD._busy, (len(HOLD._tasks), len(HOLD._busy)))
    finally:
        HOLD.prove, HOLD.WAIT = real_prove, 6
        cancel_kicks()
        assert H.TEST_DB.startswith('tejas_isolated_') and H.TEST_DB != H.REAL_DB
        await H.tdbmod.client.drop_database(H.TEST_DB)
        print('dropped', H.TEST_DB)
    print(f'TOTAL {len(RESULTS)} PASS {sum(RESULTS)} FAIL {len(RESULTS) - sum(RESULTS)}')


if __name__ == '__main__':
    asyncio.run(main())
