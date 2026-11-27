"""TEST-ONLY (testing agent, iteration 232) extra UI walk for Student Choice on the iteration-229 bridge (127.0.0.1:8783):
results rank tab notice, history badge, paper page (no Save), random-only mode step=tests, mobile step=tests, normal SetDetail unchanged.
Run through: bash tests/runners/solo.sh bash /root/p2/t1_ui232.sh
"""
import asyncio, os, re, sys, uuid
os.environ.setdefault('BRIDGE_OUT', '/tmp/uibridge229'); os.environ.setdefault('BRIDGE_PORT', '8783')
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from playwright.async_api import async_playwright  # noqa: E402
from ui_cut210 import open_as, BASE, say, RESULT, API, OVERFLOW  # noqa: E402
import httpx, json  # noqa: E402

SS = '/app/.screenshots/ui232'; os.makedirs(SS, exist_ok=True)
B = json.load(open('/tmp/uibridge229/bridge.json'))
MIN = {'Physics': 2.4, 'Chemistry': 1.6, 'Mathematics': 3.2}


async def shot(page, name):
    await page.screenshot(path=f'{SS}/{name}.jpeg', quality=30, full_page=False)


async def owner_set(pick, rnd):
    async with httpx.AsyncClient(base_url=API, cookies=B['owner'], headers={'origin': BASE}) as c:
        cur = (await c.get('/api/admin/choice/jee-main')).json()['data']['settings']
        r = await c.put('/api/admin/choice/jee-main', json={'expected_revision': cur['revision'], 'pick': pick, 'random': rnd, 'max_questions': 75,
                                                            'max_per_subject': None, 'minutes_per_question': MIN, 'daily_limit': 5})
        return r.status_code


async def make_and_finish():
    async with httpx.AsyncClient(base_url=API, cookies=B['riya'], headers={'origin': BASE}, timeout=60) as c:
        r = await c.post('/api/choice/papers', json={'exam': 'jee-main', 'request_key': 'TESTt1' + uuid.uuid4().hex, 'mode': 'random', 'count': 3})
        sid = r.json()['data']['set_id']
        r = await c.post(f'/api/sets/{sid}/start', json={'start_key': 'TEST' + uuid.uuid4().hex})
        aid = r.json()['data']['id']
        r = await c.post(f'/api/attempts/{aid}/submit')
        return sid, aid, r.status_code


async def desk(pw):
    say('setup: owner both On', await owner_set(True, True) == 200)
    sid, aid, st = await make_and_finish()
    say('setup: made, started, submitted a 3-Q random paper', st in (200, 202), st)
    br, page, bad, logs = await open_as(pw, 'riya', 'desk')
    try:
        await page.goto(f'{BASE}/sets/{sid}'); await page.get_by_test_id('set-detail-page').wait_for(timeout=30000)
        eb = (await page.locator('.eyebrow').first.inner_text()).strip().upper()
        say('paper page: eyebrow JEE MAIN · STUDENT CHOICE', eb == 'JEE MAIN · STUDENT CHOICE', eb)
        say('paper page: 3 Q, 12 marks', (await page.get_by_test_id('set-question-count').inner_text()).strip() == '3' and
            (await page.get_by_test_id('set-maximum-marks').inner_text()).strip() == '12')
        saves = await page.locator('[data-testid*="save" i]').count() + await page.get_by_role('button', name=re.compile(r'^\s*save', re.I)).count()
        say('paper page: no Save button', saves == 0, saves)
        await page.get_by_test_id('set-back').click(); await page.wait_for_url(re.compile(r'/choice'), timeout=15000)
        say('paper page: back goes to /choice', '/choice' in page.url, page.url)
        await page.goto(f'{BASE}/results/{aid}?view=rank')
        try:
            await page.get_by_test_id('result-choice-no-rank').wait_for(timeout=40000)
            say('results: rank tab shows result-choice-no-rank', 'Rank nahi banta' in await page.get_by_test_id('result-choice-no-rank').inner_text())
        except Exception as e:  # noqa: BLE001
            say('results: rank tab shows result-choice-no-rank', False, repr(e)[:200])
        await shot(page, 'desk_results_rank')
        await page.goto(f'{BASE}/exams/jee-main/results')
        try:
            await page.get_by_test_id(f'history-meta-{aid}').wait_for(timeout=30000)
            say('history: Student Choice badge', 'Student Choice' in await page.get_by_test_id(f'history-meta-{aid}').inner_text())
        except Exception as e:  # noqa: BLE001
            say('history: Student Choice badge', False, repr(e)[:200])
        # random-only mode
        say('setup: owner pick Off, random On', await owner_set(False, True) == 200)
        await page.goto(BASE + '/choice'); await page.get_by_test_id('choice-way-random').wait_for(timeout=30000)
        say('random-only: no pick way', await page.get_by_test_id('choice-way-pick').count() == 0)
        await page.goto(BASE + '/choice?step=chapters'); await page.get_by_test_id('choice-chapter-TEST_P1').wait_for(timeout=20000)
        await page.get_by_test_id('choice-chapter-TEST_P1').click()
        await page.get_by_test_id('choice-subject-chemistry').click(); await page.get_by_test_id('choice-chapter-TEST_C1').click()
        say('random-only: bar says Tests dekho', 'Tests dekho' in await page.get_by_test_id('choice-pick-bar-go').inner_text(), await page.get_by_test_id('choice-pick-bar-go').inner_text())
        await page.get_by_test_id('choice-pick-bar-go').click(); await page.get_by_test_id('choice-tests-screen').wait_for(timeout=15000)
        say('random-only: step=tests in URL', 'step=tests' in page.url, page.url)
        say('random-only: 2 chapter tests listed', '2 chapter tests' in await page.get_by_test_id('choice-tests-count').inner_text())
        say('random-only: TEST_P1 action Start', (await page.get_by_test_id('choice-test-TEST_P1-action').inner_text()).strip() == 'Start')
        await shot(page, 'desk_tests')
        await page.get_by_test_id('choice-test-TEST_P1').click(); await page.wait_for_url(re.compile(r'/sets/TEST_P1'), timeout=15000)
        await page.get_by_test_id('set-preflight-start-button').click(); await page.wait_for_url(re.compile(r'/attempts/'), timeout=30000)
        say('random-only: chapter test starts', '/attempts/' in page.url, page.url)
        await page.goto(BASE + '/choice?step=tests'); await page.get_by_test_id('choice-test-TEST_P1-action').wait_for(timeout=20000)
        await page.wait_for_timeout(1500)
        say('random-only: TEST_P1 action now Resume', (await page.get_by_test_id('choice-test-TEST_P1-action').inner_text()).strip() == 'Resume',
            await page.get_by_test_id('choice-test-TEST_P1-action').inner_text())
        await page.goto(BASE + '/choice?step=questions'); await page.wait_for_timeout(2000)
        say('random-only: step=questions falls to tests', await page.get_by_test_id('choice-tests-screen').count() == 1 and await page.locator('.ch-list .ch-q').count() == 0)
        await page.goto(BASE + '/sets/TEST_P2'); await page.get_by_test_id('set-detail-page').wait_for(timeout=30000)
        eb = (await page.locator('.eyebrow').first.inner_text()).upper()
        say('normal chapter SetDetail: no STUDENT CHOICE eyebrow', 'STUDENT CHOICE' not in eb, eb)
        say('desk: no page overflow', not await page.evaluate(OVERFLOW), await page.evaluate(OVERFLOW))
        say('desk: no console errors', not logs, logs[:3])
        print('INFO 4xx/5xx seen:', bad[:10], flush=True)
    finally:
        await br.close()
    br, page, bad, logs = await open_as(pw, 'riya', 'mob')
    check = "() => [...document.querySelectorAll('body *')].filter(e => e.getBoundingClientRect().right > innerWidth + 1 && !e.closest('.ch-pills')).slice(0,5).map(e => (e.className && e.className.toString()) || e.tagName)"
    try:
        await page.goto(BASE + '/choice?step=tests'); await page.get_by_test_id('choice-tests-none').wait_for(timeout=30000)
        say('mob: fresh browser, no ticked chapters -> choice-tests-none', True)
        await page.get_by_test_id('choice-tests-pick').click(); await page.get_by_test_id('choice-chapter-TEST_P1').click()
        await page.get_by_test_id('choice-pick-bar-go').click(); await page.get_by_test_id('choice-tests-screen').wait_for(timeout=30000)
        say('mob: step=tests no sideways overflow', not await page.evaluate(check), await page.evaluate(check))
        await shot(page, 'mob_tests')
        await page.goto(f'{BASE}/results/{aid}?view=rank')
        try:
            await page.get_by_test_id('result-choice-no-rank').wait_for(timeout=40000)
            say('mob: rank notice no overflow', not await page.evaluate(check), await page.evaluate(check))
        except Exception as e:  # noqa: BLE001
            say('mob: rank notice no overflow', False, repr(e)[:200])
        await shot(page, 'mob_results_rank')
        say('mob: no console errors', not logs, logs[:3])
    finally:
        await br.close()


async def main():
    async with async_playwright() as pw:
        try:
            await desk(pw)
        except Exception as e:  # noqa: BLE001
            say('walk finished without exception', False, repr(e)[:400])
    f = [r for r in RESULT if not r[1]]
    print(f'TOTAL {len(RESULT)} PASS {len(RESULT) - len(f)} FAIL {len(f)}')

asyncio.run(main())
