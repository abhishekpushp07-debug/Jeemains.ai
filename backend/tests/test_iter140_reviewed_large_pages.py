"""TEST-ONLY iteration 140: reviewed large-page policy guards (validate_pdf / crop_png / render_crop).
No DB, no network. Storage GET boundary is monkeypatched to return local bytes (original Jan-2026 source PDF
or synthetic PDFs). No lenient validate_pdf monkeypatch.
Run: cd /app/backend/tests && python -m pytest test_iter140_reviewed_large_pages.py -n0 -p no:cacheprovider -v
"""
import gzip, json, sys, uuid
from hashlib import sha256
from pathlib import Path
import fitz, pytest

sys.path.insert(0, '/app/backend')
import tejas_core, tejas_storage  # noqa: E402
from tejas import derivatives  # noqa: E402
from tejas.canonical import CanonicalIntegrityError  # noqa: E402

RES = Path('/app/backend/resources'); AUDIT = Path('/app/data/jee_pyq/source_audit')
DATA = json.loads(gzip.decompress((RES / 'jee_pyq.json.gz').read_bytes()))
FILES = {f['id']: f for f in DATA['collections']['tejas_files']}
JAN = [s for s in DATA['collections']['tejas_sets'] if s['pyq_date'].startswith('2026-01')]
STORE = {}


@pytest.fixture(autouse=True)
def storage(monkeypatch):
    monkeypatch.setattr(tejas_storage, 'get_object', lambda p: STORE[p])
    yield


def synth(w, h):
    d = fitz.open(); pg = d.new_page(width=w, height=h); pg.insert_text((50, 100), 'TEST large page', fontsize=40)
    return d.tobytes()


def src(raw, reviewed=True, sha=True):
    p = 'TEST/' + uuid.uuid4().hex; STORE[p] = raw
    s = {'id': 'TEST_f', 'path': p, 'kind': 'combined'}
    if sha: s['sha256'] = sha256(raw).hexdigest()
    if reviewed: s['source_collection'] = 'jee-pyq-written'
    return s


def jan_source(paper):
    f = FILES[paper['file_ids'][0]]
    raw = (AUDIT / (f['source_drive_id'] + '.pdf')).read_bytes()
    assert sha256(raw).hexdigest() == f['sha256']
    return raw, {**f, 'path': 'TEST/jan/' + f['id']}


# ordinary upload validator still 3000pt
def test_ordinary_validator_rejects_over_3000():
    tejas_core.validate_pdf(synth(3000, 3000))
    with pytest.raises(ValueError):
        tejas_core.validate_pdf(synth(2479, 3508))
    raw, _ = jan_source(JAN[0])
    with pytest.raises(ValueError):
        tejas_core.validate_pdf(raw)
    tejas_core.validate_pdf(raw, reviewed_large_pages=True)


# oversize >4000pt rejected even when reviewed
def test_oversize_4000_rejected_even_reviewed():
    tejas_core.validate_pdf(synth(4000, 4000), reviewed_large_pages=True)
    with pytest.raises(ValueError):
        tejas_core.validate_pdf(synth(2000, 4001), reviewed_large_pages=True)
    s = src(synth(2000, 4100))
    with pytest.raises(ValueError):
        derivatives.render_crop(s, {'page': 1, 'rect': [0, 0, 500, 500]}, 2)


# untrusted large PDFs rejected (no collection label, or label without sha)
def test_untrusted_large_rejected():
    raw = synth(2479, 3508)
    with pytest.raises(ValueError):
        derivatives.render_crop(src(raw, reviewed=False), {'page': 1, 'rect': [0, 0, 600, 600]}, 2)
    with pytest.raises(ValueError):
        derivatives.render_crop(src(raw, reviewed=True, sha=False), {'page': 1, 'rect': [0, 0, 600, 600]}, 2)
    bad = src(raw); bad['source_collection'] = 'other-collection'
    with pytest.raises(ValueError):
        derivatives.render_crop(bad, {'page': 1, 'rect': [0, 0, 600, 600]}, 2)


# hash mismatch fails before render
def test_hash_mismatch_fails():
    raw, f = jan_source(JAN[0]); STORE[f['path']] = raw[:-1] + b'X'
    ref = JAN[0]['questions'][0]['q_refs'][0]
    with pytest.raises(CanonicalIntegrityError):
        derivatives.render_crop({**f, 'path': f['path']}, {**ref, 'rect': [r + 0.001 for r in ref['rect']]}, 2)


# no cache bypass: reviewed render cached, untrusted identity with same bytes/ref still rejected (both caches)
def test_no_cache_bypass():
    raw = synth(2479, 3508); ref = {'page': 1, 'rect': [10, 10, 1210, 900]}
    s = src(raw); png = derivatives.render_crop(s, ref, 2)
    assert png[:8] == b'\x89PNG\r\n\x1a\n'
    assert derivatives.render_crop(s, ref, 2) == png
    with pytest.raises(ValueError):
        derivatives.render_crop({**s, 'source_collection': None}, ref, 2)
    assert tejas_core.crop_png(raw, ref, 2, reviewed_large_pages=True)
    with pytest.raises(ValueError):
        tejas_core.crop_png(raw, ref, 2)


# all 10 Jan papers: every q/s ref renders at preflight scale and real scale within 1600x2400 (+1px rounding)
def test_all_jan_refs_render_bounded():
    out = Path('/tmp/iter140'); out.mkdir(exist_ok=True)
    stats = {}
    for paper in JAN:
        raw, f = jan_source(paper); STORE[f['path']] = raw
        refs = {json.dumps(r, sort_keys=True): r for q in paper['questions'] for r in q['q_refs'] + q['s_refs']}
        mw = mh = 0
        allr = list(refs.values())
        # largest-width, largest-height + every 15th ref rendered at real scale (full set runs via API preflight test)
        sample = {id(r): r for r in sorted(allr, key=lambda r: r['rect'][2] - r['rect'][0])[-3:] + sorted(allr, key=lambda r: r['rect'][3] - r['rect'][1])[-3:] + allr[::15]}
        for r in sample.values():
            png = derivatives.render_crop(f, r, 2)
            pm = fitz.Pixmap(png); mw, mh = max(mw, pm.width), max(mh, pm.height)
            assert pm.width <= 1601 and pm.height <= 2401, (paper['id'], r, pm.width, pm.height)
        stats[paper['id']] = (len(refs), mw, mh)
        q = paper['questions'][25]
        (out / f"{paper['id']}_q26.png").write_bytes(derivatives.render_crop(f, q['q_refs'][0], 2))
        if q['s_refs']:
            (out / f"{paper['id']}_q26_sol.png").write_bytes(derivatives.render_crop(f, q['s_refs'][0], 2))
    print('STATS', stats)
    assert len(stats) == 10 and sum(v[0] for v in stats.values()) > 1000


# coordinates unchanged in bundle (refs are within page; no rescaling of source rects)
def test_refs_inside_source_pages():
    for paper in JAN:
        raw, _ = jan_source(paper); d = fitz.open(stream=raw, filetype='pdf')
        for q in paper['questions']:
            for r in q['q_refs'] + q['s_refs']:
                assert d[r['page'] - 1].rect.contains(fitz.Rect(r['rect']))
