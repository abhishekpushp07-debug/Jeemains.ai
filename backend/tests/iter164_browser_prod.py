"""TEST-ONLY iteration 164 browser E2E against the PRODUCTION build (/tmp/fe164_build, yarn build) served via Playwright
request interception on the preview origin; /api/** forwarded to the isolated bridge 127.0.0.1:8797 (disposable DB).
Third-party scripts (emergent/posthog) are ABORTED (MOCKED out) to keep first-party byte counts deterministic.
Run: python /app/backend/tests/iter164_browser_prod.py   (after iso_bridge_perf163.py prints READY)
"""
import asyncio, json, mimetypes, os, re, sys, time
from http.cookies import SimpleCookie
from pathlib import Path
import httpx
from playwright.async_api import async_playwright

ORIGIN = 'https://tejas-route2--1yaz6hh9.preview.emergentagent.com'
BUILD = Path('/tmp/fe164_build'); BRIDGE = 'http://127.0.0.1:8797'
CREDS = json.load(open('/tmp/perf163_creds.json'))
SHOTS = Path('/app/test_reports/iter164_shots'); SHOTS.mkdir(exist_ok=True)
OUT = {'method': 'prod build via request interception; Chromium headless unthrottled in preview pod; API = isolated in-process bridge; third-party aborted', 'pages': {}, 'flow': {}, 'checks': {}}
http = httpx.AsyncClient(base_url=BRIDGE, timeout=120)
jar = {}
LOG = []


def ok(name, cond, detail=''):
    OUT['checks'][name] = {'pass': bool(cond), 'detail': detail}
    print(('PASS ' if cond else 'FAIL ') + name, detail)


async def handler(route):
    req = route.request; url = req.url
    if not url.startswith(ORIGIN):
        return await route.abort()
    p = url[len(ORIGIN):]
    if p.startswith('/api/'):
        h = {k: v for k, v in (await req.all_headers()).items() if k.lower() not in ('host', 'cookie', 'content-length', 'accept-encoding')}
        h['origin'] = ORIGIN
        if jar: h['cookie'] = '; '.join(f'{k}={v}' for k, v in jar.items())
        r = await http.request(req.method, p, headers=h, content=req.post_data_buffer)
        for sc in r.headers.get_list('set-cookie'):
            c = SimpleCookie(); c.load(sc)
            for k, m in c.items():
                if m['max-age'] == '0' or (m['expires'] and '1970' in m['expires']) or m.value in ('', '""'): jar.pop(k, None)
                else: jar[k] = m.value
        hdr = {k: v for k, v in r.headers.items() if k.lower() not in ('set-cookie', 'content-encoding', 'content-length', 'transfer-encoding')}
        LOG.append((req.method, p.split('?')[0], r.status_code, len(r.content)))
        return await route.fulfill(status=r.status_code, headers=hdr, body=r.content)
    path = p.split('?')[0]
    f = BUILD / path.lstrip('/')
    if not f.is_file(): f = BUILD / 'index.html'
    ct = mimetypes.guess_type(str(f))[0] or 'application/octet-stream'
    cc = 'public, max-age=31536000, immutable' if '/static/' in path else 'no-cache'
    await route.fulfill(status=200, body=f.read_bytes(), headers={'content-type': ct, 'cache-control': cc})


CLS_JS = """() => new Promise(r => { let v = 0; new PerformanceObserver(l => { for (const e of l.getEntries()) if (!e.hadRecentInput) v += e.value; }).observe({type: 'layout-shift', buffered: true}); setTimeout(() => r(v), 300); })"""
METRICS_JS = """() => ({overflowX: document.documentElement.scrollWidth - document.documentElement.clientWidth,
  fonts: [...document.fonts].filter(f => f.status === 'loaded').map(f => f.family + ' ' + f.weight),
  preloads: [...document.querySelectorAll('link[rel=preload]')].map(l => l.href.split('/').pop()),
  googleCss: [...document.querySelectorAll('link')].some(l => /fonts.googleapis/.test(l.href)),
  bodyFont: getComputedStyle(document.body).fontFamily, ls: Object.keys(localStorage), fcp: (performance.getEntriesByName('first-contentful-paint')[0] || {}).startTime})"""


async def page_metrics(ctx, label, url):
    pg = await ctx.new_page(); reqs = []
    pg.on('requestfinished', lambda r: reqs.append(r))
    await pg.goto(ORIGIN + url, wait_until='networkidle'); await pg.wait_for_timeout(600)
    m = await pg.evaluate(METRICS_JS); m['cls'] = round(await pg.evaluate(CLS_JS), 4)
    sizes = []
    for r in reqs:
        try: s = await r.sizes(); sizes.append((r.url[len(ORIGIN):].split('?')[0], s['responseBodySize']))
        except Exception: pass
    names = [n for n, _ in sizes]
    m.update({'requests': len(sizes), 'body_bytes': sum(b for _, b in sizes), 'duplicates': sorted({n for n in names if names.count(n) > 1}),
              'woff2': [n.split('/')[-1] for n in names if n.endswith('.woff2')]})
    await pg.screenshot(path=str(SHOTS / f'{label.replace(" ", "_").replace("/", "")}.jpeg'), quality=40, type='jpeg')
    OUT['pages'][label] = m; print(label, json.dumps(m)[:600])
    await pg.close(); return m


def api_count(pat, since=0):
    return sum(1 for x in LOG[since:] if re.search(pat, x[1]))


async def main():
    async with async_playwright() as pw:
        b = await pw.chromium.launch(executable_path='/pw-browsers/chromium_headless_shell-1208/chrome-linux/headless_shell')
        for vp, (w, h) in (('desktop1920x800', (1920, 800)), ('mobile390x844', (390, 844))):
            ctx = await b.new_context(viewport={'width': w, 'height': h}); await ctx.route('**/*', handler)
            for u in ('/', '/login'):
                await page_metrics(ctx, f'{vp} {u} cold', u)
            await ctx.close()
        for k, m in OUT['pages'].items():
            ok(f'{k} no overflow', m['overflowX'] <= 0, m['overflowX'])
            ok(f'{k} no google Inter css', not m['googleCss'])
            ok(f'{k} figtree preloads 400/700', sorted(re.sub(r'\..*', '', x) for x in m['preloads']) == ['figtree-latin-400-normal', 'figtree-latin-700-normal'], m['preloads'])
            ok(f'{k} no duplicate requests', not m['duplicates'], m['duplicates'])
        # ---------- real isolated flow (desktop) ----------
        for vp, (w, h) in (('desktop1920x800', (1920, 800)), ('mobile390x844', (390, 844))):
            jar.clear()
            ctx = await b.new_context(viewport={'width': w, 'height': h}); await ctx.route('**/*', handler)
            pg = await ctx.new_page(); errs = []; pg.on('pageerror', lambda e: errs.append(str(e)))
            await pg.goto(ORIGIN + '/login', wait_until='networkidle')
            await pg.fill('[data-testid="student-login-phone-input"]', CREDS['phone']); await pg.fill('#student-pin-input', CREDS['pin'])
            await pg.click('[data-testid="student-login-continue-button"]'); await pg.wait_for_timeout(1500)
            ok(f'{vp} login', 'tejas' in ' '.join(jar) or len(jar) > 0, list(jar))
            if vp.startswith('mobile'):
                # resume existing attempt from desktop flow isn't needed; just check results+player on mobile using new start of April paper
                sid = 'jee-main-pyq-2026-04-08-s2'
            else:
                sid = 'jee-main-pyq-2026-01-24-s1'
            await pg.goto(ORIGIN + '/sets/' + sid, wait_until='networkidle')
            await pg.click('[data-testid="preflight-run-check"]')
            t0 = time.perf_counter()
            await pg.wait_for_selector('[data-testid="preflight-check-success"]', timeout=90000)
            OUT['flow'][vp + ' preflight_s'] = round(time.perf_counter() - t0, 2)
            await pg.click('[data-testid="preflight-acknowledge"]')
            mark = len(LOG); t0 = time.perf_counter()
            await pg.click('[data-testid="set-preflight-start-button"]')
            await pg.wait_for_url('**/attempts/**', timeout=20000)
            aid = pg.url.split('/attempts/')[1].split('?')[0]
            img = pg.locator('.source-image img, .source-image canvas').first
            await img.wait_for(timeout=30000)
            OUT['flow'][vp + ' start_to_first_image_s'] = round(time.perf_counter() - t0, 2)
            await pg.wait_for_timeout(1500)
            gets = api_count(rf'^/api/attempts/{aid}$', mark)
            ok(f'{vp} start handoff no extra GET', gets == 0, gets)
            pre_sol = api_count(r'/asset/solution|/solution', mark)
            await pg.screenshot(path=str(SHOTS / f'{vp}_player.jpeg'), quality=40, type='jpeg')
            ov = await pg.evaluate('document.documentElement.scrollWidth-document.documentElement.clientWidth')
            ok(f'{vp} player no overflow', ov <= 0, ov)
            m2 = len(LOG)
            for _ in range(3):
                await pg.click('[data-testid="player-next"]'); await pg.wait_for_timeout(700)
            for _ in range(3):
                await pg.click('[data-testid="player-previous"]'); await pg.wait_for_timeout(500)
            assets = [x[1] for x in LOG[m2:] if '/asset/' in x[1]]
            ok(f'{vp} next/prev no duplicate asset fetch', len(assets) == len(set(assets)), f'{len(assets)} fetches, {len(set(assets))} unique')
            ok(f'{vp} no solution/bonus fetch before submit', pre_sol == 0 and not any('/solution' in a for a in assets))
            m3 = len(LOG)
            z = pg.locator('[data-testid$="-zoom-in"]').first
            if await z.count():
                await z.click(); await pg.wait_for_timeout(500)
                fs = pg.locator('[data-testid$="-fullscreen"]').first
                if await fs.count(): await fs.click(); await pg.wait_for_timeout(800)
                OUT['flow'][vp + ' zoom_level'] = await pg.locator('[data-testid="source-zoom-level"]').first.inner_text() if await pg.locator('[data-testid="source-zoom-level"]').count() else None
                await pg.screenshot(path=str(SHOTS / f'{vp}_zoom.jpeg'), quality=40, type='jpeg')
                ok(f'{vp} zoom no refetch', not [x for x in LOG[m3:] if '/asset/' in x[1]])
                await pg.keyboard.press('Escape'); await pg.wait_for_timeout(300)
            else:
                ok(f'{vp} zoom control found', False)
            store = await pg.evaluate("""async () => ({ls: Object.entries(localStorage).filter(([k,v]) => /blob:|data:image|asset/.test(v)).map(([k]) => k),
                caches: 'caches' in window ? (await caches.keys()) : []})""")
            ok(f'{vp} no private image in localStorage/CacheStorage', not store['ls'] and not store['caches'], store)
            # answer + save
            opt = pg.locator('[data-testid^="player-option-"]:not([data-testid*="label"]):not([data-testid*="math"])').first
            if await opt.count(): await opt.click()
            else: await pg.fill('[data-testid="player-numerical-input"]', '5')
            await pg.wait_for_timeout(2500)
            saves = [x for x in LOG if x[0] == 'PUT' and aid in x[1]]
            ok(f'{vp} answer saved (PUT 200)', any(s[2] == 200 for s in saves), saves[-2:])
            # refresh/resume -> canonical GET
            m4 = len(LOG); await pg.reload(wait_until='networkidle'); await pg.wait_for_timeout(1500)
            ok(f'{vp} full reload uses canonical GET', api_count(rf'^/api/attempts/{aid}$', m4) >= 1)
            fin = pg.locator('[data-testid="player-finish"]')
            if not await fin.is_visible() and not await pg.locator('[data-testid="player-submit-button"]').is_visible():
                await pg.click('[data-testid="player-navigator-toggle"]'); await pg.wait_for_timeout(500)
            await (fin if await fin.is_visible() else pg.locator('[data-testid="player-submit-button"]')).click(); await pg.wait_for_timeout(500)
            await pg.click('[data-testid="confirm-accept"]')
            await pg.wait_for_url('**/results/**', timeout=30000); await pg.wait_for_timeout(4000)
            await pg.wait_for_load_state('networkidle')
            ov = await pg.evaluate('document.documentElement.scrollWidth-document.documentElement.clientWidth')
            ok(f'{vp} results no overflow', ov <= 0, ov)
            await pg.screenshot(path=str(SHOTS / f'{vp}_results.jpeg'), quality=40, type='jpeg')
            body = await pg.inner_text('body')
            OUT['flow'][vp + ' results_text'] = body[:300]
            # open a solution if available
            sol_btn = pg.locator('button:has-text("olution"), [data-testid*="solution"]').first
            if await sol_btn.count():
                try:
                    await sol_btn.click(timeout=3000); await pg.wait_for_timeout(3000)
                except Exception as e: print('sol click', e)
            OUT['flow'][vp + ' solution_requests_after_submit'] = [x[2] for x in LOG if '/solution' in x[1]][:5]
            await pg.screenshot(path=str(SHOTS / f'{vp}_results_solution.jpeg'), quality=40, type='jpeg')
            ok(f'{vp} no page errors', not errs, errs[:3])
            await ctx.close()
        await b.close()
    OUT['api_log_tail'] = LOG[-15:]
    Path('/app/test_reports/iter164_browser_prod.json').write_text(json.dumps(OUT, indent=1, default=str))
    print('FAILS', [k for k, v in OUT['checks'].items() if not v['pass']])

if __name__ == "__main__":
    asyncio.run(main())
