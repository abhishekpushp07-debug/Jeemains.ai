"""TEST-ONLY iteration 166: whole-page low-res validation (tejas_core.validate_crop_pages) correctness + fail-closed.
No DB, no network. Storage GET monkeypatched to ORIGINAL local PDF bytes. "old" = per-ref clip render at .3 (pre-166 path).
Run: cd /app/backend/tests && python -m pytest test_iter166_wholepage_validation.py -p no:cacheprovider -q -n0 -s
"""
import copy, gzip, json, sys
from pathlib import Path
import fitz, pytest

sys.path.insert(0, '/app/backend')
import tejas_core, tejas_storage  # noqa: E402
from tejas import derivatives  # noqa: E402
from tejas.canonical import CanonicalIntegrityError  # noqa: E402

RES = Path('/app/backend/resources'); AUDIT = Path('/app/data/jee_pyq/source_audit')
C = json.loads(gzip.decompress((RES / 'jee_pyq.json.gz').read_bytes()))['collections']
FILES = {f['id']: f for f in C['tejas_files']}
SETS = {s['id']: s for s in C['tejas_sets']}
JAN = sorted(s['id'] for s in SETS.values() if s['pyq_date'].startswith('2026-01'))
APR = sorted(s['id'] for s in SETS.values() if s['pyq_date'].startswith('2026-04'))
EV = {}
OUT = Path('/app/test_reports/iter166_wholepage_validation_evidence.json')


def paper(sid):
    s = SETS[sid]; f = FILES[s['file_ids'][0]]
    raw = (AUDIT / (f['source_drive_id'] + '.pdf')).read_bytes()
    refs = {}
    for q in s['questions']:
        for k in ('q_refs', 's_refs'):
            for r in q.get(k, []):
                refs[json.dumps(r, sort_keys=True, separators=(',', ':'))] = r
    return f, raw, list(refs.values())


def reset():
    for c in (derivatives._cache, tejas_core._crop_cache, derivatives._validation_cache):
        with c.lock:
            c.data.clear(); c.size = 0


@pytest.fixture(scope='module', autouse=True)
def dump():
    yield
    OUT.write_text(json.dumps(EV, indent=1, default=str))


@pytest.fixture
def spy(monkeypatch):
    """Records every geometry check, every Page.get_pixmap, PNG encodes, _render_crop_png, opened docs."""
    log = {'geom': [], 'pix': [], 'png': 0, 'render': 0, 'docs': [], 'get': 0}
    rg, rp, rv = tejas_core._crop_geometry, fitz.Page.get_pixmap, tejas_core.validate_pdf
    rt, rpil, rr = fitz.Pixmap.tobytes, fitz.Pixmap.pil_tobytes, tejas_core._render_crop_png

    def g(doc, ref):
        log['geom'].append(ref.get('page')); return rg(doc, ref)

    def p(self, *a, **k):
        m = k.get('matrix'); log['pix'].append((self.number, round(m.a, 3) if m else 1, k.get('clip') is None)); return rp(self, *a, **k)

    def v(data, **k):
        d = rv(data, **k); log['docs'].append(d); return d

    def enc(f):
        def w(*a, **k):
            log['png'] += 1; return f(*a, **k)
        return w

    def r(*a, **k):
        log['render'] += 1; return rr(*a, **k)
    monkeypatch.setattr(tejas_core, '_crop_geometry', g)
    monkeypatch.setattr(fitz.Page, 'get_pixmap', p)
    monkeypatch.setattr(tejas_core, 'validate_pdf', v)
    monkeypatch.setattr(fitz.Pixmap, 'tobytes', enc(rt))
    monkeypatch.setattr(fitz.Pixmap, 'pil_tobytes', enc(rpil))
    monkeypatch.setattr(tejas_core, '_render_crop_png', r)
    return log


def store(monkeypatch, log, mapping):
    def get(path):
        log['get'] += 1
        return mapping[path]
    monkeypatch.setattr(tejas_storage, 'get_object', get)


# 1. Every ref geometry-checked, exactly one whole-page .3 raster per referenced page, no PNG encode / no clip render
P164 = ['jee-main-pyq-2026-01-24-s1', 'jee-main-pyq-2026-04-08-s2']  # the 201/199-ref papers benchmarked in 163/164


@pytest.mark.parametrize('sid', P164 + [x for x in JAN + APR if x not in P164])
def test_all_refs_geometry_and_unique_pages(sid, spy, monkeypatch):
    f, raw, refs = paper(sid)
    store(monkeypatch, spy, {f['path']: raw}); reset()
    derivatives.validate_source_crops(f, refs)
    pages = {r['page'] for r in refs}
    row = {'refs': len(refs), 'geom': len(spy['geom']), 'pages': len(pages), 'pix': len(spy['pix']),
           'pix_unique': len({x[0] for x in spy['pix']}), 'png_encodes': spy['png'], 'render_crop': spy['render'], 'get': spy['get']}
    EV.setdefault('per_paper', {})[sid] = row
    assert row['geom'] == len(refs) and sorted(spy['geom']) == sorted(r['page'] for r in refs)
    assert row['pix'] == row['pix_unique'] == len(pages) and {x[0] + 1 for x in spy['pix']} == pages
    assert all(x[1] == 0.3 and x[2] for x in spy['pix'])
    assert spy['png'] == 0 and spy['render'] == 0 and spy['get'] == 1
    assert all(d.is_closed for d in spy['docs']) and len(derivatives._validation_cache.data) == 1
    if sid in P164:
        assert (len(refs), len(pages)) in ((201, 26), (199, 25)), (len(refs), len(pages))


def _mut_last_page_ref(refs, fn):
    refs = copy.deepcopy(refs); last = max(refs, key=lambda r: r['page']); fn(last); return refs


BAD = {
    'last_ref_invalid_page': lambda refs: copy.deepcopy(refs) + [{'page': 999, 'rect': [0, 0, 10, 10]}],
    'last_ref_outside_page': lambda refs: _mut_last_page_ref(refs, lambda r: r.update(rect=[0, 0, 99999, 99999])),
    'last_ref_bad_omission': lambda refs: _mut_last_page_ref(refs, lambda r: r.update(omit_rects=[[r['rect'][0] - 5, r['rect'][1], r['rect'][2], r['rect'][3]]])),
    'last_ref_empty_omission': lambda refs: _mut_last_page_ref(refs, lambda r: r.update(omit_rects=[[r['rect'][0], r['rect'][1], r['rect'][0], r['rect'][3]]])),
    # x0=10 -> 3.0px at .3; 0.002pt wide => (rect*.3).irect empty; old clip path raised FzErrorArgument at PNG encode
    'last_ref_zero_pixel_rect': lambda refs: _mut_last_page_ref(refs, lambda r: (r.pop('omit_rects', None), r.update(rect=[10, r['rect'][1], 10.002, r['rect'][3]]))),
    'last_ref_zero_area_rect': lambda refs: _mut_last_page_ref(refs, lambda r: r.update(rect=[10, 10, 10, 10])),
    'last_ref_missing_rect': lambda refs: _mut_last_page_ref(refs, lambda r: r.pop('rect')),
    'first_ref_page_zero': lambda refs: [{'page': 0, 'rect': [0, 0, 10, 10]}] + copy.deepcopy(refs),
}


# 2. Fail-closed: raises, no success proof cached, retry re-reads storage, doc closed
@pytest.mark.parametrize('name', list(BAD))
@pytest.mark.parametrize('sid', P164)
def test_negative_fail_closed(sid, name, spy, monkeypatch):
    f, raw, refs = paper(sid); bad = BAD[name](refs)
    store(monkeypatch, spy, {f['path']: raw}); reset()
    for _ in range(2):
        with pytest.raises((ValueError, KeyError)) as e:
            derivatives.validate_source_crops(f, bad)
    EV.setdefault('negatives', {})[f'{sid}:{name}'] = {'err': repr(e.value)[:90], 'geom_before_fail': len(spy['geom']) // 2, 'pix': len(spy['pix']) // 2}
    assert spy['get'] == 2 and not derivatives._validation_cache.data and spy['png'] == 0
    assert spy['docs'] and all(d.is_closed for d in spy['docs'])
    derivatives.validate_source_crops(f, refs)  # good set still validates afterwards
    assert len(derivatives._validation_cache.data) == 1


# 3. Canonical SHA / foreign source bytes rejected before any rendering, not cached
def test_sha_and_foreign_source(spy, monkeypatch):
    f, raw, refs = paper(P164[0]); f2, raw2, _ = paper(P164[1])
    store(monkeypatch, spy, {f['path']: raw2, f2['path']: raw2}); reset()
    with pytest.raises(CanonicalIntegrityError):
        derivatives.validate_source_crops(f, refs)  # foreign bytes under Jan's recorded hash
    with pytest.raises(CanonicalIntegrityError):
        derivatives.validate_source_crops({**f2, 'sha256': '0' * 64}, refs)
    assert not spy['pix'] and not spy['docs'] and not derivatives._validation_cache.data
    store(monkeypatch, spy, {f['path']: raw})
    with pytest.raises(ValueError):  # unreviewed policy -> ordinary 3000pt guard still applies, before raster
        derivatives.validate_source_crops({k: v for k, v in f.items() if k != 'source_collection'}, refs)
    assert not spy['pix'] and not derivatives._validation_cache.data


def _synthetic(rotation, annot=True):
    d = fitz.open(); p = d.new_page(width=600, height=800)
    p.insert_text((50, 100), 'Q1 text', fontsize=20); p.draw_rect(fitz.Rect(300, 300, 450, 450), color=(1, 0, 0), fill=(0, 0, 1))
    if annot:
        p.add_highlight_annot(fitz.Rect(50, 80, 250, 110)); p.add_freetext_annot(fitz.Rect(300, 600, 500, 650), 'note')
    d.new_page(width=600, height=800).insert_text((50, 100), 'page2', fontsize=20)
    for pg in d:
        pg.set_rotation(rotation)
    return d.tobytes()


def old_ok(doc, raw, ref):
    try:
        tejas_core._render_crop_png(raw, ref, .3, _document=doc); return True
    except Exception:  # noqa: BLE001  old path could also raise FzErrorArgument (zero-width pixmap PNG encode)
        return False


def new_ok(doc, ref):
    try:
        tejas_core.validate_crop_pages(doc, [ref]); return True
    except (ValueError, KeyError):
        return False


SYN_REFS = [{'page': 1, 'rect': [40, 60, 500, 500]}, {'page': 1, 'rect': [0, 0, 600, 800]}, {'page': 1, 'rect': [0, 0, 800, 600]},
            {'page': 1, 'rect': [550, 0, 790, 590]}, {'page': 1, 'rect': [40, 60, 500, 500], 'omit_rects': [[290, 290, 460, 460]]},
            {'page': 2, 'rect': [0, 0, 300, 200]}, {'page': 1, 'rect': [10, 10, 10.4, 700]}, {'page': 1, 'rect': [10, 10, 10.002, 700]},
            {'page': 1, 'rect': [10, 10, 590, 10.5]}, {'page': 1, 'rect': [5, 5, 6, 6]}, {'page': 3, 'rect': [0, 0, 10, 10]}] + [
            {'page': 1, 'rect': [x, 20, x + w, 700]} for x in (10, 10.0333, 10.3, 33.3333, 100, 0.0) for w in (0.0005, 0.002, 0.004, 0.01)] + [
            {'page': 1, 'rect': [20, y, 500, y + h]} for y in (10, 20.0333, 50) for h in (0.002, 0.004)]


# 4. Rotated pages / thin regions / annotations: new pass/fail decision == old clip-render decision (no new acceptance)
@pytest.mark.parametrize('rotation', [0, 90, 180, 270])
def test_rotation_thin_annotations_parity(rotation):
    raw = _synthetic(rotation)
    rows = []
    with tejas_core.validate_pdf(raw) as doc:
        for r in SYN_REFS:
            o, n = old_ok(doc, raw, r), new_ok(doc, r)
            rows.append((r['page'], r['rect'], 'omit' in json.dumps(r), o, n))
    EV.setdefault('rotation_parity', {})[rotation] = rows
    diverge = [x for x in rows if x[3] != x[4]]
    accepted_by_new_only = [x for x in diverge if x[4]]
    EV.setdefault('rotation_divergence', {})[rotation] = diverge
    assert not accepted_by_new_only, accepted_by_new_only  # whole-page must never accept something old rejected


def _bad_jpeg_pdf(kind):
    """Image XObject whose DCT stream is malformed: 'truncated' cuts the JPEG, 'garbage' is non-JPEG bytes."""
    from PIL import Image
    import io
    im = Image.new('RGB', (400, 300), (200, 30, 30)); b = io.BytesIO(); im.save(b, 'JPEG'); jpg = b.getvalue()
    d = fitz.open(); p = d.new_page(width=600, height=800); p.insert_text((50, 50), 'header', fontsize=12)
    p.insert_image(fitz.Rect(100, 100, 500, 400), stream=jpg)
    xref = p.get_images()[0][0]
    bad = jpg[:len(jpg) // 3] if kind == 'truncated' else b'\xff\xd8' + b'\x00garbage' * 50
    d.update_stream(xref, bad, compress=False)
    return d.tobytes()


# 5. Malformed embedded JPEG: record ACTUAL old vs new behaviour (MuPDF may only warn); assert parity of decision
@pytest.mark.parametrize('kind', ['truncated', 'garbage'])
def test_malformed_jpeg_old_vs_new(kind):
    raw = _bad_jpeg_pdf(kind); ref = {'page': 1, 'rect': [90, 90, 510, 410]}
    fitz.TOOLS.reset_mupdf_warnings()
    with tejas_core.validate_pdf(raw) as doc:
        o = old_ok(doc, raw, ref); wo = fitz.TOOLS.mupdf_warnings(); fitz.TOOLS.reset_mupdf_warnings()
        try:
            tejas_core.validate_crop_pages(doc, [ref]); n = 'accepted'
        except Exception as e:  # noqa: BLE001  record actual
            n = 'rejected: ' + repr(e)[:80]
        wn = fitz.TOOLS.mupdf_warnings()
    EV.setdefault('malformed_jpeg', {})[kind] = {'old': 'accepted' if o else 'rejected', 'new': n,
                                                  'old_warnings': wo[:200], 'new_warnings': wn[:200]}
    print(kind, EV['malformed_jpeg'][kind])
    assert ('accepted' if o else 'rejected') == n.split(':')[0]


# 6. Non-int / mixed page types: record behaviour (sort before geometry)
def test_mixed_page_types_fail_closed():
    raw = _synthetic(0)
    with tejas_core.validate_pdf(raw) as doc:
        res = {}
        for name, refs in {'str_page': [{'page': 1, 'rect': [0, 0, 10, 10]}, {'page': '2', 'rect': [0, 0, 10, 10]}],
                           'none_page': [{'page': None, 'rect': [0, 0, 10, 10]}],
                           'float_page': [{'page': 1.0, 'rect': [0, 0, 10, 10]}]}.items():
            try:
                tejas_core.validate_crop_pages(doc, refs); res[name] = 'accepted'
            except Exception as e:  # noqa: BLE001
                res[name] = type(e).__name__
    EV['mixed_page_types'] = res
    assert res['str_page'] != 'accepted' and res['none_page'] != 'accepted'
