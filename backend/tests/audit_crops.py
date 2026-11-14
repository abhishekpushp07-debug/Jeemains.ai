"""TEST-ONLY: render random question/solution crops from a repro AUDIT json into one tall image for visual checks.
Usage: python tests/audit_crops.py book.pdf audit.json out.png [count] [seed]"""
import json, random, sys
import fitz
from PIL import Image, ImageDraw

src, audit, out = sys.argv[1:4]
count = int(sys.argv[4]) if len(sys.argv) > 4 else 8
random.seed(int(sys.argv[5]) if len(sys.argv) > 5 else 7)
rows = random.sample(json.load(open(audit)), count)
doc = fitz.open(src); tiles = []
for r in rows:
    for role in ('q', 's'):
        for g in r[role][:2]:
            pg = doc[g['page'] - 1]; W, H = pg.rect.width, pg.rect.height; x0, y0, x1, y1 = g['rect']
            pix = pg.get_pixmap(dpi=55, clip=fitz.Rect(x0 * W, y0 * H, x1 * W, min(y1, y0 + .35) * H))
            im = Image.frombytes('RGB', [pix.width, pix.height], pix.samples)
            tile = Image.new('RGB', (im.width, im.height + 14), (255, 240, 200) if role == 'q' else (210, 235, 255))
            tile.paste(im, (0, 14)); ImageDraw.Draw(tile).text((4, 1), f"{r['mock']} Q{r['n']} {role} p{g['page']} {r['type']} key={r['answer']}", fill=(0, 0, 0))
            tiles.append(tile)
w = max(t.width for t in tiles); h = sum(t.height + 4 for t in tiles)
canvas = Image.new('RGB', (w, h), 'gray'); y = 0
for t in tiles: canvas.paste(t, (0, y)); y += t.height + 4
canvas.save(out); print('saved', out, canvas.size, len(tiles), 'tiles')
