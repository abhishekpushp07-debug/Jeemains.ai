"""TEST-ONLY iteration 207 browser bridge for PDF Engine 2.0 (question + options cut): real app on 127.0.0.1:8772 with a disposable DB.
Fixtures: one held mock (one question the cutter refuses), one Live mock in the new look with an active and a submitted student attempt.
Run: cd /app/backend && python tests/cut_bridge207.py 2400 &   (cookies + ids in /tmp/uibridge207/bridge.json, 0600)
"""
import asyncio, json, os, sys, uuid
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import fitz  # noqa: E402
import book_publishing_iso170 as T  # noqa: E402,F401
from book_publishing_iso170 import H, mkstaff, client, upload, complete, drain  # noqa: E402
from structure_iso173 import start  # noqa: E402
from tejas import structure  # noqa: E402
import uvicorn  # noqa: E402

OUT = os.environ.get('BRIDGE_OUT', '/tmp/uibridge207')
PORT = int(os.environ.get('BRIDGE_PORT', '8772'))
DB = H.TDB; BM = DB.tejas_book_mocks
M = '/api/admin/master'


def J(r):
    try: d = r.json()
    except Exception: return {}
    return d if d is not None else {}


def cut_pdf(tag, broken=False, long=False):
    """One paper: column, grid and row options, a diagram, a numerical question; broken=True adds a question whose labels are not lined up."""
    doc = fitz.open(); p = doc.new_page(); p.insert_text((40, 60), 'Physics', fontsize=13); y = 100
    def stem(n, text):
        nonlocal y
        for i, line in enumerate(text.split('\n')):
            p.insert_text((40, y), (f'Q{n}. ' if i == 0 else '      ') + line, fontsize=11); y += 16
        y += 4
    stem(1, f'{tag} A ball is dropped from a tower of height 20 m. Taking g = 10 m/s2,\nthe time it takes to reach the ground is')
    for lab, o in zip('ABCD', ['1 s', '2 s', '3 s', '4 s']):
        p.insert_text((60, y), f'({lab}) {o}', fontsize=11); y += 18
    y += 24
    stem(2, f'{tag} The SI unit of force is the')
    for row in (('A', 'joule', 'B', 'newton'), ('C', 'watt', 'D', 'pascal')):
        p.insert_text((60, y), f'({row[0]}) {row[1]}', fontsize=11); p.insert_text((300, y), f'({row[2]}) {row[3]}', fontsize=11); y += 18
    y += 24
    stem(3, f'{tag} The block in the figure slides on a smooth incline. Its acceleration is')
    p.draw_rect(fitz.Rect(70, y, 190, y + 46), color=(0, 0, 0), width=1); p.draw_line((70, y + 46), (190, y), color=(0, 0, 0), width=1); y += 64
    for x, lab, o in zip((60, 180, 300, 420), 'ABCD', ['g/2', 'g/3', 'g/4', 'g']):
        p.insert_text((x, y), f'({lab}) {o}', fontsize=11)
    y += 42
    if long:
        stem(4, f'{tag} Which statement about the kinetic energy of a rolling sphere is correct?')
        for lab, o in zip('ABCD', ['It is purely translational when the sphere rolls without slipping on a rough floor',
                                   'It is the sum of translational and rotational parts', 'It is purely rotational', 'It is always zero']):
            p.insert_text((60, y), f'({lab}) {o}', fontsize=11); y += 18
        y += 24
    if broken:
        stem(5 if long else 4, f'{tag} The speed of light in vacuum is of the order')
        p.insert_text((60, y), '(A) 1e3 m/s', fontsize=11); p.insert_text((300, y), '(B) 1e5 m/s', fontsize=11); y += 18
        p.insert_text((96, y), '(C) 1e8 m/s', fontsize=11); p.insert_text((300, y), '(D) 1e10 m/s', fontsize=11); y += 18
    n = 3 + int(long) + int(broken)
    p = doc.new_page(); p.insert_text((40, 60), 'Answer Key', fontsize=13); y = 100
    for num, ans in list(zip(range(1, 6), 'BBABC'))[:n]:
        p.insert_text((40, y), f'Q{num}. ({ans})', fontsize=11); y += 20
    raw = doc.tobytes(); doc.close(); return raw + b'\n%' + uuid.uuid4().hex.encode()


async def book(own, sec, tag, **kw):
    b = await upload(own, cut_pdf(tag, **kw), 'TEST_' + tag, section_id=sec); await complete(own, b['id']); await drain()
    m = await BM.find_one({'book_id': b['id']})
    print('BOOK', tag, m['state'], m.get('cut_summary'), m['issues'], [(q['original_number'], q['type'], (q.get('cut') or {}).get('status'), (q.get('cut') or {}).get('arrangement'), (q.get('cut') or {}).get('reason')) for q in m['questions']], flush=True)
    return b['id'], m['_id']


async def pump():
    while True:
        try: await drain()
        except Exception as e: print('drain error', e, flush=True)
        await asyncio.sleep(1)


async def main():
    assert not H.leftover_real_handles()
    await H.tdbmod.indexes(); await structure.seed()
    os.makedirs(OUT, exist_ok=True); path = OUT + '/bridge.json'
    try:
        own, _ = await mkstaff('owner', 'ui'); rev, _ = await mkstaff('reviewer', 'ui')
        stu = client(); await stu.post('/api/auth/phone/signup', json={'phone': '91' + str(uuid.uuid4().int)[:8], 'pin': '8261', 'confirm_pin': '8261'})
        slug = J(await own.post('/api/admin/catalog/exams', json={'name': 'CUTX', 'short': 'CX', 'subjects': ['Physics'], 'color': 'rose'})).get('slug')
        sec = J(await own.post(f'/api/admin/catalog/exams/{slug}/sections', json={'name': 'Mock Tests', 'description': '', 'layout': 'list', 'kind': 'mocks'})).get('id')
        await structure.exams.update_one({'_id': slug}, {'$set': {'shown': True}})
        f = {'slug': slug, 'section': sec}
        f['held'] = await book(own, sec, 'HELD', broken=True)
        f['held2'] = await book(own, sec, 'HELDB', broken=True)
        f['draft'] = await book(own, sec, 'DRAFT', long=True)
        f['live'] = await book(own, sec, 'LIVE', long=True)
        r = await own.post(M + '/status', json={'items': [{'kind': 'book_mock', 'id': f['live'][1]}], 'to': 'live'}); await drain()
        f['live_set'] = (await BM.find_one({'_id': f['live'][1]})).get('set_id'); print('LIVE status', r.status_code, r.text[:200], f['live_set'], flush=True)
        await asyncio.sleep(2); await structure.visibility(force=True)
        if f['live_set']:
            s = await DB.tejas_sets.find_one({'id': f['live_set']}, {'_id': 0, 'questions': 1})
            print('SET pieces', [(q['number'], [(c['part'], c['w'], c['h']) for c in q.get('c_refs', [])]) for q in s['questions']], flush=True)
            r = await start(stu, f['live_set']); a = J(r); print('START done', r.status_code, r.text[:200], flush=True)
            first = a['questions'][0]
            await stu.post(f"/api/attempts/{a['id']}/begin"); await asyncio.sleep(.2)
            f['done_attempt'] = a['id']
            f['submit'] = (await stu.post(f"/api/attempts/{a['id']}/submit")).status_code
            r = await start(stu, f['live_set']); f['active_attempt'] = J(r).get('id'); print('START active', r.status_code, r.text[:160], first.get('pieces'), flush=True)
        with open(path, 'w') as fh: json.dump({'owner': dict(own.cookies), 'reviewer': dict(rev.cookies), 'student': dict(stu.cookies), 'f': f}, fh)
        os.chmod(path, 0o600)
        print('READY', H.TEST_DB, json.dumps(f), flush=True)
        task = asyncio.create_task(pump())
        server = uvicorn.Server(uvicorn.Config(H.app, host='127.0.0.1', port=PORT, log_level='warning', lifespan='off'))
        try: await asyncio.wait_for(server.serve(), int(sys.argv[1]) if len(sys.argv) > 1 else 900)
        except asyncio.TimeoutError: pass
        task.cancel()
    finally:
        # Only the disposable database this run created; never the app's own.
        assert H.TEST_DB.startswith('tejas_isolated_') and H.TEST_DB != H.REAL_DB
        await H.tdbmod.client.drop_database(H.TEST_DB)
        try: os.unlink(path)
        except OSError: pass
        print('dropped', H.TEST_DB, flush=True)


if __name__ == '__main__':
    asyncio.run(main())
