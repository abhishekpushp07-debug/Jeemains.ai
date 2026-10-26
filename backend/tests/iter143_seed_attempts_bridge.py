"""TEST-ONLY iter143: seeds attempts on the isolated bridge (127.0.0.1:8791, DB tejas_isolated_iter134) via real API.
Creates: 1 submitted attempt (results UI) + 1 active attempt (player UI) for synthetic student 's'. Never touches the customer DB."""
import json, uuid, time, httpx
B = 'http://127.0.0.1:8791'; S = {'x-test-user': 's'}
c = httpx.Client(base_url=B, headers=S, timeout=60)
assert c.get('/__test/state').json()['db'] == 'tejas_isolated_iter134'
cat = c.get('/api/pyq/jee-main').json()
cat = cat.get('data', cat)
ids = []
def walk(o):
    if isinstance(o, dict):
        if o.get('id', '').startswith('') and 'pyq_date' in o or ('set_id' in o): ids.append(o.get('id') or o.get('set_id'))
        for v in o.values(): walk(v)
    elif isinstance(o, list):
        for v in o: walk(v)
ids=[i['id'] for i in cat['items']]
ids = [i for i in dict.fromkeys(ids) if i]
print('papers', len(ids))
def start(pid):
    assert c.post(f'/api/sets/{pid}/preflight', json={'test_response': 'ok'}).status_code == 200
    r = c.post(f'/api/sets/{pid}/start', json={'start_key': 'TEST_K143_' + uuid.uuid4().hex, 'device_checked': True})
    assert r.status_code == 200, r.text
    d = r.json(); return d.get('data', d)
a = start(ids[0]); aid = a['id'] if 'id' in a else a['attempt']['id']
att = c.get(f'/api/attempts/{aid}').json(); att = att.get('data', att)
qs = att['questions']
for q in qs[:6]:
    v = 'A' if q['type'] == 'mcq' else '5'
    c.put(f'/api/attempts/{aid}/answers/{q["id"]}', json={'value': v, 'revision': 1, 'request_id': 'TEST_R143_' + uuid.uuid4().hex})
print('submit', c.post(f'/api/attempts/{aid}/submit').status_code)
for _ in range(30):
    r = c.get(f'/api/attempts/{aid}/results')
    if r.status_code == 200: break
    time.sleep(0.5)
print('results', r.status_code)
b = start(ids[1]); bid = b['id'] if 'id' in b else b['attempt']['id']
json.dump({'submitted': aid, 'active': bid}, open('/tmp/iter143_ids.json', 'w'))
print(json.dumps({'submitted': aid, 'active': bid}))
