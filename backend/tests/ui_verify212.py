"""TEST-ONLY browser walk (iteration 212): Super admin Master -> CUTX, proof view of boxed chapter (16 q), Try as student,
Live rules, boxed fix tool, solutions matched to questions. Reuses helpers of ui_verify211 (routes /api to bridge :8772).
Run: python tests/ui_verify212.py [master proofbox tryst live solutions boxfix] [desk mob]
"""
import asyncio, os, sys, re
os.environ.setdefault('SS_DIR', '/app/.screenshots/ui212')
sys.argv_saved = sys.argv; sys.argv = [sys.argv[0], 'none']
import importlib.util
spec = importlib.util.spec_from_file_location('v211', os.path.join(os.path.dirname(__file__), 'ui_verify211_lib.py'))
v = importlib.util.module_from_spec(spec); spec.loader.exec_module(v)
sys.argv = sys.argv_saved
from playwright.async_api import async_playwright
ok, open_as, no_overflow, wait_pics, PROBE, stacked, F, BASE, SIZES = v.ok, v.open_as, v.no_overflow, v.wait_pics, v.PROBE, v.stacked, v.F, v.BASE, v.SIZES
SS = '/app/.screenshots/ui212'; os.makedirs(SS, exist_ok=True)


# Master: exam CUTX -> Chapter-wise + Mock Tests sections, book mocks listed with state + summary; Draft mock page filters
async def master(pw, size):
    tag = 'master-' + size
    br, page, bad, logs = await open_as(pw, 'owner', size)
    try:
        await page.goto(f'{BASE}/super-admin'); await page.wait_for_timeout(5000)
        await page.screenshot(path=f'{SS}/master_{size}_home.jpg', quality=40)
        txt = await page.inner_text('body')
        ok(f'{tag}: Master home lists CUTX', 'CUTX' in txt, txt[:300])
        await page.goto(f"{BASE}/super-admin/exam/{F['slug']}"); await page.wait_for_timeout(4000)
        types = await page.locator('[data-testid^="master-type-open-"]').all_inner_texts()
        print('   types:', types)
        ok(f'{tag}: exam has Chapter-wise and Mock sections', any('Chapter' in t for t in types) and any('Mock' in t for t in types), types)
        await page.screenshot(path=f'{SS}/master_{size}_exam.jpg', quality=40)
        await no_overflow(page, tag + ' exam')
        for sec in ('chapters', 'section'):
            await page.goto(f"{BASE}/super-admin/exam/{F['slug']}/{F[sec]}"); await page.wait_for_timeout(5000)
            rows = await page.locator('[data-testid^="mock-row-"]').all_inner_texts()
            sums = await page.locator('.cut-summary').all_inner_texts()
            print(f'   {sec}: {len(rows)} rows; first:', [r.replace("\n", " | ")[:160] for r in rows[:3]], 'summaries', sums[:3])
            ok(f'{tag}: section {sec} lists mocks', len(rows) > 0, rows[:2])
            await page.screenshot(path=f'{SS}/master_{size}_{sec}.jpg', quality=40)
            await no_overflow(page, f'{tag} {sec}')
        bid, mid = F['boxed']
        await page.goto(f'{BASE}/super-admin/fix/{bid}/{mid}?all=1')
        await page.wait_for_selector('[data-testid="all-questions-list"]', timeout=30000)
        fl = await page.locator('[data-testid="all-questions-filters"] button').all_inner_texts()
        print('   filters:', fl)
        for w in ('Saare sawaal', 'Cut dekhna hai', '4 se kam option', 'Engine ne mark kiye', 'Proof view'):
            ok(f'{tag}: filter "{w}" present', any(w in f for f in fl), fl)
        ok(f'{tag}: Try as student + Back on Draft page', await page.locator('[data-testid^="mock-try-"], button:has-text("Try as student")').count() >= 1 and await page.locator('[data-testid="fix-mock-back"]').count() == 1)
        summ = await page.locator('[data-testid="all-questions-cut-summary"]').all_inner_texts()
        print('   cut summary:', summ)
        ok(f'{tag}: summary "16 sawaal · 16 saaf kate"', summ and '16 sawaal' in summ[0] and '16 saaf kate' in summ[0], summ)
        await page.screenshot(path=f'{SS}/master_{size}_draft.jpg', quality=40)
        await no_overflow(page, tag + ' draft page')
        ok(f'{tag}: no API errors / page errors', not bad and not logs, (bad[:4], logs[:3]))
    except Exception as e:
        ok(tag + ' walk', False, (e, bad[:3], logs[:3])); await page.screenshot(path=f'{SS}/master_{size}_err.jpg', quality=40)
    await br.close()


# Proof view of the boxed chapter: 16 questions, 1 stem + 4 stacked full-width options, Key A-D
async def proofbox(pw, size):
    tag = 'proofbox-' + size
    br, page, bad, logs = await open_as(pw, 'owner', size)
    try:
        bid, mid = F['boxed']
        await page.goto(f'{BASE}/super-admin/fix/{bid}/{mid}?all=1')
        await page.wait_for_selector('[data-testid="all-questions-list"]', timeout=30000)
        await page.click('[data-testid="all-questions-filter-proof"]')
        await page.wait_for_selector('[data-testid="proof-list"] .piece-img', timeout=30000)
        rows = page.locator('[data-testid="proof-list"] .proof-row')
        n = await rows.count()
        ok(f'{tag}: proof lists 16 questions', n == 16, n)
        fails, keys, nopt = [], [], 0
        for i in range(n):
            row = rows.nth(i)
            await row.scroll_into_view_if_needed(); await page.wait_for_timeout(700)
            await page.wait_for_function("(i) => { const r = document.querySelectorAll('[data-testid=\"proof-list\"] .proof-row')[i]; const p = [...r.querySelectorAll('.piece-img')]; return p.length && p.every(e => e.tagName !== 'IMG' || (e.complete && e.naturalWidth > 0)); }", arg=i, timeout=20000)
            head = (await row.locator('header').inner_text()).replace('\n', ' ')
            k = re.search(r'Key: (\S+)', head); keys.append(k.group(1) if k else None)
            stems = await row.locator('.piece-stem').count()
            gs = await row.evaluate("(r) => { const box = r.querySelector('[data-testid$=\"-piece-options\"]'); const st = r.querySelector('.piece-stem'); const sw = st ? st.getBoundingClientRect().width : 0; if (!box) return {sw, none: true}; const b = box.getBoundingClientRect(); const cs = getComputedStyle(box); return {sw, layout: box.dataset.layout, cols: cs.gridTemplateColumns.split(' ').filter(Boolean).length, x: b.left, w: b.width, cards: [...box.querySelectorAll('[data-testid*=\"-option-card-\"]')].map(c => { const q = c.getBoundingClientRect(); return {x: q.left, y: q.top, w: q.width, h: q.height, k: c.dataset.testid.slice(-1)}; })}; }")
            if gs.get('none'):
                if stems != 1: fails.append((i + 1, 'stems', stems))
                continue
            nopt += 1
            letters = [c['k'] for c in gs['cards']]
            if stems != 1 or letters != list('ABCD') or not stacked(gs) or abs(gs['sw'] - gs['w']) > 4:
                fails.append((i + 1, head[:40], stems, letters, gs['cols'], round(gs['sw']), round(gs['w'])))
            if i < 16 and (size == 'desk' or i < 4):
                await row.screenshot(path=f'{SS}/proofbox_{size}_q{i + 1:02d}.jpg', quality=40)
        print('   keys:', keys, 'option questions', nopt)
        ok(f'{tag}: every question 1 stem, option questions have A-D stacked full width ({nopt})', not fails, fails[:5])
        ok(f'{tag}: every Key in A-D (or a number for numericals)', all(k and (k in 'ABCD' or re.match(r'^-?[\d.]+$', k)) for k in keys), keys)
        await no_overflow(page, tag)
        ok(f'{tag}: no API errors / page errors', not bad and not logs, (bad[:4], logs[:3]))
    except Exception as e:
        ok(tag + ' walk', False, (e, bad[:3], logs[:3])); await page.screenshot(path=f'{SS}/proofbox_{size}_err.jpg', quality=40)
    await br.close()


# Try as student from the Draft page (and from the Proof view of the Live boxed chapter) -> new tab, real player, stacked options
async def tryst(pw, size, key='boxed_small', proof=False):
    tag = 'tryst-' + key + ('-proof-' if proof else '-') + size
    br, fix, bad, logs = await open_as(pw, 'owner', size)
    try:
        bid, mid = F[key]
        await fix.goto(f'{BASE}/super-admin/fix/{bid}/{mid}?all=1')
        await fix.wait_for_selector('[data-testid="all-questions-list"]', timeout=30000)
        if proof:
            await fix.click('[data-testid="all-questions-filter-proof"]')
            await fix.wait_for_selector('[data-testid="proof-list"] .piece-img', timeout=30000)
        btn = fix.locator('[data-testid^="mock-try-"]').first
        async with fix.context.expect_page(timeout=15000) as tab_info:
            await btn.click()
        page = await tab_info.value
        page.on('pageerror', lambda e: logs.append(str(e)[:200]))
        page.on('response', lambda r: bad.append((r.status, r.url.split('/api')[-1][:80])) if '/api/' in r.url and r.status >= 400 and '/dream' not in r.url else None)
        await page.wait_for_url('**/sets/**', timeout=30000)
        ok(f'{tag}: Fix page stays open in the first tab', '/super-admin/fix/' in fix.url, fix.url)
        await page.wait_for_selector('[data-testid="set-preflight-start-button"]', timeout=20000)
        ok(f'{tag}: private preview notice shown', await page.locator('[data-testid="private-preview-notice"]').count() == 1)
        ok(f'{tag}: back link returns to Master', 'Back to Master' in await page.locator('[data-testid="set-back"]').inner_text())
        await page.screenshot(path=f'{SS}/tryst_{key}_{size}_set.jpg', quality=40)
        await page.click('[data-testid="set-preflight-start-button"]')
        await page.wait_for_url('**/attempts/**', timeout=30000)
        print('   url', page.url)
        try:
            await page.wait_for_selector('[data-testid="get-ready-begin"]', timeout=8000); await page.wait_for_timeout(3000)
            await page.click('[data-testid="get-ready-begin"]')
        except Exception:
            pass
        await page.wait_for_selector('[data-testid="player-piece-stem"]', timeout=30000)
        seen = 0; fails = []
        for _ in range(2):
            await wait_pics(page)
            if await page.locator('[data-testid="player-piece-options"]').count():
                g = (await page.evaluate(PROBE, '[data-testid="player-piece-options"]'))[0]
                seen += 1
                if not stacked(g): fails.append(g['cols'])
            nx = page.locator('[data-testid="player-next"]')
            if not await nx.count() or await nx.is_disabled(): break
            await nx.click(); await page.wait_for_timeout(500)
        await page.screenshot(path=f'{SS}/tryst_{key}_{size}.jpg', quality=40)
        ok(f'{tag}: Try as student opens player with stacked A-D ({seen} checked)', seen >= 1 and not fails, fails)
        await no_overflow(page, tag)
        ok(f'{tag}: no API errors / page errors', not bad and not logs, (bad[:4], logs[:3]))
    except Exception as e:
        ok(tag + ' walk', False, (e, bad[:3], logs[:3])); await fix.screenshot(path=f'{SS}/tryst_{key}_{size}_err.jpg', quality=40)
    await br.close()


# Live: live_set visible to student; held mock cannot go Live
async def live(pw, size):
    tag = 'live-' + size
    br, page, bad, logs = await open_as(pw, 'student', size)
    try:
        await page.goto(f"{BASE}/sets/{F['live_set']}"); await page.wait_for_timeout(5000)
        txt = await page.inner_text('body')
        ok(f'{tag}: student sees live set "Redox"', 'Redox' in txt, txt[:300])
        await page.screenshot(path=f'{SS}/live_{size}_student.jpg', quality=40)
        await page.goto(f"{BASE}/exams/{F['slug']}"); await page.wait_for_timeout(5000)
        txt2 = await page.inner_text('body')
        print('   exam page has Redox:', 'Redox' in txt2, '| has Chapter:', 'Chapter' in txt2)
        await page.screenshot(path=f'{SS}/live_{size}_exam.jpg', quality=40)
    except Exception as e:
        ok(tag + ' student', False, e)
    await br.close()
    br, page, bad, logs = await open_as(pw, 'owner', size)
    try:
        held_found = 0
        for sec in ('chapters', 'section'):
            await page.goto(f"{BASE}/super-admin/exam/{F['slug']}/{F[sec]}"); await page.wait_for_timeout(5000)
            for key in ('held', 'boxed_held', 'boxed_held_mob'):
                mid = F[key][1]
                sw = page.locator(f'[data-testid="mock-live-switch-{mid}"]')
                if await sw.count():
                    held_found += 1
                    dis = await sw.is_disabled()
                    await page.click(f'[data-testid="mock-status-{mid}"]'); await page.wait_for_timeout(400)
                    mk = page.locator(f'[data-testid="mock-make-live-{mid}"]')
                    mdis = (await mk.get_attribute('data-disabled')) is not None or (await mk.get_attribute('aria-disabled')) == 'true'
                    await page.keyboard.press('Escape')
                    ok(f'{tag}: held mock {key} cannot be set Live (switch+menu disabled)', dis and mdis, (dis, mdis))
            lv = page.locator(f'[data-testid^="mock-live-word-"]')
            print(f'   {sec} live words:', await lv.all_inner_texts())
        ok(f'{tag}: found held mocks in Master list', held_found >= 1, held_found)
        ok(f'{tag}: no API errors / page errors', not bad and not logs, (bad[:4], logs[:3]))
    except Exception as e:
        ok(tag + ' owner', False, (e, bad[:3], logs[:3]))
    await br.close()


# Results / Solutions: walk questions, screenshot question + worked solution for visual match
async def solutions(pw, size):
    tag = 'solutions-' + size
    br, page, bad, logs = await open_as(pw, 'student', size)
    try:
        await page.goto(f"{BASE}/results/{F['done_attempt']}?view=solutions")
        await page.wait_for_selector('[data-testid="solution-question-rail"]', timeout=30000)
        nums = sorted({int(x) for x in await page.locator('[data-testid="solution-question-rail"] button span').all_inner_texts() if x.strip().isdigit()})
        print('   question numbers', nums)
        fails = []; checked = 0
        for n in nums[:8] if size == 'desk' else nums[:5]:
            await page.click(f'[data-testid="solution-question-{n}"]'); await page.wait_for_timeout(1200)
            await wait_pics(page)
            sec = page.locator(f'[data-testid="solution-content-{n}"]')
            await sec.scroll_into_view_if_needed(); await page.wait_for_timeout(500)
            try:
                await page.wait_for_function("(n) => { const s = document.querySelector('[data-testid=\"solution-content-' + n + '\"]'); const p = s ? [...s.querySelectorAll('img')] : []; return p.length && p.every(e => e.complete && e.naturalWidth > 0); }", arg=n, timeout=15000)
            except Exception:
                pass
            simg = await sec.locator('img').count()
            title = await sec.locator('h3').all_inner_texts()
            if await page.locator('[data-testid$="-piece-options"]').count():
                g = (await page.evaluate(PROBE, '[data-testid$="-piece-options"]'))[0]
                right = sum('is-correct' in c['cls'] for c in g['cards'])
                icons = await page.locator('[data-testid*="-option-mark-"] svg').count()
                if not stacked(g) or right != 1 or icons < 1: fails.append((n, 'opts', g['cols'], right, icons))
            if simg < 1 or not title or f'Q{n}' not in title[0]: fails.append((n, 'sol', simg, title))
            checked += 1
            art = page.locator('[data-testid="results-question-review-item"]')
            await art.screenshot(path=f'{SS}/sol_{size}_q{n:02d}.jpg', quality=40)
            await no_overflow(page, f'{tag} Q{n}')
        ok(f'{tag}: {checked} questions show stacked options, 1 correct, marks with icon, own worked solution', checked >= 5 and not fails, fails[:5])
        ok(f'{tag}: no API errors / page errors', not bad and not logs, (bad[:4], logs[:3]))
    except Exception as e:
        ok(tag + ' walk', False, (e, bad[:3], logs[:3])); await page.screenshot(path=f'{SS}/sol_{size}_err.jpg', quality=40)
    await br.close()


# Boxed held question fix tool: printed outlines, tap -> kiska hai, A then B pre-chosen, mouse-drawn box, overlap refused,
# use-printed, save blocked until accept-outside, save -> cut by hand, mock re-checked. MUTATES boxed_held / boxed_held_mob.
async def boxfix(pw, size):
    tag = 'boxfix-' + size
    br, page, bad, logs = await open_as(pw, 'owner', size)
    try:
        t = await v.open_fix(page, 'boxed_held' if size == 'desk' else 'boxed_held_mob')
        why = await page.inner_text(f'[data-testid="{t}-held-reason"]')
        print('   held reason:', why[:200])
        ok(f'{tag}: held card explains "Chhape hue boxes ke bahar bhi kuch chhapa hai"', 'Chhape hue boxes ke bahar' in why, why)
        ok(f'{tag}: full page + draw mode by default', await page.get_attribute(f'[data-testid="{t}-view-full"]', 'aria-pressed') == 'true' and await page.get_attribute(f'[data-testid="{t}-mode-draw"]', 'aria-pressed') == 'true')
        np = await page.locator('[data-testid^="cut-printed-"]').count()
        ok(f'{tag}: 5 printed boxes outlined', np == 5, np)
        await page.screenshot(path=f'{SS}/boxfix_{size}_open.jpg', quality=40)
        pr = {i: await v.rect_of(page, f'[data-testid="cut-printed-{i}"]') for i in range(5)}
        # tap printed box 1 -> kiska hai -> A
        await page.evaluate("document.querySelector('[data-testid=\"cut-printed-1\"]').scrollIntoView({block:'center'})"); await page.wait_for_timeout(300)
        b = await page.locator('[data-testid="cut-printed-1"]').bounding_box()
        await page.mouse.click(b['x'] + b['width'] * .4, b['y'] + b['height'] * .5); await page.wait_for_timeout(300)
        title = await page.inner_text(f'[data-testid="{t}-assign-title"]')
        btns = [x for x in 'qABCD' if await page.locator(f'[data-testid="{t}-assign-{x}"]').count()]
        ok(f'{tag}: tap printed box asks kiska hai with Sawaal/A/B/C/D', 'kiska hai' in title and btns == list('qABCD'), (title, btns))
        await page.screenshot(path=f'{SS}/boxfix_{size}_ask.jpg', quality=40)
        await page.click(f'[data-testid="{t}-assign-A"]'); await page.wait_for_timeout(300)
        gotA = await v.rect_of(page, '[data-testid="cut-box-A"]')
        ok(f'{tag}: A takes the whole printed box', all(abs(x - y) < .005 for x, y in zip(gotA, pr[1])), (gotA, pr[1]))
        title2 = await page.inner_text(f'[data-testid="{t}-assign-title"]')
        ok(f'{tag}: after A, B is pre-chosen', 'B ka box' in title2, title2)
        # mouse-drawn rectangle around printed box 2 -> B (pre-chosen)
        r2 = pr[2]; px = .006 if size == 'desk' else .003
        await v.pull(page, [r2[0] - px, r2[1] - .001, r2[2] + px, r2[3] + .001])
        t3 = await page.inner_text(f'[data-testid="{t}-assign-title"]')
        ok(f'{tag}: mouse-drawn rectangle asks kiska hai', 'kiska hai' in t3, t3)
        if 'kiska hai' in t3:
            await page.click(f'[data-testid="{t}-assign-B"]'); await page.wait_for_timeout(300)
        gotB = await v.rect_of(page, '[data-testid="cut-box-B"]')
        print('   after drawing B:', t3, [round(x, 3) for x in gotB], [round(x, 3) for x in r2])
        ok(f'{tag}: mouse-drawn rectangle becomes B where drawn', abs(gotB[0] - (r2[0] - px)) < .004 and abs(gotB[2] - (r2[2] + px)) < .004, (gotB, r2))
        # overlap: draw C over A's printed ink
        if await page.locator(f'[data-testid="{t}-mode-draw"]').get_attribute('aria-pressed') != 'true':
            await page.click(f'[data-testid="{t}-mode-draw"]')
        await page.click(f'[data-testid="{t}-assign-C"]'); await page.wait_for_timeout(200)
        await v.pull(page, [pr[1][0], pr[1][1], pr[1][2], pr[1][3]])
        await page.wait_for_timeout(2500)
        reasons = ' | '.join(await page.locator(f'[data-testid="{t}-reason"]').all_inner_texts())
        print('   overlap reasons:', reasons[:300])
        ok(f'{tag}: two boxes sharing printed ink refused with a reason, Save disabled', ('chadh' in reasons or 'dono' in reasons or 'ek hi box' in reasons) and await page.locator(f'[data-testid="{t}-save"]').is_disabled(), reasons)
        await page.screenshot(path=f'{SS}/boxfix_{size}_overlap.jpg', quality=40)
        # take all printed boxes
        await page.click(f'[data-testid="{t}-use-printed"]')
        await page.wait_for_selector(f'[data-testid="{t}-reason"], [data-testid="{t}-good"]', timeout=20000); await page.wait_for_timeout(2000)
        got = {k: await v.rect_of(page, f'[data-testid="cut-box-{k}"]') for k in 'qABCD'}
        same = all(any(all(abs(a - b) < .005 for a, b in zip(got[k], pr[i])) for i in range(5)) for k in 'qABCD')
        ok(f'{tag}: use-printed puts all five boxes on the printed boxes', same, got)
        reasons = await page.locator(f'[data-testid="{t}-reason"]').all_inner_texts()
        ok(f'{tag}: outside print reported, Save disabled', reasons and await page.locator(f'[data-testid="{t}-save"]').is_disabled(), reasons)
        gs = await page.evaluate(PROBE, f'[data-testid="{t}-preview"] [data-testid$="-piece-options"]')
        nst = await page.locator(f'[data-testid="{t}-preview"] .piece-stem').count()
        ok(f'{tag}: preview = question + A-D stacked', nst == 1 and gs and stacked(gs[0]), (nst, gs[:1]))
        await page.check(f'[data-testid="{t}-accept-outside"]')
        await page.wait_for_selector(f'[data-testid="{t}-good"]', timeout=20000)
        ok(f'{tag}: tick accept-outside enables Save', await page.locator(f'[data-testid="{t}-save"]').is_enabled())
        await page.locator(f'[data-testid="{t}-preview"]').scroll_into_view_if_needed(); await page.screenshot(path=f'{SS}/boxfix_{size}_preview.jpg', quality=40)
        await no_overflow(page, tag + ' before save')
        await page.click(f'[data-testid="{t}-save"]')
        await page.wait_for_selector(f'[data-testid="{t}-saved"]', timeout=25000)
        ok(f'{tag}: "Save ho gaya"', 'Save ho gaya' in await page.inner_text(f'[data-testid="{t}-saved"]'))
        await page.wait_for_timeout(8000)
        bid, mid = F['boxed_held' if size == 'desk' else 'boxed_held_mob']
        await page.goto(f'{BASE}/super-admin/fix/{bid}/{mid}?all=1'); await page.wait_for_selector('[data-testid="all-questions-list"]', timeout=30000)
        summ = await page.inner_text('[data-testid="all-questions-cut-summary"]')
        flags = await page.locator('[data-testid^="all-q-cut-"]').all_inner_texts()
        print('   after save summary:', summ, '| flags', set(flags))
        ok(f'{tag}: summary shows by-hand cut, nothing held', 'aapke boxes se' in summ and 'dekhne hain' not in summ, summ)
        await page.screenshot(path=f'{SS}/boxfix_{size}_after.jpg', quality=40)
        ok(f'{tag}: no API errors / page errors', not bad and not logs, (bad[:4], logs[:3]))
    except Exception as e:
        ok(tag + ' walk', False, (e, bad[:3], logs[:3])); await page.screenshot(path=f'{SS}/boxfix_{size}_err.jpg', quality=40)
    await br.close()


async def main():
    a = sys.argv[1:]
    sizes = [x for x in a if x in SIZES] or ['desk', 'mob']
    want = [x for x in a if x not in SIZES] or ['master', 'proofbox', 'tryst', 'live', 'solutions']
    async def tryst_all(pw, s):
        await tryst(pw, s)
        await tryst(pw, s, 'boxed', proof=True)
    walks = {'master': master, 'proofbox': proofbox, 'tryst': tryst_all, 'live': live, 'solutions': solutions, 'boxfix': boxfix}
    async with async_playwright() as pw:
        for s in sizes:
            for w in want:
                await walks[w](pw, s)
    print('TOTAL', len(v.R), 'PASS', sum(o for _, o in v.R), 'FAIL', sum(not o for _, o in v.R))

asyncio.run(main())
