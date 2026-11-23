"""TEST-ONLY iteration 224 QA: storage health/retry/machine APIs on the isolated bridge (127.0.0.1:8774). Supabase must be DOWN (flag file present).
Run: cd /app/backend && python tests/storage_wait_api_qa224.py
"""
import json, os, requests

API = 'http://127.0.0.1:' + os.environ.get('BRIDGE_PORT', '8774')
B = json.load(open('/tmp/uibridge224/bridge.json'))
R = []


def say(n, ok, d=''):
    R.append(bool(ok)); print(('PASS ' if ok else 'FAIL ') + n + ('' if ok else ' :: ' + str(d)[:500]))


def s(role):
    x = requests.Session(); x.cookies.update(B[role]); return x


o, rv, anon = s('owner'), s('reviewer'), requests.Session()
h = o.get(API + '/api/admin/storage/health').json()['data']; print('health', json.dumps(h)[:600])
say('health mode waiting while down', h.get('mode') == 'waiting', h.get('mode'))
say('no emergent-backup mode text', 'backup' not in str(h.get('mode')), h)
m = o.get(API + '/api/admin/machine/status').json()['data']; print('machine keys', list(m.keys()))
w = m.get('storage_waiting')
say('machine storage_waiting present', w is not None, m)
books = w if isinstance(w, list) else (w or {}).get('books', [])
say('waiting book listed with waiting_minutes', any(b.get('id') == B['book'] and 'waiting_minutes' in b for b in books), w)
say('storage_waiting_jobs >= 1', (m.get('storage_waiting_jobs') or 0) >= 1, m.get('storage_waiting_jobs'))
stuck = json.dumps(m.get('stuck', m.get('stuck_books', [])))
say('waiting book NOT in stuck', B['book'] not in stuck, stuck[:300])
r = rv.post(API + '/api/admin/storage/retry'); say('reviewer retry -> 403', r.status_code == 403, (r.status_code, r.text[:200]))
r = anon.post(API + '/api/admin/storage/retry'); say('anon retry -> 401/403', r.status_code in (401, 403), r.status_code)
r = o.post(API + '/api/admin/storage/retry'); print('owner retry', r.status_code, r.text[:300])
say('owner retry 200 with mode + woke', r.status_code == 200 and 'mode' in r.json()['data'] and 'woke' in r.json()['data'], r.text[:200])
say('owner retry while down: mode waiting, woke 0', r.ok and r.json()['data'].get('mode') == 'waiting' and r.json()['data'].get('woke') == 0, r.text[:200])
print(f'TOTAL {len(R)} PASS {sum(R)} FAIL {len(R) - sum(R)}')
