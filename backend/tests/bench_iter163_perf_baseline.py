"""TEST-ONLY iteration 163 PERFORMANCE BASELINE (no app changes). Re-run unchanged AFTER fixes for exact comparison.
Isolated disposable DB (dropped before/after), synthetic random owner + PIN student generated at runtime, real auth.
In-process ASGI (httpx ASGITransport): numbers are SERVER-SIDE app time on this preview pod, no internet RTT.
Source bytes = ORIGINAL LOCAL PDFs from disk (not object-storage network latency; real storage adds per-GET RTT+transfer).
Run (foreground):
  cd /app/backend/tests && python -m pytest bench_iter163_perf_baseline.py -p no:cacheprovider -q -n0 -s
Output: /app/test_reports/iter163_perf_baseline.json   (set PERF_OUT to write elsewhere for the AFTER run)
"""
import asyncio, json, os, secrets, statistics, time, uuid
from pathlib import Path
import httpx, pytest
import iso_harness_perf163 as H
from tejas import auth

LOOP = asyncio.new_event_loop()
asyncio.set_event_loop(LOOP)
run = LOOP.run_until_complete
TDB = H.TDB
OWNER_PW = 'P163-' + secrets.token_urlsafe(14)
OWNER = {'id': str(uuid.uuid4()), 'email': 'perf163-owner@example.com', 'role': 'owner'}
OUT = Path(os.environ.get('PERF_OUT', '/app/test_reports/iter163_perf_baseline.json'))
REPEATS = 7
R = {'methodology': {
    'scope': 'ISOLATED preview pod, in-process ASGI, synthetic users; NOT customer DB; NOT live; NOT global user speed',
    'storage': 'LOCAL DISK original PDFs via patched tejas_storage.request; real get_object 32MB source cache kept',
    'cold': 'process caches cleared (source/crop/derivative/validation/pack); Mongo WiredTiger cache NOT cleared',
    'repeats': REPEATS}, 'steps': {}}


def client(peer=('127.0.0.1', 123)):
    return httpx.AsyncClient(transport=httpx.ASGITransport(app=H.app, raise_app_exceptions=False, client=peer),
                             base_url='https://api.test.example', headers={'Origin': H.ORIGIN}, timeout=600)


def J(r):
    j = r.json()
    return j.get('data') if isinstance(j, dict) and 'data' in j and 'meta' in j else j


async def timed(c, method, url, **kw):
    a = H.snap(); t = time.perf_counter()
    r = await c.request(method, url, **kw)
    ms = (time.perf_counter() - t) * 1000
    return r, {'ms': round(ms, 1), 'status': r.status_code, 'bytes': len(r.content), **H.diff(a, H.snap())}


def pct(xs, p):
    xs = sorted(xs)
    return round(xs[min(len(xs) - 1, int(round(p / 100 * (len(xs) - 1))))], 1)


async def series(c, name, method, url, n=REPEATS, **kw):
    """first call recorded separately (cold-ish), then n warm repeats -> p50/p95 + per-call counters."""
    rows = []
    for _ in range(n):
        r, m = await timed(c, method, url, **kw)
        rows.append(m)
    ms = [x['ms'] for x in rows]
    R['steps'][name] = {'n': n, 'p50_ms': pct(ms, 50), 'p95_ms': pct(ms, 95), 'max_ms': max(ms),
                        'status': sorted({x['status'] for x in rows}), 'bytes': rows[-1]['bytes'],
                        'db_cmds_per_call': rows[-1].get('db_cmds', 0), 'db_by_cmd': rows[-1].get('db_by_cmd', {}),
                        'other_counters_last_call': {k: v for k, v in rows[-1].items() if k not in ('ms', 'status', 'bytes', 'db_cmds', 'db_by_cmd')}}
    return r


def one(name, m):
    R['steps'][name] = m
    print(name, json.dumps(m))


@pytest.fixture(scope='module', autouse=True)
def isolated():
    assert H.TEST_DB != H.REAL_DB and not H.leftover_real_handles() and not H.app.dependency_overrides
    run(H.MCLIENT.drop_database(H.TEST_DB))
    run(H.tdbmod.indexes())
    run(TDB.tejas_users.insert_one({**OWNER, 'name': 'TEST perf owner', 'exam': 'JEE Main', 'access_type': 'staff_password',
                                    'password_hash': auth.hashpw(OWNER_PW), 'created_at': 0}))
    yield
    run(H.MCLIENT.drop_database(H.TEST_DB))
    assert H.TEST_DB not in run(H.MCLIENT.list_database_names())
    R['cleanup'] = {'db_dropped': True, 'storage_puts': list(H.PUTS), 'real_handles_left': H.leftover_real_handles()}
    OUT.write_text(json.dumps(R, indent=1, default=str))
    print('WROTE', OUT)


async def import_pyq():
    async with client() as o:
        assert (await o.post('/api/auth/login', json={'email': OWNER['email'], 'password': OWNER_PW})).status_code == 200
        t = time.perf_counter(); a = H.snap(); v = {}; steps = 0
        for _ in range(200):
            v = J(await o.post('/api/studio/pyq-import/step', json={})); steps += 1
            if v.get('phase') == 'complete':
                break
        assert v.get('phase') == 'complete', v
        one('setup_pyq_import_local', {'s': round(time.perf_counter() - t, 1), 'steps': steps, **H.diff(a, H.snap())})


async def pick_papers():
    sets = await TDB.tejas_sets.find({'test_kind': 'pyq'}, {'_id': 0, 'id': 1, 'title': 1, 'pyq_date': 1, 'file_ids': 1, 'questions.q_refs': 1, 'questions.s_refs': 1}).to_list(500)
    info = []
    for s in sets:
        size = 0
        for fid in s.get('file_ids', []):
            f = await TDB.tejas_files.find_one({'id': fid}, {'_id': 0, 'path': 1})
            size += H.PATHS[f['path']].stat().st_size
        refs = {json.dumps(r, sort_keys=True) for q in s['questions'] for k in ('q_refs', 's_refs') for r in q.get(k, [])}
        qrefs = sum(len(q.get('q_refs', [])) for q in s['questions'])
        info.append({'id': s['id'], 'title': s['title'], 'date': s.get('pyq_date'), 'pdf_bytes': size, 'files': len(s.get('file_ids', [])),
                     'questions': len(s['questions']), 'question_crops': qrefs, 'unique_refs_all': len(refs)})
    jan = max((x for x in info if str(x['date'])[5:7] == '01'), key=lambda x: x['pdf_bytes'])
    apr = max((x for x in info if str(x['date'])[5:7] == '04'), key=lambda x: x['pdf_bytes'])
    R['papers'] = {'january': jan, 'april': apr, 'all_count': len(info),
                   'pdf_bytes_range': [min(x['pdf_bytes'] for x in info), max(x['pdf_bytes'] for x in info)]}
    return jan, apr


async def results_poll(c, aid):
    t = time.perf_counter(); polls = []
    for _ in range(120):
        r, m = await timed(c, 'GET', f'/api/attempts/{aid}/results')
        polls.append(m)
        if r.status_code == 200:
            break
        assert r.status_code == 202, r.text
        await asyncio.sleep(0.3)
    return r, {'total_ms': round((time.perf_counter() - t) * 1000, 1), 'polls': len(polls),
               'codes': [p['status'] for p in polls], 'final': polls[-1]}


async def paper_flow(label, paper, phone, p):
    pid = paper['id']
    async with client(('10.81.5.%d' % (11 if label == 'january' else 12), 1)) as c:
        assert (await c.post('/api/auth/phone', json={'phone': phone, 'pin': p})).status_code == 200
        H.reset_process_caches()
        _, m = await timed(c, 'GET', f'/api/my/sets/{pid}'); one(f'{label}.my_set_detail_cold', m)
        r, m = await timed(c, 'POST', f'/api/sets/{pid}/preflight', json={'test_response': 'ok'}); one(f'{label}.preflight_cold', m)
        assert r.status_code == 200, r.text
        await series(c, f'{label}.preflight_warm', 'POST', f'/api/sets/{pid}/preflight', n=3, json={'test_response': 'ok'})
        r, m = await timed(c, 'POST', f'/api/sets/{pid}/start', json={'start_key': 'P163_' + uuid.uuid4().hex, 'device_checked': True})
        one(f'{label}.start', m); assert r.status_code == 200, r.text
        a = J(r); aid = a['id']; qs = a['questions']
        # Player mounts and re-fetches the same attempt (duplicate of start payload)
        _, m = await timed(c, 'GET', f'/api/attempts/{aid}'); one(f'{label}.player_refetch_attempt', m)
        # first image AFTER preflight (preflight validated low-res only)
        _, m = await timed(c, 'GET', f'/api/attempts/{aid}/questions/{qs[0]["id"]}/asset/question/0?v=0'); one(f'{label}.first_image_after_preflight', m)
        _, m = await timed(c, 'GET', f'/api/attempts/{aid}/questions/{qs[1]["id"]}/asset/question/0?v=0'); one(f'{label}.second_image', m)
        # all remaining question images sequentially (student navigating)
        a0 = H.snap(); t = time.perf_counter(); per = []; nbytes = 0
        for q in qs[2:]:
            for i in range(q.get('asset_count', 0)):
                _, m = await timed(c, 'GET', f'/api/attempts/{aid}/questions/{q["id"]}/asset/question/{i}?v=0'); per.append(m['ms']); nbytes += m['bytes']
        one(f'{label}.remaining_images_sequential', {'images': len(per), 'total_s': round(time.perf_counter() - t, 2), 'png_bytes_total': nbytes,
            'p50_ms': pct(per, 50), 'p95_ms': pct(per, 95), 'max_ms': max(per), **H.diff(a0, H.snap())})
        await series(c, f'{label}.image_warm_repeat', 'GET', f'/api/attempts/{aid}/questions/{qs[0]["id"]}/asset/question/0?v=0', n=5)
        await series(c, f'{label}.read_attempt_warm', 'GET', f'/api/attempts/{aid}', n=5)
        await series(c, f'{label}.status_poll', 'GET', f'/api/attempts/{aid}/status', n=5)
        saves = []
        for k, q in enumerate(qs[:5]):
            val = 'A' if q.get('type', 'mcq') != 'numeric' else '1'
            r, m = await timed(c, 'PUT', f'/api/attempts/{aid}/answers/{q["id"]}', json={'value': val, 'revision': 1, 'request_id': 'P163R_' + uuid.uuid4().hex})
            saves.append(m)
        ok = [s['ms'] for s in saves if s['status'] == 200]
        one(f'{label}.save_answer', {'n': len(saves), 'statuses': [s['status'] for s in saves], 'p50_ms': pct(ok or [0], 50),
                                     'p95_ms': pct(ok or [0], 95), 'db_cmds_per_call': saves[-1].get('db_cmds'), 'db_by_cmd': saves[-1].get('db_by_cmd')})
        r, m = await timed(c, 'POST', f'/api/attempts/{aid}/submit'); one(f'{label}.submit', m)
        assert r.status_code in (200, 202), r.text
        r, m = await results_poll(c, aid); one(f'{label}.results_until_ready', m)
        res = J(r)
        await series(c, f'{label}.results_warm', 'GET', f'/api/attempts/{aid}/results', n=5)
        qsol = next(q for q in res['questions'] if q.get('solution_asset_count'))
        _, m = await timed(c, 'GET', f'/api/attempts/{aid}/questions/{qsol["id"]}/asset/solution/0?v=0'); one(f'{label}.original_solution_image_first', m)
        _, m = await timed(c, 'GET', f'/api/attempts/{aid}/questions/{qsol["id"]}/asset/solution/0?v=0'); one(f'{label}.original_solution_image_repeat', m)
        # True COLD image: fresh process caches, no preflight warm (fresh pod / evicted)
        H.reset_process_caches()
        _, m = await timed(c, 'GET', f'/api/attempts/{aid}/questions/{qs[3]["id"]}/asset/question/0?v=0'); one(f'{label}.image_cold_after_cache_reset', m)
        _, m = await timed(c, 'GET', f'/api/attempts/{aid}/questions/{qs[4]["id"]}/asset/question/0?v=0'); one(f'{label}.image_next_distinct_source_cached', m)
        return aid, qs


async def explain_all(student_id, set_id, aid):
    from tejas.catalog import available
    u = await TDB.tejas_users.find_one({'id': student_id}, {'_id': 0})
    match = {**available(u, 'JEE Main'), 'test_kind': 'pyq', 'qa_only': {'$ne': True}, 'is_deleted': {'$ne': True}}
    qs = {
        'pyq_catalogue': ('tejas_sets', match, [('pyq_date', -1), ('pyq_shift', 1), ('id', 1)]),
        'public_catalogue_home': ('tejas_sets', {**available(None, ''), }, [('created_at', -1), ('id', 1)]),
        'set_by_id': ('tejas_sets', {'id': set_id}, None),
        'attempt_owned': ('tejas_attempts', {'id': aid, 'user_id': student_id}, None),
        'attempts_recent_by_user': ('tejas_attempts', {'user_id': student_id}, [('started_at', -1)]),
        'attempts_user_set_state': ('tejas_attempts', {'user_id': student_id, 'set_id': {'$in': [set_id]}, 'mode': {'$nin': ['preview', 'retry']}}, [('started_at', -1), ('id', -1)]),
        'start_key_lookup': ('tejas_attempts', {'user_id': student_id, '$or': [{'start_key': 'x'}, {'start_request_keys': 'x'}]}, None),
        'files_by_id': ('tejas_files', {'id': 'x'}, None),
        'preflight_upsert_key': ('tejas_preflight', {'user_id': student_id, 'set_id': set_id}, None),
    }
    out = {}
    for name, (coll, filt, sort) in qs.items():
        try:
            cur = TDB[coll].find(filt)
            if sort:
                cur = cur.sort(sort)
            e = await cur.explain()
            plan = e['queryPlanner']['winningPlan']; stages = []
            def walk(p):
                stages.append(p.get('stage') + (':' + str(p.get('keyPattern')) if p.get('keyPattern') else ''))
                for k in ('inputStage',):
                    if k in p: walk(p[k])
                for x in p.get('inputStages', []): walk(x)
            walk(plan.get('queryPlan', plan))
            ex = e.get('executionStats', {})
            out[name] = {'stages': stages, 'COLLSCAN': any(s.startswith('COLLSCAN') for s in stages),
                         'docsExamined': ex.get('totalDocsExamined'), 'keysExamined': ex.get('totalKeysExamined'), 'nReturned': ex.get('nReturned')}
        except Exception as ex:
            out[name] = {'error': str(ex)[:200]}
    stats = {}
    for coll in ('tejas_sets', 'tejas_attempts', 'tejas_packs', 'tejas_files', 'tejas_users', 'tejas_sessions'):
        try:
            s = await TDB.command('collStats', coll)
            stats[coll] = {'count': s.get('count'), 'avgObjSize': s.get('avgObjSize'), 'size': s.get('size'), 'nindexes': s.get('nindexes'),
                           'indexes': sorted((await TDB[coll].index_information()).keys())}
        except Exception as ex:
            stats[coll] = {'error': str(ex)[:120]}
    R['mongo_explain'] = out; R['collection_stats'] = stats


def test_perf_baseline():
    async def go():
        R['rss_mb_start'] = H.rss_mb()
        await import_pyq()
        jan, apr = await pick_papers()
        phone, p = f'99163{secrets.randbelow(10**5):05d}', f'{secrets.randbelow(10000):04d}'
        async with client(('10.81.5.10', 1)) as c:
            r, m = await timed(c, 'POST', '/api/auth/phone/signup', json={'phone': phone, 'pin': p, 'confirm_pin': p}); one('auth.signup', m)
            assert r.status_code == 200, r.text
            sid = J(r)['id']
            H.reset_process_caches()
            _, m = await timed(c, 'GET', '/api/health'); one('health_first', m)
            for name, url in [('home.sets', '/api/sets'), ('home.series', '/api/series/all-india-jee'), ('home.auth_me', '/api/auth/me'),
                              ('pyq.catalogue', '/api/pyq/jee-main'), ('home.my_sets', '/api/my/sets'), ('history.attempts', '/api/attempts')]:
                _, m = await timed(c, 'GET', url); one(name + '_first', m)
                await series(c, name + '_warm', 'GET', url)
        async with client() as g:
            for name, url in [('guest.sets', '/api/sets'), ('guest.series', '/api/series/all-india-jee')]:
                await series(g, name + '_warm', 'GET', url)
        ja, jq = await paper_flow('january', jan, phone, p)
        R['rss_mb_after_january'] = H.rss_mb()
        aa, aq = await paper_flow('april', apr, phone, p)
        R['rss_mb_after_april'] = H.rss_mb()
        # modest concurrency 10: cold distinct images on january attempt after cache reset; warm catalogue reads
        async with client(('10.81.5.11', 1)) as c:
            assert (await c.post('/api/auth/phone', json={'phone': phone, 'pin': p})).status_code == 200
            H.reset_process_caches()
            urls = [f'/api/attempts/{ja}/questions/{q["id"]}/asset/question/0?v=1' for q in jq[5:15]]
            a0 = H.snap(); t = time.perf_counter()
            rs = await asyncio.gather(*[timed(c, 'GET', u) for u in urls])
            one('concurrency10.cold_distinct_images', {'wall_ms': round((time.perf_counter() - t) * 1000, 1), 'statuses': sorted(x[1]['status'] for x in rs),
                'p50_ms': pct([x[1]['ms'] for x in rs], 50), 'max_ms': max(x[1]['ms'] for x in rs), **H.diff(a0, H.snap())})
            t = time.perf_counter()
            rs = await asyncio.gather(*[timed(c, 'GET', '/api/pyq/jee-main') for _ in range(10)])
            one('concurrency10.pyq_catalogue_warm', {'wall_ms': round((time.perf_counter() - t) * 1000, 1), 'statuses': sorted({x[1]['status'] for x in rs}),
                'p50_ms': pct([x[1]['ms'] for x in rs], 50), 'max_ms': max(x[1]['ms'] for x in rs)})
            t = time.perf_counter()
            rs = await asyncio.gather(*[timed(c, 'POST', f'/api/sets/{jan["id"]}/preflight', json={'test_response': 'ok'}) for _ in range(10)])
            one('concurrency10.preflight_warm', {'wall_ms': round((time.perf_counter() - t) * 1000, 1), 'statuses': sorted({x[1]['status'] for x in rs}),
                'p50_ms': pct([x[1]['ms'] for x in rs], 50), 'max_ms': max(x[1]['ms'] for x in rs)})
            # two students on two different papers (Jan 18.4MB + Apr 13.9MB > 32MB source cache): alternate distinct crops
            H.reset_process_caches(); a0 = H.snap(); t = time.perf_counter()
            for k in range(5, 11):
                await timed(c, 'GET', f'/api/attempts/{ja}/questions/{jq[k]["id"]}/asset/question/0?v=2')
                await timed(c, 'GET', f'/api/attempts/{aa}/questions/{aq[k]["id"]}/asset/question/0?v=2')
            one('alternating_two_papers_12_distinct_images', {'wall_ms': round((time.perf_counter() - t) * 1000, 1), **H.diff(a0, H.snap())})
        R['admission_snapshot'] = {k: {kk: v[kk] for kk in ('limit', 'peak', 'admitted', 'rejected', 'failed')} for k, v in H.app.state.admission.snapshot()['lanes'].items()}
        from tejas import packs, derivatives
        import tejas_storage, tejas_core
        R['cache_limits'] = {'pack_cache': packs.cache_stats(), 'source_pdf_cache': {'limit': tejas_storage._source_cache.limit, 'used': tejas_storage._source_cache.size, 'entries': len(tejas_storage._source_cache.data)},
                             'core_crop_cache': {'limit': tejas_core._crop_cache.limit, 'used': tejas_core._crop_cache.size}, 'derivative_cache': {'limit': derivatives._cache.limit, 'used': derivatives._cache.size},
                             'validation_cache': {'limit': derivatives._validation_cache.limit, 'used': derivatives._validation_cache.size}}
        R['rss_mb_end'] = H.rss_mb()
        await explain_all(sid, jan['id'], ja)
    run(go())


def test_event_loop_latency_during_cold_preflight():
    """Probe: GET /api/health + /api/series every 50ms while a COLD preflight renders ~200 crops in threadpool.
    High probe latency => GIL/CPU contention starves the event loop for unrelated users."""
    async def go():
        jan = R['papers']['january']
        phone, p = f'99164{secrets.randbelow(10**5):05d}', f'{secrets.randbelow(10000):04d}'
        async with client(('10.81.5.20', 1)) as c, client(('10.81.5.21', 1)) as g:
            assert (await c.post('/api/auth/phone/signup', json={'phone': phone, 'pin': p, 'confirm_pin': p})).status_code == 200
            base = []
            for _ in range(10):
                t = time.perf_counter(); await g.get('/api/health'); base.append((time.perf_counter() - t) * 1000)
            H.reset_process_caches()
            done = asyncio.Event(); lat = {'health': [], 'series': []}

            async def probe():
                while not done.is_set():
                    for k, u in (('health', '/api/health'), ('series', '/api/series/all-india-jee')):
                        t = time.perf_counter(); await g.get(u); lat[k].append((time.perf_counter() - t) * 1000)
                    await asyncio.sleep(0.05)

            async def pre():
                t = time.perf_counter()
                r = await c.post(f'/api/sets/{jan["id"]}/preflight', json={'test_response': 'ok'})
                done.set(); return r.status_code, (time.perf_counter() - t) * 1000
            pr, (code, pms) = await asyncio.gather(probe(), pre())
            one('event_loop_probe_during_cold_preflight', {'preflight_ms': round(pms, 1), 'status': code,
                'idle_health_p50_ms': pct(base, 50), 'health_p50_ms': pct(lat['health'], 50), 'health_p95_ms': pct(lat['health'], 95),
                'health_max_ms': round(max(lat['health']), 1), 'series_p50_ms': pct(lat['series'], 50), 'series_p95_ms': pct(lat['series'], 95),
                'series_max_ms': round(max(lat['series']), 1), 'probes': len(lat['health'])})
    run(go())


def test_zz_no_real_handles_no_puts():
    assert not H.leftover_real_handles() and not H.PUTS
