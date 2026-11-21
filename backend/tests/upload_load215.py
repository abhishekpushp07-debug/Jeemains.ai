"""TEST-ONLY iteration 215: is Super Admin slow while a book is read? Real app over real HTTP (127.0.0.1:8773), disposable DB, storage mocked.
Book 1 (owner's boxed chemistry, 43 MB) is uploaded part by part exactly like the browser; while it is being read and cut, book 2
(AITS maths, 51 MB) is uploaded. A probe opens the Super Admin book list every 0.5 s the whole time. Prints how long every request took.
Run: cd /app/backend && BOOK_LANES=2 BOOK_PAGES=100 python tests/upload_load215.py 600 > /tmp/load215.log 2>&1 &
"""
import asyncio, hashlib, math, os, statistics, sys, time, uuid
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import httpx  # noqa: E402
import book_publishing_iso170 as T  # noqa: E402,F401
from book_publishing_iso170 import H, mkstaff  # noqa: E402
from tejas import structure, book_pdf, book_worker  # noqa: E402
import uvicorn  # noqa: E402

PORT = 8773
if os.environ.get('BOOK_LANES'):
    book_pdf.LANES = int(os.environ['BOOK_LANES'])
if os.environ.get('BOOK_PAGES'):
    book_worker.PAGES_PER_STEP = int(os.environ['BOOK_PAGES'])
ORIGIN = 'https://pdf-engine-v2--49kthst3.preview.emergentagent.com'
T0 = time.time()
LOG = {'probe': [], 'part1': [], 'part2': []}
EVENTS = []


def ev(text):
    EVENTS.append((round(time.time() - T0, 1), text)); print(f'[{time.time() - T0:7.1f}s] {text}', flush=True)


def stats(rows):
    if not rows:
        return 'none'
    d = sorted(r[1] for r in rows)
    bad = sum(1 for r in rows if r[2] != 200)
    return f'n={len(d)} p50={statistics.median(d):.2f}s p95={d[int(.95 * (len(d) - 1))]:.2f}s max={d[-1]:.2f}s >2s={sum(x > 2 for x in d)} errors={bad}'


async def probe(c, stop):
    while not stop.is_set():
        t = time.time()
        try:
            r = await c.get('/api/admin/books'); code = r.status_code
        except Exception as e:  # noqa: BLE001
            code = 'ERR ' + type(e).__name__
        LOG['probe'].append((round(t - T0, 1), time.time() - t, code))
        await asyncio.sleep(.5)


async def send(c, raw, title, sec, key):
    sha = hashlib.sha256(raw).hexdigest()
    r = await c.post('/api/admin/books', json={'filename': title + '.pdf', 'title': title, 'sha256': sha, 'size': len(raw), 'edition': '',
                                              'rights_confirmed': True, 'section_id': sec, 'subject': 'Chemistry' if 'CHEM' in title else 'Mathematics'})
    b = r.json(); b = b.get('data', b) if isinstance(b, dict) else b
    if r.status_code != 200:
        ev(f'{title} create failed {r.status_code} {r.text[:200]}'); return None
    ch = b['chunk_size']; total = math.ceil(len(raw) / ch); ev(f'{title} upload start: {total} parts')
    for n in range(total):
        part = raw[n * ch:(n + 1) * ch]; t = time.time()
        try:
            pr = await c.put(f"/api/admin/books/{b['id']}/parts/{n}", params={'sha256': hashlib.sha256(part).hexdigest()}, content=part,
                             headers={'content-type': 'application/octet-stream'}, timeout=90)
            code = pr.status_code
        except Exception as e:  # noqa: BLE001
            code = 'ERR ' + type(e).__name__
        LOG[key].append((round(t - T0, 1), time.time() - t, code))
        if code != 200:
            ev(f'{title} part {n} -> {code}')
    t = time.time(); r = await c.post(f"/api/admin/books/{b['id']}/complete"); ev(f'{title} complete {r.status_code} in {time.time() - t:.2f}s')
    return b['id']


async def watch(ids, limit):
    last = {}
    while time.time() - T0 < limit:
        for bid in ids:
            if not bid:
                continue
            bk = await H.TDB.tejas_books.find_one({'_id': bid}, {'state': 1, 'payload.message': 1, 'payload.read_pages': 1, 'payload.pages': 1})
            now = (bk['state'], bk['payload'].get('read_pages'))
            if last.get(bid) != now:
                last[bid] = now; ev(f"book {bid[:8]} {bk['state']} read {bk['payload'].get('read_pages')}/{bk['payload'].get('pages')} :: {bk['payload'].get('message', '')[:90]}")
        if all(b and last.get(b, ('',))[0] in ('ready', 'attention_needed', 'published', 'failed') for b in ids):
            return True
        await asyncio.sleep(2)
    return False


async def main():
    limit = int(sys.argv[1]) if len(sys.argv) > 1 else 600
    assert not H.leftover_real_handles()
    await H.tdbmod.indexes(); await structure.seed()
    server = uvicorn.Server(uvicorn.Config(H.app, host='127.0.0.1', port=PORT, log_level='warning', lifespan='off'))
    serving = asyncio.create_task(server.serve())
    try:
        own, _ = await mkstaff('owner', 'load')
        slug = (await own.post('/api/admin/catalog/exams', json={'name': 'LOADX', 'short': 'LX', 'subjects': ['Chemistry', 'Mathematics'], 'color': 'rose'})).json().get('slug')
        chap = (await own.post(f'/api/admin/catalog/exams/{slug}/sections', json={'name': 'Chapter-wise', 'description': '', 'layout': 'chapters', 'kind': 'chapters'})).json().get('id')
        while not server.started:
            await asyncio.sleep(.1)
        c = httpx.AsyncClient(base_url=f'http://127.0.0.1:{PORT}', cookies=dict(own.cookies), headers={'Origin': ORIGIN}, timeout=120)
        ev(f'lanes={book_pdf.LANES} pages_per_step={book_worker.PAGES_PER_STEP} cpus={book_pdf.cpus()}')
        stop = asyncio.Event(); p = asyncio.create_task(probe(c, stop))
        await asyncio.sleep(3)
        raw1 = open('/root/pdfengine/chemistry_chapterwise.pdf', 'rb').read() + b'\n%' + uuid.uuid4().hex.encode()
        raw2 = open('/root/pdfengine/aits_maths.pdf', 'rb').read() + b'\n%' + uuid.uuid4().hex.encode()
        t_idle = len(LOG['probe'])
        b1 = await send(c, raw1, 'TEST_LOAD_CHEM', chap, 'part1'); t_up1 = len(LOG['probe'])
        await asyncio.sleep(20)
        b2 = await send(c, raw2, 'TEST_LOAD_MATH', chap, 'part2'); t_up2 = len(LOG['probe'])
        done = await watch([b1, b2], limit)
        stop.set(); await p
        pr = LOG['probe']
        print('\n==== RESULT lanes', book_pdf.LANES, 'pages/step', book_worker.PAGES_PER_STEP, 'finished' if done else 'TIMED OUT', flush=True)
        print('probe idle        ', stats(pr[:t_idle]))
        print('probe book1 upload', stats(pr[t_idle:t_up1]))
        print('probe while book1 reads + book2 uploads', stats(pr[t_up1:t_up2]))
        print('probe after       ', stats(pr[t_up2:]))
        print('book1 parts       ', stats(LOG['part1']))
        print('book2 parts (book1 being read)', stats(LOG['part2']))
        slow = sorted(pr, key=lambda r: -r[1])[:8]
        print('slowest probes', [(r[0], round(r[1], 2), r[2]) for r in slow])
        for bid in (b1, b2):
            bk = await H.TDB.tejas_books.find_one({'_id': bid})
            ms = await H.TDB.tejas_book_mocks.count_documents({'book_id': bid})
            print('BOOK', bid[:8], bk['state'], bk['payload'].get('read_pages'), '/', bk['payload'].get('pages'), 'mocks', ms, bk['payload'].get('message', '')[:120], flush=True)
        # The screens Super Admin keeps open: the book page (asked every 8 s while working) and the mock type list.
        from tejas.book_store import mocks_for
        from tejas.book_models import Book
        for name, path in (('book page', f'/api/admin/books/{b1}'), ('type list', f'/api/admin/master/types/{chap}/mocks'), ('fix list', '/api/admin/master/fix')):
            ts = []
            for _ in range(5):
                t = time.time(); r = await c.get(path); ts.append(time.time() - t)
            print(f'SCREEN {name}: {r.status_code} {len(r.content) // 1024} KB, best {min(ts):.3f}s worst {max(ts):.3f}s', flush=True)
        book = Book.from_mongo(await H.TDB.tejas_books.find_one({'_id': b1}))
        t = time.time(); full = await mocks_for(book); print(f'OLD book page work (all mocks with every question): {time.time() - t:.3f}s for {len(full)} mocks', flush=True)
        await c.aclose()
    finally:
        server.should_exit = True
        try:
            await asyncio.wait_for(serving, 10)
        except Exception:  # noqa: BLE001
            pass
        assert H.TEST_DB.startswith('tejas_isolated_') and H.TEST_DB != H.REAL_DB
        await H.tdbmod.client.drop_database(H.TEST_DB)
        print('dropped', H.TEST_DB, flush=True)


if __name__ == '__main__':
    asyncio.run(main())
