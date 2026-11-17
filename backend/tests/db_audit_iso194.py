"""TEST-ONLY iteration 194: DB audit fixes C1-C7 (admission waiting line, staff out of peer stats + one-time migration,
safe index builds, series CAS, phone _id==id, owner-only QA test-account removal).
Isolated disposable DB (book_publishing_iso170 harness, storage + AI mocked). Run: cd /app/backend && timeout 290 python tests/db_audit_iso194.py
"""
import asyncio, sys, time, uuid, secrets, types
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import book_publishing_iso170 as T  # noqa: E402,F401
from book_publishing_iso170 import H, mkstaff, client, check, RESULTS  # noqa: E402
from structure_iso173 import mkset, start  # noqa: E402
from tejas import structure, admission as ADM, cohorts as CH, corrections as CO, library as LIB, db as DBM, integrity as INT, series_admin, live_series  # noqa: E402

DB = H.TDB
URL = '/api/admin/qa/test-accounts/remove'
CONFIRM = 'REMOVE TEST ACCOUNTS'


def J(r):
    try: d = r.json()
    except Exception: return {}
    if isinstance(d, dict) and 'data' in d and 'error' in d: d = d['data'] if d['data'] is not None else d
    return d if d is not None else {}


# ---------------- C1 unit: AdmissionGate with a fake app ----------------
def gate_with(delay):
    async def app(scope, receive, send):
        await asyncio.sleep(delay)
        await send({'type': 'http.response.start', 'status': 200, 'headers': []})
        await send({'type': 'http.response.body', 'body': b'ok'})
    return ADM.AdmissionGate(app, types.SimpleNamespace(state=types.SimpleNamespace()))


async def hit(g, path='/api/auth/phone', method='POST'):
    out = {}
    async def send(m):
        if m['type'] == 'http.response.start':
            out['status'] = m['status']; out['headers'] = dict((k.decode().lower(), v.decode()) for k, v in m.get('headers', []))
    async def receive(): return {'type': 'http.request', 'body': b''}
    t = time.monotonic()
    await g({'type': 'http', 'path': path, 'method': method, 'headers': []}, receive, send)
    out['t'] = time.monotonic() - t
    return out


async def gate_tests():
    W = ADM.ADMISSION_WAIT; saved = dict(W)
    try:
        g = gate_with(0.1); lane = g.lanes['auth']
        rs = await asyncio.gather(*(hit(g) for _ in range(20)))
        check('C1 gate: 20 auth bursts all 200 (wait line)', all(r['status'] == 200 for r in rs), [r['status'] for r in rs])
        check('C1 gate: peak <= limit and in_flight back to 0', lane['peak'] <= lane['limit'] and lane['in_flight'] == 0, (lane['peak'], lane['limit'], lane['in_flight']))
        check('C1 gate: waited counted (16) and queue empty', lane['waited'] == 20 - lane['limit'] and not g.waiting['auth'], (lane['waited'], len(g.waiting['auth'])))

        W['auth'] = 0.15
        g = gate_with(1.0); lane = g.lanes['auth']
        rs = await asyncio.gather(*(hit(g) for _ in range(10)))
        ok = [r for r in rs if r['status'] == 200]; busy = [r for r in rs if r['status'] == 503]
        check('C1 gate: short wait -> 4 ok, 6 x 503 capacity_busy', len(ok) == 4 and len(busy) == 6, [r['status'] for r in rs])
        check('C1 gate: 503 carries Retry-After 2', all(b['headers'].get('retry-after') == '2' for b in busy), busy[:1])
        check('C1 gate: timed-out waiters waited ~0.15 s (not immediate)', all(0.1 < b['t'] < 0.6 for b in busy), [round(b['t'], 2) for b in busy])
        check('C1 gate: after timeouts in_flight 0, queue empty, rejected 6', lane['in_flight'] == 0 and not g.waiting['auth'] and lane['rejected'] == 6, (lane['in_flight'], len(g.waiting['auth']), lane['rejected']))

        W['auth'] = 6
        g = gate_with(0.4); lane = g.lanes['auth']
        holders = [asyncio.create_task(hit(g)) for _ in range(4)]
        await asyncio.sleep(0.02)
        waiters = [asyncio.create_task(hit(g)) for _ in range(5)]
        await asyncio.sleep(0.05)
        check('C1 gate: 5 waiters queued while full', len(g.waiting['auth']) == 5 and lane['in_flight'] == 4, (len(g.waiting['auth']), lane['in_flight']))
        for w in waiters: w.cancel()
        await asyncio.gather(*waiters, return_exceptions=True)
        check('C1 gate: cancelled waiters leave the queue', not g.waiting['auth'], len(g.waiting['auth']))
        await asyncio.gather(*holders)
        check('C1 gate: cancelled waiters leak no slot (in_flight 0)', lane['in_flight'] == 0, lane['in_flight'])
        r = await hit(gate_with(0.0)) if False else await hit(g)
        check('C1 gate: next request admitted straight away', r['status'] == 200 and r['t'] < 0.6 and lane['in_flight'] == 0, (r, lane['in_flight']))

        # race: slot handed over, then the waiter is cancelled before it resumes -> slot given back, not leaked
        g = gate_with(0.0); lane = g.lanes['auth']; lane['in_flight'] = lane['limit']
        wt = asyncio.create_task(g.wait_slot('auth', lane)); await asyncio.sleep(0.01)
        g.give_back('auth', lane)  # hands the slot to the waiter, in_flight unchanged
        wt.cancel()
        try:
            got = await wt  # Python 3.11 wait_for returns the result when the future is already done (cancel swallowed)
        except asyncio.CancelledError:
            got = None
        if got:
            g.give_back('auth', lane)  # the caller owns the slot and releases it in its finally
        print('race outcome', 'kept-slot' if got else 'cancelled')
        check('C1 gate: handed-over-then-cancelled waiter returns its slot', lane['in_flight'] == lane['limit'] - 1 and not g.waiting['auth'], lane['in_flight'])

        # read/asset lanes reject immediately (no wait)
        g = gate_with(0.5)
        rs = await asyncio.gather(*(hit(g, '/api/catalog', 'GET') for _ in range(20)))
        rb = [r for r in rs if r['status'] == 503]
        check('C1 gate: read lane 16 ok + 4 immediate 503', len(rb) == 4 and all(r['t'] < 0.1 for r in rb), [(r['status'], round(r['t'], 2)) for r in rs])
        rs = await asyncio.gather(*(hit(g, '/api/sets/x/asset/y', 'GET') for _ in range(10)))
        rb = [r for r in rs if r['status'] == 503]
        check('C1 gate: asset lane 8 ok + 2 immediate 503', len(rb) == 2 and all(r['t'] < 0.1 for r in rb), [(r['status'], round(r['t'], 2)) for r in rs])
        check('C1 gate: read/asset waited 0, in_flight 0', g.lanes['read']['waited'] == 0 and g.lanes['asset']['waited'] == 0 and g.lanes['read']['in_flight'] == 0 and g.lanes['asset']['in_flight'] == 0, (g.lanes['read'], g.lanes['asset']))

        # queue cap = limit*64 -> excess rejected immediately
        W['auth'] = 0.4
        g = gate_with(0.8); lane = g.lanes['auth']; cap = lane['limit'] * 64
        rs = await asyncio.gather(*(hit(g) for _ in range(lane['limit'] + cap + 30)))
        fast = [r for r in rs if r['status'] == 503 and r['t'] < 0.2]; slow = [r for r in rs if r['status'] == 503 and r['t'] >= 0.2]
        check('C1 gate: queue cap limit*64 -> 30 immediate 503, cap waited then 503', len(fast) == 30 and len(slow) == cap, (len(fast), len(slow), cap))
        check('C1 gate: after cap test in_flight 0', lane['in_flight'] == 0 and not g.waiting['auth'], lane['in_flight'])

        # live lane waits too (3 s default)
        check('C1 runtime: default waits auth 6 s / live 3 s', saved.get('auth') == 6.0 and saved.get('live') == 3.0, saved)
        W['live'] = 0.1
        g = gate_with(0.5); lane = g.lanes['live']
        rs = await asyncio.gather(*(hit(g, '/api/attempts/a1/submit', 'POST') for _ in range(lane['limit'] + 3)))
        rb = [r for r in rs if r['status'] == 503]
        check('C1 gate: live lane waits before 503', len(rb) == 3 and all(r['t'] >= 0.08 for r in rb) and lane['in_flight'] == 0, [round(r['t'], 2) for r in rb])
    finally:
        W.clear(); W.update(saved)


# ---------------- C1 + C6 integration: 50 parallel sign-ups through the real app ----------------
async def signup_burst(prefix):
    phones = [prefix + f'{i:04d}' for i in range(50)]
    cs = [client() for _ in phones]
    gate = None
    t = time.monotonic()
    rs = await asyncio.gather(*(c.post('/api/auth/phone/signup', json={'phone': p, 'pin': '4826', 'confirm_pin': '4826'}) for c, p in zip(cs, phones)))
    el = time.monotonic() - t
    codes = [r.status_code for r in rs]
    check('C1 app: 50 parallel sign-ups all 200', codes.count(200) == 50, {c: codes.count(c) for c in set(codes)})
    gate = H.app.state.admission; lane = gate.lanes['auth']
    check('C1 app: auth lane peak <= limit, in_flight 0', lane['peak'] <= lane['limit'] and lane['in_flight'] == 0, (lane['peak'], lane['limit'], lane['in_flight']))
    print('burst seconds', round(el, 2), 'waited', lane['waited'], 'rejected', lane['rejected'])
    rows = await DB.tejas_phone_profiles.find({'phone': {'$in': phones}}).to_list(None)
    check('C6: new sign-ups store _id == id', len(rows) == 50 and all(r['_id'] == r['id'] for r in rows), [(r['_id'], r['id']) for r in rows if r['_id'] != r['id']][:3])
    # sign-in, forgot PIN, change PIN still work for _id==id rows
    c = client(); r = await c.post('/api/auth/phone', json={'phone': phones[0], 'pin': '4826'})
    check('C6: sign-in works', r.status_code == 200, r.text[:200])
    r = await c.post('/api/auth/pin', json={'phone': phones[0], 'new_pin': '5937', 'confirm_pin': '5937'})
    check('C6: change PIN works', r.status_code == 200, r.text[:200])
    r = await client().post('/api/auth/pin/reset', json={'phone': phones[1], 'new_pin': '6148', 'confirm_pin': '6148'})
    check('C6: forgot PIN works', r.status_code == 200, r.text[:200])
    r = await client().post('/api/auth/phone', json={'phone': phones[1], 'pin': '6148'})
    check('C6: sign-in with reset PIN', r.status_code == 200, r.text[:200])
    return phones, cs


# ---------------- C2 staff out of peer stats ----------------
async def complete_practice(c, sid):
    r = await start(c, sid); a = J(r)
    assert r.status_code == 200, r.text[:300]
    await c.post(f"/api/attempts/{a['id']}/begin")
    r = await c.post(f"/api/attempts/{a['id']}/submit")
    assert r.status_code in (200, 202), r.text[:300]
    for _ in range(20):
        d = await DB.tejas_attempts.find_one({'id': a['id']})
        if d.get('ledger') or d.get('status') == 'completed' and d.get('grading_status') == 'ready': break
        await asyncio.sleep(0.2)
    d = await DB.tejas_attempts.find_one({'id': a['id']}, {'_id': 0})
    if not d.get('ledger'):
        from tejas import attempts as AT
        led = await CO.freeze_ledger(dict(await AT.owned(a['id'], {'id': d['user_id'], 'role': 'student'})))
        await DB.tejas_attempts.update_one({'id': a['id']}, {'$set': {'summary': led['summary'], 'grading_status': 'ready'}})
    return a['id']


async def cohort_tests(own, own_id, stu):
    sid = await mkset('C2', exam='JEE Main')
    aid_s = await complete_practice(own, sid)
    a = await DB.tejas_attempts.find_one({'id': aid_s}, {'_id': 0})
    r = await own.get(f'/api/attempts/{aid_s}/cohort'); d = J(r)
    check("C2: staff cohort -> state 'unavailable' + staff reason", r.status_code == 200 and d.get('state') == 'unavailable' and 'Staff practice attempts are kept out of student statistics' in (d.get('reason') or ''), (r.status_code, r.text[:250]))
    check('C2: record() returns False for staff attempt', (await CH.record({**a, 'status': 'completed', 'mode': 'practice'}, a.get('ledger') or {'x': 1})) is False)
    check('C2: no staff cohort entry written', not await DB.tejas_cohort_entries.find_one({'user_id': own_id}))
    aid = await complete_practice(stu, sid)
    r = await stu.get(f'/api/attempts/{aid}/cohort'); d = J(r)
    check('C2: student cohort not blocked by staff rule', r.status_code == 200 and d.get('state') != 'unavailable', (r.status_code, r.text[:250]))
    me = J(await stu.get('/api/auth/me'))
    check('C2: student cohort entry recorded', bool(await DB.tejas_cohort_entries.find_one({'user_id': me.get('id') or (me.get('user') or {}).get('id')})), me)
    return sid


async def migration_tests(own_id):
    cid_s, cid_x = 'TEST_C2_cohort_staff_' + uuid.uuid4().hex[:6], 'TEST_C2_cohort_stu_' + uuid.uuid4().hex[:6]
    await DB.tejas_cohorts.insert_many([{'id': cid_s, 'dirty': False, 'generation': 'g0'}, {'id': cid_x, 'dirty': False, 'generation': 'g0'}])
    await DB.tejas_cohort_entries.insert_many([{'id': 'TEST_e1_' + uuid.uuid4().hex, 'cohort_id': cid_s, 'user_id': own_id},
                                               {'id': 'TEST_e2_' + uuid.uuid4().hex, 'cohort_id': cid_x, 'user_id': 'TEST_student_x'}])
    await DB.tejas_migrations.delete_one({'_id': 'staff-out-of-peer-stats-2026-11'})
    await LIB.run_cleanups()
    m = await DB.tejas_migrations.find_one({'_id': 'staff-out-of-peer-stats-2026-11'})
    check('C2 migration: run_cleanups marks staff-out-of-peer-stats-2026-11 done', m and m.get('state') == 'done', m)
    check('C2 migration: staff entry removed, student entry kept', not await DB.tejas_cohort_entries.find_one({'user_id': own_id}) and await DB.tejas_cohort_entries.find_one({'user_id': 'TEST_student_x'}))
    cs = await DB.tejas_cohorts.find_one({'id': cid_s}); cx = await DB.tejas_cohorts.find_one({'id': cid_x})
    check('C2 migration: affected cohort dirty + new generation; other untouched', cs['dirty'] is True and cs['generation'] != 'g0' and cx['dirty'] is False and cx['generation'] == 'g0', (cs, cx))
    await DB.tejas_cohort_entries.insert_one({'id': 'TEST_e3_' + uuid.uuid4().hex, 'cohort_id': cid_s, 'user_id': own_id})
    again = await LIB.run_once('staff-out-of-peer-stats-2026-11', CH.remove_staff_entries, 'x')
    check('C2 migration: runs only once (second run is a no-op)', again is None and await DB.tejas_cohort_entries.find_one({'user_id': own_id}), again)
    await DB.tejas_cohort_entries.delete_many({'user_id': own_id})


# ---------------- C3 safe index builds ----------------
async def index_tests():
    await DB.tejas_ledgers.drop_indexes() if 'tejas_ledgers' in await DB.list_collection_names() else None
    await DB.tejas_ledgers.insert_many([{'_id': 'TEST_dup1', 'id': 'TEST_DUP'}, {'_id': 'TEST_dup2', 'id': 'TEST_DUP'}])
    await DB.tejas_users.drop_index('email_1') if 'email_1' in await DB.tejas_users.index_information() else None
    before = len(DBM.INDEX_PROBLEMS)
    err = None
    try: await DBM.indexes()
    except Exception as e: err = e
    check('C3: indexes() completes despite a failing unique index', err is None, repr(err))
    new = DBM.INDEX_PROBLEMS[before:]
    check('C3: INDEX_PROBLEMS records tejas_ledgers id failure', any(p['collection'] == 'tejas_ledgers' and 'id' in p['keys'] for p in new), new)
    check('C3: later indexes still built (users email unique)', 'email_1' in await DB.tejas_users.index_information())
    rep = await INT.run('test194', repair=False)
    rep = rep if isinstance(rep, dict) and 'index_problems' in rep else ((await DB.tejas_operations.find_one({'id': 'integrity'})) or {}).get('report', {})
    check('C3: integrity report carries index_problems', any(p['collection'] == 'tejas_ledgers' for p in rep.get('index_problems', [])), str(rep)[:300])
    await DB.tejas_ledgers.delete_many({'_id': {'$in': ['TEST_dup1', 'TEST_dup2']}})


# ---------------- C4 series CAS ----------------
async def series_tests(own):
    r = await own.post('/api/admin/catalog/exams', json={'name': 'CASX' + secrets.token_hex(2).upper(), 'short': 'CX', 'subjects': ['Physics', 'Chemistry', 'Mathematics'], 'color': 'rose'})
    slug = J(r).get('slug')
    r = await own.post(f'/api/admin/catalog/exams/{slug}/sections', json={'name': 'All India Test Series', 'description': '', 'layout': 'list', 'kind': 'aits',
                       'first_date': '2027-03-20', 'days': 5, 'open_time': '09:00', 'last_start': '11:00', 'minutes': 10, 'correct': 4, 'wrong': -1})
    sid = J(r).get('series_id'); check('C4 setup: custom series', r.status_code == 200 and sid, r.text[:200])
    cfg = await series_admin.series_cfg(sid)
    w = series_admin.window('2027-03-21', cfg)
    pid = await mkset('CAS', exam=slug, series_id=sid, series_date='2027-03-21', series_window=w, series_import=True, live_enabled=True, start_at=w['opens_at'], end_at=w['closes_at'], test_kind='mock')
    r = await own.put(f'/api/admin/master/series/{sid}', json={'open_time': '08:00'})
    s = await DB.tejas_sets.find_one({'id': pid})
    check('C4: normal settings save 200 and paper window moved', r.status_code == 200 and s['series_window']['opens_at'] < w['opens_at'] and s['revision'] == 2 and s['series_date'] == '2027-03-21', (r.status_code, r.text[:200], s.get('revision')))
    orig = series_admin.window; hit_ = {'n': 0}
    def racing(day, c):
        out = orig(day, c)
        if c.get('open_time') == '07:30' and not hit_['n']:
            hit_['n'] = 1
            asyncio.get_event_loop().create_task(DB.tejas_sets.update_one({'id': pid}, {'$inc': {'revision': 1}, '$set': {'title': 'TEST_changed'}}))
        return out
    # bump the revision between read and write
    await DB.tejas_sets.update_one({'id': pid}, {'$set': {}}) if False else None
    rows_find = series_admin.sets.find
    class Stale:
        def __init__(s, cur): s.cur = cur
        async def to_list(s, n):
            rows = await s.cur.to_list(n)
            await DB.tejas_sets.update_one({'id': pid}, {'$inc': {'revision': 1}, '$set': {'title': 'TEST_changed'}})
            return rows
    series_admin.sets.find = lambda *a, **k: Stale(rows_find(*a, **k)) if a and a[0] == {'series_id': sid} else rows_find(*a, **k)
    try:
        r = await own.put(f'/api/admin/master/series/{sid}', json={'open_time': '07:30'})
    finally:
        series_admin.sets.find = rows_find
    s2 = await DB.tejas_sets.find_one({'id': pid}); cfg2 = await series_admin.series_cfg(sid)
    check('C4: paper changed meanwhile -> re-read and saved (200), no half-saved series', r.status_code == 200, (r.status_code, r.text[:200]))
    check('C4: concurrent change kept, window moved, series config saved', s2['title'] == 'TEST_changed' and s2['series_window']['opens_at'] < s['series_window']['opens_at'] and cfg2.get('open_time') == '07:30', (s2['title'], cfg2.get('open_time')))
    r = await own.put(f'/api/admin/master/series/{sid}', json={'open_time': '07:30'})
    s3 = await DB.tejas_sets.find_one({'id': pid})
    check('C4: saving the same settings again -> 200, window unchanged', r.status_code == 200 and s3['series_window'] == s2['series_window'] and s3['title'] == 'TEST_changed', (r.status_code, r.text[:200]))
    r = await own.put(f'/api/admin/master/series/{sid}', json={'days': 1})
    s4 = await DB.tejas_sets.find_one({'id': pid})
    check('C4: shrinking days still unassigns the paper (moved 1)', r.status_code == 200 and J(r).get('moved') == 1 and not s4.get('series_date'), (r.status_code, r.text[:200], s4.get('series_date')))


# ---------------- C7 owner-only QA cleanup ----------------
async def qa_cleanup_tests(own, rev, stu, burst_phones, burst_clients, keep_phone):
    prefix = burst_phones[0][:-4]
    t0 = time.time() - 3600
    # an old account with the same prefix (created before the cut-off) must stay
    old_phone = prefix + '9999'
    oc = client(); r = await oc.post('/api/auth/phone/signup', json={'phone': old_phone, 'pin': '4826', 'confirm_pin': '4826'})
    await DB.tejas_phone_profiles.update_one({'phone': old_phone}, {'$set': {'created_at': t0 - 86400}})
    ids = [p['id'] for p in await DB.tejas_phone_profiles.find({'phone': {'$in': burst_phones}}, {'id': 1}).to_list(None)]
    keep = await DB.tejas_phone_profiles.find_one({'phone': keep_phone}); old = await DB.tejas_phone_profiles.find_one({'phone': old_phone})
    cid = 'TEST_C7_cohort_' + uuid.uuid4().hex[:6]
    await DB.tejas_cohorts.insert_one({'id': cid, 'dirty': False, 'generation': 'g0'})
    for i, u in enumerate(ids[:5] + [keep['id'], old['id']]):
        await DB.tejas_attempts.insert_one({'id': f'TEST_C7_a{i}_' + uuid.uuid4().hex[:6], 'user_id': u, 'status': 'completed', 'set_id': 'x', 'start_key': uuid.uuid4().hex})
        for coll in ('tejas_ledgers', 'tejas_saved_tests', 'tejas_question_reports', 'tejas_reviews', 'tejas_score_versions', 'tejas_preflight', 'tejas_jobs', 'tejas_solution_requests'):
            await DB[coll].insert_one({'id': f'TEST_C7_{coll}_{i}_' + uuid.uuid4().hex[:6], 'user_id': u})
        await DB.tejas_cohort_entries.insert_one({'id': f'TEST_C7_e{i}_' + uuid.uuid4().hex[:6], 'cohort_id': cid, 'user_id': u})
    body = {'prefix': prefix, 'created_after': t0}
    r = await client().post(URL, json=body); check('C7: anon -> 401/403', r.status_code in (401, 403), r.status_code)
    r = await rev.post(URL, json=body); check('C7: reviewer -> 403', r.status_code == 403, r.status_code)
    r = await stu.post(URL, json=body); check('C7: student -> 401/403', r.status_code in (401, 403), r.status_code)
    r = await own.post(URL, json={**body, 'prefix': '+916'}); check("C7: prefix '+916' alone -> 422", r.status_code == 422, r.status_code)
    r = await own.post(URL, json={**body, 'prefix': '+915123456'}); check("C7: prefix '+915…' -> 422", r.status_code == 422, r.status_code)
    r = await own.post(URL, json={**body, 'created_after': 100}); check('C7: created_after too old -> 422', r.status_code == 422, r.status_code)
    r = await own.post(URL, json={**body, 'created_after': int(t0)}); d = J(r)
    check('C7: integer created_after accepted (dry run)', r.status_code == 200, (r.status_code, r.text[:200]))
    r = await own.post(URL, json=body); d = J(r)
    check('C7: dry run default -> would_remove 50 accounts / 5 attempts, nothing removed', r.status_code == 200 and d.get('dry_run') is True and d['would_remove'] == {'accounts': 50, 'attempts': 5} and await DB.tejas_phone_profiles.count_documents({'id': {'$in': ids}}) == 50, (r.status_code, r.text[:300]))
    r = await own.post(URL, json={**body, 'dry_run': False}); check('C7: real run without confirm -> 422', r.status_code == 422, (r.status_code, r.text[:200]))
    r = await own.post(URL, json={**body, 'dry_run': False, 'confirm': 'yes'}); check('C7: wrong confirm -> 422', r.status_code == 422, r.status_code)
    check('C7: nothing removed by rejected calls', await DB.tejas_phone_profiles.count_documents({'id': {'$in': ids}}) == 50)
    async def snap(uid_):
        return [await DB[c].count_documents({'user_id': uid_}) for c in ('tejas_attempts', 'tejas_cohort_entries', 'tejas_ledgers', 'tejas_sessions', 'tejas_jobs')]
    before = {k: await snap(u['id']) for k, u in (('other-prefix', keep), ('old same-prefix', old))}
    r = await burst_clients[3].get('/api/auth/me'); check('C7 setup: test student session valid before removal', r.status_code == 200, r.status_code)
    r = await own.post(URL, json={**body, 'dry_run': False, 'confirm': CONFIRM}); d = J(r)
    rm = d.get('removed', {})
    check('C7: real run 200, removed 50 accounts + 5 attempts', r.status_code == 200 and rm.get('accounts') == 50 and rm.get('attempts') == 5, (r.status_code, r.text[:400]))
    check('C7: removed counts for by-user collections = 5 each, cohort entries 5', all(rm.get(k) == 5 for k in ('ledgers', 'saved_tests', 'question_reports', 'reviews', 'score_versions', 'preflight', 'jobs', 'solution_requests', 'cohort_entries')), rm)
    check('C7: sessions of removed accounts deleted', rm.get('sessions', 0) >= 50, rm.get('sessions'))
    left = sum([await DB[c].count_documents({'user_id': {'$in': ids}}) for c in ('tejas_attempts', 'tejas_ledgers', 'tejas_sessions', 'tejas_cohort_entries', 'tejas_jobs')])
    check('C7: no rows left for removed ids', left == 0 and await DB.tejas_phone_profiles.count_documents({'id': {'$in': ids}}) == 0, left)
    c = await DB.tejas_cohorts.find_one({'id': cid}); check('C7: cohort marked dirty + new generation', c['dirty'] is True and c['generation'] != 'g0', c)
    for name, u in (('other-prefix', keep), ('old same-prefix', old)):
        after = await snap(u['id'])
        ok = bool(await DB.tejas_phone_profiles.find_one({'id': u['id']})) and after == before[name] and after[0] >= 1
        check(f'C7: {name} account and its data untouched', ok, (before[name], after))
    r = await burst_clients[3].get('/api/auth/me'); check('C7: removed student session no longer valid', r.status_code == 401, (r.status_code, r.text[:150]))
    r = await client().post('/api/auth/phone', json={'phone': burst_phones[4], 'pin': '4826'}); check('C7: removed number cannot sign in', r.status_code in (401, 404, 422), (r.status_code, r.text[:150]))
    r = await client().post('/api/auth/phone', json={'phone': old_phone, 'pin': '4826'}); check('C7: old same-prefix account still signs in', r.status_code == 200, r.status_code)
    au = await DB.tejas_audit.find_one({'action': 'QA test accounts removed'}) or await DB.tejas_audits.find_one({'action': 'QA test accounts removed'})
    check('C7: audit row written', bool(au), au)
    r = await own.post(URL, json={**body, 'dry_run': False, 'confirm': CONFIRM}); d = J(r)
    check('C7: second real run idempotent (0 accounts)', r.status_code == 200 and d.get('would_remove', {}).get('accounts') == 0, r.text[:200])


async def main():
    check('no customer DB handles', not H.leftover_real_handles(), H.leftover_real_handles())
    await H.tdbmod.indexes(); await structure.seed()
    try:
        await gate_tests()
        own, own_id = await mkstaff('owner', 'own194'); rev, _ = await mkstaff('reviewer', 'rev194')
        prefix = '+916' + f'{secrets.randbelow(10 ** 5):05d}'
        keep_phone = '+917' + f'{secrets.randbelow(10 ** 9):09d}'
        stu = client(); r = await stu.post('/api/auth/phone/signup', json={'phone': keep_phone, 'pin': '4826', 'confirm_pin': '4826'})
        check('setup: other-prefix student signs up', r.status_code == 200, r.text[:200])
        phones, cs = await signup_burst(prefix)
        await cohort_tests(own, own_id, stu)
        await migration_tests(own_id)
        await index_tests()
        await series_tests(own)
        await qa_cleanup_tests(own, rev, stu, phones, cs, keep_phone)
    except Exception as e:
        import traceback; traceback.print_exc(); check('no crash', False, repr(e))
    finally:
        await H.tdbmod.client.drop_database(H.TEST_DB)
        print('dropped', H.TEST_DB)
    f = [r for r in RESULTS if not r[1]]
    print(f'TOTAL {len(RESULTS)} PASS {len(RESULTS) - len(f)} FAIL {len(f)}')


if __name__ == '__main__':
    asyncio.run(main())
