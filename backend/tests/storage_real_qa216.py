# Real Supabase (preview project) round-trip, privacy, probe, and in-process outage -> Emergent failover. Only TEST_qa216/ paths; cleans Supabase.
import os, sys, time
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from dotenv import load_dotenv
load_dotenv(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), '.env'))
import tejas_storage as S

R = []
def chk(name, ok, extra=''):
    R.append(ok); print(('PASS ' if ok else 'FAIL ') + name + (f'  [{extra}]' if extra else ''))

created = []
try:
    chk('configured', S.configured())
    b = S.bucket_name(); print('bucket', b)
    small = os.urandom(3000)
    t = time.time(); ref = S.put_object('TEST_qa216/x.png', small, 'image/png'); wt = time.time() - t
    chk('small put -> sb:// ref', ref.startswith('sb://'), f'{ref} {wt:.2f}s')
    if ref.startswith('sb://'): created.append(ref.split('/', 3)[3])
    S._source_cache.remove(ref)
    t = time.time(); got = S.get_object(ref)
    chk('small get identical', got == small, f'{time.time()-t:.2f}s')
    big = os.urandom(15 * 1024 * 1024)
    t = time.time(); ref2 = S.put_object('TEST_qa216/big.pdf', big, 'application/pdf'); wt = time.time() - t
    chk('15MB put -> sb://', ref2.startswith('sb://'), f'{wt:.2f}s')
    if ref2.startswith('sb://'): created.append(ref2.split('/', 3)[3])
    S._source_cache.remove(ref2)
    t = time.time(); got2 = S.get_object(ref2)
    chk('15MB get identical', got2 == big, f'{time.time()-t:.2f}s')
    r = S._call('GET', f'{S.project_url()}/storage/v1/bucket/{b}')
    chk('bucket private', r.status_code == 200 and r.json().get('public') is False, f'{r.status_code}')
    # anonymous public url must not serve
    import httpx
    pu = httpx.get(f'{S.project_url()}/storage/v1/object/public/{b}/TEST_qa216/x.png', timeout=20)
    chk('public url refuses object', pu.status_code != 200, str(pu.status_code))
    p = S.probe()
    chk('probe supabase ok', p['supabase'].get('ok'), str({k: v for k, v in p['supabase'].items() if k != 'error'}))
    chk('probe emergent ok', p['emergent'].get('ok'), str(p['emergent']))
    # outage
    good = os.environ['SUPABASE_SECRET_KEY']
    f0 = S.STATE['failovers']
    os.environ['SUPABASE_SECRET_KEY'] = 'sb_secret_invalid'
    S.STATE['bucket'] = None
    data3 = os.urandom(2000)
    t = time.time(); ref3 = S.put_object('TEST_qa216/outage.png', data3, 'image/png'); wt = time.time() - t
    chk('outage put -> plain Emergent path', not ref3.startswith('sb://'), f'{ref3} {wt:.2f}s')
    S._source_cache.remove(ref3)
    chk('outage get identical', S.get_object(ref3) == data3)
    chk('failovers incremented', S.STATE['failovers'] > f0, f"{f0}->{S.STATE['failovers']} reason={S.STATE['last_failover'] and S.STATE['last_failover']['reason'][:80]}")
    chk('breaker resting', not S.supabase_on())
    os.environ['SUPABASE_SECRET_KEY'] = good
    S.STATE['down_until'] = 0; S.STATE['strikes'] = 0
finally:
    os.environ['SUPABASE_SECRET_KEY'] = good if 'good' in dir() else os.environ['SUPABASE_SECRET_KEY']
    if created:
        r = S._call('DELETE', f'{S.project_url()}/storage/v1/object/{S.bucket_name()}', {'Content-Type': 'application/json'}, json={'prefixes': created})
        print('cleanup', r.status_code, len(r.json()) if r.status_code == 200 else r.text[:100])
        r = S._call('POST', f'{S.project_url()}/storage/v1/object/list/{S.bucket_name()}', {'Content-Type': 'application/json'}, json={'prefix': 'TEST_qa216/', 'limit': 100})
        chk('cleanup verified (no TEST_qa216 objects left)', r.status_code == 200 and len(r.json()) == 0, str(r.json())[:120])
print(f'TOTAL {len(R)} PASS {sum(R)} FAIL {len(R)-sum(R)}')
