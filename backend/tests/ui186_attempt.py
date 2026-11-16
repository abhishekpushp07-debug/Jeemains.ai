"""TEST-ONLY: start an active attempt on the bridge typed set for Player UI checks (bridge on 127.0.0.1:8770)."""
import json, uuid, httpx
b = json.load(open('/tmp/uibridge/bridge.json'))
f = b['f']
c = httpx.Client(base_url='http://127.0.0.1:8770', cookies=b['student'], timeout=30)
sid = f['typed_set']
c.post(f'/api/sets/{sid}/preflight', json={})
r = c.post(f'/api/sets/{sid}/start', json={'start_key': 'k186-' + uuid.uuid4().hex[:12], 'device_checked': True})
print('start', r.status_code, r.text[:200])
d = r.json().get('data', r.json())
qs = d.get('questions') or c.get(f"/api/attempts/{d['id']}").json().get('data', {}).get('questions', [])
for q in qs:
    print(q.get('id'), q.get('number'), q.get('render_mode'), list((q.get('options') or {})), q.get('typed_options'))
b['f']['ui_attempt'] = d.get('id')
json.dump(b, open('/tmp/uibridge/bridge.json', 'w'))
print('attempt', d.get('id'))
