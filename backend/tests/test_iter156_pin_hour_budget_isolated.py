"""TEST-ONLY iteration 156: hourly failed-PIN budget + IP-before-account ordering + fail-closed limiter.
REAL FastAPI app over httpx ASGITransport with explicit client peer tuple, REAL JWT cookies, NO auth.current override,
random isolated DB (iso_harness_iter156) dropped before/after. Controlled clock (H.OFFSET), no real sleeps.
Run (foreground): cd /app/backend/tests && python -m pytest test_iter156_pin_hour_budget_isolated.py -p no:cacheprovider -q -s
"""
import asyncio, hashlib, secrets, time, uuid
import httpx, pytest
from pymongo.errors import ConnectionFailure, OperationFailure
from motor.motor_asyncio import AsyncIOMotorCollection
import iso_harness_iter156 as H
from tejas import auth, phone as phone_mod

LOOP = asyncio.new_event_loop()
asyncio.set_event_loop(LOOP)
run = LOOP.run_until_complete
TDB = H.TDB
OWNER_PW = 'T156-' + secrets.token_urlsafe(14)
OWNER = {'id': str(uuid.uuid4()), 'email': 'test156-owner@example.com', 'role': 'owner'}
VERIFY_CALLS = [0]
_real_verify = phone_mod.verify


def counting_verify(p, h):
    VERIFY_CALLS[0] += 1
    return _real_verify(p, h)


_n = [0]
BASE_HOUR = [int(time.time() // 3600) + 10]


def num():
    _n[0] += 1
    return f'99026{_n[0]:05d}'


def pin():
    return f'{secrets.randbelow(10000):04d}'


def wrong(p):
    return f'{(int(p) + 1) % 10000:04d}'


def set_clock(t):
    H.OFFSET[0] = t - time.time()


def new_hour(sec=5):
    """Jump the controlled clock to a fresh clock hour + sec seconds."""
    BASE_HOUR[0] += 1
    set_clock(BASE_HOUR[0] * 3600 + sec)
    return BASE_HOUR[0]


def hour_key(e164, hour):
    return hashlib.sha256(f'pin:failed-hour:{e164}:{hour}'.encode()).hexdigest()


def short_key(e164, t, action='login'):
    return hashlib.sha256(f'{action}:number:{e164}:{int(t // 900)}'.encode()).hexdigest()


async def count(key):
    d = await TDB.tejas_phone_limits.find_one({'_id': key})
    return d['count'] if d else 0


def client(peer=('127.0.0.1', 123)):
    return httpx.AsyncClient(transport=httpx.ASGITransport(app=H.app, raise_app_exceptions=False, client=peer),
                             base_url='https://api.test.example', headers={'Origin': H.ORIGIN}, timeout=300)


def J(r):
    j = r.json()
    return j.get('data') if isinstance(j, dict) and 'data' in j and 'meta' in j else j


async def signup(phone, p):
    async with client() as c:
        r = await c.post('/api/auth/phone/signup', json={'phone': phone, 'pin': p, 'confirm_pin': p})
        assert r.status_code == 200, r.text
        return J(r)


async def login(phone, p, peer=('127.0.0.1', 123), headers=None):
    async with client(peer) as c:
        return await c.post('/api/auth/phone', json={'phone': phone, 'pin': p}, headers=headers or {})


def no_secret(r):
    t = r.text
    assert '$2b$' not in t and 'pin_hash' not in t and 'access_token' not in t and 'set-cookie' not in r.headers


@pytest.fixture(scope='module', autouse=True)
def isolated():
    assert H.TEST_DB != H.REAL_DB and H.TEST_DB.startswith('tejas_isolated_iter156_')
    assert not H.leftover_real_handles() and not H.app.dependency_overrides
    run(H.tdbmod.client.drop_database(H.TEST_DB))
    run(H.tdbmod.indexes())
    run(TDB.tejas_users.insert_one({**OWNER, 'name': 'TEST owner', 'exam': 'JEE Main', 'access_type': 'staff_password',
                                    'password_hash': auth.hashpw(OWNER_PW), 'created_at': 0}))
    phone_mod.verify = counting_verify
    yield
    phone_mod.verify = _real_verify
    run(H.tdbmod.client.drop_database(H.TEST_DB))
    assert H.TEST_DB not in run(H.tdbmod.client.list_database_names())


# ---- interleaved 4 wrong + 1 correct cycles do NOT replenish hour budget; 21st check 429 before verify ----
def test_interleave_cycles_exact_20_then_429_before_verify():
    async def go():
        new_hour(5)
        ph, p = num(), pin()
        e = '+91' + ph
        await signup(ph, p)
        hk = hour_key(e, BASE_HOUR[0])
        seq = []
        last = None
        for cycle in range(5):
            for _ in range(4):
                seq.append((await login(ph, wrong(p))).status_code)
            v0 = VERIFY_CALLS[0]
            last = await login(ph, p)
            seq.append(last.status_code)
        # 20 failures retained across 4 successes; the 21st PIN check (here the CORRECT pin) waits
        assert seq == ([401] * 4 + [200]) * 4 + [401] * 4 + [429], seq
        assert VERIFY_CALLS[0] == v0, 'bcrypt verify ran for 21st check'
        assert 'incorrect PIN' in last.text and 'access_token' not in last.cookies
        no_secret(last)
        ra = int(last.headers['retry-after'])
        expect = (BASE_HOUR[0] + 1) * 3600 - H.fake_now()
        assert abs(ra - expect) <= 3 and ra > 900, (ra, expect)
        assert await count(hk) == 20, await count(hk)
        assert await count(short_key(e, H.fake_now())) == 5  # 4 wrong + the 429 after last reset
        # next 15-min window, same hour: short guard fresh, hourly still blocks wrong AND correct
        set_clock(BASE_HOUR[0] * 3600 + 905)
        v0 = VERIFY_CALLS[0]
        r = await login(ph, wrong(p))
        assert r.status_code == 429 and 'incorrect PIN' in r.text, r.text
        no_secret(r)
        assert abs(int(r.headers['retry-after']) - ((BASE_HOUR[0] + 1) * 3600 - H.fake_now())) <= 3
        rc = await login(ph, p)  # correct PIN also waits (explicit policy)
        assert rc.status_code == 429 and 'set-cookie' not in rc.headers, rc.text
        assert VERIFY_CALLS[0] == v0, 'bcrypt verify ran during hourly lockout'
        assert await count(hk) == 20
        # excess 429s never push budget past cap
        for _ in range(8):
            assert (await login(ph, p)).status_code == 429
        assert await count(hk) == 20, await count(hk)
        doc = await TDB.tejas_phone_limits.find_one({'_id': hk})
        assert doc.get('expires_at') is not None
        # next clock hour: fresh budget, correct PIN works
        set_clock((BASE_HOUR[0] + 1) * 3600 + 1)
        BASE_HOUR[0] += 1
        r = await login(ph, p)
        assert r.status_code == 200 and 'access_token' in r.cookies, r.text
    run(go())


# ---- many successful sign-ins consume 0 budget ----
def test_many_successes_consume_zero_budget():
    async def go():
        new_hour(5)
        ph, p = num(), pin()
        await signup(ph, p)
        codes = [(await login(ph, p)).status_code for _ in range(25)]
        assert codes == [200] * 25
        assert await count(hour_key('+91' + ph, BASE_HOUR[0])) == 0
    run(go())


# ---- concurrency at remaining capacity 1 admits <=1 verification; no negative counter ----
@pytest.mark.parametrize('mix_correct', [False, True])
def test_concurrent_remaining_capacity_one(mix_correct):
    async def go():
        new_hour(5)
        ph, p = num(), pin()
        e = '+91' + ph
        await signup(ph, p)
        hk = hour_key(e, BASE_HOUR[0])
        await TDB.tejas_phone_limits.update_one({'_id': hk}, {'$set': {'count': 19}}, upsert=True)
        v0 = VERIFY_CALLS[0]
        pins = [p if (mix_correct and i == 0) else wrong(p) for i in range(5)]  # 5 = max reaching hour check (short guard 5)
        rs = await asyncio.gather(*[login(ph, x, peer=('10.9.0.%d' % (i + 1), 1)) for i, x in enumerate(pins)])
        codes = [r.status_code for r in rs]
        admitted = [c for c in codes if c in (200, 401)]
        print('concurrent codes', codes, 'verify', VERIFY_CALLS[0] - v0, [r.text[:200] for r in rs if r.status_code >= 500])
        assert len(admitted) <= 1 and VERIFY_CALLS[0] - v0 <= 1, codes
        busy = [r for r in rs if r.status_code == 503]
        assert all('capacity_busy' in r.text for r in busy)  # existing per-process auth admission lane
        assert codes.count(429) + len(busy) >= 4 and set(codes) <= {200, 401, 429, 503}
        c = await count(hk)
        assert 0 <= c <= 20, c
        assert c == (19 if 200 in codes else 20), (codes, c)
    run(go())


# ---- same with auth admission lane raised so all 5 reach the handler; repeated rounds ----
def test_concurrent_capacity_one_lane_raised_repeated():
    async def go():
        lanes = H.app.state.admission.lanes['auth']
        old = lanes['limit']
        lanes['limit'] = 64
        try:
            for rnd in range(6):
                new_hour(5)
                ph, p = num(), pin()
                await signup(ph, p)
                hk = hour_key('+91' + ph, BASE_HOUR[0])
                await TDB.tejas_phone_limits.update_one({'_id': hk}, {'$set': {'count': 19}}, upsert=True)
                v0 = VERIFY_CALLS[0]
                pins = [p if rnd % 2 and i == rnd % 5 else wrong(p) for i in range(5)]
                rs = await asyncio.gather(*[login(ph, x) for x in pins])
                codes = [r.status_code for r in rs]
                print('lane-raised round', rnd, codes)
                assert 503 not in codes and codes.count(429) == 4 and VERIFY_CALLS[0] - v0 == 1, codes
                assert await count(hk) == (19 if 200 in codes else 20)
        finally:
            lanes['limit'] = old
    run(go())


def test_counter_never_negative_on_rollback():
    async def go():
        new_hour(5)
        ph, p = num(), pin()
        await signup(ph, p)
        hk = hour_key('+91' + ph, BASE_HOUR[0])
        r = await login(ph, p)
        assert r.status_code == 200
        assert await count(hk) == 0
        d = await TDB.tejas_phone_limits.find_one({'_id': hk})
        assert d is None or d['count'] >= 0
    run(go())


# ---- unknown profile uses guard; 15-min windows across one clock hour; Retry-After to hour end ----
def test_unknown_profile_hour_budget_across_15min_windows():
    async def go():
        h = new_hour(1)
        ph = num()  # never signed up
        e = '+91' + ph
        seq = []
        for q in range(4):
            set_clock(h * 3600 + q * 900 + 2)
            for _ in range(5):
                seq.append((await login(ph, '1234')).status_code)
            r6 = await login(ph, '1234')
            seq.append(r6.status_code)
            if q < 3:
                ra = int(r6.headers['retry-after'])
                assert abs(ra - (900 - 2)) <= 3, ra  # short-window Retry-After preserved
        assert seq == ([401] * 5 + [429]) * 4, seq
        assert await count(hour_key(e, h)) == 20
        set_clock(h * 3600 + 3 * 900 + 899)
        set_clock((h * 3600) + 3600 - 600)  # :50 still same hour, short window #4 already full
        r = await login(ph, '1234')
        assert r.status_code == 429
        # boundary: hour h ends -> new window, new budget
        set_clock((h + 1) * 3600 + 1)
        BASE_HOUR[0] = h + 1
        assert (await login(ph, '1234')).status_code == 401
        assert await count(hour_key(e, h + 1)) == 1
    run(go())


def test_unknown_profile_hourly_429_retry_after_hour_end_with_success_resets_impossible():
    """Use 4 windows of 5 failures, then 1st request of a NEW short window in same hour -> hourly 429."""
    async def go():
        h = new_hour(1)
        ph = num()
        for q in range(4):
            set_clock(h * 3600 + q * 900 + 1)
            for _ in range(5):
                assert (await login(ph, '4321')).status_code == 401
        # all 4 short windows consumed: budget at 20; craft a fresh short window by clearing ONLY short key in last window
        await TDB.tejas_phone_limits.delete_one({'_id': short_key('+91' + ph, H.fake_now())})
        r = await login(ph, '4321')
        assert r.status_code == 429 and 'incorrect PIN' in r.text, r.text
        ra = int(r.headers['retry-after'])
        assert abs(ra - ((h + 1) * 3600 - H.fake_now())) <= 3
    run(go())


# ---- separate phones not globally blocked; normalized duplicates share bucket ----
def test_normalized_forms_share_bucket_and_other_phone_unaffected():
    async def go():
        h = new_hour(5)
        ph, p = num(), pin()
        await signup(ph, p)
        forms = [ph, '+91' + ph, '0' + ph, '+91 ' + ph[:5] + ' ' + ph[5:], '91' + ph]
        seq = []
        for cycle in range(5):
            for i in range(4):
                seq.append((await login(forms[(cycle + i) % len(forms)], wrong(p))).status_code)
            seq.append((await login(forms[cycle], p)).status_code)
        assert seq == ([401] * 4 + [200]) * 4 + [401] * 4 + [429], seq  # 20 failures retained; the 21st check (even correct) waits
        assert await count(hour_key('+91' + ph, h)) == 20
        for f in forms:
            assert (await login(f, p)).status_code == 429, f
        other, op = num(), pin()
        await signup(other, op)
        assert (await login(other, wrong(op))).status_code == 401
        assert (await login(other, op)).status_code == 200
    run(go())


# ---- IP limit BEFORE account: IP-rejected requests do not burn victim short/hour budget ----
def test_ip_limit_before_account_does_not_burn_victim():
    async def go():
        h = new_hour(5)
        victim, vp = num(), pin()
        await signup(victim, vp)
        e = '+91' + victim
        peer = ('8.8.8.8', 999)
        codes = [(await login(num(), '0000', peer)).status_code for _ in range(60)]
        assert codes == [401] * 60
        spoof = {'X-Forwarded-For': '1.2.3.4', 'CF-Connecting-IP': '9.9.9.9', 'X-Real-IP': '5.5.5.5', 'Forwarded': 'for=7.7.7.7'}
        for _ in range(10):
            r = await login(victim, '0000', peer, headers=spoof)
            assert r.status_code == 429 and int(r.headers['retry-after']) > 0
        assert await count(short_key(e, H.fake_now())) == 0
        assert await count(hour_key(e, h)) == 0
        assert (await login(victim, vp, ('1.1.1.1', 1))).status_code == 200
        # private ingress: no global 60 block
        pcodes = [(await login(num(), '0000', ('10.81.4.%d' % (200 + i % 2), 1))).status_code for i in range(70)]
        assert set(pcodes) == {401}
    run(go())


# ---- fail closed when limiter DB fails ----
@pytest.mark.parametrize('mode', ['none', 'connfail', 'opfail'])
def test_fail_closed_on_increment_failure(mode):
    orig = AsyncIOMotorCollection.find_one_and_update

    async def broken(self, *a, **k):
        if self.name == 'tejas_phone_limits':
            if mode == 'none':
                return None
            raise (ConnectionFailure if mode == 'connfail' else OperationFailure)('TEST injected limiter failure')
        return await orig(self, *a, **k)

    async def go():
        new_hour(5)
        ph, p = num(), pin()
        await signup(ph, p)
        v0 = VERIFY_CALLS[0]
        AsyncIOMotorCollection.find_one_and_update = broken
        try:
            r = await login(ph, p)
        finally:
            AsyncIOMotorCollection.find_one_and_update = orig
        print(mode, '->', r.status_code, r.headers.get('retry-after'))
        assert r.status_code == 503 and r.headers.get('retry-after') == '3'
        assert 'access_token' not in r.cookies and 'set-cookie' not in r.headers
        assert VERIFY_CALLS[0] == v0
    run(go())


# ---- narrow dependent regressions: anonymous / other student denied; owner directory only; student forced ----
def test_pin_change_denials_and_directory_scope():
    async def go():
        new_hour(5)
        a, ap = num(), pin()
        b, bp = num(), pin()
        await signup(a, ap)
        await signup(b, bp)
        async with client() as anon:
            r = await anon.post('/api/auth/pin', json={'phone': a, 'new_pin': '1111', 'confirm_pin': '1111'})
            assert r.status_code == 401
            assert (await anon.get('/api/admin/students')).status_code == 401
        async with client() as c:
            r = await c.post('/api/auth/phone', json={'phone': a, 'pin': ap})
            assert r.status_code == 200 and J(r)['role'] == 'student'
            r = await c.post('/api/auth/pin', json={'phone': b, 'new_pin': '1111', 'confirm_pin': '1111'})
            assert r.status_code == 403
            assert (await c.get('/api/admin/students')).status_code == 403
        assert (await login(b, bp)).status_code == 200
        async with client() as o:
            assert (await o.post('/api/auth/login', json={'email': OWNER['email'], 'password': OWNER_PW})).status_code == 200
            d = J(await o.get('/api/admin/students'))
            assert d['items'] and all(set(x) <= {'id', 'phone', 'pin_version'} for x in d['items']), d['items'][:2]
            assert '$2b$' not in str(d)
    run(go())


def test_zz_no_real_handles_no_puts():
    assert not H.leftover_real_handles() and not H.PUTS
