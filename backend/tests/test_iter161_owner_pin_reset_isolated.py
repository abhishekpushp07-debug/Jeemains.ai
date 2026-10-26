"""TEST-ONLY iteration 161: owner-only student PIN reset POST /api/auth/owner/student-pin-reset.
REAL FastAPI app over httpx ASGITransport, REAL JWT cookies/sessions, NO dependency overrides, random isolated DB
(iso_harness_iter161) dropped before/after. Controlled clock (H.OFFSET). Never touches customer DB/credentials.
Run (foreground): cd /app/backend/tests && python -m pytest test_iter161_owner_pin_reset_isolated.py -p no:cacheprovider -q -s
"""
import asyncio, hashlib, logging, secrets, time, uuid
import httpx, pytest
from pymongo.errors import ConnectionFailure, OperationFailure
from motor.motor_asyncio import AsyncIOMotorCollection
import iso_harness_iter161 as H
from tejas import auth, phone as phone_mod

LOOP = asyncio.new_event_loop()
asyncio.set_event_loop(LOOP)
run = LOOP.run_until_complete
TDB = H.TDB
URL = '/api/auth/owner/student-pin-reset'
OWNER_PW = 'T161-' + secrets.token_urlsafe(14)
OWNER2_PW = 'T161b-' + secrets.token_urlsafe(14)
REV_PW = 'T161r-' + secrets.token_urlsafe(14)
OWNER = {'id': str(uuid.uuid4()), 'email': 'test161-owner@example.com', 'role': 'owner'}
OWNER2 = {'id': str(uuid.uuid4()), 'email': 'test161-owner2@example.com', 'role': 'owner'}
REV = {'id': str(uuid.uuid4()), 'email': 'test161-rev@example.com', 'role': 'reviewer'}
_n = [0]
BASE_WIN = [int(time.time() // 3600) + 50]


def num():
    _n[0] += 1
    return f'99161{_n[0]:05d}'


def pin(avoid=None):
    while True:
        p = f'{secrets.randbelow(10000):04d}'
        if p != avoid:
            return p


def fresh_clock():
    """New clock hour => fresh 15-min windows for every limiter."""
    BASE_WIN[0] += 1
    H.OFFSET[0] = BASE_WIN[0] * 3600 + 5 - time.time()


def client(origin=None):
    return httpx.AsyncClient(transport=httpx.ASGITransport(app=H.app, raise_app_exceptions=False, client=('127.0.0.1', 123)),
                             base_url='https://api.test.example', headers={'Origin': origin or H.ORIGIN}, timeout=300)


def J(r):
    j = r.json()
    return j.get('data') if isinstance(j, dict) and 'data' in j and 'meta' in j else j


async def staff_client(acct, pw):
    c = client()
    r = await c.post('/api/auth/login', json={'email': acct['email'], 'password': pw})
    assert r.status_code == 200, r.text
    return c


async def student(ph=None, p=None):
    ph, p = ph or num(), p or pin()
    c = client()
    r = await c.post('/api/auth/phone/signup', json={'phone': ph, 'pin': p, 'confirm_pin': p})
    assert r.status_code == 200, r.text
    return c, ph, p, J(r)['id']


def body(ph, p, v, **extra):
    return {'phone': ph, 'new_pin': p, 'confirm_pin': p, 'expected_pin_version': v, **extra}


async def prof(sid):
    return await TDB.tejas_phone_profiles.find_one({'id': sid}, {'_id': 0})


@pytest.fixture(scope='module', autouse=True)
def isolated():
    assert H.TEST_DB != H.REAL_DB and H.TEST_DB.startswith('tejas_isolated_iter161_')
    assert not H.leftover_real_handles() and not H.app.dependency_overrides
    run(H.tdbmod.client.drop_database(H.TEST_DB))
    run(H.tdbmod.indexes())
    for a, pw in ((OWNER, OWNER_PW), (OWNER2, OWNER2_PW), (REV, REV_PW)):
        run(TDB.tejas_users.insert_one({**a, 'name': 'TEST staff', 'exam': 'JEE Main', 'access_type': 'staff_password',
                                        'password_hash': auth.hashpw(pw), 'created_at': 0}))
    fresh_clock()
    yield
    H.OFFSET[0] = 0
    run(H.tdbmod.client.drop_database(H.TEST_DB))
    assert H.TEST_DB not in run(H.tdbmod.client.list_database_names())


# ---- authorization matrix: anonymous/student/reviewer/revoked owner/cross-origin ----
def test_authz_matrix():
    async def go():
        fresh_clock()
        sc, ph, p, sid = await student()
        np = pin(p)
        async with client() as anon:
            r = await anon.post(URL, json=body(ph, np, 1))
            assert r.status_code == 401, r.text
            r = await anon.post(URL, json=body(ph, np, 1, role='owner'))
            assert r.status_code in (401, 422)
        r = await sc.post(URL, json=body(ph, np, 1))
        assert r.status_code == 403, r.text
        rv = await staff_client(REV, REV_PW)
        assert (await rv.post(URL, json=body(ph, np, 1))).status_code == 403
        o2 = await staff_client(OWNER2, OWNER2_PW)
        # cross-origin with a valid owner cookie must be blocked
        r = await o2.post(URL, json=body(ph, np, 1), headers={'Origin': 'https://evil.example'})
        assert r.status_code in (400, 403), (r.status_code, r.text)
        # revoke owner role in DB -> owner dep re-reads role
        await TDB.tejas_users.update_one({'id': OWNER2['id']}, {'$set': {'role': 'reviewer'}})
        assert (await o2.post(URL, json=body(ph, np, 1))).status_code == 403
        await TDB.tejas_users.update_one({'id': OWNER2['id']}, {'$set': {'role': 'unknown'}})
        assert (await o2.post(URL, json=body(ph, np, 1))).status_code in (401, 403)
        await TDB.tejas_users.update_one({'id': OWNER2['id']}, {'$set': {'role': 'owner'}})
        q = await prof(sid)
        assert q['pin_version'] == 1 and 'pin_reset_by' not in q
        for c in (sc, rv, o2):
            await c.aclose()
    run(go())


# ---- strict payload validation ----
def test_payload_validation():
    async def go():
        fresh_clock()
        _, ph, p, sid = await student()
        o = await staff_client(OWNER, OWNER_PW)
        bad = [
            body(ph, '1234', 1, role='owner'), body(ph, '1234', 1, token='x'), body(ph, '1234', True),
            body(ph, '1234', '1'), body(ph, '1234', 1.0), body(ph, '١٢٣٤', 1), body(ph, '12a4', 1), body(ph, '12345', 1),
            {'phone': ph, 'new_pin': '1234', 'confirm_pin': '4321', 'expected_pin_version': 1},
            {'phone': ph, 'new_pin': '1234', 'confirm_pin': '1234'}, body(ph, '1234', -1), body(123, '1234', 1),
            body(ph, 1234, 1),
        ]
        for b in bad:
            r = await o.post(URL, json=b)
            assert r.status_code == 422, (b, r.status_code, r.text)
            assert '"input"' not in r.text and 'pin_hash' not in r.text
            if isinstance(b.get('new_pin'), str):
                assert b['new_pin'] not in r.text
        # non-ASCII (Devanagari) phone digits
        dev = ph.translate(str.maketrans('0123456789', '०१२३४५६७८९'))
        r = await o.post(URL, json=body(dev, pin(p), 1))
        print('DEVANAGARI_PHONE_STATUS', r.status_code)
        q = await prof(sid)
        assert r.status_code == 422 and q['pin_version'] == 1, r.text
        await o.aclose()
    run(go())


# ---- happy path v1: receipt shape, sessions, login, snapshot, directory, audit ----
def test_reset_v1_full_flow():
    async def go():
        fresh_clock()
        sc, ph, p, sid = await student()
        other_c, oph, op, osid = await student()
        o = await staff_client(OWNER, OWNER_PW)
        # synthetic history linked to student
        hist = {'attempts': {'id': 'TEST161_' + uuid.uuid4().hex, 'user_id': sid, 'answers': {'q1': 'A'}, 'score': 7},
                'results': {'id': 'TEST161_' + uuid.uuid4().hex, 'user_id': sid, 'total': 7}}
        for k, d in hist.items():
            await TDB['tejas_' + k].insert_one(dict(d))
        await TDB.tejas_phone_profiles.update_one({'id': sid}, {'$set': {'name': 'TEST Name', 'exam': 'BITSAT', 'streak': 3}})
        before = await prof(sid)
        # second old student session
        s2 = client()
        assert (await s2.post('/api/auth/phone', json={'phone': ph, 'pin': p})).status_code == 200
        np = pin(p)
        logs = []
        h = logging.Handler(); h.emit = lambda rec: logs.append(rec.getMessage())
        logging.getLogger().addHandler(h)
        try:
            r = await o.post(URL, json=body('+91' + ph, np, 1))
        finally:
            logging.getLogger().removeHandler(h)
        assert r.status_code == 200, r.text
        d = J(r)
        assert set(d) == {'ok', 'student_id', 'pin_version', 'old_sessions_revoked'}, d
        assert d == {'ok': True, 'student_id': sid, 'pin_version': 2, 'old_sessions_revoked': True}
        assert 'set-cookie' not in r.headers and 'no-store' in r.headers.get('cache-control', '')
        for leak in (ph, np, '$2b$', 'pin_hash'):
            assert leak not in r.text
        for line in logs:
            assert ph not in line and np not in line and '$2b$' not in line, line
        # owner stays owner
        me = await o.get('/api/auth/me')
        assert me.status_code == 200 and J(me)['role'] == 'owner', me.text
        # old sessions dead (access + refresh)
        for c in (sc, s2):
            assert (await c.get('/api/auth/me')).status_code == 401
            assert (await c.post('/api/auth/refresh')).status_code == 401
        assert await TDB.tejas_sessions.count_documents({'user_id': sid}) == 0
        # other student + owner sessions intact
        assert (await other_c.get('/api/auth/me')).status_code == 200
        assert await TDB.tejas_sessions.count_documents({'user_id': OWNER['id']}) >= 1
        # login: old fails, new works, same id
        async with client() as c:
            assert (await c.post('/api/auth/phone', json={'phone': ph, 'pin': p})).status_code == 401
            r2 = await c.post('/api/auth/phone', json={'phone': ph, 'pin': np})
            assert r2.status_code == 200 and J(r2)['id'] == sid
            assert (await c.get('/api/auth/me')).status_code == 200
        after = await prof(sid)
        assert after['pin_hash'].startswith('$2b$') and after['pin_hash'] != before['pin_hash']
        assert after['pin_reset_by'] == OWNER['id'] and isinstance(after['pin_reset_at'], float)
        strip = lambda x: {k: v for k, v in x.items() if k not in ('pin_hash', 'pin_version', 'pin_reset_by', 'pin_reset_at', 'last_seen_at')}
        assert strip(after) == strip(before)
        for k, dct in hist.items():
            got = await TDB['tejas_' + k].find_one({'id': dct['id']}, {'_id': 0})
            assert got == dct, (k, got)
        # audit: actor/resource, no secrets
        a = await TDB.tejas_audit.find_one({'action': 'owner_student_pin_reset', 'resource': sid}, {'_id': 0}) \
            if 'tejas_audit' in await TDB.list_collection_names() else None
        if a is None:
            for coll in await TDB.list_collection_names():
                a = await TDB[coll].find_one({'action': 'owner_student_pin_reset', 'resource': sid}, {'_id': 0})
                if a:
                    break
        assert a and a['actor'] == OWNER['id'], a
        assert ph not in str(a) and np not in str(a) and '$2b$' not in str(a)
        # directory projection
        lst = J(await o.get('/api/admin/students', params={'q': ph}))
        assert lst['items'] == [{'id': sid, 'phone': '+91' + ph, 'pin_version': 2}], lst
        # stale version
        r = await o.post(URL, json=body(ph, pin(), 1))
        assert r.status_code == 409 and 'Refresh' in r.text
        for c in (sc, s2, other_c, o):
            await c.aclose()
    run(go())


# ---- legacy v0 profile (no pin_version/access_type/role) + normalized phone variants ----
def test_legacy_v0_and_phone_variants():
    async def go():
        fresh_clock()
        ph = num()
        sid = 'TEST161_legacy_' + uuid.uuid4().hex
        await TDB.tejas_phone_profiles.insert_one({'id': sid, 'phone': '+91' + ph, 'name': 'Legacy', 'created_at': 1.0})
        o = await staff_client(OWNER, OWNER_PW)
        assert J(await o.get('/api/admin/students', params={'q': ph}))['items'][0]['pin_version'] == 0
        assert (await o.post(URL, json=body(ph, '1111', 1))).status_code == 409
        np = pin()
        r = await o.post(URL, json=body('0' + ph, np, 0))
        assert r.status_code == 200 and J(r)['pin_version'] == 1, r.text
        for variant, v in (('91' + ph, 1), ('+91 ' + ph[:5] + ' ' + ph[5:], 2)):
            np = pin(np)
            r = await o.post(URL, json=body(variant, np, v))
            assert r.status_code == 200 and J(r)['student_id'] == sid and J(r)['pin_version'] == v + 1, (variant, r.text)
        assert await TDB.tejas_phone_profiles.count_documents({'phone': '+91' + ph}) == 1
        async with client() as c:
            r = await c.post('/api/auth/phone', json={'phone': ph, 'pin': np})
            assert r.status_code == 200 and J(r)['id'] == sid
        p = await prof(sid)
        assert p['pin_hash'].startswith('$2b$') and 'role' not in p and 'access_type' not in p
        await o.aclose()
    run(go())


# ---- nonexistent target / non-student profile: 409 and nothing created ----
def test_nonexistent_and_non_student_targets():
    async def go():
        fresh_clock()
        o = await staff_client(OWNER, OWNER_PW)
        ph = num()
        n0 = await TDB.tejas_phone_profiles.count_documents({})
        r = await o.post(URL, json=body(ph, '2468', 0))
        assert r.status_code == 409, r.text
        assert await TDB.tejas_phone_profiles.count_documents({}) == n0
        ph2 = num()
        await TDB.tejas_phone_profiles.insert_one({'id': 'TEST161_odd_' + uuid.uuid4().hex, 'phone': '+91' + ph2,
                                                   'role': 'owner', 'pin_version': 1, 'pin_hash': 'x'})
        assert (await o.post(URL, json=body(ph2, '2468', 1))).status_code == 409
        users_before = await TDB.tejas_users.find({}, {'_id': 0}).to_list(None)
        assert await TDB.tejas_users.find({}, {'_id': 0}).to_list(None) == users_before
        await o.aclose()
    run(go())


# ---- concurrency: 5 owner resets with same version -> exactly one wins; own-change race ----
def test_concurrent_resets_and_own_change_race():
    async def go():
        fresh_clock()
        lanes = H.app.state.admission.lanes['auth']
        old = lanes['limit']
        lanes['limit'] = 64
        try:
            _, ph, p, sid = await student()
            o = await staff_client(OWNER, OWNER_PW)
            pins = [f'{i}{i}{i}{i}' for i in range(5)]
            rs = await asyncio.gather(*[o.post(URL, json=body(ph, x, 1)) for x in pins])
            codes = sorted(r.status_code for r in rs)
            assert codes == [200, 409, 409, 409, 409], codes
            win = pins[[r.status_code for r in rs].index(200)]
            assert (await prof(sid))['pin_version'] == 2
            async with client() as c:
                assert (await c.post('/api/auth/phone', json={'phone': ph, 'pin': win})).status_code == 200
            # race: student own change vs owner reset at same version 2
            for rnd in range(3):
                fresh_clock()
                cur = (await prof(sid))['pin_version']
                sc = client()
                assert (await sc.post('/api/auth/phone', json={'phone': ph, 'pin': win})).status_code == 200
                own, rst = '7' * 3 + str(rnd), '8' * 3 + str(rnd)
                a, b = await asyncio.gather(
                    sc.post('/api/auth/pin', json={'phone': ph, 'new_pin': own, 'confirm_pin': own}),
                    o.post(URL, json=body(ph, rst, cur)))
                ok = [x for x in (a, b) if x.status_code == 200]
                assert len(ok) == 1, (a.status_code, a.text, b.status_code, b.text)
                win = own if a.status_code == 200 else rst
                assert (await prof(sid))['pin_version'] == cur + 1
                async with client() as c:
                    assert (await c.post('/api/auth/phone', json={'phone': ph, 'pin': win})).status_code == 200
                await sc.aclose()
            await o.aclose()
        finally:
            lanes['limit'] = old
    run(go())


# ---- physical cleanup scope: only old/missing student versions deleted ----
def test_cleanup_scope_keeps_new_version_and_others():
    async def go():
        fresh_clock()
        _, ph, p, sid = await student()
        from datetime import datetime, timezone, timedelta
        exp = datetime.now(timezone.utc) + timedelta(days=1)
        await TDB.tejas_sessions.insert_many([
            {'id': 'TEST161_nov', 'user_id': sid, 'access_type': 'unverified_phone', 'expires_at': exp},
            {'id': 'TEST161_newv', 'user_id': sid, 'access_type': 'unverified_phone', 'pin_version': 2, 'expires_at': exp},
            {'id': 'TEST161_staffshape', 'user_id': sid, 'access_type': 'staff_password', 'expires_at': exp}])
        o = await staff_client(OWNER, OWNER_PW)
        assert (await o.post(URL, json=body(ph, pin(p), 1))).status_code == 200
        left = {s['id'] for s in await TDB.tejas_sessions.find({'user_id': sid}).to_list(None)}
        assert left == {'TEST161_newv', 'TEST161_staffshape'}, left
        assert await TDB.tejas_sessions.count_documents({'user_id': OWNER['id']}) >= 1
        await o.aclose()
    run(go())


# ---- reset does NOT clear existing failed-PIN hourly lockout ----
def test_reset_keeps_failed_pin_lockout():
    async def go():
        fresh_clock()
        _, ph, p, sid = await student()
        hour = int(H.fake_now() // 3600)
        key = hashlib.sha256(f'pin:failed-hour:+91{ph}:{hour}'.encode()).hexdigest()
        await TDB.tejas_phone_limits.update_one({'_id': key}, {'$set': {'count': 20}}, upsert=True)
        o = await staff_client(OWNER, OWNER_PW)
        np = pin(p)
        assert (await o.post(URL, json=body(ph, np, 1))).status_code == 200
        async with client() as c:
            r = await c.post('/api/auth/phone', json={'phone': ph, 'pin': np})
            assert r.status_code == 429 and 'retry-after' in r.headers, r.text
        await o.aclose()
    run(go())


# ---- rate limits: target 5 / actor 10 per 15 min -> 429 Retry-After ----
def test_rate_limits_target_and_actor():
    async def go():
        fresh_clock()
        o = await staff_client(OWNER, OWNER_PW)
        _, ph, p, sid = await student()
        codes = []
        v = 1
        for i in range(6):
            r = await o.post(URL, json=body(ph, pin(), v))
            codes.append(r.status_code)
            if r.status_code == 200:
                v += 1
        assert codes == [200] * 5 + [429], codes
        assert 1 <= int(r.headers['retry-after']) <= 901
        assert 'Too many' in r.text and ph not in r.text
        fresh_clock()
        targets = [await student() for _ in range(11)]
        codes = [(await o.post(URL, json=body(t[1], pin(), 1))).status_code for t in targets]
        assert codes == [200] * 10 + [429], codes
        # other owner unaffected by actor bucket
        o2 = await staff_client(OWNER2, OWNER2_PW)
        assert (await o2.post(URL, json=body(targets[10][1], pin(), 1))).status_code == 200
        for c in [o, o2] + [t[0] for t in targets]:
            await c.aclose()
    run(go())


# ---- fault injection: audit failure, cleanup failure, limiter failure, mutation failure ----
def test_fault_injection():
    async def go():
        fresh_clock()
        o = await staff_client(OWNER, OWNER_PW)
        # central audit failure -> still 200, embedded receipt preserved, generic warning
        sc, ph, p, sid = await student()
        real_audit = phone_mod.audit
        async def bad_audit(*a, **k): raise OperationFailure('TEST audit down')
        phone_mod.audit = bad_audit
        logs = []
        h = logging.Handler(); h.emit = lambda rec: logs.append(rec.getMessage())
        logging.getLogger().addHandler(h)
        try:
            np = pin(p)
            r = await o.post(URL, json=body(ph, np, 1))
        finally:
            phone_mod.audit = real_audit
        assert r.status_code == 200, r.text
        q = await prof(sid)
        assert q['pin_reset_by'] == OWNER['id'] and q['pin_version'] == 2
        assert any('audit' in m.lower() for m in logs) and not any(ph in m or np in m for m in logs)
        # cleanup failure -> old cookie still fenced
        sc2, ph2, p2, sid2 = await student()
        real_dm = AsyncIOMotorCollection.delete_many
        async def bad_dm(self, *a, **k):
            if self.name == 'tejas_sessions':
                raise ConnectionFailure('TEST cleanup down')
            return await real_dm(self, *a, **k)
        AsyncIOMotorCollection.delete_many = bad_dm
        try:
            r = await o.post(URL, json=body(ph2, pin(p2), 1))
        finally:
            AsyncIOMotorCollection.delete_many = real_dm
        logging.getLogger().removeHandler(h)
        assert r.status_code == 200, r.text
        assert await TDB.tejas_sessions.count_documents({'user_id': sid2}) >= 1
        assert (await sc2.get('/api/auth/me')).status_code == 401
        assert (await sc2.post('/api/auth/refresh')).status_code == 401
        # limiter failure -> fail closed, no mutation
        _, ph3, p3, sid3 = await student()
        real_inc = phone_mod.increment
        async def bad_inc(*a, **k): raise ConnectionFailure('TEST limiter down')
        phone_mod.increment = bad_inc
        try:
            r = await o.post(URL, json=body(ph3, pin(p3), 1))
        finally:
            phone_mod.increment = real_inc
        assert r.status_code >= 500 or r.status_code == 503, r.text
        assert (await prof(sid3))['pin_version'] == 1
        async def none_inc(*a, **k): return None
        phone_mod.increment = none_inc
        try:
            r = await o.post(URL, json=body(ph3, pin(p3), 1))
        finally:
            phone_mod.increment = real_inc
        print('LIMITER_NONE_STATUS', r.status_code, r.text[:120])
        assert r.status_code != 200 and (await prof(sid3))['pin_version'] == 1
        # mutation failure -> fail closed
        real_fou = AsyncIOMotorCollection.find_one_and_update
        async def bad_fou(self, *a, **k):
            if self.name == 'tejas_phone_profiles':
                raise ConnectionFailure('TEST mutation down')
            return await real_fou(self, *a, **k)
        AsyncIOMotorCollection.find_one_and_update = bad_fou
        try:
            r = await o.post(URL, json=body(ph3, pin(p3), 1))
        finally:
            AsyncIOMotorCollection.find_one_and_update = real_fou
        assert r.status_code >= 500 and ph3 not in r.text, (r.status_code, r.text)
        assert (await prof(sid3))['pin_version'] == 1
        async with client() as c:
            assert (await c.post('/api/auth/phone', json={'phone': ph3, 'pin': p3})).status_code == 200
        for c in (sc, sc2, o):
            await c.aclose()
    run(go())


def test_no_real_handles_leaked():
    assert not H.leftover_real_handles()
