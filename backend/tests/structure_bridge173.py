"""TEST-ONLY iteration 173 browser bridge: real app on 127.0.0.1:8773 bound to a disposable isolated DB (storage/AI mocked).
Seeds built-in structure + TEST_ fixtures + one processed book (2 ready, 1 held) in bitsat:mocks + hidden custom exam.
Writes /tmp/uibridge173/bridge.json (owner/reviewer/student cookies + ids, 0600). Drops its DB on exit.
Run: cd /app/backend && python tests/structure_bridge173.py 1500 &
"""
import asyncio, json, os, sys, time, uuid
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import book_publishing_iso170 as T  # noqa
from book_publishing_iso170 import H, mkstaff, client, build_pdf, q3, upload, complete
from structure_iso173 import mkset
from tejas import structure
import uvicorn

OUT = '/tmp/uibridge173'


async def main():
    assert not H.leftover_real_handles()
    os.makedirs(OUT, exist_ok=True)
    await structure.seed()
    own, _ = await mkstaff('owner', 'ui')
    rev, _ = await mkstaff('reviewer', 'uirev')
    stu = client(); await stu.post('/api/auth/phone/signup', json={'phone': '95' + str(uuid.uuid4().int)[:8], 'pin': '4826', 'confirm_pin': '4826'})
    t = time.time()
    fx = {'pyq': await mkset('PYQ', exam='JEE Main', test_kind='pyq', pyq_date='2024-01-27'),
          'bm1': await mkset('BM1', exam='BITSAT', test_kind='mock', mock_number=1),
          'bm2': await mkset('BM2', exam='BITSAT', test_kind='mock', mock_number=2),
          'jch': await mkset('JCH', exam='JEE Main', test_kind='chapter', chapter_book_id='TEST_CB173', chapter_subject='Physics', chapter_number=1,
                             live_enabled=True, start_at=t - 3600, end_at=t + 86400 * 30)}
    r = await own.post('/api/admin/catalog/exams', json={'name': 'TEST NEET', 'short': 'TNEET', 'subjects': ['Physics', 'Biology'], 'color': 'teal'})
    fx['exam'] = r.json()['slug']
    r = await own.post(f"/api/admin/catalog/exams/{fx['exam']}/sections", json={'name': 'TEST Full Mocks', 'description': 'Full papers', 'layout': 'list'})
    fx['nsec'] = r.json()['id']; fx['nsec_slug'] = r.json()['slug']
    fx['cust'] = await mkset('CUST', exam='TEST NEET', catalog_section_id=fx['nsec'], test_kind='mock')
    mocks = [{'n': 1, 'qs': q3('U1'), 'keys': [(1, 'B'), (2, 'B'), (3, 'C')]},
             {'n': 2, 'qs': q3('U2'), 'keys': [(1, 'B'), (2, 'B'), (3, 'C')]},
             {'n': 3, 'qs': q3('U3'), 'keys': [(1, 'B'), (2, 'B'), (2, 'A'), (3, 'C')]}]
    b = await upload(own, build_pdf(mocks), 'TEST_QA173 UI Book', section_id='bitsat:mocks')
    await complete(own, b['id']); fx['book'] = b['id']
    build_pdf([{'n': 1, 'qs': q3('W1'), 'keys': [(1, 'B'), (2, 'B'), (3, 'C')]}], path=OUT + '/wizard.pdf')
    path = OUT + '/bridge.json'
    with open(path, 'w') as f:
        json.dump({'owner': dict(own.cookies), 'reviewer': dict(rev.cookies), 'student': dict(stu.cookies), 'fx': fx}, f)
    os.chmod(path, 0o600)
    print('READY', H.TEST_DB, json.dumps(fx), flush=True)
    server = uvicorn.Server(uvicorn.Config(H.app, host='127.0.0.1', port=8773, log_level='warning', lifespan='off'))
    try:
        await asyncio.wait_for(server.serve(), int(sys.argv[1]) if len(sys.argv) > 1 else 900)
    except asyncio.TimeoutError:
        pass
    finally:
        await H.tdbmod.client.drop_database(H.TEST_DB)
        try: os.unlink(path)
        except OSError: pass
        print('dropped', H.TEST_DB, flush=True)

asyncio.run(main())
