"""TEST-ONLY iter166 microbench: PNG encode CPU/bytes pre-163 (pix.tobytes('png') RGB) vs current (gray check + Pillow compress 6),
on ALL full-res reviewed refs of Jan24S1 + Apr08S2; plus GIL-hold probe old clip-loop vs new whole-page validation."""
import sys, time, json, threading, statistics
sys.path.insert(0, '/app/backend/tests'); sys.path.insert(0, '/app/backend')
import fitz, numpy as np, tejas_core
from test_iter166_wholepage_validation import paper
OUT = {}


def enc_old(pix):
    return pix.tobytes('png')


def enc_new(pix):
    pixels = np.frombuffer(pix.samples, dtype=np.uint8).reshape(pix.height, pix.width, pix.n)
    if pix.n == 3 and np.array_equal(pixels[:, :, 0], pixels[:, :, 1]) and np.array_equal(pixels[:, :, 0], pixels[:, :, 2]):
        pix = fitz.Pixmap(fitz.csGRAY, pix.width, pix.height, pixels[:, :, 0].tobytes(), False)
    return pix.pil_tobytes(format='PNG', compress_level=6)


def cpu(fn, *a, **k):
    t, w = time.process_time(), time.perf_counter(); r = fn(*a, **k); return r, time.process_time() - t, time.perf_counter() - w


for sid in ('jee-main-pyq-2026-01-24-s1', 'jee-main-pyq-2026-04-08-s2'):
    f, raw, refs = paper(sid)
    rows = []
    with tejas_core.validate_pdf(raw, reviewed_large_pages=True) as doc:
        for r in refs:
            page, rect = tejas_core._crop_geometry(doc, r)
            sc = min(2, 1600 / rect.width, 2400 / rect.height)
            pix, rc, _ = cpu(page.get_pixmap, matrix=fitz.Matrix(sc, sc), clip=rect, alpha=False)
            bo, co, _ = cpu(enc_old, pix); bn, cn, _ = cpu(enc_new, pix)
            bo2, co2, _ = cpu(enc_old, pix); bn2, cn2, _ = cpu(enc_new, pix)
            rows.append({'px': pix.width * pix.height, 'raster_cpu': rc, 'old_cpu': min(co, co2), 'new_cpu': min(cn, cn2), 'old_b': len(bo), 'new_b': len(bn)})
    tot = lambda k: round(sum(x[k] for x in rows), 3)  # noqa: E731
    big = sorted(rows, key=lambda x: -x['px'])[:10]
    OUT[sid] = {'refs': len(rows), 'raster_cpu_s': tot('raster_cpu'), 'encode_old_cpu_s': tot('old_cpu'), 'encode_new_cpu_s': tot('new_cpu'),
                'bytes_old': tot('old_b'), 'bytes_new': tot('new_b'),
                'per_image_end_to_end_cpu_ratio_median': round(statistics.median((x['raster_cpu'] + x['new_cpu']) / (x['raster_cpu'] + x['old_cpu']) for x in rows), 3),
                'top10_largest': [{'px': x['px'], 'old_ms': round(x['old_cpu'] * 1000, 1), 'new_ms': round(x['new_cpu'] * 1000, 1),
                                   'raster_ms': round(x['raster_cpu'] * 1000, 1), 'old_kb': x['old_b'] // 1024, 'new_kb': x['new_b'] // 1024} for x in big],
                'max_new_minus_old_ms': round(max(x['new_cpu'] - x['old_cpu'] for x in rows) * 1000, 1),
                'n_new_bigger_bytes': sum(x['new_b'] > x['old_b'] for x in rows)}
    print(sid, json.dumps({k: v for k, v in OUT[sid].items() if k != 'top10_largest'}))


# GIL-hold probe: Python-side latency of a tiny workload while another thread validates (old per-ref clip vs new whole page)
def probe(target):
    lat, done = [], threading.Event()
    th = threading.Thread(target=lambda: (target(), done.set())); t0 = time.perf_counter(); th.start()
    payload = {'k%d' % i: list(range(20)) for i in range(200)}
    while not done.is_set():
        t = time.perf_counter(); json.dumps(payload); time.sleep(0.001); lat.append((time.perf_counter() - t) * 1000)
    th.join()
    lat.sort()
    return {'wall_ms': round((time.perf_counter() - t0) * 1000), 'n': len(lat), 'p50_ms': round(lat[len(lat) // 2], 2),
            'p95_ms': round(lat[int(len(lat) * .95)], 2), 'max_ms': round(lat[-1], 2)}


for sid in ('jee-main-pyq-2026-01-24-s1', 'jee-main-pyq-2026-04-08-s2'):
    f, raw, refs = paper(sid)
    sub = refs[:60]
    with tejas_core.validate_pdf(raw, reviewed_large_pages=True) as doc:
        old = probe(lambda: [tejas_core._render_crop_png(raw, r, .3, reviewed_large_pages=True, _document=doc) for r in sub])
    with tejas_core.validate_pdf(raw, reviewed_large_pages=True) as doc:
        new = probe(lambda: tejas_core.validate_crop_pages(doc, refs))
    OUT['gil_probe_' + sid] = {'old_60refs_clip': old, 'new_all_refs_wholepage': new}
    print('gil', sid, json.dumps(OUT['gil_probe_' + sid]))
open('/app/test_reports/iter166_png6_cpu_gil_microbench.json', 'w').write(json.dumps(OUT, indent=1))
