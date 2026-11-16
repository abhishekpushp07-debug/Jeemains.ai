"""TEST-ONLY iteration 190: owner's 640-page chapter-wise BITSAT maths PDF (bookmarks: Questions / Answer key / Solutions per chapter).
Run: cd /app/backend && python tests/maths_bookmarks_iso190.py /tmp/maths.pdf   (isolated DB, storage + AI mocked; drops its DB at end)
Never prints question/solution text of the owner's PDF.
"""
import asyncio, sys, time
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import book_publishing_iso170 as T  # noqa: E402  (rebinds DB + mocks storage/AI first)
from book_publishing_iso170 import H, check, mkstaff, upload, complete, drain, RESULTS  # noqa: E402
from tejas import structure, book_worker  # noqa: E402
from tejas.book_reader import READER_VERSION  # noqa: E402
from tejas.book_store import identity  # noqa: E402

DB = H.TDB
SRC = sys.argv[1] if len(sys.argv) > 1 else '/tmp/maths.pdf'
NAMES_FIRST = ['Sets Relations & Functions', 'Complex Numbers']


async def mocks(bid):
    return await DB.tejas_book_mocks.find({'book_id': bid}).sort('order', 1).to_list(500)


def summary(ms):
    return [(m['label'], (m.get('chapter') or {}).get('title'), m['state'], len(m['questions']), len(m['issues'])) for m in ms]


async def main():
    await H.tdbmod.indexes(); await structure.seed()
    own, _ = await mkstaff('owner', 'own')
    raw = Path(SRC).read_bytes()
    try:
        # 1. Fresh upload, chapter-wise BITSAT, Mathematics.
        t0 = time.time()
        b = await upload(own, raw, 'bitsat maths final', section_id='bitsat:chapters', subject='Mathematics')
        bid = b['id']
        await complete(own, bid); await drain(5000)
        print('drain seconds', round(time.time() - t0))
        book = await DB.tejas_books.find_one({'_id': bid}); p = book['payload']
        check('book reader_version 4', p.get('reader_version') == READER_VERSION == 4, p.get('reader_version'))
        check('plan from bookmarks at receive', p.get('plan_source') == 'bookmarks' and len(p.get('chapter_plan') or []) == 96, (p.get('plan_source'), len(p.get('chapter_plan') or [])))
        ms = await mocks(bid)
        print('MOCKS', summary(ms))
        check('32 chapter mocks', len(ms) == 32, len(ms))
        titles = [(m.get('chapter') or {}).get('title') for m in ms]
        check('chapter names from bookmarks', titles[:2] == NAMES_FIRST and titles[-2:] == ['Linear Programming', 'Mathematical Modelling'], titles)
        held = [m for m in ms if m['state'] == 'held']
        check('only Mathematical Induction held', [(m.get('chapter') or {}).get('title') for m in held] == ['Mathematical Induction'], [(m.get('chapter') or {}).get('title') for m in held])
        if held:
            print('held issues', held[0]['issues'][:4])
            check('held reason is Q37/Q38 crop only', all('Q37' in i or 'Q38' in i for i in held[0]['issues']), held[0]['issues'][:4])
        ok = [m for m in ms if m['state'] in ('ready', 'published')]
        check('31 ready/published', len(ok) == 31, [m['state'] for m in ms])
        check('every mock 50 questions', all(len(m['questions']) == 50 for m in ms), [len(m['questions']) for m in ms])
        worked = all(q.get('solution_kind') == 'supplied_worked' and 'does not contain a worked solution' not in str(q.get('solution', '')) for m in ok for q in m['questions'])
        check('original worked solutions on every question', worked, {q.get('solution_kind') for m in ok for q in m['questions']})
        check('every question has answer A-D', all(q.get('answer') in ('A', 'B', 'C', 'D') for m in ms for q in m['questions']), {q.get('answer') for m in ms for q in m['questions']})
        q = {(m.get('chapter') or {}).get('title'): [x.get('answer') for x in m['questions'][:2]] for m in ms}
        check('Sets Q1=B Q2=D', q.get('Sets Relations & Functions') == ['B', 'D'], q.get('Sets Relations & Functions'))
        check('Complex Q1=B Q2=D', q.get('Complex Numbers') == ['B', 'D'], q.get('Complex Numbers'))
        unresolved = await DB.tejas_book_pages.count_documents({'book_id': bid, 'classification': 'unresolved'})
        check('no unresolved pages', unresolved == 0, unresolved)
        print('book state', book['state'], 'metrics', p.get('metrics'))

        # 2. Upgrade path: the same book as the OLD reader (v3) left it.
        await DB.tejas_book_mocks.delete_many({'book_id': bid})
        await DB.tejas_book_pages.update_many({'book_id': bid}, {'$set': {'provenance.reader': 3}})
        await DB.tejas_books.update_one({'_id': bid}, {'$set': {'payload.reader_version': 3, 'state': 'attention_needed'}, '$unset': {'payload.chapter_plan': '', 'payload.plan_source': ''}})
        base = dict(book_id=bid, revision=0, generation=1, rules={}, questions=[], history=[], missed_release=False, original_solution_identities=[],
                    release_override=False, publish_hold='', publish_requested=False, release_at=None, series_date=None, series_id=None, archived=False, deleted=False, live_exam=False, chapter={})
        old = [('Sets Relations & Functions', 'held', 0, None, {'question': [3, 4]}), ('Differentiability)', 'held', 0, None, {'solution': [250]}),
               ('Complex Numbers', 'published', 1, 'TEST_set_x', {'question': [22, 23]})]
        for i, (label, state, pg, sid, pages) in enumerate(old, 1):
            await DB.tejas_book_mocks.insert_one({'_id': identity(bid, label), **base, 'label': label, 'order': i, 'state': state, 'issues': ['old'] if state == 'held' else [],
                                                  'published_generation': pg, 'set_id': sid, 'pages': pages})
        await DB.tejas_jobs.delete_many({'kind': 'book_step', 'set_id': bid})
        r = await book_worker.step({'payload': {'book_id': bid}})
        print('step ->', r)
        book = await DB.tejas_books.find_one({'_id': bid}); p = book['payload']
        check('upgrade: reader_version 4 + bookmarks plan', p.get('reader_version') == 4 and p.get('plan_source') == 'bookmarks' and len(p.get('chapter_plan') or []) == 96, (p.get('reader_version'), p.get('plan_source')))
        labels = {m['label'] for m in await mocks(bid)}
        check('upgrade: never-released old-label mocks deleted', 'Sets Relations & Functions' not in labels and 'Differentiability)' not in labels, labels)
        check('upgrade: published mock kept', 'Complex Numbers' in labels, labels)
        await drain(5000)
        ms = await mocks(bid)
        print('UPGRADE MOCKS', summary(ms))
        chap = [m for m in ms if m['label'].startswith('Chapter ')]
        check('upgrade: 32 new chapter mocks', len(chap) == 32, len(chap))
        check('upgrade: old held labels not recreated', not any(m['label'] in ('Sets Relations & Functions', 'Differentiability)') for m in ms), [m['label'] for m in ms if not m['label'].startswith('Chapter ')])
        pub = [m for m in ms if m['label'] == 'Complex Numbers']
        check('upgrade: published mock untouched', pub and pub[0]['published_generation'] == 1 and pub[0]['set_id'] == 'TEST_set_x', pub[:1] and {k: pub[0][k] for k in ('state', 'published_generation', 'set_id')})
        check('upgrade: only Mathematical Induction held among chapters', [(m.get('chapter') or {}).get('title') for m in chap if m['state'] == 'held'] == ['Mathematical Induction'],
              [((m.get('chapter') or {}).get('title'), m['issues'][:2]) for m in chap if m['state'] == 'held'])
        unresolved = await DB.tejas_book_pages.count_documents({'book_id': bid, 'classification': 'unresolved'})
        check('upgrade: no unresolved pages', unresolved == 0, unresolved)
        print('book state after upgrade', (await DB.tejas_books.find_one({'_id': bid}))['state'])

        # 3. Edge (informational): v3 pages kept across the re-read (pages of a published mock, owner repairs) still carry OLD labels.
        await DB.tejas_book_mocks.delete_many({'book_id': bid})
        await DB.tejas_book_pages.update_many({'book_id': bid}, {'$set': {'provenance.reader': 3}})
        await DB.tejas_book_pages.update_many({'book_id': bid, 'number': {'$in': [22, 23]}}, {'$set': {'regions.$[].mock': 'Complex Numbers'}})
        await DB.tejas_book_pages.update_one({'book_id': bid, 'number': 4}, {'$set': {'regions.$[].mock': 'Sets Relations & Functions', 'provenance.kind': 'owner_repair'}})
        await DB.tejas_books.update_one({'_id': bid}, {'$set': {'payload.reader_version': 3}, '$unset': {'payload.chapter_plan': '', 'payload.plan_source': ''}})
        await DB.tejas_book_mocks.insert_one({'_id': identity(bid, 'Complex Numbers'), **base, 'label': 'Complex Numbers', 'order': 1, 'state': 'published', 'issues': [],
                                              'published_generation': 1, 'set_id': 'TEST_set_x', 'pages': {'question': [22, 23]}})
        await DB.tejas_jobs.delete_many({'kind': 'book_step', 'set_id': bid})
        await book_worker.step({'payload': {'book_id': bid}}); await drain(5000)
        ms = await mocks(bid)
        ch2 = [m for m in ms if m['label'] == 'Chapter 2']
        ch1 = [m for m in ms if m['label'] == 'Chapter 1']
        print('EDGE labels', [m['label'] for m in ms if not m['label'].startswith('Chapter ')])
        print('EDGE chapter2', ch2 and (ch2[0]['state'], len(ch2[0]['questions']), ch2[0]['issues'][:2]))
        print('EDGE chapter1', ch1 and (ch1[0]['state'], len(ch1[0]['questions']), ch1[0]['issues'][:2]))
        print('EDGE old-label repaired mock', [(m['label'], m['state'], len(m['questions'])) for m in ms if m['label'] == 'Sets Relations & Functions'])
    finally:
        await H.tdbmod.client.drop_database(H.TEST_DB)
    failed = [r for r in RESULTS if not r[1]]
    print(f'\n{len(RESULTS) - len(failed)}/{len(RESULTS)} passed')
    sys.exit(1 if failed else 0)

if __name__ == '__main__':
    asyncio.run(main())
