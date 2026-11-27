"""TEST-ONLY iteration 248 (pocket H1): where a question was printed from ('Source: AITS Mock 06 / Q65') is the Super Admin's,
never the student's. Chapter 8 of the owner's chemistry book through the real app (upload -> Draft -> Live -> a student's attempt),
in a disposable DB (storage mocked, no AI, no network).
A. Draft keeps the line; the Live test keeps the address apart (printed_source) and its words go on without the line.
B. The student: start, attempt, pictures (whole question, pieces), results, solution pictures, Misfire: the address is nowhere.
   A whole picture differs from the printed page only inside that one line, which is white.
C. A paper frozen BEFORE this change (its pack still carries the line): the student still never gets it; the frozen pack is untouched.
D. The red alert for a repeated question still fires between a Live test (no line) and a waiting Draft (line).
E. Only a heading line is hidden: a line of the question itself that begins with 'Source:' stays, in the picture and in the words.
Run: cd /app/backend && python tests/source_hidden248.py   (drops only its own disposable database)
"""
import asyncio, hashlib, json, math, re, sys, time, uuid
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import fitz  # noqa: E402
import numpy as np  # noqa: E402
from book_speed211 import chapter8, run_book  # noqa: E402
from cut_bridge207 import H, BM, DB, mkstaff, client, drain  # noqa: E402
from structure_iso173 import start, mkset  # noqa: E402
from tejas import structure, jobs as JOBS  # noqa: E402
from tejas.book_pdf import inspect_many  # noqa: E402
from tejas.packs import unpack  # noqa: E402
import tejas_core as core  # noqa: E402
from tejas_core import without_source, printed_address  # noqa: E402

RESULTS = []
M = '/api/admin/master'
WORK = Path('/root/aitsv_out/src248'); WORK.mkdir(parents=True, exist_ok=True)  # kept across pod restarts
BOOK = str(WORK / 'src248.pdf')
ADDRESS = re.compile(r'AITS Mock \d+ / Q\d+')
LEAK = re.compile(r'AITS\s*Mock|printed_source|Source:|Mock\s*\d+\s*/\s*Q\s*\d+')
OLD = 'Question {n}\nSource: AITS Mock 06 / Q6{n}\nCH 08 / Redox Reactions\nA 25.0 mL aliquot of a Mohr-salt stock, question {n}.'


def check(name, ok, detail=''):
    RESULTS.append((name, bool(ok)))
    print(('PASS ' if ok else 'FAIL ') + name + ('' if ok else ' :: ' + str(detail)[:900]), flush=True)


def J(r):
    try: d = r.json()
    except Exception: return {}
    if isinstance(d, dict) and 'data' in d and 'error' in d: d = d['data']
    return d if d is not None else {}


def leak(text):
    return [text[max(0, m.start() - 40):m.end() + 40] for m in LEAK.finditer(text)][:3]


def pix(png):
    p = fitz.Pixmap(png)
    if p.n - p.alpha != 3: p = fitz.Pixmap(fitz.csRGB, p)
    if p.alpha: p = fitz.Pixmap(p, 0)
    return np.frombuffer(p.samples, np.uint8).reshape(p.height, p.stride)[:, :p.width * 3].reshape(p.height, p.width, 3)


def painted(path, ref, shown, plain=None):
    """(ok, detail): the student's picture differs from the printed page only inside the heading 'Source' line, and that line is white.
    plain: the same region cut without the mask, when the caller already has it."""
    plain = plain or inspect_many(path, [{'action': 'crop', 'page': ref['page'], 'rect': ref['rect']}])[0]['image_bytes']
    doc = fitz.open(path); page = doc[ref['page'] - 1]; w, h = page.rect.width, page.rect.height; r = ref['rect']
    clip = fitz.Rect(r[0] * w, r[1] * h, r[2] * w, r[3] * h)
    lines = sorted((l['bbox'] for b in page.get_text('dict', clip=clip)['blocks'] for l in b.get('lines', []) if re.match(r'\s*Source\s*:', ''.join(s['text'] for s in l['spans']))), key=lambda b: b[1])
    doc.close()
    a, b = pix(shown), pix(plain)
    if a.shape != b.shape or not lines: return False, ('shape or line', a.shape, b.shape, len(lines))
    scale = min(2, 1800 / clip.width, 2400 / clip.height); ox, oy = math.floor(clip.x0 * scale), math.floor(clip.y0 * scale)
    x0, y0, x1, y1 = lines[0]
    box = (math.floor(x0 * scale) - ox, math.floor(y0 * scale) - oy, math.ceil(x1 * scale) - ox, math.ceil(y1 * scale) - oy)
    diff = np.argwhere((a != b).any(axis=2))
    if not len(diff): return False, 'nothing was painted: the line is still in the picture'
    (ya, xa), (yb, xb) = diff.min(axis=0), diff.max(axis=0)
    inside = xa >= box[0] - 3 and ya >= box[1] - 3 and xb <= box[2] + 3 and yb <= box[3] + 3
    white = bool((a[max(0, box[1]):box[3], max(0, box[0]):box[2]] == 255).all())
    inked = int((b[max(0, box[1]):box[3], max(0, box[0]):box[2]] < 200).any(axis=2).sum())
    return inside and white and inked > 50, {'line': box, 'changed': (int(xa), int(ya), int(xb), int(yb)), 'white': white, 'ink before': inked, 'lines': len(lines)}


async def graded(c, aid):
    for _ in range(40):
        r = await c.get(f'/api/attempts/{aid}/results'); d = J(r)
        if r.status_code == 200 and d.get('status') != 'grading' and d.get('summary'):
            return r, d
        for j in await DB.tejas_jobs.find({'status': 'queued'}).to_list(50):
            try: await JOBS.run_job(j['id'])
            except Exception: pass
        await asyncio.sleep(.3)
    return r, d


async def student():
    s = client(); r = await s.post('/api/auth/phone/signup', json={'phone': '91' + str(uuid.uuid4().int)[:8], 'pin': '8261', 'confirm_pin': '8261'})
    assert r.status_code == 200, r.text
    return s


async def picture(text):
    doc = fitz.open(); page = doc.new_page(width=420, height=120); page.insert_text((20, 40), text, fontsize=11)
    raw = page.get_pixmap(matrix=fitz.Matrix(2, 2), alpha=False).tobytes('png'); doc.close()
    fid = str(uuid.uuid4()); path = f'jeelive/test248/{fid}.png'; H.STORE[path] = raw
    await DB.tejas_files.insert_one({'id': fid, 'path': path, 'kind': 'rendered_png', 'sha256': hashlib.sha256(raw).hexdigest(), 'created_at': time.time()})
    return {'file_id': fid, 'page': 1, 'rect': [0, 0, 420, 120], 'prerendered': True}


def heading_pdf():
    """A question whose own second line begins with 'Source:' (two rows of print above it), under a heading that prints its source."""
    doc = fitz.open(); p = doc.new_page()
    p.insert_text((40, 60), 'Question 1', fontsize=13); p.insert_text((420, 60), 'Source: AITS Mock 09 / Q9', fontsize=8)
    p.insert_text((40, 78), 'CH 01 / Optics', fontsize=9)
    for i, line in enumerate(('A lamp is placed 20 cm from a thin convex lens of focal length 15 cm.', 'Source: the lamp emits light of wavelength 500 nm in air.', 'Find the distance of the image from the lens.')):
        p.insert_text((40, 110 + 18 * i), line, fontsize=11)
    raw = doc.tobytes(); doc.close()
    return raw


async def new_paper(own, chap):
    raw = chapter8(); open(BOOK, 'wb').write(raw)
    bid, rows, _, _ = await run_book(own, chap, raw, 'TEST_SRC248')
    m = rows[0]; draft = {q['id']: q for q in m['questions']}
    check('A the Draft is ready and keeps the printed line in its words (the Super Admin still sees where each question came from)',
          m['state'] == 'ready' and all(ADDRESS.search(q['text']) and 'Source:' in q['text'] for q in m['questions']), (m['state'], m['issues'][:3]))
    r = await own.post(M + '/status', json={'items': [{'kind': 'book_mock', 'id': m['_id']}], 'to': 'live'}); await drain()
    mk = await BM.find_one({'_id': m['_id']}); sid = mk.get('set_id')
    check('A the mock goes Live', r.status_code == 200 and bool(sid) and mk['state'] == 'published', (r.status_code, r.text[:300], mk['state'], mk['issues'][:3]))
    if not sid: return None, None, m
    s = await DB.tejas_sets.find_one({'id': sid})
    qs = s['questions']
    check('A the Live test keeps each address apart, the very one its Draft prints',
          len(qs) == len(draft) and all(q.get('printed_source') and q['printed_source'] == ADDRESS.search(draft[q['id']]['text'])[0] for q in qs), [(q.get('printed_source'), draft[q['id']]['text'][:60]) for q in qs][:3])
    check("A its words go on without the line, and without anything else lost", all(not leak(q['text'] + q['accessible_text']) and q['text'] == q['accessible_text'] == without_source(draft[q['id']]['text'])
          and len(q['text'].split('\n')) == len(draft[q['id']]['text'].split('\n')) - 1 for q in qs), [(q['text'][:90]) for q in qs][:2])
    check('A every question still has its whole picture, its solution picture and its pieces', all(len(q['q_refs']) >= 1 and len(q['s_refs']) >= 1 and q.get('c_refs') for q in qs), [(len(q['q_refs']), len(q['s_refs']), len(q.get('c_refs', []))) for q in qs][:5])
    return sid, qs, m


async def as_student(sid, qs):
    await asyncio.sleep(2); await structure.visibility(force=True)
    stu = await student(); r = await start(stu, sid); a = J(r); aid = a.get('id')
    check('B a student starts the test', r.status_code == 200 and len(a.get('questions', [])) == len(qs), (r.status_code, r.text[:300]))
    if not aid: return
    check('B start: the address is nowhere in what the student receives', not leak(r.text), leak(r.text))
    r = await stu.get(f'/api/attempts/{aid}'); check('B attempt: the address is nowhere', r.status_code == 200 and not leak(r.text), (r.status_code, leak(r.text)))
    check('B the new look still arrives: question piece and option pieces', all(q.get('pieces') for q in J(r)['questions'] if q['type'] == 'mcq'), [q.get('pieces') for q in J(r)['questions']][:2])
    pack = await unpack((await DB.tejas_attempts.find_one({'id': aid}, {'pack_id': 1}))['pack_id'])
    check("B the paper frozen for this student carries neither the line nor the address kept for the Super Admin", not leak(json.dumps(pack)), leak(json.dumps(pack)))
    bad = []
    for q in qs[:3] + qs[-1:]:
        r = await stu.get(f"/api/attempts/{aid}/questions/{q['id']}/asset/question/0")
        ok, why = await asyncio.to_thread(painted, BOOK, q['q_refs'][0], r.content) if r.status_code == 200 else (False, r.status_code)
        if not ok: bad.append((q['number'], why))
        r = await stu.get(f"/api/attempts/{aid}/questions/{q['id']}/asset/piece/0")
        if r.status_code != 200 or r.content[:4] != b'\x89PNG': bad.append((q['number'], 'piece', r.status_code))
    check("B whole-question pictures: only the 'Source' line is painted out (white), every other pixel is the printed page", not bad, bad)
    r = await stu.get(f"/api/attempts/{aid}/questions/{qs[0]['id']}/asset/solution/0"); check('B solution pictures stay closed until the paper is submitted', r.status_code == 403, r.status_code)
    await stu.post(f'/api/attempts/{aid}/begin'); await asyncio.sleep(.2)
    r = await stu.post(f'/api/attempts/{aid}/submit'); check('B submit', r.status_code in (200, 202), (r.status_code, r.text[:200]))
    r, d = await graded(stu, aid)
    check('B results arrive', r.status_code == 200 and len(d.get('questions', [])) == len(qs), (r.status_code, r.text[:300]))
    check('B results: the address is nowhere', not leak(r.text), leak(r.text))
    bad = []
    for q in qs[:3] + qs[-1:]:
        r = await stu.get(f"/api/attempts/{aid}/questions/{q['id']}/asset/solution/0")
        ok, why = await asyncio.to_thread(painted, BOOK, q['s_refs'][0], r.content) if r.status_code == 200 else (False, r.status_code)
        if not ok: bad.append((q['number'], why))
    check("B solution pictures: only the 'Source' line is painted out (white), every other pixel is the printed page", not bad, bad)
    r = await stu.get('/api/my/misfire/summary'); s = J(r)
    r2 = await stu.get('/api/my/misfire'); items = J(r2).get('items', [])
    check('B Misfire lists the left questions, and the address is nowhere', r.status_code == 200 and s.get('open') == len(qs) and len(items) == len(qs) and not leak(r.text + r2.text), (r.status_code, s, len(items), leak(r.text + r2.text)))
    kept = await DB.tejas_misfires.count_documents({'attempt_id': aid})
    await DB.tejas_misfires.update_many({'attempt_id': aid}, {'$set': {'question.accessible_text': OLD.format(n=1)}})
    r = await stu.get('/api/my/misfire'); items = J(r).get('items', [])
    check('B a Misfire row kept before this change (it still holds the line) is shown without it, the rest of its words unchanged',
          kept == len(qs) and items and not leak(r.text) and all(i['question']['accessible_text'] == without_source(OLD.format(n=1)) for i in items), (kept, leak(r.text), items[0]['question'] if items else None))


async def old_paper():
    qs = [{'id': str(uuid.uuid4()), 'number': n, 'type': 'mcq', 'subject': 'Chemistry', 'section': 'Chemistry', 'options': {k: k for k in 'ABCD'}, 'answer': 'A', 'solution': 'Original book worked solution.',
           'render_mode': 'source', 'text': OLD.format(n=n), 'accessible_text': OLD.format(n=n), 'solution_accessible_text': 'Original book worked solution.',
           'q_refs': [await picture(f'old question {n}')], 's_refs': [await picture(f'old solution {n}')]} for n in (1, 2, 3)]
    sid = await mkset('OLD248', exam='JEE Main', catalog_section_id='jee-main:mocks', test_kind='mock', questions=qs)
    stu = await student(); r = await start(stu, sid); a = J(r); aid = a.get('id')
    check('C a student starts a paper made before this change', r.status_code == 200 and len(a.get('questions', [])) == 3, (r.status_code, r.text[:300]))
    if not aid: return
    check('C start: the address is nowhere', not leak(r.text), leak(r.text))
    check('C the words for screen readers are the same without that one line', [q.get('accessible_text') for q in a['questions']] == [without_source(OLD.format(n=n)) for n in (1, 2, 3)], [q.get('accessible_text') for q in a['questions']])
    r = await stu.get(f'/api/attempts/{aid}'); check('C attempt: the address is nowhere', r.status_code == 200 and not leak(r.text), leak(r.text))
    await stu.post(f'/api/attempts/{aid}/begin'); await asyncio.sleep(.2); await stu.post(f'/api/attempts/{aid}/submit')
    r, d = await graded(stu, aid)
    check('C results: the address is nowhere', r.status_code == 200 and len(d.get('questions', [])) == 3 and not leak(r.text), (r.status_code, leak(r.text)))
    r = await stu.get('/api/my/misfire'); check('C Misfire: the address is nowhere', r.status_code == 200 and len(J(r).get('items', [])) == 3 and not leak(r.text), (r.status_code, leak(r.text)))
    pack = await unpack((await DB.tejas_attempts.find_one({'id': aid}, {'pack_id': 1}))['pack_id'])
    check('C the frozen paper itself is not rewritten (it is only shown without the line)', [q['accessible_text'] for q in pack] == [OLD.format(n=n) for n in (1, 2, 3)], [q['accessible_text'][:60] for q in pack])


async def repeated(own, chap, m):
    _, rows, _, _ = await run_book(own, chap, chapter8(), 'TEST_SRC248_AGAIN')
    r = await own.get(f"/api/admin/duplicates/mock/{rows[0]['_id']}"); d = J(r)
    check('D the same chapter uploaded again: every question is still flagged as repeated against the Live test', r.status_code == 200 and d.get('checked') and len(d.get('items', [])) == len(m['questions']),
          (r.status_code, d.get('checked'), len(d.get('items', [])), len(m['questions'])))


def heading_only():
    path = str(WORK / 'src248_heading.pdf'); open(path, 'wb').write(heading_pdf()); ref = {'page': 1, 'rect': [.02, .03, .98, .5]}
    got = inspect_many(path, [{'action': 'crop', **ref, 'mask': 'source'}, {'action': 'crop', **ref}])
    ok, why = painted(path, ref, got[0]['image_bytes'])
    check("E only the heading line is painted out; the question's own line that begins with 'Source:' stays in the picture", got[0].get('masked') == 1 and 'masked' not in got[1] and ok and why['lines'] == 2, (got[0].get('masked'), why))
    body = 'Question 1\nSource: AITS Mock 09 / Q9\nCH 01 / Optics\nA lamp is placed 20 cm from a lens.\nSource: the lamp emits light of wavelength 500 nm.\nFind the image distance.'
    check("E the words: only the heading line goes", without_source(body) == body.replace('Source: AITS Mock 09 / Q9\n', '') and without_source('No line here.') == 'No line here.' and without_source('') == ''
          and printed_address(body) == 'AITS Mock 09 / Q9' and printed_address('nlts test 3/q.7'.join(('Question 2\nsource : ', '\nwords'))) == 'nlts test 3/q.7', (without_source(body), printed_address(body)))
    # A heading that names a past exam, not a question's address in a series, is the student's to read: nothing is hidden.
    doc = fitz.open(); p = doc.new_page(); p.insert_text((40, 60), 'Question 1', fontsize=13); p.insert_text((380, 60), 'Source: JEE Main 2019 (9 Jan, Shift 1)', fontsize=8)
    p.insert_text((40, 110), 'A lamp is placed 20 cm from a thin convex lens of focal length 15 cm.', fontsize=11); other = str(WORK / 'src248_pyq.pdf'); doc.save(other); doc.close()
    got = inspect_many(other, [{'action': 'crop', **ref, 'mask': 'source'}, {'action': 'crop', **ref}]); year = 'Question 1\nSource: JEE Main 2019 (9 Jan, Shift 1)\nA lamp is placed 20 cm from a lens.'
    check("E a heading 'Source: JEE Main 2019 (9 Jan, Shift 1)' is not an address: the picture and the words keep it", 'masked' not in got[0] and got[0]['image_bytes'] == got[1]['image_bytes']
          and without_source(year) == year and printed_address(year) == '', (got[0].get('masked'), without_source(year)))
    worker = re.search(r"^SOURCE=re\.compile\(r'(.+)',re\.I\)$", (Path(__file__).resolve().parents[1] / 'tejas' / 'book_pdf_worker.py').read_text(), re.M)
    check('E the picture and the words are hidden by one and the same pattern', bool(worker) and worker[1] == core._SOURCE_LINE.pattern, worker and worker[1])


async def main():
    assert not H.leftover_real_handles()
    await H.tdbmod.indexes(); await structure.seed()
    try:
        own, _ = await mkstaff('owner', 'src248')
        slug = J(await own.post('/api/admin/catalog/exams', json={'name': 'SRCX', 'short': 'SX', 'subjects': ['Chemistry'], 'color': 'rose'})).get('slug')
        chap = J(await own.post(f'/api/admin/catalog/exams/{slug}/sections', json={'name': 'Chapter-wise', 'description': '', 'layout': 'chapters', 'kind': 'chapters'})).get('id')
        await structure.exams.update_one({'_id': slug}, {'$set': {'shown': True}})
        sid, qs, m = await new_paper(own, chap)
        if sid:
            await as_student(sid, qs)
            await repeated(own, chap, m)
        await old_paper()
        await asyncio.to_thread(heading_only)
    finally:
        # Only the disposable database this run created; never the app's own.
        assert H.TEST_DB.startswith('tejas_isolated_') and H.TEST_DB != H.REAL_DB, H.TEST_DB
        await H.tdbmod.client.drop_database(H.TEST_DB)
        print('dropped', H.TEST_DB, flush=True)
        f = [x for x in RESULTS if not x[1]]
        print(f'TOTAL {len(RESULTS)} PASS {len(RESULTS) - len(f)} FAIL {len(f)}', flush=True)


if __name__ == '__main__':
    asyncio.run(main())
