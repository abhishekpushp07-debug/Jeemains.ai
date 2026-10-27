"""TEST-ONLY: compare BEFORE (iter163) vs AFTER perf baseline JSON produced by bench_iter163_perf_baseline.py.
Usage: python compare_perf163.py /app/test_reports/iter163_perf_baseline.json /app/test_reports/iterNNN_perf_after.json
AFTER run: PERF_OUT=/app/test_reports/iterNNN_perf_after.json python -m pytest bench_iter163_perf_baseline.py -p no:cacheprovider -q -n0 -s
"""
import json, sys

KEYS = ('ms', 'p50_ms', 'p95_ms', 'max_ms', 'total_s', 'wall_ms', 'preflight_ms', 'bytes', 'png_bytes_total', 'db_cmds', 'db_cmds_per_call',
        'storage_get', 'storage_bytes', 'crop_render', 'crop_render_s', 'pdf_open', 'series_p50_ms', 'series_p95_ms', 'health_p95_ms')


def flat(step):
    out = {k: step[k] for k in KEYS if k in step}
    if 'final' in step:
        out['polls'] = step.get('polls')
    return out


def main(a, b):
    A, B = json.load(open(a))['steps'], json.load(open(b))['steps']
    for name in sorted(set(A) | set(B)):
        fa, fb = flat(A.get(name, {})), flat(B.get(name, {}))
        rows = []
        for k in sorted(set(fa) | set(fb)):
            va, vb = fa.get(k), fb.get(k)
            if va != vb:
                ratio = f' x{(vb / va):.2f}' if isinstance(va, (int, float)) and isinstance(vb, (int, float)) and va else ''
                rows.append(f'{k}: {va} -> {vb}{ratio}')
        print(f'{name}: ' + ('; '.join(rows) if rows else 'unchanged'))


if __name__ == '__main__':
    main(sys.argv[1], sys.argv[2])
