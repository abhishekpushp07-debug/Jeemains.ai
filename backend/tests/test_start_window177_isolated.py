"""TEST-ONLY iteration 177: live exam 15-minute start window + instant score, against the REAL ASGI app and REAL cookie
auth in a disposable isolated DB (dropped at the end). Customer DB never touched. Run: python test_start_window177_isolated.py"""
import asyncio, copy, os, secrets, sys, time, uuid
from datetime import datetime, timezone, timedelta
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
os.environ['TEJAS_ISO_DB'] = 'tejas_isolated_window177_' + secrets.token_hex(3)
import iso_harness_scale176 as H  # noqa: E402
import httpx  # noqa: E402

TDB, PID = H.TDB, 'jee-main-pyq-2025-04-02-s1'
RESULTS = []


def check(name, ok, info=''):
    RESULTS.append(ok); print(('PASS ' if ok else 'FAIL ') + name + ('' if ok else ' :: ' + str(info)[:300]), flush=True)


def J(r):
    j = r.json(); return j.get('data') if isinstance(j, dict) and 'data' in j and 'meta' in j else j


async def student(i):
    from tejas import auth
    uid = 'TEST_U177W_%04d' % i; stamp = time.time()
    u = {'_id': uid, 'id': uid, 'phone': '+91992%07d' % i, 'name': 'TEST', 'role': 'student', 'exam': 'JEE Main', 'access_type': 'unverified_phone',
         'pin_version': 1, 'created_at': stamp, 'consent_at': stamp, 'last_seen_at': stamp}
    sid = str(uuid.uuid4())
    await TDB.tejas_phone_profiles.insert_one(u)
    await TDB.tejas_sessions.insert_one({'id': sid, 'user_id': uid, 'access_type': 'unverified_phone', 'pin_version': 1, 'expires_at': datetime.now(timezone.utc) + timedelta(days=1)})
    return uid, {'access_token': auth.token(u, sid, 'access', 3600)}


async def main():
    assert not H.leftover_real_handles()
    await H.tdbmod.client.drop_database(H.TEST_DB); await H.tdbmod.indexes()
    for name, rows in H.DATA['collections'].items():
        await TDB[name].insert_many([copy.deepcopy(r) for r in rows])
    from tejas import live_window as W, jobs as J_
    from tejas.imports import schedule_import
    from tejas.import_models import ScheduleInput
    t = time.time()
    # Unit: window maths
    check('fixed exam: starts close 15 min after opening, end = last start + duration', W.window(1000, 180) == (1900, 1900 + 10800))
    check('long window: last start leaves the full duration before close', W.window(0, 180, 86400) == (86400 - 10800, 86400))
    check('score sealed only for All India series before close', W.score_sealed({'series_id': 'x', 'competition_end': t + 60}, t)
          and not W.score_sealed({'competition_end': t + 60}, t) and not W.score_sealed({'series_id': 'x', 'competition_end': t - 1}, t))
    # Make the seeded paper a live exam that opened 14 minutes ago (start window open for ~1 more minute)
    minutes = (await TDB.tejas_sets.find_one({'id': PID}, {'rules.minutes': 1}))['rules']['minutes']
    opened = t - 14 * 60
    last, end = W.window(opened, minutes)
    await TDB.tejas_sets.update_one({'id': PID}, {'$set': {'competition': True, 'start_at': opened, 'end_at': end, 'last_start_at': last, 'live_enabled': True}})
    S = [await student(i) for i in range(4)]
    T = httpx.ASGITransport(app=H.app, raise_app_exceptions=False)
    async with httpx.AsyncClient(transport=T, base_url='https://api.test.example', timeout=120) as c:
        def go(i, method, url, body=None):
            return c.request(method, url, json=body, cookies=S[i][1])
        comp = J(await go(0, 'GET', '/api/competitions'))['items']
        mine = next((x for x in comp if x['id'] == PID), {})
        check('competition list shows last_start_at and can_start while the window is open', mine.get('last_start_at') == last and mine.get('can_start') is True and mine.get('status') == 'live', mine)
        # Late (14 min) starter gets full time
        assert (await go(0, 'POST', f'/api/sets/{PID}/preflight', {'test_response': 'ok'})).status_code == 200
        assert (await go(2, 'POST', f'/api/sets/{PID}/preflight', {'test_response': 'ok'})).status_code == 200
        r = await go(0, 'POST', f'/api/sets/{PID}/start', {'start_key': str(uuid.uuid4()), 'device_checked': True})
        A = J(r); aid = A['id']
        check('student starting 14 minutes late gets the full duration', r.status_code == 200 and abs(A['deadline'] - A['started_at'] - minutes * 60) < 1 and A['competition_end'] == end, (r.status_code, A.get('deadline'), A.get('started_at')))
        # Close the window
        await TDB.tejas_sets.update_one({'id': PID}, {'$set': {'last_start_at': time.time() - 1}})
        r = await go(1, 'POST', f'/api/sets/{PID}/preflight', {'test_response': 'ok'})
        check('after the window, the device check is refused with a clear message', r.status_code == 409 and 'Starting closed' in r.text, (r.status_code, r.text[:200]))
        r = await go(2, 'POST', f'/api/sets/{PID}/start', {'start_key': str(uuid.uuid4()), 'device_checked': True})
        check('after the window, a new start is refused even with an earlier device check', r.status_code == 409 and 'Starting closed' in r.text, (r.status_code, r.text[:200]))
        r = await go(0, 'POST', f'/api/sets/{PID}/start', {'start_key': str(uuid.uuid4()), 'device_checked': True})
        check('a student who started on time can still reopen the same attempt', r.status_code == 200 and J(r)['id'] == aid, r.status_code)
        comp = J(await go(3, 'GET', f'/api/competitions/{PID}'))
        check('competition detail: can_start false after the window, leaderboard still embargoed', comp['competition']['can_start'] is False and comp['status'] == 'embargoed', comp.get('competition'))
        # Answer a few, submit, instant score
        for q in [q for q in A['questions'] if q['type'] == 'mcq'][:5]:
            await go(0, 'PUT', f'/api/attempts/{aid}/answers/{q["id"]}', {'value': sorted(q['options'])[0], 'revision': 1, 'request_id': str(uuid.uuid4())})
        r = await go(0, 'POST', f'/api/attempts/{aid}/submit')
        check('submit accepted', r.status_code in (200, 202), r.status_code)
        await J_.drain_lane('grade')
        res = J(await go(0, 'GET', f'/api/attempts/{aid}/results'))
        led = await TDB.tejas_ledgers.find_one({'id': aid})
        check('results right after submission show the score (still embargoed for answers)', res['status'] == 'embargoed' and res.get('score_released') is True
              and res.get('summary') and res['summary']['score_exact'] == led['summary']['score_exact'] and res['release_at'] == end, res)
        check('results before the end carry no questions, answers or solutions', 'questions' not in res and 'analytics' not in res)
        q0 = A['questions'][0]['id']
        r = await go(0, 'GET', f'/api/attempts/{aid}/questions/{q0}/asset/solution/0')
        check('solution images stay locked until every student has finished', r.status_code == 403, r.status_code)
        r = await go(0, 'POST', f'/api/attempts/{aid}/retry', {'start_key': str(uuid.uuid4())})
        check('revision attempt stays locked until the end', r.status_code == 403, r.status_code)
        r = await go(0, 'POST', f'/api/attempts/{aid}/questions/{q0}/solution-open')
        check('solution-open stays locked until the end', r.status_code == 403, r.status_code)
        view = J(await go(0, 'GET', f'/api/attempts/{aid}'))
        hist = J(await go(0, 'GET', '/api/attempts'))['items']
        check('attempt view and history show the score immediately', bool(view.get('summary')) and any(h['id'] == aid and h.get('summary') for h in hist))
        mt = J(await go(0, 'GET', '/api/my/tests?tab=completed'))
        item = next((x for x in mt['items'] if x['id'] == aid), {})
        check('My Tests marks it completed with the score, reports stay off until the end', item.get('status') == 'completed' and item.get('summary') and item.get('report_allowed') is False, item)
        mt = J(await go(0, 'GET', '/api/my/tests?tab=completed&status=completed'))
        check('My Tests completed filter includes it', any(x['id'] == aid for x in mt['items']), mt.get('total'))
        mt = J(await go(0, 'GET', '/api/my/tests?tab=completed&status=embargoed'))
        check('My Tests sealed filter excludes regular live exams', not any(x['id'] == aid for x in mt['items']), mt.get('total'))
        # Series attempts keep the sealed score
        await TDB.tejas_attempts.update_one({'id': aid}, {'$set': {'series_id': 'all-india-jee-2026-27'}})
        res = J(await go(0, 'GET', f'/api/attempts/{aid}/results'))
        view = J(await go(0, 'GET', f'/api/attempts/{aid}'))
        check('All India series attempt keeps its score sealed until the day closes', res['status'] == 'embargoed' and not res.get('summary') and not res.get('score_released') and view.get('summary') is None, res)
        await TDB.tejas_attempts.update_one({'id': aid}, {'$unset': {'series_id': 1}})
        # After the end, full results open
        await TDB.tejas_attempts.update_one({'id': aid}, {'$set': {'competition_end': time.time() - 1}})
        await TDB.tejas_sets.update_one({'id': PID}, {'$set': {'end_at': time.time() - 1}})
        res = J(await go(0, 'GET', f'/api/attempts/{aid}/results'))
        check('after the end, full results with questions open', res.get('status') == 'completed' and len(res.get('questions', [])) == 75, res.get('status'))
        r = await go(0, 'GET', f'/api/competitions/{PID}')
        check('after the end, the leaderboard opens', J(r)['status'] in ('ready', 'provisional'), J(r)['status'])
    # Upcoming exams scheduled before this change get the window, once
    now_ = time.time()
    base = {'competition': True, 'rules': {'minutes': 180}, 'title': 'TEST', 'exam': 'JEE Main', 'questions': []}
    await TDB.tejas_sets.insert_many([
        {**base, 'id': 'TEST_up_fixed', 'start_at': now_ + 3600, 'end_at': now_ + 3600 + 10800},
        {**base, 'id': 'TEST_up_long', 'start_at': now_ + 3600, 'end_at': now_ + 3600 + 86400},
        {**base, 'id': 'TEST_running', 'start_at': now_ - 600, 'end_at': now_ - 600 + 10800},
        {**base, 'id': 'TEST_series', 'series_id': 'all-india-jee-2026-27', 'competition': True, 'start_at': now_ + 3600, 'end_at': now_ + 7200}])
    await W.apply_to_upcoming(); await W.apply_to_upcoming()
    docs = {d['id']: d async for d in TDB.tejas_sets.find({'id': {'$regex': '^TEST_'}}, {'_id': 0, 'id': 1, 'start_at': 1, 'end_at': 1, 'last_start_at': 1})}
    f, lg = docs['TEST_up_fixed'], docs['TEST_up_long']
    check('upcoming fixed exam: last start +15 min, end moved 15 min later, applied once', f['last_start_at'] == f['start_at'] + 900 and abs(f['end_at'] - (f['start_at'] + 900 + 10800)) < 0.01)
    check('upcoming long-window exam: end kept, starts close when less than full time is left', lg['end_at'] == lg['start_at'] + 86400 and lg['last_start_at'] == lg['end_at'] - 10800)
    check('running exam and All India series day untouched', 'last_start_at' not in docs['TEST_running'] and 'last_start_at' not in docs['TEST_series'])
    # New schedules get the window
    rid = 'TEST_imp177'
    q = copy.deepcopy((await TDB.tejas_sets.find_one({'id': PID}, {'questions': {'$slice': 1}}))['questions'])
    await TDB.tejas_imports.insert_one({'id': rid, 'title': 'TEST import', 'format': 'pdf', 'status': 'ready', 'issues': [], 'questions': q, 'exam': 'JEE Main',
                                        'duration_minutes': 180, 'created_at': now_, 'rights_attested_by': 'TEST_owner'})
    start = datetime.fromtimestamp(now_ + 7200, timezone.utc).isoformat()
    v = await schedule_import(rid, ScheduleInput(start_at=start, revision=0), u={'id': 'TEST_owner', 'role': 'owner'})
    check('new live exam schedule sets last_start_at = start + 15 min and end = start + 15 min + duration', v.last_start_at == v.start_at + 900 and v.end_at == v.start_at + 900 + 10800, (v.start_at, v.last_start_at, v.end_at))
    await H.tdbmod.client.drop_database(H.TEST_DB)
    print(f'TOTAL {len(RESULTS)} PASS {sum(RESULTS)} FAIL {len(RESULTS) - sum(RESULTS)}')


if __name__ == '__main__':
    asyncio.run(main())
