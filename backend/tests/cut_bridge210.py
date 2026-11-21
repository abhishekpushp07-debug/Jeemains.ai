"""TEST-ONLY iteration 210 browser bridge for PDF Engine 2.0 (printed boxes first): real app on 127.0.0.1:8772 with a disposable DB.
Fixtures: the owner's own boxed PDF (two chapters cut out of /root/pdfengine/chemistry_chapterwise.pdf), once clean and Live with a student
attempt, once with a mark printed between the boxes (held, for the fix tool), plus the made-up papers of bridge 207.
Run: cd /app/backend && python tests/cut_bridge210.py 2400 &   (cookies + ids in /tmp/uibridge210/bridge.json, 0600)
Stop with: kill -INT <pid>   (only then is its database dropped)
"""
import asyncio, json, os, sys, uuid
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
os.environ.setdefault('BRIDGE_OUT', '/tmp/uibridge210')
import fitz  # noqa: E402
import cut_bridge207 as B  # noqa: E402
from cut_bridge207 import H, J, BM, DB, M, book, pump, mkstaff, client, drain, upload, complete, start  # noqa: E402
from tejas import structure  # noqa: E402
import uvicorn  # noqa: E402

OUT, PORT = os.environ['BRIDGE_OUT'], B.PORT
REAL = '/root/pdfengine/chemistry_chapterwise.pdf'


def boxed_pdf(stray=False):
    """Chapter 8 (16 questions, key, solutions) and chapter 24 (2 questions) of the owner's boxed PDF, with their bookmarks."""
    src = fitz.open(REAL); doc = fitz.open()
    doc.insert_pdf(src, from_page=706, to_page=738); doc.insert_pdf(src, from_page=2522, to_page=2526)
    doc.set_toc([[1, '08 Redox Reactions', 1], [2, 'Questions', 1], [2, 'Answer key', 17], [2, 'Solutions', 18],
                 [1, '24 Miscellaneous', 34], [2, 'Questions', 34], [2, 'Answer key', 36], [2, 'Solutions', 37]])
    if stray:
        # Something printed between the question's box and option A's box: the engine must not guess whose it is.
        doc[2].insert_text((44, 321), 'Note: see table', fontsize=6)
    raw = doc.tobytes(garbage=3, deflate=True); doc.close(); src.close()
    return raw + b'\n%' + uuid.uuid4().hex.encode()


async def chapters(own, sec, tag, **kw):
    b = await upload(own, boxed_pdf(**kw), 'TEST_' + tag, section_id=sec, subject='Chemistry'); await complete(own, b['id']); await drain(3000)
    rows = await BM.find({'book_id': b['id']}).sort('order', 1).to_list(20)
    bk = await DB.tejas_books.find_one({'_id': b['id']})
    print('BOOK', tag, bk['state'], bk['payload'].get('plan_source'), bk['payload'].get('message'), flush=True)
    for m in rows:
        print('  MOCK', m['label'], (m.get('chapter') or {}).get('title'), m['state'], m.get('cut_summary'), m['issues'][:6],
              [(q['original_number'], q['type'], q.get('answer'), (q.get('cut') or {}).get('status'), (q.get('cut') or {}).get('arrangement')) for q in m['questions']], flush=True)
    return b['id'], [m['_id'] for m in rows]


async def main():
    assert not H.leftover_real_handles()
    await H.tdbmod.indexes(); await structure.seed()
    os.makedirs(OUT, exist_ok=True); path = OUT + '/bridge.json'
    try:
        own, _ = await mkstaff('owner', 'ui'); rev, _ = await mkstaff('reviewer', 'ui')
        stu = client(); await stu.post('/api/auth/phone/signup', json={'phone': '91' + str(uuid.uuid4().int)[:8], 'pin': '8261', 'confirm_pin': '8261'})
        slug = J(await own.post('/api/admin/catalog/exams', json={'name': 'CUTX', 'short': 'CX', 'subjects': ['Physics', 'Chemistry'], 'color': 'rose'})).get('slug')
        sec = J(await own.post(f'/api/admin/catalog/exams/{slug}/sections', json={'name': 'Mock Tests', 'description': '', 'layout': 'list', 'kind': 'mocks'})).get('id')
        r = await own.post(f'/api/admin/catalog/exams/{slug}/sections', json={'name': 'Chapter-wise', 'description': '', 'layout': 'chapters', 'kind': 'chapters'})
        chap = J(r).get('id'); print('chapter section', r.status_code, chap, r.text[:160], flush=True)
        await structure.exams.update_one({'_id': slug}, {'$set': {'shown': True}})
        f = {'slug': slug, 'section': sec, 'chapters': chap}
        f['held'] = await book(own, sec, 'HELD', broken=True)
        f['draft'] = await book(own, sec, 'DRAFT', long=True)
        bid, mids = await chapters(own, chap, 'BOXED')
        f['boxed'] = [bid, mids[0]]; f['boxed_small'] = [bid, mids[-1]]
        bid, mids = await chapters(own, chap, 'BOXEDHELD', stray=True)
        f['boxed_held'] = [bid, mids[0]]
        # A second copy, so the fix can be saved once on a desktop and once on a phone.
        bid, mids = await chapters(own, chap, 'BOXEDHELD2', stray=True)
        f['boxed_held_mob'] = [bid, mids[0]]
        r = await own.post(M + '/status', json={'items': [{'kind': 'book_mock', 'id': f['boxed'][1]}], 'to': 'live'}); await drain()
        f['live_set'] = (await BM.find_one({'_id': f['boxed'][1]})).get('set_id'); print('LIVE status', r.status_code, r.text[:300], f['live_set'], flush=True)
        await asyncio.sleep(2); await structure.visibility(force=True)
        if f['live_set']:
            s = await DB.tejas_sets.find_one({'id': f['live_set']}, {'_id': 0, 'questions': 1})
            print('SET pieces', [(q['number'], q['type'], [(c['part'], c['w'], c['h']) for c in q.get('c_refs', [])]) for q in s['questions']], flush=True)
            r = await start(stu, f['live_set']); a = J(r); print('START done', r.status_code, r.text[:200], flush=True)
            await stu.post(f"/api/attempts/{a['id']}/begin"); await asyncio.sleep(.2)
            f['done_attempt'] = a['id']
            f['submit'] = (await stu.post(f"/api/attempts/{a['id']}/submit")).status_code
            r = await start(stu, f['live_set']); f['active_attempt'] = J(r).get('id'); print('START active', r.status_code, r.text[:160], flush=True)
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
