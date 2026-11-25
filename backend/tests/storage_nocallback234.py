"""TEST-ONLY iteration 234 (code-review finding, medium): a big file sent by a caller that keeps no place between tries
(chapter book, Studio import, report PDF). When Supabase is up but returns this file on BOTH big-file routes, it must become
"stuck" (StorageStuck) in that one call, not wait for ever as "this file only". Supabase faked at the wire, no network, no DB.
Run: cd /app/backend && python tests/storage_nocallback234.py
"""
import os, sys, time, types
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent)); sys.path.insert(0, str(Path(__file__).resolve().parent))
os.environ.update(SUPABASE_URL='https://abcdefghijklmnopqrst.supabase.co', SUPABASE_SECRET_KEY='sb_secret_test')
import httpx  # noqa: E402
import tejas_storage as S  # noqa: E402
from fake_supabase229 import FakeSupabase  # noqa: E402

RESULTS = []
KEY = 'TEST_p234/report.pdf'


def check(name, ok, detail=''):
    RESULTS.append(bool(ok)); print(('PASS ' if ok else 'FAIL ') + name + ('' if ok else ' :: ' + str(detail)[:400]), flush=True)


def fresh():
    sb = FakeSupabase(S.TUS_CHUNK)
    client = httpx.Client(transport=httpx.MockTransport(sb))
    S._client = lambda: client
    S.STATE.update(down_until=0.0, strikes=0, last_error='', auth=None, bucket=None, failovers=0, last_failover=None, backup_since=None)
    return sb


def send(data, *more):
    try:
        return S.put_object(KEY, data, 'application/pdf', *more)
    except S.StorageError as exc:
        return exc


S.time = types.SimpleNamespace(time=time.time, sleep=lambda s: None)
big = os.urandom(S.TUS_CHUNK * 2 + 234)

sb = fresh(); sb.tus_down = True; sb.one_request_code = 400
out = send(big)
check('no place kept, both big-file routes return the file: it is STUCK in this one call, with the code and the 15-minute step',
      isinstance(out, S.StorageStuck) and out.scope == 'stuck' and '15 minute' in out.step, (type(out).__name__, getattr(out, 'scope', ''), getattr(out, 'step', '')))
check('...Supabase is not rested for anyone and nothing was half-saved', S.supabase_on() and S.STATE['strikes'] == 0 and not sb.objects, (S.STATE['strikes'], list(sb.objects)))

sb = fresh(); sb.patch_code = 400; sb.one_request_code = 400; seen = []
out = send(big, None, seen.append)
check('a caller that DOES keep the place is unchanged: its first try waits as "this file only"', isinstance(out, S.StorageWaiting) and not isinstance(out, S.StorageStuck) and out.scope == 'file', (type(out).__name__, getattr(out, 'scope', '')))

sb = fresh(); sb.tus_down = True; sb.one_request_code = 503
out = send(big)
check('no place kept, but the last answer is Supabase\'s own fault (503): it WAITS for Supabase, it is not called stuck', isinstance(out, S.StorageWaiting) and not isinstance(out, S.StorageStuck) and out.scope == 'away',
      (type(out).__name__, getattr(out, 'scope', '')))

sb = fresh(); sb.down = True
out = send(big)
check('Supabase itself away: it WAITS (not stuck) and Supabase is rested', isinstance(out, S.StorageWaiting) and not isinstance(out, S.StorageStuck) and out.scope == 'away' and not S.supabase_on(), (type(out).__name__, getattr(out, 'scope', '')))

sb = fresh(); sb.tus_down = True
out = send(big)
check('piece route broken but the one-request route works: the file is saved exactly', out == f'sb://{S.bucket_name()}/{KEY}' and sb.objects.get(f'{S.bucket_name()}/{KEY}') == big, out)

sb = fresh()
out = send(big)
check('healthy Supabase: saved by the piece route', out == f'sb://{S.bucket_name()}/{KEY}' and sb.objects.get(f'{S.bucket_name()}/{KEY}') == big, out)
print(f'TOTAL {len(RESULTS)} PASS {sum(RESULTS)} FAIL {len(RESULTS) - sum(RESULTS)}')
