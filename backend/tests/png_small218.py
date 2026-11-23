"""TEST-ONLY (iteration 218): lossless PNG shrinking of real PDF crops. No database, no storage.
Makes question-sized crops from local PDFs through the real sandboxed PDF worker, shrinks them with tejas.png_small and checks every
result is pixel-for-pixel the same picture. Prints the measured saving per oxipng level and the time it costs.
Run: cd /app/backend && python tests/png_small218.py [pages_per_pdf]
"""
import io, sys, time
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from PIL import Image  # noqa: E402
import oxipng  # noqa: E402
from tejas.book_pdf import inspect, inspect_many  # noqa: E402
from tejas import png_small  # noqa: E402

PDFS = [p for p in ('/root/pdfengine/aits_maths.pdf', '/root/pdfengine/chemistry_chapterwise.pdf', '/app/data/mocks/mocks.pdf') if Path(p).exists()]
BANDS = [(.06, .08, .94, .34), (.06, .34, .94, .62), (.06, .62, .94, .92)]
RESULTS = []


def check(name, ok, info=''):
    RESULTS.append(bool(ok))
    print(('PASS ' if ok else 'FAIL ') + name + ('' if ok else f'  -> {info}'), flush=True)


def same(a, b):
    x, y = Image.open(io.BytesIO(a)), Image.open(io.BytesIO(b))
    return x.size == y.size and x.convert('RGBA').tobytes() == y.convert('RGBA').tobytes()


def crops(pdf, count):
    pages = inspect(pdf)['pages']
    step = max(1, pages // count)
    items = []
    for n in list(range(3, pages, step))[:count]:
        for r in BANDS:
            items.append({'action': 'crop', 'page': n, 'rect': list(r)})
            items.append({'action': 'piece', 'page': n, 'rect': list(r), 'scale': 2, 'erase': []})
    return [c['image_bytes'] for c in inspect_many(pdf, items, 20) if c.get('image_bytes')]


def main():
    count = int(sys.argv[1]) if len(sys.argv) > 1 else 25
    check('a local PDF is available', bool(PDFS), 'no sample PDF found')
    total_before = total_after = 0
    for pdf in PDFS:
        pics = crops(pdf, count)
        before = sum(map(len, pics))
        line = [f'{Path(pdf).name}: {len(pics)} pictures, {before / 1024:.0f} KB']
        for level in (2, 4, 6):
            t = time.time()
            small = [oxipng.optimize_from_memory(p, level=level, strip=oxipng.StripChunks.safe()) for p in pics]
            line.append(f'level {level}: -{100 - 100 * sum(map(len, small)) / before:.1f}% in {time.time() - t:.1f}s')
        print(' | '.join(line), flush=True)
        t = time.time()
        out = png_small.shrink_many(pics)
        took = time.time() - t
        after = sum(map(len, out))
        total_before += before
        total_after += after
        check(f'{Path(pdf).name}: same number of pictures, same order', len(out) == len(pics))
        check(f'{Path(pdf).name}: every picture is pixel-for-pixel the same', all(same(a, b) for a, b in zip(pics, out)))
        check(f'{Path(pdf).name}: no picture got bigger', all(len(b) <= len(a) for a, b in zip(pics, out)))
        print(f'  shrink_many (as used when publishing): {before / 1024:.0f} KB -> {after / 1024:.0f} KB (-{100 - 100 * after / before:.1f}%) in {took:.1f}s '
              f'({1000 * took / max(1, len(pics)):.0f} ms per picture)', flush=True)
    check('broken bytes keep their original', png_small.shrink_many([b'not a png', b'']) == [b'not a png', b''])
    check('an empty list stays empty', png_small.shrink_many([]) == [])
    if total_before:
        print(f'TOTAL {total_before / 1024:.0f} KB -> {total_after / 1024:.0f} KB = -{100 - 100 * total_after / total_before:.1f}%', flush=True)
    print(f'{sum(RESULTS)}/{len(RESULTS)} passed', flush=True)
    return 0 if all(RESULTS) else 1


if __name__ == '__main__':
    sys.exit(main())
