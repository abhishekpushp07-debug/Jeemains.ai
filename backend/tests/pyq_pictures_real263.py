"""TEST-ONLY iteration 263, no database: the preview's REAL storage does not give back a PYQ original (the fault the app saw on live);
the website now cuts the picture from the kept copy in the repository. Read only: nothing is written anywhere.
Run: cd /app/backend && bash /root/p2/solo.sh python -u tests/pyq_pictures_real263.py
"""
import hashlib, sys, time
from pathlib import Path
from dotenv import load_dotenv
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
load_dotenv(Path(__file__).resolve().parents[1] / '.env')
import tejas_storage as S  # noqa: E402
from tejas import derivatives as D  # noqa: E402

DRIVE = '1-0YnLVIrzU-vARvQ_KNEWilYFai1wRsr'
REF = {'file_id': 'jee-pyq-source-1ca9b573decd04c6d188d37b', 'page': 1, 'rect': [20.825, 167.873, 297.5, 227.968]}
RESULTS = []


def check(name, ok, info=''):
    RESULTS.append((name, bool(ok), info))


sha = hashlib.sha256((D.PYQ_COPIES / f'{DRIVE}.pdf').read_bytes()).hexdigest()
src = {'id': REF['file_id'], 'path': f'tejas/jee-pyq/originals/{sha}.pdf', 'sha256': sha, 'source_collection': 'jee-pyq-written', 'source_drive_id': DRIVE}
t = time.time()
try:
    S.request('GET', src['path']); seen = 'read'
except S.StorageError as exc:
    seen = str(exc)
check('real storage does not give the original back (the fault, reproduced)', seen != 'read', seen)
t = time.time()
png = D.render_crop(src, REF)
first = time.time() - t
check('picture cut from the kept copy, PNG', png[:8] == b'\x89PNG\r\n\x1a\n' and len(png) > 1000, f'{len(png)} bytes in {first:.1f} s')
D._cache.data.clear(); D._cache.size = 0
t = time.time(); D.render_crop(src, {**REF, 'page': 2}); second = time.time() - t
check('next picture of the paper without waiting for storage (< 2 s)', second < 2, f'{second:.2f} s')
for r in RESULTS: print('PASS' if r[1] else 'FAIL', r[0], r[2])
ok = sum(1 for r in RESULTS if r[1]); print(f'TOTAL {len(RESULTS)} PASS {ok} FAIL {len(RESULTS) - ok}')
