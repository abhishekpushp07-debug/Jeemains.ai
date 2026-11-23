"""TEST-ONLY (testing agent, iteration 219): retest of storage_move fixes C/D/E/F.
C) lease_until renewed before every file and on progress callbacks
D) switch requires the recorded sha (a file whose sha changed mid-copy is not switched)
E) failure reasons are fixed Hinglish text, no raw exception text, no paths
F) Start: 409 when Supabase down (fresh check); Start on a waiting run with Supabase back resumes once; Start while running returns status
Disposable DB (iso harness), Supabase faked. Run: cd /app/backend && python tests/storage_move_fix226.py
"""
import asyncio, hashlib, os, sys, threading, time, uuid
from pathlib import Path
from unittest import mock
sys.path.insert(0, str(Path(__file__).resolve().parent))
from storage_wait224 import FakeSupabase  # noqa: E402
from cut_bridge207 import H, J, DB, mkstaff, cut_pdf  # noqa: E402
from tejas import structure, storage_move as SM  # noqa: E402
import tejas_storage as S  # noqa: E402
from pymongo import MongoClient  # noqa: E402

RESULTS = []


def check(name, ok, detail=''):
    RESULTS.append(bool(ok)); print(('PASS ' if ok else 'FAIL ') + name + ('' if ok else ' :: ' + str(detail)[:400]), flush=True)


async def settle():
    while SM._tasks:
        await asyncio.gather(*list(SM._tasks))


async def main():
    assert not H.leftover_real_handles()
    await H.tdbmod.indexes(); await structure.seed()
    sb = FakeSupabase()
    sync = MongoClient(os.environ['MONGO_URL'])[H.TEST_DB]
    gate = {'hold': None, 'shachg': None}

    def sb_get(bucket, path, tries=4):
        if path.endswith('readback.pdf'):
            raise S.StorageError('Supabase file unavailable (404) secret/' + path)
        return sb.get(bucket, path, tries)

    def sb_put(path, data, ct, resume=None, on_progress=None):
        if gate['hold'] is not None:
            gate['hold'].wait(20)
        if gate['shachg'] and path == gate['shachg']:
            sync.tejas_files.update_one({'path': path}, {'$set': {'sha256': 'cd' * 32}})  # the file was re-saved with new bytes meanwhile
        return sb.put(path, data, ct, resume, on_progress)
    patches = [mock.patch.object(S, 'configured', lambda: True), mock.patch.object(S, 'sb_put', sb_put), mock.patch.object(S, 'sb_get', sb_get),
               mock.patch.object(S, 'bucket_name', lambda: 'test-bucket')]
    for p in patches:
        p.start()
    S.STATE.update(down_until=0.0, strikes=0, failovers=0, last_failover=None, backup_since=None)
    try:
        own, _ = await mkstaff('owner', 'mvf')
        pdf = cut_pdf('MVF'); h = hashlib.sha256(pdf).hexdigest()
        paths = {k: f'tejas/test/{k}.pdf' for k in ('ok', 'missing', 'readback', 'shachg')}
        for k in ('ok', 'readback', 'shachg'):
            H.STORE[paths[k]] = pdf
        ids = {k: 'TEST_' + k + '_' + uuid.uuid4().hex[:6] for k in paths}
        await DB.tejas_files.insert_many([{'id': ids[k], 'kind': 'combined', 'path': paths[k], 'sha256': h, 'filename': f'{k}.pdf', 'created_at': time.time() + i}
                                         for i, k in enumerate(paths)])
        gate['shachg'] = paths['shachg']
        # F1: Supabase down -> 409, nothing started
        sb.down = True
        r = await own.post('/api/admin/storage/move/start')
        check('F: Start with Supabase down -> 409 Hinglish', r.status_code == 409 and 'jawab nahi de raha' in r.text, (r.status_code, r.text[:200]))
        op = await DB.tejas_operations.find_one({'_id': SM.OP})
        check('F: nothing started after 409', not op or op.get('state') != 'running', op and op.get('state'))
        sb.down = False; S.STATE.update(down_until=0.0, strikes=0)
        # C: record lease renewals
        notes = []
        real_note = SM._note

        async def spy(token, change):
            notes.append(change.get('$set') or {})
            return await real_note(token, change)
        with mock.patch.object(SM, '_note', spy):
            r = await own.post('/api/admin/storage/move/start')
            check('F: Start with Supabase up -> 200', r.status_code == 200, (r.status_code, r.text[:200]))
            await settle()
        st = J(await own.get('/api/admin/storage/move/status'))
        pre = [n for n in notes if 'current' in n and n.get('current') and 'lease_until' in n]
        check('C: lease renewed before every file (4 files)', len(pre) == 4, len(pre))
        rows = {d['id']: d async for d in DB.tejas_files.find({'id': {'$in': list(ids.values())}})}
        check('ok file switched', rows[ids['ok']]['path'].startswith('sb://'), rows[ids['ok']]['path'])
        check('D: sha changed mid-copy -> not switched', rows[ids['shachg']]['path'] == paths['shachg'], rows[ids['shachg']])
        check('D: counted as skipped', st['skipped'] == 1, {k: st[k] for k in ('moved', 'failed', 'skipped')})
        check('missing/readback stay on Emergent', rows[ids['missing']]['path'] == paths['missing'] and rows[ids['readback']]['path'] == paths['readback'])
        reasons = {f['label']: f['reason'] for f in st['failures']}
        miss = [v for k, v in reasons.items() if 'missing' in k]; rb = [v for k, v in reasons.items() if 'readback' in k]
        check('E: missing on Emergent -> fixed Hinglish reason', miss == [SM.NOT_ON_EMERGENT], reasons)
        check('E: Supabase read-back failure -> Hinglish reason', rb and rb[0].startswith('Supabase se copy wapas padhi nahi ja saki'), reasons)
        blob = str(st['failures'])
        check('E: no paths / raw exception text in failures', 'tejas/' not in blob and 'secret' not in blob and 'TEST: missing' not in blob and '404' not in blob, blob)
        check('status totals: done state, total 4', st['state'] == 'done' and st['total'] == 4 and st['moved'] == 1 and st['failed'] == 2, {k: st[k] for k in ('state', 'total', 'moved', 'failed', 'skipped')})
        # F2: Start while a run is going -> status, no second run
        H.STORE['tejas/test/hold.pdf'] = pdf
        await DB.tejas_files.insert_one({'id': 'TEST_hold', 'kind': 'combined', 'path': 'tejas/test/hold.pdf', 'sha256': h, 'filename': 'hold.pdf', 'created_at': time.time()})
        gate['hold'] = threading.Event()
        r1 = await own.post('/api/admin/storage/move/start'); await asyncio.sleep(0.5)
        r2 = await own.post('/api/admin/storage/move/start')
        check('F: Start while running -> 200 status (running)', r2.status_code == 200 and J(r2)['state'] == 'running', (r1.status_code, r2.status_code, r2.text[:200]))
        check('F: only one run task', len(SM._tasks) == 1, len(SM._tasks))
        gate['hold'].set(); gate['hold'] = None; await settle()
        # F3: waiting run, Supabase back, Start -> resumes (not fresh, counters kept), one run
        H.STORE['tejas/test/w.pdf'] = pdf
        await DB.tejas_files.insert_one({'id': 'TEST_w', 'kind': 'combined', 'path': 'tejas/test/w.pdf', 'sha256': h, 'filename': 'w.pdf', 'created_at': time.time()})
        sb.down = True; S.STATE.update(down_until=0.0, strikes=0)
        await SM.begin(True); await settle()
        st = J(await own.get('/api/admin/storage/move/status'))
        check('setup: run waiting', st['state'] == 'waiting', st['state'])
        sb.down = False
        r = await own.post('/api/admin/storage/move/start')
        check('F: Start right after Supabase is back -> 200', r.status_code == 200, (r.status_code, r.text[:200]))
        await settle()
        st = J(await own.get('/api/admin/storage/move/status'))
        w = await DB.tejas_files.find_one({'id': 'TEST_w'})
        check('F: waiting run resumed and finished (file switched)', st['state'] == 'done' and w['path'].startswith('sb://'), (st['state'], w['path']))
    finally:
        for p in patches:
            p.stop()
        assert H.TEST_DB.startswith('tejas_isolated_') and H.TEST_DB != H.REAL_DB
        await H.tdbmod.client.drop_database(H.TEST_DB)
    print(f'TOTAL {len(RESULTS)} PASS {sum(RESULTS)} FAIL {len(RESULTS) - sum(RESULTS)}')


if __name__ == '__main__':
    asyncio.run(main())
