"""TEST-ONLY packet D on the REAL Supabase, preview bucket only. No app data, no database.
The app's own storage checks run for real: the small check (a new file name each time, read back, removed), the 7 MB big-file test
by the real piece route (read back, removed), and the sweep of a check file left behind. Only this app's own check files are made
and removed; the folder is listed before and after. Run: cd /app/backend && python tests/storage_badge_real236.py
"""
import os, sys, time
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from dotenv import load_dotenv
load_dotenv(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), '.env'))
import tejas_storage as S

assert 'preview' in S.bucket_name(), 'preview bucket only'
RESULTS = []
B = S._bucket()


def check(name, ok, detail=''):
    RESULTS.append(bool(ok)); print(('PASS ' if ok else 'FAIL ') + name + ('' if ok else ' :: ' + str(detail)[:400]), flush=True)


def listed():
    return sorted(n for n, _ in S.sb_list('health/')[0])


def settled(want):
    """The running preview server may be checking at the same moment: its own check file is gone a moment later."""
    for _ in range(6):
        if listed() == want:
            return True
        time.sleep(2)
    return False


before = listed()
print('folder before:', before, flush=True)
outs = [S.probe() for _ in range(4)]
check('1. four checks on the real Supabase: all write and read back, never "Read back different bytes"', all(o['supabase']['ok'] and not o['supabase']['error'] for o in outs), [o['supabase'] for o in outs])
check('2. Emergent answers too; both give real timings', all(o['emergent']['ok'] for o in outs) and all(o['supabase']['write_ms'] > 0 and o['supabase']['read_ms'] > 0 for o in outs), [o['emergent'] for o in outs])
print('   Supabase ms (write+read):', [o['supabase']['write_ms'] + o['supabase']['read_ms'] for o in outs], ' Emergent ms:', [o['emergent']['write_ms'] + o['emergent']['read_ms'] for o in outs], flush=True)
check('3. no check file is left in Supabase: the folder lists exactly what it listed before', settled(before), (before, listed()))
big = S.probe_big()
print('   big-file test:', {k: big.get(k) for k in ('ok', 'ms', 'size', 'error', 'code', 'scope')}, flush=True)
check('4. the 7 MB big-file test goes by the real piece route, is read back whole and compared', big['ok'] and big['size'] == S.BIG_TEST and big['ms'] > 0, big)
check('5. ...and its test file is removed', settled(before), (before, listed()))
check('6. nothing here rested Supabase', S.supabase_on() and S.STATE['strikes'] == 0, S.STATE['strikes'])
left = f'health/check-{int(time.time()) - 7200}-{os.urandom(6).hex()}.bin'
S.sb_put(left, b'TEST leftover check file', 'application/octet-stream')
there = left[len('health/'):] in listed()
swept = S.sweep_checks()
check('7. a check file left behind two hours ago is swept; nothing else in that folder is touched', there and swept >= 1 and settled(before), (there, swept, listed()))
refused = 0
for names in (['health/check.bin'], ['jeelive/books/x/original.pdf'], []):
    try:
        S._drop_checks(B, names)
    except ValueError:
        refused += 1
check('8. the check refuses to remove anything that is not its own check file', refused == 3 and settled(before), refused)
kinds = [e['kind'] + (':' + e.get('store', e.get('how', ''))) for e in S.EVENTS]
check('9. every check was noted for the shared record (small checks of both stores, the big test)', kinds.count('check:supabase') == 4 and kinds.count('check:emergent') == 4 and kinds.count('big:test') == 1, kinds)
print('folder after:', listed(), flush=True)
print(f'TOTAL {len(RESULTS)} PASS {sum(RESULTS)} FAIL {len(RESULTS) - sum(RESULTS)}')
