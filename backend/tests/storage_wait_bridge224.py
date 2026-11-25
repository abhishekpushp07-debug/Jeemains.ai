"""TEST-ONLY iteration 224 browser bridge: the real app on 127.0.0.1:8774 bound to a disposable isolated DB, Supabase faked in memory.
Supabase is DOWN while /tmp/uibridge224/supabase_down exists (delete the file = Supabase back). Seeds one PDF waiting for Supabase half way through its original, in BITSAT > Mock Tests, and 3 old Emergent files (1 lost) for 'Purani files'. Writes /tmp/uibridge224/bridge.json (owner + reviewer cookies, 0600, key 'book').
Run: cd /app/backend && python tests/storage_wait_bridge224.py 2400 &   (stops by itself; drops its own DB)
"""
import asyncio, json, os, sys
from pathlib import Path
from unittest import mock
sys.path.insert(0, str(Path(__file__).resolve().parent))
from storage_wait224 import FakeSupabase  # noqa: E402
from cut_bridge207 import H, mkstaff, upload, complete, cut_pdf  # noqa: E402
from tejas import structure  # noqa: E402
import tejas_storage as S  # noqa: E402
import uvicorn  # noqa: E402

OUT = '/tmp/uibridge224'
FLAG = OUT + '/supabase_down'


class SwitchedSupabase(FakeSupabase):
    @property
    def down(self):
        return os.path.exists(FLAG)

    @down.setter
    def down(self, value):
        pass


async def main():
    assert not H.leftover_real_handles()
    await H.tdbmod.indexes(); await structure.seed()
    os.makedirs(OUT, exist_ok=True)
    sb = SwitchedSupabase()
    for p in (mock.patch.object(S, 'configured', lambda: True), mock.patch.object(S, 'sb_put', sb.put), mock.patch.object(S, 'sb_get', sb.get),
              mock.patch.object(S, 'sb_list', sb.list), mock.patch.object(S, 'bucket_name', lambda: 'test-bucket')):
        p.start()
    own, _ = await mkstaff('owner', 'ui224'); rev, _ = await mkstaff('reviewer', 'ui224')
    raw = cut_pdf('UI224', long=True)
    Path(OUT, 'one_mock.pdf').write_bytes(raw)
    Path(FLAG).touch(); sb.cut = len(raw) // 2
    b = await upload(own, raw, 'TEST_SUPABASE_WAIT', section_id='bitsat:mocks')
    await complete(own, b['id']); sb.cut = None
    # Old files still on Emergent for the 'Purani files' copy: one picture, one PDF, and one already lost from Emergent.
    import hashlib, time as _t
    for i, (name, data) in enumerate((('old_q1.png', raw[:0] + b'\x89PNG-test-' + bytes(range(64))), ('old_paper.pdf', raw), ('old_lost.png', None))):
        if data is not None:
            H.STORE['tejas/ui224/' + name] = data
        await H.TDB.tejas_files.insert_one({'id': f'ui224-old-{i}', 'kind': 'combined', 'path': 'tejas/ui224/' + name, 'filename': name, 'created_at': _t.time(),
                                            **({'sha256': hashlib.sha256(data).hexdigest()} if data else {'sha256': 'ab' * 32})})
    path = OUT + '/bridge.json'
    with open(path, 'w') as f:
        json.dump({'owner': dict(own.cookies), 'reviewer': dict(rev.cookies), 'book': b['id'], 'type': '/super-admin/exam/bitsat/bitsat:mocks'}, f)
    os.chmod(path, 0o600)
    print('READY', H.TEST_DB, flush=True)
    server = uvicorn.Server(uvicorn.Config(H.app, host='127.0.0.1', port=8774, log_level='warning', lifespan='off'))
    try:
        await asyncio.wait_for(server.serve(), int(sys.argv[1]) if len(sys.argv) > 1 else 900)
    except asyncio.TimeoutError:
        pass
    finally:
        assert H.TEST_DB.startswith('tejas_isolated_') and H.TEST_DB != H.REAL_DB
        await H.tdbmod.client.drop_database(H.TEST_DB)
        for name in ('bridge.json', 'one_mock.pdf', 'supabase_down'):
            try: os.unlink(OUT + '/' + name)
            except OSError: pass
        print('dropped', H.TEST_DB, flush=True)

asyncio.run(main())
