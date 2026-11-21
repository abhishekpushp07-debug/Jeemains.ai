"""PDF Engine 2.0 cutter: one question region -> five pieces (question, A, B, C, D).
Uses only where the text sits and where the page is blank. No AI, no guessing: a cut that fails any check is held with its reason."""
import itertools
import re
import fitz
import numpy as np
from pymupdf import mupdf

CUT_VERSION = 2
SCALE = 2.0      # pixels per PDF point used to look at the ink
MARGIN = 4.0     # points of blank kept around every piece
HEAD = 60.0      # points above a question's printed box in which its heading (number, source, chapter) may sit
ANCHOR = re.compile(r'^\s*(?:Q(?:uestion|ues)?\.?\s*\d{1,3}\b|\d{1,3}\s*[.)])', re.I)
STYLES = (('paren', r'\(\s?([A-Da-d1-4])\s?\)'), ('close', r'([A-Da-d1-4])\)'), ('dot', r'([A-Da-d])\.'))
KNOWN = 'ABCDabcd1234'
TEXT_ONLY = fitz.TEXTFLAGS_RAWDICT & ~fitz.TEXT_PRESERVE_IMAGES


class Held(Exception):
    pass


_LISTS = {}


def listing(page):
    """The page read from the PDF once; every later look at it (letters, ink, pictures) replays this instead of reading the PDF again."""
    key = (id(page.parent), page.number)
    if key not in _LISTS:
        if len(_LISTS) >= 6:
            _LISTS.pop(next(iter(_LISTS)))
        _LISTS[key] = (page.parent, page.get_displaylist())
    return _LISTS[key][1]


def textpage(page, clip, flags):
    """Exactly what page.get_textpage(clip, flags) gives, made from the page's display list."""
    tpage = mupdf.FzStextPage(mupdf.FzRect(clip[0], clip[1], clip[2], clip[3]))
    dev = mupdf.fz_new_stext_device(tpage, mupdf.FzStextOptions(flags))
    mupdf.fz_run_display_list(listing(page).this, dev, mupdf.FzMatrix(), mupdf.FzRect(mupdf.FzRect.Fixed_INFINITE), mupdf.FzCookie())
    mupdf.fz_close_device(dev)
    tp = fitz.TextPage(tpage)
    tp.parent = page
    return tp


def pixmap(page, **kw):
    return listing(page).get_pixmap(**kw)


def kind_of(ch):
    return 'd' if ch.isdigit() else 'U' if ch.isupper() else 'l'


def index_of(ch):
    return '1234'.index(ch) if ch.isdigit() else 'abcd'.index(ch.lower())


def cap(text):
    return text[:1].upper() + text[1:]


def text_lines(page, clip):
    out = []
    # Only the letters are read: decoding the page's pictures as well made this ten times slower.
    for block in page.get_text('rawdict', textpage=textpage(page, clip, TEXT_ONLY)).get('blocks', []):
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
                wide = chars[a][1].x0 - next((c[1].x1 for c in reversed(chars[:a]) if not c[0].isspace()), -999)
                if style == 'paren':
                    if not (lead or text[a - 1].isspace() or gap > .25 * size):
                        continue
                else:
                    # 'A.' and 'A)' count only at the start of a line or after a clear gap, and need a space after them.
                    if (a and text[a - 1] == '(') or not (lead or wide > 1.2 * size) or (b < len(text) and not text[b].isspace()):
                        continue
                rect = fitz.Rect()
                for c in chars[a:b]:
                    if not c[0].isspace():
                        rect |= c[1]
                # 'apart': it starts its line or stands clear of the text before it, as an option label does; a letter inside a sentence does not.
                found.append({'i': index_of(m[1]), 'family': (style, kind_of(m[1])), 'rect': rect, 'size': size, 'ch': m[0].strip(), 'lead': lead, 'apart': lead or wide > 1.2 * size})
    mid = lambda c: (c['rect'].y0 + c['rect'].y1) / 2
    for c in found:
        # An option label starts its printed row. A letter in brackets inside an option's own text, like "(a), (b) and (c) only", does not:
        # it follows text on its line, or the label of another family (capital vs small) printed before it on the same row.
        c['first'] = c['lead'] and not any(d['family'] != c['family'] and (d['family'][1] == 'd') == (c['family'][1] == 'd') and d['rect'].x1 <= c['rect'].x0
                                           and abs(mid(d) - mid(c)) < .6 * c['size'] for d in found)
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
    """The last full set of the wanted labels that is lined up; statement labels higher in the question lose to it.
    Letters of the other case printed inside the options themselves, like the (a), (b) of "(a) and (b) only", are never the options:
    a set that begins inside another set's own lines loses to that set."""
    best = {}
    for family in {c['family'] for c in found if c['family'][1] in kinds}:
        per = [[c for c in found if c['family'] == family and c['i'] == i][-8:] for i in want]
        if not per or not all(per):
            continue
        for s in itertools.product(*per):
            s = list(s)
            shape = arrangement(s)
            # Every row of options begins with a real option label (see candidates): statement letters inside an option never start a row.
            if not shape or not all(s[row[0]]['first'] for row in shape[1]):
                continue
            key = (min(x['rect'].y0 for x in s), family[0] == 'paren', -max(x['rect'].y1 for x in s))
            if family not in best or key > best[family][0]:
                best[family] = (key, s, shape)
    sets = list(best.values())
    span = lambda b: (min(x['rect'].y0 for x in b[1]), max(x['rect'].y1 for x in b[1]))
    outer = [a for a in sets if not any(b is not a and span(b)[0] < span(a)[0] - 1 and span(a)[0] < span(b)[1] for b in sets)]
    pick = max(outer or sets, key=lambda b: b[0], default=None)
    if not pick:
        return None
    # Capital and small letters are never mixed up: when a full set of the other case is printed below the lined-up set,
    # that lower set is the options (it is only not lined up), and the set above it is the question's own statements.
    mid = lambda c: (c['rect'].y0 + c['rect'].y1) / 2
    case = pick[1][0]['family'][1]
    low = max(mid(x) for x in pick[1]) + .6 * max(x['size'] for x in pick[1])
    under = {}
    for c in found:
        if c['family'][1] in kinds and c['family'][1] != case and c['apart'] and mid(c) > low:
            under.setdefault(c['family'], set()).add(c['i'])
    if any(all(i in seen for i in want) for seen in under.values()):
        return None
    return pick[1], pick[2]


def ruled(d):
    """The rectangle a stroked path draws and its corner radius: a plain rectangle, or straight sides joined by square or rounded corners. None for anything else."""
    items = d.get('items') or []
    if d.get('type') not in ('s', 'fs') or not d.get('color') or not items:
        return None
    r = fitz.Rect(d['rect'])
    if len(items) == 1 and items[0][0] == 're':
        return r, 0.0
    if len(items) == 1 and items[0][0] == 'qu':
        return (r, 0.0) if items[0][1].is_rectangular else None
    if not 3 <= len(items) <= 12:
        return None
    edge = lambda p: min(abs(p.x - r.x0), abs(p.x - r.x1)) < .5 or min(abs(p.y - r.y0), abs(p.y - r.y1)) < .5
    radius, sides = 0.0, 0
    for it in items:
        a, b = it[1], it[-1]
        if it[0] not in ('l', 'c') or not (edge(a) and edge(b)):
            return None
        if it[0] == 'l':
            if abs(a.x - b.x) > .5 and abs(a.y - b.y) > .5:
                return None
            sides += 1
        else:
            w, h = abs(a.x - b.x), abs(a.y - b.y)
            if not (.5 < w <= 14 and .5 < h <= 14):
                return None
            radius = max(radius, w, h)
    return (r, radius) if sides >= 3 else None


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
        pix = pixmap(page, matrix=fitz.Matrix(SCALE, SCALE), clip=clip, colorspace=fitz.csGRAY, alpha=False)
        gray = np.frombuffer(pix.samples, dtype=np.uint8).reshape(pix.height, pix.stride)[:, :pix.width]
        self.H, self.W = gray.shape
        back = int(np.bincount(gray.ravel(), minlength=256).argmax())
        self.mask = np.abs(gray.astype(np.int16) - back) > 24
        self.rings, self.boxes, self.small = [], [], []
        self.frames()

    def px(self, r):
        c = self.clip
        return (max(0, int((r.x0 - c.x0) * SCALE)), max(0, int((r.y0 - c.y0) * SCALE)), min(self.W, int(np.ceil((r.x1 - c.x0) * SCALE))), min(self.H, int(np.ceil((r.y1 - c.y0) * SCALE))))

    def pt(self, b):
        c = self.clip
        return fitz.Rect(c.x0 + b[0] / SCALE, c.y0 + b[1] / SCALE, c.x0 + b[2] / SCALE, c.y0 + b[3] / SCALE)

    def norm(self, r):
        return [round(max(0, r[0] / self.pw), 5), round(max(0, r[1] / self.ph), 5), round(min(1, r[2] / self.pw), 5), round(min(1, r[3] / self.ph), 5)]

    def strips(self, r, t, radius=0.0):
        """The pixel strips a ruled box's border is printed in, and its rounded corners when it has them."""
        W, H = self.W, self.H
        x0, y0, x1, y1 = self.px(r)
        out = [(x0 - t, y0 - t, x1 + t, y0 + t), (x0 - t, y1 - t, x1 + t, y1 + t), (x0 - t, y0 - t, x0 + t, y1 + t), (x1 - t, y0 - t, x1 + t, y1 + t)]
        if radius:
            k = int(np.ceil(radius * SCALE)) + t
            out += [(x0 - t, y0 - t, x0 + k, y0 + k), (x1 - k, y0 - t, x1 + t, y0 + k), (x0 - t, y1 - k, x0 + k, y1 + t), (x1 - k, y1 - k, x1 + t, y1 + t)]
        out = [(max(0, a), max(0, b), min(W, c), min(H, e)) for a, b, c, e in out]
        return [s for s in out if s[2] > s[0] and s[3] > s[1]]

    def frames(self):
        """A wide ruled box that is really printed and that nothing touches only holds content: its border belongs to no piece.
        Narrower ruled boxes are only remembered: they count when a question prints its options in boxes side by side."""
        W, H = self.W, self.H
        for d in self.page.get_drawings():
            shape = ruled(d)
            if not shape:
                continue
            r, radius = shape
            wide = r.width >= .45 * self.clip.width and r.height >= 18
            if not (wide or (r.width >= 30 and r.height >= 14 and len(self.small) < 60)) or not r.intersects(self.clip) or not self.page.rect.contains(r):
                continue
            t = int(np.ceil(float(d.get('width') or 1) * SCALE / 2)) + 2
            sides = self.strips(r, t)
            # Clipped-away boxes of the PDF leave no ink: only a border that is really printed counts.
            printed = sum(int(self.mask[b:e, a:c].any(axis=0 if c - a > e - b else 1).sum()) for a, b, c, e in sides)
            if printed < .6 * sum(max(c - a, e - b) for a, b, c, e in sides):
                continue
            if not wide:
                self.small.append((r, t))
                continue
            self.boxes.append((r, t))
            sides = self.strips(r, t, radius)
            trial = self.mask.copy()
            for a, b, c, e in sides:
                trial[b:e, a:c] = False
            if any(trial[max(0, b - 3):min(H, e + 3), max(0, a - 3):min(W, c + 3)].any() for a, b, c, e in sides):
                continue
            self.mask = trial
            self.rings += [self.pt(s) for s in sides]
            if len(self.rings) > 160:
                break

    def outermost(self, boxes):
        """Of these ruled boxes, the ones that lie wholly inside the region and inside no other box, in reading order."""
        c = self.clip
        outer = []
        for r, t in sorted(boxes, key=lambda b: -b[0].get_area()):
            if c.x0 - 1 <= r.x0 and r.x1 <= c.x1 + 1 and c.y0 - 1 <= r.y0 and r.y1 <= c.y1 + 1 and not any(o.x0 - 1 <= r.x0 and o.y0 - 1 <= r.y0 and r.x1 <= o.x1 + 1 and r.y1 <= o.y1 + 1 for o, _ in outer):
                outer.append((r, t))
        return sorted(outer, key=lambda b: (b[0].y0, b[0].x0))

    def stack(self):
        """The printed boxes of a boxed layout, top to bottom: the outermost wide ruled boxes of the region. Empty unless they sit one below another."""
        outer = self.outermost(self.boxes)
        return [] if any(b[0].y0 < a[0].y1 for a, b in zip(outer, outer[1:])) else outer

    def layout(self):
        """A boxed layout whose option boxes may sit side by side: the question's wide box, then every outermost box printed below it.
        Empty unless no box overlaps another and all of them lie below the question's box."""
        every = self.outermost(self.boxes + self.small)
        top = next((b for b in every if b in self.boxes), None)
        if not top:
            return []
        # A small box printed above the question's box (a number badge) is part of the heading.
        rest = [b for b in every if b is not top and b[0].y1 > top[0].y0 + 1]
        if any(b[0].y0 < top[0].y1 - 1 for b in rest) or any((a[0] & b[0]).get_area() > 1 for a, b in itertools.combinations(rest, 2)):
            return []
        return [top, *rest]

    def inner(self, box):
        """The pixels inside a printed box, clear of its border line."""
        x0, y0, x1, y1 = self.px(box[0])
        return x0 + box[1], y0 + box[1], x1 - box[1], y1 - box[1]

    def piece(self, cell, ink):
        m = int(MARGIN * SCALE)
        b = (max(cell[0], ink[0] - m), max(cell[1], ink[1] - m), min(cell[2], ink[2] + m), min(cell[3], ink[3] + m))
        area = self.pt(b)
        return b, {'rect': self.norm(area), 'erase': [self.norm(r & area) for r in self.rings if r.intersects(area)]}


def region_clip(page, rect):
    w, h = page.rect.width, page.rect.height
    return fitz.Rect(rect[0] * w, rect[1] * h, rect[2] * w, rect[3] * h) & page.rect


def heading(sheet, box):
    """What is printed above a question's box is its heading (number, source, chapter) and belongs to no piece.
    Returns the pixel row where the heading ends. Anything else printed up there is not guessed about."""
    top = max(0, sheet.inner(box)[1] - 2 * box[1])
    rows = np.flatnonzero(sheet.mask[:top].any(axis=1))
    if not len(rows):
        return top
    # The 'Question N' line is looked for on the page itself: the region may begin just under it.
    above = text_lines(sheet.page, fitz.Rect(sheet.clip.x0, max(0, box[0].y0 - HEAD), sheet.clip.x1, box[0].y0))
    if (top - int(rows[0])) / SCALE > HEAD or not any(ANCHOR.match(''.join(c[0] for c in l)) for l in above):
        raise Held('Sawaal ke box ke upar kuch chhapa hai jo heading jaisa nahi hai; yeh saaf nahi ki woh sawaal ka hissa hai ya nahi.')
    return top


def outside(sheet, cells, head):
    """True when something is printed in the region that is neither the heading nor inside a printed box."""
    left = sheet.mask.copy()
    left[:head] = False
    for box in cells:
        c, t = sheet.inner(box), 2 * box[1]
        left[max(0, c[1] - t):c[3] + t, max(0, c[0] - t):c[2] + t] = False
    return bool(left.any())


def inside(sheet, key, cell, own):
    """The piece printed inside one box (a box whose border something touches is never taken as a printed box, see Sheet.frames)."""
    ink = box_of(own, *cell)
    if not ink:
        raise Held('Sawaal ke box me kuch chhapa nahi hai.' if key == 'q' else f'Option {key} ke label ke baad kuch chhapa nahi hai.')
    return sheet.piece(cell, ink)


def assign(cells, found, lines, labels, typed, kinds):
    """Which printed box is whose: every box below the question's box is named by the option label printed first inside it,
    so boxes one below another, two in a line or four in a line are all read the same way. Capital labels are looked for first.
    Returns (the label found for each option that needs a picture, [the question's box, one box per label], boxes that hold neither) or None."""
    drawn = [i for i, x in enumerate(labels) if x not in typed]
    centre = lambda r: fitz.Point((r.x0 + r.x1) / 2, (r.y0 + r.y1) / 2)
    mid = lambda c: centre(c['rect'])
    marks = [(r, centre(r)) for line in lines for ch, r, _ in line if not ch.isspace()]

    def leads(c, box):
        # A label is the first thing printed on its row inside its own box; a letter inside an option's text, like the (b) of "(a) and (b) only", is not.
        y = mid(c).y
        return not any(r.x1 <= c['rect'].x0 + .5 and abs(p.y - y) < .6 * c['size'] and box.contains(p) for r, p in marks)

    for family in sorted({c['family'] for c in found if c['family'][1] in kinds}, key=lambda f: (f[0] != 'paren', f[1] != 'U')):
        where = {}
        for n in range(1, len(cells)):
            own = [c for c in found if c['family'] == family and c['i'] < len(labels) and cells[n][0].contains(mid(c)) and leads(c, cells[n][0])]
            if own:
                c = min(own, key=lambda c: (round(c['rect'].y0), c['rect'].x0))
                if c['i'] in where:
                    where = None
                    break
                where[c['i']] = (n, c)
        if not where or not all(i in where for i in drawn):
            continue
        spare = [n for n in range(1, len(cells)) if n not in {w[0] for w in where.values()}]
        order = [where[i][0] if i in where else spare.pop(0) if spare else None for i in range(len(labels))]
        if None not in order:
            return [where[i][1] for i in drawn], [cells[0], *(cells[n] for n in order)], [cells[n] for n in spare]
    return None


def cut_printed(sheet, cells, chosen, lines, labels, typed):
    """A boxed layout: the first printed box holds the question and every other box holds one option, its own label printed first.
    The printed boxes are the pieces. cells: the question's box, then one box per label. Returns {q, <label>...: {rect, erase}}."""
    head = heading(sheet, cells[0])
    drawn = [i for i, x in enumerate(labels) if x not in typed]
    pieces = {'q': inside(sheet, 'q', sheet.inner(cells[0]), sheet.mask)[1]}
    for (mark, alone), i in zip(label_boxes(sheet, chosen, lines), drawn):
        own = sheet.mask
        if alone:
            own = sheet.mask.copy()
            own[mark[1]:mark[3], mark[0]:mark[2]] = False
        box, pieces[labels[i]] = inside(sheet, labels[i], sheet.inner(cells[i + 1]), own)
        if alone:
            gone = sheet.pt((mark[0] - 2, mark[1] - 2, mark[2] + 2, mark[3] + 2)) & sheet.pt(box)
            if not gone.is_empty:
                pieces[labels[i]]['erase'].append(sheet.norm(gone))
    if outside(sheet, cells, head):
        raise Held('Chhape hue boxes ke bahar bhi kuch chhapa hai jo kisi box me nahi aaya.')
    return pieces


def printed_boxes(sheet, cells=None):
    """The printed boxes of the region for the fix tool (0..1 of the page), in reading order."""
    return [sheet.norm(sheet.pt(sheet.inner(b))) for b in (sheet.stack() if cells is None else cells)[:12]]


def trim_region(page, rect):
    """A region with no options (a numerical question, or the part of a question printed on another page): trimmed to its ink."""
    sheet = Sheet(page, region_clip(page, rect))
    size, cells = [sheet.pw, sheet.ph], sheet.stack()
    out = {'v': CUT_VERSION, 'status': 'trim', 'reason': '', 'arrangement': '', 'size': size, 'frames': printed_boxes(sheet), 'pieces': {}}
    if len(cells) == 1:
        # Boxes first: a question printed in its own box is that box, without the heading above it.
        try:
            head = heading(sheet, cells[0])
            piece = inside(sheet, 'q', sheet.inner(cells[0]), sheet.mask)[1]
            if not outside(sheet, cells, head):
                return {**out, 'arrangement': 'boxes', 'pieces': {'q': piece}}
        except Held:
            pass
    ink = box_of(sheet.mask, 0, 0, sheet.W, sheet.H)
    if not ink:
        return {**out, 'status': 'none'}
    return {**out, 'pieces': {'q': sheet.piece((0, 0, sheet.W, sheet.H), ink)[1]}}


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
    pool = [c for c in found if c['family'][1] in kinds and c['i'] < len(labels)]
    if not pool:
        return {}
    centre = lambda c: (c['rect'].y0 + c['rect'].y1) / 2
    # One kind of label only: capitals and small letters are never mixed. The options are the last thing printed in a question,
    # so the kind whose first label starts a line lowest on the page is taken, and every other label is the first one printed after it.
    heads = [c for c in pool if c['i'] == 0 and c['first']] or [c for c in pool if c['i'] == 0] or pool
    head = max(heads, key=lambda c: (c['rect'].y0, c['family'][0] == 'paren'))
    last = {head['i']: head}
    for c in sorted(pool, key=lambda c: (not c['apart'], round(c['rect'].y0), c['rect'].x0)):
        if c['family'] == head['family'] and c['i'] not in last and centre(c) > centre(head) - .6 * head['size']:
            last[c['i']] = c
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
    out = {'v': CUT_VERSION, 'status': 'held', 'reason': '', 'arrangement': '', 'size': [page.rect.width, page.rect.height], 'frames': [], 'pieces': {}}
    clip, found, kinds, boxed, printed = None, [], (), '', {}
    try:
        if len(labels) != 4:
            raise Held(f'Chaar option hone chahiye; is sawaal me {len(labels)} hi answer button {"hai" if len(labels) == 1 else "hain"}. Jo option chhapa nahi hai use type karo, ya boxes khud banao.')
        clip = region_clip(page, rect)
        lines = text_lines(page, clip)
        if not lines:
            raise Held('Page ke is hisse me padhne layak text nahi hai (shayad scan hai), isliye option ke label nahi mile.')
        found = candidates(lines)
        kinds = ('d',) if labels[0].isdigit() else ('U', 'l')
        sheet = Sheet(page, clip)
        wide = sheet.stack()
        out['frames'] = printed_boxes(sheet, sheet.layout() or wide)
        # Boxes first: a page that prints the question in one box and every option in its own box is cut along those boxes.
        for cells in (wide, sheet.layout()):
            placed = assign(cells, found, lines, list(labels), typed, kinds) if len(cells) > len(labels) else None
            if placed:
                chosen, cells, spare = placed
                out['frames'] = printed_boxes(sheet, cells + spare)
                printed = dict(zip(['q', *labels], out['frames']))
                if spare:
                    raise Held('Is sawaal me ek aur chhapa hua box hai jo na sawaal ka hai, na kisi option ka.')
                # Once the boxes are known, anything wrong with them is shown to the owner; nothing is guessed from white space instead.
                out.update(pieces=cut_printed(sheet, cells, chosen, lines, list(labels), typed), arrangement='boxes', status='ok')
                return out
        if len(wide) == len(labels) + 1:
            printed = dict(zip(['q', *labels], printed_boxes(sheet, wide)))
            boxed = 'Har option ke box me uska apna label (A, B, C, D) sabse pehle chhapa hona chahiye; aisa nahi mila.'
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
        out['reason'] = boxed or str(exc)
        if printed:
            # The printed boxes themselves are the best place for the fix tool to start from.
            out['pieces'], out['draft'] = {}, printed
        elif not out['pieces'] and clip is not None and labels:
            try:
                out['draft'] = proposal(page, clip, found, kinds or (('d',) if labels[0].isdigit() else ('U', 'l')), list(labels))
            except Exception:  # noqa: BLE001  a starting suggestion must never fail the cut itself
                out['draft'] = {}
    return out


def cut_boxes(page, rect, boxes, labels):
    """Boxes drawn by hand (0..1 of the page) -> pieces, after the same checks.
    Returns {status:'manual'|'held', reason, pieces, outside}: `outside` is true when printed marks of the region lie in no box."""
    said = lambda k: 'Sawaal ka box' if k == 'q' else f'Option {k} ka box'
    out = {'v': CUT_VERSION, 'status': 'held', 'reason': '', 'arrangement': 'by hand', 'size': [page.rect.width, page.rect.height], 'frames': [], 'pieces': {}, 'outside': False}
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
                both = areas[keys[a]] & areas[keys[b]]
                if both.get_area() <= .5:
                    continue
                # A box drawn by hand may run over its neighbour on blank paper; nothing printed may lie in two boxes.
                x0, y0, x1, y1 = sheet.px(both)
                if sheet.mask[y0:y1, x0:x1].any():
                    raise Held(f'{said(keys[a])} aur {said(keys[b])[:1].lower() + said(keys[b])[1:]} ek doosre par chadh rahe hain. Jo chhapa hai woh ek hi box me aa sakta hai.')
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
        for r, t in sheet.small:
            # The printed border of a small box that one of these boxes was drawn in is not content of the question.
            if any((a & r).get_area() > .6 * a.get_area() for a in areas.values()):
                for a, b, c, e in sheet.strips(r, t):
                    left[b:e, a:c] = False
        cells = sheet.layout() or sheet.stack()
        out['frames'] = printed_boxes(sheet, cells)
        if cells:
            # The heading printed above a boxed question (number, source, chapter) belongs to no piece.
            try:
                left[:heading(sheet, cells[0])] = False
            except Held:
                pass
        x0, y0, x1, y1 = sheet.px(region_clip(page, rect))
        out['outside'] = bool(left[y0:y1, x0:x1].sum() > 12)
        out['status'] = 'manual'
    except Held as exc:
        out['reason'] = str(exc)
        out['pieces'] = {}
    return out

