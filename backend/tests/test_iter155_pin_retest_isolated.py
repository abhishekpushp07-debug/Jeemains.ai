"""TEST-ONLY iteration 155: narrow retest of iteration-154 PIN bugs + ISOLATED two-cookie PYQ attempt proof.
REAL FastAPI app over httpx ASGITransport (explicit client peer tuple), REAL JWT cookies, NO auth.current override,
isolated DB tejas_isolated_iter155 (dropped before/after). Synthetic random credentials only. NOT native/prod proof.
Run (foreground): cd /app/backend/tests && python -m pytest test_iter155_pin_retest_isolated.py -p no:cacheprovider -q -n0 -s
"""
import asyncio, json, secrets, time, uuid
from datetime import datetime, timezone, timedelta
from pathlib import Path
import httpx, pytest
from motor.motor_asyncio import AsyncIOMotorCollection
from pymongo.errors import PyMongoError
import iso_harness_iter155 as H
from tejas import auth

LOOP = asyncio.new_event_loop()
asyncio.set_event_loop(LOOP)
run = LOOP.run_until_complete
TDB = H.TDB
OWNER_PW = 'T155-' + secrets.token_urlsafe(14)
OWNER = {'id': str(uuid.uuid4()), 'email': 'test155-owner@example.com', 'role': 'owner'}
CTX = {}
PROOF = Path('/app/test_reports/iter155_isolated_pyq_proof.json')
PRIVATE_A, PRIVATE_B = ('10.81.4.212', 40001), ('10.81.4.213', 40002)


def pin():
    return f'{secrets.randbelow(10000):04d}'


_n = [0]


def num():
    _n[0] += 1
    return f'99025{_n[0]:05d}'


def fresh_window():
    H.OFFSET[0] += 1800


def client(peer=('127.0.0.1', 123)):
    return httpx.AsyncClient(transport=httpx.ASGITransport(app=H.app, raise_app_exceptions=False, client=peer),
                             base_url='https://api.test.example', headers={'Origin': H.ORIGIN}, timeout=300)


def J(r):
    j = r.json()
    return j.get('data') if isinstance(j, dict) and 'data' in j and 'meta' in j else j


async def signup(c, phone, p):
    return await c.post('/api/auth/phone/signup', json={'phone': phone, 'pin': p, 'confirm_pin': p})


async def login(c, phone, p):
    return await c.post('/api/auth/phone', json={'phone': phone, 'pin': p})


def legacy_cookie(c, user_id, sid):
    u = {'id': user_id, 'access_type': 'unverified_phone'}
    c.cookies.set('access_token', auth.token(u, sid, 'access', 600), domain='api.test.example')
    c.cookies.set('refresh_token', auth.token(u, sid, 'refresh', 600), domain='api.test.example')


def exp():
    return datetime.now(timezone.utc) + timedelta(days=1)


@pytest.fixture(scope='module', autouse=True)
def isolated():
    assert H.TEST_DB != H.REAL_DB and not H.leftover_real_handles() and not H.app.dependency_overrides
    run(H.tdbmod.client.drop_database(H.TEST_DB))
    run(H.tdbmod.indexes())
    run(TDB.tejas_users.insert_one({**OWNER, 'name': 'TEST owner', 'exam': 'JEE Main', 'access_type': 'staff_password',
                                    'password_hash': auth.hashpw(OWNER_PW), 'created_at': 0}))
    yield
    run(H.tdbmod.client.drop_database(H.TEST_DB))
    assert H.TEST_DB not in run(H.tdbmod.client.list_database_names())


# ---------- limiter: private/loopback peers have no IP bucket ----------
def test_private_shared_ingress_peers_do_not_global_429():
    async def go():
        fresh_window()
        codes = []
        for i in range(70):  # 70 different accounts across the two ingress peers, wrong PIN each
            async with client(PRIVATE_A if i % 2 else PRIVATE_B) as c:
                codes.append((await login(c, num(), '0000')).status_code)
        assert 429 not in codes and set(codes) == {401}, codes
        # each number still fails at 6th
        phone = num()
        seq = []
        for i in range(6):
            async with client(PRIVATE_A if i % 2 else PRIVATE_B) as c:
                seq.append((await login(c, phone, '0000')).status_code)
        assert seq == [401] * 5 + [429], seq
        async with client(('127.0.0.1', 5)) as c:
            r = None
            for _ in range(65):
                r = await login(c, num(), '0000')
            assert r.status_code == 401
    run(go())


def test_public_peer_60_not_bypassable_by_forwarded_headers_and_peers_separate():
    async def go():
        fresh_window()
        spoof = lambda i: {'X-Forwarded-For': f'1.2.{i % 250}.{i % 200 + 1}', 'CF-Connecting-IP': f'9.9.{i % 250}.1',
                           'X-Real-IP': f'5.5.{i % 250}.1', 'Forwarded': f'for=7.7.{i % 250}.1'}
        codes = []
        async with client(('8.8.8.8', 999)) as c:
            for i in range(62):
                codes.append((await login(c, num(), '0000')).status_code)
        assert codes[:60] == [401] * 60 and codes[60:] == [429, 429], codes[55:]
        fresh_window()
        codes = []
        async with client(('8.8.4.4', 999)) as c:
            for i in range(61):
                codes.append((await c.post('/api/auth/phone', json={'phone': num(), 'pin': '0000'}, headers=spoof(i))).status_code)
        assert codes[59] == 401 and codes[60] == 429, codes[55:]
        # a different public peer in the same window is unaffected
        async with client(('1.1.1.1', 999)) as c:
            assert (await login(c, num(), '0000')).status_code == 401
        r = None
        async with client(('8.8.4.4', 999)) as c:
            r = await login(c, num(), '0000')
        assert r.status_code == 429 and int(r.headers['retry-after']) > 0
    run(go())


# ---------- success clears number key; failure counter still blocks ----------
def test_six_plus_successful_logins_then_failure_blocks_sixth():
    async def go():
        fresh_window()
        phone, p = num(), pin()
        async with client() as c:
            assert (await signup(c, phone, p)).status_code == 200
        ok = []
        for _ in range(8):
            async with client() as c:
                ok.append((await login(c, phone, p)).status_code)
        assert ok == [200] * 8, ok
        wrong = f'{(int(p) + 1) % 10000:04d}'
        seq = []
        for _ in range(6):
            async with client() as c:
                seq.append((await login(c, phone, wrong)).status_code)
        assert seq == [401] * 5 + [429], seq
        async with client() as c:
            CTX['correct_after_lock'] = (await login(c, phone, p)).status_code
        print('correct PIN during lockout ->', CTX['correct_after_lock'])
        assert CTX['correct_after_lock'] == 429
        # interleave: 4 wrong + 1 correct resets counter (documented behaviour)
        fresh_window()
        seq = []
        for i in range(10):
            async with client() as c:
                seq.append((await login(c, phone, p if i == 4 else wrong)).status_code)
        print('4 wrong, 1 correct, 5 wrong ->', seq)
        CTX['reset_by_success_seq'] = seq
    run(go())


# ---------- legacy profile with missing/incorrect access_type/role stays student ----------
@pytest.mark.parametrize('extra', [{}, {'role': 'owner', 'access_type': 'staff_password'}, {'role': 'reviewer'}])
def test_legacy_profile_tampered_fields_first_pin_and_relogin_student(extra):
    async def go():
        fresh_window()
        legacy, lid = num(), str(uuid.uuid4())
        await TDB.tejas_phone_profiles.insert_one({'_id': lid, 'id': lid, 'phone': '+91' + legacy, 'name': 'Learner', 'created_at': 0, **extra})
        sid = str(uuid.uuid4())
        await TDB.tejas_sessions.insert_one({'id': sid, 'user_id': lid, 'access_type': 'unverified_phone', 'expires_at': exp()})
        async with client() as c:
            legacy_cookie(c, lid, sid)
            before = J(await c.get('/api/auth/me'))
            assert before['role'] == 'student' and before['access_type'] == 'unverified_phone' and before['pin_configured'] is False
            r = await c.post('/api/auth/pin', json={'phone': legacy, 'new_pin': '0808', 'confirm_pin': '0808'})
            assert r.status_code == 200, r.text
            after = J(r)
            assert after['id'] == lid and after['role'] == 'student' and after['pin_configured'] is True
            assert J(await c.get('/api/auth/me'))['role'] == 'student'
            assert (await c.get('/api/admin/students')).status_code == 403
        doc = await TDB.tejas_phone_profiles.find_one({'id': lid})
        assert doc['pin_version'] == 1 and doc['pin_hash'].startswith('$2b$')
        news = await TDB.tejas_sessions.find({'user_id': lid}).to_list(10)
        assert [s.get('pin_version') for s in news] == [1] and all(s['access_type'] == 'unverified_phone' for s in news)
        async with client() as c:
            legacy_cookie(c, lid, sid)
            assert (await c.get('/api/auth/me')).status_code == 401
        async with client() as c:
            r = await login(c, legacy, '0808')
            assert r.status_code == 200 and J(r)['role'] == 'student' and J(r)['id'] == lid, r.text
            assert (await c.get('/api/admin/students')).status_code == 403
            assert (await c.get('/api/studio/sets')).status_code in (401, 403, 404)
    run(go())


# ---------- physical cleanup scope ----------
def test_pin_change_deletes_only_old_same_user_student_sessions():
    async def go():
        fresh_window()
        phone, p = num(), pin()
        async with client() as c:
            u = J(await signup(c, phone, p))
        async with client() as c2:
            o = J(await signup(c2, num(), pin()))
        uid_ = u['id']
        rows = {'missing': {}, 'v0': {'pin_version': 0}, 'future': {'pin_version': 9}}
        for k, extra in rows.items():
            await TDB.tejas_sessions.insert_one({'id': 'TEST155_' + k, 'user_id': uid_, 'access_type': 'unverified_phone', 'expires_at': exp(), **extra})
        await TDB.tejas_sessions.insert_one({'id': 'TEST155_other', 'user_id': o['id'], 'access_type': 'unverified_phone', 'pin_version': 0, 'expires_at': exp()})
        await TDB.tejas_sessions.insert_one({'id': 'TEST155_staff', 'user_id': uid_, 'access_type': 'staff_password', 'credential_generation': 0, 'expires_at': exp()})
        async with client() as c:
            r1 = await login(c, phone, p)
            old_sid = (await TDB.tejas_sessions.find({'user_id': uid_, 'pin_version': 1}).to_list(10))
            np = f'{(int(p) + 7) % 10000:04d}'
            r = await c.post('/api/auth/pin', json={'phone': phone, 'new_pin': np, 'confirm_pin': np})
            assert r.status_code == 200, r.text
            assert (await c.get('/api/auth/me')).status_code == 200
        left = {s['id']: s.get('pin_version') for s in await TDB.tejas_sessions.find({'user_id': uid_}).to_list(50)}
        print('remaining same-user sessions:', left)
        assert 'TEST155_missing' not in left and 'TEST155_v0' not in left
        assert not any(v == 1 for v in left.values()) and len(old_sid) >= 1
        assert left.get('TEST155_future') == 9 and 'TEST155_staff' in left and 2 in left.values()
        assert await TDB.tejas_sessions.count_documents({'id': 'TEST155_other'}) == 1
        CTX['cleanup'] = (phone, np, uid_)
    run(go())


def test_cleanup_pymongo_error_still_logically_fenced():
    phone, p, uid_ = CTX['cleanup']
    orig = AsyncIOMotorCollection.delete_many

    async def boom(self, *a, **k):
        if self.name == 'tejas_sessions':
            raise PyMongoError('TEST injected cleanup failure')
        return await orig(self, *a, **k)

    async def go():
        fresh_window()
        async with client() as old:
            assert (await login(old, phone, p)).status_code == 200
            old_cookies = dict(old.cookies.items())
        AsyncIOMotorCollection.delete_many = boom
        try:
            async with client() as c:
                assert (await login(c, phone, p)).status_code == 200
                np = f'{(int(p) + 3) % 10000:04d}'
                r = await c.post('/api/auth/pin', json={'phone': phone, 'new_pin': np, 'confirm_pin': np})
                assert r.status_code == 200, r.text
                assert (await c.get('/api/auth/me')).status_code == 200
        finally:
            AsyncIOMotorCollection.delete_many = orig
        stale = await TDB.tejas_sessions.count_documents({'user_id': uid_, 'pin_version': 2})
        assert stale >= 1  # cleanup was really skipped
        async with client() as old:
            for k, v in old_cookies.items():
                old.cookies.set(k, v, domain='api.test.example')
            assert (await old.get('/api/auth/me')).status_code == 401
            assert (await old.post('/api/auth/refresh')).status_code == 401
        async with client() as c:
            assert (await login(c, phone, p)).status_code == 401
            assert (await login(c, phone, np)).status_code == 200
        CTX['cleanup'] = (phone, np, uid_)
    run(go())


def test_concurrent_changes_and_delayed_old_login_no_resurrection():
    phone, p, uid_ = CTX['cleanup']
    async def go():
        fresh_window()
        async with client() as c:
            assert (await login(c, phone, p)).status_code == 200
            pins = [f'{(int(p) + k) % 10000:04d}' for k in (11, 12, 13)]
            rs = await asyncio.gather(*[c.post('/api/auth/pin', json={'phone': phone, 'new_pin': x, 'confirm_pin': x}) for x in pins])
        codes = sorted(r.status_code for r in rs)
        assert codes == [200, 409, 409], codes
        doc = await TDB.tejas_phone_profiles.find_one({'id': uid_}, {'_id': 0})
        win = pins[[r.status_code for r in rs].index(200)]
        from fastapi import Response, HTTPException
        before = await TDB.tejas_sessions.count_documents({'user_id': uid_})
        with pytest.raises(HTTPException) as e:
            await auth.new_session({**doc, 'pin_version': doc['pin_version'] - 1}, Response())
        assert e.value.status_code == 401
        assert await TDB.tejas_sessions.count_documents({'user_id': uid_}) == before
        assert await TDB.tejas_sessions.count_documents({'user_id': uid_, 'access_type': 'unverified_phone', 'pin_version': {'$lt': doc['pin_version']}}) == 0
        async with client() as c:
            for x in pins:
                assert (await login(c, phone, x)).status_code == (200 if x == win else 401)
    run(go())


# ---------- owner directory: phone sort + audit on actual tejas_audits ----------
def test_owner_directory_sorted_and_audited():
    async def go():
        fresh_window()
        for i in (7, 3, 9, 1):
            sid = str(uuid.uuid4())
            await TDB.tejas_phone_profiles.insert_one({'_id': sid, 'id': sid, 'phone': f'+9198155{i:05d}', 'pin_hash': '$2b$12$x', 'pin_version': 1})
        async with client() as c:
            assert (await c.post('/api/auth/login', json={'email': OWNER['email'], 'password': OWNER_PW})).status_code == 200
            a0 = await TDB.tejas_audits.count_documents({'action': 'student_directory_read', 'actor': OWNER['id']})
            d = J(await c.get('/api/admin/students'))
            phones = [x['phone'] for x in d['items']]
            assert phones == sorted(phones), phones[:5]
            s = J(await c.get('/api/admin/students', params={'q': '98155'}))
            assert [x['phone'] for x in s['items']] == ['+919815500001', '+919815500003', '+919815500007', '+919815500009']
            a1 = await TDB.tejas_audits.count_documents({'action': 'student_directory_read', 'actor': OWNER['id']})
            assert a1 == a0 + 2, (a0, a1)
            assert await TDB.tejas_audits.count_documents({'action': 'student_pin_changed'}) >= 1
    run(go())


# ---------- ISOLATED two-cookie PYQ attempt proof (not native/prod) ----------
async def _results(c, aid):
    for _ in range(40):
        r = await c.get(f'/api/attempts/{aid}/results')
        if r.status_code == 200:
            return J(r)
        assert r.status_code == 202, r.text
        await asyncio.sleep(0.3)
    raise AssertionError('grading never completed')


def test_isolated_two_cookie_sessions_same_student_pyq_flow():
    async def go():
        async with client() as o:
            assert (await o.post('/api/auth/login', json={'email': OWNER['email'], 'password': OWNER_PW})).status_code == 200
            v = {}
            for _ in range(150):
                v = J(await o.post('/api/studio/pyq-import/step', json={}))
                if v.get('phase') == 'complete':
                    break
            assert v.get('phase') == 'complete', v
        fresh_window()
        phone, p = num(), pin()
        async with client() as c:
            stu = J(await signup(c, phone, p))
        async with client(('10.81.4.212', 1)) as A, client(('10.81.4.213', 2)) as B:
            assert (await login(A, phone, p)).status_code == 200
            assert (await login(B, phone, p)).status_code == 200
            assert A.cookies.get('access_token') != B.cookies.get('access_token')
            cat = J(await A.get('/api/pyq/jee-main'))
            assert cat['total'] == 30
            pid = cat['items'][0]['id']
            assert (await A.post(f'/api/sets/{pid}/preflight', json={'test_response': 'ok'})).status_code == 200
            st = await A.post(f'/api/sets/{pid}/start', json={'start_key': 'TEST155_K_' + uuid.uuid4().hex, 'device_checked': True})
            assert st.status_code == 200, st.text
            a = J(st); aid = a['id']
            q0, q1 = a['questions'][0], a['questions'][1]
            r = await A.put(f'/api/attempts/{aid}/answers/{q0["id"]}', json={'value': 'A', 'revision': 1, 'request_id': 'TEST155_R_' + uuid.uuid4().hex})
            assert r.status_code == 200, r.text
            # session B resumes same attempt
            assert (await B.post(f'/api/sets/{pid}/preflight', json={'test_response': 'ok'})).status_code == 200
            rb = J(await B.post(f'/api/sets/{pid}/start', json={'start_key': 'TEST155_K_' + uuid.uuid4().hex, 'device_checked': True}))
            assert rb['id'] == aid and rb['deadline'] == a['deadline'] and q0['id'] in rb['answers']
            r = await B.put(f'/api/attempts/{aid}/answers/{q1["id"]}', json={'value': 'B', 'revision': 1, 'request_id': 'TEST155_R_' + uuid.uuid4().hex})
            assert r.status_code == 200, r.text
            ga = J(await A.get(f'/api/attempts/{aid}'))
            assert {q0['id'], q1['id']} <= set(ga['answers'])
            sub = await B.post(f'/api/attempts/{aid}/submit')
            assert sub.status_code in (200, 202), sub.text
            ra, rbres = await _results(A, aid), await _results(B, aid)
            assert ra['summary'] == rbres['summary']
            qsol = next(q for q in ra['questions'] if q.get('solution_asset_count'))
            sol = await A.get(f'/api/attempts/{aid}/questions/{qsol["id"]}/asset/solution/0')
            assert sol.status_code == 200 and len(sol.content) > 1000, sol.status_code
            so = await B.post(f'/api/attempts/{aid}/questions/{qsol["id"]}/solution-open')
            assert so.status_code == 200
            # reattempt via session B creates new attempt; old result intact
            assert (await B.post(f'/api/sets/{pid}/preflight', json={'test_response': 'ok'})).status_code == 200
            a2 = J(await B.post(f'/api/sets/{pid}/start', json={'start_key': 'TEST155_K_' + uuid.uuid4().hex, 'device_checked': True}))
            assert a2['id'] != aid and a2['answers'] == {}
            again = await _results(A, aid)
            assert again['summary'] == ra['summary']
            hist = J(await A.get('/api/attempts'))
            items = hist['items'] if isinstance(hist, dict) else hist
            ids = {x['id'] for x in items}
            assert {aid, a2['id']} <= ids
            async with client() as other:
                assert (await signup(other, num(), pin())).status_code == 200
                assert (await other.get(f'/api/attempts/{aid}/results')).status_code == 404
        PROOF.write_text(json.dumps({'ISOLATED': True, 'NOT_NATIVE_OR_PROD_PROOF': True, 'db': H.TEST_DB,
            'student_id': stu['id'], 'paper_id': pid, 'attempt_id': aid, 'reattempt_id': a2['id'],
            'solution_question_id': qsol['id'], 'solution_png_bytes': len(sol.content), 'submit_status': sub.status_code,
            'summary_score': ra['summary'].get('score'), 'storage_puts': list(H.PUTS)}, indent=1))
    run(go())


def test_zz_no_real_handles_no_puts():
    assert not H.leftover_real_handles() and not H.PUTS
