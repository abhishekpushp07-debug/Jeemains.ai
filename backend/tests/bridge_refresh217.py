"""TEST-ONLY (iteration 217): refresh expired bridge cookies in place. Run: python tests/bridge_refresh217.py /tmp/uibridge/bridge.json 8770 owner [role...]"""
import json, sys, requests
path, port, roles = sys.argv[1], sys.argv[2], sys.argv[3:]
B = json.load(open(path))
for role in roles:
    r = requests.post(f'http://127.0.0.1:{port}/api/auth/refresh', headers={'Cookie': '; '.join(f'{k}={v}' for k, v in B[role].items()),
                      'Origin': [l.split('=', 1)[1].strip() for l in open('/app/frontend/.env') if l.startswith('REACT_APP_BACKEND_URL')][0]})
    print(role, r.status_code)
    if r.status_code == 200:
        B[role].update({k: v for k, v in r.cookies.items()})
json.dump(B, open(path, 'w'))
