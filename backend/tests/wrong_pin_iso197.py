"""TEST-ONLY iteration 197: sign-in limit counts only wrong PINs, per number (10 -> 15 min wait) and per real student address (100).
Real app over httpx ASGITransport, peer = private ingress address, X-Forwarded-For shaped like the live edge
('<typed by client>, student, Cloudflare, load balancer'). Isolated random DB (iso_harness_iter156), dropped before and after.
Run: cd /app/backend && python tests/wrong_pin_iso197.py
"""
import asyncio, secrets, sys
from pathlib import Path
from types import SimpleNamespace
sys.path.insert(0, str(Path(__file__).resolve().parent))
import httpx  # noqa: E402
import iso_harness_iter156 as H  # noqa: E402
from tejas import phone as P  # noqa: E402

TDB = H.TDB
RESULTS = []
CALLS = [0]
_verify = P.verify
LB, EDGE, EDGE2 = '136.110.214.0', '172.70.100.107', '104.22.62.16'


def check(name, ok, info=''):
    RESULTS.append(bool(ok))
    print(('PASS ' if ok else 'FAIL ') + name + ('' if ok else f'  -> {info}'), flush=True)


def counting(p, h):
    CALLS[0] += 1
    return _verify(p, h)


def xff(student, typed=None):
    return {'X-Forwarded-For': ','.join(([typed] if typed else []) + [student, EDGE, LB])}


def req(header=None, peer='10.81.1.13'):
    return SimpleNamespace(headers={'x-forwarded-for': header} if header else {}, client=SimpleNamespace(host=peer) if peer else None)


_n = [0]


def number():
    _n[0] += 1
    return f'99197{secrets.randbelow(90) + 10}{_n[0]:03d}'


def wrong(p):
    return f'{(int(p) + 1) % 10000:04d}'


def client():
    return httpx.AsyncClient(transport=httpx.ASGITransport(app=H.app, raise_app_exceptions=False, client=('10.81.1.13', 4321)),
                             base_url='https://api.test.example', headers={'Origin': H.ORIGIN}, timeout=120)


async def signup(c, ph, p, ip):
    r = await c.post('/api/auth/phone/signup', json={'phone': ph, 'pin': p, 'confirm_pin': p}, headers=xff(ip))
    assert r.status_code == 200, r.text


async def login(c, ph, p, ip, typed=None):
    return await c.post('/api/auth/phone', json={'phone': ph, 'pin': p}, headers=xff(ip, typed))


def later(seconds):
    H.OFFSET[0] += seconds


def unit():
    check('student is the hop left of Cloudflare', P.client_ip(req(f'34.170.12.145,{EDGE},{LB}')) == '34.170.12.145')
    check('a typed X-Forwarded-For is ignored', P.client_ip(req(f'1.2.3.4,34.170.12.145,{EDGE2},{LB}')) == '34.170.12.145')
    check('two Cloudflare hops are skipped', P.client_ip(req(f'49.36.1.2,104.16.0.5,172.64.0.9,{LB}')) == '49.36.1.2')
    check('IPv6 student', P.client_ip(req(f'2405:201:5c01::7,2400:cb00::1,{LB}')) == '2405:201:5c01::7')
    check('no Cloudflare hop -> no address (number limit only)', P.client_ip(req(f'1.2.3.4,{LB}')) is None)
    check('private student hop -> no address', P.client_ip(req(f'10.0.0.5,{EDGE},{LB}')) is None)
    check('garbage left of Cloudflare -> no address', P.client_ip(req(f'not-an-ip,{EDGE},{LB}')) is None)
    check('only Cloudflare -> no address', P.client_ip(req(f'{EDGE},{LB}')) is None)
    check('no header, public peer -> peer', P.client_ip(req(None, '49.36.9.9')) == '49.36.9.9')
    check('no header, private peer -> no address', P.client_ip(req(None, '10.81.1.13')) is None)


async def main():
    assert H.TEST_DB != H.REAL_DB and not H.leftover_real_handles()
    await H.tdbmod.client.drop_database(H.TEST_DB)
    await H.tdbmod.indexes()
    P.verify = counting
    unit()
    async with client() as c:
        # 1. Correct PINs are never counted: 70 correct sign-ins from one address, 7 numbers.
        ip = '49.36.10.1'
        people = [(number(), f'{secrets.randbelow(10000):04d}') for _ in range(7)]
        for ph, p in people:
            await signup(c, ph, p, ip)
        codes = [(await login(c, ph, p, ip)).status_code for _ in range(10) for ph, p in people]
        check('70 correct sign-ins from one address all pass', codes == [200] * 70, sorted(set(codes)))
        left = await TDB.tejas_phone_limits.count_documents({'started': {'$exists': True}})
        check('no wrong-PIN counter was written for correct PINs', left == 0, left)

        # 2. 9 wrong -> 401 with tries left, 10th wrong -> 429 15 min, then even the correct PIN waits (no PIN check).
        ph, p = people[0]
        ip = '49.36.20.2'
        msgs = [await login(c, ph, wrong(p), ip) for _ in range(9)]
        check('9 wrong PINs -> 401', [r.status_code for r in msgs] == [401] * 9, [r.status_code for r in msgs])
        check('message counts down the tries', '9 tries left' in msgs[0].text and '1 try left' in msgs[-1].text, [msgs[0].text[:160], msgs[-1].text[:160]])
        r = await login(c, ph, wrong(p), ip)
        check('10th wrong PIN -> 429, 15 min', r.status_code == 429 and 880 <= int(r.headers.get('retry-after', 0)) <= 901, [r.status_code, r.headers.get('retry-after'), r.text[:120]])
        before = CALLS[0]
        r = await login(c, ph, p, '49.36.20.3')
        check('during the wait even the correct PIN (other address) waits, PIN not checked', r.status_code == 429 and CALLS[0] == before, [r.status_code, CALLS[0] - before])
        later(600)
        r = await login(c, ph, p, ip)
        check('still waiting after 10 min', r.status_code == 429 and 280 <= int(r.headers['retry-after']) <= 301, [r.status_code, r.headers.get('retry-after')])
        later(301)
        r = await login(c, ph, p, ip)
        check('after 15 min the correct PIN signs in', r.status_code == 200, r.text[:160])
        r = await login(c, ph, wrong(p), ip)
        check('fresh count after the wait', r.status_code == 401 and '9 tries left' in r.text, r.text[:160])

        # 3. A correct PIN clears the count.
        ph, p = people[1]
        for _ in range(5):
            await login(c, ph, wrong(p), ip)
        check('correct PIN after 5 wrong signs in', (await login(c, ph, p, ip)).status_code == 200)
        codes = [(await login(c, ph, wrong(p), ip)).status_code for _ in range(9)]
        check('count started again after the correct PIN', codes == [401] * 9, codes)
        await login(c, ph, p, ip)

        # 4. Wrong PINs more than 15 min apart from the first start a new count.
        ph, p = people[2]
        for _ in range(9):
            await login(c, ph, wrong(p), ip)
        later(16 * 60)
        codes = [(await login(c, ph, wrong(p), ip)).status_code for _ in range(9)]
        check('9 + 9 wrong across 16 minutes never waits', codes == [401] * 9, codes)
        await login(c, ph, p, ip)

        # 5. One address: 100 wrong PINs (unknown numbers, at most 9 each) -> that address waits, others do not.
        bad = '49.36.30.3'
        later(16 * 60)
        codes = []
        for i in range(12):
            ghost = number()
            for _ in range(9 if i < 11 else 1):
                codes.append((await login(c, ghost, '1234', bad)).status_code)
        check('100 wrong PINs from one address -> 401 each', len(codes) == 100 and set(codes) == {401}, [len(codes), sorted(set(codes))])
        ph, p = people[3]
        r = await login(c, ph, p, bad)
        check('that address now waits, even with a correct PIN', r.status_code == 429 and int(r.headers['retry-after']) > 800, [r.status_code, r.text[:120]])
        r = await login(c, ph, p, bad, typed='8.8.8.8')
        check('a typed X-Forwarded-For does not get around the wait', r.status_code == 429, r.status_code)
        r = await login(c, ph, p, '49.36.30.4')
        check('another student behind the same Cloudflare edge signs in', r.status_code == 200, r.text[:160])

        # 6. The old bug: thousands of students share the Cloudflare/ingress hop, which is never counted.
        r = await c.post('/api/auth/phone', json={'phone': people[4][0], 'pin': people[4][1]}, headers={'X-Forwarded-For': f'{EDGE},{LB}'})
        check('edge-only header still signs in (no shared address limit)', r.status_code == 200, r.text[:160])
        ip_rows = await TDB.tejas_phone_limits.count_documents({'blocked_until': {'$exists': True}})
        check('only the address wait is left (the number wait was cleared by its correct PIN)', ip_rows == 1, ip_rows)

        # 7. Signup, Forgot PIN and wrong-PIN messages keep working; no secrets in replies.
        ph = number()
        r = await c.post('/api/auth/phone/signup', json={'phone': ph, 'pin': '4321', 'confirm_pin': '4321'}, headers=xff('49.36.40.4'))
        check('signup works', r.status_code == 200, r.text[:160])
        r = await c.post('/api/auth/pin/reset', json={'phone': ph, 'new_pin': '5678', 'confirm_pin': '5678'}, headers=xff('49.36.40.4'))
        check('Forgot PIN works', r.status_code == 200, r.text[:160])
        r = await login(c, ph, '4321', '49.36.40.4')
        check('old PIN is wrong after reset, no secret in reply', r.status_code == 401 and '$2b$' not in r.text and 'pin_hash' not in r.text, r.text[:160])
    P.verify = _verify
    await H.tdbmod.client.drop_database(H.TEST_DB)
    check('isolated DB dropped', H.TEST_DB not in await H.tdbmod.client.list_database_names())
    print(f'\n{sum(RESULTS)}/{len(RESULTS)} passed', flush=True)


asyncio.run(main())
