"""TEST-ONLY iter168: side-by-side 163/164/166/166r2/168 for key bench steps (bench_iter163_perf_baseline.py JSONs)."""
import json
P = '/app/test_reports/'
F = {'163': 'iter163_perf_baseline.json', '164': 'iter164_perf_after.json', '166': 'iter166_perf_after.json',
     '166b': 'iter166_perf_after_run2.json', '168': 'iter168_perf_after.json'}
S = {k: json.load(open(P + v))['steps'] for k, v in F.items()}
KEYS = ('ms', 'p50_ms', 'p95_ms', 'max_ms', 'wall_ms', 'total_ms', 'preflight_ms', 'bytes', 'png_bytes_total', 'crop_render_s',
        'crop_render', 'storage_get', 'crop_geometry', 'wholepage_pixmap', 'pixmap_calls', 'series_max_ms', 'series_p95_ms', 'health_p95_ms', 'probes', 'statuses', 'status')
names = sorted(set().union(*[set(s) for s in S.values()]))
for n in names:
    print('==', n)
    for k in KEYS + tuple(sorted({kk for s in S.values() for kk in (s.get(n) or {}) if 'page' in kk or 'geom' in kk})):
        vals = [(S[i].get(n) or {}).get(k) for i in F]
        if any(v is not None for v in vals):
            print('   %-22s' % k, ' | '.join('%s=%s' % (i, v) for i, v in zip(F, vals)))
