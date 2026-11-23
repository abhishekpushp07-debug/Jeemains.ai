"""TEST-ONLY iteration 227 browser bridge for the All India series hub (app look, marks on day buttons, day analysis).
Real app on 127.0.0.1:8775 bound to a disposable isolated DB (storage + AI mocked). The series clock is frozen at
14 Dec 2026 15:00 IST (day 6): days 1-5 are past (archive), day 6 is live today.
Hero student: day 1 + day 2 + day 3 live attempts finished (day 3 = a real graded attempt, the others are copies of it with
other marks), days 4 and 5 not attempted (a tap starts them), day 6 live and not attempted. Days 7-50 have no paper.
Writes /tmp/uibridge227/bridge.json (hero cookies, attempt ids, set ids; 0600).
Run: cd /app/backend && setsid nohup python tests/series_hub_bridge227.py 2400 > /tmp/bridge227.log 2>&1 &
"""
import asyncio, copy, json, os, sys, uuid
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import analysis_fixture195 as F  # noqa: E402
from book_publishing_iso170 import H  # noqa: E402
import uvicorn  # noqa: E402
from datetime import date, datetime  # noqa: E402
from tejas import canonical, live_series  # noqa: E402


def ist(d, h=0):
    return datetime.combine(date.fromisoformat(d), datetime.min.time().replace(hour=h), live_series.IST).timestamp()


OUT = '/tmp/uibridge227'
CLOCK = ist('2026-12-14', 15)
DAYS = {i: (live_series.FIRST + live_series.timedelta(days=i - 1)).isoformat() for i in range(1, 7)}


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


async def main():
    path = OUT + '/bridge.json'
    try:
        assert not H.leftover_real_handles()
        os.makedirs(OUT, exist_ok=True)
        f = await F.build(others=2)
        hero, real_id = f['hero'], f['hero_attempt']
        uid = (await H.TDB.tejas_attempts.find_one({'id': real_id}))['user_id']
        sets_coll = H.TDB.tejas_sets
        base = await sets_coll.find_one({'id': f['set']})
        set_ids = {}
        for day, d in DAYS.items():
            doc = copy.deepcopy(base); doc.pop('_id', None)
            doc.update({'id': f'TEST_S227_day{day}_' + uuid.uuid4().hex[:6], 'title': f'TEST_All India JEE Mains · Test {day:02d}', 'series_id': live_series.SERIES_ID,
                        'series_date': d, 'series_window': live_series.window(d), 'status': 'published'})
            await sets_coll.insert_one(doc); set_ids[day] = doc['id']
        real = await H.TDB.tejas_attempts.find_one({'id': real_id}); real.pop('_id', None)
        ids = {}
        for day, score in ((1, 188), (2, 205), (3, None)):
            d = DAYS[day]; w = live_series.window(d)
            if score is None:
                aid = real_id
                await H.TDB.tejas_attempts.update_one({'id': aid}, {'$set': {'series_id': live_series.SERIES_ID, 'series_date': d, 'mode': 'series_live',
                                                                            'started_at': w['opens_at'] + 3600, 'submitted_at': w['opens_at'] + 7200, 'competition_end': w['closes_at']}})
            else:
                doc = copy.deepcopy(real); aid = 'TEST_A227_day%d_%s' % (day, uuid.uuid4().hex[:8])
                doc.update({'id': aid, 'start_key': uuid.uuid4().hex, 'receipt': uuid.uuid4().hex, 'series_id': live_series.SERIES_ID, 'series_date': d,
                            'mode': 'series_live', 'started_at': w['opens_at'] + 3600, 'submitted_at': w['opens_at'] + 7200, 'competition_end': w['closes_at'],
                            'summary': {**(real.get('summary') or {}), 'score': score, 'maximum': 300}})
                doc.pop('start_request_keys', None)
                await H.TDB.tejas_attempts.insert_one(doc)
            ids[day] = aid
        freeze_series_clock()
        with open(path, 'w') as fh:
            json.dump({'hero': dict(hero.cookies), 'user_id': uid, 'attempts': ids, 'sets': set_ids, 'clock': CLOCK, 'days': DAYS}, fh)
        os.chmod(path, 0o600)
        print('READY', H.TEST_DB, flush=True)
        server = uvicorn.Server(uvicorn.Config(H.app, host='127.0.0.1', port=8775, log_level='warning', lifespan='off'))
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
