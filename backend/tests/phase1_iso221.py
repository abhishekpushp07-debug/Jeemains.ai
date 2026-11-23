"""TEST-ONLY iteration 221: Phase 1 re-read guard and busy-PDF handling.
- Master shows "dobara padhi ja rahi hai" data (rereading) for a PDF being read again, hides its old fixes, and refuses Live/Schedule for its mocks.
- A book step that loses its lock (409) is not marked failed: the job waits its turn; after 90 waits it is a normal failure.
Isolated disposable DB via iso_harness_book170 (storage + AI mocked). Run: cd /app/backend && python tests/phase1_iso221.py
"""
import asyncio, sys, time
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from book_publishing_iso170 import H, mkstaff, build_pdf, q3, upload, complete, drain, check, RESULTS  # noqa: E402
from fastapi import HTTPException  # noqa: E402
from tejas import structure, book_worker, jobs as JOBS  # noqa: E402

BOOKS = H.TDB.tejas_books
BUSY = HTTPException(409, 'This book changed or is processing a batch. Reload and retry; saved work is retained.')


async def rereading_view(own, bid):
    await BOOKS.update_one({'_id': bid}, {'$set': {'payload.rereading': True, 'state': 'reading', 'payload.read_pages': 1}})
    d = (await own.get('/api/admin/master/types/bitsat:mocks/mocks')).json()
    mine = [m for m in d['items'] if m.get('book_id') == bid]
    check('type list: both mocks of the PDF listed', len(mine) == 2, [m.get('title') for m in mine])
    check('type list: rereading progress on each mock', all(m.get('rereading', {}).get('read_pages') == 1 and m['rereading'].get('pages', 0) > 0 for m in mine), [m.get('rereading') for m in mine])
    check('type list: old fix count hidden while re-reading', all(m['to_fix'] == 0 for m in mine), [m['to_fix'] for m in mine])
    up = [u for u in d['uploads'] if u['id'] == bid]
    check('type list: the upload says it is re-reading', bool(up) and up[0].get('rereading') is True and up[0].get('active') is True, up)
    s = (await own.get('/api/admin/master/summary')).json()
    check('summary: rereading entry with pages', any(r['book_id'] == bid and r['read_pages'] == 1 and r['pages'] > 0 for r in s.get('rereading', [])), s.get('rereading'))
    f = (await own.get('/api/admin/master/fix')).json()
    check('fix list: rereading entry, its mocks not listed', any(r['book_id'] == bid for r in f['rereading']) and not any(x.get('book_id') == bid for x in f['items'] + f['ready']), (f['rereading'], len(f['items'])))
    return mine


async def guard(own, bid, mine):
    body = {'items': [{'kind': 'book_mock', 'id': mine[0]['id']}], 'to': 'live'}
    r = (await own.post('/api/admin/master/status', json=body)).json()
    check('Live refused while re-reading (Hinglish reason)', r.get('done') == 0 and r['skipped'] and 'dobara padhi' in r['skipped'][0]['reason'], r)
    r = (await own.post('/api/admin/master/status', json={**body, 'to': 'scheduled', 'at': time.time() + 86400})).json()
    check('Schedule refused while re-reading', r.get('done') == 0 and r['skipped'] and 'dobara padhi' in r['skipped'][0]['reason'], r)
    await BOOKS.update_one({'_id': bid}, {'$unset': {'payload.rereading': ''}, '$set': {'state': 'ready'}})
    d = (await own.get('/api/admin/master/types/bitsat:mocks/mocks')).json()
    check('after re-read: no rereading key on the mocks', not any(m.get('rereading') for m in d['items'] if m.get('book_id') == bid))
    r = (await own.post('/api/admin/master/status', json=body)).json()
    check('after re-read: Live accepted again', r.get('done') == 1, r)
    await drain()


async def busy_step(bid):
    await BOOKS.update_one({'_id': bid}, {'$set': {'state': 'reading', 'payload.read_pages': 0}})
    orig = book_worker.fence

    async def lost(book, token): raise BUSY
    book_worker.fence = lost
    raised = None
    try: await book_worker.step({'payload': {'book_id': bid}})
    except HTTPException as e: raised = e.status_code
    finally: book_worker.fence = orig
    b = await BOOKS.find_one({'_id': bid})
    check('lost lock inside a step: 409 goes to the job runner', raised == 409, raised)
    check('lost lock inside a step: book not marked failed', b['state'] != 'failed', (b['state'], b['payload'].get('message')))
    check('lost lock inside a step: lock released', not b.get('lock_token'), b.get('lock_token'))


async def wait_cap(own_id):
    j = await JOBS.enqueue('book_step', own_id, 'bk221', {'key': 'bk221:1', 'book_id': 'bk221'}); orig = book_worker.step

    async def held(job): raise BUSY
    book_worker.step = held
    try:
        await JOBS.run_job(j['id'], drain=False)
        row = await H.TDB.tejas_jobs.find_one({'id': j['id']})
        check('busy PDF: first wait counted, tries kept', row['status'] == 'queued' and row.get('busy_waits') == 1 and row.get('attempts') == 0, {k: row.get(k) for k in ('status', 'busy_waits', 'attempts')})
        await H.TDB.tejas_jobs.update_one({'id': j['id']}, {'$set': {'busy_waits': JOBS.BUSY_WAITS, 'next_run_at': 0}})
        await JOBS.run_job(j['id'], drain=False)
        row = await H.TDB.tejas_jobs.find_one({'id': j['id']})
        check('busy PDF: after 90 waits it counts as a normal try', row.get('attempts') == 1 and row['error'].startswith('Processing could not finish'), {k: row.get(k) for k in ('status', 'busy_waits', 'attempts', 'error')})
    finally: book_worker.step = orig


async def main():
    check('no customer DB handles', not H.leftover_real_handles(), H.leftover_real_handles())
    await structure.seed()
    own, me = await mkstaff('owner', 'own221')
    mocks = [{'n': 1, 'qs': q3('P1'), 'keys': [(1, 'B'), (2, 'B'), (3, 'C')]}, {'n': 2, 'qs': q3('P2'), 'keys': [(1, 'B'), (2, 'B'), (3, 'C')]}]
    b = await upload(own, build_pdf(mocks), 'TEST_QA221 Reread guard', section_id='bitsat:mocks'); bid = b['id']
    _, view = await complete(own, bid)
    check('book read: 2 ready mocks', [m['state'] for m in view['mocks']] == ['ready', 'ready'], [m['state'] for m in view['mocks']])
    mine = await rereading_view(own, bid)
    await guard(own, bid, mine)
    await busy_step(bid)
    await wait_cap(me['id'] if isinstance(me, dict) else me)


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
