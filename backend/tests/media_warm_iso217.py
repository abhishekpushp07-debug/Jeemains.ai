"""TEST-ONLY (iteration 217): picture pre-warm + publish progress in an isolated DB (storage mocked). Same as media_cdn_iso198 but the paper
uses a 4-option PDF (Phase 1 rule), and checks media.stats['warmed'] after go-Live and after GET /api/sets/{id}, and that the
tejas_publish_progress doc is removed. Run: cd /app/backend && python tests/media_warm_iso217.py"""
import asyncio, sys, time
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import media_cdn_iso198 as C  # noqa: E402
from media_cdn_iso198 import H, mkstaff, client, upload, complete, drain, check, RESULTS, J, student, structure, M, BM, MEDIA  # noqa: E402
from book_publishing_iso170 import build_pdf, q3  # noqa: E402
from tejas.db import db  # noqa: E402


async def paper4(own, stu):
    b = await upload(own, build_pdf([{'n': 1, 'qs': q3('W217'), 'keys': [(1, 'B'), (2, 'B'), (3, 'C')]}]), 'TEST_WARM', section_id='jee-main:mocks')
    await complete(own, b['id']); await drain()
    m = await BM.find_one({'book_id': b['id']}); base = f"/api/admin/books/{b['id']}/mocks/{m['_id']}"
    p = J(await own.get(base + '/problems', params={'all': 'true'}))
    for q in p.get('questions', []):
        p = J(await own.get(base + '/problems', params={'all': 'true'}))
        await own.post(base + '/fix', json={'revision': p['revision'], 'question_id': q['id'], 'response_type': 'mcq', 'option_labels': ['A', 'B', 'C', 'D'], 'answer': 'B', 'complete': True}); await drain()
    w0 = MEDIA.stats['warmed']
    r = await own.post(M + '/status', json={'items': [{'kind': 'book_mock', 'id': m['_id']}], 'to': 'live'}); await drain()
    print('status reply', r.status_code, r.text[:300])
    await asyncio.sleep(3); await structure.visibility(force=True)
    sid = (await BM.find_one({'_id': m['_id']})).get('set_id')
    check('paper built (4 options)', bool(sid), (await BM.find_one({'_id': m['_id']}, {'state': 1, 'issues': 1})))
    if not sid:
        return None
    check('publish progress doc removed after publish', await db.tejas_publish_progress.count_documents({'_id': m['_id']}) == 0, '')
    for _ in range(20):
        if MEDIA.stats['warmed'] > w0: break
        await asyncio.sleep(0.5)
    check('go-Live warms the picture packs (stats.warmed +1)', MEDIA.stats['warmed'] > w0, MEDIA.stats)
    built = MEDIA.stats['built']
    t = time.time(); r = await client().get(f'/api/sets/{sid}'); dt = time.time() - t
    check('GET /api/sets/{id} 200 fast', r.status_code == 200 and dt < 1.5 and J(r).get('id') == sid, (r.status_code, dt))
    await asyncio.sleep(1)
    check('set page within 10 min of warm does not warm again', MEDIA.stats['built'] == built, MEDIA.stats)
    # forget throttle -> set page warms by itself
    MEDIA._warm_at.clear(); MEDIA._parts.data.clear(); MEDIA._parts.size = 0; w1 = MEDIA.stats['warmed']
    await client().get(f'/api/sets/{sid}')
    for _ in range(20):
        if MEDIA.stats['warmed'] > w1: break
        await asyncio.sleep(0.5)
    check('GET /api/sets/{id} warms packs in background', MEDIA.stats['warmed'] > w1 and MEDIA.stats['built'] > built, MEDIA.stats)
    return sid


async def main():
    own, _ = await mkstaff('owner', 'w217'); a = await student('83'); b = await student('82')
    await structure.exams.update_one({'_id': 'jee-main'}, {'$set': {'shown': True}})
    C.paper = paper4
    try:
        await C.links_and_parts(own, a, b)
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
