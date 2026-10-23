# Independent Phase-A source audit for the staged JEE Main chapter books (READ-ONLY).
# Uses poppler (pdftotext) instead of the PyMuPDF importer parser; never writes to MongoDB.
import hashlib
import html
import json
import os
import re
import subprocess
import sys
import tempfile
from pathlib import Path

from pymongo import MongoClient

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from dotenv import load_dotenv
load_dotenv(ROOT / '.env')
from tejas_storage import get_object  # read-only GET

SRC = Path('/tmp/jee_chapter_import')
MANIFEST = Path('/app/data/jee_chapters/import_manifest.json')
OUT = Path(sys.argv[1] if len(sys.argv) > 1 else '/app/test_reports/jee_chapter_source_audit.json')
EXPECT = {'Physics': (29, 90, 60), 'Mathematics': (26, 120, 90), 'Chemistry': (23, 70, 40)}
db = MongoClient(os.environ['MONGO_URL'])[os.environ['DB_NAME']]
sha = lambda b: hashlib.sha256(b).hexdigest()
norm = lambda s: s.replace('−', '-').replace('–', '-')
WORD = re.compile(r'<word xMin="([\d.]+)" yMin="([\d.]+)" xMax="([\d.]+)" yMax="([\d.]+)">(.*?)</word>')
PAGE = re.compile(r'<page width="([\d.]+)" height="([\d.]+)">(.*?)</page>', re.S)


def bbox_pages(path):
    out = subprocess.run(['pdftotext', '-bbox', str(path), '-'], capture_output=True, text=True, check=True).stdout
    pages = []
    for w, h, body in PAGE.findall(out):
        words = [(float(a), float(b), float(c), float(d), norm(html.unescape(t))) for a, b, c, d, t in WORD.findall(body)]
        pages.append({'w': float(w), 'h': float(h), 'words': words})
    return pages


def text_pages(path):
    return subprocess.run(['pdftotext', '-layout', str(path), '-'], capture_output=True, text=True, check=True).stdout.split('\f')


def lines_of(words):
    rows = []
    for wd in sorted(words, key=lambda w: (round(w[1]), w[0])):
        row = next((r for r in rows if abs(r[0][1] - wd[1]) < 2.5), None)
        (rows.append([wd]) if row is None else row.append(wd))
    for r in rows: r.sort(key=lambda w: w[0])
    return rows


def inside(wd, rect):
    cx, cy = (wd[0] + wd[2]) / 2, (wd[1] + wd[3]) / 2
    return rect[0] <= cx <= rect[2] and rect[1] <= cy <= rect[3]


def audit_book(book, subject):
    issues, rows = [], []
    pdf = SRC / (subject.lower() + '.pdf')
    raw = pdf.read_bytes()
    if sha(raw) != book['source_sha256']: issues.append('source sha mismatch vs manifest')
    dbbook = db.tejas_chapter_books.find_one({'id': book['id']}, {'_id': 0})
    if not dbbook or dbbook['source']['sha256'] != sha(raw): issues.append('DB book source sha mismatch')
    parsed = json.loads((SRC / (subject.lower() + '.parsed.json')).read_text())
    psha = sha(json.dumps(parsed, sort_keys=True).encode())
    if psha != book['parsed_sha256'] or (dbbook and dbbook.get('parsed_sha256') != psha): issues.append('parsed sha mismatch')
    pages, texts = bbox_pages(pdf), text_pages(pdf)
    cover = texts[0]
    m = re.search(r'(\d+) chapters / (\d+) questions / (\d+) minutes per chapter', cover)
    n_exp, online, printed = EXPECT[subject]
    if not m or int(m[1]) != n_exp or int(m[2]) != n_exp * 50 or int(m[3]) != printed:
        issues.append(f'cover mismatch {m and m.groups()}')
    # independent chapter starts: pages whose first body lines are "Chapter N" then title
    starts = []
    for pi, p in enumerate(pages):
        ls = [' '.join(w[4] for w in r) for r in lines_of([w for w in p['words'] if w[1] > 45])]
        if ls and re.fullmatch(r'Chapter \d+', ls[0]) and len(ls) > 2 and 'Chapter test' in ls[2:4]:
            starts.append((int(ls[0].split()[1]), ls[1], pi + 1))
    if [s[0] for s in starts] != list(range(1, n_exp + 1)): issues.append(f'independent chapter-start detection found {len(starts)}')
    if len(book['chapters']) != n_exp: issues.append('manifest chapter count')
    for ci, c in enumerate(book['chapters']):
        rows.append(audit_chapter(book, c, subject, pages, texts, starts, raw, online, printed, psha))
    return issues, rows


def audit_chapter(book, c, subject, pages, texts, starts, raw, online, printed, psha):
    iss = []
    s = db.tejas_sets.find_one({'id': c['set_id']}, {'_id': 0})
    st = next((x for x in starts if x[0] == c['number']), None)
    nxt = next((x for x in starts if x[0] == c['number'] + 1), None)
    end = (nxt[2] - 1) if nxt else len(pages)
    if not st or st[2] != c['start_page'] or end != c['end_page']: iss.append(f'page range mismatch {st} {end}')
    if st and st[1] != c['title']: iss.append(f'title mismatch {st[1]!r} vs {c["title"]!r}')
    sp, ep = c['start_page'], c['end_page']
    intro = norm(texts[sp - 1])
    mm = re.search(r'50 questions / (\d+) minutes / Maximum 200 marks', intro)
    ty = re.search(r'(\d+) single-correct questions and (\d+) integer-response', re.sub(r'\s+', ' ', intro))
    if not mm or int(mm[1]) != printed: iss.append('printed timer mismatch')
    if '+4 for correct, -1 for incorrect and 0 for unanswered' not in re.sub(r'\s+', ' ', intro): iss.append('printed scoring statement missing')
    # key page
    kps = [p for p in range(sp, ep + 1) if re.search(r'^\s*Answer key\s*$', texts[p - 1], re.M)]
    if len(kps) != 1: iss.append(f'key pages {kps}'); return fail_row(book, c, s, iss, psha)
    kp = kps[0]
    if s and s.get('key_page') != kp: iss.append('key_page mismatch')
    P = pages[kp - 1]
    hy = {' '.join(w[4] for w in r): r[0][1] for r in lines_of(P['words'])}
    a_y, w_y = hy.get('Answer key'), hy.get('Worked solutions and insights')
    keys = {}
    for r in lines_of([w for w in P['words'] if a_y < w[1] < w_y]):
        toks = [w[4] for w in r]
        for i in range(0, len(toks) - 1, 2):
            if toks[i].isdigit(): keys[int(toks[i])] = toks[i + 1]
    # second read: layout text tokens
    block = norm(texts[kp - 1]).split('Answer key', 1)[1].split('Worked solutions and insights', 1)[0].split()
    keys2 = {int(block[i]): block[i + 1] for i in range(0, len(block) - 1, 2) if block[i].isdigit()}
    if sorted(keys) != list(range(1, 51)) or keys != keys2: iss.append('key table read incomplete/disagree')
    # anchors (Qn. at left margin) on question pages and solution pages
    def anchors(p0, p1, after_y=None):
        out = []
        for pi in range(p0, p1 + 1):
            for wd in pages[pi - 1]['words']:
                if re.fullmatch(r'Q\d{1,2}\.', wd[4]) and wd[0] < 70 and wd[1] > 45 and (pi != kp or after_y is None or wd[1] > after_y):
                    out.append((int(wd[4][1:-1]), pi, wd[1]))
        return out
    qa = anchors(sp, kp - 1)
    sa = anchors(kp, ep, w_y)
    if [a[0] for a in qa] != list(range(1, 51)) or [a[0] for a in sa] != list(range(1, 51)): iss.append('anchor sequence')
    qs = {q['number']: q for q in (s or {}).get('questions', [])}
    if sorted(qs) != list(range(1, 51)): iss.append('DB question numbers')
    file_ok = check_file(s, c, raw, sp, ep, texts, iss)
    nm = ni = 0
    covered = {}
    for n in range(1, 51):
        q = qs.get(n)
        if not q: continue
        k = keys.get(n)
        if q['answer'] != k: iss.append(f'Q{n} DB answer {q["answer"]} != source key {k}')
        # solution answer line
        stext = norm(region_text(pages, q['s_refs'], sp))
        sm = re.search(r'Answer:\s*([A-D]|[+-]?\d+)\s*/\s*10-mark solution', stext)
        if not sm or sm[1] != k: iss.append(f'Q{n} worked answer {sm and sm[1]} != key {k}')
        if not re.match(rf'\s*Q{n}\.', stext) or re.findall(r'(?m)^\s*Q(\d{1,2})\.', region_lines(pages, q['s_refs'], sp)) != [str(n)]:
            iss.append(f'Q{n} solution crop not exactly Q{n}')
        marks = sum(map(int, re.findall(r'\[(\d+) marks?\]', stext)))
        if marks != 10 or not all(x in stext for x in ('Insight:', 'Trap:', 'Quick check:')): iss.append(f'Q{n} worked solution incomplete ({marks})')
        qtext = norm(region_text(pages, q['q_refs'], sp))
        if re.findall(r'(?m)^\s*Q(\d{1,2})\.', region_lines(pages, q['q_refs'], sp)) != [str(n)]: iss.append(f'Q{n} question crop not exactly Q{n}')
        if 'Single correct' in qtext.split('\n')[0] + qtext[:60]:
            nm += 1
            if q['type'] != 'mcq' or k not in ('A', 'B', 'C', 'D') or not all(f'({o})' in qtext for o in 'ABCD'): iss.append(f'Q{n} mcq type/options/key')
        elif 'Integer response' in qtext[:60]:
            ni += 1
            if q['type'] != 'integer' or not re.fullmatch(r'[+-]?\d+', k or ''): iss.append(f'Q{n} integer type/key')
        else: iss.append(f'Q{n} response type label missing')
        for ref in q['q_refs'] + q['s_refs']:
            if ref.get('file_id') != (s['file_ids'][0] if s else None) or not 1 <= ref['page'] <= ep - sp + 1: iss.append(f'Q{n} ref file/page')
            bp = ref['page'] + sp - 1
            for wi, wd in enumerate(pages[bp - 1]['words']):
                if inside(wd, ref['rect']): covered[(bp, wi)] = covered.get((bp, wi), 0) + 1
    if ty and (nm, ni) != (int(ty[1]), int(ty[2])): iss.append(f'type counts {nm}/{ni} vs printed {ty.groups()}')
    # coverage: every body word from Q1 to end (excluding key table area) belongs to exactly one crop
    lost, dup = 0, 0
    q1p, q1y = (qa[0][1], qa[0][2]) if qa else (sp, 0)
    s1y = sa[0][2] if sa else 0
    for pi in range(sp, ep + 1):
        P2 = pages[pi - 1]
        for wi, wd in enumerate(P2['words']):
            if wd[1] < 40 or wd[1] > P2['h'] - 45: continue
            if pi < q1p or (pi == q1p and wd[1] < q1y - 1): continue
            if pi == kp and wd[1] < s1y - 1: continue
            cnt = covered.get((pi, wi), 0)
            if cnt == 0: lost += 1
            elif cnt > 1: dup += 1
    if lost or dup: iss.append(f'crop coverage lost={lost} duplicated={dup}')
    # rules / status / timers
    if s:
        r = s['rules']
        if (r.get('minutes'), r.get('correct'), r.get('wrong'), r.get('skipped')) != (online, 4, -1, 0): iss.append(f'rules {r}')
        if s.get('source_minutes') != printed or s.get('status') != 'draft' or s.get('independent_check') is not None: iss.append('status/source_minutes')
        if s.get('exam') != 'JEE Main' or s.get('test_kind') != 'chapter' or s.get('chapter_subject') != subject: iss.append('exam/kind/subject')
    return {'book_id': book['id'], 'set_id': c['set_id'], 'subject': subject, 'number': c['number'], 'title': c['title'],
            'status': 'PASS' if not iss else 'FAIL', 'keys_checked': 50 if not iss else len(keys), 'solutions_checked': 50 if not iss else 0,
            'mcq': nm, 'integer': ni, 'pages': [sp, ep], 'key_page': kp, 'file_verified': file_ok,
            'source_book_sha256': book['source_sha256'], 'parsed_sha256': psha, 'chapter_source_sha256': c['source_sha256'], 'issues': iss}


def fail_row(book, c, s, iss, psha):
    return {'book_id': book['id'], 'set_id': c['set_id'], 'status': 'FAIL', 'keys_checked': 0, 'solutions_checked': 0, 'issues': iss,
            'source_book_sha256': book['source_sha256'], 'parsed_sha256': psha, 'chapter_source_sha256': c['source_sha256']}


def region_words(pages, refs, sp):
    out = []
    for ref in refs:
        P = pages[ref['page'] + sp - 2]
        out.append(lines_of([w for w in P['words'] if inside(w, ref['rect'])]))
    return out


def region_text(pages, refs, sp):
    return '\n'.join(' '.join(w[4] for w in r) for rows in region_words(pages, refs, sp) for r in rows)


def region_lines(pages, refs, sp):
    return '\n'.join(' '.join(w[4] for w in r) for rows in region_words(pages, refs, sp) for r in rows if r[0][0] < 70)


def check_file(s, c, raw, sp, ep, texts, iss):
    f = db.tejas_files.find_one({'id': c['source_file_id']}, {'_id': 0})
    if not f or not s or s['file_ids'] != [c['source_file_id']] or f['sha256'] != c['source_sha256'] or f.get('is_deleted'):
        iss.append('file record mismatch'); return False
    data = get_object(f['path'])
    if sha(data) != f['sha256'] or len(data) != f['size']: iss.append('stored chapter bytes hash mismatch'); return False
    with tempfile.NamedTemporaryFile(suffix='.pdf') as t:
        t.write(data); t.flush()
        sub = text_pages(t.name)
    sub = [x for x in sub if x is not None][:ep - sp + 1 + 1]
    body = [p for p in sub]
    if len([p for p in body if p.strip()]) != ep - sp + 1 or any(body[i] != texts[sp - 1 + i] for i in range(ep - sp + 1)):
        iss.append('stored chapter pages differ from book range'); return False
    return True


def main():
    man = json.loads(MANIFEST.read_text())
    report = {'method': 'Independent poppler pdftotext (bbox+layout) re-read of supplied PDFs; read-only DB/storage; not academic certification',
              'books': [], 'chapters': []}
    for book in man['books']:
        bi, rows = audit_book(book, book['subject'])
        report['books'].append({'id': book['id'], 'subject': book['subject'], 'chapters': len(rows), 'issues': bi,
                                'questions': sum(50 for r in rows if r['status'] == 'PASS')})
        report['chapters'] += rows
        print(book['subject'], len(rows), 'chapters', sum(r['status'] == 'PASS' for r in rows), 'PASS', bi, flush=True)
    names = {b['subject'] for b in man['books']}
    allok = names == set(EXPECT) and all(not b['issues'] for b in report['books']) and all(r['status'] == 'PASS' for r in report['chapters'])
    report['status'] = 'PASS' if allok else 'FAIL'
    OUT.write_text(json.dumps(report, indent=1, ensure_ascii=False))
    for r in report['chapters']:
        if r['issues']: print(r.get('subject'), r.get('number'), r['issues'][:6])
    print('OVERALL', report['status'], len(report['chapters']))


if __name__ == '__main__':
    main()
