"""TEST-ONLY iteration 208: run a real PDF (or a page range of it) through PDF Engine 2.0 in a disposable DB and report every cut.
No AI, storage mocked. Run: cd /app/backend && python tests/cut_probe208.py <pdf> <first> <last> <section> <out_dir> [sheets]
Prints one line per mock and every held reason; writes picture sheets (question + options as students get them) to out_dir.
"""
import asyncio, collections, io, json, os, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import fitz  # noqa: E402
from PIL import Image, ImageDraw  # noqa: E402
import book_publishing_iso170 as T  # noqa: E402,F401
from book_publishing_iso170 import H, mkstaff, upload, complete, drain  # noqa: E402
from tejas import structure  # noqa: E402

SRC, FIRST, LAST, SECTION, OUT = sys.argv[1], int(sys.argv[2]), int(sys.argv[3]), sys.argv[4], sys.argv[5]
SHEETS = int(sys.argv[6]) if len(sys.argv) > 6 else 4
PER = 6


def subset():
    src = fitz.open(SRC); last = min(LAST, src.page_count)
    doc = fitz.open(); doc.insert_pdf(src, from_page=FIRST - 1, to_page=last - 1)
    toc = [[l, t, p - FIRST + 1] for l, t, p in src.get_toc() if FIRST <= p <= last]
    while toc and toc[0][0] != 1:
        toc.pop(0)
    try: doc.set_toc(toc)
    except Exception as e: print('toc skipped', e)
    raw = doc.tobytes(garbage=3, deflate=True); doc.close(); src.close()
    return raw


def picture(doc, part):
    page = doc[part['page'] - 1]; w, h = page.rect.width, page.rect.height; r = part['rect']
    pix = page.get_pixmap(matrix=fitz.Matrix(2, 2), clip=fitz.Rect(r[0] * w, r[1] * h, r[2] * w, r[3] * h), alpha=False)
    for e in part.get('erase', []):
        box = fitz.IRect(int(e[0] * w * 2) - 1, int(e[1] * h * 2) - 1, int(e[2] * w * 2 + 1) + 1, int(e[3] * h * 2 + 1) + 1) & pix.irect
        if not box.is_empty: pix.set_rect(box, (255, 255, 255))
    return Image.open(io.BytesIO(pix.tobytes('png'))).convert('RGB')


def card(doc, q):
    cut = q.get('cut') or {}; rows = []
    head = f"Q{q['original_number']} {q['type']} key={q.get('answer') or '-'} cut={cut.get('status')} {cut.get('arrangement', '')}"
    if cut.get('status') in ('ok', 'manual', 'trim'):
        rows = [(p['part'], picture(doc, p)) for p in cut['parts']]
    else:
        rows = [('HELD', picture(doc, {'page': r['page'], 'rect': r['rect']})) for r in q['source_regions']['question']]
        head += ' :: ' + cut.get('reason', '')
    width = max(900, max(im.width for _, im in rows) + 70); height = 26 + sum(im.height + 8 for _, im in rows)
    out = Image.new('RGB', (width, height), (236, 238, 242)); d = ImageDraw.Draw(out); d.text((6, 6), head[:150], fill=(150, 0, 0)); y = 26
    for name, im in rows:
        d.text((6, y + 4), name, fill=(0, 60, 160)); out.paste(im, (60, y)); d.rectangle((59, y - 1, 60 + im.width, y + im.height), outline=(120, 170, 255)); y += im.height + 8
    return out


def sheet(cards, path):
    width = max(c.width for c in cards); out = Image.new('RGB', (width, sum(c.height + 6 for c in cards)), (255, 255, 255)); y = 0
    for c in cards:
        out.paste(c, (0, y)); y += c.height + 6
    out.save(path, quality=60)


async def main():
    await H.tdbmod.indexes(); await structure.seed(); os.makedirs(OUT, exist_ok=True)
    try:
        own, _ = await mkstaff('owner', 'probe'); raw = subset()
        print('subset bytes', len(raw), flush=True)
        b = await upload(own, raw, 'TEST_PROBE', section_id=SECTION); await complete(own, b['id']); await drain(5000)
        book = await H.TDB.tejas_books.find_one({'_id': b['id']})
        print('BOOK', book['state'], book['payload'].get('message'), book['payload'].get('plan_source'), flush=True)
        mocks = await H.TDB.tejas_book_mocks.find({'book_id': b['id']}).sort('order', 1).to_list(500)
        doc = fitz.open(stream=raw, filetype='pdf'); total = collections.Counter(); reasons = collections.Counter(); shapes = collections.Counter(); held = []
        for m in mocks:
            qs = m['questions']; total['mocks'] += 1; total['questions'] += len(qs)
            print('MOCK', m['label'], '|', (m.get('chapter') or {}).get('title'), '|', m['state'], json.dumps(m.get('cut_summary')), 'types', dict(collections.Counter(q['type'] for q in qs)),
                  'nokey', sum(not q.get('answer') for q in qs), 'issues', [i for i in m['issues'] if 'saaf nahi kate' not in i][:4], flush=True)
            for q in qs:
                cut = q.get('cut') or {}; total[cut.get('status', 'none')] += 1; shapes[cut.get('arrangement', '')] += 1
                if cut.get('status') == 'held':
                    reasons[cut.get('reason', '')[:70]] += 1; held.append((m['label'], q)); print('   HELD', m['label'], 'Q', q['original_number'], 'page', [r['page'] + FIRST - 1 for r in q['source_regions']['question']], cut.get('reason'), flush=True)
        print('TOTAL', dict(total)); print('SHAPES', dict(shapes)); print('REASONS', json.dumps(reasons.most_common(20), ensure_ascii=False, indent=1))
        flat = [q for m in mocks for q in m['questions']]
        step = max(1, len(flat) // (SHEETS * PER)) if flat else 1
        picked = flat[::step][:SHEETS * PER]
        for n in range(0, len(picked), PER):
            sheet([card(doc, q) for q in picked[n:n + PER]], f'{OUT}/sample_{n // PER}.jpg')
        for n in range(0, min(len(held), 3 * PER), PER):
            sheet([card(doc, q) for _, q in held[n:n + PER]], f'{OUT}/held_{n // PER}.jpg')
        # Every question's page regions, so a held cut can be looked at next to its neighbours on the page.
        json.dump([{'mock': m['label'], 'n': q['original_number'], 'cut': (q.get('cut') or {}).get('status'), 'regions': q['source_regions']['question']} for m in mocks for q in m['questions']], open(f'{OUT}/regions.json', 'w'))
        print('SHEETS', sorted(os.listdir(OUT)), flush=True)
    finally:
        assert H.TEST_DB.startswith('tejas_isolated_') and H.TEST_DB != H.REAL_DB
        await H.tdbmod.client.drop_database(H.TEST_DB); print('dropped', H.TEST_DB, flush=True)


if __name__ == '__main__':
    asyncio.run(main())
