"""TEST-ONLY iteration 141: PYQ preflight performance + guard cases for derivatives.validate_source_crops.
No DB, no network. Storage GET boundary monkeypatched to return ORIGINAL local Jan-2026 source PDF bytes.
Measures old validate_refs-equivalent loop (render_crop per unique ref at .3) vs new batch validator,
cold / warm / 4-way concurrent, with call counts for get_object, fitz.open, _render_crop_png, get_pixmap.
Run: cd /app/backend/tests && python -m pytest test_iter141_preflight_perf.py -n0 -p no:cacheprovider -v
"""
import copy, gzip, json, sys, time, threading
from concurrent.futures import ThreadPoolExecutor
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
JAN = sorted([s for s in DATA['collections']['tejas_sets'] if s['pyq_date'].startswith('2026-01')], key=lambda s: s['id'])
PAPER = JAN[0]
FID = PAPER['file_ids'][0]
RAW = (AUDIT / (FILES[FID]['source_drive_id'] + '.pdf')).read_bytes()
SRC = {**FILES[FID], 'path': 'TEST/jan141/' + FID}
STORE = {SRC['path']: RAW}
C = {'get': 0, 'open': 0, 'render': 0, 'pixmap': 0}
LK = threading.Lock()
EV = {}
OUT = Path('/app/test_reports/iter141_preflight_perf_evidence.json')


def unique_refs(s):
    # identical to attempts.preflight unique-ref collection (q_refs then s_refs, JSON identity)
    seen, out = set(), []
    for q in s['questions']:
        for kind in ('q_refs', 's_refs'):
            for ref in q.get(kind, []):
                k = json.dumps(ref, sort_keys=True, separators=(',', ':'))
                if k not in seen:
                    seen.add(k); out.append(ref)
    return out


REFS = unique_refs(PAPER)


def bump(k):
    with LK: C[k] += 1


@pytest.fixture(autouse=True)
def counters(monkeypatch):
    real_open, real_render, real_pix = fitz.open, tejas_core._render_crop_png, fitz.Page.get_pixmap
    def g(p):
        bump('get'); return STORE[p]
    def o(*a, **k):
        bump('open'); return real_open(*a, **k)
    def r(*a, **k):
        bump('render'); return real_render(*a, **k)
    def px(self, *a, **k):
        bump('pixmap'); return real_pix(self, *a, **k)
    monkeypatch.setattr(tejas_storage, 'get_object', g)
    monkeypatch.setattr(fitz, 'open', o)
    monkeypatch.setattr(tejas_core, '_render_crop_png', r)
    monkeypatch.setattr(fitz.Page, 'get_pixmap', px)
    yield


def reset():
    for c in (derivatives._cache, tejas_core._crop_cache, derivatives._validation_cache):
        with c.lock:
            c.data.clear(); c.size = 0
    for k in C: C[k] = 0


def snap():
    return dict(C)


def old_loop(source, refs):
    # equivalent of content.validate_refs for one file: render_crop(f, r, 0.3) for every ref, sequential
    for r in refs:
        derivatives.render_crop(source, r, 0.3)


def timed(fn, *a):
    t = time.perf_counter(); fn(*a); return round(time.perf_counter() - t, 3)


@pytest.fixture(scope='module', autouse=True)
def dump():
    yield
    OUT.write_text(json.dumps(EV, indent=2, default=str))


# Baseline vs new, cold + warm, with call counts on the actual Jan 2026 paper/original PDF
def test_baseline_vs_new_cold_warm():
    assert sha256(RAW).hexdigest() == SRC['sha256'] and SRC['source_collection'] == 'jee-pyq-written'
    n = len(REFS)
    reset(); old_cold = timed(old_loop, SRC, REFS); old_cold_c = snap()
    for k in C: C[k] = 0
    old_warm = timed(old_loop, SRC, REFS); old_warm_c = snap()
    reset(); new_cold = timed(derivatives.validate_source_crops, SRC, REFS); new_cold_c = snap()
    for k in C: C[k] = 0
    new_warm = timed(derivatives.validate_source_crops, SRC, REFS); new_warm_c = snap()
    EV['paper'] = PAPER['id']; EV['unique_refs'] = n; EV['pdf_bytes'] = len(RAW)
    EV['old'] = {'cold_s': old_cold, 'cold_calls': old_cold_c, 'warm_s': old_warm, 'warm_calls': old_warm_c}
    EV['new'] = {'cold_s': new_cold, 'cold_calls': new_cold_c, 'warm_s': new_warm, 'warm_calls': new_warm_c}
    # old opens/reads the PDF once per unique ref
    assert old_cold_c['get'] == n and old_cold_c['open'] == n and old_cold_c['render'] == n
    # new: one GET, one fitz Document, every unique region rendered (no skipped regions)
    assert new_cold_c == {'get': 1, 'open': 1, 'render': n, 'pixmap': n}, new_cold_c
    assert new_warm_c == {'get': 0, 'open': 0, 'render': 0, 'pixmap': 0}, new_warm_c
    assert new_cold < old_cold, (new_cold, old_cold)


# All 10 Jan papers cold with new validator: one GET/open per paper, every region rendered
def test_all_jan_papers_new_cold():
    rows = {}
    for s in JAN:
        fid = s['file_ids'][0]
        raw = (AUDIT / (FILES[fid]['source_drive_id'] + '.pdf')).read_bytes()
        src = {**FILES[fid], 'path': 'TEST/jan141/' + fid}; STORE[src['path']] = raw
        refs = unique_refs(s); reset()
        rows[s['id']] = {'refs': len(refs), 's': timed(derivatives.validate_source_crops, src, refs), 'calls': snap()}
        assert rows[s['id']]['calls'] == {'get': 1, 'open': 1, 'render': len(refs), 'pixmap': len(refs)}
    EV['all_jan_new_cold'] = rows
    EV['all_jan_new_cold_max_s'] = max(r['s'] for r in rows.values())


# 4 concurrent cold requests coalesce on striped lock: one GET/open/render pass total
def test_four_concurrent_coalesced():
    reset()
    t = time.perf_counter()
    with ThreadPoolExecutor(4) as ex:
        list(ex.map(lambda _: derivatives.validate_source_crops(SRC, list(REFS)), range(4)))
    EV['new_concurrent4'] = {'wall_s': round(time.perf_counter() - t, 3), 'calls': snap()}
    assert snap() == {'get': 1, 'open': 1, 'render': len(REFS), 'pixmap': len(REFS)}, snap()
    # shuffled order of same complete ref set reuses proof
    for k in C: C[k] = 0
    derivatives.validate_source_crops(SRC, list(reversed(REFS)))
    assert snap()['get'] == 0
    reset(); t = time.perf_counter()
    with ThreadPoolExecutor(4) as ex:
        list(ex.map(lambda _: old_loop(SRC, REFS), range(4)))
    EV['old_concurrent4'] = {'wall_s': round(time.perf_counter() - t, 3), 'calls': snap()}


# Shared-document render bytes identical to independent render (no shortcut in .3 validation)
def test_shared_document_render_equivalent():
    reviewed = True
    with tejas_core.validate_pdf(RAW, reviewed_large_pages=reviewed) as doc:
        for r in REFS[:6] + REFS[-3:]:
            a = tejas_core._render_crop_png(RAW, r, .3, reviewed_large_pages=reviewed, _document=doc)
            b = tejas_core._render_crop_png(RAW, r, .3, reviewed_large_pages=reviewed)
            assert a == b


def _bad(mut):
    refs = copy.deepcopy(REFS); mut(refs); return refs


BAD = {
    'last_bad_coords': lambda r: r[-1].update(rect=[0, 0, 99999, 99999]),
    'last_invalid_page': lambda r: r[-1].update(page=999),
    'last_page_zero': lambda r: r[-1].update(page=0),
    'last_bad_omit': lambda r: r[-1].update(omit_rects=[[0, 0, 5, 5]] if r[-1]['rect'][0] > 5 else [[-50, -50, -10, -10]]),
    'last_missing_rect': lambda r: r[-1].pop('rect'),
    'last_empty_rect': lambda r: r[-1].update(rect=[10, 10, 10, 10]),
}


# Negative LAST-ref cases fail, are not cached and repeat the work on retry
@pytest.mark.parametrize('name', list(BAD))
def test_negative_last_ref_not_cached(name):
    refs = _bad(BAD[name]); reset()
    with pytest.raises((ValueError, KeyError, TypeError)):
        derivatives.validate_source_crops(SRC, refs)
    first = snap()
    assert first['get'] == 1 and first['open'] == 1 and first['render'] == len(refs)  # earlier refs were all rendered
    assert len(derivatives._validation_cache.data) == 0
    with pytest.raises((ValueError, KeyError, TypeError)):
        derivatives.validate_source_crops(SRC, refs)
    assert C['get'] == 2  # not served from cache
    EV.setdefault('negatives', {})[name] = first


# Hash mismatch raises CanonicalIntegrityError before rendering and is not cached
def test_hash_mismatch_not_cached():
    reset()
    STORE['TEST/tampered'] = RAW[:-1] + b'X'
    bad = {**SRC, 'path': 'TEST/tampered'}
    for _ in range(2):
        with pytest.raises(CanonicalIntegrityError):
            derivatives.validate_source_crops(bad, REFS)
    assert C['get'] == 2 and C['open'] == 0 and C['render'] == 0 and not derivatives._validation_cache.data
    # INFO: content-addressed proof (same as old render_crop cache): after a success, storage bytes are not
    # re-read for the same sha within the process; record behaviour, do not assert either way.
    derivatives.validate_source_crops(SRC, REFS)
    try:
        derivatives.validate_source_crops(bad, REFS); EV['tamper_after_success_same_sha'] = 'served from proof (no re-read)'
    except CanonicalIntegrityError:
        EV['tamper_after_success_same_sha'] = 'rechecked'


# Mutated refs / new sha / review-policy change cannot reuse a successful proof
def test_proof_key_sensitivity():
    reset(); derivatives.validate_source_crops(SRC, REFS); assert len(derivatives._validation_cache.data) == 1
    for k in C: C[k] = 0
    mutated = copy.deepcopy(REFS); mutated[-1]['rect'] = [mutated[-1]['rect'][0], mutated[-1]['rect'][1], mutated[-1]['rect'][2] - 1, mutated[-1]['rect'][3]]
    derivatives.validate_source_crops(SRC, mutated); assert C['get'] == 1
    subset = REFS[:-1]; derivatives.validate_source_crops(SRC, subset); assert C['get'] == 2  # subset != complete set
    with pytest.raises(CanonicalIntegrityError):
        derivatives.validate_source_crops({**SRC, 'sha256': '0' * 64}, REFS)  # new sha
    assert C['get'] == 3
    with pytest.raises(ValueError):  # policy change: unreviewed -> ordinary 3000pt guard applies
        derivatives.validate_source_crops({k: v for k, v in SRC.items() if k != 'source_collection'}, REFS)
    with pytest.raises(ValueError):
        derivatives.validate_source_crops({**SRC, 'source_collection': 'other'}, REFS)
    assert C['get'] == 5
    nosha = {k: v for k, v in SRC.items() if k != 'sha256'}  # not cacheable, and also not reviewed
    with pytest.raises(ValueError):
        derivatives.validate_source_crops(nosha, REFS)


# Concurrent failures do not cache
def test_concurrent_failures_not_cached():
    refs = _bad(BAD['last_bad_coords']); reset(); errs = []
    def go(_):
        try:
            derivatives.validate_source_crops(SRC, refs)
        except ValueError as e:
            errs.append(e)
    with ThreadPoolExecutor(4) as ex:
        list(ex.map(go, range(4)))
    assert len(errs) == 4 and C['get'] == 4 and not derivatives._validation_cache.data


# Validation proof cache bounded at 256 entries (8 KiB / 32-byte values)
def test_validation_cache_bound():
    reset()
    for i in range(300):
        derivatives._validation_cache.put(('k', i), bytes(32))
    assert len(derivatives._validation_cache.data) == 256 and derivatives._validation_cache.size <= 8 * 1024


# Ordinary 3000pt upload guard unchanged
def test_ordinary_guard_unchanged():
    with pytest.raises(ValueError):
        tejas_core.validate_pdf(RAW)
    d = fitz.open(); d.new_page(width=3001, height=500)
    with pytest.raises(ValueError):
        tejas_core.validate_pdf(d.tobytes())
