"""TEST-ONLY: render question crops whose text contains another question-number line, or that are tall. Usage: python flagged_crops179.py book.pdf audit.json out.png count kind(other|tall)"""
import json, re, sys
import fitz
from PIL import Image, ImageDraw

src, audit, out, count, kind = sys.argv[1], sys.argv[2], sys.argv[3], int(sys.argv[4]), sys.argv[5]
doc = fitz.open(src); rows = json.load(open(audit)); hits = []
for r in rows:
    for g in r['q']:
        pg = doc[g['page'] - 1]; W, H = pg.rect.width, pg.rect.height; x0, y0, x1, y1 = g['rect']
        clip = fitz.Rect(x0 * W, y0 * H, x1 * W, y1 * H)
        if kind == 'tall':
            if y1 - y0 > .6: hits.append((r, g, clip))
        else:
            t = pg.get_text('text', clip=clip)
            other = [int(x) for x in re.findall(r'(?m)^(?:Question\s+)?(\d{1,3})[.)]\s', t) if int(x) != r['n']]
            if other: hits.append((r, g, clip, other))
print('hits', len(hits))
step = max(1, len(hits) // count); sel = hits[::step][:count]; tiles = []
for h in sel:
    r, g, clip = h[:3]
    print(r['mock'], 'Q', r['n'], 'p', g['page'], [round(v, 3) for v in g['rect']], h[3] if len(h) > 3 else '')
    pix = doc[g['page'] - 1].get_pixmap(dpi=50, clip=clip)
    im = Image.frombytes('RGB', [pix.width, pix.height], pix.samples)
    tile = Image.new('RGB', (im.width, im.height + 14), (255, 240, 200)); tile.paste(im, (0, 14))
    ImageDraw.Draw(tile).text((4, 1), f"{r['mock']} Q{r['n']} p{g['page']} key={r['answer']} {h[3] if len(h) > 3 else ''}", fill=(0, 0, 0)); tiles.append(tile)
w = max(t.width for t in tiles); hh = sum(t.height + 4 for t in tiles)
c = Image.new('RGB', (w, hh), 'gray'); y = 0
for t in tiles: c.paste(t, (0, y)); y += t.height + 4
c.save(out); print('saved', out, c.size)
