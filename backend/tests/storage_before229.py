"""TEST-ONLY iteration 229: the stand-in Supabase shows the live fault with the storage code that was live on 24 Nov
(taken from git, commit before the Pocket 1 work), and the same call with today's code saves the file. No network, no database.
Run: cd /app/backend && python tests/storage_before229.py
"""
import importlib.util, os, subprocess, sys, tempfile
from pathlib import Path
from unittest import mock
import httpx

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT)); sys.path.insert(0, str(ROOT / 'tests'))
os.environ.update(SUPABASE_URL='https://abcdefghijklmnopqrst.supabase.co', SUPABASE_SECRET_KEY='sb_secret_test', FRONTEND_URL='https://preview-x.example.com')
os.environ.pop('SUPABASE_BUCKET', None)
from fake_supabase229 import FakeSupabase  # noqa: E402

LIVE_CODE = '9febed8~1:backend/tejas_storage.py'
B, KEY = 'jeelive-preview-x-example-com', 'jeelive/books/b1/original.pdf'
RESULTS = []


def check(name, ok, detail=''):
    RESULTS.append(bool(ok)); print(('PASS ' if ok else 'FAIL ') + name + ('' if ok else ' :: ' + str(detail)[:400]), flush=True)


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, str(path))
    module = importlib.util.module_from_spec(spec); spec.loader.exec_module(module)
    return module


def three_tries(S, already, new):
    """The same PDF sent three times (as the waiting job does) to a path that already holds a file."""
    sb = FakeSupabase(S.TUS_CHUNK); sb.objects[B + '/' + KEY] = already
    client = httpx.Client(transport=httpx.MockTransport(sb)); S._client = lambda: client
    place, out = None, []
    for _ in range(3):
        S.STATE['down_until'] = 0.0
        seen = []
        try:
            out.append(S.put_object(KEY, new, 'application/pdf', place, seen.append))
        except S.StorageError as exc:
            out.append(exc)
        place = seen[-1] if seen else place
    return sb, out


def main():
    src = subprocess.run(['git', '-C', str(ROOT.parent), 'show', LIVE_CODE], capture_output=True, text=True)
    if src.returncode:
        print('SKIP: the 24 Nov code is not in this git history'); return
    check('this is the code the live report quotes (409 counted as "ask again")', 'r.status_code not in TRANSIENT + (409,)' in src.stdout)
    with tempfile.TemporaryDirectory() as d:
        (Path(d) / 'old_storage.py').write_text(src.stdout)
        old = load('old229', Path(d) / 'old_storage.py')
    new = load('new229', ROOT / 'tejas_storage.py')
    pdf, other = os.urandom(20 * 1024 * 1024 + 321), os.urandom(20 * 1024 * 1024 + 321)
    with mock.patch.object(old.time, 'sleep', lambda s: None), mock.patch.object(new.time, 'sleep', lambda s: None):
        for label, already in (('the same PDF', pdf), ('another file', other)):
            sb, out = three_tries(old, already, pdf)
            check(f'24 Nov code, {label} already at the path: all 3 tries wait with "stopped at 0 ... (409)", exactly the live log line',
                  all(isinstance(x, old.StorageWaiting) and f'stopped at 0 of {len(pdf)} bytes (409)' in str(x) for x in out), [str(x)[-90:] for x in out])
            check('...and nothing ever reaches Supabase (it would wait for ever)', sb.objects[B + '/' + KEY] == already and sb.pieces() >= 3, sb.pieces())
            sb, out = three_tries(new, already, pdf)
            check(f"today's code, {label} already at the path: saved on the first try", all(x == f'sb://{B}/{KEY}' for x in out) and sb.objects[B + '/' + KEY] == pdf, [str(x)[-90:] for x in out])
            check('...the same PDF is recognised and not sent again' if already is pdf else '...the other file is replaced, each piece sent once', sb.pieces() == (0 if already is pdf else 4), sb.pieces())
    print(f'TOTAL {len(RESULTS)} PASS {sum(RESULTS)} FAIL {len(RESULTS) - sum(RESULTS)}')


if __name__ == '__main__':
    main()
