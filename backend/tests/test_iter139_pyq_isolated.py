"""TEST-ONLY iteration 139: JEE Main date-wise PYQ bundle/import/catalogue/attempt/results/crop.
Isolated DB via iso_harness_iter134 (all Motor handles rebound, no lifespan, no AI). Storage boundary is MOCKED:
object GETs map to the ORIGINAL local source PDFs in /app/data/jee_pyq/source_audit; any put_object raises.
Run: cd /app/backend/tests && python -m pytest test_iter139_pyq_isolated.py -n0 -p no:cacheprovider -v
"""
import asyncio, copy, gzip, hashlib, json, os, re, time, uuid
from pathlib import Path
import httpx, pytest
import iso_harness_iter134 as H

LOOP = asyncio.new_event_loop()
asyncio.set_event_loop(LOOP)
run = LOOP.run_until_complete
TDB = H.TDB
import sys
import tejas_storage, tejas_core  # noqa: E402
from tejas import pyq_import as PI, attempts as AT  # noqa: E402

RES = Path('/app/backend/resources')
AUDIT = Path('/app/data/jee_pyq/source_audit')
DATA = json.loads(gzip.decompress((RES / 'jee_pyq.json.gz').read_bytes()))
MANIFEST = json.loads((RES / 'jee_pyq_manifest.json').read_text())
SETS = DATA['collections']['tejas_sets']
FILES = DATA['collections']['tejas_files']
PATHS = {f['path']: AUDIT / (f['source_drive_id'] + '.pdf') for f in FILES}
TAMPER = set()
PUTS, GETS = [], []
EV = {}
OUT = Path('/tmp/iter139'); OUT.mkdir(exist_ok=True)


class _Resp:
    def __init__(self, c): self.content = c


def _bytes(path):
    GETS.append(path)
    if path not in PATHS:
        raise tejas_storage.StorageError('TEST: unknown object ' + path)
    raw = PATHS[path].read_bytes()
    return raw[:-1] + b'X' if path in TAMPER else raw


def fake_request(method, path, data=None, content_type=None):
    if method != 'GET':
        PUTS.append(path); raise RuntimeError('TEST: storage writes forbidden')
    return _Resp(_bytes(path))


def fake_get(path): return _bytes(path)
def fake_put(*a, **k): PUTS.append(a[:1]); raise RuntimeError('TEST: storage writes forbidden')


REAL = (tejas_storage.request, tejas_storage.get_object, tejas_storage.put_object)
for name, mod in list(sys.modules.items()):
    if mod is None or not (name.startswith('tejas') or name == 'server'):
        continue
    for attr, val in list(vars(mod).items()):
        if val is REAL[0]: setattr(mod, attr, fake_request)
        elif val is REAL[1]: setattr(mod, attr, fake_get)
        elif val is REAL[2]: setattr(mod, attr, fake_put)

OWNER = {'id': 'TEST_U139_owner', 'role': 'owner', 'name': 'TEST Owner', 'email': 'test139-owner@example.invalid', 'access_type': 'password'}
OWNER2 = {'id': 'TEST_U139_owner2', 'role': 'owner', 'name': 'TEST Owner2', 'email': 'test139-owner2@example.invalid', 'access_type': 'password'}
REVIEWER = {'id': 'TEST_U139_rev', 'role': 'reviewer', 'name': 'TEST Rev', 'email': 'test139-rev@example.invalid', 'access_type': 'password'}
STUDENT = {'id': 'TEST_U139_s', 'role': 'student', 'name': 'TEST S', 'phone': '+919900000139', 'access_type': 'unverified_phone', 'exam': 'JEE Main'}
OTHER = {'id': 'TEST_U139_o', 'role': 'student', 'name': 'TEST O', 'phone': '+919900000140', 'access_type': 'unverified_phone', 'exam': 'JEE Main'}
H.USERS.update({'w': OWNER, 'w2': OWNER2, 'r': REVIEWER, 's': STUDENT, 'o': OTHER})
W, W2, RV, S, O = ({'x-test-user': k} for k in ('w', 'w2', 'r', 's', 'o'))
UUID_RE = re.compile(r'^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$')
CTX = {}


def client():
    return httpx.AsyncClient(transport=httpx.ASGITransport(app=H.app, raise_app_exceptions=False), base_url='https://api.test.example', timeout=120)


def J(r):
    j = r.json()
    return j.get('data') if isinstance(j, dict) and 'data' in j and 'meta' in j else j


async def counts():
    return {n: await TDB[n].count_documents({'id': {'$regex': '^jee-'}}) for n in PI.COLLECTIONS}


@pytest.fixture(scope='module', autouse=True)
def isolated():
    assert H.TEST_DB != H.REAL_DB and not H.leftover_real_handles()
    run(H.tdbmod.client.drop_database(H.TEST_DB))
    run(H.tdbmod.indexes())
    # pre-existing unrelated JEE mock + NEET pyq-like set must remain unchanged
    run(TDB.tejas_sets.insert_many([
        {'_id': 'TEST_mock139', 'id': 'TEST_mock139', 'title': 'TEST JEE Mock', 'exam': 'JEE Main', 'status': 'published', 'audience': 'all',
         'test_kind': 'mock', 'full_length': True, 'questions': [], 'rules': {'minutes': 180, 'correct': 4}, 'revision': 1},
        {'_id': 'TEST_neet139', 'id': 'TEST_neet139', 'title': 'TEST NEET pyq', 'exam': 'NEET', 'status': 'published', 'audience': 'all',
         'test_kind': 'pyq', 'pyq_date': '2025-05-04', 'pyq_year': 2025, 'pyq_shift': 1, 'questions': [], 'rules': {'minutes': 180, 'correct': 4}}]))
    CTX['pre'] = run(TDB.tejas_sets.find({'id': {'$in': ['TEST_mock139', 'TEST_neet139']}}).to_list(5))
    yield
    run(H.tdbmod.client.drop_database(H.TEST_DB))
    EV['db_dropped'] = H.TEST_DB not in run(H.tdbmod.client.list_database_names())
    EV['storage_puts'] = PUTS
    EV['distinct_storage_gets'] = len(set(GETS))
    with open('/app/test_reports/iter139_pyq_evidence.json', 'w') as f:
        json.dump(EV, f, indent=2, default=str)
    assert EV['db_dropped']


# ---------- bundle / source contract ----------
def test_bundle_integrity_and_shape():
    raw = gzip.decompress((RES / 'jee_pyq.json.gz').read_bytes())
    assert hashlib.sha256(raw).hexdigest() == MANIFEST['sha256'] and MANIFEST['papers'] == 30 and MANIFEST['questions'] == 2250
    sha, data = PI.bundle()
    assert sha == MANIFEST['sha256'] and sum(len(v) for v in data['collections'].values()) == 90
    keys = [(s['pyq_date'], s['pyq_shift']) for s in SETS]
    assert len(set(keys)) == 30 and ('2025-01-23', 1) not in keys
    assert any('23 jan shift 1 of 2025' in b['filename'] for b in DATA['audit']['blocked_sources'])
    disp, ids = {}, set()
    for s in SETS:
        assert s['exam'] == 'JEE Main' and s['test_kind'] == 'pyq' and s['audience'] == 'all' and s['status'] == 'published'
        r = s['rules']; assert (r['minutes'], r['correct'], r['wrong'], r['skipped']) == (180, 4, -1, 0)
        qs = s['questions']; assert len(qs) == 75 and [q['number'] for q in qs] == list(range(1, 76))
        for sub in ('Mathematics', 'Physics', 'Chemistry'):
            sq = [q for q in qs if q['section'] == sub]
            assert len(sq) == 25 and sum(q['type'] == 'mcq' for q in sq) == 20 and sum(q['type'] == 'integer' for q in sq) == 5, (s['id'], sub)
        f = next(x for x in FILES if x['id'] in s['file_ids'])
        assert f['set_id'] == s['id'] or f['set_id'] + '-source-v1' == s['id'] or s['id'].startswith(f['set_id'])
        assert hashlib.sha256(PATHS[f['path']].read_bytes()).hexdigest() == f['sha256'] and PATHS[f['path']].stat().st_size == f['size']
        assert s['pyq_year'] == int(s['pyq_date'][:4])
        for q in qs:
            assert UUID_RE.match(q['id']) and q['id'] not in ids; ids.add(q['id'])
            disp[q['disposition']] = disp.get(q['disposition'], 0) + 1
            if q['type'] == 'mcq':
                assert q['source_option_labels'] == {'A': '1', 'B': '2', 'C': '3', 'D': '4'}
                assert set(q['accepted_answers']) <= set('ABCD')
                if q['disposition'] == 'standard':
                    m = re.search(r'\((\d)\)', ' '.join(q['source_evidence']['printed_key']))
                    if m: assert 'ABCD'[int(m.group(1)) - 1] == q['answer'], (s['id'], q['number'])
            if q['disposition'] == 'bonus_all':
                assert q['accepted_answers'] == [] and q['source_warning']
    EV['dispositions'] = disp
    assert disp.get('bonus_all') == 3 and disp.get('multiple_accepted') == 2


# ---------- import roles / gates ----------
def test_import_roles_and_status_read_only():
    async def go():
        async with client() as c:
            out = {}
            for tag, h in (('anon', {}), ('student', S), ('reviewer', RV)):
                out[tag] = [(await c.get('/api/studio/pyq-import/status', headers=h)).status_code,
                            (await c.post('/api/studio/pyq-import/step', headers=h, json={})).status_code]
            st = await c.get('/api/studio/pyq-import/status', headers=W)
            out['owner_status'] = (st.status_code, J(st))
            out['transfers'] = await TDB.tejas_content_transfers.count_documents({})
            return out
    o = run(go()); EV['roles'] = o
    assert o['anon'] == [401, 401] and o['student'][0] == 403 and o['student'][1] == 403 and o['reviewer'] == [403, 403]
    st = o['owner_status'][1]
    assert o['owner_status'][0] == 200 and st['phase'] == 'ready' and st['total_files'] == 30 and st['total_records'] == 90 and st['questions'] == 2250
    assert o['transfers'] == 0


def test_import_tamper_concurrency_lease_and_verify_before_append():
    async def go():
        async with client() as c:
            TAMPER.add(FILES[0]['path'])
            t = await c.post('/api/studio/pyq-import/step', headers=W, json={})
            doc = await TDB.tejas_content_transfers.find_one({})
            TAMPER.clear()
            res = {'tamper': (t.status_code, t.json()), 'after_tamper': {k: doc[k] for k in ('verified_files', 'phase', 'lease_until')}, 'c0': await counts()}
            a, b = await asyncio.gather(c.post('/api/studio/pyq-import/step', headers=W, json={}), c.post('/api/studio/pyq-import/step', headers=W, json={}))
            res['concurrent'] = sorted([a.status_code, b.status_code])
            res['other_owner'] = (await c.post('/api/studio/pyq-import/step', headers=W2, json={})).status_code
            await TDB.tejas_content_transfers.update_one({}, {'$set': {'lease': 'TEST_foreign', 'lease_until': time.time() + 300}})
            res['held'] = (await c.post('/api/studio/pyq-import/step', headers=W, json={})).status_code
            await TDB.tejas_content_transfers.update_one({}, {'$set': {'lease_until': time.time() - 1}})
            res['takeover'] = (await c.post('/api/studio/pyq-import/step', headers=W, json={})).status_code
            for _ in range(40):
                v = J(await c.post('/api/studio/pyq-import/step', headers=W, json={}))
                if v['phase'] != 'verifying': break
                res.setdefault('mid_counts', await counts())
            res['phase_after_verify'] = v; res['c1'] = await counts()
            return res
    o = run(go()); EV['import_verify'] = o
    assert o['tamper'][0] == 409 and o['after_tamper']['verified_files'] == 0 and o['after_tamper']['lease_until'] == 0
    assert o['c0'] == {n: 0 for n in PI.COLLECTIONS} and o['mid_counts'] == {n: 0 for n in PI.COLLECTIONS}
    assert o['concurrent'] == [200, 409], o['concurrent']
    assert o['other_owner'] == 409 and o['held'] == 409 and o['takeover'] == 200
    # first importing step appends 4 records after all 30 verified
    assert o['phase_after_verify']['verified_files'] == 30


def test_import_conflict_replay_complete_and_idempotent():
    async def go():
        async with client() as c:
            res = {}
            doc = await TDB.tejas_content_transfers.find_one({})
            res['cursor0'] = doc['cursor']
            # conflicting pre-existing record at the NEXT cursor position is never overwritten
            ordered = [(n, r) for n in PI.COLLECTIONS for r in DATA['collections'][n]]
            name, row = ordered[doc['cursor']]
            await TDB[name].insert_one({'_id': 'TEST_conflict', 'id': row['id'], 'name': 'TEST different'})
            cf = await c.post('/api/studio/pyq-import/step', headers=W, json={})
            res['conflict'] = (cf.status_code, cf.json())
            res['conflict_doc_kept'] = (await TDB[name].find_one({'_id': 'TEST_conflict'}))['name']
            res['cursor_after_conflict'] = (await TDB.tejas_content_transfers.find_one({}))['cursor']
            await TDB[name].delete_one({'_id': 'TEST_conflict'})
            # crash replay: roll cursor back after records were appended (identical re-append must be accepted)
            replays = []
            for _ in range(60):
                v = J(await c.post('/api/studio/pyq-import/step', headers=W, json={}))
                d = await TDB.tejas_content_transfers.find_one({})
                if v['phase'] == 'complete': break
                if d['cursor'] in (8, 36, 64):  # files->versions->sets boundaries incl. sets with nested None
                    await TDB.tejas_content_transfers.update_one({}, {'$set': {'cursor': d['cursor'] - 4}})
                    r = await c.post('/api/studio/pyq-import/step', headers=W, json={})
                    replays.append((d['cursor'], r.status_code, r.text[:200] if r.status_code != 200 else ''))
            res['replays'] = replays; res['final'] = v; res['c'] = await counts()
            again = [J(await c.post('/api/studio/pyq-import/step', headers=W, json={})) for _ in range(3)]
            res['again'] = again; res['c_again'] = await counts()
            res['status'] = J(await c.get('/api/studio/pyq-import/status', headers=W))
            # stored set equals bundle (modulo owner attribution) and is parseable
            sdoc = await TDB.tejas_sets.find_one({'id': SETS[0]['id']}, {'_id': 0})
            exp = copy.deepcopy(SETS[0]); exp['rights_attested_by'] = exp['published_by'] = OWNER['id']
            for src in exp['sources'].values(): src['uploaded_by'] = OWNER['id']
            res['stored_equals'] = PI.fingerprint(sdoc) == PI.fingerprint(exp)
            res['pre_unchanged'] = await TDB.tejas_sets.find({'id': {'$in': ['TEST_mock139', 'TEST_neet139']}}).to_list(5) == CTX['pre']
            return res
    o = run(go()); EV['import_append'] = {k: v for k, v in o.items() if k != 'again'}
    assert o['conflict'][0] == 409 and o['conflict_doc_kept'] == 'TEST different' and o['cursor_after_conflict'] == o['cursor0']
    assert all(r[1] == 200 for r in o['replays']), o['replays']
    assert o['final']['phase'] == 'complete' and o['c'] == {n: 30 for n in PI.COLLECTIONS} and o['c_again'] == o['c']
    assert all(a['phase'] == 'complete' and a['published_papers'] == 30 for a in o['again'])
    assert o['status']['inserted_records'] == 90 and o['stored_equals'] and o['pre_unchanged']


# ---------- catalogue ----------
def test_catalogue_auth_shape_filters():
    async def go():
        async with client() as c:
            res = {'anon': (await c.get('/api/pyq/jee-main')).status_code}
            base = await TDB.tejas_sets.find_one({'id': SETS[0]['id']}, {'_id': 0})
            extra = []
            for tag, patch in (('restricted', {'audience': 'restricted', 'allowed_phones': [OTHER['phone']]}), ('expired', {'expires': '2020-01-01'}),
                               ('future', {'start_at': time.time() + 86400}), ('qa', {'qa_only': True}), ('draft', {'status': 'draft'}), ('deleted', {'is_deleted': True})):
                d = {**copy.deepcopy(base), **patch, 'id': 'TEST_pyq_' + tag, 'title': 'TEST ' + tag}
                extra.append(d)
            await TDB.tejas_sets.insert_many([{**d, '_id': d['id']} for d in extra])
            r = await c.get('/api/pyq/jee-main', headers=S); ro = await c.get('/api/pyq/jee-main', headers=O)
            res['status'] = r.status_code; res['cc'] = r.headers.get('cache-control'); res['body'] = J(r); res['other_ids'] = [p['id'] for p in J(ro)['items']]
            res['mocks'] = J(await c.get('/api/exam-navigation/jee-main/catalogue?kind=mocks', headers=S))
            await TDB.tejas_sets.delete_many({'id': {'$regex': '^TEST_pyq_'}})
            return res
    o = run(go())
    b = o['body']; ids = [p['id'] for p in b['items']]
    EV['catalogue'] = {'total': b['total'], 'years': b['years'], 'first': b['items'][:2], 'other_ids_extra': [i for i in o['other_ids'] if i.startswith('TEST')]}
    assert o['anon'] == 401 and o['status'] == 200 and 'no-store' in o['cc'] and 'private' in o['cc']
    assert b['total'] == 30 and b['years'] == [2026, 2025] and not any(i.startswith('TEST') for i in ids)
    assert 'TEST_pyq_restricted' in o['other_ids']
    txt = json.dumps(b)
    for leak in ('questions', 'answer', 'q_refs', 's_refs', 'path', 'sha256', 'accepted'):
        assert '"' + leak not in txt, leak
    assert all(p['count'] == 75 and p['minutes'] == 180 and p['maximum'] == 300 and p['attempt'] is None for p in b['items'])
    dates = [(p['exam_date'], -p['shift']) for p in b['items']]; assert dates == sorted(dates, reverse=True)
    EV['mocks_catalogue_keys'] = list(o['mocks'].keys()) if isinstance(o['mocks'], dict) else str(o['mocks'])[:200]
    assert 'jee-main-pyq' not in json.dumps(o['mocks'])


# ---------- full attempt flow ----------
def _paper(pid):
    return next(s for s in SETS if s['id'] == pid)


async def start(c, pid, h=S, key=None):
    pf = await c.post(f'/api/sets/{pid}/preflight', headers=h, json={'test_response': 'ok'})
    assert pf.status_code == 200, pf.text
    st = await c.post(f'/api/sets/{pid}/start', headers=h, json={'start_key': key or 'TEST_K139_' + uuid.uuid4().hex, 'device_checked': True})
    assert st.status_code == 200, st.text
    return J(st)


async def save(c, aid, qid, value, h=S, rev=1):
    return await c.put(f'/api/attempts/{aid}/answers/{qid}', headers=h, json={'value': value, 'revision': rev, 'request_id': 'TEST_R139_' + uuid.uuid4().hex})


async def results(c, aid, h=S):
    for _ in range(20):
        r = await c.get(f'/api/attempts/{aid}/results', headers=h)
        if r.status_code == 200: return J(r)
        assert r.status_code == 202, r.text
        await asyncio.sleep(0.3)
    raise AssertionError('grading never completed')


Q67_PAPER = next(s['id'] for s in SETS if s['pyq_date'] == '2026-04-04' and s['pyq_shift'] == 2)


def test_full_attempt_flow_q67_paper():
    pid = Q67_PAPER; src = _paper(pid); key = {q['id']: q for q in src['questions']}
    async def go():
        async with client() as c:
            res = {}
            pre = await c.post(f'/api/sets/{pid}/start', headers=S, json={'start_key': 'TEST_K139_nopf_' + uuid.uuid4().hex, 'device_checked': True})
            res['start_without_preflight'] = pre.status_code
            a = await start(c, pid); aid = a['id']; res['attempt'] = a
            txt = json.dumps(a['questions'])
            res['leaks'] = [k for k in ('"answer"', 'accepted_answers', 'source_evidence', 'source_warning', 's_refs', 'q_refs', 'pairing_evidence', 'printed_key', '"solution"', 'disposition') if k in txt]
            res['leak_context'] = [txt[max(0, txt.find(k) - 300):txt.find(k) + 200] for k in res['leaks']]
            qs = a['questions']
            v = await c.post(f'/api/attempts/{aid}/visit', headers=S, json={'question_id': qs[0]['id']})
            res['visit'] = v.status_code
            res['visit_bad'] = (await c.post(f'/api/attempts/{aid}/visit', headers=S, json={'question_id': 'q1'})).status_code
            plan = {}
            mcq = [q for q in src['questions'] if q['type'] == 'mcq' and q['disposition'] == 'standard']
            ints = [q for q in src['questions'] if q['type'] == 'integer']
            for q in mcq[:10]: plan[q['id']] = q['answer']
            for q in mcq[10:15]: plan[q['id']] = next(x for x in 'ABCD' if x != q['answer'])
            for q in ints[:3]: plan[q['id']] = q['answer']
            plan[ints[3]['id']] = str(int(ints[3]['answer']) + 1)
            codes = [(await save(c, aid, qid, val)).status_code for qid, val in plan.items()]
            res['saves'] = codes
            res['bad_qid'] = (await save(c, aid, 'TEST-not-a-question', 'A')).status_code
            res['foreign_get'] = (await c.get(f'/api/attempts/{aid}', headers=O)).status_code
            res['foreign_save'] = (await save(c, aid, qs[0]['id'], 'A', h=O)).status_code
            res['foreign_asset'] = (await c.get(f'/api/attempts/{aid}/questions/{qs[0]["id"]}/asset/question/0', headers=O)).status_code
            q67 = next(q for q in qs if q['number'] == 67)
            res['active_solution_asset'] = (await c.get(f'/api/attempts/{aid}/questions/{q67["id"]}/asset/solution/0', headers=S)).status_code
            res['active_results'] = (await c.get(f'/api/attempts/{aid}/results', headers=S)).status_code
            qa = await c.get(f'/api/attempts/{aid}/questions/{q67["id"]}/asset/question/0', headers=S)
            res['q67_q'] = (qa.status_code, qa.headers.get('content-type'), len(qa.content)); (OUT / 'q67_question.png').write_bytes(qa.content)
            # resume: reload + re-start same key/new key keep deadline + answers
            again = J(await c.get(f'/api/attempts/{aid}', headers=S))
            res['resume_same_deadline'] = again['deadline'] == a['deadline'] and abs(a['deadline'] - a['started_at'] - 10800) < 2
            res['resume_answers'] = sum(1 for k in plan if k in again['answers'])
            rs = await start(c, pid)
            res['restart_same_attempt'] = rs['id'] == aid and rs['deadline'] == a['deadline']
            cat = J(await c.get('/api/pyq/jee-main', headers=S)); row = next(p for p in cat['items'] if p['id'] == pid)
            res['cat_active'] = row
            sub = await c.post(f'/api/attempts/{aid}/submit', headers=S); res['submit'] = sub.status_code
            r = await results(c, aid); res['score'] = r['summary'].get('score') if 'summary' in r else None
            rq = {q['id']: q for q in r['questions']}
            res['r_q67'] = {k: rq[q67['id']].get(k) for k in ('source_option_labels', 'source_warning', 'source_evidence', 'asset_count', 'solution_asset_count', 'outcome')}
            sa = [await c.get(f'/api/attempts/{aid}/questions/{q67["id"]}/asset/solution/{i}', headers=S) for i in range(2)]
            for i, x in enumerate(sa): (OUT / f'q67_solution_{i}.png').write_bytes(x.content)
            res['q67_s'] = [(x.status_code, len(x.content)) for x in sa]
            res['foreign_results'] = (await c.get(f'/api/attempts/{aid}/results', headers=O)).status_code
            # key-only paper solution notice (2025-01-22 s1 Q43) via frozen pack retention
            # attempt again
            a2 = await start(c, pid)
            res['retake'] = {'new_id': a2['id'] != aid, 'blank': a2['answers'] == {}, 'n': len(a2['questions']), 'uuid': bool(UUID_RE.match(a2['id']))}
            res['old_result_kept'] = (await c.get(f'/api/attempts/{aid}/results', headers=S)).status_code
            cat = J(await c.get('/api/pyq/jee-main', headers=S)); row = next(p for p in cat['items'] if p['id'] == pid)
            res['cat_after_retake'] = row
            # expire active attempt: catalogue exposes result access but does not mutate DB
            await TDB.tejas_attempts.update_one({'id': a2['id']}, {'$set': {'deadline': time.time() - 5}})
            before = await TDB.tejas_attempts.find_one({'id': a2['id']}, {'_id': 0})
            row = next(p for p in J(await c.get('/api/pyq/jee-main', headers=S))['items'] if p['id'] == pid)
            after = await TDB.tejas_attempts.find_one({'id': a2['id']}, {'_id': 0})
            res['cat_expired'] = row; res['expired_unmutated'] = before == after and after['status'] == 'active'
            r2 = await results(c, a2['id']); res['expired_result'] = (r2.get('status'), r2.get('reason'), r2['summary'].get('score'))
            other = J(await c.get('/api/pyq/jee-main', headers=O)); res['other_sees'] = [p for p in other['items'] if p['attempt'] or p['attempt_count']]
            hist = await c.get('/api/exam-navigation/jee-main/history?kind=pyq', headers=S)
            res['history'] = (hist.status_code, [ (i.get('id'), i.get('kind') or i.get('test_kind')) for i in J(hist).get('items', [])][:5])
            CTX['aid'] = aid
            return res, plan
    o, plan = run(go()); EV['flow'] = {k: v for k, v in o.items() if k != 'attempt'}
    expected = 13 * 4 - 6 * 1  # 10 mcq + 3 int correct, 5 mcq + 1 int wrong
    assert o['start_without_preflight'] == 400
    CTX['leak'] = o['leaks']  # asserted separately at the end so the rest of the flow is exercised
    assert all(q.get('source_option_labels') == ({'A': '1', 'B': '2', 'C': '3', 'D': '4'} if q['type'] == 'mcq' else q.get('source_option_labels')) for q in o['attempt']['questions'])
    assert len(o['attempt']['questions']) == 75 and all(UUID_RE.match(q['id']) for q in o['attempt']['questions'])
    assert o['visit'] == 200 and o['visit_bad'] in (400, 422) and set(o['saves']) == {200} and o['bad_qid'] in (400, 404)
    assert o['foreign_get'] == 404 and o['foreign_save'] == 404 and o['foreign_asset'] == 404
    assert o['active_solution_asset'] == 403 and o['active_results'] == 403
    assert o['q67_q'][0] == 200 and o['q67_q'][1] == 'image/png' and o['q67_q'][2] > 5000
    assert o['resume_same_deadline'] and o['resume_answers'] == len(plan) and o['restart_same_attempt']
    assert o['cat_active']['attempt']['status'] == 'active' and o['cat_active']['latest_result_id'] is None
    assert o['submit'] in (200, 202) and o['score'] == expected, o['score']
    assert o['r_q67']['source_option_labels'] and o['r_q67']['solution_asset_count'] == 2 and o['q67_s'] == [(200, o['q67_s'][0][1]), (200, o['q67_s'][1][1])]
    assert o['foreign_results'] == 404
    assert all(o['retake'].values()) and o['retake']['n'] == 75 and o['old_result_kept'] == 200
    assert o['cat_after_retake']['attempt_count'] == 2 and o['cat_after_retake']['attempt']['status'] == 'active' and o['cat_after_retake']['latest_result_id'] == CTX['aid']
    assert o['cat_expired']['attempt']['status'] == 'completed' and o['expired_unmutated']
    assert o['expired_result'][2] == 0 and o['other_sees'] == []


def test_jan2026_large_page_papers_preflight_and_assets():
    # 10 Jan-2026 source PDFs have 2479x3508pt (A4@300dpi-as-points) pages; tejas_core.validate_pdf rejects >3000pt
    jan = [s['id'] for s in SETS if s['pyq_date'].startswith('2026-01')]
    async def go():
        async with client() as c:
            return {pid: ((r := await c.post(f'/api/sets/{pid}/preflight', headers=S, json={})).status_code, r.text[:160]) for pid in jan}
    o = run(go()); EV['jan2026_preflight'] = o
    assert len(jan) == 10
    assert all(v[0] == 200 for v in o.values()), o


def test_bonus_multikey_keyonly_dispositions():
    bonus_pid = 'jee-main-pyq-2026-01-22-s1'; multi_pid = next(s['id'] for s in SETS if any(q['disposition'] == 'multiple_accepted' for q in s['questions']))
    keyonly_pid = 'jee-main-pyq-2025-01-22-s1'
    async def go():
        async with client() as c:
            res = {}
            for pid in (bonus_pid, multi_pid, keyonly_pid):
                src = _paper(pid); a = await start(c, pid)
                if pid == multi_pid:
                    mq = [q for q in src['questions'] if q['disposition'] == 'multiple_accepted']
                    for q in mq: await save(c, a['id'], q['id'], q['accepted_answers'][-1])
                await c.post(f'/api/attempts/{a["id"]}/submit', headers=S)
                r = await results(c, a['id'])
                rows = {q['id']: q for q in r['questions']}
                interesting = [q for q in src['questions'] if q['disposition'] != 'standard' or q['solution_kind'] == 'supplied_key_only']
                res[pid] = {'score': r['summary'].get('score'),
                            'rows': [{'n': q['number'], 'disp': q['disposition'], **{k: rows[q['id']].get(k) for k in ('outcome', 'marks', 'source_warning', 'solution_kind', 'solution_asset_count')}} for q in interesting]}
            return res
    o = run(go()); EV['dispositions_results'] = o
    nb = sum(q['disposition'] == 'bonus_all' for q in _paper(bonus_pid)['questions'])
    assert o[bonus_pid]['score'] == 4 * nb and all(r['marks'] == 4 for r in o[bonus_pid]['rows'] if r['disp'] == 'bonus_all')
    nm = sum(q['disposition'] == 'multiple_accepted' for q in _paper(multi_pid)['questions'])
    assert o[multi_pid]['score'] == 4 * nm
    ko = [r for r in o[keyonly_pid]['rows'] if r['solution_kind'] == 'supplied_key_only']
    assert ko and all(r['source_warning'] for r in ko)


# ---------- crop omission (Apr4 2026 S2 Q67) ----------
def test_q67_crop_omission_and_cache_separation():
    q = next(x for x in _paper(Q67_PAPER)['questions'] if x['number'] == 67)
    f = next(x for x in FILES if x['id'] == q['q_refs'][0]['file_id']); raw = PATHS[f['path']].read_bytes()
    ref = q['q_refs'][0]; plain = {k: v for k, v in ref.items() if k != 'omit_rects'}
    masked = tejas_core.crop_png(raw, ref); unmasked = tejas_core.crop_png(raw, plain)
    (OUT / 'q67_unmasked.png').write_bytes(unmasked); (OUT / 'q67_masked.png').write_bytes(masked)
    assert masked != unmasked and tejas_core.crop_png(raw, ref) == masked and tejas_core.crop_png(raw, plain) == unmasked
    with pytest.raises(ValueError):
        tejas_core._render_crop_png(raw, {**ref, 'omit_rects': [[0, 0, 600, 900]]})
    with pytest.raises(ValueError):
        tejas_core._render_crop_png(raw, {**ref, 'omit_rects': [[30, 500, 30, 500]]})
    assert hashlib.sha256(raw).hexdigest() == f['sha256']
    import fitz, numpy as np
    pm = lambda b: fitz.Pixmap(b)
    a, b = pm(masked), pm(unmasked)
    A = np.frombuffer(a.samples, dtype=np.uint8).reshape(a.height, a.width, a.n); B = np.frombuffer(b.samples, dtype=np.uint8).reshape(b.height, b.width, b.n)
    diff = np.argwhere((A != B).any(axis=2))
    EV['q67_mask_diff_rows'] = [int(diff[:, 0].min()), int(diff[:, 0].max()), int(diff[:, 1].min()), int(diff[:, 1].max())] if len(diff) else []
    om = ref['omit_rects'][0]; y0 = (om[1] - ref['rect'][1]) * 2
    assert len(diff) and diff[:, 0].min() >= y0 - 2


def test_active_start_payload_has_no_answer_provenance():
    assert not CTX.get('leak'), (CTX.get('leak'), EV['flow'].get('leak_context'))


def test_isolation_still_holds():
    assert not H.leftover_real_handles() and PUTS == []
