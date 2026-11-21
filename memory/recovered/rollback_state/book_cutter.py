"""PDF Engine 2.0 cutter: one question region -> five pieces (question, A, B, C, D).
Uses only where the text sits and where the page is blank. No AI, no guessing: a cut that fails any check is held with its reason."""
import itertools
import re
import fitz
import numpy as np

CUT_VERSION = 1
SCALE = 2.0      # pixels per PDF point used to look at the ink
MARGIN = 4.0     # points of blank kept around every piece
STYLES = (('paren', r'\(\s?([A-Da-d1-4])\s?\)'), ('close', r'([A-Da-d1-4])\)'), ('dot', r'([A-Da-d])\.'))
KNOWN = 'ABCDabcd1234'


class Held(Exception):
    pass


def kind_of(ch):
    return 'd' if ch.isdigit() else 'U' if ch.isupper() else 'l'


def index_of(ch):
    return '1234'.index(ch) if ch.isdigit() else 'abcd'.index(ch.lower())


def cap(text):
    return text[:1].upper() + text[1:]


def text_lines(page, clip):
    out = []
    for block in page.get_text('rawdict', clip=clip).get('blocks', []):
        for line in block.get('lines', []):
            chars = [(c['c'], fitz.Rect(c['bbox']), s['size']) for s in line['spans'] for c in s['chars']]
            if chars:
                out.append(chars)
    return out


def candidates(lines):
    """Every printed token that looks like an option label, with its box in page points."""
    found = []
    for chars in lines:
        text = ''.join(c[0] for c in chars)
        for style, pattern in STYLES:
            for m in re.finditer(pattern, text):
                a, b = m.start(), m.end()
                size = chars[a][2]
                gap = chars[a][1].x0 - chars[a - 1][1].x1 if a else 99
                lead = not text[:a].strip()
                if style == 'paren':
                    if not (lead or text[a - 1].isspace() or gap > .25 * size):
                        continue
                else:
                    # 'A.' and 'A)' count only at the start of a line or after a clear gap, and need a space after them.
                    wide = chars[a][1].x0 - next((c[1].x1 for c in reversed(chars[:a]) if not c[0].isspace()), -999)
                    if (a and text[a - 1] == '(') or not (lead or wide > 1.2 * size) or (b < len(text) and not text[b].isspace()):
                        continue
                rect = fitz.Rect()
                for c in chars[a:b]:
                    if not c[0].isspace():
                        rect |= c[1]
                found.append({'i': index_of(m[1]), 'family': (style, kind_of(m[1])), 'rect': rect, 'size': size, 'ch': m[0].strip()})
    return found


def arrangement(s):
    """How the labels sit: one per line, two per line (row-wise or column-wise) or all in one line. None if they are not lined up."""
    n = len(s)
    tol = 1.1 * max(x['size'] for x in s)
    cy = [(x['rect'].y0 + x['rect'].y1) / 2 for x in s]
    x0 = [x['rect'].x0 for x in s]
    same = lambda a, b: abs(cy[a] - cy[b]) < .6 * s[a]['size']
    below = lambda a, b: cy[b] - cy[a] > .8 * s[a]['size']
    lined = lambda a, b: abs(x0[a] - x0[b]) <= tol
    if all(below(i, i + 1) and lined(0, i + 1) for i in range(n - 1)):
        return 'column', [[i] for i in range(n)]
    if all(same(0, i) for i in range(1, n)) and all(x0[i] < x0[i + 1] for i in range(n - 1)):
        return 'row', [list(range(n))]
    if n != 4:
        return None
    if same(0, 1) and same(2, 3) and below(0, 2) and x0[0] < x0[1] and x0[2] < x0[3] and lined(0, 2) and lined(1, 3):
        return 'grid', [[0, 1], [2, 3]]
    if same(0, 2) and same(1, 3) and below(0, 1) and x0[0] < x0[2] and x0[1] < x0[3] and lined(0, 1) and lined(2, 3):
        return 'grid', [[0, 2], [1, 3]]
    return None


def choose(found, kinds, want=(0, 1, 2, 3)):
    """The last full set of the wanted labels that is lined up; statement labels higher in the question lose to it."""
    best = None
    for family in {c['family'] for c in found if c['family'][1] in kinds}:
        per = [[c for c in found if c['family'] == family and c['i'] == i][-8:] for i in want]
        if not per or not all(per):
            continue
        for s in itertools.product(*per):
            s = list(s)
            shape = arrangement(s)
            if not shape:
                continue
            key = (min(x['rect'].y0 for x in s), family[0] == 'paren', -max(x['rect'].y1 for x in s))
            if not best or key > best[0]:
                best = (key, s, shape)
    return best and (best[1], best[2])


def bands(flags, least):
    """Runs of blank rows or columns at least `least` pixels long."""
    out, start = [], None
    for i, on in enumerate(list(flags) + [True]):
        if not on and start is None:
            start = i
        elif on and start is not None:
            if i - start >= least:
                out.append((start, i))
            start = None
    return out


def neck(mask, x0, x1, ya, yb):
    """The emptiest pixel row between ya and yb in columns x0..x1 (the middle of the lowest such run)."""
    if yb <= ya or x1 <= x0:
        return max(0, yb)
    ink = mask[ya:yb, x0:x1].sum(axis=1)
    low = set(np.flatnonzero(ink == ink.min()).tolist())
    end = start = max(low)
    while start - 1 in low:
        start -= 1
    return ya + (start + end + 1) // 2


def box_of(mask, x0, y0, x1, y1):
    part = mask[y0:y1, x0:x1]
    ys, xs = np.where(part.any(axis=1))[0], np.where(part.any(axis=0))[0]
    return None if not len(ys) else (x0 + int(xs[0]), y0 + int(ys[0]), x0 + int(xs[-1]) + 1, y0 + int(ys[-1]) + 1)


class Sheet:
    """The ink of one region of a page, with the borders of ruled boxes taken out."""

    def __init__(self, page, clip):
        self.page, self.clip = page, clip
        self.pw, self.ph = page.rect.width, page.rect.height
        pix = page.get_pixmap(matrix=fitz.Matrix(SCALE, SCALE), clip=clip, colorspace=fitz.csGRAY, alpha=False)
        gray = np.frombuffer(pix.samples, dtype=np.uint8).reshape(pix.height, pix.stride)[:, :pix.width]
        self.H, self.W = gray.shape
        back = int(np.bincount(gray.ravel(), minlength=256).argmax())
        self.mask = np.abs(gray.astype(np.int16) - back) > 24
        self.rings = []
        self.frames()

    def px(self, r):
        c = self.clip
        return (max(0, int((r.x0 - c.x0) * SCALE)), max(0, int((r.y0 - c.y0) * SCALE)), min(self.W, int(np.ceil((r.x1 - c.x0) * SCALE))), min(self.H, int(np.ceil((r.y1 - c.y0) * SCALE))))

    def pt(self, b):
        c = self.clip
        return fitz.Rect(c.x0 + b[0] / SCALE, c.y0 + b[1] / SCALE, c.x0 + b[2] / SCALE, c.y0 + b[3] / SCALE)

    def norm(self, r):
        return [round(max(0, r[0] / self.pw), 5), round(max(0, r[1] / self.ph), 5), round(min(1, r[2] / self.pw), 5), round(min(1, r[3] / self.ph), 5)]

    def frames(self):
        """A ruled box that is really printed and that nothing touches only holds content: its border belongs to no piece."""
        W, H = self.W, self.H
        for d in self.page.get_drawings():
            if d.get('type') not in ('s', 'fs') or not d.get('color') or len(d['items']) != 1 or d['items'][0][0] != 're':
                continue
            r = fitz.Rect(d['rect'])
            if r.width < .45 * self.clip.width or r.height < 18 or not r.intersects(self.clip) or not self.page.rect.contains(r):
                continue
            t = int(np.ceil(float(d.get('width') or 1) * SCALE / 2)) + 2
            x0, y0, x1, y1 = self.px(r)
            sides = [(x0 - t, y0 - t, x1 + t, y0 + t), (x0 - t, y1 - t, x1 + t, y1 + t), (x0 - t, y0 - t, x0 + t, y1 + t), (x1 - t, y0 - t, x1 + t, y1 + t)]
            sides = [(max(0, a), max(0, b), min(W, c), min(H, e)) for a, b, c, e in sides]
            sides = [s for s in sides if s[2] > s[0] and s[3] > s[1]]
            # Clipped-away boxes of the PDF leave no ink: only a border that is really printed counts.
            printed = sum(int(self.mask[b:e, a:c].any(axis=0 if c - a > e - b else 1).sum()) for a, b, c, e in sides)
            if printed < .6 * sum(max(c - a, e - b) for a, b, c, e in sides):
                continue
            trial = self.mask.copy()
            for a, b, c, e in sides:
                trial[b:e, a:c] = False
            if any(trial[max(0, b - 3):min(H, e + 3), max(0, a - 3):min(W, c + 3)].any() for a, b, c, e in sides):
                continue
            self.mask = trial
            self.rings += [self.pt(s) for s in sides]
            if len(self.rings) > 160:
                break

    def piece(self, cell, ink):
        m = int(MARGIN * SCALE)
        b = (max(cell[0], ink[0] - m), max(cell[1], ink[1] - m), min(cell[2], ink[2] + m), min(cell[3], ink[3] + m))
        area = self.pt(b)
        return b, {'rect': self.norm(area), 'erase': [self.norm(r & area) for r in self.rings if r.intersects(area)]}


def region_clip(page, rect):
    w, h = page.rect.width, page.rect.height
    return fitz.Rect(rect[0] * w, rect[1] * h, rect[2] * w, rect[3] * h) & page.rect


def trim_region(page, rect):
    """A region with no options (a numerical question, or the part of a question printed on another page): trimmed to its ink."""
    sheet = Sheet(page, region_clip(page, rect))
    ink = box_of(sheet.mask, 0, 0, sheet.W, sheet.H)
    size = [sheet.pw, sheet.ph]
    if not ink:
        return {'v': CUT_VERSION, 'status': 'none', 'reason': '', 'size': size, 'pieces': {}}
    return {'v': CUT_VERSION, 'status': 'trim', 'reason': '', 'size': size, 'pieces': {'q': sheet.piece((0, 0, sheet.W, sheet.H), ink)[1]}}


def label_boxes(sheet, chosen, lines):
    """The ink of each chosen label, and whether the label stands alone (so it can be left out of the option picture)."""
    other = [c[1] for line in lines for c in line if not c[0].isspace()]
    out = []
    for c in chosen:
        b = box_of(sheet.mask, *sheet.px(c['rect']))
        if not b:
            raise Held('Ek option ka label page par kisi aur cheez ke neeche chhupa hai.')
        alone = sum(1 for r in other if (r & c['rect']).get_area() > 1) <= len(c['ch'])
        out.append((b, alone))
    return out


def proposal(page, clip, found, kinds, labels):
    """Boxes for the fix tool to start from when a cut is held, drawn around whichever option labels were found.
    Only a starting point: nothing here reaches a student until the owner saves boxes that pass every check."""
    last = {}
    for c in found:
        if c['family'][1] in kinds and c['i'] < len(labels):
            old = last.get(c['i'])
            if not old or (c['rect'].y0, c['rect'].x0) >= (old['rect'].y0, old['rect'].x0):
                last[c['i']] = c
    if not last:
        return {}
    sheet = Sheet(page, clip)
    rows = []
    for i, c in sorted(last.items(), key=lambda kv: ((kv[1]['rect'].y0 + kv[1]['rect'].y1) / 2, kv[1]['rect'].x0)):
        cy = (c['rect'].y0 + c['rect'].y1) / 2
        if rows and abs(cy - rows[-1][0]) < .6 * c['size']:
            rows[-1][1].append((i, c))
        else:
            rows.append((cy, [(i, c)]))
    px = {i: sheet.px(c['rect']) for i, c in last.items()}
    size = int(max(c['size'] for c in last.values()) * SCALE)
    cells = {}
    for n, (_, row) in enumerate(rows):
        row.sort(key=lambda ic: ic[1]['rect'].x0)
        above = max(px[i][3] for i, _ in rows[n - 1][1]) if n else None
        below = min(px[i][1] for i, _ in rows[n + 1][1]) if n + 1 < len(rows) else None
        base = max(px[i][3] for i, _ in row)
        for j, (i, _) in enumerate(row):
            x0, x1 = max(0, px[i][0] - 2), px[row[j + 1][0]][0] - 2 if j + 1 < len(row) else sheet.W
            # Lines that touch have no blank row between them: the emptiest row is the best place to start from.
            top = neck(sheet.mask, 0, sheet.W, max(0, min(px[k][1] for k, _ in row) - size), min(px[k][1] for k, _ in row)) if above is None else neck(sheet.mask, x0, x1, above, px[i][1])
            cells[i] = (x0, top, x1, sheet.H if below is None else neck(sheet.mask, x0, x1, base, below))
    out = {}
    first = min(cells[i][1] for i, _ in rows[0][1])
    stem = box_of(sheet.mask, 0, 0, sheet.W, first)
    if stem:
        out['q'] = sheet.piece((0, 0, sheet.W, first), stem)[1]['rect']
    for i, cell in cells.items():
        ink = box_of(sheet.mask, *cell) if cell[2] > cell[0] and cell[3] > cell[1] else None
        if ink:
            out[labels[i]] = sheet.piece(cell, ink)[1]['rect']
    return out


def cut_region(page, rect, labels, typed=()):
    """rect: the question's region on the page (0..1). labels: the four answer keys in order. typed: keys the owner typed, which need no picture.
    Returns {v, status, reason, arrangement, pieces:{q, <label>...: {rect, erase}}} with every rect in 0..1 of the page."""
    out = {'v': CUT_VERSION, 'status': 'held', 'reason': '', 'arrangement': '', 'size': [page.rect.width, page.rect.height], 'pieces': {}}
    clip, found, kinds = None, [], ()
    try:
        if len(labels) != 4:
            raise Held(f'Chaar option hone chahiye; is sawaal me {len(labels)} hi answer button {"hai" if len(labels) == 1 else "hain"}. Jo option chhapa nahi hai use type karo, ya boxes khud banao.')
        clip = region_clip(page, rect)
        lines = text_lines(page, clip)
        if not lines:
            raise Held('Page ke is hisse me padhne layak text nahi hai (shayad scan hai), isliye option ke label nahi mile.')
        found = candidates(lines)
        kinds = ('d',) if labels[0].isdigit() else ('U', 'l')
        names = list(labels)
        picked = choose(found, kinds)
        if not picked and typed:
            # Options the owner typed need not be printed at all: the printed ones are cut on their own.
            names = [x for x in labels if x not in typed]
            if not names:
                trimmed = trim_region(page, rect)
                return {**out, 'status': 'ok' if trimmed['pieces'] else 'held', 'pieces': trimmed['pieces'],
                        'reason': '' if trimmed['pieces'] else 'Page ke is hisse me kuch chhapa nahi hai.'}
            picked = choose(found, kinds, [labels.index(x) for x in names])
        if not picked:
            seen = sorted({c['ch'].strip('().').upper() for c in found if c['family'][1] in kinds})
            raise Held('Chaaron option ke label chhape hain, par woh seedhi line ya column me nahi hain.' if len(seen) == 4 else
                       'Chaaron option ke label nahi mile' + (f' (sirf {", ".join(seen)} mile).' if seen else '.'))
        chosen, (shape, rows) = picked
        count = len(names)
        out['arrangement'] = shape
        sheet = Sheet(page, clip)
        mask, W, H = sheet.mask, sheet.W, sheet.H
        size = max(c['size'] for c in chosen) * SCALE
        marks = label_boxes(sheet, chosen, lines)
        inked = [m[0] for m in marks]
        least = max(6, int(.3 * size))
        wide = max(3 * size, 28 * SCALE)
        name = lambda row: 'option ' + ', '.join(names[i] for i in row) if len(row) < 3 else 'options'

        def cut_above(row, floor, who, x0=0, x1=W):
            """The blank line above these labels, within columns x0..x1: where one piece ends and the next begins."""
            blank = bands(mask[:, x0:x1].any(axis=1), 2)
            top = min(inked[i][1] for i in row)
            under = [b for b in blank if b[1] <= top + 1 and b[0] >= floor]
            if not under:
                raise Held(f'{who} aur {name(row)} ke beech khaali jagah nahi hai, isliye saaf nahi kat sakta.')
            pick = len(under) - 1
            if pick:
                # A small mark alone between two blank lines (a limit, a power) goes with the side it sits against; if that is not clear, no guess is made.
                lower, upper = under[pick], under[pick - 1]
                slab = box_of(mask, x0, upper[1], x1, lower[0])
                if slab and slab[3] - slab[1] < .9 * size and slab[2] - slab[0] < 3 * size and slab[0] > min(inked[i][2] for i in row):
                    below_gap, above_gap = lower[1] - lower[0], upper[1] - upper[0]
                    if below_gap * 2 <= above_gap:
                        pick -= 1
                    elif above_gap * 2 > below_gap:
                        raise Held(f'{cap(name(row))} ke theek upar ek chhota nishaan chhapa hai; yeh saaf nahi ki woh kis hisse ka hai.')
            return (under[pick][0] + under[pick][1]) // 2

        def gutter(ya, yb, lefts, rights):
            """The blank column between the options on the left and the option labels on the right, over the whole height ya..yb.
            A later line of an option may hang a hair to the left of its label (a root sign, a bracket), so the blank is looked for left of that."""
            edge, after = min(inked[i][0] for i in rights), max(inked[i][2] for i in lefts)
            cols = mask[ya:yb].any(axis=0)
            stop = edge
            while stop > max(after, edge - int(.25 * size)) and cols[stop - 1]:
                stop -= 1
            run = 0
            while stop - run > after and not cols[stop - 1 - run]:
                run += 1
            if run < least:
                raise Held(f'Ek hi line me option {names[lefts[-1]]} aur option {names[rights[0]]} aapas me jud rahe hain.')
            return stop - min(run // 2, int(3 * SCALE)), stop

        def own_line(i, top, stop, before):
            # Anything printed between the blank column and a label, on the label's own line or above it, belongs to the option before it.
            if mask[top:inked[i][3], stop:inked[i][0]].any():
                raise Held(f'Ek hi line me option {names[before]} aur option {names[i]} aapas me jud rahe hain.')

        def lines_of(tops):
            """Every printed line of options is one band across the whole width."""
            out = {}
            for n, row in enumerate(rows):
                ya, yb = tops[n], tops[n + 1]
                base = max(inked[i][3] for i in row)
                for b in bands(mask[base:yb].any(axis=1), int(wide)):
                    if mask[base + b[1]:yb].any():
                        where = f'{cap(name(row))} ke neeche' if n == len(rows) - 1 else f'{cap(name(row))} aur {name(rows[n + 1])} ke beech'
                        raise Held(f'{where} badi khaali jagah ke baad kuch chhapa hai; ho sakta hai woh kisi option ka na ho.')
                xs = [0]
                for j in range(1, len(row)):
                    x, stop = gutter(ya, yb, [row[j - 1]], [row[j]])
                    own_line(row[j], ya, stop, row[j - 1])
                    xs.append(x)
                xs.append(W)
                for j, i in enumerate(row):
                    out[i] = (xs[j], ya, xs[j + 1], yb)
            return out

        def columns_of(top):
            """Two options per line where a tall fraction leaves no blank line across the whole width: each column is cut on its own blank line."""
            (a, b), (c, d) = rows
            x, stop = gutter(top, H, [a, c], [b, d])
            out = {}
            for upper, lower, x0, x1 in ((a, c, 0, x), (b, d, x, W)):
                y = cut_above([lower], inked[upper][3], 'Option ' + names[upper], x0, x1)
                out[upper], out[lower] = (x0, top, x1, y), (x0, y, x1, H)
            own_line(b, top, stop, a)
            own_line(d, out[d][1], stop, c)
            for i, cell in out.items():
                part = mask[inked[i][3]:cell[3], cell[0]:cell[2]]
                for g in bands(part.any(axis=1), int(wide)):
                    if part[g[1]:].any():
                        raise Held(f'Option {names[i]} ke neeche badi khaali jagah ke baad kuch chhapa hai; ho sakta hai woh kisi option ka na ho.')
            return out

        top0 = cut_above(rows[0], 0, 'Sawaal')
        try:
            tops = [top0]
            for n in range(1, len(rows)):
                tops.append(cut_above(rows[n], max(inked[i][3] for i in rows[n - 1]), cap(name(rows[n - 1]))))
            cells = lines_of(tops + [H])
        except Held:
            if shape != 'grid':
                raise
            cells = columns_of(top0)
        pieces, boxes, skipped = {}, {}, []
        stem = box_of(mask, 0, 0, W, top0)
        if stem:
            boxes['q'], pieces['q'] = sheet.piece((0, 0, W, top0), stem)
        far = max(6 * size, .3 * W)
        for i in range(count):
            cell = cells[i]
            if names[i] in typed:
                # The owner typed this option: whatever the page prints in its place is left out with it.
                skipped.append(cell)
                continue
            own = mask.copy()
            (lx0, ly0, lx1, ly1), alone = marks[i]
            if alone:
                own[ly0:ly1, lx0:lx1] = False
            ink = box_of(own, *cell)
            if not ink:
                raise Held(f'Option {names[i]} ke label ke baad kuch chhapa nahi hai.')
            for b in bands(own[cell[1]:cell[3], lx1:cell[2]].any(axis=0), int(far)):
                if own[cell[1]:cell[3], lx1 + b[1]:cell[2]].any():
                    raise Held(f'Option {names[i]} ke bahut door daayin taraf kuch chhapa hai; ho sakta hai woh iska na ho.')
            boxes[names[i]], pieces[names[i]] = sheet.piece(cell, ink)
            if alone:
                gone = sheet.pt((lx0 - 2, ly0 - 2, lx1 + 2, ly1 + 2)) & sheet.pt(boxes[names[i]])
                if not gone.is_empty:
                    pieces[names[i]]['erase'].append(sheet.norm(gone))
        out['pieces'] = pieces
        # Nothing lost, nothing shared.
        left = mask.copy()
        for b in list(boxes.values()) + skipped:
            left[b[1]:b[3], b[0]:b[2]] = False
        for b, _ in marks:
            left[b[1]:b[3], b[0]:b[2]] = False
        if left.any():
            raise Held('Is sawaal ka kuch chhapa hua hissa na sawaal ki picture me aaya, na kisi option ki picture me.')
        said = lambda k: 'Sawaal' if k == 'q' else 'option ' + k
        keys = list(boxes)
        for a in range(len(keys)):
            for b in range(a + 1, len(keys)):
                p, q = boxes[keys[a]], boxes[keys[b]]
                if min(p[2], q[2]) > max(p[0], q[0]) and min(p[3], q[3]) > max(p[1], q[1]):
                    raise Held(f'{cap(said(keys[a]))} aur {said(keys[b])} ki picture ek doosre par chadh rahi hain.')
        out['status'] = 'ok'
    except Held as exc:
        out['reason'] = str(exc)
        if not out['pieces'] and clip is not None and labels:
            try:
                out['draft'] = proposal(page, clip, found, kinds or (('d',) if labels[0].isdigit() else ('U', 'l')), list(labels))
            except Exception:  # noqa: BLE001  a starting suggestion must never fail the cut itself
                out['draft'] = {}
    return out


def cut_boxes(page, rect, boxes, labels):
    """Boxes drawn by hand (0..1 of the page) -> pieces, after the same checks.
    Returns {status:'manual'|'held', reason, pieces, outside}: `outside` is true when printed marks of the region lie in no box."""
    said = lambda k: 'Sawaal ka box' if k == 'q' else f'Option {k} ka box'
    out = {'v': CUT_VERSION, 'status': 'held', 'reason': '', 'arrangement': 'by hand', 'size': [page.rect.width, page.rect.height], 'pieces': {}, 'outside': False}
    try:
        clip = region_clip(page, rect)
        areas = {}
        for key in ['q'] + list(labels):
            b = boxes.get(key)
            if not b or len(b) != 4 or not (0 <= b[0] < b[2] <= 1 and 0 <= b[1] < b[3] <= 1):
                raise Held(f'{said(key)} nahi mila.')
            areas[key] = fitz.Rect(b[0] * page.rect.width, b[1] * page.rect.height, b[2] * page.rect.width, b[3] * page.rect.height)
            clip |= areas[key]
        clip &= page.rect
        sheet = Sheet(page, clip)
        lines = text_lines(page, clip)
        marks = {}
        if labels and all(k in KNOWN for k in labels):
            picked = choose(candidates(lines), ('d',) if labels[0].isdigit() else ('U', 'l'), [index_of(k) for k in labels])
            if picked:
                try:
                    marks = dict(zip(labels, label_boxes(sheet, picked[0], lines)))
                except Held:
                    marks = {}
        keys = list(areas)
        for a in range(len(keys)):
            for b in range(a + 1, len(keys)):
                if (areas[keys[a]] & areas[keys[b]]).get_area() > .5:
                    raise Held(f'{said(keys[a])} aur {said(keys[b])[:1].lower() + said(keys[b])[1:]} ek doosre par chadh rahe hain. Do hisse page ka koi bhi hissa share nahi kar sakte.')
        left = sheet.mask.copy()
        for key in keys:
            cell = sheet.px(areas[key])
            own = sheet.mask.copy()
            mark = marks.get(key)
            # The printed label is left out only when it stands alone inside its own option box.
            inside = mark and mark[1] and cell[0] <= mark[0][0] and cell[1] <= mark[0][1] and mark[0][2] <= cell[2] and mark[0][3] <= cell[3]
            if inside:
                own[mark[0][1]:mark[0][3], mark[0][0]:mark[0][2]] = False
            ink = box_of(own, *cell)
            if not ink:
                raise Held(f'{said(key)} me kuch chhapa nahi hai.')
            box, out['pieces'][key] = sheet.piece(cell, ink)
            if inside:
                gone = sheet.pt((mark[0][0] - 2, mark[0][1] - 2, mark[0][2] + 2, mark[0][3] + 2)) & sheet.pt(box)
                if not gone.is_empty:
                    out['pieces'][key]['erase'].append(sheet.norm(gone))
            left[cell[1]:cell[3], cell[0]:cell[2]] = False
        for b, _ in marks.values():
            left[b[1]:b[3], b[0]:b[2]] = False
        x0, y0, x1, y1 = sheet.px(region_clip(page, rect))
        out['outside'] = bool(left[y0:y1, x0:x1].sum() > 12)
        out['status'] = 'manual'
    except Held as exc:
        out['reason'] = str(exc)
        out['pieces'] = {}
    return out
