"""TEST-ONLY iteration 222 UI walk: AITS 'Saare din ek saath' insights + day page, /api routed to tests/series_insights_bridge228.py.
Run: BRIDGE_OUT=/tmp/uibridge228s BRIDGE_PORT=8777 python tests/ui_series_insights228.py
"""
import asyncio, json, os, sys
from pathlib import Path
os.environ.setdefault('BRIDGE_OUT', '/tmp/uibridge228s'); os.environ.setdefault('BRIDGE_PORT', '8777')
sys.path.insert(0, str(Path(__file__).resolve().parent))
from playwright.async_api import async_playwright  # noqa: E402
from ui_cut210 import open_as, BASE, say, RESULT, OVERFLOW  # noqa: E402

INFO = json.load(open(os.environ['BRIDGE_OUT'] + '/bridge.json'))
SS = '/app/.screenshots/ui228'; os.makedirs(SS, exist_ok=True)
H, P = INFO['attempts']['hero'], INFO['attempts']['peer']
EX = INFO['expect']['hero']
T = lambda s: f'[data-testid="{s}"]'


async def no_scroll(page, tag):
    off = await page.evaluate(OVERFLOW)
    sw = await page.evaluate('document.documentElement.scrollWidth'); vw = await page.evaluate('document.documentElement.clientWidth')
    say(f'{tag}: no horizontal scroll', sw <= vw + 1, (sw, vw, off))


async def txt(page, s):
    return (await page.locator(T(s)).first.inner_text()).replace('\n', ' ')


async def hero_walk(pw, size):
    br, page, bad, logs = await open_as(pw, 'hero', size)
    tag = 'hero ' + size
    try:
        # Hub
        await page.goto(BASE + '/series/all-india-jee'); await page.wait_for_selector(T('streak-journey'), timeout=30000)
        await page.wait_for_selector('[data-testid^=series-chip-marks-]', timeout=20000)
        say(f'{tag}: hub chips show marks', await page.locator('[data-testid^=series-chip-marks-]').count() >= 5)
        say(f'{tag}: hub score trend', await page.locator(T('series-trend')).count() == 1)
        await page.click(T('today-analysis-button'))
        await page.wait_for_selector(T('series-analysis-list'), timeout=15000)
        await page.wait_for_selector(T('series-insights'), timeout=20000); await page.wait_for_timeout(800)
        ins_y = (await page.locator(T('series-insights')).bounding_box())['y']
        row_y = (await page.locator('[data-testid^=series-analysis-row-]').first.bounding_box())['y']
        say(f'{tag}: insights above day rows', ins_y < row_y, (ins_y, row_y))
        lab = page.locator('.si-days-label')
        say(f'{tag}: "Har din ka analysis" label', await lab.count() == 1 and 'har din ka analysis' in (await lab.inner_text()).lower())
        ov = await txt(page, 'si-overall'); print('   overall:', ov)
        say(f'{tag}: overall Din diye 6/50', '6/50' in ov.replace(' ', ''), ov)
        say(f'{tag}: overall best 210', '210' in await txt(page, 'si-overall-best'), ov)
        print('   dir:', await txt(page, 'si-dir-marks'), '|', await txt(page, 'si-dir-accuracy'))
        say(f'{tag}: marks direction up', 'badh' in await txt(page, 'si-dir-marks'))
        n_avg = await page.locator(T('si-overall-average')).count()
        say(f'{tag}: unique testid si-overall-average (cosmetic/testability)', n_avg == 1, f'{n_avg} elements share si-overall-average')
        above = (await page.locator(T('si-overall-average')).nth(n_avg - 1).inner_text()).replace('\n', ' ')
        print('   above-average cell:', above)
        say(f'{tag}: "Average se upar" x/5 din', '/5 din' in above, above)
        # Subjects
        say(f'{tag}: subject chart 3 lines', await page.locator(T('si-subject-chart') + ' polyline').count() == 3)
        dirs = [await txt(page, 'si-dir-' + s) for s in ('physics', 'chemistry', 'mathematics')]; print('   subj dirs:', dirs)
        say(f'{tag}: physics up, chemistry down, maths up', 'badh' in dirs[0] and 'gir' in dirs[1] and 'badh' in dirs[2], dirs)
        say(f'{tag}: subject rows', all([await page.locator(T('si-subject-' + s)).count() == 1 for s in ('physics', 'chemistry', 'mathematics')]))
        # Vs class
        say(f'{tag}: vs chart has Aap/Average/Topper', all([await page.locator(T('si-vs-chart-' + k)).count() == 1 for k in ('you', 'average', 'topper')]))
        vs = await page.locator('[data-testid^=si-vs-day-]').evaluate_all('els => els.map(e => e.dataset.testid)')
        say(f'{tag}: vs rows day 5..1 newest first', vs == [f'si-vs-day-{d}' for d in (5, 4, 3, 2, 1)], vs)
        r3 = await txt(page, 'si-vs-day-3'); print('   vs day3:', r3)
        say(f'{tag}: vs day 3 avg/topper', str(EX['day_average']['3']).rstrip('0').rstrip('.') in r3 and str(EX['day_topper']['3']) in r3, r3)
        # Accuracy/time
        say(f'{tag}: accuracy+time charts and tip', await page.locator(T('si-accuracy-chart') + ' svg').count() == 1 and await page.locator(T('si-time-chart') + ' svg').count() == 1 and len(await txt(page, 'si-time-tip')) > 10)
        print('   tip:', await txt(page, 'si-time-tip'))
        # Weak
        ch = await page.locator('[data-testid^=si-chapter-]').evaluate_all('els => els.map(e => e.dataset.testid)')
        say(f'{tag}: first chapter rotational motion', ch[:1] == ['si-chapter-rotational-motion'], ch)
        print('   chapter1:', await txt(page, 'si-chapter-rotational-motion'))
        say(f'{tag}: no untagged note for hero', await page.locator(T('si-weak-untagged')).count() == 0)
        say(f'{tag}: misfire link', (await page.get_attribute(T('si-misfire-link'), 'href')) == '/misfire')
        note = await page.locator('.si-label-note').first.evaluate("e => [getComputedStyle(e).fontSize, getComputedStyle(e).color]")
        h2 = await page.locator('.si-block .sh-label h2').first.evaluate("e => getComputedStyle(e).fontSize")
        print('   note style', note, 'h2', h2)
        say(f'{tag}: notes small grey', float(note[0][:-2]) < float(h2[:-2]), (note, h2))
        await no_scroll(page, tag + ' list')
        await page.locator(T('series-insights')).scroll_into_view_if_needed()
        await page.screenshot(path=f'{SS}/{size}_list_top.jpg', quality=40)
        await page.locator(T('si-vs')).scroll_into_view_if_needed(); await page.screenshot(path=f'{SS}/{size}_list_vs.jpg', quality=40)
        await page.locator(T('si-weak')).scroll_into_view_if_needed(); await page.screenshot(path=f'{SS}/{size}_list_weak.jpg', quality=40)
        # Day 3 via vs row
        await page.click(T('si-vs-day-3'))
        await page.wait_for_selector(T('series-analysis-detail'), timeout=15000)
        say(f'{tag}: vs row opens day 3', page.url.endswith('/analysis/' + H['3']), page.url)
        await page.wait_for_selector(T('si-day-vs'), timeout=15000)
        await page.wait_for_selector(T('series-analysis-stats'), timeout=15000); say(f'{tag}: day stats card', True)
        await page.wait_for_selector(T('series-rank-card'), timeout=15000)
        print('   rank card:', (await txt(page, 'series-rank-card'))[:120])
        dv = await txt(page, 'si-day-vs'); print('   day vs:', dv)
        say(f'{tag}: day vs average 185 topper 255', '185' in dv and '255' in dv, dv)
        btns = await page.locator(T('series-day-destinations') + ' [data-testid^=series-day-view-]').evaluate_all('els => els.map(e => e.dataset.testid)')
        say(f'{tag}: five result buttons', btns == ['series-day-view-' + v for v in ('analysis', 'progress', 'accuracy', 'rank', 'solutions')], btns)
        await page.wait_for_selector(T('a2-top-bar'), timeout=30000)
        say(f'{tag}: workspace loads for day 3', True)
        await no_scroll(page, tag + ' day3')
        await page.screenshot(path=f'{SS}/{size}_day3.jpg', quality=40)
        # five destinations
        for v in ('progress', 'accuracy', 'rank', 'solutions'):
            await page.click(T('series-day-view-' + v))
            await page.wait_for_url(f'**/results/{H["3"]}?view={v}*', timeout=15000)
            await page.wait_for_selector(T('result-view-navigation'), timeout=20000)
            sel = await page.get_attribute(T('result-view-' + v), 'data-state')
            say(f'{tag}: {v} opens results view={v} ({sel})', sel == 'active', page.url)
            if v == 'solutions':
                await page.screenshot(path=f'{SS}/{size}_results_solutions.jpg', quality=40)
            await page.go_back(); await page.wait_for_timeout(1500)
            one = page.url.endswith('/analysis/' + H['3'])
            say(f'{tag}: ONE browser Back from {v} -> day page', one, page.url)
            if not one:
                await page.go_back()
            await page.wait_for_selector(T('series-day-destinations'), timeout=15000)
        await page.wait_for_selector(T('a2-view-solutions'), timeout=30000)
        await page.click(T('a2-view-solutions'))
        await page.wait_for_url('**/results/*view=solutions*', timeout=15000)
        say(f'{tag}: Solutions dekho opens solutions', 'view=solutions' in page.url, page.url)
        await page.go_back(); await page.wait_for_selector(T('a2-retry-mistakes'), timeout=30000)
        say(f'{tag}: back from Solutions dekho -> day page', page.url.endswith('/analysis/' + H['3']), page.url)
        await page.click(T('a2-retry-mistakes')); await page.wait_for_timeout(600)
        dlg = page.get_by_role('dialog')
        say(f'{tag}: retry confirm dialog', await dlg.count() >= 1 and 'Turn mistakes' in await dlg.first.inner_text())
        await page.screenshot(path=f'{SS}/{size}_retry_dialog.jpg', quality=40)
        await page.keyboard.press('Escape'); await page.wait_for_timeout(400)
        # Back chain
        await page.go_back(); await page.wait_for_selector(T('series-analysis-list'), timeout=15000)
        say(f'{tag}: back -> list', page.url.endswith('/series/all-india-jee/analysis'), page.url)
        await page.go_back(); await page.wait_for_selector(T('streak-journey'), timeout=15000)
        say(f'{tag}: back -> hub', page.url.endswith('/series/all-india-jee'), page.url)
        # Row tap -> day page -> back
        await page.click(T('today-analysis-button')); await page.wait_for_selector('[data-testid^=series-analysis-open-]', timeout=15000)
        await page.click(T('series-analysis-open-' + H['6']))
        await page.wait_for_selector(T('series-analysis-detail'), timeout=15000)
        await page.wait_for_selector(T('si-day-vs-sealed'), timeout=15000)
        print('   day6 sealed:', await txt(page, 'si-day-vs-sealed'))
        say(f'{tag}: day 6 sealed card', True)
        say(f'{tag}: day 6 five buttons', await page.locator('[data-testid^=series-day-view-]').count() == 5)
        await page.wait_for_timeout(2500)
        print('   day6 workspace text:', (await page.locator(T('series-analysis-detail')).inner_text())[-200:].replace('\n', ' | '))
        await no_scroll(page, tag + ' day6')
        await page.go_back(); await page.wait_for_selector(T('series-analysis-list'), timeout=15000)
        say(f'{tag}: back from row -> list', page.url.endswith('/analysis'), page.url)
        # Resize check
        if size == 'desk':
            await page.wait_for_selector(T('si-subject-chart') + ' svg', timeout=15000)
            w0 = await page.locator(T('si-subject-chart') + ' svg').get_attribute('width')
            await page.set_viewport_size({'width': 390, 'height': 844}); await page.wait_for_timeout(1200)
            w1 = await page.locator(T('si-subject-chart') + ' svg').get_attribute('width')
            say(f'{tag}: chart redraws after resize', float(w1) < float(w0) and float(w1) <= 390, (w0, w1))
            await no_scroll(page, tag + ' list after resize to 390')
            await page.screenshot(path=f'{SS}/resized_list.jpg', quality=40)
            await page.goto(BASE + '/series/all-india-jee/analysis/' + H['3']); await page.wait_for_selector(T('a2-top-bar'), timeout=30000)
            await page.set_viewport_size({'width': 1920, 'height': 1000}); await page.wait_for_timeout(500)
            await page.set_viewport_size({'width': 390, 'height': 844}); await page.wait_for_timeout(1200)
            await no_scroll(page, tag + ' day3 after resize to 390')
        # Regression
        await page.goto(BASE + '/results/' + H['3']); await page.wait_for_selector(T('result-view-navigation'), timeout=30000)
        say(f'{tag}: results page five tabs', await page.locator('[data-testid^=result-view-]').filter(has_not=page.locator('section')).count() >= 5)
        await page.goto(BASE + '/series/all-india-jee?tab=results'); await page.wait_for_selector('[data-testid^=series-result-]', timeout=30000)
        say(f'{tag}: hub ?tab=results loads', await page.locator('[data-testid^=series-result-]').count() >= 1)
    except Exception as e:
        say(tag + ' walk', False, str(e)[:400]); await page.screenshot(path=f'{SS}/{size}_err.jpg', quality=40)
    finally:
        print('   bad api:', bad[:10]); print('   logs:', logs[:5])
        say(f'{tag}: no page errors', not [l for l in logs if 'PAGEERROR' in l], logs[:3])
        say(f'{tag}: no 5xx', not [b for b in bad if b[0] >= 500 and '/dream' not in b[1]], bad[:5])
        await br.close()


async def peer_walk(pw, size):
    br, page, bad, logs = await open_as(pw, 'peer', size)
    tag = 'peer ' + size
    try:
        await page.goto(BASE + '/series/all-india-jee/analysis'); await page.wait_for_selector(T('series-insights'), timeout=30000)
        await page.wait_for_timeout(800)
        print('   overall:', await txt(page, 'si-overall'))
        say(f'{tag}: 4/50 days', '4/50' in (await txt(page, 'si-overall')).replace(' ', ''))
        lost = await page.locator('[data-testid^=si-lost-]').evaluate_all('els => els.map(e => e.dataset.testid)')
        say(f'{tag}: subject loss rows', len(lost) == 3, lost)
        say(f'{tag}: untagged note', await page.locator(T('si-weak-untagged')).count() == 1)
        say(f'{tag}: no chapter rows', await page.locator('[data-testid^=si-chapter-]').count() == 0)
        vs = await page.locator('[data-testid^=si-vs-day-]').evaluate_all('els => els.map(e => e.dataset.testid)'); print('   vs rows:', vs)
        say(f'{tag}: practice day 5 not in vs rows', 'si-vs-day-5' not in vs, vs)
        html = await page.content()
        say(f'{tag}: no hero attempt ids on page', not any(i in html for i in H.values()))
        await no_scroll(page, tag + ' list')
        await page.locator(T('si-weak')).scroll_into_view_if_needed(); await page.screenshot(path=f'{SS}/peer_{size}_weak.jpg', quality=40)
        await page.click(T('series-analysis-open-' + P['5'])); await page.wait_for_selector(T('series-day-destinations'), timeout=15000)
        await page.wait_for_timeout(2500)
        say(f'{tag}: practice day has no vs card', await page.locator(T('si-day-vs')).count() == 0 and await page.locator(T('si-day-vs-sealed')).count() == 0)
        await no_scroll(page, tag + ' practice day')
        await page.screenshot(path=f'{SS}/peer_{size}_day5.jpg', quality=40)
    except Exception as e:
        say(tag + ' walk', False, str(e)[:400]); await page.screenshot(path=f'{SS}/peer_{size}_err.jpg', quality=40)
    finally:
        print('   bad api:', bad[:10])
        say(f'{tag}: no page errors', not [l for l in logs if 'PAGEERROR' in l], logs[:3])
        await br.close()


async def main():
    async with async_playwright() as pw:
        for size in ('desk', 'mob'):
            await hero_walk(pw, size)
            await peer_walk(pw, size)
    ok = sum(1 for r in RESULT if r[1])
    print('TOTAL', len(RESULT), 'PASS', ok, 'FAIL', len(RESULT) - ok)

asyncio.run(main())
