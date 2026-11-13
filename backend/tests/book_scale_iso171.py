"""TEST-ONLY iteration 171: limits removal (100 MB only, no page / mock cap) + scale architecture.
Isolated DB + MOCKED storage/AI via iso_harness_book170 (imported through book_publishing_iso170); REAL sealed PDF worker; real JWT.
Run: cd /app/backend && python tests/book_scale_iso171.py <group ...>   groups: size key3 pages large cache lease patho
"""
import asyncio, hashlib, json, math, os, resource, sys, time, uuid
import book_publishing_iso170 as T  # noqa (harness)
from book_publishing_iso170 import H, J, check, drain, mkstaff, client, upload, put_part, OUT, RESULTS
import fitz
from fastapi import HTTPException
from tejas import book_worker as BW, book_store as BS, book_reader as BR, book_imports as BI


async def _enqueue_only(book, bg): await BS.enqueue_book(book)
STEPWISE = {'on': False}
_real_dispatch = BI.dispatch
async def _dispatch(book, bg):
    return await (_enqueue_only if STEPWISE['on'] else _real_dispatch)(book, bg)
BI.dispatch = _dispatch

INSTR = ['JEE Main Instructions', 'Duration: 180 minutes', 'Total Questions: {n}', 'Correct: +4', 'Wrong: -1',
         'Unanswered: 0', 'All questions are compulsory', 'No worked solutions; answer key only.']
ANS = 'ABCD'


def noise_png(side=420):
    return fitz.Pixmap(fitz.csRGB, side, side, os.urandom(side * side * 3), False).tobytes('png')


def big_pdf(nums, qper, key_heading='Answer Key', images=False, contents=True):
    """Per mock: instruction page, qper question pages (one Q each), key page. Optional incompressible image per Q/key page."""
    d = fitz.open()
    if contents:
        p = d.new_page(); p.insert_text((40, 60), 'Contents', fontsize=14)
    for n in nums:
        p = d.new_page(); p.insert_text((40, 60), f'Mock Test {n}', fontsize=14); y = 90
        for ln in INSTR: p.insert_text((40, y), ln.format(n=qper), fontsize=11); y += 20
        for i in range(1, qper + 1):
            p = d.new_page(); p.insert_text((40, 60), 'Physics', fontsize=13)
            p.insert_text((40, 100), f'Q{i}. M{n} question {i}: choose the right value.', fontsize=11); y = 120
            for lab in ANS: p.insert_text((60, y), f'({lab}) value {lab}{i}', fontsize=11); y += 18
            if images: p.insert_image(fitz.Rect(100, 520, 400, 780), stream=noise_png())
        p = d.new_page(); p.insert_text((40, 60), key_heading.format(n=n), fontsize=13); y = 100
        for i in range(1, qper + 1): p.insert_text((40, y), f'Q{i}. ({ANS[(n + i) % 4]})', fontsize=11); y += 20
        if images: p.insert_image(fitz.Rect(100, 520, 400, 780), stream=noise_png())
    raw = d.tobytes(garbage=0, deflate=False); d.close()
    return raw


def want_keys(n, qper): return [ANS[(n + i) % 4] for i in range(1, qper + 1)]


async def view(c, bid): return (await c.get(f'/api/admin/books/{bid}')).json()


async def drain_stats(bid, limit=3000):
    steps = []
    while len(steps) < limit:
        j = await H.TDB.tejas_jobs.find_one({'kind': 'book_step', 'status': 'queued'}, sort=[('created_at', 1)])
        if not j: break
        t = time.time(); await J.run_job(j['id'], drain=False); dt = time.time() - t
        b = await H.TDB.tejas_books.find_one({'_id': bid})
        pub = await H.TDB.tejas_sets.count_documents({'book_import_id': bid, 'status': 'published'})
        steps.append((round(dt, 2), b['payload'].get('read_pages'), b['state'], pub))
    return steps


async def complete_stats(c, bid):
    t = time.time(); r = await c.post(f'/api/admin/books/{bid}/complete'); steps = await drain_stats(bid)
    return r, steps, time.time() - t


def summarize(name, steps, total):
    reads = [s[0] for s in steps if s[2] == 'reading']
    print(f'{name}: steps={len(steps)} total={total:.1f}s max_step={max([s[0] for s in steps] or [0]):.2f}s '
          f'read_steps={len(reads)} avg_read={sum(reads) / max(1, len(reads)):.2f}s maxrss_self={resource.getrusage(resource.RUSAGE_SELF).ru_maxrss // 1024}MB '
          f'maxrss_children={resource.getrusage(resource.RUSAGE_CHILDREN).ru_maxrss // 1024}MB', flush=True)


async def student():
    stu = client(); phone = '97' + str(uuid.uuid4().int)[:8]
    r = await stu.post('/api/auth/phone/signup', json={'phone': phone, 'pin': '4826', 'confirm_pin': '4826'})
    assert r.status_code == 200, r.text
    return stu


# ---------------- size limit 100 MiB
async def g_size(own):
    sha = hashlib.sha256(b'x').hexdigest(); base = {'filename': 'a.pdf', 'title': 'TEST_QA171 size', 'sha256': sha, 'rights_confirmed': True}
    r = await own.post('/api/admin/books', json={**base, 'size': 100 * 1024 * 1024})
    check('exactly 100 MiB accepted (200)', r.status_code == 200, (r.status_code, r.text[:200]))
    if r.status_code == 200: check('100 MiB book exposes 200 expected parts via chunk_size', math.ceil(100 * 1024 * 1024 / r.json()['chunk_size']) == 200, r.json().get('chunk_size'))
    r = await own.post('/api/admin/books', json={**base, 'sha256': hashlib.sha256(b'y').hexdigest(), 'size': 100 * 1024 * 1024 + 1})
    check('100 MiB + 1 rejected 422', r.status_code == 422, (r.status_code, r.text[:200]))
    r = await own.post('/api/admin/books', json={**base, 'sha256': hashlib.sha256(b'z').hexdigest(), 'size': 60 * 1024 * 1024})
    check('60 MB (previously >50MB) accepted', r.status_code == 200, r.status_code)
    lim = (await own.get('/api/admin/books')).json().get('limits')
    check('listing limits bytes=100MiB pages=None mocks=None', lim == {'bytes': 104857600, 'pages': None, 'mocks': None}, lim)
    src = open('/app/frontend/src/components/books/BookUpload.js').read()
    check('frontend copy: 100 MB message + no page/mock limit', 'Choose a PDF within 100 MB.' in src and 'no page or mock limit' in src and '100*1024*1024' in src.replace(' ', ''), 'copy missing')


# ---------------- 3-digit mock labels in key headings
async def g_key3(own):
    for h in ('Answer Key - Mock Test 9', 'Answer Key - Mock Test 100', 'Solutions for Mock Test 120', 'Answer Key: Mock Test 99'):
        print('ROLE.fullmatch', repr(h), bool(BR.ROLE.fullmatch(h)))
    check('ROLE recognises "Answer Key - Mock Test 100" (3-digit)', bool(BR.ROLE.fullmatch('Answer Key - Mock Test 100')), 'regex mock number \\d{1,2}')
    for heading, tag in (('Answer Key', 'plain'), ('Answer Key - Mock Test {n}', 'labelled')):
        nums = [9, 99, 100, 101]
        raw = big_pdf(nums, 2, key_heading=heading)
        b = await upload(own, raw, f'TEST_QA171 key3 {tag}'); _, steps, tt = await complete_stats(own, b['id'])
        v = await view(own, b['id']); st = {m['label']: m['state'] for m in v['mocks']}
        check(f'[{tag} key heading] mocks 9/99/100/101 detected with distinct labels', sorted(st) == sorted(f'Mock {n}' for n in nums), st)
        bad = {m['label']: m['issues'][:2] for m in v['mocks'] if m['state'] != 'published'}
        check(f'[{tag} key heading] all 4 published (3-digit included)', not bad, bad)


# ---------------- >1000 pages, >50 mocks
async def g_pages(own):
    NM, QP = 150, 8; STEPWISE['on'] = True
    nums = list(range(1, NM + 1)); t = time.time(); raw = big_pdf(nums, QP); total_pages = 1 + NM * (QP + 2)
    print(f'built {total_pages}-page PDF {len(raw) / 1e6:.1f}MB in {time.time() - t:.1f}s', flush=True)
    b = await upload(own, raw, 'TEST_QA171 Big'); bid = b['id']
    r, steps, tt = await complete_stats(own, bid); summarize('1501p/150m auto', steps, tt)
    v = await view(own, bid)
    check(f'{total_pages}-page book pages/read_pages complete', v['pages'] == total_pages and v['read_pages'] == total_pages, (v['pages'], v['read_pages'], v['state'], v['message']))
    check('every page persisted', await H.TDB.tejas_book_pages.count_documents({'book_id': bid}) == total_pages)
    reads = [s[1] for s in steps if s[1] is not None]
    incs = [b2 - a for a, b2 in zip([0] + reads, reads) if b2 != a]
    check('reading advanced in batches of <=20 pages', incs and max(incs) <= 20 and sum(incs) == total_pages, incs[:5])
    bad_pages = await H.TDB.tejas_book_pages.find({'book_id': bid, 'issues': {'$regex': '1,?000'}}, {'number': 1, 'issues': 1}).to_list(5)
    check('no 1000-page error on any page', not bad_pages and '1,000' not in v['message'] and '1000' not in v['message'], bad_pages)
    labels = [m['label'] for m in v['mocks']]
    check('150 mocks detected, distinct, book order (incl 3-digit)', labels == [f'Mock {n}' for n in nums], labels[:3] + labels[-3:])
    cnt = v['counts']; check('all 150 clean mocks published', cnt['published'] == NM and v['state'] == 'published', (cnt, v['state'], v['message']))
    pubs = [s[3] for s in steps]; deltas = [b2 - a for a, b2 in zip([0] + pubs, pubs)]
    check('publication in batches of max 5 per step with re-enqueue', max(deltas) <= 5 and sum(1 for d in deltas if d > 0) >= NM // 5, (max(deltas), deltas[-40:]))
    wrong = []
    for m in v['mocks']:
        s = await H.TDB.tejas_sets.find_one({'id': m['set_id']}); n = int(m['label'].split()[1])
        if [q['answer'] for q in s['questions']] != want_keys(n, QP) or not all(f'M{n} question' in q['text'] for q in s['questions']) or s['mock_number'] != n: wrong.append(m['label'])
    check('every mock: own questions + correct key pairing + mock_number', not wrong, wrong[:5])
    pl = (await own.get(f'/api/admin/books/{bid}/pages', params={'page': 41})).json()
    check('page list pagination p41 -> pages 1001..1025', [x['number'] for x in pl['items']] == list(range(1001, 1026)) and pl['total'] == total_pages, [x['number'] for x in pl['items']][:3])
    pl = (await own.get(f'/api/admin/books/{bid}/pages', params={'page': 61})).json()
    check('page list last page p61 -> [1501]', [x['number'] for x in pl['items']] == [1501], pl['items'][:1])
    d = (await own.get(f'/api/admin/books/{bid}/pages/1501')).json(); check('page detail 1501 readable (key page)', d.get('number') == 1501 and d.get('classification') == 'answer_key', d.get('classification'))
    r = await own.get(f'/api/admin/books/{bid}/pages/1499/image'); check('page image 1499 PNG', r.status_code == 200 and r.content[:4] == b'\x89PNG', r.status_code)
    stu = await student()
    sd = (await stu.get(f'/api/book-series/{bid}')).json()
    titles = [x.get('title', '') for x in sd.get('items', [])]
    check('series detail lists ALL 150 in book order', sd.get('published_count') == NM and all(t2.endswith(f'Mock {n}') for t2, n in zip(titles, nums)), (sd.get('published_count'), titles[:2], titles[-2:]))
    sl = (await stu.get('/api/book-series')).json(); check('series list published_count 150', any(x['id'] == bid and x['published_count'] == NM for x in sl['items']), sl)
    json.dump({'bid': bid, 'steps': steps}, open(OUT / 'pages171.json', 'w'))
    # ---- Book R: same original, unpublished (auto_publish False) -> repair clip_text, allowance page validation, map-range >1000
    b = await upload(own, raw, 'TEST_QA171 BigR', edition='R', auto_publish=False); rid = b['id']
    r = await own.post(f'/api/admin/books/{rid}/complete'); t = time.time(); steps = await drain_stats(rid, limit=110); summarize('1501p/150m manual', steps, time.time() - t)
    left = await H.TDB.tejas_jobs.count_documents({'kind': 'book_step', 'status': 'queued'}); rb = await H.TDB.tejas_books.find_one({'_id': rid})
    check('auto_publish=False book processing TERMINATES (no endless re-enqueue)', left == 0 and rb['state'] != 'matching', (len(steps), left, rb['state'], rb['payload'].get('message')))
    await H.TDB.tejas_jobs.delete_many({'kind': 'book_step', 'status': 'queued'})  # stop endless loop so remaining checks can run
    v = await view(own, rid); check('R: 150 ready, none published', v['counts']['ready'] == NM and await H.TDB.tejas_sets.count_documents({'book_import_id': rid}) == 0, v['counts'])
    pg = (await own.get(f'/api/admin/books/{rid}/pages/1393')).json()
    q = [x for x in pg['regions'] if x['role'] == 'question'][0]
    q2 = dict(q, text='BOGUS owner typed text')
    t = time.time()
    r = await own.put(f'/api/admin/books/{rid}/pages/1393', json={'revision': pg['revision'], 'classification': pg['classification'], 'regions': [x if x is not q else q2 for x in pg['regions']], 'issues': [], 'note': 'QA171 repair page beyond 1000'})
    print('repair p1393 %.2fs' % (time.time() - t))
    after = (await own.get(f'/api/admin/books/{rid}/pages/1393')).json(); qt = [x for x in after['regions'] if x['role'] == 'question'][0]['text'] if r.status_code == 200 else ''
    check('repair page 1393: text re-clipped from source (batched clip_text)', r.status_code == 200 and 'BOGUS' not in qt and 'M140 question' in qt, (r.status_code, r.text[:150], qt[:80]))
    await drain_stats(rid, limit=3); await H.TDB.tejas_jobs.delete_many({'kind': 'book_step', 'status': 'queued'})
    vv = await view(own, rid)
    r = await own.post(f'/api/admin/books/{rid}/control', json={'revision': vv['revision'], 'action': 'pause'}); check('R pause', r.status_code == 200, r.text[:150])
    vv = await view(own, rid)
    r = await own.post(f'/api/admin/books/{rid}/allowances', json={'revision': vv['revision'], 'purpose': 'reading', 'pages': [1200, 1501], 'max_requests': 2, 'approved': True, 'request_id': 'qa171' + uuid.uuid4().hex[:8]})
    check('AI reading allowance accepts pages 1200/1501 (>1000)', r.status_code == 200, (r.status_code, r.text[:200]))
    vv = await view(own, rid)
    r = await own.post(f'/api/admin/books/{rid}/allowances', json={'revision': vv['revision'], 'purpose': 'reading', 'pages': [1502], 'max_requests': 1, 'approved': True, 'request_id': 'qa171' + uuid.uuid4().hex[:8]})
    check('AI allowance page 1502 outside book -> 422', r.status_code == 422, r.status_code)
    await H.TDB.tejas_book_allowances.delete_many({'book_id': rid})
    vv = await view(own, rid)
    r = await own.post(f'/api/admin/books/{rid}/control', json={'revision': vv['revision'], 'action': 'resume'}); await drain_stats(rid, limit=3); await H.TDB.tejas_jobs.delete_many({'kind': 'book_step', 'status': 'queued'})
    vv = await view(own, rid); t = time.time()
    r = await own.post(f'/api/admin/books/{rid}/map-range', json={'revision': vv['revision'], 'first_page': 2, 'last_page': 1301, 'mock': 'Mock 1', 'subject': 'Physics', 'role': 'question', 'note': 'QA171 map range over 1300 pages'})
    print('map-range 1300 pages %.1fs' % (time.time() - t))
    n = await H.TDB.tejas_book_pages.count_documents({'book_id': rid, 'number': {'$gte': 2, '$lte': 1301}, 'provenance.kind': 'owner_repair'})
    check('map-range pages 2..1301 (>1000) applied to all', r.status_code == 200 and n == 1300, (r.status_code, r.text[:200], n))
    r = await own.post(f'/api/admin/books/{rid}/map-range', json={'revision': (await view(own, rid))['revision'], 'first_page': 1, 'last_page': 1502, 'mock': 'Mock 1', 'role': 'question', 'note': 'QA171 map range beyond end'})
    check('map-range beyond read pages 422', r.status_code == 422, r.status_code)
    await drain_stats(rid, limit=3); await H.TDB.tejas_jobs.delete_many({'kind': 'book_step', 'status': 'queued'}); v = await view(own, rid)
    check('after remap still no publication, Mock 1 held', await H.TDB.tejas_sets.count_documents({'book_import_id': rid}) == 0 and {m['label']: m['state'] for m in v['mocks']}.get('Mock 1') == 'held', v['counts'])


# ---------------- ~100MB realistic file, resumable >100 parts
async def g_large(own):
    STEPWISE['on'] = True
    t = time.time(); raw = big_pdf(range(1, int(os.environ.get('LARGE_MOCKS', '20')) + 1), 8, images=True)
    if os.environ.get('LARGE_EXACT'):  # pad after %%EOF with a PDF comment to EXACTLY 100 MiB
        raw = raw + b'\n%' + b'0' * (100 * 1048576 - len(raw) - 2); assert len(raw) == 100 * 1048576
    total = math.ceil(len(raw) / BS.CHUNK)
    print(f'built large PDF {len(raw) / 1048576:.1f}MiB parts={total} in {time.time() - t:.1f}s', flush=True)
    check('large fixture is 90-100 MiB', 90 * 1048576 <= len(raw) <= 100 * 1048576, len(raw)); NMK = int(os.environ.get('LARGE_MOCKS', '20'))
    b = await upload(own, raw, 'TEST_QA171 Large', parts=[]); bid = b['id']; ch = b['chunk_size']
    first = list(range(0, 150, 1)); t = time.time()
    for n in first: assert (await put_part(own, bid, n, raw[n * ch:(n + 1) * ch])).status_code == 200
    print('uploaded 150 parts %.1fs' % (time.time() - t))
    r = await own.post(f'/api/admin/books/{bid}/complete'); check('complete with missing parts 409', r.status_code == 409, r.status_code)
    v = await view(own, bid); check('GET book shows ALL 150 received parts (>100)', v['received_parts'] == first, len(v['received_parts']))
    missing = sorted(set(range(total)) - set(v['received_parts'])); puts = 0
    for n in missing: assert (await put_part(own, bid, n, raw[n * ch:(n + 1) * ch])).status_code == 200; puts += 1
    check('resume uploads only missing parts', puts == total - 150 and len((await view(own, bid))['received_parts']) == total, (puts, total))
    r = await put_part(own, bid, 3, raw[3 * ch:4 * ch]); check('re-sending an existing identical part is idempotent', r.status_code == 200, r.status_code)
    r, steps, tt = await complete_stats(own, bid); summarize('large ~96MiB 20 mocks', steps, tt)
    print('step times', [s[0] for s in steps])
    check('parts deleted after original stored', await H.TDB.tejas_book_parts.count_documents({'book_id': bid}) == 0)
    src = (await H.TDB.tejas_books.find_one({'_id': bid}))['payload'].get('source_path')
    check('original stored byte-exact in (mocked) storage', src in H.STORE and hashlib.sha256(H.STORE[src]).hexdigest() == hashlib.sha256(raw).hexdigest(), src)
    v = await view(own, bid)
    check(f'large book fully processed and all mocks published', v['read_pages'] == v['pages'] == 1 + NMK * 10 and v['counts']['published'] == NMK, (v['state'], v['counts'], v['message'][:150], [m['issues'][:1] for m in v['mocks'] if m['issues']][:3]))
    check('no single step > 120s', max(s[0] for s in steps) < 120, max(s[0] for s in steps))
    check('process maxrss < 2.5GB', resource.getrusage(resource.RUSAGE_SELF).ru_maxrss < 2.5 * 1024 * 1024, resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)
    # concurrent owner reads while worker idle/large
    m = v['mocks'][0]; md = (await own.get(f"/api/admin/books/{bid}/mocks/{m['id']}")).json()
    print('mock detail keys', list(md)[:12])


# ---------------- original cache + integrity + concurrency
async def g_cache(own):
    STEPWISE['on'] = True; import tejas_storage as TS
    raw = big_pdf(range(1, 5), 6); b = await upload(own, raw, 'TEST_QA171 Cache'); bid = b['id']
    await own.post(f'/api/admin/books/{bid}/complete')
    j = await H.TDB.tejas_jobs.find_one({'kind': 'book_step', 'status': 'queued'})
    if j: await J.run_job(j['id'], drain=False)
    bk = BS.Book.from_mongo(await H.TDB.tejas_books.find_one({'_id': bid})); sha = bk.payload['sha256']
    check('first step read 20 of 33 pages', bk.payload.get('read_pages') == 20 and bk.payload['pages'] == 33, (bk.payload.get('read_pages'), bk.payload.get('pages')))
    p = await BS.original(bk); check('original() returns on-disk cache path with exact size', p.exists() and p.stat().st_size == len(raw) and p.parent == BS.CACHE, str(p))
    p.unlink(); p2 = await BS.original(bk)
    check('deleted cache re-downloaded from storage and sha verified', p2.exists() and hashlib.sha256(p2.read_bytes()).hexdigest() == sha)
    path = bk.payload['source_path']; good = H.STORE[path]; H.STORE[path] = good[:-10] + b'CORRUPTED!'; p2.unlink(); TS._source_cache.remove(path)  # simulate fresh process (in-memory transport cache)
    try: await BS.original(bk); check('corrupted storage raises integrity error', False, 'no error')
    except ValueError as e: check('corrupted storage raises integrity error', 'integrity' in str(e), e)
    j = await H.TDB.tejas_jobs.find_one({'kind': 'book_step', 'status': 'queued'})
    if j: await J.run_job(j['id'], drain=False)
    v = await view(own, bid)
    check('corrupted original holds book with integrity message, nothing published', v['state'] == 'failed' and 'integrity' in v['message'] and await H.TDB.tejas_sets.count_documents({'book_import_id': bid}) == 0 and v['read_pages'] == 20, (v['state'], v['message'], v['read_pages']))
    H.STORE[path] = good; TS._source_cache.remove(path)
    r = await own.post(f'/api/admin/books/{bid}/control', json={'revision': v['revision'], 'action': 'retry'}); check('retry after storage restored 200', r.status_code == 200, r.text[:200])
    # concurrent owner page images while worker runs
    async def reads():
        out = []
        for n in (2, 5, 9, 30, 33):
            out.append(await own.get(f'/api/admin/books/{bid}/pages/{n}/image'))
        return out
    STEPWISE['on'] = False
    res = await asyncio.gather(drain(), reads(), reads())
    codes = [x.status_code for grp in res[1:] for x in grp]
    check('concurrent page-image requests during worker OK', all(c == 200 for c in codes), codes)
    await drain(); v = await view(own, bid)
    check('retry resumed from saved pages and published 4 mocks', v['counts']['published'] == 4 and v['read_pages'] == 33, (v['state'], v['counts'], v['message']))
    m = v['mocks'][0]; md = (await own.get(f"/api/admin/books/{bid}/mocks/{m['id']}")).json()
    qs = md.get('questions') or (md.get('mock') or {}).get('questions') or []
    if qs:
        qid = qs[0]['id']; codes = await asyncio.gather(*[own.get(f"/api/admin/books/{bid}/mocks/{m['id']}/questions/{qid}/asset/question/0") for _ in range(4)])
        print('preview-crop codes', [c.status_code for c in codes])
        for f in BS.CACHE.glob(f'{sha}.pdf'): f.unlink()
        codes2 = await asyncio.gather(*[own.get(f'/api/admin/books/{bid}/pages/{n}/image') for n in (3, 4, 6, 7)])
        check('concurrent cold-cache page images all OK (re-download race)', all(c.status_code == 200 for c in codes2), [c.status_code for c in codes2])


# ---------------- lease 409 during publish must not hold mocks
async def g_lease(own):
    raw = big_pdf(range(1, 4), 2); b = await upload(own, raw, 'TEST_QA171 Lease'); bid = b['id']
    real = BW.publish_ready; calls = {'n': 0}
    async def flaky(book, token, source, mid=None):
        calls['n'] += 1
        if calls['n'] == 2: raise HTTPException(409, 'Book processing lease expired. Retry from saved progress.')
        return await real(book, token, source, mid)
    BW.publish_ready = flaky
    try:
        await own.post(f'/api/admin/books/{bid}/complete'); await drain()
    finally: BW.publish_ready = real
    v = await view(own, bid); st = {m['label']: (m['state'], m['issues'][:1]) for m in v['mocks']}
    check('lease 409 mid-publication: no mock wrongly held', not any(s == 'held' for s, _ in st.values()) and v['state'] == 'failed', (v['state'], v['message'], st))
    r = await own.post(f'/api/admin/books/{bid}/control', json={'revision': v['revision'], 'action': 'retry'}); await drain()
    v = await view(own, bid); check('retry resumes and publishes all 3', v['counts']['published'] == 3 and v['state'] == 'published', (r.status_code, v['state'], v['counts']))


# ---------------- pathological page: batch crash -> per-page fallback
async def g_patho(own):
    raw = big_pdf(range(1, 4), 3); b = await upload(own, raw, 'TEST_QA171 Patho'); bid = b['id']
    BAD = 4  # a question page of Mock 1 (page1 contents, 2 instr, 3..5 questions, 6 key)
    real_many, real_one = BW.inspect_many, BW.inspect
    def many(source, items, size=10):
        if any(i.get('page') == BAD for i in items): raise ValueError('PDF processing stopped safely. Original upload is retained.')
        return real_many(source, items, size)
    def one(source, action='info', page=None, rect=None):
        if page == BAD: raise ValueError('QA171 pathological page crashed the parser')
        return real_one(source, action, page, rect)
    BW.inspect_many, BW.inspect = many, one
    try:
        await own.post(f'/api/admin/books/{bid}/complete'); await drain()
    finally: BW.inspect_many, BW.inspect = real_many, real_one
    v = await view(own, bid)
    pages = await H.TDB.tejas_book_pages.find({'book_id': bid}).sort('number', 1).to_list(None)
    with_issue = [p['number'] for p in pages if p.get('issues')]
    check('only pathological page has parser issue; all pages persisted', len(pages) == v['pages'] == 16 and with_issue == [BAD] and 'pathological' in pages[BAD - 1]['issues'][0], (len(pages), with_issue))
    st = {m['label']: m['state'] for m in v['mocks']}
    check('Mock 1 held, Mocks 2/3 published', st.get('Mock 1') == 'held' and st.get('Mock 2') == 'published' and st.get('Mock 3') == 'published', st)


GROUPS = {'size': g_size, 'key3': g_key3, 'pages': g_pages, 'large': g_large, 'cache': g_cache, 'lease': g_lease, 'patho': g_patho}


async def run(names):
    try:
        own, _ = await mkstaff('owner', 'owner171')
        for n in names:
            t = time.time(); print('=== group', n, flush=True)
            try: await GROUPS[n](own)
            except Exception as e:
                import traceback; traceback.print_exc(); check(f'group {n} completed without exception', False, repr(e))
            print(f'=== group {n} {time.time() - t:.1f}s', flush=True)
    finally:
        await H.tdbmod.client.drop_database(H.TEST_DB)
        print('dropped', H.TEST_DB)
        f = [r for r in RESULTS if not r[1]]
        print(f'TOTAL {len(RESULTS)} PASS {len(RESULTS) - len(f)} FAIL {len(f)}')
        json.dump(RESULTS, open(OUT / ('results171_' + '_'.join(names) + '.json'), 'w'), indent=1)

if __name__ == '__main__':
    asyncio.run(run(sys.argv[1:] or ['size']))
