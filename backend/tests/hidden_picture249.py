"""TEST-ONLY iteration 249 (pocket R1): a picture a PDF places on a page but hides completely behind a clip path is not a picture of
the page, so it can no longer hold a question ("crop boundary crosses text or a diagram"). A picture that shows, whole or in part, counts as before.
No database, no storage, no AI: made-up pages, and the owner's own page that showed this (when his book is on this machine), go through
the app's sealed PDF worker and its page reader.
Run: cd /app/backend && python tests/hidden_picture249.py
"""
import re, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from dotenv import load_dotenv  # noqa: E402
load_dotenv('/app/backend/.env')  # import only; no database access in this test
import fitz  # noqa: E402
from tejas.book_pdf import inspect_many  # noqa: E402
from tejas.book_reader import read_page  # noqa: E402

RESULTS = []
WORK = Path('/root/aitsv_out/hidden249'); WORK.mkdir(parents=True, exist_ok=True)
OWNER_BOOK = '/root/pdfengine/aits/b.pdf'
PICTURE = (178, 180, 411, 336)   # where the picture is placed: over the drawn graph and down past the question's box
CLIPS = {'shown': '', 'hidden_far': '0 0 1 1 re W n', 'hidden_flat': '180 700 220 0 re W n', 'hidden_apart': '44 600 500 60 re W n 44 300 500 60 re W n',
         'half': '178 506 116 156 re W n'}
CONTEXT = {'mock': 'Mock 45', 'subject': 'Physics', 'role': 'question'}
HELD = 'crop boundary crosses text or a diagram'


def check(name, ok, detail=''):
    RESULTS.append((name, bool(ok)))
    print(('PASS ' if ok else 'FAIL ') + name + ('' if ok else ' :: ' + str(detail)[:700]), flush=True)


def page_pdf(clip):
    """One page laid out like the owner's: heading, a ruled question box with words and a graph drawn in lines, an answer box under it,
    and one dark picture placed over the graph and past the question box, under this clip ('' = no clip)."""
    doc = fitz.open(); p = doc.new_page(width=595.276, height=841.89)
    p.insert_text((32, 20), 'AITS / JEE MAIN 2027', fontsize=8); p.draw_line((32, 28), (563, 28), width=.5)
    p.insert_text((32, 48), 'Question 46', fontsize=15); p.insert_text((32, 60), 'MOCK 45 / Physics / Numerical value', fontsize=8)
    p.draw_rect(fitz.Rect(32, 66, 563, 311), width=.7, fill=(1, 1, 1))
    for i, line in enumerate(('The potential energy U of a particle moving along the x-axis varies with its position x as shown in',
                              'the graph, which consists of straight-line segments. The maximum magnitude of the force acting on the',
                              'particle in the region 0 < x < 8 m (excluding the corner points) is ________ N.')):
        p.insert_text((45, 88 + 14 * i), line, fontsize=10.5)
    for i in range(9): p.draw_line((222 + 20 * i, 140), (222 + 20 * i, 215), width=.4)
    p.draw_line((222, 215), (390, 215), width=.8); p.draw_line((222, 200), (284, 140), width=1); p.draw_line((284, 140), (390, 215), width=1)
    p.insert_text((300, 240), 'x (m)', fontsize=9)
    p.draw_rect(fitz.Rect(32, 325, 563, 397), width=.7, fill=(1, 1, 1)); p.insert_text((44, 350), 'Numerical response', fontsize=10); p.draw_line((44, 376), (242, 376), width=.5)
    p.insert_text((524, 817), 'BOOK 2938', fontsize=7)
    pix = fitz.Pixmap(fitz.csRGB, fitz.IRect(0, 0, 60, 40)); pix.clear_with(60)
    p.insert_image(fitz.Rect(*PICTURE), pixmap=pix, keep_proportion=False)
    p.clean_contents()
    x = p.get_contents()[0]; s = doc.xref_stream(x)
    do = list(re.finditer(rb'/\w+\s+Do', s))[-1]; start = s.rfind(b'q', 0, do.start())
    if clip: doc.update_stream(x, s[:start] + b'q ' + clip.encode() + b' ' + s[start:do.end()] + b' Q' + s[do.end():])
    return doc


def dark(doc):
    """Dark pixels the page really shows inside the picture's place but clear of the drawn graph and the words (the strip between the two boxes and below)."""
    pix = doc[0].get_pixmap(clip=fitz.Rect(PICTURE[0], 312, PICTURE[2], 324), colorspace=fitz.csGRAY)
    return sum(v < 100 for v in pix.samples)


def read(data, images=None, geometry=None):
    lines = [dict(x) for x in data['lines']]
    m, _ = read_page(lines, dict(CONTEXT), data['geometry'] if geometry is None else geometry, data['images'] if images is None else images)
    return m


def made_up():
    paths = {}
    for name, clip in CLIPS.items():
        doc = page_pdf(clip); paths[name] = str(WORK / f'{name}.pdf'); shown = dark(doc); doc.save(paths[name]); doc.close()
        check(f'{name}: the made-up page is what its name says (the picture {"shows" if name in ("shown", "half") else "shows nothing"})', (shown > 0) == (name in ('shown', 'half')), shown)
    got = {name: inspect_many(path, [{'action': 'text', 'page': 1}])[0] for name, path in paths.items()}
    check('every made-up page is read without an error', all(not g.get('error') and g.get('lines') for g in got.values()), {k: g.get('error') for k, g in got.items()})
    w, h = 595.276, 841.89; box = [PICTURE[0] / w, PICTURE[1] / h, PICTURE[2] / w, PICTURE[3] / h]
    near = lambda b: all(abs(a - c) < .004 for a, c in zip(b, box))
    check('a picture that shows is counted, at the place it is put', len(got['shown']['images']) == 1 and near(got['shown']['images'][0]), got['shown']['images'])
    check('a picture that shows in part is counted, at the place it is put', len(got['half']['images']) == 1 and near(got['half']['images'][0]), got['half']['images'])
    for name in ('hidden_far', 'hidden_flat', 'hidden_apart'):
        check(f'{name}: a picture hidden completely is not counted', got[name]['images'] == [] and not any(near(b) for b in got[name]['geometry']), (got[name]['images'], len(got[name]['geometry'])))
        m = read(got[name])
        check(f'{name}: the question is read whole and is not held', m.classification == 'questions' and not m.issues and [(r.role, r.number) for r in m.regions] == [('question', 46)], (m.classification, m.issues, [(r.role, r.number) for r in m.regions]))
        before = read(got[name], images=[box], geometry=[box] + got[name]['geometry'])
        check(f'{name}: the same page with the hidden picture counted (as it was) is held, so this check can see the fault', any(HELD in i for i in before.issues), before.issues)
    m = read(got['shown'])
    check('a picture that really runs past the question box still holds the question', any(HELD in i for i in m.issues), m.issues)
    words = lambda g: [x['text'] for x in g['lines']]
    check('the words and the drawn lines of the page are read the same with or without the hidden picture', all(words(got[n]) == words(got['shown']) for n in got)
          and all(len(got[n]['geometry']) == len(got['shown']['geometry']) - 1 for n in ('hidden_far', 'hidden_flat', 'hidden_apart')), {n: (len(words(g)), len(g['geometry'])) for n, g in got.items()})


def owners_page():
    if not Path(OWNER_BOOK).exists():
        print("NOT RUN: the owner's book (Mocks 26-50) is not on this machine; its page 2938 was not read", flush=True); return
    pages = (2937, 2938, 2939)
    got = dict(zip(pages, inspect_many(OWNER_BOOK, [{'action': 'text', 'page': n} for n in pages], 10)))
    check("the owner's pages 2937-2939 (their pictures are all hidden): no picture is counted", all(not g.get('error') and g['images'] == [] for g in got.values()), {n: (g.get('error'), g.get('images')) for n, g in got.items()})
    m = read(got[2938])
    check("the owner's page 2938 (Mock 45, Q46): read whole, not held", m.classification == 'questions' and not m.issues and [(r.role, r.number) for r in m.regions] == [('question', 46)], (m.issues, [(r.role, r.number) for r in m.regions]))
    doc = fitz.open(OWNER_BOOK); p = doc[2937]; w, h = p.rect.width, p.rect.height
    placed = [[b[0] / w, b[1] / h, b[2] / w, b[3] / h] for b in (i['bbox'] for i in p.get_image_info())]; doc.close()
    before = read(got[2938], images=placed, geometry=placed + got[2938]['geometry'])
    check("the owner's page 2938 with its hidden picture counted (as it was) is held", len(placed) == 1 and any(HELD in i for i in before.issues), (placed, before.issues))


if __name__ == '__main__':
    made_up(); owners_page()
    f = [r for r in RESULTS if not r[1]]
    print(f'TOTAL {len(RESULTS)} PASS {len(RESULTS) - len(f)} FAIL {len(f)}', flush=True)
    sys.exit(1 if f else 0)
