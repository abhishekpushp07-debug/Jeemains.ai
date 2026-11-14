"""TEST-ONLY iteration 178 (T1): extra edge cases for the 15-minute live start window + instant score.
REAL ASGI app + REAL cookie auth in a disposable isolated DB (dropped at the end). Customer DB never touched.
Run: cd /app/backend/tests && python -W ignore test_iter178_t1_window_isolated.py"""
import asyncio, copy, os, secrets, sys, time, uuid
from datetime import datetime, timezone, timedelta
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
os.environ['TEJAS_ISO_DB'] = 'tejas_isolated_t1w178_' + secrets.token_hex(3)
import iso_harness_scale176 as H  # noqa: E402
import httpx  # noqa: E402

TDB, PID = H.TDB, 'jee-main-pyq-2025-04-02-s1'
RESULTS = []


def check(name, ok, info=''):
    RESULTS.append(ok); print(('PASS ' if ok else 'FAIL ') + name + ('' if ok else ' :: ' + str(info)[:400]), flush=True)


def J(r):
    j = r.json(); return j.get('data') if isinstance(j, dict) and 'data' in j and 'meta' in j else j


async def user(i, role='student'):
    from tejas import auth
    uid = 'TEST_U178T_%04d' % i; stamp = time.time()
    u = {'_id': uid, 'id': uid, 'phone': '+91993%07d' % i, 'name': 'TEST', 'role': 'student', 'exam': 'JEE Main', 'access_type': 'unverified_phone',
         'pin_version': 1, 'created_at': stamp, 'consent_at': stamp, 'last_seen_at': stamp}
    sid = str(uuid.uuid4())
    await TDB.tejas_phone_profiles.insert_one(u)
    await TDB.tejas_sessions.insert_one({'id': sid, 'user_id': uid, 'access_type': 'unverified_phone', 'pin_version': 1, 'expires_at': datetime.now(timezone.utc) + timedelta(days=1)})
    return uid, {'access_token': auth.token(u, sid, 'access', 3600)}


async def main():
    assert not H.leftover_real_handles()
    await H.tdbmod.client.drop_database(H.TEST_DB); await H.tdbmod.indexes()
    try:
        for name, rows in H.DATA['collections'].items():
            await TDB[name].insert_many([copy.deepcopy(r) for r in rows])
        await run()
    finally:
        await H.tdbmod.client.drop_database(H.TEST_DB)
    print(f'TOTAL {len(RESULTS)} PASS {sum(RESULTS)} FAIL {len(RESULTS) - sum(RESULTS)}')


async def run():
    from tejas import live_window as W, jobs as J_, structure
    await structure.seed()  # exam catalogue for exam-navigation (isolated DB only)
    # Unit: window edge maths (book publishing closes_at shorter than duration, exact boundary)
    check('closes_at shorter than duration still gives last start +15 and full time', W.window(0, 180, 3600) == (900, 900 + 10800))
    check('can_start true exactly at last_start_at, false 1s after', W.can_start({'last_start_at': 100}, 100) and not W.can_start({'last_start_at': 100}, 101))
    check('can_start true when no window recorded (legacy running exams)', W.can_start({}, 10 ** 12))
    t = time.time()
    minutes = (await TDB.tejas_sets.find_one({'id': PID}, {'rules.minutes': 1}))['rules']['minutes']
    # Scheduled (future) exam: status scheduled, can_start true
    fut = t + 3600; fl, fe = W.window(fut, minutes)
    await TDB.tejas_sets.update_one({'id': PID}, {'$set': {'competition': True, 'start_at': fut, 'end_at': fe, 'last_start_at': fl, 'live_enabled': True}})
    S = [await user(i) for i in range(4)]
    T = httpx.ASGITransport(app=H.app, raise_app_exceptions=False)
    async with httpx.AsyncClient(transport=T, base_url='https://api.test.example', timeout=120) as c:
        async def go(i, method, url, body=None):
            c.cookies.clear(); c.cookies.update(S[i][1])
            return await c.request(method, url, json=body)
        comp = J(await go(0, 'GET', '/api/competitions'))['items']
        mine = next((x for x in comp if x['id'] == PID), {})
        check('scheduled exam: status scheduled, can_start true, last_start_at = start+900', mine.get('status') == 'scheduled' and mine.get('can_start') is True and mine.get('last_start_at') == fut + 900, mine)
        # Open the exam 5 min ago
        opened = t - 300; last, end = W.window(opened, minutes)
        await TDB.tejas_sets.update_one({'id': PID}, {'$set': {'start_at': opened, 'end_at': end, 'last_start_at': last}})
        for i in (0, 1):
            assert (await go(i, 'POST', f'/api/sets/{PID}/preflight', {'test_response': 'ok'})).status_code == 200
        A0 = J(await go(0, 'POST', f'/api/sets/{PID}/start', {'start_key': str(uuid.uuid4()), 'device_checked': True}))
        A1 = J(await go(1, 'POST', f'/api/sets/{PID}/start', {'start_key': str(uuid.uuid4()), 'device_checked': True}))
        check('on-time starter deadline = own start + full duration and <= end_at', abs(A0['deadline'] - A0['started_at'] - minutes * 60) < 1 and A0['deadline'] <= end, (A0['deadline'], A0['started_at'], end))
        # Submit student 0 and read results immediately (grading may be pending)
        mcq = [q for q in A0['questions'] if q['type'] == 'mcq'][:3]
        for q in mcq:
            await go(0, 'PUT', f'/api/attempts/{A0["id"]}/answers/{q["id"]}', {'value': sorted(q['options'])[0], 'revision': 1, 'request_id': str(uuid.uuid4())})
        r = await go(0, 'POST', f'/api/attempts/{A0["id"]}/submit')
        check('submit accepted', r.status_code in (200, 202), r.status_code)
        res = J(await go(0, 'GET', f'/api/attempts/{A0["id"]}/results'))
        shape_ok = res.get('status') == 'embargoed' and res.get('score_released') is True and (
            (res.get('summary') is None and res.get('retry_after_ms')) or bool(res.get('summary')))
        check('results right after submit: embargoed + score_released, summary or retry_after_ms', shape_ok, res)
        check('results before end leak no questions/answers/analytics/ledger', not any(k in res for k in ('questions', 'analytics', 'ledger', 'answers')), list(res))
        await J_.drain_lane('grade')
        res = J(await go(0, 'GET', f'/api/attempts/{A0["id"]}/results'))
        check('after grading, summary present with score and maximum', bool(res.get('summary')) and 'score' in res['summary'] and 'maximum' in res['summary'], res)
        # Another student cannot read this result
        r = await go(2, 'GET', f'/api/attempts/{A0["id"]}/results')
        check('other student cannot read the result', r.status_code in (403, 404), r.status_code)
        # Exam navigation history shows score
        hist = J(await go(0, 'GET', '/api/exam-navigation/jee-main/history'))
        item = next((x for x in (hist or {}).get('items', []) if x['id'] == A0['id']), None)
        check('exam-navigation history shows summary for regular live exam', bool(item and item.get('summary')), hist if not item else item)
        print('INFO exam slug used jee-main; history total', (hist or {}).get('total'))
        # Leaderboard still embargoed while other students are running
        lb = J(await go(0, 'GET', f'/api/competitions/{PID}'))
        check('leaderboard embargoed until end_at', lb.get('status') == 'embargoed' and not lb.get('rows') and not lb.get('items'), {k: lb.get(k) for k in ('status',)})
        # Reports and worked solutions locked
        r = await go(0, 'POST', f'/api/attempts/{A0["id"]}/report', {})
        check('report endpoint 403 before end', r.status_code == 403, r.status_code)
        # Close the window
        await TDB.tejas_sets.update_one({'id': PID}, {'$set': {'last_start_at': time.time() - 1}})
        r = await go(3, 'POST', f'/api/sets/{PID}/preflight', {'test_response': 'ok'})
        check('late student 409 message names IST time and full minutes', r.status_code == 409 and 'IST' in r.text and f'{minutes} minutes' in r.text, r.text[:300])
        r = await go(0, 'POST', f'/api/sets/{PID}/start', {'start_key': str(uuid.uuid4()), 'device_checked': True})
        n = await TDB.tejas_attempts.count_documents({'user_id': S[0][0], 'set_id': PID})
        check('submitted student cannot open a second attempt after window', r.status_code != 200 or J(r).get('id') == A0['id'], (r.status_code, r.text[:200]))
        check('only one attempt row for submitted student', n == 1, n)
        r = await go(1, 'POST', f'/api/sets/{PID}/start', {'start_key': str(uuid.uuid4()), 'device_checked': True})
        check('running student reopens same attempt after window', r.status_code == 200 and J(r)['id'] == A1['id'], (r.status_code, r.text[:200]))
        comp = J(await go(3, 'GET', '/api/competitions'))['items']
        mine = next((x for x in comp if x['id'] == PID), {})
        check('list: status stays live and can_start false after window', mine.get('status') == 'live' and mine.get('can_start') is False, mine)
        # My Tests grading filter: ungraded regular live attempt
        await TDB.tejas_attempts.update_one({'id': A0['id']}, {'$set': {'summary': None}})
        mt = J(await go(0, 'GET', '/api/my/tests?tab=completed&status=grading'))
        check('My Tests grading filter includes ungraded regular live exam', any(x['id'] == A0['id'] and x['status'] == 'grading' for x in mt['items']), mt.get('items'))
    # Reschedule an existing future live exam: window recomputed
    from tejas.imports import schedule_import
    from tejas.import_models import ScheduleInput
    rid = 'TEST_imp178'; now_ = time.time()
    q = copy.deepcopy((await TDB.tejas_sets.find_one({'id': PID}, {'questions': {'$slice': 1}}))['questions'])
    await TDB.tejas_imports.insert_one({'id': rid, 'title': 'TEST import', 'format': 'pdf', 'status': 'ready', 'issues': [], 'questions': q, 'exam': 'JEE Main',
                                        'duration_minutes': 60, 'created_at': now_, 'rights_attested_by': 'TEST_owner'})
    owner = {'id': 'TEST_owner', 'role': 'owner'}
    v = await schedule_import(rid, ScheduleInput(start_at=datetime.fromtimestamp(now_ + 7200, timezone.utc).isoformat(), revision=0), u=owner)
    s = await TDB.tejas_sets.find_one({'id': rid}, {'revision': 1})
    v2 = await schedule_import(rid, ScheduleInput(start_at=datetime.fromtimestamp(now_ + 9000, timezone.utc).isoformat(), revision=s['revision']), u=owner)
    check('reschedule recomputes last_start_at and end_at', v2.last_start_at == v2.start_at + 900 and v2.end_at == v2.start_at + 900 + 3600 and v2.start_at != v.start_at, (v2.start_at, v2.last_start_at, v2.end_at))
    # apply_to_upcoming leaves exams that already have a window alone
    await TDB.tejas_sets.update_one({'id': rid}, {'$set': {'last_start_at': v2.start_at + 60}})
    await W.apply_to_upcoming()
    d = await TDB.tejas_sets.find_one({'id': rid}, {'last_start_at': 1, 'end_at': 1})
    check('apply_to_upcoming skips exams that already have last_start_at', d['last_start_at'] == v2.start_at + 60 and d['end_at'] == v2.end_at, d)


if __name__ == '__main__':
    asyncio.run(main())
