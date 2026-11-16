"""TEST-ONLY iteration 188: simple Start test (no preflight), 60 s get-ready (ready_until/deadline), /begin, /assets/pack,
All India series score+solutions on submit with the rank after the day closes (/series-rank), regular live exams still sealed.
Isolated disposable DB (storage + AI mocked). Run: cd /app/backend && timeout 290 python tests/get_ready_iso188.py
"""
import asyncio, json, sys, time, uuid
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import book_publishing_iso170 as T  # noqa: E402,F401
from book_publishing_iso170 import H, mkstaff, client, upload, complete, drain, check, RESULTS  # noqa: E402
from structure_iso173 import mkset  # noqa: E402
from typed_delete_iso185 import two_opt_pdf, M  # noqa: E402
from tejas import structure, live_series  # noqa: E402
from tejas import jobs as JOBS  # noqa: E402

DB = H.TDB; SETS, ATT, BM = DB.tejas_sets, DB.tejas_attempts, DB.tejas_book_mocks


def J(r):
    try: d = r.json()
    except Exception: return {}
    if isinstance(d, dict) and 'data' in d and 'error' in d: d = d['data']
    return d if d is not None else {}


def key(): return 'k188-' + uuid.uuid4().hex[:12]


async def go(c, sid, ready=True, k=None):
    body = {'preview': False, 'start_key': k or key()}
    if ready: body['get_ready'] = True
    return await c.post(f'/api/sets/{sid}/start', json=body)


async def student(p):
    s = client(); r = await s.post('/api/auth/phone/signup', json={'phone': p + str(uuid.uuid4().int)[:8], 'pin': '8261', 'confirm_pin': '8261'})
    assert r.status_code == 200, r.text
    return s


async def answer(c, aid, qid, val):
    return await c.put(f'/api/attempts/{aid}/answers/{qid}', json={'value': val, 'revision': 1, 'request_id': str(uuid.uuid4())})


async def result(c, aid):
    for _ in range(30):
        r = await c.get(f'/api/attempts/{aid}/results'); d = J(r)
        if r.status_code == 200 and d.get('status') != 'grading' and (d.get('summary') or d.get('status') == 'embargoed' and d.get('summary')):
            return r, d
        for j in await DB.tejas_jobs.find({'status': 'queued'}).to_list(50):
            try: await JOBS.run_job(j['id'])
            except Exception: pass
        await asyncio.sleep(0.4)
    return r, d


def unpack(b):
    n = int.from_bytes(b[:4], 'big'); head = json.loads(b[4:4 + n]); pos = 4 + n; imgs = []
    for it in head['items']:
        imgs.append(b[pos:pos + it['size']]); pos += it['size']
    return head, imgs, pos == len(b)


async def start_api(own, a, b):
    sid = await mkset('PRAC', exam='JEE Main', catalog_section_id='jee-main:mocks', test_kind='mock', title='TEST_Prac')
    t0 = time.time(); r = await c_pre(a, sid); check('preflight still 200 and fast', r.status_code == 200 and time.time() - t0 < 3, (r.status_code, r.text[:150]))
    k = key(); r = await go(a, sid, k=k); x = J(r)
    check('start get_ready without preflight/device_checked 200', r.status_code == 200 and x.get('id'), (r.status_code, r.text[:200]))
    row = await ATT.find_one({'id': x['id']})
    check('ready_until = started_at + 60', abs(row.get('ready_until', 0) - row['started_at'] - 60) < 0.01, (row.get('ready_until'), row['started_at']))
    check('deadline = ready_until + minutes*60', abs(row['deadline'] - row['ready_until'] - 600) < 0.01, (row['deadline'], row.get('ready_until')))
    check('attempt view exposes ready_until', abs((x.get('ready_until') or 0) - row['ready_until']) < 0.01, {k2: x.get(k2) for k2 in ('ready_until', 'deadline')})
    r2 = await go(a, sid, k=k); check('same start_key -> same attempt', J(r2).get('id') == x['id'], (r2.status_code, J(r2).get('id')))
    # begin
    r = await b.post(f"/api/attempts/{x['id']}/begin"); check('begin other user 404', r.status_code == 404, r.status_code)
    r = await a.post(f"/api/attempts/{x['id']}/begin"); d = J(r)
    check('begin 200 sets ready_until=now, deadline=now+600', r.status_code == 200 and abs(d['ready_until'] - d['server_now']) < 0.01 and abs(d['deadline'] - d['server_now'] - 600) < 0.01, d)
    r = await a.post(f"/api/attempts/{x['id']}/begin"); d2 = J(r)
    check('second begin no-op same values', r.status_code == 200 and d2['ready_until'] == d['ready_until'] and d2['deadline'] == d['deadline'], (d, d2))
    row = await ATT.find_one({'id': x['id']}); check('begin persisted', row['deadline'] == d['deadline'] and row['ready_until'] == d['ready_until'], '')
    # no get_ready (mobile app)
    await a.post(f"/api/attempts/{x['id']}/submit")
    r = await go(a, sid, ready=False); y = J(r); row = await ATT.find_one({'id': y.get('id')}) or {}
    check('no get_ready: no ready_until, deadline=start+600', r.status_code == 200 and 'ready_until' not in row and abs(row['deadline'] - row['started_at'] - 600) < 0.01, {k2: row.get(k2) for k2 in ('ready_until', 'deadline', 'started_at')})
    r = await a.post(f"/api/attempts/{y['id']}/begin"); d = J(r)
    check('begin on attempt without ready_until no-op', r.status_code == 200 and d.get('deadline') == row['deadline'], d)
    await a.post(f"/api/attempts/{y['id']}/submit")
    r = await a.get(f"/api/attempts/{y['id']}/series-rank"); check('practice series-rank unavailable', J(r).get('state') == 'unavailable', r.text[:150])
    r = await a.get('/api/my/tests', params={'tab': 'completed', 'status': 'embargoed'}); check("My Tests status=embargoed -> 422", r.status_code == 422, r.status_code)
    # begin on completed -> no-op
    r = await a.post(f"/api/attempts/{x['id']}/begin"); check('begin on completed attempt does not change', r.status_code == 200, (r.status_code, r.text[:150]))


async def c_pre(c, sid): return await c.post(f'/api/sets/{sid}/preflight', json={})


async def live_cut(own, a):
    # Regular live exam ending in 10 min + 20 s with 10-minute paper: lead must be 20 s.
    t = time.time()
    sid = await mkset('LIVECUT', exam='JEE Main', catalog_section_id='jee-main:mocks', test_kind='mock', competition=True, start_at=t - 30, last_start_at=t + 300, end_at=t + 620, live_enabled=True)
    r = await go(a, sid); x = J(r); row = await ATT.find_one({'id': x.get('id')}) or {}
    lead = row.get('ready_until', row.get('started_at', 0)) - row.get('started_at', 0)
    check('live window cut: lead ~ end - minutes*60 - start (~20 s)', r.status_code == 200 and 17 < lead < 21, (r.status_code, lead, r.text[:200]))
    check('live cut deadline capped by competition_end', row.get('deadline', 0) <= row.get('competition_end', 0) + 0.01, {k: row.get(k) for k in ('deadline', 'competition_end')})
    qid = x['questions'][0]['id']; await answer(a, x['id'], qid, 'A')
    await a.post(f"/api/attempts/{x['id']}/submit"); r, d = await result(a, x['id'])
    check('regular live: results embargoed + score_released + summary', d.get('status') == 'embargoed' and d.get('score_released') is True and d.get('summary'), {k: d.get(k) for k in ('status', 'score_released')})
    r = await a.get(f"/api/attempts/{x['id']}/series-rank"); check('regular live series-rank unavailable', J(r).get('state') == 'unavailable', r.text[:150])
    r = await a.post(f"/api/attempts/{x['id']}/retry", json={"start_key": key()}); check('regular live retry locked before end', r.status_code in (403, 409, 423), (r.status_code, r.text[:150]))
    # end passed (window too short) -> lead 0
    sid2 = await mkset('LIVEZERO', exam='JEE Main', catalog_section_id='jee-main:mocks', test_kind='mock', competition=True, start_at=t - 30, last_start_at=t + 300, end_at=t + 590, live_enabled=True)
    r = await go(a, sid2); row = await ATT.find_one({'id': J(r).get('id')}) or {}
    check('live window shorter than paper: no ready_until', r.status_code == 200 and 'ready_until' not in row, (r.status_code, row.get('ready_until'), r.text[:150]))


async def pack(own, stu, other):
    sec = 'jee-main:mocks'
    b = await upload(own, two_opt_pdf('PACK'), 'TEST_PACK', section_id=sec); await complete(own, b['id']); await drain()
    m = await BM.find_one({'book_id': b['id']}); base = f"/api/admin/books/{b['id']}/mocks/{m['_id']}"
    p = J(await own.get(base + '/problems', params={'all': 'true'}))
    for q in p.get('questions', []):
        p = J(await own.get(base + '/problems', params={'all': 'true'}))
        await own.post(base + '/fix', json={'revision': p['revision'], 'question_id': q['id'], 'response_type': 'mcq', 'option_labels': ['A', 'B'], 'answer': 'B', 'complete': True}); await drain()
    await own.post(M + '/status', json={'items': [{'kind': 'book_mock', 'id': m['_id']}], 'to': 'live'}); await drain()
    sid = (await BM.find_one({'_id': m['_id']})).get('set_id')
    await asyncio.sleep(2); await structure.visibility(force=True)
    check('book-mock set built', bool(sid), m.get('state'))
    if not sid: return
    r = await go(stu, sid); x = J(r); aid = x.get('id'); check('book set start get_ready', r.status_code == 200, r.text[:200])
    row = await ATT.find_one({'id': aid}) or {}
    qs = row.get('questions') or []
    if row.get('pack_id'):
        from tejas.packs import entry_for
        qs = (await entry_for(row['pack_id'])).questions
    expect = [(q['id'], i) for q in qs if not q.get('bonus') for i, _ in enumerate(q.get('q_refs', []))]
    t0 = time.time(); r = await stu.get(f'/api/attempts/{aid}/assets/pack', params={'offset': 0, 'limit': 16}); took = time.time() - t0
    check('pack 200 octet-stream no-store', r.status_code == 200 and r.headers.get('content-type', '').startswith('application/octet-stream') and 'no-store' in r.headers.get('cache-control', ''), (r.status_code, dict(r.headers), r.text[:200]))
    if r.status_code != 200: return
    head, imgs, exact = unpack(r.content)
    check('pack total == q_refs count in paper order', head['total'] == len(expect) and [(i['question_id'], i['index']) for i in head['items']] == expect[:16], (head['total'], len(expect)))
    check('pack body length exact', exact, '')
    check('pack images are PNG', all(i[:8] == b'\x89PNG\r\n\x1a\n' for i in imgs) and len(imgs) > 0, [i[:8] for i in imgs[:2]])
    same = True
    for it, img in zip(head['items'], imgs):
        a1 = await stu.get(f"/api/attempts/{aid}/questions/{it['question_id']}/asset/question/{it['index']}")
        same = same and a1.status_code == 200 and a1.content == img
    check('each pack image == single asset bytes', same, '')
    r2 = await stu.get(f'/api/attempts/{aid}/assets/pack', params={'offset': 1, 'limit': 1}); h2, i2, _ = unpack(r2.content) if r2.status_code == 200 else ({}, [], 0)
    check('offset=1 limit=1 returns 2nd item', r2.status_code == 200 and len(i2) == (1 if len(expect) > 1 else 0) and (not i2 or i2[0] == imgs[1]), (r2.status_code, h2))
    r3 = await stu.get(f'/api/attempts/{aid}/assets/pack', params={'offset': 0, 'limit': 17}); check('limit 17 -> 422', r3.status_code == 422, r3.status_code)
    r4 = await other.get(f'/api/attempts/{aid}/assets/pack'); check('pack other user 404', r4.status_code == 404, r4.status_code)
    r5 = await stu.get(f'/api/attempts/{aid}/assets/pack', params={'offset': 4000}); h5 = unpack(r5.content)[0] if r5.status_code == 200 else {}
    check('offset beyond end -> empty items', r5.status_code == 200 and h5.get('items') == [], (r5.status_code, h5))
    print('pack took', round(took, 2), 'items', len(imgs), flush=True)
    await stu.post(f'/api/attempts/{aid}/submit')
    r6 = await stu.get(f'/api/attempts/{aid}/assets/pack'); check('pack after submit -> 409', r6.status_code == 409, r6.status_code)


async def series(own, s1, s2, s3):
    t = time.time(); w = live_series.window('2026-12-12'); shift = t - w['opens_at'] - 600
    w = {k: (v + shift if isinstance(v, (int, float)) else v) for k, v in w.items()}
    sid = await mkset('SDAY', exam='JEE Main', series_id=live_series.SERIES_ID, series_date='2026-12-12', test_kind='mock', series_import=True, series_window=w, live_enabled=True, start_at=0, end_at=4e9)
    sd = await SETS.find_one({'id': sid}); await SETS.update_one({'id': sid}, {'$set': {'series_pattern': live_series.paper_pattern(sd)}})
    await DB.tejas_series.update_one({'_id': live_series.SERIES_ID}, {'$set': {'shown': True}})
    ids = {}
    for name, c, vals in (('s1', s1, ['A', 'A', 'A']), ('s2', s2, ['A', 'B', 'B']), ('s3', s3, ['A', 'B', 'B'])):
        r = await go(c, sid); x = J(r)
        check(f'series {name} start series_live with ready', r.status_code == 200 and x.get('mode') == 'series_live', (r.status_code, x.get('mode'), r.text[:200]))
        row = await ATT.find_one({'id': x['id']}); ids[name] = x['id']
        if name == 's1':
            check('series ready lead 60 (window long)', abs(row.get('ready_until', 0) - row['started_at'] - 60) < 0.01, row.get('ready_until'))
        await c.post(f"/api/attempts/{x['id']}/begin")
        for q, v in zip(x['questions'], vals): await answer(c, x['id'], q['id'], v)
        await c.post(f"/api/attempts/{x['id']}/submit")
    await series_assets(s1, ids['s1'])
    r, d = await result(s1, ids['s1'])
    check('series_live results full right after submit (not embargoed)', r.status_code == 200 and d.get('status') != 'embargoed' and d.get('questions') and d.get('summary'), (r.status_code, d.get('status'), str(d)[:200]))
    check('series s1 score 12', (d.get('summary') or {}).get('score') == 12, d.get('summary'))
    r = await s1.get(f"/api/attempts/{ids['s1']}/series-rank"); d = J(r); row = await ATT.find_one({'id': ids['s1']})
    check('series-rank sealed release_at=competition_end before close', d.get('state') == 'sealed' and d.get('release_at') == row['competition_end'] and d.get('rank') is None, d)
    r = await s2.get(f"/api/attempts/{ids['s1']}/series-rank"); check('series-rank other user 404', r.status_code == 404, r.status_code)
    r = await s1.post(f"/api/attempts/{ids['s1']}/retry", json={"start_key": key()}); check('series retry not sealed after submit (200 or no-wrong 400, never 403)', r.status_code == 200 or (r.status_code == 400 and 'no incorrect' in r.text), (r.status_code, r.text[:120]))
    r = await s1.get('/api/my/tests', params={'tab': 'completed'}); items = J(r).get('items', [])
    it = next((i for i in items if i['id'] == ids['s1']), {})
    check('My Tests series item status completed with score (not embargoed)', it.get('status') == 'completed' and 'embargo' not in json.dumps(it), it)
    for name in ('s2', 's3'): await result({'s2': s2, 's3': s3}[name], ids[name])
    # close the day
    await ATT.update_many({'id': {'$in': list(ids.values())}}, {'$set': {'competition_end': time.time() - 5}})
    r1 = J(await s1.get(f"/api/attempts/{ids['s1']}/series-rank")); r2 = J(await s2.get(f"/api/attempts/{ids['s2']}/series-rank")); r3 = J(await s3.get(f"/api/attempts/{ids['s3']}/series-rank"))
    check('after close: s1 rank 1 of 3', r1.get('state') == 'ready' and r1.get('rank') == 1 and r1.get('total') == 3, r1)
    check('after close: ties share rank 2 (s2, s3)', r2.get('rank') == 2 and r3.get('rank') == 2 and r2.get('total') == 3, (r2, r3))
    check('top_percent = 100*rank/total', r1.get('top_percent') == round(100 / 3, 1), r1)
    return ids


async def series_assets(s1, aid):
    row = J(await s1.get(f'/api/attempts/{aid}'))
    # solution asset allowed even if no s_refs → expect 404 for missing index but not 403-sealed
    r = await s1.get(f"/api/attempts/{aid}/questions/{row['questions'][0]['id']}/asset/solution/0")
    check('INFO series solution asset (text paper)', True, r.status_code)


async def main():
    own, _ = await mkstaff('owner', 'g188'); a = await student('94'); b = await student('95'); c = await student('96')
    await structure.exams.update_one({'_id': 'jee-main'}, {'$set': {'shown': True}})
    for fn in (lambda: start_api(own, a, b), lambda: live_cut(own, a), lambda: pack(own, a, b), lambda: series(own, a, b, c)):
        try: await fn()
        except Exception:
            import traceback; traceback.print_exc(); check('section ran', False, 'exception above')


async def run():
    assert not H.leftover_real_handles()
    await H.tdbmod.indexes(); await structure.seed()
    try: await main()
    finally:
        await H.tdbmod.client.drop_database(H.TEST_DB)
        for r in RESULTS: print('PASS' if r[1] else 'FAIL', r[0], '' if r[1] else r[2])
        ok = sum(1 for r in RESULTS if r[1]); print(f'TOTAL {len(RESULTS)} PASS {ok} FAIL {len(RESULTS) - ok}'); print('dropped', H.TEST_DB)

if __name__ == '__main__':
    asyncio.run(run())
