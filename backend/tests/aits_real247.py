"""TEST-ONLY iteration 247: one of the owner's All India Test Series books (Mocks 01-25 or 26-50) through the real app
(upload -> Draft, into the built-in JEE series) in a disposable DB. Checks every mock as the Super Admin would get it: 75 questions,
20 MCQ + 5 numerical a subject, key, worked solution, clean cut, its own Mock/Q address, fit for an All India day.
Then every picture is looked at as students' pictures are cut: no question or option piece carries the printed 'Source: ...' line,
and the app's own PDF worker paints it out of every whole-question and solution picture.
Run: cd /app/backend && python tests/aits_real247.py <pdf> <tag>   (drops only its own disposable database; storage is mocked; no AI)
"""
import asyncio, collections, os, pickle, re, sys, time, unicodedata
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import fitz  # noqa: E402
import cut_bridge207 as B  # noqa: E402,F401
from cut_bridge207 import H, BM, DB, mkstaff, upload, drain  # noqa: E402
from tejas import structure  # noqa: E402
from tejas.book_models import BookMock  # noqa: E402
from tejas.book_pdf import inspect_many  # noqa: E402
from tejas.live_series import series_problem  # noqa: E402

RESULTS = []
SRC = re.compile(r'(?im)^\s*Source\s*:\s*AITS\s*Mock\s*0*(\d+)\s*/\s*Q\s*0*(\d+)\s*$')
LINE = re.compile(r'(?im)^\s*Source\s*:')
HEAD = re.compile(r'(?im)^\s*(question\s*\d+|source\s*:.*|mock\s*\d+\s*/.*|ch\s*\d+\s*/.*)\s*$')
SHAPE = {(s, k): n for s in ('Mathematics', 'Physics', 'Chemistry') for k, n in (('mcq', 20), ('integer', 5))}


def check(name, ok, detail=''):
    RESULTS.append((name, bool(ok)))
    print(('PASS ' if ok else 'FAIL ') + name + ('' if ok else ' :: ' + str(detail)[:900]), flush=True)


def words(text):
    return re.sub(r'[^a-z0-9]+', '', unicodedata.normalize('NFKC', HEAD.sub('', text)).lower())


def piece_words(pdf, pieces):
    """Keys of the pieces (or regions) that overlap a printed 'Source' line; the lines' boxes are read straight from the PDF, once a page."""
    doc = fitz.open(pdf); dirty = []; lines = {}
    for key, p in pieces:
        n = p['page']
        if n not in lines:
            page = doc[n - 1]; w, h = page.rect.width, page.rect.height
            lines[n] = [(b[0] / w, b[1] / h, b[2] / w, b[3] / h) for blk in page.get_text('dict', flags=fitz.TEXTFLAGS_DICT & ~fitz.TEXT_PRESERVE_IMAGES)['blocks']
                        for ln in blk.get('lines', []) for b in [ln['bbox']] if LINE.match(''.join(s['text'] for s in ln['spans']))]
        r = p['rect']
        if any(min(r[2], b[2]) - max(r[0], b[0]) > .001 and min(r[3], b[3]) - max(r[1], b[1]) > .001 for b in lines[n]): dirty.append(key)
    doc.close()
    return dirty


async def sweep(pdf, wanted, keep=()):
    """Every region through the app's own PDF worker, a few hundred at a time so the pictures never pile up in memory."""
    rows, kept = [], {}
    for i in range(0, len(wanted), 400):
        part = wanted[i:i + 400]
        for (key, _), x in zip(part, await asyncio.to_thread(inspect_many, pdf, [w for _, w in part], 20)):
            rows.append((key, x.get('error'), x.get('masked', 0), len(LINE.findall(x.get('text') or ''))))
            if key in keep and x.get('image_bytes'): kept[key] = x['image_bytes']
    return rows, kept


async def main(pdf, tag):
    assert not H.leftover_real_handles()
    await H.tdbmod.indexes(); await structure.seed()
    try:
        own, _ = await mkstaff('owner', 'aits247')
        raw = open(pdf, 'rb').read()
        t0 = time.time(); b = await upload(own, raw, 'TEST_AITS_' + tag, section_id='jee-main:aits'); t_up = time.time() - t0
        t1 = time.time(); r = await own.post(f"/api/admin/books/{b['id']}/complete"); await drain(100000); t_draft = time.time() - t1
        book = await DB.tejas_books.find_one({'_id': b['id']})
        rows = await BM.find({'book_id': b['id']}).sort('order', 1).to_list(200)
        print('UPLOAD', round(t_up, 1), 's  COMPLETE->DRAFT', round(t_draft, 1), 's  book state', book['state'], '| mocks', len(rows), '|', book['payload'].get('message'), flush=True)
        check('the book is read to the end', r.status_code == 200 and book['state'] not in ('failed', 'uploading', 'received', 'reading') and book['payload'].get('read_pages') == book['payload']['pages'],
              (r.status_code, book['state'], book['payload'].get('read_pages'), book['payload'].get('pages'), book['payload'].get('message')))
        check('25 mocks arrive as Draft', len(rows) == 25, [m['label'] for m in rows][:30])
        out, bad, total, crops, pieces, nums = [], [], collections.Counter(), [], [], []
        for m in rows:
            qs = m['questions']
            addr = [(lambda s: (int(s[1]), int(s[2])) if s else None)(SRC.search(q['text'])) for q in qs]
            num = addr[0][0] if addr and addr[0] else 0; nums.append(num)
            shape = dict(collections.Counter((q['subject'], q['type']) for q in qs))
            cuts = collections.Counter((q.get('cut') or {}).get('status') for q in qs)
            why = []
            if m['state'] != 'ready' or m['issues']: why.append(('state', m['state'], m['issues'][:3]))
            if len(qs) != 75: why.append(('count', len(qs)))
            if shape != SHAPE: why.append(('shape', shape))
            if any(not q['answer'] for q in qs): why.append(('no key', [q['original_number'] for q in qs if not q['answer']][:8]))
            if any(q['solution_kind'] != 'supplied_worked' for q in qs): why.append(('no solution', sum(q['solution_kind'] != 'supplied_worked' for q in qs)))
            if set(cuts) - {'ok', 'trim'}: why.append(('cut', dict(cuts)))
            if addr != [(num, q['original_number']) for q in qs]: why.append(('address', [(a, q['original_number']) for a, q in zip(addr, qs) if a != (num, q['original_number'])][:5]))
            if [q['original_number'] for q in qs] != list(range(1, 76)): why.append(('numbers', [q['original_number'] for q in qs][:10]))
            problem = series_problem(BookMock.from_mongo(m))
            if problem: why.append(('series', problem))
            if why: bad.append((m['label'], why))
            print(f"  {m['label']:10} address mock {num:2} {m['state']:6} q={len(qs):3} cut={dict(cuts)} issues={len(m['issues'])}", flush=True)
            total.update(questions=len(qs), **{'cut_' + str(k): v for k, v in cuts.items()}, boxes=sum((q.get('cut') or {}).get('arrangement') == 'boxes' for q in qs))
            for q in qs:
                key = (num, q['original_number'])
                out.append({'addr': key, 'label': m['label'], 'subject': q['subject'], 'type': q['type'], 'answer': q['answer'], 'words': words(q['text']),
                            'text': q['text'], 'id': q['id'], 'mock_id': m['_id'], 'order': m['order'],
                            'cut': (q.get('cut') or {}).get('status'), 'rules': m.get('rules')})
                crops += [((*key, role), {'action': 'crop', 'page': x['page'], 'rect': x['rect'], 'mask': 'source'}) for role in ('question', 'solution') for x in q['source_regions'][role]]
                pieces += [((*key, p['part']), p) for p in (q.get('cut') or {}).get('parts', [])]
        print('TOTAL', dict(total), '| regions', len(crops), '| pieces', len(pieces), flush=True)
        check('every mock is ready with no issue: 75 questions 1..75, 20 MCQ + 5 numerical a subject, a key and a worked solution for each, a clean cut, its own Mock/Q address, fit for an All India day', not bad, bad[:6])
        check('1,875 questions; the 25 mocks carry 25 different mock numbers, in the order of the book', total['questions'] == 1875 and len(set(nums)) == 25 and nums == sorted(nums), (total['questions'], nums))
        rules = collections.Counter((m.get('rules') or {}).get('minutes') for m in rows), collections.Counter(((m.get('rules') or {}).get('correct'), (m.get('rules') or {}).get('wrong')) for m in rows)
        check('every mock: 180 minutes, +4 / -1', rules == (collections.Counter({180.0: len(rows)}), collections.Counter({(4.0, -1.0): len(rows)})), rules)
        t2 = time.time(); dirty = await asyncio.to_thread(piece_words, pdf, pieces); have = collections.Counter(k[:2] for k, _ in pieces if k[2] == 'q')
        print('PIECES', len(pieces), 'read', round(time.time() - t2), 's', flush=True)
        check("every question has its own question piece; no question or option piece carries the printed 'Source' line", not dirty and len(have) == total['questions'] and set(have.values()) == {1},
              (dirty[:6], len(have), dict(collections.Counter(have.values()))))
        seen = await asyncio.to_thread(piece_words, pdf, [(k, w) for k, w in crops if k[2] == 'question'])
        check("the same reading does find the line in every whole-question region (so the check above can see it)", len(seen) == total['questions'], len(seen))
        first = rows[0]['questions'] if rows else []
        keep = {(nums[0], q['original_number'], role) for q in (first[0], first[20], first[-1]) for role in ('question', 'solution')} if first else set()
        t3 = time.time(); got, kept = await sweep(pdf, crops, keep)
        wrong = [(k, err, masked, printed) for k, err, masked, printed in got if err or masked != printed]
        per = collections.Counter()
        for k, _, masked, _ in got: per[k] += masked
        print('MASK', len(got), 'regions', dict(collections.Counter((k[2], masked) for k, _, masked, _ in got)), round(time.time() - t3), 's', flush=True)
        check("students' whole-question and solution pictures: every printed 'Source' line is painted out, none is left", bool(got) and not wrong, wrong[:6])
        check("the 'Source' line is printed once on every question and once on every solution (so nothing went unseen)", len(per) == 2 * total['questions'] and set(per.values()) == {1},
              (len(per), dict(collections.Counter(per.values())), [k for k, v in per.items() if v != 1][:6]))
        os.makedirs(f'/root/aitsv_out/sweep_{tag}', exist_ok=True)
        for (mock, q, role), png in kept.items(): open(f'/root/aitsv_out/sweep_{tag}/m{mock}_q{q}_{role}.png', 'wb').write(png)
        pickle.dump(out, open(f'/root/link/real_{tag}.pkl', 'wb'))
    finally:
        # Only the disposable database this run created; never the app's own.
        assert H.TEST_DB.startswith('tejas_isolated_') and H.TEST_DB != H.REAL_DB, H.TEST_DB
        await H.tdbmod.client.drop_database(H.TEST_DB)
        print('dropped', H.TEST_DB, flush=True)
        f = [x for x in RESULTS if not x[1]]
        print(f'TOTAL {len(RESULTS)} PASS {len(RESULTS) - len(f)} FAIL {len(f)}', flush=True)


if __name__ == '__main__':
    asyncio.run(main(sys.argv[1], sys.argv[2]))
