"""TEST-ONLY iteration 184: Forgot PIN (POST /api/auth/pin/reset), signed-in Change PIN, PIN bcrypt cost 12 -> 8 rehash,
staff login unchanged, and Master type Uploads showing a PDF restored from the Library.
Isolated disposable DB (book_publishing_iso170 harness). Run: cd /app/backend && python tests/forgot_pin_iso184.py
"""
import asyncio, sys, time, uuid, secrets
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import book_publishing_iso170 as T  # noqa: E402,F401
from book_publishing_iso170 import H, mkstaff, client, check, RESULTS  # noqa: E402
from structure_iso173 import mkset  # noqa: E402
from tejas import structure, auth  # noqa: E402
import bcrypt  # noqa: E402

DB = H.TDB
RESET = '/api/auth/pin/reset'


def num():
    return '95' + f'{secrets.randbelow(10 ** 8):08d}'


def env(r):
    try: return r.json()
    except Exception: return {}


def body(ph, p, c=None, **x):
    return {'phone': ph, 'new_pin': p, 'confirm_pin': c if c is not None else p, **x}


async def signup(ph, p='8261'):
    c = client(); r = await c.post('/api/auth/phone/signup', json={'phone': ph, 'pin': p, 'confirm_pin': p})
    assert r.status_code == 200, r.text
    return c, env(r)


async def login(ph, p):
    c = client(); r = await c.post('/api/auth/phone', json={'phone': ph, 'pin': p})
    return c, r


async def pin_tests():
    # --- reset happy path
    ph = num()
    old, me0 = await signup(ph, '1111')
    sid = me0['id']
    await DB.tejas_attempts.insert_one({'id': 'TEST_att184_' + uuid.uuid4().hex[:6], 'user_id': sid, 'set_id': 'x', 'status': 'submitted', 'created_at': time.time()})
    other, r = await login(ph, '1111'); check('second session signed in before reset', r.status_code == 200, r.text[:200])
    anon = client()
    r = await anon.post(RESET, json=body(ph, '2222'))
    d = env(r)
    check('reset 200 with user body', r.status_code == 200 and d.get('id') == sid and d.get('role') == 'student' and d.get('access_type') == 'unverified_phone'
          and d.get('pin_configured') is True and d.get('phone'), r.text[:300])
    sc = r.headers.get_list('set-cookie') if hasattr(r.headers, 'get_list') else [r.headers.get('set-cookie', '')]
    check('reset sets access + refresh cookies', any('access_token=' in x for x in sc) and any('refresh_token=' in x for x in sc) and all('httponly' in x.lower() for x in sc if 'token=' in x), sc)
    check('reset body has no hash', 'pin_hash' not in r.text and '$2b$' not in r.text)
    r = await anon.get('/api/auth/me'); check('/me works with reset cookies', r.status_code == 200 and env(r).get('id') == sid, r.text[:200])
    r = await old.get('/api/auth/me'); check('signup session revoked after reset', r.status_code == 401, r.status_code)
    r = await other.get('/api/auth/me'); check('other login session revoked after reset', r.status_code == 401, r.status_code)
    _, r = await login(ph, '1111'); check('old PIN fails 401 with Forgot PIN text', r.status_code == 401 and 'Forgot PIN' in r.text, r.text[:200])
    nc, r = await login(ph, '2222'); check('new PIN signs in, same id', r.status_code == 200 and env(r).get('id') == sid, r.text[:200])
    r = await nc.get('/api/attempts'); check('earlier attempt row kept', await DB.tejas_attempts.count_documents({'user_id': sid}) == 1 and r.status_code == 200, r.text[:200])
    p = await DB.tejas_phone_profiles.find_one({'id': sid})
    check('profile marked reset via forgot_pin, version 1, cost 8', p.get('pin_reset_via') == 'forgot_pin' and p.get('pin_version') == (me0.get('pin_version') or 1) + 1 and p['pin_hash'].startswith('$2b$08$'), {k: p.get(k) for k in ('pin_version', 'pin_reset_via')})
    check('only one profile for the number', await DB.tejas_phone_profiles.count_documents({'phone': p['phone']}) == 1)

    # --- validation
    n0 = await DB.tejas_phone_profiles.count_documents({})
    unk = num(); r = await anon.post(RESET, json=body(unk, '3333'))
    check('unknown number 404 message', r.status_code == 404 and 'No account with this number. Create one instead.' in r.text, r.text[:200])
    check('no profile created for unknown', await DB.tejas_phone_profiles.count_documents({}) == n0)
    for name, b in (('mismatch', body(ph, '3333', '4444')), ('3-digit', body(ph, '333')), ('letters', body(ph, 'abcd')), ('5-digit', body(ph, '33333')),
                    ('extra field', body(ph, '3333', role='owner')), ('missing confirm', {'phone': ph, 'new_pin': '3333'}), ('invalid phone', body('12345', '3333')),
                    ('unicode digits', body(ph, '\u0663\u0663\u0663\u0663')), ('int pin', {'phone': ph, 'new_pin': 3333, 'confirm_pin': 3333})):
        r = await anon.post(RESET, json=b); check(f'reset {name} -> 422', r.status_code == 422, (r.status_code, r.text[:160]))
    _, r = await login(ph, '2222'); check('PIN unchanged after rejected resets', r.status_code == 200)

    # --- rate limit 5 per number per 15 min
    ph2 = num(); await signup(ph2, '5555')
    codes = []
    for i in range(6):
        r = await client().post(RESET, json=body(ph2, f'{6000 + i}'))
        codes.append(r.status_code)
    check('6th reset 429 with Retry-After', codes[:5] == [200] * 5 and codes[5] == 429 and r.headers.get('retry-after', '').isdigit(), (codes, dict(r.headers)))
    r2 = await client().post(RESET, json=body(ph, '2223')); check('limit is per number (other number fine)', r2.status_code == 200, r2.text[:120])
    _, r = await login(ph, '2223'); check('second reset new PIN works', r.status_code == 200)

    # --- legacy profile with no pin_hash
    ph3 = num(); e164 = '+91' + ph3; lid = str(uuid.uuid4())
    await DB.tejas_phone_profiles.insert_one({'_id': lid, 'id': lid, 'phone': e164, 'created_at': time.time(), 'consent_at': time.time(), 'last_seen_at': time.time()})
    _, r = await login(ph3, '7777'); check('legacy no-PIN profile cannot sign in', r.status_code == 401)
    r = await client().post(RESET, json=body(ph3, '7777')); check('legacy reset sets first PIN', r.status_code == 200 and env(r).get('id') == lid, r.text[:200])
    _, r = await login(ph3, '7777'); check('legacy signs in with new PIN', r.status_code == 200 and env(r).get('id') == lid, r.text[:200])

    # --- signed-in change PIN
    ph4 = num(); c4, me4 = await signup(ph4, '1234'); o4, _ = await login(ph4, '1234')
    r = await c4.post('/api/auth/pin', json=body(ph4, '4321'))
    sc = r.headers.get_list('set-cookie') if hasattr(r.headers, 'get_list') else []
    check('change PIN 200 + new cookies', r.status_code == 200 and any('access_token=' in x for x in sc), r.text[:200])
    r = await c4.get('/api/auth/me'); check('changer still signed in', r.status_code == 200)
    r = await o4.get('/api/auth/me'); check('change PIN revokes other session', r.status_code == 401, r.status_code)
    _, r = await login(ph4, '4321'); check('changed PIN works', r.status_code == 200)
    r = await c4.post('/api/auth/pin', json=body(ph, '9999')); check("changing another number's PIN 403", r.status_code == 403, r.text[:160])
    r = await client().post('/api/auth/pin', json=body(ph4, '9999')); check('change PIN unauthenticated 401', r.status_code == 401, r.status_code)

    # --- cost 12 -> 8 rehash
    check('new signup stores $2b$08$', (await DB.tejas_phone_profiles.find_one({'id': me4['id']}))['pin_hash'].startswith('$2b$08$'))
    ph5 = num(); hid = str(uuid.uuid4())
    await DB.tejas_phone_profiles.insert_one({'_id': hid, 'id': hid, 'phone': '+91' + ph5, 'pin_hash': bcrypt.hashpw(b'4826', bcrypt.gensalt(12)).decode(),
                                              'created_at': time.time(), 'consent_at': time.time(), 'last_seen_at': time.time()})
    _, r = await login(ph5, '0000'); h = (await DB.tejas_phone_profiles.find_one({'id': hid}))['pin_hash']
    check('wrong PIN on cost-12 profile 401, hash untouched', r.status_code == 401 and h.startswith('$2b$12$'))
    _, r = await login(ph5, '4826'); h = (await DB.tejas_phone_profiles.find_one({'id': hid}))['pin_hash']
    check('cost-12 PIN signs in and is rehashed to $2b$08$', r.status_code == 200 and h.startswith('$2b$08$'), h[:7])
    _, r = await login(ph5, '4826'); check('rehashed PIN still signs in', r.status_code == 200)

    # --- staff unchanged / owner email can't be reset
    check('staff hashpw still cost 12', auth.hashpw('x-Qa184-pw').startswith('$2b$12$'))
    em = f'qa184-own-{uuid.uuid4().hex[:6]}@example.com'; pw = 'Qa184!' + uuid.uuid4().hex[:10]
    await DB.tejas_users.insert_one({'id': str(uuid.uuid4()), 'name': 'QA184', 'email': em, 'role': 'owner', 'credential_generation': 0, 'password_hash': auth.hashpw(pw), 'created_at': time.time()})
    c = client(); r = await c.post('/api/auth/login', json={'email': em, 'password': pw}); check('owner cost-12 login works', r.status_code == 200, r.text[:200])
    r = await client().post(RESET, json={'phone': em, 'new_pin': '1212', 'confirm_pin': '1212'}); check('owner email cannot use reset (422)', r.status_code == 422, r.status_code)
    r = await c.post('/api/auth/pin', json=body(ph, '1212')); check('owner session cannot change student PIN (403)', r.status_code == 403, r.status_code)


async def uploads_tests():
    own, _ = await mkstaff('owner', 'up184')
    sid = 'bitsat:mocks'
    t = time.time()
    for bid in ('bk184-arch', 'bk184-viaset'):
        await DB.tejas_books.insert_one({'_id': bid, 'removed': False, 'paused': False, 'state': 'ready', 'created_at': t,
                                         'payload': {'title': 'TEST_' + bid, 'chapters': False, 'destination': {'section_id': sid}}})
    s1 = await mkset('UPA', exam='BITSAT', catalog_section_id=sid, test_kind='mock', book_import_id='bk184-arch')
    s2 = await mkset('UPB', exam='BITSAT', catalog_section_id=sid, test_kind='mock', book_import_id='bk184-viaset')
    await DB.tejas_book_mocks.insert_many([{'_id': 'bm184-1', 'book_id': 'bk184-arch', 'set_id': s1, 'label': 'Mock 1'},
                                           {'_id': 'bm184-2', 'book_id': 'bk184-viaset', 'set_id': s2, 'label': 'Mock 1'}])
    up = lambda: own.get(f'/api/admin/master/types/{sid}/mocks')
    r = await up(); ids = [u['id'] for u in env(r).get('uploads', [])]
    check('ready non-chapter PDFs hidden before archive', r.status_code == 200 and not {'bk184-arch', 'bk184-never', 'bk184-viaset'} & set(ids), (r.status_code, ids))
    r = await own.post('/api/admin/library/archive', json={'ids': [s1, s2]})
    a = await DB.tejas_books.find_one({'_id': 'bk184-arch'})
    print('INFO archive by ids -> book archived?', a.get('archived'), r.text[:120])
    r = await own.post('/api/admin/library/archive', json={'section_id': sid})
    a = await DB.tejas_books.find_one({'_id': 'bk184-arch'})
    check('archive whole section moves its PDFs to the Library', r.status_code == 200 and a.get('archived'), (r.text[:200], a.get('archived')))
    await DB.tejas_books.insert_one({'_id': 'bk184-never', 'removed': False, 'paused': False, 'state': 'ready', 'created_at': t,
                                     'payload': {'title': 'TEST_bk184-never', 'chapters': False, 'destination': {'section_id': sid}}})
    r = await own.post('/api/admin/library/restore', json={'uploads': [{'kind': 'book', 'id': 'bk184-arch'}]})
    check('restore upload 200', r.status_code == 200 and env(r).get('uploads') == 1, r.text[:200])
    r = await own.post('/api/admin/library/restore', json={'ids': [s2]})
    check('restore test 200 (brings its PDF back)', r.status_code == 200 and env(r).get('restored') == 1, r.text[:200])
    r = await up(); ups = {u['id']: u for u in env(r).get('uploads', [])}
    for bid in ('bk184-arch', 'bk184-viaset'):
        u = ups.get(bid, {})
        check(f'{bid} listed as done with Library message', u.get('state') == 'done' and u.get('message', '').startswith('Back from the Library.') and 'listed in this type' in u.get('message', ''), u or list(ups))
    check('bk184-arch message counts 1 mock (singular)', ups.get('bk184-arch', {}).get('message') == 'Back from the Library. 1 mock read from it, listed in this type.', ups.get('bk184-arch', {}).get('message'))
    check('never-archived ready PDF still hidden', 'bk184-never' not in ups, list(ups))


async def main():
    check('no customer DB handles', not H.leftover_real_handles(), H.leftover_real_handles())
    await H.tdbmod.indexes(); await structure.seed()
    try:
        await pin_tests()
        await uploads_tests()
    except Exception as e:
        import traceback; traceback.print_exc(); check('no crash', False, repr(e))
    finally:
        await H.tdbmod.client.drop_database(H.TEST_DB)
        print('dropped', H.TEST_DB)
    f = [r for r in RESULTS if not r[1]]
    print(f'TOTAL {len(RESULTS)} PASS {len(RESULTS) - len(f)} FAIL {len(f)}')


if __name__ == '__main__':
    asyncio.run(main())
