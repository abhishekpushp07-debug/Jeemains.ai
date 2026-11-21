"""TEST-ONLY (iteration 216): ask the bridge (:8772) for every page of the boxed chapter's proof view as owner,
sequentially and then 6 at once (as the desktop proof view does), and print status + 422 reason."""
import json, requests, concurrent.futures as cf
B = json.load(open('/tmp/uibridge210/bridge.json')); F = B['f']; API = 'http://127.0.0.1:8772'
s = requests.Session(); s.cookies.update(B['owner'])
bid, mid = F['boxed']
m = s.get(f'{API}/api/admin/books/{bid}/mocks/{mid}').json()
m = m.get('data', m)
pages = sorted({q['cut']['region']['page'] for q in m['questions'] if (q.get('cut') or {}).get('region')} | {p['page'] for q in m['questions'] for p in (q.get('cut') or {}).get('parts', [])})
print('pages', pages, 'q1 cut page', (m['questions'][0].get('cut') or {}).get('region', {}).get('page'))
def get(p):
    r = s.get(f'{API}/api/admin/books/{bid}/mocks/{mid}/page/{p}')
    return p, r.status_code, (r.text[:200] if r.status_code != 200 else len(r.content))
for p in pages:
    print('seq', get(p))
with cf.ThreadPoolExecutor(8) as ex:
    for res in ex.map(get, pages * 2):
        print('par', res)
