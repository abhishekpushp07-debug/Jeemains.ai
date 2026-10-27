"""TEST-ONLY iteration 164: pixel fidelity of the new renderer (grayscale-when-identical + DisplayList validation)
vs an ISOLATED copy of the pre-change renderer from git 9d5e193. Reads ORIGINAL LOCAL PDFs; no DB, no storage writes.
Run: cd /app/backend/tests && python -m pytest test_iter164_pixel_fidelity.py -p no:cacheprovider -q -s
"""
import gzip, io, json, math, os, sys
from pathlib import Path
import fitz, numpy as np, pytest
from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import tejas_core  # noqa: E402
from tejas import derivatives  # noqa: E402
from tejas.canonical import CanonicalIntegrityError  # noqa: E402

RES = Path('/app/backend/resources'); AUDIT = Path('/app/data/jee_pyq/source_audit')
C = json.loads(gzip.decompress((RES / 'jee_pyq.json.gz').read_bytes()))['collections']
FILES = {f['id']: f for f in C['tejas_files']}
SETS = {s['id']: s for s in C['tejas_sets']}
PAPERS = ['jee-main-pyq-2026-01-24-s1', 'jee-main-pyq-2026-04-08-s2']
OUT = Path(os.environ.get('PNG_OUT', '/tmp/iter164_png')); OUT.mkdir(exist_ok=True)  # iter166: PNG_OUT override (test-only)
STATS = {}


# ---- isolated reference: pre-change _render_crop_png copied verbatim from git 9d5e193 ----
def old_render(data, ref, scale=2, *, reviewed_large_pages=False, _document=None):
    doc = _document if _document is not None else tejas_core.validate_pdf(data, reviewed_large_pages=reviewed_large_pages)
    p = ref["page"] - 1
    if p < 0 or p >= len(doc):
        raise ValueError("Source page is out of range.")
    rect = fitz.Rect(ref["rect"])
    if rect.is_empty or not doc[p].rect.contains(rect):
        raise ValueError("Source region is outside the page.")
    if reviewed_large_pages:
        scale = min(scale, 1600 / rect.width, 2400 / rect.height)
    pix = doc[p].get_pixmap(matrix=fitz.Matrix(scale, scale), clip=rect, alpha=False)
    if ref.get('omit_rects'):
        pixels = np.frombuffer(pix.samples, dtype=np.uint8).reshape(pix.height, pix.width, pix.n).copy()
        for coordinates in ref['omit_rects']:
            omitted = fitz.Rect(coordinates)
            if omitted.is_empty or not rect.contains(omitted):
                raise ValueError('Omitted source region must be within its crop.')
            left, top = max(0, math.floor(omitted.x0 * scale) - pix.x), max(0, math.floor(omitted.y0 * scale) - pix.y)
            right, bottom = math.ceil(omitted.x1 * scale) - pix.x, math.ceil(omitted.y1 * scale) - pix.y
            pixels[top:bottom, left:right] = 255
        pix = fitz.Pixmap(fitz.csRGB, pix.width, pix.height, pixels.tobytes(), False)
    return pix.tobytes('png')


def rgb(png):
    im = Image.open(io.BytesIO(png)); mode = im.mode
    return np.asarray(im.convert('RGB')), mode


def paper(sid):
    s = SETS[sid]
    f = FILES[s['file_ids'][0]]
    raw = (AUDIT / (f['source_drive_id'] + '.pdf')).read_bytes()
    refs = {}
    for q in s['questions']:
        for k in ('q_refs', 's_refs'):
            for r in q.get(k, []):
                refs[json.dumps(r, sort_keys=True)] = (r, q['number'], k)
    return s, f, raw, refs


@pytest.mark.parametrize('sid', PAPERS)
def test_all_refs_pixel_identical(sid):
    s, f, raw, refs = paper(sid)
    reviewed = f.get('source_collection') == 'jee-pyq-written' and bool(f.get('sha256'))
    doc = tejas_core.validate_pdf(raw, reviewed_large_pages=reviewed)
    rot = sorted({p.rotation for p in doc}); omit = sum(1 for r, _, _ in refs.values() if r.get('omit_rects'))
    mism, modes, multi, saved = [], {}, 0, 0
    qnums = {}
    for r, n, k in refs.values():
        qnums.setdefault(n, set()).add(r['page'])
        a = old_render(raw, r, 2, reviewed_large_pages=reviewed, _document=doc)
        b = tejas_core._render_crop_png(raw, r, 2, reviewed_large_pages=reviewed)
        pa, _ = rgb(a); pb, mb = rgb(b)
        modes[mb] = modes.get(mb, 0) + 1; saved += len(a) - len(b)
        if pa.shape != pb.shape or not np.array_equal(pa, pb):
            mism.append((n, k, r['page']))
    multi = sum(1 for v in qnums.values() if len(v) > 1)
    STATS[sid] = {'refs': len(refs), 'modes': modes, 'bytes_saved_total': saved, 'page_rotations': rot,
                  'omit_rect_refs': omit, 'multipage_questions': multi, 'mismatches': mism}
    print(sid, STATS[sid])
    assert len(refs) in (199, 201) and not mism


@pytest.mark.parametrize('sid', PAPERS)
def test_validation_displaylist_matches_get_pixmap(sid):
    """low-res validation path (DisplayList) must be pixel-identical to page.get_pixmap reference."""
    s, f, raw, refs = paper(sid)
    reviewed = True
    doc = tejas_core.validate_pdf(raw, reviewed_large_pages=reviewed)
    dls, bad = {}, []
    for r, n, k in sorted(refs.values(), key=lambda x: x[0]['page']):
        a = old_render(raw, r, .3, reviewed_large_pages=reviewed, _document=doc)
        b = tejas_core._render_crop_png(raw, r, .3, reviewed_large_pages=reviewed, _document=doc, _display_lists=dls)
        if not np.array_equal(rgb(a)[0], rgb(b)[0]):
            bad.append((n, k))
    assert len(dls) <= 2 and not bad, bad
    assert not doc.is_closed  # caller-owned document must not be closed


def _synthetic_pdf(rotation):
    d = fitz.open(); p = d.new_page(width=600, height=800)
    p.insert_text((50, 100), 'Q1 grayscale text', fontsize=20)
    p.draw_rect(fitz.Rect(300, 300, 450, 450), color=(1, 0, 0), fill=(0, 0, 1))
    p.add_highlight_annot(fitz.Rect(50, 80, 250, 110))  # colored annotation
    p2 = d.new_page(width=600, height=800); p2.insert_text((50, 100), 'page2', fontsize=20)
    for pg in d:
        pg.set_rotation(rotation)
    return d.tobytes()


@pytest.mark.parametrize('rotation', [0, 90, 180, 270])
def test_synthetic_rotation_color_annot_omit(rotation):
    raw = _synthetic_pdf(rotation)
    doc = tejas_core.validate_pdf(raw)
    refs = [{'page': 1, 'rect': [40, 60, 500, 500]}, {'page': 1, 'rect': [40, 60, 290, 140]},
            {'page': 1, 'rect': [40, 60, 500, 500], 'omit_rects': [[290, 290, 460, 460]]}, {'page': 2, 'rect': [0, 0, 300, 200]}]
    dls = {}
    for r in refs:
        for sc in (2, .3):
            a = old_render(raw, r, sc, _document=doc)
            b = tejas_core._render_crop_png(raw, r, sc)
            c = tejas_core._render_crop_png(raw, r, sc, _document=doc, _display_lists=dls)
            assert np.array_equal(rgb(a)[0], rgb(b)[0]) and np.array_equal(rgb(a)[0], rgb(c)[0]), (rotation, r, sc)
    # colored crop must stay RGB; omitted-colour-only crop may become gray
    assert rgb(tejas_core._render_crop_png(raw, refs[0], 2))[1] == 'RGB'
    assert rgb(tejas_core._render_crop_png(raw, refs[3], 2))[1] == 'L'


def test_render_errors_close_doc_and_fail():
    raw = _synthetic_pdf(0)
    opened = []
    real = tejas_core.validate_pdf
    def spy(data, **k):
        d = real(data, **k); opened.append(d); return d
    tejas_core.validate_pdf = spy
    try:
        for bad in ({'page': 9, 'rect': [0, 0, 10, 10]}, {'page': 1, 'rect': [0, 0, 9999, 10]},
                    {'page': 1, 'rect': [0, 0, 100, 100], 'omit_rects': [[50, 50, 400, 400]]}):
            with pytest.raises(ValueError):
                tejas_core._render_crop_png(raw, bad)
    finally:
        tejas_core.validate_pdf = real
    assert opened and all(d.is_closed for d in opened)


def test_validate_source_crops_fail_closed_not_cached(monkeypatch):
    s, f, raw, refs = paper(PAPERS[0])
    import tejas_storage
    calls = []
    monkeypatch.setattr(tejas_storage, 'get_object', lambda p: calls.append(p) or raw)
    derivatives._validation_cache.data.clear(); derivatives._validation_cache.size = 0
    good = [r for r, _, _ in refs.values()]
    bad_last = good + [{'file_id': f['id'], 'page': 999, 'rect': [0, 0, 10, 10]}]
    for _ in range(2):  # second call must re-validate (failure NOT cached)
        with pytest.raises(ValueError):
            derivatives.validate_source_crops(f, bad_last)
    assert len(calls) == 2 and derivatives._validation_cache.size == 0
    with pytest.raises(CanonicalIntegrityError):
        derivatives.validate_source_crops({**f, 'sha256': '0' * 64}, good)
    other = FILES[SETS[PAPERS[1]]['file_ids'][0]]  # foreign source bytes vs recorded hash
    with pytest.raises(CanonicalIntegrityError):
        derivatives.validate_source_crops(other, good[:3])
    assert derivatives._validation_cache.size == 0
    derivatives.validate_source_crops(f, good)
    n = len(calls); derivatives.validate_source_crops(f, good)
    assert len(calls) == n and derivatives._validation_cache.size > 0  # success cached


def test_derivative_path_no_core_crop_cache(monkeypatch):
    s, f, raw, refs = paper(PAPERS[1])
    import tejas_storage
    monkeypatch.setattr(tejas_storage, 'get_object', lambda p: raw)
    before = tejas_core._crop_cache.size
    r = next(iter(refs.values()))[0]
    png = derivatives.render_crop(f, r, 2)
    assert png[:8] == b'\x89PNG\r\n\x1a\n' and tejas_core._crop_cache.size == before


def test_jan24_s1_q2_and_dump_pngs():
    s, f, raw, refs = paper(PAPERS[0])
    q2 = next(q for q in s['questions'] if q['number'] == 2)
    doc = fitz.open(stream=raw, filetype='pdf')
    info = []
    for k in ('q_refs', 's_refs'):
        for i, r in enumerate(q2.get(k, [])):
            png = tejas_core._render_crop_png(raw, r, 2, reviewed_large_pages=True)
            p = OUT / f'jan24s1_q2_{k}_{i}.png'; p.write_bytes(png)
            text = doc[r['page'] - 1].get_text('text', clip=fitz.Rect(r['rect'])).strip().replace('\n', ' | ')
            info.append({'ref': k, 'i': i, 'page': r['page'], 'rect': r['rect'], 'png': str(p), 'text_layer': text[:300]})
    # representative extra images: April colored/first question + solution
    s2, f2, raw2, _ = paper(PAPERS[1])
    for q in s2['questions'][:1] + [x for x in s2['questions'] if len(x.get('q_refs', [])) > 1][:1]:
        for k in ('q_refs', 's_refs'):
            for i, r in enumerate(q.get(k, [])[:2]):
                (OUT / f'apr08s2_q{q["number"]}_{k}_{i}.png').write_bytes(tejas_core._render_crop_png(raw2, r, 2, reviewed_large_pages=True))
    (OUT / 'q2_info.json').write_text(json.dumps(info, indent=1))
    print(json.dumps(info, indent=1))
    assert q2.get('q_refs')
