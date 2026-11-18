"""Staged load test for jeelive.ai: sign-up rush, paper open, answer saves every ~30 s, last-second submit.
Each stage stops by itself when errors pass 2 % or p95 latency passes 5 s. Accounts use one reserved test prefix.
Usage: python tools/load_live.py BASE_URL PREFIX SET_ID STAGES   (e.g. https://jeelive.ai +91600001 jee-main-pyq-2025-04-02-s1 50,200,800)
Env: LOAD_SIGNIN_ONLY=1 (accounts already seeded, exam-day sign-in rush), LOAD_PACKS (picture packs per student, 7 = whole JEE paper),
LOAD_MEDIA=1 (pictures through the public CDN links of /assets/links, fetched without cookies, like the website),
LOAD_PIDS=backend:PID,mongo:PID (CPU-seconds each process used per stage, same machine only).
Every save carries the time record like the real player (2 on-screen stretches + the answer change); about 1 visit per 2 saves.
"""
import asyncio, json, os, random, sys, time, uuid
from collections import Counter, defaultdict
import aiohttp

BASE, PREFIX, SET_ID = sys.argv[1].rstrip('/'), sys.argv[2], sys.argv[3]
STAGES = [int(x) for x in sys.argv[4].split(',')]
SAVE_EVERY, WRITE_SECONDS, PIN = int(os.environ.get('LOAD_SAVE_EVERY', 30)), int(os.environ.get('LOAD_WRITE_SECONDS', 150)), '4826'
SIGNIN_ONLY, PACKS, RAMP = os.environ.get('LOAD_SIGNIN_ONLY') == '1', int(os.environ.get('LOAD_PACKS', 1)), float(os.environ.get('LOAD_RAMP', 0))
MEDIA = os.environ.get('LOAD_MEDIA') == '1'
PIDS = dict(x.split(':') for x in os.environ.get('LOAD_PIDS', '').split(',') if x)
UA = {'User-Agent': 'Mozilla/5.0 (JEELIVE load test)', 'Content-Type': 'application/json', 'Origin': os.environ.get('LOAD_ORIGIN', BASE)}
LAT, CODES, ERR, BYTES = defaultdict(list), defaultdict(Counter), [], Counter()
FINAL = Counter()  # calls that still failed after the student's retries (what the student is left with)
STOP = asyncio.Event()


def phone(i):
    tail = 10 - (len(PREFIX) - 3)
    return PREFIX + str(i).zfill(tail)


async def call(s, step, method, path, body=None, jar=None, tries=6):
    """First-try status is what a student sees; busy answers are retried like a student tapping again."""
    for n in range(tries):
        t = time.perf_counter()
        headers = {**UA, **({'Cookie': '; '.join(f'{k}={v}' for k, v in jar.items())} if jar else {})}
        wait = 2
        try:
            async with s.request(method, BASE + '/api' + path, json=body, headers=headers, timeout=aiohttp.ClientTimeout(total=60)) as r:
                raw = await r.read()
                BYTES[step] += len(raw)
                text = raw.decode('utf-8', 'replace') if 'json' in r.headers.get('Content-Type', '') or r.status >= 400 else ''
                code = r.status
                wait = float(r.headers.get('Retry-After') or 2)
                if jar is not None:
                    jar.update({k: v.value for k, v in r.cookies.items()})
        except Exception as e:
            code, text = 0, type(e).__name__
        name = step if n == 0 else step + '_retry'
        LAT[name].append(time.perf_counter() - t); CODES[name][code] += 1
        if code >= 400 and code != 409 and len(ERR) < 40:
            ERR.append((name, code, text[:160]))
        if code not in (0, 429, 503) or STOP.is_set():
            break
        await asyncio.sleep(min(10, wait) + random.uniform(0, 1))
    FINAL['calls'] += 1
    FINAL['failed'] += code in (0, 429) or code >= 500
    try:
        j = json.loads(text)
        return code, (j.get('data') if isinstance(j, dict) and 'data' in j else j)
    except Exception:
        return code, None


async def student(i, signup_only=False):
    jar = {}
    await asyncio.sleep(random.uniform(0, RAMP))
    async with aiohttp.ClientSession() as s:
        go = lambda *a, **k: call(s, *a, jar=jar, **k)
        code = 409 if SIGNIN_ONLY else (await go('signup', 'POST', '/auth/phone/signup', {'phone': phone(i), 'pin': PIN, 'confirm_pin': PIN}))[0]
        if code == 409:
            code, _ = await go('signin', 'POST', '/auth/phone', {'phone': phone(i), 'pin': PIN})
        if code != 200 or signup_only or STOP.is_set():
            return
        code, a = await go('start', 'POST', f'/sets/{SET_ID}/start', {'start_key': uuid.uuid4().hex})
        if code != 200 or not a:
            return
        aid = a['id']
        await go('begin', 'POST', f'/attempts/{aid}/begin')
        if MEDIA:
            _, links = await go('links', 'GET', f'/attempts/{aid}/assets/links')
            for link in ((links or {}).get('parts') or [])[:PACKS]:
                await call(s, 'media', 'GET', link[len(BASE) + 4:] if link.startswith('http') else link[4:])
        for k in range(0 if MEDIA else PACKS):
            await go('pack', 'GET', f'/attempts/{aid}/assets/pack?offset={12 * k}&limit=12')
        qs = [q for q in (a.get('questions') or []) if q.get('type') == 'mcq' and q.get('options')]
        rev, n, sid, seen = {}, 0, uuid.uuid4().hex[:16], time.time()
        end = time.monotonic() + WRITE_SECONDS
        await asyncio.sleep(random.uniform(0, SAVE_EVERY))
        while time.monotonic() < end and qs and not STOP.is_set():
            q = random.choice(qs); rev[q['id']] = rev.get(q['id'], 0) + 1
            if random.random() < .5:
                await go('visit', 'POST', f'/attempts/{aid}/visit', {'question_id': q['id']})
            value, t = random.choice(list(q['options'])), time.time() - 1
            mid = seen + (t - seen) / 2
            events = [{'n': n + 1, 'k': 'v', 'q': random.choice(qs)['id'], 'a': seen, 'b': mid},
                      {'n': n + 2, 'k': 'v', 'q': q['id'], 'a': mid, 'b': t}, {'n': n + 3, 'k': 'a', 'q': q['id'], 'a': t, 'v': value}]
            n, seen = n + 3, t
            await go('save', 'PUT', f"/attempts/{aid}/answers/{q['id']}",
                     {'value': value, 'revision': rev[q['id']], 'request_id': uuid.uuid4().hex, 'timeline': {'sid': sid, 'events': events}})
            await asyncio.sleep(SAVE_EVERY + random.uniform(-3, 3))
        await go('submit', 'POST', f'/attempts/{aid}/submit')
        for _ in range(10):
            code, r = await go('results', 'GET', f'/attempts/{aid}/results', tries=1)
            if code == 200:
                break
            await asyncio.sleep(3)


def p(xs, q):
    xs = sorted(xs); return xs[min(len(xs) - 1, int(q * len(xs)))] if xs else 0


def cpu(pid):
    try:
        f = open(f'/proc/{pid}/stat').read().rsplit(')', 1)[1].split()
        return (int(f[11]) + int(f[12])) / os.sysconf('SC_CLK_TCK')
    except OSError:
        return None


def report(stage, seconds, used=None):
    out = {'stage_students': stage, 'seconds': round(seconds, 1), 'cpu_seconds': used or {}, 'steps': {}}
    for step in LAT:
        n = len(LAT[step]); bad = sum(v for k, v in CODES[step].items() if k == 0 or k >= 500 or k == 429)
        if step.endswith('_retry'):
            bad = 0
        out['steps'][step] = {'n': n, 'codes': dict(CODES[step]), 'p50': round(p(LAT[step], .5), 3), 'p95': round(p(LAT[step], .95), 3),
                              'max': round(max(LAT[step]), 3), 'bad_pct': round(100 * bad / n, 2) if n else 0, 'mb': round(BYTES[step] / 1e6, 2)}
    out['still_failed_after_retries'] = dict(FINAL)
    out['first_errors'] = ERR[:15]
    return out


async def watchdog():
    while not STOP.is_set():
        await asyncio.sleep(5)
        allc, bad = FINAL['calls'], FINAL['failed']
        recent = [x for v in LAT.values() for x in v[-200:]]
        if allc > 50 and (bad / allc > .02 or p(recent, .95) > 5):
            print('ABORT: errors', bad, 'of', allc, 'p95', round(p(recent, .95), 2), flush=True); STOP.set()


async def main():
    base = int(os.environ.get('LOAD_BASE', 0))
    for stage in STAGES:
        LAT.clear(); CODES.clear(); ERR.clear(); BYTES.clear(); FINAL.clear()
        t = time.perf_counter(); dog = asyncio.create_task(watchdog())
        before = {k: cpu(v) for k, v in {**PIDS, 'generator': os.getpid()}.items()}
        await asyncio.gather(*(student(base + i) for i in range(stage)))
        used = {k: round(cpu(v) - before[k], 1) for k, v in {**PIDS, 'generator': os.getpid()}.items() if before[k] is not None and cpu(v) is not None}
        dog.cancel(); print(json.dumps(report(stage, time.perf_counter() - t, used)), flush=True)
        base += stage
        if STOP.is_set():
            break
        await asyncio.sleep(20)


asyncio.run(main())
