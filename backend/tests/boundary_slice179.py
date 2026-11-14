"""TEST-ONLY: find question crops whose top/bottom boundary slices through a text span or drawing (e.g. a matrix raised above the question number).
Usage: python boundary_slice179.py book.pdf audit.json [out.png] [count]"""
import json, sys
import fitz
from PIL import Image, ImageDraw

src, audit = sys.argv[1], sys.argv[2]
out = sys.argv[3] if len(sys.argv) > 3 else None; count = int(sys.argv[4]) if len(sys.argv) > 4 else 8
doc = fitz.open(src); rows = json.load(open(audit)); cache = {}; hits = []
def boxes(pno):
    if pno not in cache:
        pg = doc[pno - 1]; H = pg.rect.height; bs = []
        for b in pg.get_text('rawdict')['blocks']:
            for l in b.get('lines', []):
                for s in l['spans']:
                    for c in s['chars']:
                        if c['c'].strip(): bs.append((c['bbox'][1] / H, c['bbox'][3] / H, c['c']))
        import os
        for d in ([] if os.environ.get('TEXTONLY') else pg.get_drawings()):
            r = d['rect']
            if r.height < H * .3: bs.append((r.y0 / H, r.y1 / H, 'drawing'))
        cache[pno] = bs
    return cache[pno]
for r in rows:
    for g in r['q']:
        y0, y1 = g['rect'][1], g['rect'][3]
        for edge in (y0, y1):
            cut = [c for c in boxes(g['page']) if c[0] + .002 < edge < c[1] - .002]
            if cut and edge > .06 and edge < .94:
                hits.append((r, g, edge, ''.join(sorted({c[2][:7] for c in cut}))[:30])); break
print('crops whose edge slices glyphs/drawings', len(hits))
for h in hits[:: max(1, len(hits) // 25)][:25]: print(' ', h[0]['mock'], 'Q', h[0]['n'], 'p', h[1]['page'], 'edge', round(h[2], 3), repr(h[3]))
if out and hits:
    tiles = []
    for r, g, edge, what in hits[:: max(1, len(hits) // count)][:count]:
        pg = doc[g['page'] - 1]; W, H = pg.rect.width, pg.rect.height
        pix = pg.get_pixmap(dpi=55, clip=fitz.Rect(0, max(0, edge - .05) * H, W, min(1, edge + .05) * H))
        im = Image.frombytes('RGB', [pix.width, pix.height], pix.samples); dr = ImageDraw.Draw(im)
        yy = int(min(.05, edge) * H * 55 / 72); dr.line([(0, yy), (im.width, yy)], fill=(255, 0, 0))
        t = Image.new('RGB', (im.width, im.height + 14), (255, 240, 200)); t.paste(im, (0, 14))
        ImageDraw.Draw(t).text((4, 1), f"{r['mock']} Q{r['n']} p{g['page']} edge={edge:.3f} {what}", fill=(0, 0, 0)); tiles.append(t)
    c = Image.new('RGB', (max(t.width for t in tiles), sum(t.height + 4 for t in tiles)), 'gray'); y = 0
    for t in tiles: c.paste(t, (0, y)); y += t.height + 4
    c.save(out); print('saved', out)
