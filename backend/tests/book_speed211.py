"""TEST-ONLY iteration 211: the owner's whole boxed chemistry book through the real app (upload -> Draft) in a disposable DB.
Measures how long the owner waits, and checks every question: question box, four option boxes, its answer key and its own worked solution.
Then two small copies of chapter 8 prove the solution check: a solution that prints another question's source is held; solution pages
printed out of order still go to the right question (matched by the 'Question N' printed on them, never by position).
Run: cd /app/backend && python tests/book_speed211.py [full|small]   (drops its database at the end; storage is mocked)
"""
import asyncio, collections, json, re, sys, time, uuid
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import fitz  # noqa: E402
import cut_bridge207 as B  # noqa: E402
from cut_bridge207 import H, J, BM, DB, mkstaff, upload, drain  # noqa: E402
from tejas import structure  # noqa: E402

REAL = '/root/pdfengine/chemistry_chapterwise.pdf'
RESULTS = []


def check(name, ok, detail=''):
    RESULTS.append((name, bool(ok)))
    print(('PASS ' if ok else 'FAIL ') + name + ('' if ok else ' :: ' + str(detail)[:600]), flush=True)


def chapter8(change=None):
    """Chapter 8 of the owner's book (16 questions, key, 16 solutions). change='source': Q1's solution prints another source.
    change='swap': the solution pages of Q1 and Q2 are printed the other way round."""
    src = fitz.open(REAL); doc = fitz.open(); doc.insert_pdf(src, from_page=706, to_page=738); doc.insert_pdf(src, from_page=2522, to_page=2526)
    sol = [i for i in range(len(doc)) if re.search(r'^Question 1\s*$', doc[i].get_text(), re.M) and 'DETAILED SOLUTION' in doc[i].get_text()][0]
    # Two chapters, as in the owner's book: the PDF's bookmarks split a book only when it has more than one chapter.
    toc = [[1, '08 Redox Reactions', 1], [2, 'Questions', 1], [2, 'Answer key', 17], [2, 'Solutions', 18],
           [1, '24 Miscellaneous', 34], [2, 'Questions', 34], [2, 'Answer key', 36], [2, 'Solutions', 37]]
    if change == 'source':
        page = doc[sol]; label = page.search_for('Source:')[0]; value = page.search_for('AITS Mock')[0]
        line = fitz.Rect(label.x0 - 1, min(label.y0, value.y0) - 1, page.rect.x1 - 20, max(label.y1, value.y1) + 1)
        page.add_redact_annot(line, fill=(1, 1, 1)); page.apply_redactions()
        page.insert_text((label.x0, label.y1 - 2), 'Source: AITS Mock 99 / Q99', fontsize=8)
    if change == 'swap':
        doc.move_page(sol + 1, sol)
    doc.set_toc(toc)
    raw = doc.tobytes(garbage=3, deflate=True); doc.close(); src.close()
    return raw + b'\n%' + uuid.uuid4().hex.encode()


async def run_book(own, sec, raw, title):
    t0 = time.time(); b = await upload(own, raw, title, section_id=sec, subject='Chemistry'); t_up = time.time() - t0
    seen = []
    async def watch():
        while True:
            bk = await DB.tejas_books.find_one({'_id': b['id']}, {'state': 1, 'payload.read_pages': 1})
            mark = (bk['state'], (bk['payload'].get('read_pages') or 0) >= 2527 or bk['state'] != 'reading')
            if not seen or seen[-1][1] != mark:
                seen.append((round(time.time() - t0, 1), mark)); print('  at', seen[-1][0], 's', bk['state'], bk['payload'].get('read_pages'), flush=True)
            await asyncio.sleep(2)
    w = asyncio.create_task(watch())
    t1 = time.time(); await own.post(f"/api/admin/books/{b['id']}/complete"); await drain(100000); t_draft = time.time() - t1
    w.cancel()
    rows = await BM.find({'book_id': b['id']}).sort('order', 1).to_list(100)
    return b['id'], rows, t_up, t_draft


def report(rows):
    total = collections.Counter(); bad = []
    for m in rows:
        qs = m['questions']; c = collections.Counter((q.get('cut') or {}).get('status') for q in qs)
        kinds = collections.Counter(q['solution_kind'] for q in qs)
        total.update(questions=len(qs), **{'cut_' + str(k): v for k, v in c.items()}, **{k: v for k, v in kinds.items()})
        total['no_key'] += sum(not q['answer'] for q in qs)
        total['boxes'] += sum((q.get('cut') or {}).get('arrangement') == 'boxes' for q in qs)
        total['held_mocks'] += m['state'] == 'held'
        total['source_mismatch'] += sum('kisi aur sawaal' in i for i in m['issues'])
        if m['state'] == 'held':
            bad.append((m['label'], m['issues'][:3]))
        print(f"  {m['label']:11} {(m.get('chapter') or {}).get('title', '')[:38]:38} {m['state']:6} q={len(qs):3} cut={dict(c)} solutions={dict(kinds)}", flush=True)
    return total, bad


async def full(own, chap):
    raw = open(REAL, 'rb').read()
    bid, rows, t_up, t_draft = await run_book(own, chap, raw, 'TEST_BOXED_FULL')
    total, bad = report(rows)
    print('UPLOAD', round(t_up, 1), 's  COMPLETE->DRAFT', round(t_draft, 1), 's', dict(total), flush=True)
    check('24 chapters arrive as Draft mocks', len(rows) == 24, len(rows))
    check('1250 questions found', total['questions'] == 1250, total['questions'])
    check('no chapter held', total['held_mocks'] == 0, bad[:6])
    check('1000 option questions cut by their printed boxes', total['boxes'] == 1000, total['boxes'])
    check('every question cut clean (ok or numerical trim)', total['cut_ok'] + total['cut_trim'] == 1250, dict(total))
    check('every question has its answer key', total['no_key'] == 0, total['no_key'])
    check('every question has its own worked solution', total['supplied_worked'] == 1250, dict(total))
    check('every solution prints the same source as its question', total['source_mismatch'] == 0, total['source_mismatch'])
    # Spot check: each question's solution region is on a page that prints that question's 'Question N' heading and the same source.
    doc = fitz.open(REAL); wrong = []
    for m in rows:
        for q in m['questions']:
            pages = [r['page'] for r in q['source_regions']['solution']]
            page_text = doc[pages[0] - 1].get_text() if pages else ''
            src = re.findall(r'Source:\s*(.+)', doc[q['source_regions']['question'][0]['page'] - 1].get_text())
            if not pages or not re.search(rf'^Question {q["original_number"]}\s*$', page_text, re.M) or not src or src[0].strip() not in page_text:
                wrong.append((m['label'], q['original_number'], pages))
    check('every solution picture is the page of that same question (number and source)', not wrong, wrong[:8])
    return t_draft


async def small(own, chap):
    _, rows, _, _ = await run_book(own, chap, chapter8('source'), 'TEST_SRC')
    m = rows[0]; mine = [i for i in m['issues'] if 'kisi aur sawaal' in i]
    print('  issues', m['issues'][:4], flush=True)
    check('a solution printing another source is held, with the reason', m['state'] == 'held' and len(mine) == 1 and 'Q1:' in mine[0] and 'Q99' in mine[0], m['issues'][:4])
    _, rows, _, _ = await run_book(own, chap, chapter8('swap'), 'TEST_SWAP')
    m = rows[0]; q1 = next(q for q in m['questions'] if q['original_number'] == 1); q2 = next(q for q in m['questions'] if q['original_number'] == 2)
    check('solution pages out of order still reach the right question', m['state'] == 'ready' and q1['source_regions']['solution'][0]['page'] > q2['source_regions']['solution'][0]['page'],
          (m['state'], m['issues'][:3], q1['source_regions']['solution'], q2['source_regions']['solution']))


async def main(which):
    assert not H.leftover_real_handles()
    await H.tdbmod.indexes(); await structure.seed()
    try:
        own, _ = await mkstaff('owner', 'speed')
        slug = B.J(await own.post('/api/admin/catalog/exams', json={'name': 'SPEEDX', 'short': 'SX', 'subjects': ['Chemistry'], 'color': 'rose'})).get('slug')
        chap = B.J(await own.post(f'/api/admin/catalog/exams/{slug}/sections', json={'name': 'Chapter-wise', 'description': '', 'layout': 'chapters', 'kind': 'chapters'})).get('id')
        if which in ('small', 'both'):
            await small(own, chap)
        if which in ('full', 'both'):
            await full(own, chap)
    finally:
        assert H.TEST_DB.startswith('tejas_isolated_'), H.TEST_DB
        await H.tdbmod.client.drop_database(H.TEST_DB)
        print('dropped', H.TEST_DB, flush=True)
        f = [r for r in RESULTS if not r[1]]
        print(f'TOTAL {len(RESULTS)} PASS {len(RESULTS) - len(f)} FAIL {len(f)}', flush=True)
        json.dump(RESULTS, open('/root/pdfengine/scans/speed211_results.json', 'w'), indent=1)


if __name__ == '__main__':
    asyncio.run(main(sys.argv[1] if len(sys.argv) > 1 else 'both'))
