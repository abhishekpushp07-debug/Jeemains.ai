# Helper: start disposable attempts on the analysis bridge (theme QA iteration 198)
import json, uuid, requests
B = 'http://127.0.0.1:8773'
d = json.load(open('/tmp/uibridge196/bridge.json'))
origin = open('/app/frontend/.env').read().split('REACT_APP_BACKEND_URL=')[1].split()[0]
out = {}
for who, gr in (('old', False), ('friend', True)):
    r = requests.post(f"{B}/api/sets/{d['set']}/start", json={'start_key': str(uuid.uuid4()), 'get_ready': gr},
                      cookies=d[who], headers={'Origin': origin})
    print(who, r.status_code, r.text[:200])
    try:
        out[who] = r.json()['data']['id']
    except Exception:
        pass
json.dump(out, open('/tmp/uibridge196/theme198.json', 'w'))
print(out)
