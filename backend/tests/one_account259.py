"""TEST-ONLY iteration 259 (the owner's question, 27 Nov: "is your login and the app's login the same?").
The real website server in a disposable DB (storage mocked, no AI, no network). Two kinds of caller, as on live:
  web = a browser on the website: sends Origin and Sec-Fetch, keeps its own cookies;
  app = the app's server (the app has no accounts of its own; it passes every request to these same doors): no Origin, no Sec-Fetch,
        its library's user agent, its own cookie jar for each phone.
A  an account made in the app signs in on the website: the same id.   B  the other way round.
C  one number = one account, however the number is typed and from whichever side.
D  the name: set on one side, read on the other.
E  one paper across both: started on the website, answered and submitted in the app; result, My Tests and Misfire are the same on both.
F  PIN changed in the app.   G  Forgot PIN on the website.   H  refresh; sign-out ends that device only.
I  a write from a foreign website is refused; the app's server (no Origin) is let in.   J  wrong PINs are counted together.
K  AS BUILT TODAY: the website limits sign-ups and wrong PINs per address, and every app student reaches it from the app server's address.
Run: cd /app/backend && bash /root/p2/solo.sh python -u tests/one_account259.py   (drops only its own disposable database)
"""
import asyncio, secrets, sys, time, uuid
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import httpx  # noqa: E402
import book_publishing_iso170 as T  # noqa: E402,F401
from book_publishing_iso170 import H, client, check, RESULTS  # noqa: E402
from structure_iso173 import mkset, start  # noqa: E402
from tejas import structure, jobs as JOBS  # noqa: E402

DB = H.TDB
BASE, ORIGIN = str(client().base_url), client().headers['origin']
EDGE, LB = '172.70.100.107', '136.110.214.0'   # a Cloudflare hop and the load balancer, as the live edge writes them
APP_ADDRESS, HOME_ADDRESS, PHONE_ADDRESS = '34.170.12.145', '49.36.30.4', '49.36.30.9'
PHONE = '/api/auth/phone'


def web():
    return httpx.AsyncClient(transport=httpx.ASGITransport(app=H.app), base_url=BASE, timeout=120,
                             headers={'Origin': ORIGIN, 'Sec-Fetch-Site': 'same-origin', 'User-Agent': 'Mozilla/5.0 (Linux; Android 14) Chrome/130 Mobile'})


def app():
    return httpx.AsyncClient(transport=httpx.ASGITransport(app=H.app), base_url=BASE, timeout=120)


def J(r):
    try: d = r.json()
    except Exception: return {}
    return d if d is not None else {}


def num():
    return '96' + f'{secrets.randbelow(10 ** 8):08d}'


def via(address, typed=None):
    return {'X-Forwarded-For': ','.join(([typed] if typed else []) + [address, EDGE, LB])}


async def signup(c, phone, pin, **kw):
    return await c.post(PHONE + '/signup', json={'phone': phone, 'pin': pin, 'confirm_pin': pin}, **kw)


async def login(c, phone, pin, **kw):
    return await c.post(PHONE, json={'phone': phone, 'pin': pin}, **kw)


async def me(c):
    r = await c.get('/api/auth/me')
    return r.status_code, J(r).get('id')


async def graded(c, aid):
    d = {}
    for _ in range(40):
        r = await c.get(f'/api/attempts/{aid}/results'); d = J(r)
        if r.status_code == 200 and d.get('status') != 'grading' and d.get('summary'):
            return d
        for j in await DB.tejas_jobs.find({'status': 'queued'}).to_list(50):
            try: await JOBS.run_job(j['id'])
            except Exception: pass
        await asyncio.sleep(.3)
    return d


async def both_ways():
    pa, pb = num(), num()
    a_app = app(); r = await signup(a_app, pa, '4826'); a = J(r); aid = a.get('id')
    sc = r.headers.get_list('set-cookie')
    check('A the app signs a student up through the website door: 200, a student with an id, no PIN or hash in the answer, in the website envelope (data / error / meta.api_version)',
          r.status_code == 200 and bool(aid) and a.get('role') == 'student' and a.get('access_type') == 'unverified_phone' and a.get('pin_configured') is True
          and '4826' not in r.text and 'pin_hash' not in r.text and '"api_version"' in r.text and '"data"' in r.text, (r.status_code, r.text[:300]))
    check('A the session comes as two cookies (access, refresh), HttpOnly and Secure; there is no bearer token in the body',
          any(x.startswith('access_token=') for x in sc) and any(x.startswith('refresh_token=') for x in sc) and all('httponly' in x.lower() and 'secure' in x.lower() for x in sc) and 'token' not in a, sc)
    a_web = web(); r = await login(a_web, pa, '4826')
    check('A the same number and PIN sign in on the website: the very same id; "who am I" says that id on both sides',
          r.status_code == 200 and J(r).get('id') == aid and await me(a_app) == (200, aid) and await me(a_web) == (200, aid), (r.status_code, J(r).get('id'), aid))
    s1, s2 = J(await a_app.get('/api/auth/session')), J(await a_web.get('/api/auth/session'))
    check('A auth/session gives the same student on both sides', (s1.get('user') or {}).get('id') == aid == (s2.get('user') or {}).get('id'), (s1, s2))
    seen = [a, J(r), J(await a_app.get('/api/auth/me')), s1.get('user') or {}, s2.get('user') or {}, J(await a_app.post('/api/auth/refresh'))]
    check('A no name chosen yet: "display_name" is in every answer that carries the student (sign-up, sign-in, auth/me, auth/session twice, auth/refresh) and is null, never left out',
          all('display_name' in x and x['display_name'] is None for x in seen), [x.get('display_name', 'LEFT OUT') for x in seen])
    anon = app(); r = await anon.get('/api/auth/session')
    check('A signed out: auth/session answers 200 with user null; auth/me answers 401', r.status_code == 200 and J(r) == {'user': None} and (await me(anon))[0] == 401, (r.status_code, r.text[:200]))
    b_web = web(); r = await signup(b_web, pb, '7391'); bid = J(r).get('id')
    b_app = app(); r2 = await login(b_app, pb, '7391')
    check('B an account made on the website signs in to the app: the very same id', r.status_code == 200 and bool(bid) and bid != aid and r2.status_code == 200 and J(r2).get('id') == bid, (r.status_code, r2.status_code, bid, J(r2).get('id')))
    rows = {p['id']: p async for p in DB.tejas_phone_profiles.find({'id': {'$in': [aid, bid]}})}
    check('B the list remembers where each was made (app / web); both are in the ONE student list', len(rows) == 2 and rows[aid].get('signup_channel') == 'app' and rows[bid].get('signup_channel') == 'web'
          and await DB.tejas_phone_profiles.count_documents({}) == 2, {k: v.get('signup_channel') for k, v in rows.items()})
    return pa, pb, aid, bid, a_app, a_web, b_app, b_web


async def one_number(pa, pb, aid, bid):
    r1 = await signup(app(), pb, '0000'); r2 = await signup(web(), '+91 ' + pa[:5] + ' ' + pa[5:], '0000')
    check('C a second sign-up with a number that has an account is refused from either side (409, a plain sentence); still two accounts',
          r1.status_code == 409 and r2.status_code == 409 and 'already has' in r1.text and await DB.tejas_phone_profiles.count_documents({}) == 2, (r1.status_code, r2.status_code, r1.text[:160]))
    got = [(r.status_code, J(r).get('id')) for r in [await login(app(), t, '4826') for t in (pa, '+91' + pa, pa[:5] + ' ' + pa[5:], '0' + pa)]]
    check('C the number typed four ways (10 digits, +91, with a space, with a leading 0) is the same account', got == [(200, aid)] * 4, got)
    r = await login(web(), pa, '7391')
    check("C another student's PIN does not open it (401)", r.status_code == 401, r.status_code)


async def name(aid, a_app, a_web):
    put = lambda c, n: c.put('/api/profile/display-name', json={'name': n})  # noqa: E731
    r = await put(a_web, '  Arjun   Sharma ')
    seen = J(await a_app.get('/api/auth/me')).get('display_name')
    check('D the name saved on the website (its spaces tidied) is the answer of the PUT and the name the app reads', r.status_code == 200 and J(r).get('display_name') == 'Arjun Sharma' and seen == 'Arjun Sharma', (r.status_code, r.text[:160], seen))
    bad = [await put(a_app, n) for n in ('A', 'Arjun@Sharma', 'Arjun 9876543210', 'JEELIVE Admin', 'A' * 21)]
    seen = J(await a_app.get('/api/auth/me')).get('display_name')
    check('D a name that breaks a rule (too short, a sign, a phone number, an official word, too long) is refused: 422 with one plain sentence in error.message; the name stays',
          [b.status_code for b in bad] == [422] * 5 and all('"message"' in b.text and 'naam' in b.text.lower() for b in bad) and seen == 'Arjun Sharma', [(b.status_code, b.text[:120]) for b in bad])
    r = await put(a_app, 'Arjun S')
    seen = (J(await a_web.get('/api/auth/session')).get('user') or {}).get('display_name')
    check('D the name saved from the app is the name the website shows; the id is the same (the five refused tries were not counted)', r.status_code == 200 and seen == 'Arjun S' and await me(a_web) == (200, aid), (r.status_code, r.text[:160], seen))
    r = await put(a_web, '')
    m1, m2 = J(await a_app.get('/api/auth/me')), J(await a_web.get('/api/auth/session')).get('user') or {}
    check('D the name taken away on the website: the PUT answers display_name ""; the app and the website then read display_name null (the key stays in the answer)',
          r.status_code == 200 and J(r).get('display_name') == '' and all('display_name' in m and m['display_name'] is None for m in (m1, m2)), (r.status_code, r.text[:160], m1, m2))
    r = await put(a_app, 'Arjun S')
    check('D the fourth change of a day is refused: 429 "Naam din mein 3 baar hi badal sakta hai. Kal dobara try karo."; the name stays away',
          r.status_code == 429 and 'Naam din mein 3 baar hi badal sakta hai. Kal dobara try karo.' in r.text and J(await a_web.get('/api/auth/me')).get('display_name') is None, (r.status_code, r.text[:200]))


async def paper(aid, a_app, a_web, b_app):
    sid = await mkset('ONE259', exam='JEE Main')
    r = await start(a_web, sid); att = J(r); at = att.get('id'); qs = [q['id'] for q in att.get('questions', [])]
    check('E the student starts a paper on the website', r.status_code == 200 and bool(at) and len(qs) == 3, (r.status_code, r.text[:300]))
    if not at:
        return
    r = await a_app.get(f'/api/attempts/{at}'); seen = J(r)
    check('E the app opens the very same attempt: same id, same questions, same deadline', r.status_code == 200 and seen.get('id') == at and [q['id'] for q in seen.get('questions', [])] == qs
          and seen.get('deadline') == att.get('deadline'), (r.status_code, r.text[:200]))
    r = await start(a_app, sid)
    check('E "Start" pressed again in the app while it runs (no Origin, as the app server sends it): the same attempt, never a second one',
          r.status_code == 200 and J(r).get('id') == at and await DB.tejas_attempts.count_documents({'user_id': aid}) == 1, (r.status_code, r.text[:200]))
    r = await b_app.get(f'/api/attempts/{at}')
    check("E another student cannot open it (404)", r.status_code == 404, r.status_code)
    await a_web.post(f'/api/attempts/{at}/begin'); await asyncio.sleep(.2)
    save = lambda c, q, v: c.put(f'/api/attempts/{at}/answers/{q}', json={'value': v, 'marked': False, 'revision': 1, 'request_id': str(uuid.uuid4())})  # noqa: E731
    r1 = await save(a_app, qs[0], 'B'); r2 = await save(a_web, qs[1], 'A')
    left, right = J(await a_web.get(f'/api/attempts/{at}')).get('answers') or {}, J(await a_app.get(f'/api/attempts/{at}')).get('answers') or {}
    check('E an answer saved in the app shows on the website and one saved on the website shows in the app', r1.status_code == 200 and r2.status_code == 200
          and (left.get(qs[0]) or {}).get('value') == 'B' and (right.get(qs[1]) or {}).get('value') == 'A' and left == right, (r1.status_code, r2.status_code, left, right))
    r = await a_app.post(f'/api/attempts/{at}/submit')
    one, two = await graded(a_app, at), await graded(a_web, at)
    out = {q['id']: q.get('outcome') for q in one.get('questions', [])}
    check('E submitted in the app: one result, the same on both sides (wrong -1, right +4, left 0 = 3 of 12)', r.status_code in (200, 202) and (one.get('summary') or {}).get('score') == 3
          and one.get('summary') == two.get('summary') and out == {qs[0]: 'incorrect', qs[1]: 'correct', qs[2]: 'skipped'}, (r.status_code, one.get('summary'), out))
    lists = [[i['id'] for i in J(await c.get('/api/my/tests', params={'tab': 'completed'})).get('items', [])] for c in (a_app, a_web)]
    check('E My Tests lists that one attempt on both sides', lists == [[at], [at]], lists)
    items = [sorted(i['id'] for i in J(await c.get('/api/my/misfire')).get('items', [])) for c in (a_app, a_web)]
    want = sorted([f'{at}:{qs[0]}', f'{at}:{qs[2]}'])
    check('E Misfire: the wrong and the left question, under the id <attempt id>:<question id>, the same on both sides', items == [want, want], items)
    r = await a_app.post(f'/api/my/misfire/{at}:{qs[0]}/try', json={'value': 'A'})
    seen = next((i for i in J(await a_web.get('/api/my/misfire')).get('items', []) if i['id'] == f'{at}:{qs[0]}'), {})
    r2 = await a_web.post(f'/api/my/misfire/{at}:{qs[0]}/done')
    fixed = [i['id'] for i in J(await a_app.get('/api/my/misfire', params={'status': 'fixed'})).get('items', [])]
    check('E a right try in the app is seen on the website; "Samajh gaya" on the website moves it for the app too', r.status_code == 200 and J(r).get('correct') is True
          and seen.get('tries') == 1 and seen.get('last_correct') is True and r2.status_code == 200 and fixed == [f'{at}:{qs[0]}'], (r.status_code, seen.get('tries'), r2.status_code, fixed))
    return at


async def pins(pa, aid, at, a_app, a_web):
    r = await a_app.post('/api/auth/pin', json={'phone': pa, 'new_pin': '5150', 'confirm_pin': '5150'})
    check('F PIN changed in the app: 200, the same id, the app stays signed in', r.status_code == 200 and J(r).get('id') == aid and J(r).get('display_name', 'LEFT OUT') is None and await me(a_app) == (200, aid), (r.status_code, r.text[:200]))
    old, new = await login(web(), pa, '4826'), web(); r = await login(new, pa, '5150')
    check('F the website session of before is ended (401); the old PIN is refused; the new PIN signs in on the website with the same id',
          (await me(a_web))[0] == 401 and old.status_code == 401 and r.status_code == 200 and J(r).get('id') == aid, ((await me(a_web))[0], old.status_code, r.status_code))
    r = await web().post('/api/auth/pin/reset', json={'phone': pa, 'new_pin': '6274', 'confirm_pin': '6274'})
    back = app(); r2 = await login(back, pa, '6274')
    check('G Forgot PIN on the website: the same id; the app session of before is ended; the app signs in with the new PIN, the same id',
          r.status_code == 200 and J(r).get('id') == aid and J(r).get('display_name', 'LEFT OUT') is None and (await me(a_app))[0] == 401 and r2.status_code == 200 and J(r2).get('id') == aid, (r.status_code, (await me(a_app))[0], r2.status_code))
    lists = [i['id'] for i in J(await back.get('/api/my/tests', params={'tab': 'completed'})).get('items', [])]
    row = await DB.tejas_phone_profiles.find_one({'phone': '+91' + pa})
    check('G after two PIN changes: the same one account, the same id, its paper still in My Tests', row['id'] == aid and lists == [at]
          and await DB.tejas_phone_profiles.count_documents({'phone': '+91' + pa}) == 1, (row['id'], lists))
    site = web(); await login(site, pa, '6274')
    r = await back.post('/api/auth/refresh')
    check('H the app renews its session (auth/refresh): 200, the same id, new cookies', r.status_code == 200 and J(r).get('id') == aid and any(x.startswith('access_token=') for x in r.headers.get_list('set-cookie')), (r.status_code, r.text[:160]))
    r = await back.post('/api/auth/logout'); gone = await back.post('/api/auth/refresh')
    check('H sign-out in the app ends that device only: the app is out (401, cannot renew); the website stays signed in',
          r.status_code == 200 and (await me(back))[0] == 401 and gone.status_code == 401 and await me(site) == (200, aid), (r.status_code, (await me(back))[0], gone.status_code))
    return '6274'


async def gate(pa, pin, aid):
    n = await DB.tejas_sessions.count_documents({'user_id': aid})
    r = await app().post(PHONE, json={'phone': pa, 'pin': pin}, headers={'Origin': 'https://evil.example'})
    check('I a write that says it comes from another website is refused before the PIN is looked at (403 origin_denied); no session is made',
          r.status_code == 403 and 'origin_denied' in r.text and await DB.tejas_sessions.count_documents({'user_id': aid}) == n, (r.status_code, r.text[:160]))
    r = await login(app(), pa, pin)
    check('I the same write with no Origin at all (how the app server sends it) is let in', r.status_code == 200 and J(r).get('id') == aid, r.status_code)


async def counted_together(pb, bid):
    codes = [(await login(app(), pb, '0001')).status_code for _ in range(5)]
    r = await login(web(), pb, '0001')
    check('J five wrong PINs from the app and one from the website are one count for that number: the sixth says 4 tries left', codes == [401] * 5 and r.status_code == 401 and '4 tries left' in r.text, (codes, r.text[:200]))
    r = await login(app(), pb, '7391'); r2 = await login(web(), pb, '0001')
    check('J the right PIN signs in and clears the count for both sides (the next wrong one says 9 tries left)', r.status_code == 200 and J(r).get('id') == bid and '9 tries left' in r2.text, (r.status_code, r2.text[:200]))
    await login(web(), pb, '7391')


async def one_address(pa, pin, aid):
    left = 900 - time.time() % 900
    if left < 45:   # the count is per quarter of an hour: do not start across its edge
        await asyncio.sleep(left + 1)
    codes = [(await signup(app(), num(), '2468', headers=via(APP_ADDRESS))).status_code for _ in range(61)]
    r = await signup(app(), num(), '2468', headers=via(APP_ADDRESS, typed=PHONE_ADDRESS))
    check("K AS BUILT TODAY: 60 sign-ups in a quarter of an hour that reach the website from ONE address pass; the 61st is refused (429, Retry-After), also when the app server names the phone's own address in front",
          codes == [200] * 60 + [429] and r.status_code == 429 and r.headers.get('retry-after', '').isdigit(), (codes[-3:], r.status_code))
    r = await signup(web(), num(), '2468', headers=via(HOME_ADDRESS)); r2 = await login(app(), pa, pin, headers=via(APP_ADDRESS))
    check('K at that moment a browser at another address still signs up, and a right PIN through the app address still signs in (sign-in is not in this count)', r.status_code == 200 and r2.status_code == 200, (r.status_code, r2.status_code))
    codes = []
    for i in range(12):
        ghost = num()
        for _ in range(9 if i < 11 else 1):
            codes.append((await login(app(), ghost, '1234', headers=via(APP_ADDRESS))).status_code)
    r = await login(app(), pa, pin, headers=via(APP_ADDRESS)); r2 = await login(app(), pa, pin, headers=via(APP_ADDRESS, typed=PHONE_ADDRESS)); r3 = await login(web(), pa, pin, headers=via(HOME_ADDRESS))
    check('K AS BUILT TODAY: 100 wrong PINs in a quarter of an hour from ONE address (any numbers) make that address wait: a RIGHT PIN through it is refused (429) for 15 minutes; a browser at another address signs in',
          len(codes) == 100 and set(codes) == {401} and r.status_code == 429 and r2.status_code == 429 and int(r.headers.get('retry-after', 0)) > 800 and r3.status_code == 200 and J(r3).get('id') == aid,
          (len(codes), sorted(set(codes)), r.status_code, r2.status_code, r3.status_code))


async def main():
    assert not H.leftover_real_handles()
    await H.tdbmod.indexes(); await structure.seed()
    try:
        pa, pb, aid, bid, a_app, a_web, b_app, b_web = await both_ways()
        await one_number(pa, pb, aid, bid)
        await name(aid, a_app, a_web)
        at = await paper(aid, a_app, a_web, b_app)
        pin = await pins(pa, aid, at, a_app, a_web)
        await gate(pa, pin, aid)
        await counted_together(pb, bid)
        await one_address(pa, pin, aid)
        rows = {p['phone']: p['id'] async for p in DB.tejas_phone_profiles.find({'phone': {'$in': ['+91' + pa, '+91' + pb]}})}
        check('at the end: each of the two numbers still has its one account with the id it was given at sign-up', rows == {'+91' + pa: aid, '+91' + pb: bid}, rows)
    except Exception as e:   # noqa: BLE001
        import traceback; traceback.print_exc(); check('no crash', False, repr(e))
    finally:
        # Only the disposable database this run created; never the app's own.
        assert H.TEST_DB.startswith('tejas_isolated_') and H.TEST_DB != H.REAL_DB, H.TEST_DB
        await H.tdbmod.client.drop_database(H.TEST_DB)
        print('dropped', H.TEST_DB, flush=True)
        bad = [r for r in RESULTS if not r[1]]
        print(f'TOTAL {len(RESULTS)} PASS {len(RESULTS) - len(bad)} FAIL {len(bad)}', flush=True)


if __name__ == '__main__':
    asyncio.run(main())
