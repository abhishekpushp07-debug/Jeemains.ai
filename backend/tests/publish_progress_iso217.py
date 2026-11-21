"""TEST-ONLY (iteration 217): publish progress {done,total} visible while a book mock goes Live (crop_ref slowed down), shown in
master type_mocks as publish_progress, removed after. Isolated DB. Run: cd /app/backend && python tests/publish_progress_iso217.py"""
import asyncio, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import media_cdn_iso198 as C  # noqa: E402
from media_cdn_iso198 import H, mkstaff, upload, complete, drain, check, RESULTS, J, structure, M, BM  # noqa: E402
from book_publishing_iso170 import build_pdf, q3  # noqa: E402
from tejas.db import db  # noqa: E402
from tejas import book_publish as BP  # noqa: E402


async def main():
    own, _ = await mkstaff('owner', 'p217')
    await structure.exams.update_one({'_id': 'jee-main'}, {'$set': {'shown': True}})
    b = await upload(own, build_pdf([{'n': 1, 'qs': q3('P217'), 'keys': [(1, 'B'), (2, 'B'), (3, 'C')]}]), 'TEST_PROG', section_id='jee-main:mocks')
    await complete(own, b['id']); await drain()
    m = await BM.find_one({'book_id': b['id']}); base = f"/api/admin/books/{b['id']}/mocks/{m['_id']}"
    p = J(await own.get(base + '/problems', params={'all': 'true'}))
    for q in p.get('questions', []):
        p = J(await own.get(base + '/problems', params={'all': 'true'}))
        await own.post(base + '/fix', json={'revision': p['revision'], 'question_id': q['id'], 'response_type': 'mcq', 'option_labels': ['A', 'B', 'C', 'D'], 'answer': 'B', 'complete': True}); await drain()
    real = BP.crop_ref

    async def slow(*a, **k):
        await asyncio.sleep(2.0); return await real(*a, **k)
    BP.crop_ref = slow
    BP_gate = None
    seen_doc, seen_row = [], []
    async def go_live():
        r = await own.post(M + '/status', json={'items': [{'kind': 'book_mock', 'id': m['_id']}], 'to': 'live'})
        print('status', r.status_code, r.text[:200]); await drain()
    job = asyncio.ensure_future(go_live())
    for _ in range(120):
        d = await db.tejas_publish_progress.find_one({'_id': m['_id']})
        if d: seen_doc.append((d['done'], d['total']))
        rows = J(await own.get(f'{M}/types/jee-main:mocks/mocks')).get('items', [])
        for it in rows:
            if it.get('id') == m['_id'] and it.get('status') == 'publishing' and it.get('publish_progress'):
                seen_row.append(it['publish_progress'])
        if job.done(): break
        await asyncio.sleep(0.4)
    await job; BP.crop_ref = real
    print('doc progress', seen_doc[:8], '... rows', seen_row[:4])
    check('progress doc written while publishing with total>0', any(t > 0 for _, t in seen_doc), seen_doc)
    check('progress done increases', len({d for d, _ in seen_doc}) >= 2, seen_doc)
    check('type_mocks row status publishing carries publish_progress', bool(seen_row), seen_row)
    await asyncio.sleep(1)
    sid = (await BM.find_one({'_id': m['_id']})).get('set_id')
    check('published after progress', bool(sid), '')
    check('progress doc removed', await db.tejas_publish_progress.count_documents({}) == 0, '')


async def run():
    assert not H.leftover_real_handles()
    await H.tdbmod.indexes(); await structure.seed()
    try:
        await main()
    except Exception:
        import traceback; traceback.print_exc(); check('ran', False, 'exception')
    finally:
        await H.tdbmod.client.drop_database(H.TEST_DB)
        for r in RESULTS: print('PASS' if r[1] else 'FAIL', r[0], '' if r[1] else r[2])
        ok = sum(1 for r in RESULTS if r[1]); print(f'TOTAL {len(RESULTS)} PASS {ok} FAIL {len(RESULTS) - ok}')

if __name__ == '__main__':
    asyncio.run(run())
