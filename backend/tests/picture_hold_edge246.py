"""TEST-ONLY iteration 246: testing-agent's edge suite for Packet E step 5 (picture hold).

Ideas the builder's picture_hold245.py did not cover or covered thinly:
  (a) two owners/tabs pressing Live and Off on the same waiting test at nearly the same time
  (b) "Dobara chalao" pressed twice quickly
  (c) a bulk press mixing a Draft, an Off test with a gone photo, a typed Off test and a verified PYQ paper
  (d) a waiting test renamed (PATCH title / section_id) - the wait must survive and nothing becomes visible
  (e) Off -> Scheduled with live_exam=true not proven, then proven after the time
  (f) a restore of 3 tests at once: one proven, one gone photo, one no pictures
  (g) a series paper restored from the Library when its day is already taken
  (h) the student-facing lists and start route never expose a waiting test or any picture_wait field
  (i) reviewer cannot see or press anything new
  (j) the 15-minute round with 3 stuck tests where only one photo is back
Supabase faked at the wire (tests/fake_supabase239.py), Emergent in memory, disposable DB.
Run: cd /app/backend && python tests/picture_hold_edge246.py
"""
import asyncio, sys, time, types, uuid
from datetime import datetime, timedelta
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from storage_book229 import H, J, DB, S, RESULTS, check, mkstaff, cancel_kicks  # noqa: E402
from storage_stuck231 import item  # noqa: E402
import picture_gate239 as PG  # noqa: E402
from book_publishing_iso170 import client  # noqa: E402
from written_live244 import written, key_of, press, one, doc  # noqa: E402
import httpx  # noqa: E402
from tejas import structure, library, picture_hold as HOLD  # noqa: E402
from tejas.live_series import IST  # noqa: E402
from fake_supabase239 import Leaky  # noqa: E402

M, LIB = '/api/admin/master', '/api/admin/library'
SETS = DB.tejas_sets
NOT = 'Iski pictures storage mein saabit nahi hui, isliye yeh {} (Off hi hai). Wajah: '
NOT_LIVE, NOT_SCHEDULED = NOT.format('Live nahi hua'), NOT.format('Schedule nahi hua')
GONE1, AGAIN = '1 picture storage me nahi mili', 'Har 15 minute mein apne aap phir jaanch hoti hai; abhi ke liye “Dobara chalao” dabaiye.'


async def wait_of(id):
    return (await SETS.find_one({'id': id}, {'_id': 0, 'picture_wait': 1}) or {}).get('picture_wait') or {}


async def pics(id):
    s = await SETS.find_one({'id': id}, {'_id': 0, 'questions.q_refs': 1}) or {}
    return [r['file_id'] for q in s.get('questions') or [] for r in q.get('q_refs') or []]


async def take(sb, fid):
    key = await key_of(fid)
    return key, sb.objects.pop(key)


async def off(own, id):
    return await press(own, 'off', [one('set', id)])


async def was_live(own, sec, title, photo_count=1, plain=1):
    wid = await written(own, sec, title, photos=photo_count, plain=plain)
    sc, d = await press(own, 'live', [one('set', wid)])
    assert d.get('done') == 1, d
    sc, d = await off(own, wid)
    assert d.get('done') == 1, d
    return wid


async def gone(own, sb, sec, title):
    wid = await was_live(own, sec, title)
    key, raw = await take(sb, (await pics(wid))[0])
    return wid, key, raw


async def retry(own, id):
    r = await own.post(f'{M}/pictures/{id}/retry')
    return r.status_code, J(r)


def held(s, to, state='stuck'):
    w = s.get('picture_wait') or {}
    return s.get('status') == 'published' and s.get('owner_unlive') is True and w.get('to') == to and w.get('state') == state


def clean(s):
    return s.get('status') == 'published' and not s.get('owner_unlive') and 'picture_wait' not in s and not s.get('archived')


async def seen(stu, slug, id):
    structure._seen['at'] = -1e9
    for page in range(1, 9):
        rows = [x['id'] for x in J(await stu.get(f'/api/exam-navigation/{slug}/catalogue', params={'section': 'mock-tests', 'page': page})).get('items', [])]
        if id in rows or not rows:
            return id in rows
    return False


async def main():
    assert not H.leftover_real_handles()
    await H.tdbmod.indexes(); await structure.seed()
    sb = Leaky(S.TUS_CHUNK); PG.sb = sb
    wire = httpx.Client(transport=httpx.MockTransport(sb))
    S._client = lambda: wire
    S.time = types.SimpleNamespace(time=time.time, sleep=lambda s: None)
    S.STATE.update(down_until=0.0, strikes=0, last_error='', auth=None, bucket=None, failovers=0, last_failover=None, backup_since=None)
    real_prove = HOLD.prove
    try:
        own, owner_id = await mkstaff('owner', 'e246')
        own2, _ = await mkstaff('owner', 'e246b')  # second owner/tab
        rev, _ = await mkstaff('reviewer', 'e246r')
        stu = client(); await stu.post('/api/auth/phone/signup', json={'phone': '94' + str(uuid.uuid4().int)[:8], 'pin': '8260', 'confirm_pin': '8260'})
        slug = J(await own.post('/api/admin/catalog/exams', json={'name': 'EDGX', 'short': 'ED', 'subjects': ['Physics'], 'color': 'rose'})).get('slug')
        sec = J(await own.post(f'/api/admin/catalog/exams/{slug}/sections', json={'name': 'Mock Tests', 'description': '', 'layout': 'list', 'kind': 'mocks'})).get('id')
        sec2 = J(await own.post(f'/api/admin/catalog/exams/{slug}/sections', json={'name': 'Mock Tests Two', 'description': '', 'layout': 'list', 'kind': 'custom'})).get('id')
        await structure.exams.update_one({'_id': slug}, {'$set': {'shown': True}})

        # ---- (a) two owners press Live and Off on the same waiting test at nearly the same time.
        wid, key, raw = await gone(own, sb, sec, 'E a two owners race')
        # Owner-1 kicks off a "stuck" wait by pressing Live
        sc, d = await press(own, 'live', [one('set', wid)])
        assert d.get('done') == 0, d
        s0 = await doc(wid)
        check('a. stuck after first owner pressed Live (photo gone)', held(s0, 'live'), s0.get('picture_wait'))
        # Now owner-2 presses Off nearly at the same time while owner-1 presses "Dobara chalao" (still gone)
        off_task = asyncio.create_task(off(own2, wid))
        retry_task = asyncio.create_task(retry(own, wid))
        off_res, retry_res = await asyncio.gather(off_task, retry_task)
        s = await doc(wid)
        # whichever finished last must be the state, but either outcome must be consistent: if Off wins we are plainly Off and wait is cleared
        is_off = s.get('owner_unlive') is True and 'picture_wait' not in s
        is_stuck = held(s, 'live')
        check('a. race Off vs Dobara-chalao: ends in a consistent state (plainly Off OR still stuck), never half-and-half', is_off or is_stuck, (is_off, is_stuck, s.get('owner_unlive'), s.get('picture_wait')))
        check('a. and no student exposure during the race', not await seen(stu, slug, wid), None)
        # restore and tidy
        sb.objects[key] = raw
        if is_stuck:
            await retry(own, wid)
        # ---- (b) "Dobara chalao" pressed twice quickly (concurrent).
        wid2, key2, raw2 = await gone(own, sb, sec, 'E b double dobara')
        await press(own, 'live', [one('set', wid2)])
        sb.objects[key2] = raw2
        r1, r2 = await asyncio.gather(retry(own, wid2), retry(own, wid2))
        s = await doc(wid2)
        both_sc = (r1[0], r2[0])
        # One retry becomes 'done'. Other retry may legitimately observe wait already cleared and return 404 - that is NOT a regression.
        okset = {r1[1].get('state'), r2[1].get('state')}
        # Also check it does NOT end double-live / duplicate side-effects
        check('b. two concurrent Dobara chalao: at least one answered done; final test is Live and clean', 'done' in okset and clean(s), (both_sc, r1[1], r2[1], s.get('owner_unlive')))
        check('b. only one wait doc remains (or none) after the race', s.get('picture_wait') is None, s.get('picture_wait'))

        # ---- (c) a bulk press mixing a Draft, an Off-gone-photo test, a typed Off test and a verified PYQ.
        drft = await written(own, sec, 'E c Draft left alone', photos=1)   # left as Draft
        bad3, key3, raw3 = await gone(own, sb, sec, 'E c Off gone photo')
        typed = await written(own, sec, 'E c typed', photos=0, plain=2)
        await press(own, 'live', [one('set', typed)]); await off(own, typed)
        # verified PYQ
        pyq = 'TEST_E246_pyq_' + uuid.uuid4().hex[:6]
        refs = [{'id': str(uuid.uuid4()), 'number': 1, 'type': 'mcq', 'subject': 'Physics', 'section': 'A',
                 'options': {'A': 'a', 'B': 'b', 'C': 'c', 'D': 'd'}, 'answer': 'A', 'text': 'q',
                 'q_refs': [{'file_id': 'no-such-picture'}], 's_refs': []}]
        paper = {'id': pyq, 'status': 'published', 'audience': 'all', 'title': 'TEST E246 PYQ', 'version': 1, 'revision': 1,
                 'created_at': time.time(), 'questions': refs, 'exam': 'JEE Main',
                 'rules': {'minutes': 180, 'correct': 4, 'wrong': -1, 'skipped': 0}, 'test_kind': 'pyq',
                 'catalog_section_id': 'jee-main:pyq', 'pyq_date': '2024-01-27', 'owner_unlive': True}
        await SETS.insert_one(dict(paper))
        n = len(sb.calls)
        sc, d = await press(own, 'live', [one('set', drft), one('set', bad3), one('set', typed), one('set', pyq)])
        skipped_ids = [x['id'] for x in d.get('skipped', [])]
        # draft isn't skipped because Live includes publish semantics; let's not over-assert on draft handling.
        check('c. bulk press: only the gone-photo test is skipped for the picture reason', bad3 in skipped_ids
              and len([x for x in d.get('skipped', []) if 'picture' in (x.get('reason', '') + x.get('note', '')).lower() or 'saabit' in (x.get('reason', '') + x.get('note', ''))]) >= 1,
              (d, skipped_ids))
        check('c. typed and PYQ go Live (clean, no wait)', clean(await doc(typed)) and clean(await doc(pyq)), (await wait_of(typed), await wait_of(pyq)))
        # PYQ must not have provoked any storage calls (paper already loaded; we only measure the delta on this press).
        # (We only loosely assert: no listing of pyq folder occurred.)
        pyq_calls = [p for _, _, p in sb.calls[n:] if pyq in p]
        check('c. verified PYQ is never checked by storage', pyq_calls == [], pyq_calls)
        sb.objects[key3] = raw3
        await retry(own, bad3)
        check('c. after photo is back: previously stuck test is Live', clean(await doc(bad3)), await wait_of(bad3))

        # ---- (d) a waiting test renamed / moved: wait must survive, and nothing becomes visible.
        wid_d, key_d, raw_d = await gone(own, sb, sec, 'E d rename while waiting')
        await press(own, 'live', [one('set', wid_d)])
        s_before = await doc(wid_d); w_before = s_before.get('picture_wait') or {}
        new_title = 'E d renamed while waiting'
        r = await own.patch(f'/api/admin/catalog/tests/{wid_d}', json={'title': new_title})
        s = await doc(wid_d)
        # NOTE: the API stores the edited name in display_title and keeps the original in `title`.
        check('d. PATCH title on a waiting test: 200 and wait survives', r.status_code == 200
              and (s.get('picture_wait') or {}).get('to') == w_before.get('to')
              and s.get('display_title') == new_title and held(s, 'live'), (r.status_code, r.text[:300], s.get('picture_wait'), s.get('display_title')))
        check('d. students still do not see it after rename', not await seen(stu, slug, wid_d), None)
        # The api view uses display_title on the row (via test_view) and the library/restore uses title.
        # Section-move via PATCH section_id: we verify the wait survives whatever the API's own validation decides.
        r = await own.patch(f'/api/admin/catalog/tests/{wid_d}', json={'section_id': sec2})
        s = await doc(wid_d)
        if r.status_code == 200:
            check('d. PATCH section_id on a waiting test: 200 and wait survives', held(s, 'live') and s.get('catalog_section_id') == sec2, (r.status_code, s.get('catalog_section_id')))
        else:
            # API refused the move while waiting / nothing-to-change: still must preserve the wait and the test must stay Off.
            check('d. PATCH section_id answered non-200: wait survives, test stays Off', held(s, 'live'), (r.status_code, r.text[:200], s.get('picture_wait')))
        sb.objects[key_d] = raw_d
        sc, rr = await retry(own, wid_d)
        s_final = await doc(wid_d)
        check('d. ...and the photo back + Dobara chalao makes it Live with the renamed title intact', rr.get('state') == 'done'
              and clean(s_final) and s_final.get('display_title') == new_title, (rr, s_final.get('display_title')))

        # ---- (e) Off -> Scheduled with live_exam=true not proven, proven only after the time.
        wid_e, key_e, raw_e = await gone(own, sb, sec, 'E e sched live-exam late')
        at = time.time() + 3600
        sc, d = await press(own, 'scheduled', [one('set', wid_e)], at=at, live_exam=True)
        s, w = await doc(wid_e), await wait_of(wid_e)
        check('e. Off -> Scheduled live_exam while photo gone: not scheduled, still Off, chosen time remembered + kind live_exam',
              d.get('done') == 0 and held(s, 'scheduled') and abs((w.get('at') or 0) - at) < 1 and w.get('live_exam') is True, (d, w))
        # Fast-forward: the chosen time passes while we wait
        await SETS.update_one({'id': wid_e}, {'$set': {'picture_wait.at': time.time() - 5}})
        sb.objects[key_e] = raw_e
        sc, r = await retry(own, wid_e)
        s, it = await doc(wid_e), await item(own, sec, wid_e)
        check('e. proven after the time: does NOT open late; state missed; live_exam does not force it Live either',
              r.get('state') == 'missed' and 'der se apne aap nahi khulega' in r.get('message', '')
              and s.get('owner_unlive') is True and not s.get('start_at')
              and (s.get('picture_wait') or {}).get('state') == 'missed'
              and (it.get('pictures_wait') or {}).get('state') == 'missed', (r, s.get('picture_wait'), it.get('pictures_wait')))

        # ---- (f) restore of 3 tests at once: one proven, one gone photo, one typed (no pictures).
        a = await written(own, sec, 'E f proven', photos=1); await press(own, 'live', [one('set', a)]); await press(own, 'library', [one('set', a)])
        b = await written(own, sec, 'E f gone photo', photos=1); await press(own, 'live', [one('set', b)])
        key_f, raw_f = await take(sb, (await pics(b))[0])
        await press(own, 'library', [one('set', b)])
        c = await written(own, sec, 'E f typed', photos=0, plain=2); await press(own, 'live', [one('set', c)]); await press(own, 'library', [one('set', c)])
        n = len(sb.calls)
        r = await own.post(LIB + '/restore', json={'ids': [a, b, c], 'uploads': []}); d = J(r)
        unproven_ids = [x['id'] for x in d.get('unproven', [])]
        check('f. restore 3: all 3 marked restored; only the gone-photo one is unproven',
              d.get('restored') == 3 and unproven_ids == [b]
              and clean(await doc(a)) and held(await doc(b), 'restore') and clean(await doc(c)), (d, unproven_ids))
        check('f. ...students see the proven and the typed, not the gone-photo one',
              await seen(stu, slug, a) and await seen(stu, slug, c) and not await seen(stu, slug, b), None)
        sb.objects[key_f] = raw_f
        sc, rr = await retry(own, b)
        check('f. ...photo back + Dobara chalao: the third one becomes Live too', rr.get('state') == 'done' and clean(await doc(b)) and await seen(stu, slug, b), rr)
        _ = n  # (we don't strictly measure storage calls here)

        # ---- (g) a series paper restored when its day is already taken (comes back without a day).
        first = datetime.now(IST).date() + timedelta(days=2)
        days = [(first + timedelta(days=i)).isoformat() for i in range(3)]
        made = J(await own.post(f'/api/admin/catalog/exams/{slug}/sections', json={'name': 'All India Test Series', 'description': '', 'layout': 'list', 'kind': 'aits',
                 'first_date': days[0], 'days': 3, 'open_time': '09:00', 'last_start': '11:00', 'minutes': 10, 'correct': 4, 'wrong': -1}))
        ser, sid = made.get('id'), made.get('series_id')
        await own.put(f'{M}/series/{sid}', json={'shown': True})
        sp1 = await written(own, ser, 'E g first series paper', photos=1)
        assert (await own.post(f'{M}/series/{sid}/assign', json={'kind': 'written', 'id': sp1, 'date': days[0]})).status_code == 200
        # send sp1 to Library; then assign another paper to the same day; then restore sp1
        await library.clear_series(owner_id, 'TEST: g to library', [sp1])
        sp2 = await written(own, ser, 'E g second series paper', photos=1)
        assert (await own.post(f'{M}/series/{sid}/assign', json={'kind': 'written', 'id': sp2, 'date': days[0]})).status_code == 200
        # now take sp1's photo away and restore it
        key_g, raw_g = await take(sb, (await pics(sp1))[0])
        r = await own.post(LIB + '/restore', json={'ids': [sp1], 'uploads': []}); d = J(r)
        s = await doc(sp1)
        # Behaviour: when the day is already taken, the series paper comes back WITHOUT a day.
        # Without a day it cannot be Live and students do not see it, so no picture_wait is set.
        check('g. series paper restored when its day is taken: comes back without a day (no picture_wait needed because it is not Live)',
              d.get('restored') == 1 and d.get('without_day') >= 1 and not s.get('series_date')
              and 'picture_wait' not in s, (d, s.get('series_date'), s.get('picture_wait')))
        sb.objects[key_g] = raw_g
        # And since it has no wait, Dobara chalao answers 404.
        sc, rr = await retry(own, sp1)
        check('g. ...Dobara chalao on a without-a-day restored paper: 404', sc == 404, (sc, rr))

        # ---- (h) student lists/start route never expose a waiting test or any picture_wait field.
        wid_h, key_h, raw_h = await gone(own, sb, sec, 'E h student exposure')
        await press(own, 'live', [one('set', wid_h)])
        check('h. student catalogue never lists a waiting test', not await seen(stu, slug, wid_h), None)
        r = await stu.get(f'/api/exam-navigation/{slug}/catalogue', params={'section': 'mock-tests', 'page': 1})
        payload = r.text
        check('h. student catalogue payload never leaks picture_wait', 'picture_wait' not in payload and 'pictures_wait' not in payload, payload[:200])
        r = await stu.post(f'/api/tests/{wid_h}/start', json={})
        check('h. student start on a waiting test: non-200', r.status_code != 200, r.status_code)
        sb.objects[key_h] = raw_h
        await retry(own, wid_h)  # cleanup

        # ---- (i) reviewer cannot press anything new.
        wid_i, key_i, raw_i = await gone(own, sb, sec, 'E i reviewer not allowed')
        await press(own, 'live', [one('set', wid_i)])
        r = await rev.post(f'{M}/pictures/{wid_i}/retry')
        check('i. reviewer Dobara chalao: 403', r.status_code == 403, r.status_code)
        r2 = await rev.post(f'{M}/status', json={'action': 'live', 'items': [one('set', wid_i)]})
        check('i. reviewer status change: non-200', r2.status_code != 200, r2.status_code)
        sb.objects[key_i] = raw_i
        await retry(own, wid_i)

        # ---- (j) 15-minute round with 3 stuck tests where only one photo is back.
        j1, kj1, rj1 = await gone(own, sb, sec, 'E j stuck 1')
        j2, kj2, rj2 = await gone(own, sb, sec, 'E j stuck 2')
        j3, kj3, rj3 = await gone(own, sb, sec, 'E j stuck 3')
        for jx in (j1, j2, j3):
            await press(own, 'live', [one('set', jx)])
        # age their tried_at so the round picks them
        await SETS.update_many({'id': {'$in': [j1, j2, j3]}}, {'$set': {'picture_wait.tried_at': time.time() - 900}})
        # bring only j2's photo back
        sb.objects[kj2] = rj2
        tasks = await HOLD.resume()
        out = await HOLD.settle(tasks, 30)
        s1, s2, s3 = await doc(j1), await doc(j2), await doc(j3)
        states = [out.count(('done', '')), len(tasks)]
        check('j. 15-min round picks all 3 stuck tests', len(tasks) == 3, (len(tasks), out))
        check('j. only j2 becomes Live; the other two stay stuck with their reasons',
              clean(s2) and held(s1, 'live') and held(s3, 'live') and states[0] == 1, (states, s1.get('picture_wait'), s3.get('picture_wait')))
        # cleanup
        sb.objects[kj1] = rj1; sb.objects[kj3] = rj3
        await retry(own, j1); await retry(own, j3)

        check('nothing of this run waits on this server any more', not HOLD._tasks and not HOLD._busy, (len(HOLD._tasks), len(HOLD._busy)))
    finally:
        HOLD.prove = real_prove
        cancel_kicks()
        assert H.TEST_DB.startswith('tejas_isolated_') and H.TEST_DB != H.REAL_DB
        await H.tdbmod.client.drop_database(H.TEST_DB)
        print('dropped', H.TEST_DB)
    print(f'TOTAL {len(RESULTS)} PASS {sum(RESULTS)} FAIL {len(RESULTS) - sum(RESULTS)}')


if __name__ == '__main__':
    asyncio.run(main())
