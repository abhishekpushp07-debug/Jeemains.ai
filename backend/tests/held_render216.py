"""TEST-ONLY (iteration 216): render the 5 stuck-option cases from memory/pause_2026-11-20/held_cases.json with the v3 cutter
into one JPEG per case (stem + A-D stacked, erase rects painted white) so the cut can be checked by eye. Reads PDFs only."""
import json, sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
import fitz
from tejas import book_cutter as bc

OUT = '/app/.screenshots/held216'; os.makedirs(OUT, exist_ok=True)
cases = json.load(open('/app/memory/pause_2026-11-20/held_cases.json'))
for path, pno, rect, name in cases:
    doc = fitz.open(path); page = doc[pno]
    r = bc.cut_region(page, rect, ['A', 'B', 'C', 'D'])
    print(name, r['status'], r['arrangement'], r['reason'][:120])
    if r['status'] != 'ok':
        continue
    W, H = page.rect.width, page.rect.height
    imgs = []
    for k in ['q', 'A', 'B', 'C', 'D']:
        p = r['pieces'].get(k)
        if not p:
            continue
        x0, y0, x1, y1 = p['rect']
        clip = fitz.Rect(x0 * W, y0 * H, x1 * W, y1 * H)
        pix = page.get_pixmap(clip=clip, dpi=200)
        # paint erase rects
        from PIL import Image, ImageDraw
        im = Image.frombytes('RGB', (pix.width, pix.height), pix.samples)
        d = ImageDraw.Draw(im)
        for e in p.get('erase', []):
            ex0 = (e[0] * W - clip.x0) / clip.width * pix.width; ex1 = (e[2] * W - clip.x0) / clip.width * pix.width
            ey0 = (e[1] * H - clip.y0) / clip.height * pix.height; ey1 = (e[3] * H - clip.y0) / clip.height * pix.height
            d.rectangle([ex0, ey0, ex1, ey1], fill='white')
        imgs.append((k, im))
    from PIL import Image, ImageDraw
    tw = max(i.width for _, i in imgs) + 40; th = sum(i.height + 14 for _, i in imgs)
    can = Image.new('RGB', (tw, th), (200, 200, 200)); y = 0
    for k, im in imgs:
        ImageDraw.Draw(can).text((2, y), k, fill='red'); can.paste(im, (30, y + 10)); y += im.height + 14
    can.save(f'{OUT}/{name.replace(" ", "_")}.jpg', quality=70)
