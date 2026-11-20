"""TEST-ONLY iteration 209: PDF Engine 2.0 over a real chapter-wise book WITHOUT any database.
The app's own page reader finds every question; the app's own cutter cuts it. One process per chapter. No AI, no storage, no DB.
Scan:   cd /app/backend && python tests/cut_scan209.py scan <pdf> <out_dir> [first_chapter last_chapter]
Sheets: cd /app/backend && python tests/cut_scan209.py sheets <pdf> <out_dir> held|ok|<chapter>:<q>,<chapter>:<q>... [count]
"""
import collections, io, json, os, sys, time
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT), str(ROOT / 'tejas')]
from dotenv import load_dotenv  # noqa: E402
load_dotenv(ROOT / '.env')
import fitz  # noqa: E402
from book_pdf_worker import handle  # noqa: E402
from book_cutter import cut_region, trim_region  # noqa: E402
from tejas.book_reader import read_page  # noqa: E402
from tejas.chapter_reader import bookmark_plan, plan_start  # noqa: E402


def chapter(job):
    pdf, label, title, entries, first, last = job
    doc = fitz.open(pdf); context = {'chapters': True, 'plan': True}; groups = collections.OrderedDict(); keys = {}; issues = {}
    for n in range(first, last + 1):
        for e in entries.get(str(n), []):
            context = plan_start(context, e)
        data = handle(doc, {'action': 'text', 'page': n})
        mapped, context = read_page(data['lines'], context, data.get('geometry', []), data.get('images', []))
        if mapped.issues:
            issues[n] = mapped.issues
        for r in mapped.regions:
            if r.mock != label:
                continue
            if r.role == 'question':
                groups.setdefault(r.number, []).append((n, r))
            elif r.role == 'key' and r.answer:
                keys.setdefault(r.number, set()).add(r.answer)
    out = []
    for number, found in groups.items():
        labels = list(dict.fromkeys(x for _, r in found for x in r.option_labels)); head = found[0][1]
        kind = head.response_type if head.response_type != 'unresolved' or len(labels) < 2 else 'mcq'
        marked = [i for i, (_, r) in enumerate(found) if r.option_labels] if kind == 'mcq' else []
        at = marked[-1] if marked else len(found) - 1
        row = {'chapter': label, 'title': title, 'n': number, 'type': kind, 'labels': labels, 'key': sorted(keys.get(number, [])), 'status': 'trim', 'reason': '', 'arrangement': '',
               'regions': [{'page': n, 'rect': r.rect} for n, r in found], 'parts': [], 'draft': {}, 'ms': 0, 'checked': all(r.checked for _, r in found)}
        for i, (n, r) in enumerate(found):
            own = i == at and kind == 'mcq' and bool(labels); t = time.time()
            cut = cut_region(doc[n - 1], r.rect, labels) if own else trim_region(doc[n - 1], r.rect)
            row['ms'] += round((time.time() - t) * 1000)
            if cut['status'] == 'held' or (own and cut['status'] != 'ok'):
                row.update(status='held', reason=cut.get('reason') or 'Page ka yeh hissa kat nahi paya.', parts=[], draft=cut.get('draft') or {}); break
            if own:
                row.update(status=cut['status'], arrangement=cut.get('arrangement', ''))
            row['parts'] += [{'part': k, 'page': n, 'size': cut['size'], **cut['pieces'][k]} for k in ['q', *labels] if k in cut['pieces']]
        if row['status'] != 'held' and not any(p['part'] == 'q' for p in row['parts']):
            row.update(status='held', reason='Options ke upar kuch chhapa nahi hai, isliye sawaal ki picture nahi bani.', parts=[])
        out.append(row)
    return label, title, out, issues


def scan(pdf, out, lo, hi):
    doc = fitz.open(pdf); plan = bookmark_plan(doc.get_toc(simple=True), doc.page_count); pages = doc.page_count; doc.close()
    by = collections.OrderedDict()
    for e in plan:
        by.setdefault(e['label'], []).append(e)
    jobs = []
    for i, (label, entries) in enumerate(by.items(), 1):
        if not lo <= i <= hi:
            continue
        start = {e['role']: e['page'] for e in entries}
        nxt = min([e['page'] for e in plan if e['page'] > start['question'] and e['label'] != label] + [pages + 1])
        last = start.get('solution', nxt) - 1
        at = collections.defaultdict(list)
        for e in entries:
            at[str(e['page'])].append(e)
        jobs.append((pdf, label, entries[0]['title'], dict(at), start['question'], last))
    os.makedirs(out, exist_ok=True); total = collections.Counter(); reasons = collections.Counter(); shapes = collections.Counter(); t = time.time()
    with ProcessPoolExecutor(max_workers=min(12, len(jobs))) as pool:
        for label, title, rows, issues in pool.map(chapter, jobs):
            json.dump({'rows': rows, 'issues': issues}, open(f"{out}/{label.replace(' ', '_')}.json", 'w'))
            c = collections.Counter(r['status'] for r in rows); total.update(c); total['questions'] += len(rows)
            nokey = [r['n'] for r in rows if len(r['key']) != 1]; bad = [r['n'] for r in rows if r['type'] == 'mcq' and r['key'] and r['key'][0] not in r['labels']]
            unchecked = [r['n'] for r in rows if not r['checked']]; unresolved = [r['n'] for r in rows if r['type'] == 'unresolved']
            total['nokey'] += len(nokey); total['key_not_in_labels'] += len(bad); total['unchecked'] += len(unchecked); total['unresolved'] += len(unresolved); total['page_issues'] += len(issues)
            for r in rows:
                shapes[r['arrangement'] or r['status']] += 1
                if r['status'] == 'held':
                    reasons[r['reason'][:90]] += 1
            print(f"{label:11} {title[:40]:40} q={len(rows):3} {dict(c)} nokey={nokey[:6]} badkey={bad[:6]} unchecked={unchecked[:6]} unresolved={unresolved[:6]} page_issues={len(issues)} held={[r['n'] for r in rows if r['status'] == 'held']}", flush=True)
    print('TOTAL', dict(total), f'{time.time() - t:.0f}s'); print('SHAPES', dict(shapes)); print('REASONS', json.dumps(reasons.most_common(30), ensure_ascii=False, indent=1))


def picture(doc, part, scale=2):
    page = doc[part['page'] - 1]; w, h = page.rect.width, page.rect.height; r = part['rect']
    pix = page.get_pixmap(matrix=fitz.Matrix(scale, scale), clip=fitz.Rect(r[0] * w, r[1] * h, r[2] * w, r[3] * h), alpha=False)
    for e in part.get('erase', []):
        box = fitz.IRect(int(e[0] * w * scale) - 1, int(e[1] * h * scale) - 1, int(e[2] * w * scale + 1) + 1, int(e[3] * h * scale + 1) + 1) & pix.irect
        if not box.is_empty:
            pix.set_rect(box, (255, 255, 255))
    from PIL import Image
    return Image.open(io.BytesIO(pix.tobytes('png'))).convert('RGB')


def card(doc, q, scale):
    from PIL import Image, ImageDraw
    head = f"{q['chapter']} Q{q['n']} p{q['regions'][0]['page']} {q['type']} key={','.join(q['key']) or '-'} cut={q['status']} {q['arrangement']}"
    if q['status'] == 'held':
        rows = [('HELD', picture(doc, r, scale)) for r in q['regions']]; head += ' :: ' + q['reason']
    else:
        rows = [(p['part'], picture(doc, p, scale)) for p in q['parts']]
    width = max(900, max(im.width for _, im in rows) + 70); height = 26 + sum(im.height + 8 for _, im in rows)
    out = Image.new('RGB', (width, height), (236, 238, 242)); d = ImageDraw.Draw(out); d.text((6, 6), head[:170], fill=(150, 0, 0)); y = 26
    for name, im in rows:
        d.text((6, y + 4), name, fill=(0, 60, 160)); out.paste(im, (60, y)); d.rectangle((59, y - 1, 60 + im.width, y + im.height), outline=(120, 170, 255)); y += im.height + 8
    return out


def sheets(pdf, out, what, count, per=6, scale=1.4):
    from PIL import Image
    rows = [r for f in sorted(Path(out).glob('Chapter_*.json'), key=lambda p: int(p.stem.split('_')[1])) for r in json.load(open(f))['rows']]
    if what in ('held', 'ok'):
        picked = [r for r in rows if (r['status'] == 'held') == (what == 'held')]
        if what == 'ok':
            picked = picked[::max(1, len(picked) // count)]
    else:
        want = {tuple(int(v) for v in x.split(':')) for x in what.split(',')}
        picked = [r for r in rows if (int(r['chapter'].split()[1]), r['n']) in want]
    picked = picked[:count]; doc = fitz.open(pdf); tag = what if what in ('held', 'ok') else 'pick'
    for n in range(0, len(picked), per):
        cards = [card(doc, q, scale) for q in picked[n:n + per]]
        sheet = Image.new('RGB', (max(c.width for c in cards), sum(c.height + 6 for c in cards)), (255, 255, 255)); y = 0
        for c in cards:
            sheet.paste(c, (0, y)); y += c.height + 6
        sheet.save(f'{out}/{tag}_{n // per}.jpg', quality=55); print(f'{out}/{tag}_{n // per}.jpg', [(q['chapter'], q['n']) for q in picked[n:n + per]])


if __name__ == '__main__':
    if sys.argv[1] == 'scan':
        scan(sys.argv[2], sys.argv[3], int(sys.argv[4]) if len(sys.argv) > 4 else 1, int(sys.argv[5]) if len(sys.argv) > 5 else 999)
    else:
        sheets(sys.argv[2], sys.argv[3], sys.argv[4], int(sys.argv[5]) if len(sys.argv) > 5 else 18)
