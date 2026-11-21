# GET /api/admin/storage/health via isolated master bridge (127.0.0.1:8770): shape, caching, fresh throttle, auth, no secrets.
import json, os, time, requests
API = 'http://127.0.0.1:8770'
B = json.load(open('/tmp/uibridge/bridge.json'))
R = []
def chk(n, ok, extra=''):
    R.append(ok); print(('PASS ' if ok else 'FAIL ') + n + (f'  [{extra}]' if extra else ''))
def get(role=None, q='', cookies=None):
    c = cookies if cookies is not None else (B[role] if role else {})
    return requests.get(API + '/api/admin/storage/health' + q, cookies=c, headers={'Origin': API}, timeout=60)

r = get('owner'); d = r.json().get('data', {}) if r.ok else {}
chk('owner 200', r.status_code == 200, r.status_code)
for k in ('mode', 'checked_at', 'supabase', 'emergent', 'writes', 'failovers', 'last_failover'):
    chk(f'key {k}', k in d)
chk('mode valid', d.get('mode') in ('supabase', 'slow', 'emergent', 'down'), d.get('mode'))
chk('bridge mode is emergent (Supabase offline)', d.get('mode') == 'emergent', d.get('mode'))
for k in ('ok', 'configured', 'bucket', 'error', 'resting_until'):
    chk(f'supabase.{k}', k in d.get('supabase', {}), list(d.get('supabase', {}).keys()))
chk('emergent ok+times', all(k in d.get('emergent', {}) for k in ('ok', 'write_ms', 'read_ms')), d.get('emergent'))
chk('writes shape', set(d.get('writes', {})) == {'supabase', 'emergent'}, d.get('writes'))
r2 = get('owner'); chk('cached: same checked_at', r2.json()['data'].get('checked_at') == d.get('checked_at'))
r3 = get('owner', '?fresh=true'); c3 = r3.json()['data'].get('checked_at')
chk('fresh within 10s does not re-check', c3 == d.get('checked_at') or (time.time() - d['checked_at']) > 10, f'{c3} vs {d.get("checked_at")}')
time.sleep(11)
r4 = get('owner', '?fresh=true'); c4 = r4.json()['data'].get('checked_at')
chk('fresh after 10s re-checks', c4 > d.get('checked_at', 0), f'{c4} vs {d.get("checked_at")}')
r5 = get('owner', '?fresh=true'); chk('fresh again immediately -> cached', r5.json()['data'].get('checked_at') == c4)
rv = get('reviewer'); chk('reviewer (staff) 200', rv.status_code == 200, rv.status_code)
ra = get(cookies={}); chk('anonymous rejected', ra.status_code in (401, 403), ra.status_code)
rb = get(cookies={k: 'bogus' for k in B['owner']}); chk('bogus cookie rejected', rb.status_code in (401, 403), rb.status_code)
body = r.text.lower()
secrets = [v for v in (os.environ.get('SUPABASE_SECRET_KEY'), os.environ.get('EMERGENT_LLM_KEY')) if v]
chk('no secrets/keys in body', not any(s.lower() in body for s in secrets) and 'storage_key' not in body and 'sb_secret' not in body and 'eyj' not in body)
# parallel calls do not stack probes
import concurrent.futures as cf
with cf.ThreadPoolExecutor(10) as ex:
    outs = list(ex.map(lambda _: get('owner', '?fresh=true').json()['data'].get('checked_at'), range(10)))
chk('10 concurrent calls share one check', len(set(outs)) == 1, outs)
print('sample', json.dumps(d)[:600])
print(f'TOTAL {len(R)} PASS {sum(R)} FAIL {len(R)-sum(R)}')
