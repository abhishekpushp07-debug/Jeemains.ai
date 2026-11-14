"""TEST-ONLY iteration 179: books read by an older page reader are re-read automatically and safely.
Isolated disposable DB via iso_harness_book170 (storage + AI mocked). Checks: old native pages re-read, owner repairs and
published-mock pages kept, no duplicate mocks, no AI allowance, book not failed.
Run: cd /app/backend && python tests/reread_iso179.py   (prints PASS/FAIL, drops its DB)
"""
import asyncio, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from book_publishing_iso170 import H, mkstaff, build_pdf, q3, upload, complete, drain, check, RESULTS  # noqa: E402
from tejas import structure, book_worker  # noqa: E402
from tejas.book_reader import READER_VERSION  # noqa: E402

PAGES, MOCKS = H.TDB.tejas_book_pages, H.TDB.tejas_book_mocks


async def age(bid):
    await PAGES.update_many({'book_id': bid}, {'$set': {'provenance.reader': 'old', 'text': 'OLD READER TEXT'}})
    await H.TDB.tejas_books.update_one({'_id': bid}, {'$set': {'payload.reader_version': 'old', 'state': 'attention_needed'}})


async def main():
    check('no customer DB handles', not H.leftover_real_handles(), H.leftover_real_handles())
    await structure.seed()
    own, _ = await mkstaff('owner', 'own179')
    mocks = [{'n': 1, 'qs': q3('R1'), 'keys': [(1, 'B'), (2, 'B'), (3, 'C')]}, {'n': 2, 'qs': q3('R2'), 'keys': [(1, 'B'), (2, 'B'), (3, 'C')]}]
    b = await upload(own, build_pdf(mocks), 'TEST_QA179 Reread', section_id='bitsat:mocks'); bid = b['id']
    r, view = await complete(own, bid)
    check('book read natively: 2 ready mocks', [m['state'] for m in view['mocks']] == ['ready', 'ready'], [m['state'] for m in view['mocks']])
    total = await PAGES.count_documents({'book_id': bid}); mock_ids = sorted([m['id'] for m in view['mocks']])

    # --- case A: nothing published; one owner-repaired page
    await age(bid)
    first = await PAGES.find_one({'book_id': bid}, sort=[('number', 1)])
    await PAGES.update_one({'_id': first['_id']}, {'$set': {'provenance': {'kind': 'owner_repair'}, 'text': 'OWNER FIX'}})
    await book_worker.recover(); await drain()
    book = await H.TDB.tejas_books.find_one({'_id': bid})
    check('reader version upgraded', book['payload'].get('reader_version') == READER_VERSION, book['payload'].get('reader_version'))
    check('book not failed after re-read', book['state'] in ('ready', 'attention_needed', 'published'), (book['state'], book['payload'].get('message')))
    check('page count unchanged', await PAGES.count_documents({'book_id': bid}) == total, total)
    check('old native pages re-read', await PAGES.count_documents({'book_id': bid, 'text': 'OLD READER TEXT'}) == 0)
    check('owner repair kept', (await PAGES.find_one({'_id': first['_id']}))['text'] == 'OWNER FIX')
    check('no duplicate mocks', sorted([m['_id'] async for m in MOCKS.find({'book_id': bid})]) == mock_ids)
    check('no AI allowance created', await H.TDB.tejas_book_allowances.count_documents({'book_id': bid}) == 0)

    # --- case B: mock 1 published; its pages must not change under students
    view = (await own.get(f'/api/admin/books/{bid}')).json(); mid = {m['label']: m['id'] for m in view['mocks']}
    await own.post(f'/api/admin/books/{bid}/control', json={'revision': view['revision'], 'action': 'publish_ready', 'mock_id': mid['Mock 1']}); await drain()
    m1 = await MOCKS.find_one({'_id': mid['Mock 1']})
    check('mock 1 published', m1.get('published_generation', 0) > 0, m1.get('state'))
    kept = sorted({n for v in m1['pages'].values() for n in v})
    await age(bid)
    await book_worker.recover(); await drain()
    left = await PAGES.count_documents({'book_id': bid, 'number': {'$in': kept}, 'text': 'OLD READER TEXT'})
    check('published mock pages untouched', left == len(kept) and len(kept) > 0, (left, kept))
    rest = await PAGES.count_documents({'book_id': bid, 'number': {'$nin': kept}, 'provenance.kind': 'native', 'text': 'OLD READER TEXT'})
    check('other native pages re-read', rest == 0, rest)
    check('owner repair still kept on second re-read', (await PAGES.find_one({'_id': first['_id']}))['provenance']['kind'] == 'owner_repair')
    m1b = await MOCKS.find_one({'_id': mid['Mock 1']})
    check('published mock generation unchanged', m1b.get('published_generation') == m1.get('published_generation'), (m1b.get('published_generation'), m1.get('published_generation')))
    check('no duplicate mocks after second re-read', await MOCKS.count_documents({'book_id': bid}) == 2)


async def run():
    try:
        await main()
    except Exception as e:
        import traceback; traceback.print_exc(); check('completed without exception', False, repr(e))
    finally:
        await H.tdbmod.client.drop_database(H.TEST_DB)
        print('dropped', H.TEST_DB)
        f = [r for r in RESULTS if not r[1]]
        print(f'TOTAL {len(RESULTS)} PASS {len(RESULTS) - len(f)} FAIL {len(f)}')
        for x in f: print('  FAILED', x[0], '::', x[2])

if __name__ == '__main__':
    asyncio.run(run())
