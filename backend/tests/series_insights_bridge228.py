"""TEST-ONLY iteration 228 bridge for the All India 'saare din ek saath' insights + day result buttons.
Real app on 127.0.0.1:8777 bound to a disposable isolated DB (storage + AI mocked). Series clock frozen at 14 Dec 2026 15:00 IST (day 6).
hero: live days 1-6 finished (day 3 = a real graded attempt, others copies with set marks); papers carry chapter tags.
peer: live days 1, 2, 4 + practice day 5; papers carry NO chapter tags (subject-wise fallback).
Two other students sit each live day so every closed day has an average and a topper; day 6's class stays sealed until 11:59 PM.
Writes /tmp/uibridge228s/bridge.json (hero/peer cookies, attempt ids, expected numbers; 0600). DB dropped on exit.
Run: cd /app/backend && setsid nohup python tests/series_insights_bridge228.py 2400 > /tmp/bridge228s.log 2>&1 &
"""
import asyncio, copy, json, os, sys, uuid
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import analysis_fixture195 as F  # noqa: E402
from book_publishing_iso170 import H  # noqa: E402
import httpx, uvicorn  # noqa: E402
from datetime import date, datetime  # noqa: E402
from tejas import canonical, live_series  # noqa: E402

OUT = '/tmp/uibridge228s'
BASE = [l.split('=', 1)[1].strip() for l in open('/app/frontend/.env') if l.startswith('REACT_APP_BACKEND_URL')][0].rstrip('/')


def ist(d, h=0):
    return datetime.combine(date.fromisoformat(d), datetime.min.time().replace(hour=h), live_series.IST).timestamp()


CLOCK = ist('2026-12-14', 15)
DAYS = {i: (live_series.FIRST + live_series.timedelta(days=i - 1)).isoformat() for i in range(1, 7)}
HERO = {1: (50, 40, 60), 2: (55, 35, 70), 3: (60, 30, 80), 4: (70, 30, 90), 5: (75, 25, 100), 6: (80, 30, 100)}
HERO_ACC = {1: 60.0, 2: 62.0, 3: 65.0, 4: 68.0, 5: 70.0, 6: 72.0}
HERO_TOPICS = {1: {'Rotational Motion': (4, 3, 1), 'Definite Integration': (5, 4, 2)}, 2: {'Rotational Motion': (4, 4, 2), 'Chemical Bonding': (5, 3, 1)},
               3: {'Rotational Motion': (4, 2, 1), 'Chemical Bonding': (5, 4, 2)}, 4: {'Rotational Motion': (4, 4, 3)},
               5: {'Chemical Bonding': (5, 5, 3)}, 6: {'Definite Integration': (5, 5, 5)}}
PEER = {1: (40, 30, 30, 'series_live'), 2: (45, 35, 30, 'series_live'), 4: (35, 40, 35, 'series_live'), 5: (50, 45, 40, 'series_practice')}


async def fake_database_now():
    return CLOCK


def freeze_series_clock():
    real = canonical.database_now
    for name, mod in list(sys.modules.items()):
        if mod is None or not (name.startswith('tejas') or name == 'server'):
            continue
        if getattr(mod, 'database_now', None) is real:
            setattr(mod, 'database_now', fake_database_now)
    import tejas.series_streak as st
    st.now = lambda: CLOCK


def summary(base, p, c, m, acc, topics=None):
    score = p + c + m
    subjects = {'Physics': {'count': 25, 'correct': p // 4, 'attempted': p // 4 + 3, 'score': p}, 'Chemistry': {'count': 25, 'correct': c // 4, 'attempted': c // 4 + 3, 'score': c},
                'Mathematics': {'count': 25, 'correct': m // 4, 'attempted': m // 4 + 3, 'score': m}}
    tops = {name: dict(g) for name, g in subjects.items()}
    for name, (count, attempted, correct) in (topics or {}).items():
        tops[name] = {'count': count, 'attempted': attempted, 'correct': correct, 'score': 4 * correct - (attempted - correct)}
    attempted = sum(g['attempted'] for g in subjects.values())
    return {**(base or {}), 'score': score, 'maximum': 300, 'eligible_count': 75, 'attempted': attempted, 'correct': sum(g['correct'] for g in subjects.values()),
            'incorrect': attempted - sum(g['correct'] for g in subjects.values()), 'skipped': 75 - attempted, 'accuracy': acc,
            'attempt_rate': round(100 * attempted / 75, 1), 'total_seconds': 170 * 60, 'subjects': subjects, 'topics': tops}


async def main():
    path = OUT + '/bridge.json'
    try:
        assert not H.leftover_real_handles()
        os.makedirs(OUT, exist_ok=True)
        f = await F.build(others=2)
        hero, real_id = f['hero'], f['hero_attempt']
        T = H.TDB
        uid = (await T.tejas_attempts.find_one({'id': real_id}))['user_id']
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=H.app), base_url='http://bridge') as c:
            r = await c.post('/api/auth/phone/signup', json={'phone': '9822299001', 'pin': '8261', 'confirm_pin': '8261'}, headers={'origin': BASE})
            assert r.status_code == 200, r.text
            peer = dict(r.cookies)
        peer_id = (await T.tejas_phone_profiles.find_one({'phone': '+919822299001'}))['id']
        base = await T.tejas_sets.find_one({'id': f['set']})
        set_ids = {}
        for day, d in DAYS.items():
            doc = copy.deepcopy(base); doc.pop('_id', None)
            doc.update({'id': f'TEST_S228_day{day}_' + uuid.uuid4().hex[:6], 'title': f'TEST_All India JEE Mains · Test {day:02d}', 'series_id': live_series.SERIES_ID,
                        'series_date': d, 'series_window': live_series.window(d), 'status': 'published'})
            await T.tejas_sets.insert_one(doc); set_ids[day] = doc['id']
        real = await T.tejas_attempts.find_one({'id': real_id}); real.pop('_id', None)

        async def put(doc):  # copies carry no ledger (it is bound to its own attempt), so only day 3 opens a full analysis
            await T.tejas_attempts.insert_one(doc)

        def copy_of(user, day, s, mode='series_live', hour=1):
            d, w = DAYS[day], live_series.window(DAYS[day])
            doc = copy.deepcopy(real)
            doc.update({'id': 'TEST_A228_%s_d%d_%s' % (user[:6], day, uuid.uuid4().hex[:6]), 'user_id': user, 'set_id': set_ids[day], 'start_key': uuid.uuid4().hex,
                        'receipt': uuid.uuid4().hex, 'series_id': live_series.SERIES_ID, 'series_date': d, 'mode': mode, 'summary': s,
                        'started_at': w['opens_at'] + hour * 3600, 'submitted_at': w['opens_at'] + hour * 3600 + 170 * 60, 'competition_end': w['closes_at']})
            if mode != 'series_live':
                doc.update(started_at=CLOCK - 7200, submitted_at=CLOCK - 3600, competition_end=None)
            doc.pop('start_request_keys', None)
            return doc

        ids = {'hero': {}, 'peer': {}}
        for day, (p, c, m) in HERO.items():
            s = summary(real.get('summary'), p, c, m, HERO_ACC[day], HERO_TOPICS[day])
            if day == 3:
                w = live_series.window(DAYS[3])
                await T.tejas_attempts.update_one({'id': real_id}, {'$set': {'set_id': set_ids[3], 'series_id': live_series.SERIES_ID, 'series_date': DAYS[3], 'mode': 'series_live',
                    'summary': s, 'started_at': w['opens_at'] + 3600, 'submitted_at': w['opens_at'] + 3600 + 170 * 60, 'competition_end': w['closes_at']}})
                ids['hero'][day] = real_id
            else:
                doc = copy_of(uid, day, s, hour=9 if day == 6 else 1)
                await put(doc); ids['hero'][day] = doc['id']
        for day, (p, c, m, mode) in PEER.items():
            doc = copy_of(peer_id, day, summary(real.get('summary'), p, c, m, 55.0), mode)
            await put(doc); ids['peer'][day] = doc['id']
        for day in DAYS:
            for k, score in enumerate((100 + 10 * day, 240 + 5 * day)):
                third = score // 3
                await put(copy_of('TEST_other%d' % k, day, summary(real.get('summary'), third, third, score - 2 * third, 70.0)))
        freeze_series_clock()
        peer_live = lambda day: day in PEER and PEER[day][3] == 'series_live'
        avg = lambda day: round((sum(HERO[day]) + (sum(PEER[day][:3]) if peer_live(day) else 0) + 100 + 10 * day + 240 + 5 * day) / (3 + peer_live(day)), 1)
        expect = {'hero': {'overall.days': 6, 'overall.live_days': 6, 'overall.compared_days': 5, 'overall.best': 210, 'overall.direction': 'up',
                           'day_average': {d: avg(d) for d in range(1, 6)}, 'day_topper': {d: 240 + 5 * d for d in range(1, 6)}, 'day6_class': 'sealed',
                           'subjects': {'Physics': 'up', 'Chemistry': 'down', 'Mathematics': 'up'}, 'chapters_tagged': True,
                           'first_chapter': 'Rotational Motion (4 days)'},
                  'peer': {'overall.days': 4, 'overall.live_days': 3, 'chapters_tagged': False}}
        with open(path, 'w') as fh:
            json.dump({'hero': dict(hero.cookies), 'peer': peer, 'user_id': uid, 'peer_id': peer_id, 'attempts': ids, 'sets': set_ids, 'clock': CLOCK, 'days': DAYS, 'expect': expect}, fh, indent=1)
        os.chmod(path, 0o600)
        print('READY', H.TEST_DB, flush=True)
        server = uvicorn.Server(uvicorn.Config(H.app, host='127.0.0.1', port=8777, log_level='warning', lifespan='off'))
        try:
            await asyncio.wait_for(server.serve(), int(sys.argv[1]) if len(sys.argv) > 1 else 900)
        except asyncio.TimeoutError:
            pass
    finally:
        assert H.TEST_DB.startswith('tejas_isolated_') and H.TEST_DB != H.REAL_DB
        await H.tdbmod.client.drop_database(H.TEST_DB)
        try:
            os.unlink(path)
        except OSError:
            pass
        print('dropped', H.TEST_DB, flush=True)

asyncio.run(main())
