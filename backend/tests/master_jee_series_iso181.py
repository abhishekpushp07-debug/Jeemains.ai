"""TEST-ONLY iteration 181b: the JEE Main All India series run from the new Master routes with a real 75-question PDF book.
Isolated disposable DB (storage + AI mocked). Run: cd /app/backend && timeout 280 python tests/master_jee_series_iso181.py
"""
import asyncio, sys, uuid
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import book_publishing_iso170 as T  # noqa: E402,F401
from book_publishing_iso170 import H, mkstaff, client, upload, complete, drain, check, RESULTS  # noqa: E402
from library_aits_iso180 import build_aits, aits_mock  # noqa: E402
from structure_iso173 import start  # noqa: E402
from tejas import structure, live_series  # noqa: E402

SETS, M, S = H.TDB.tejas_sets, '/api/admin/master', live_series.SERIES_ID


def J(r):
    try: d = r.json()
    except Exception: return {}
    if isinstance(d, dict) and 'data' in d and 'error' in d: d = d['data']
    return d if d is not None else {}


async def main():
    own, _ = await mkstaff('owner', 'j'); anon = client()
    stu = client(); await stu.post('/api/auth/phone/signup', json={'phone': '93' + str(uuid.uuid4().int)[:8], 'pin': '8261', 'confirm_pin': '8261'})
    book = await upload(own, build_aits([aits_mock(1), aits_mock(2)]), 'JEE Series Book', section_id='jee-main:aits'); await complete(own, book['id']); await drain()
    rows = J(await own.get(f'{M}/types/jee-main:aits/mocks')); check('JEE series type opens in Master', rows.get('section', {}).get('kind') == 'aits' and rows['section']['series_id'] == S, rows.get('section'))
    cands = [c for c in J(await own.get(f'{M}/series/{S}')).get('candidates', []) if c['kind'] == 'book_mock']
    check('both PDF papers listed, waiting for numerical answers to be confirmed', len(cands) == 2 and all(c['held'] and c['count'] == 75 for c in cands), cands)
    r = await own.post(f'{M}/series/{S}/assign', json={'kind': 'book_mock', 'id': cands[0]['id'], 'date': '2026-12-05'}); check('paper with things to fix cannot take a day 409', r.status_code == 409, r.status_code)
    for c in cands:
        base = f"/api/admin/books/{book['id']}/mocks/{c['id']}"
        for _ in range(40):
            p = J(await own.get(base + '/problems'))
            if not p.get('questions'): break
            q = p['questions'][0]; integer = q['number'] % 25 in (21, 22, 23, 24, 0)
            r = await own.post(base + '/fix', json={'revision': p['revision'], 'question_id': q['id'], 'response_type': 'integer' if integer else 'mcq',
                'option_labels': [] if integer else ['A', 'B', 'C', 'D'], 'answer': str((q['number'] - 1) % 25) if integer else 'B', 'complete': True}); await drain()
            if r.status_code != 200: print('fix fail', q['number'], r.status_code, r.text[:200]); break
    cands = [c for c in J(await own.get(f'{M}/series/{S}')).get('candidates', []) if c['kind'] == 'book_mock']
    check('after Fix both papers can take a day', len(cands) == 2 and all(not c['problem'] and not c['held'] for c in cands), cands)
    r = await own.post(f'{M}/series/{S}/assign', json={'kind': 'book_mock', 'id': cands[0]['id'], 'date': '2026-12-05'}); await drain()
    s = await SETS.find_one({'series_id': S, 'series_date': '2026-12-05'}) or {}
    check('Give a day builds the JEE paper privately for that day', r.status_code == 200 and s.get('series_import') and s.get('status') == 'published' and len(s.get('questions', [])) == 75 and 'series_pattern' not in s and live_series.valid_paper(s), (r.status_code, r.text[:200], s.get('status')))
    w = live_series.window('2026-12-05'); check('it keeps the JEE times 12:01 AM / 8:59 PM / 11:59 PM', s.get('series_window') == w and s.get('start_at') == w['opens_at'] and s.get('end_at') == w['closes_at'], s.get('series_window'))
    r = await own.post(f'{M}/series/{S}/fill'); await drain(); s2 = await SETS.find_one({'series_id': S, 'series_date': '2026-12-01'}) or {}
    check('Fill days in order puts the next paper on the first free day (1 Dec)', r.status_code == 200 and J(r).get('placed') == 1 and len(s2.get('questions', [])) == 75, (r.status_code, r.text[:200]))
    v = J(await own.get(f'{M}/series/{S}')); got = {x['date']: x['paper']['title'] for x in v['slots'] if x['paper']}; check('Master day list shows both days', set(got) == {'2026-12-01', '2026-12-05'}, got)
    old = J(await own.get('/api/studio/all-india-jee')); check('the older series endpoint agrees', {x['date'] for x in old.get('slots', []) if x.get('set_id')} == {'2026-12-01', '2026-12-05'}, [x['date'] for x in old.get('slots', []) if x.get('set_id')])
    pub = J(await anon.get('/api/series/all-india-jee')); d5 = next(x for x in pub['slots'] if x['date'] == '2026-12-05')
    check('students do not see the paper before its day', d5['set_id'] is None and d5['ready'] is False and 'AITS1' not in str(pub), d5)
    r = await start(stu, s.get('id', 'x')); check('student cannot start it before its day', r.status_code in (404, 409), r.status_code)
    r = await own.post(f'{M}/series/{S}/unassign', json={'kind': 'set', 'id': s.get('id', 'x')}); back = [c for c in J(await own.get(f'{M}/series/{S}'))['candidates'] if c['id'] == s.get('id')]
    check('free a future day: paper returns to the list, stays hidden', r.status_code == 200 and len(back) == 1 and back[0]['kind'] == 'set' and not back[0]['problem'], (r.status_code, back))
    r = await start(stu, s.get('id', 'x')); check('paper without a day is not startable', r.status_code in (404, 409), r.status_code)
    r = await own.post(f'{M}/series/{S}/assign', json={'kind': 'set', 'id': s.get('id', 'x'), 'date': '2026-12-10'}); s3 = await SETS.find_one({'id': s.get('id')}) or {}
    check('built paper takes a new day', r.status_code == 200 and s3.get('series_date') == '2026-12-10' and s3.get('series_id') == S and s3.get('start_at') == live_series.window('2026-12-10')['opens_at'], (r.status_code, r.text[:200]))
    r = await own.post(f'{M}/series/{S}/assign', json={'kind': 'set', 'id': s.get('id', 'x'), 'date': '2026-11-30'}); check('day outside 1 Dec - 31 Jan refused 422', r.status_code == 422, r.status_code)
    r = await own.post(f'{M}/series/{S}/clear'); n = await SETS.count_documents({'series_id': S}); check('Free all future days', r.status_code == 200 and n == 0, (r.text[:150], n))
    check('no AI calls in whole run', H.AI_CALLS == {'ask': 0, 'solve': 0}, H.AI_CALLS)


async def run():
    assert not H.leftover_real_handles()
    await H.tdbmod.indexes(); await structure.seed()
    try: await main()
    except Exception:
        import traceback; traceback.print_exc(); check('suite ran to the end', False, 'exception above')
    finally:
        await H.tdbmod.client.drop_database(H.TEST_DB)
        ok = sum(1 for r in RESULTS if r[1]); print(f'TOTAL {len(RESULTS)} PASS {ok} FAIL {len(RESULTS) - ok}'); print('dropped', H.TEST_DB)

if __name__ == '__main__':
    asyncio.run(run())
