"""TEST-ONLY iteration 254 (pocket C1a, "Jod: ek sawaal, ek record"): the real app in a disposable DB (storage mocked, no AI, no network).
Two of the owner's All India papers (Mock 06 and 07, their pages cut out of the owner's AITS book) go into the built-in JEE series, and
chapter 8 of the owner's chemistry book into Chapter-wise, both the usual way (upload -> Draft). Then:
A  before "Jod banao": nothing is made, and the screen says so.
B  "Jod banao": one record per printed address; the paper's question and the chapter's question meet on one record; the AITS question
   gets its chapter; no paper, test, file, attempt or upload is written.
C  pressed again: the same records (made once, never twice).
D  only the owner: no login 401; a reviewer and a student 403; an unknown exam 404.
E  one run at a time: a press while a run is going is told so.
F  the locks: another answer, another kind, other words under the same address are not joined; they go to the owner's list with the reason.
G  "badla hua": a question whose answer changed since the last run is counted once.
H  a paper question without the printed line still has its address (its paper's heading and its number); a chapter question without it
   is counted as "bina pate ke"; a paper question that prints another paper's address goes to the owner's list.
I  the chapter upload is deleted for good: its records stay, with their words, answer and chapter; uploaded again: the same records.
J  another exam has records of its own; the first exam's are not touched.
K  the papers' upload goes to the Library: its records stay.
Run: cd /app/backend && python -u tests/question_records_iso254.py   (drops only its own disposable database)
"""
import asyncio, hashlib, json, re, sys, time, uuid
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import fitz  # noqa: E402
from cut_bridge207 import H, BM, DB, J, mkstaff, client, upload, drain  # noqa: E402
from book_speed211 import chapter8, run_book  # noqa: E402
from source_hidden248 import student  # noqa: E402
from tejas import structure, question_records as QR, question_link as L  # noqa: E402
from tejas.book_store import identity  # noqa: E402

RESULTS = []
AITS = '/root/pdfengine/aits/a.pdf'
API, SLUG = '/api/admin/links/', 'jee-main'
REC, OPS = DB.tejas_question_records, DB.tejas_operations
WATCH = ('tejas_sets', 'tejas_books', 'tejas_book_mocks', 'tejas_book_pages', 'tejas_files', 'tejas_attempts', 'tejas_jobs', 'tejas_packs', 'tejas_series',
         'tejas_catalog_sections', 'tejas_catalog_exams', 'tejas_users')
SOURCE = re.compile(r'(?m)^Source:.*\n')


def check(name, ok, detail=''):
    RESULTS.append((name, bool(ok)))
    print(('PASS ' if ok else 'FAIL ') + name + ('' if ok else ' :: ' + str(detail)[:900]), flush=True)


def aits_slice(first=6, count=2):
    """Mocks `first`.. of the owner's AITS book as a PDF of their own: each is a title page, 75 question pages, its key, 75 solution pages."""
    src = fitz.open(AITS); doc = fitz.open()
    start = 4 + (first - 1) * 152
    doc.insert_pdf(src, from_page=start - 1, to_page=start - 2 + count * 152)
    toc = []
    for i in range(count):
        p = 1 + i * 152
        toc += [[1, f'Mock {first + i:02d}', p], [2, 'Questions', p + 1], [2, 'Answer key', p + 76], [2, 'Solutions', p + 77]]
    doc.set_toc(toc)
    raw = doc.tobytes(garbage=3, deflate=True); doc.close(); src.close()
    return raw + b'\n%' + uuid.uuid4().hex.encode()


async def snap():
    """A fingerprint of everything the join must never write."""
    out = {}
    for n in WATCH:
        h = hashlib.sha256()
        async for d in DB[n].find({}).sort('_id', 1):
            h.update(json.dumps(d, sort_keys=True, default=str).encode())
        out[n] = h.hexdigest()
    return out


async def run(own, slug=SLUG):
    r = await own.post(API + slug + '/run')
    return r, J(r)


async def rows(slug=SLUG):
    return {r['_id']: r async for r in REC.find({'exam_slug': slug})}


def rid(mock, q, slug=SLUG):
    return identity('question-record', slug, 'aitsmock', mock, q)


def same(d):
    return {k: v for k, v in d.items() if k not in ('run', 'updated_at')}


async def drafts(bid):
    out = {}
    async for m in BM.find({'book_id': bid}).sort('order', 1):
        for q in m['questions']:
            a = L.address(q['text'])
            out[a[1:3] if a else ('none', q['id'])] = (m, q)
    return out


async def edit(m, q, **fields):
    """TEST: one field of one Draft question, the way a fix in the Draft changes it (its mock's revision goes up)."""
    await BM.update_one({'_id': m['_id'], 'questions.id': q['id']}, {'$set': {'questions.$.' + k: v for k, v in fields.items()}, '$inc': {'revision': 1}})


async def setup(own):
    t = time.time()
    b = await upload(own, aits_slice(), 'TEST_AITS_06_07', section_id='jee-main:aits')
    await own.post(f"/api/admin/books/{b['id']}/complete"); await drain(100000)
    papers = await BM.find({'book_id': b['id']}).sort('order', 1).to_list(10)
    check("setup: Mock 06 and 07 of the owner's AITS book arrive as two ready Drafts of 75 questions", [(m['label'], m['state'], len(m['questions'])) for m in papers] == [('Mock 6', 'ready', 75), ('Mock 7', 'ready', 75)],
          [(m['label'], m['state'], len(m['questions']), m['issues'][:2]) for m in papers])
    chem, crow, _, _ = await run_book(own, 'jee-main:chapters', chapter8(), 'TEST_CHEM_CH08')
    check("setup: chapter 8 of the owner's chemistry book arrives as a ready Draft of 16 questions", bool(crow) and crow[0]['state'] == 'ready' and len(crow[0]['questions']) == 16,
          [(m['label'], m['state'], len(m['questions']), m['issues'][:2]) for m in crow])
    print(f'  setup: {time.time() - t:.0f} s', flush=True)
    return b['id'], chem


async def made(own, aits, chem):
    P, C = await drafts(aits), await drafts(chem)
    both = set(P) & set(C)
    check('setup: every Draft question prints an address; Mock 06 / Q65 and Mock 07 / Q56 are printed in the papers and in chapter 8',
          len(P) == 150 and not [k for k in list(P) + list(C) if k[0] == 'none'] and {(6, 65), (7, 56)} <= both, (len(P), len(C), sorted(both)))
    r = await own.get(API + SLUG); st = J(r)
    check('A before "Jod banao": the screen says nothing is made yet and names the two uploads it would read; no record exists',
          r.status_code == 200 and st['ran_at'] is None and st['sources'] == 2 and not any(st['counts'].values()) and st['fresh'] is False and st['running'] is False and st['mocks'] == [] and st['review'] == []
          and sorted((b['title'], b['side']) for b in st['books']) == [('TEST_AITS_06_07', 'paper'), ('TEST_CHEM_CH08', 'chapter')] and await REC.count_documents({}) == 0, st)
    before = await snap()
    t = time.time(); r, st = await run(own); took = time.time() - t
    recs = await rows(); c = st.get('counts', {})
    print(f'  "Jod banao": {len(recs)} records in {took:.2f} s', flush=True)
    check('B "Jod banao": one record per printed address; a question printed in a paper and in the chapter is one record',
          r.status_code == 200 and c == {'records': len(set(P) | set(C)), 'linked': len(both), 'paper': 150 - len(both), 'chapter': len(C) - len(both), 'review': 0, 'bare': 0, 'gone': 0, 'changed': 0}
          and len(recs) == c['records'], (r.status_code, c, len(recs)))
    check('B the screen: made just now, nothing changed since; each paper says how many of its 75 are joined', st['fresh'] is True and st['running'] is False and st['ran_at'] and st['review'] == []
          and st['mocks'] == [{'mock': n, 'label': f'Mock {n}', 'questions': 75, 'linked': sum(1 for k in both if k[0] == n), 'review': 0} for n in (6, 7)], st.get('mocks'))
    check('B the uploads it read are named, with how many questions of each printed an address',
          sorted((b['title'], b['side'], b['archived'], b['mocks'], b['questions'], b['addressed']) for b in st['books'])
          == [('TEST_AITS_06_07', 'paper', False, 2, 150, 150), ('TEST_CHEM_CH08', 'chapter', False, await BM.count_documents({'book_id': chem}), len(C), len(C))], st.get('books'))
    one = recs[rid(6, 65)]; (pm, pq), (cm, cq) = P[(6, 65)], C[(6, 65)]
    series = (await DB.tejas_books.find_one({'_id': aits}))['payload']['destination'].get('series_id')
    check('B Mock 06 / Q65 is one record: the paper place and the chapter place, both question ids, the key answer, and the chapter the AITS question never printed',
          one['state'] == 'linked' and one['address'] == 'AITS Mock 06 / Q65' and (one['mock'], one['q']) == (6, 65) and one['type'] == pq['type'] == cq['type'] and one['answer'] == pq['answer'] == cq['answer']
          and one['subject'] == 'Chemistry' and one['chapter']['name'] == 'Redox Reactions' and one['chapter']['number'] == cm['chapter']['number'] and one['chapter']['title'] == cm['chapter']['title'] and sorted(one['qids']) == sorted([pq['id'], cq['id']])
          and [(p['side'], p['mock_id'], p['qid'], p['number']) for p in one['places']] == [('paper', pm['_id'], pq['id'], 65), ('chapter', cm['_id'], cq['id'], cq['original_number'])]
          and one['places'][1]['chapter'] == 'Redox Reactions' and bool(series) and one['series_id'] == series, {k: v for k, v in one.items() if k != 'text'})
    check("B its words are the question's own: without the number, the address and the place line, the same in both copies", one['text'] == L.body(pq['text']) and L.letters(one['text']) == L.letters(L.body(cq['text']))
          and not re.search(r'Source:|MOCK 06|CH 08|^Question', one['text']), one['text'][:200])
    lone, only = recs[rid(6, 1)], next(k for k in sorted(C) if k not in both)
    check('B a question only in a paper, and a question only in the chapter book, each has its own record under its address', lone['state'] == 'paper' and 'chapter' not in lone and lone['has_paper'] and not lone['has_chapter']
          and recs[rid(*only)]['state'] == 'chapter' and recs[rid(*only)]['chapter']['name'] and recs[rid(*only)]['address'] == f'AITS Mock {only[0]:02d} / Q{only[1]}' and 'series_id' not in recs[rid(*only)],
          (lone['state'], recs[rid(*only)]['state'], recs[rid(*only)]['address']))
    check('B nothing else is written: every upload, Draft, page, test, file, attempt, job and account is exactly as before', await snap() == before, [k for k, v in (await snap()).items() if before[k] != v])
    check('B the run is on the record (audit): who, how many, and that no AI was used', await DB.tejas_audits.count_documents({'action': 'Question records rebuilt', 'detail': {'$regex': 'No AI'}}) == 1, '')
    r, st2 = await run(own); again = await rows()
    check('C pressed again: the same counts and the very same records; none is made twice', r.status_code == 200 and st2['counts'] == st['counts'] and {k: same(v) for k, v in again.items()} == {k: same(v) for k, v in recs.items()}
          and all(again[k]['created_at'] == recs[k]['created_at'] and again[k]['run'] != recs[k]['run'] for k in recs), (st2.get('counts'), len(again)))
    return P, C, both, st, recs


async def doors(own):
    anon = client(); rev, _ = await mkstaff('reviewer', 'c254r'); stu = await student()
    codes = [(await x.get(API + SLUG)).status_code for x in (anon, rev, stu)] + [(await x.post(API + SLUG + '/run')).status_code for x in (anon, rev, stu)]
    check('D only the owner: no login 401; a reviewer and a student 403; on the list and on the button', codes == [401, 403, 403] * 2, codes)
    a, b = await own.get(API + 'no-such-exam'), await own.post(API + 'no-such-exam/run')
    check('D an unknown exam: 404, and nothing is started for it', (a.status_code, b.status_code) == (404, 404) and not await OPS.count_documents({'_id': QR.OP + 'no-such-exam'}), (a.status_code, b.status_code))
    was = {k: same(v) for k, v in (await rows()).items()}
    await OPS.update_one({'_id': QR.OP + SLUG}, {'$set': {'lease': 'another-server', 'lease_until': time.time() + 120}})
    r = await own.post(API + SLUG + '/run'); st = J(await own.get(API + SLUG))
    check('E a run is going on another server: the press is told "abhi ban raha hai" (409); the screen shows it running; no record is touched',
          r.status_code == 409 and 'ban raha hai' in r.text and st['running'] is True and {k: same(v) for k, v in (await rows()).items()} == was, (r.status_code, r.text[:200], st.get('running')))
    await OPS.update_one({'_id': QR.OP + SLUG}, {'$set': {'lease_until': 0}})
    a, b = await asyncio.gather(own.post(API + SLUG + '/run'), own.post(API + SLUG + '/run'))
    st = J(await own.get(API + SLUG))
    check('E two presses at the same moment: the records are whole and the same, and nothing is left running', sorted((a.status_code, b.status_code)) in ([200, 200], [200, 409]) and st['running'] is False
          and {k: same(v) for k, v in (await rows()).items()} == was, (a.status_code, b.status_code, st.get('running')))


async def locks(own, P, C, both, st0):
    (_, pq), (cm, cq) = P[(6, 65)], C[(6, 65)]
    n6 = sum(1 for k in both if k[0] == 6)
    other = next(x for x in 'ABCD' if x != cq['answer'])
    await edit(cm, cq, answer=other)
    st = J(await own.get(API + SLUG))
    check('F a Draft is changed after the join was made: the screen says the join is older than the Drafts; the counts stay as they were until the button is pressed',
          st['fresh'] is False and st['counts'] == st0['counts'], (st.get('fresh'), st.get('counts')))
    r, st = await run(own); one = (await rows())[rid(6, 65)]
    item = next((x for x in st['review'] if x['address'] == 'AITS Mock 06 / Q65'), None) or {'problems': [{'say': '', 'with': ''}]}
    check("F another answer under the same address: not joined; on the owner's list with both answers and where the other copy is",
          st['counts']['review'] == 1 and st['counts']['linked'] == len(both) - 1 and one['state'] == 'review' and st['fresh'] is True and st['review_more'] == 0 and len(st['review']) == 1
          and f"jawab alag: {pq['answer']} aur {other}" in item['problems'][0]['say'] and item['problems'][0]['with'] == f"Chapter-wise · TEST_CHEM_CH08 · {cm['chapter']['title']} · Q{cq['original_number']}"
          and st['mocks'][0] == {'mock': 6, 'label': 'Mock 6', 'questions': 75, 'linked': n6 - 1, 'review': 1}, (st['counts'], item, st['mocks'][0]))
    check('F ...the record still keeps both places, so the owner can see the two copies', [p['side'] for p in one['places']] == ['paper', 'chapter'] and one['answer'] == pq['answer'], one['places'])
    await edit(cm, cq, answer=cq['answer'], type='integer')
    r, st = await run(own); say = (st['review'] or [{'problems': [{'say': ''}]}])[0]['problems'][0]['say']
    check('F one copy an MCQ, the other numerical: not joined, and the reason says so', st['counts']['review'] == 1 and 'MCQ' in say and 'numerical' in say, say)
    head, tail = cq['text'].split('\n')[:3], cq['text'][L._run(cq['text'])[0].start():]
    await edit(cm, cq, type=cq['type'], text='\n'.join(head) + '\nWhich statement about the colour of a transition metal complex in water is the correct one here?\n' + tail)
    r, st = await run(own); say = (st['review'] or [{'problems': [{'say': ''}]}])[0]['problems'][0]['say']
    check('F the same address, kind, answer and options, but another question above the options: not joined, and the reason gives the percentage', st['counts']['review'] == 1 and 'shabd sirf' in say and '%' in say, say)
    await edit(cm, cq, text=cq['text'])
    r, st = await run(own)
    check('F the Draft is put right and the button pressed: joined again, the list is empty', st['counts'] == st0['counts'] and st['review'] == [] and (await rows())[rid(6, 65)]['state'] == 'linked', st['counts'])
    m1, q1 = P[(6, 1)]; new = next(x for x in 'ABCD' if x != q1['answer'])
    await edit(m1, q1, answer=new); r, st = await run(own); rec = (await rows())[rid(6, 1)]
    check('G a key answer corrected since the last run: counted as "badla hua" once, with what it was before', st['counts']['changed'] == 1 and rec['answer'] == new and rec['changed']['answer'] == q1['answer']
          and rec['changed']['words'] is False and rec['state'] == 'paper', (st['counts'], rec.get('changed')))
    r, st = await run(own); rec = (await rows())[rid(6, 1)]
    check('G the next run, nothing new: it is not counted again', st['counts']['changed'] == 0 and 'changed' not in rec, (st['counts'], rec.get('changed')))
    await edit(m1, q1, answer=q1['answer']); await run(own); await run(own)


async def odd_pages(own, P, C, both, st0, recs0):
    (m2, q2), (m3, q3) = P[(6, 2)], P[(6, 3)]
    only = next(k for k in sorted(C) if k not in both); mc, qc = C[only]
    await edit(m2, q2, text=SOURCE.sub('', q2['text'], count=1))
    await edit(mc, qc, text=SOURCE.sub('', qc['text'], count=1))
    await edit(m3, q3, text=q3['text'].replace('Source: AITS Mock 06 / Q3\n', 'Source: AITS Mock 09 / Q3\n'))
    assert 'Source:' not in (await BM.find_one({'_id': m2['_id']}))['questions'][1]['text'] and 'Mock 09' in (await BM.find_one({'_id': m3['_id']}))['questions'][2]['text']
    r, st = await run(own); recs = await rows(); c = st['counts']
    a = recs[rid(6, 2)]
    check("H a paper question that prints no address: its paper's heading and its number are its address; the same record, the same words",
          a['state'] == 'paper' and a['address'] == 'AITS Mock 06 / Q2' and a['qids'] == [q2['id']] and a['words_sha'] == recs0[rid(6, 2)]['words_sha'] and a['created_at'] == recs0[rid(6, 2)]['created_at'] and 'changed' not in a,
          {k: a.get(k) for k in ('state', 'address', 'qids', 'changed')})
    gone = recs[rid(*only)]
    check('H a chapter question that prints no address: counted as "bina pate ke"; it is joined to nothing; the record it had stays, with its words and chapter',
          c['bare'] == 1 and gone['state'] == 'gone' and gone['places'] == [] and gone['qids'] == [] and gone['text'] == recs0[rid(*only)]['text'] and gone['chapter'] == recs0[rid(*only)]['chapter'], (c, gone['state']))
    odd = recs.get(rid(9, 3)) or {}
    item = next((x for x in st['review'] if x['address'] == 'AITS Mock 09 / Q3'), None) or {'problems': [{'say': ''}]}
    check("H a paper question that prints another paper's address: on the owner's list, saying which paper it sits in and what it prints",
          odd.get('state') == 'review' and c['review'] == 1 and item['problems'][0]['say'] == 'Paper mein yeh Mock 6 / Q3 hai, par is par chhapa pata AITS Mock 09 / Q3 hai.' and recs[rid(6, 3)]['state'] == 'gone'
          and c['gone'] == 2 and [m['mock'] for m in st['mocks']] == [6, 7, 9] and st['mocks'][2] == {'mock': 9, 'label': '', 'questions': 1, 'linked': 0, 'review': 1}, (odd.get('state'), c, item, st['mocks'][-1]))
    await edit(m2, q2, text=q2['text']); await edit(mc, qc, text=qc['text']); await edit(m3, q3, text=q3['text'])
    r, st = await run(own); recs = await rows()
    check('H the three pages are put right: every record is back under its own address; only the misprinted address is left, empty',
          {**st['counts'], 'gone': 0} == st0['counts'] and st['counts']['gone'] == 1 and recs[rid(9, 3)]['state'] == 'gone' and recs[rid(6, 3)]['state'] == 'paper' and recs[rid(*only)]['state'] == 'chapter'
          and st['review'] == [], st['counts'])
    return only


async def goes_and_returns(own, chem, C, both, st0, recs0, only):
    await own.post('/api/auth/refresh')  # TEST: this walk may be longer than one 15-minute sign-in
    r = await own.post(f'/api/admin/master/uploads/book/{chem}/delete', json={'confirm': 'DELETE'})
    for _ in range(120):
        row = await DB.tejas_books.find_one({'_id': chem}, {'removed': 1})
        if not row or row.get('removed'):
            break
        await asyncio.sleep(.25)
    st = J(await own.get(API + SLUG))
    check('I the chapter upload is deleted for good: the screen says the join is older than the uploads', r.status_code == 200 and st['fresh'] is False and st['sources'] == 1, (r.status_code, r.text[:200], st.get('fresh'), st.get('sources')))
    r, st = await run(own); recs = await rows(); c = st['counts']
    left = [recs[rid(*k)] for k in C if k not in both]
    check('I after the run: nothing is joined; the papers keep their 150 records; the chapter-only records stay, with their words, answer and chapter, and say their upload is gone',
          c['records'] == 150 and c['linked'] == 0 and c['paper'] == 150 and c['chapter'] == 0 and c['gone'] == 1 + len(left) and len(recs) == len(recs0) + 1
          and all(d['state'] == 'gone' and d['places'] == [] and d['text'] == recs0[d['_id']]['text'] and d['answer'] == recs0[d['_id']]['answer'] and d['chapter'] == recs0[d['_id']]['chapter'] for d in left), c)
    one = recs[rid(6, 65)]
    check('I Mock 06 / Q65 is a paper-only record again, and keeps the chapter it learned', one['state'] == 'paper' and [p['side'] for p in one['places']] == ['paper'] and one['chapter']['name'] == 'Redox Reactions'
          and not one['has_chapter'], (one['state'], one.get('chapter')))
    chem2, crow, _, _ = await run_book(own, 'jee-main:chapters', chapter8(), 'TEST_CHEM_CH08_AGAIN')
    r, st = await run(own); recs = await rows(); C2 = await drafts(chem2)
    check('I the chapter book is uploaded again: every question sits on the record it had (same record, made the first day), joined as before',
          set(C2) == set(C) and {**st['counts'], 'gone': 0} == st0['counts'] and st['counts']['gone'] == 1 and all(recs[rid(*k)]['created_at'] == recs0[rid(*k)]['created_at'] for k in C)
          and recs[rid(6, 65)]['state'] == 'linked' and recs[rid(6, 65)]['places'][1]['book'] == 'TEST_CHEM_CH08_AGAIN' and recs[rid(*only)]['state'] == 'chapter'
          and C2[(6, 65)][1]['id'] in recs[rid(6, 65)]['qids'] and C[(6, 65)][1]['id'] not in recs[rid(6, 65)]['qids'], st['counts'])
    return st


async def elsewhere(own, aits, C, st0):
    slug = J(await own.post('/api/admin/catalog/exams', json={'name': 'LINKX', 'short': 'LX', 'subjects': ['Chemistry'], 'color': 'rose'})).get('slug')
    sec = J(await own.post(f'/api/admin/catalog/exams/{slug}/sections', json={'name': 'Chapter-wise', 'description': '', 'layout': 'chapters', 'kind': 'chapters'})).get('id')
    await run_book(own, sec, chapter8(), 'TEST_LINKX_CH08')
    mine = await rows()
    r, st = await run(own, slug); theirs = await rows(slug)
    check('J another exam with the same chapter book: records of its own (none joined, it has no papers); the first exam is not read',
          r.status_code == 200 and st['counts']['records'] == st['counts']['chapter'] == len(C) == len(theirs) and st['counts']['linked'] == 0 and st['mocks'] == [] and [b['title'] for b in st['books']] == ['TEST_LINKX_CH08']
          and not set(theirs) & set(mine), (r.status_code, st.get('counts'), st.get('books')))
    check("J the first exam's records are exactly as they were", await rows() == mine and J(await own.get(API + SLUG))['counts'] == st0['counts'], '')
    r = await own.post(f'/api/admin/master/uploads/book/{aits}/dismiss')
    stale = J(await own.get(API + SLUG))
    r2, st = await run(own); recs = await rows()
    check("K the papers' upload is sent to the Library: the records stay as they were, joined as before; each paper place says it is in the Library",
          r.status_code == 200 and stale['fresh'] is False and r2.status_code == 200 and st['counts'] == st0['counts'] and st['fresh'] is True
          and all(p['archived'] for d in recs.values() for p in d['places'] if p['side'] == 'paper') and not any(p['archived'] for d in recs.values() for p in d['places'] if p['side'] == 'chapter')
          and [b['archived'] for b in st['books'] if b['side'] == 'paper'] == [True], (r.status_code, r.text[:200], st.get('counts'), st.get('books')))


async def main():
    assert not H.leftover_real_handles()
    await H.tdbmod.indexes(); await structure.seed()
    try:
        own, _ = await mkstaff('owner', 'c254')
        aits, chem = await setup(own)
        if all(ok for _, ok in RESULTS):
            P, C, both, st0, recs0 = await made(own, aits, chem)
            await doors(own)
            await locks(own, P, C, both, st0)
            only = await odd_pages(own, P, C, both, st0, recs0)
            st1 = await goes_and_returns(own, chem, C, both, st0, recs0, only)
            await elsewhere(own, aits, C, st1)
    finally:
        # Only the disposable database this run created; never the app's own.
        assert H.TEST_DB.startswith('tejas_isolated_') and H.TEST_DB != H.REAL_DB, H.TEST_DB
        await H.tdbmod.client.drop_database(H.TEST_DB)
        print('dropped', H.TEST_DB, flush=True)
        bad = [n for n, ok in RESULTS if not ok]
        print(f'TOTAL {len(RESULTS)} PASS {len(RESULTS) - len(bad)} FAIL {len(bad)}', flush=True)


if __name__ == '__main__':
    asyncio.run(main())
