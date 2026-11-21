"""TEST-ONLY (iteration 217, T1): Playwright helpers routing /api to the master bridge (tests/master_bridge181.py on 127.0.0.1:8770)."""
import json, os, subprocess
B = json.load(open('/tmp/uibridge/bridge.json'))
BASE = [l.split('=', 1)[1].strip() for l in open('/app/frontend/.env') if l.startswith('REACT_APP_BACKEND_URL')][0].rstrip('/')
API = 'http://127.0.0.1:8770'
DBN = [l for l in open('/tmp/bridge181.log') if l.startswith('READY')][-1].split()[1]
SS = os.environ.get('SS_DIR', '/app/.screenshots/ui217'); os.makedirs(SS, exist_ok=True)
R = []


def ok(name, cond, detail=''):
    R.append((name, bool(cond))); print(('PASS ' if cond else 'FAIL ') + name + ('' if cond else ' :: ' + str(detail)[:600]), flush=True)


def mongo(js):
    return subprocess.run(['mongosh', '--quiet', DBN, '--eval', js], capture_output=True, text=True).stdout.strip()


async def open_as(pw, role, w=1920, h=900, extra=None):
    br = await pw.chromium.launch()
    ctx = await br.new_context(viewport={'width': w, 'height': h})
    cookie = '; '.join(f'{k}={v}' for k, v in B[role].items())
    page = await ctx.new_page(); bad, logs = [], []

    async def handler(route):
        req = route.request
        if extra:
            done = await extra(route, req)
            if done:
                return
        hd = {k: v for k, v in req.headers.items() if k.lower() not in ('cookie', 'host', 'origin', 'referer', 'content-length')}
        hd['cookie'] = cookie
        try:
            r = await route.fetch(url=req.url.replace(BASE, API), headers=hd)
            rh = {k: v for k, v in r.headers.items() if k.lower() not in ('set-cookie', 'content-encoding', 'content-length')}
            await route.fulfill(status=r.status, headers=rh, body=await r.body())
        except Exception as e:
            print('route error', e); await route.abort()
    await ctx.route('**/api/**', handler)
    page.on('response', lambda r: bad.append((r.status, r.request.method, r.url.split('/api')[-1][:160])) if '/api/' in r.url and r.status >= 400 else None)
    page.on('pageerror', lambda e: logs.append(str(e)[:200]))
    return br, page, bad, logs
