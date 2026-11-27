"""TEST-ONLY iteration 229 UI walk for Student Choice via local Playwright against the preview frontend, /api routed to
tests/choice_bridge229.py (127.0.0.1:8783). Run: BRIDGE_OUT=/tmp/uibridge229 BRIDGE_PORT=8783 python tests/ui_choice229.py desk mob
"""
import asyncio, os, re, sys
os.environ.setdefault('BRIDGE_OUT', '/tmp/uibridge229'); os.environ.setdefault('BRIDGE_PORT', '8783')
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from playwright.async_api import async_playwright  # noqa: E402
from ui_cut210 import open_as, BASE, say, RESULT, API, OVERFLOW  # noqa: E402
import httpx  # noqa: E402
import json  # noqa: E402

SS = '/app/.screenshots/ui229'; os.makedirs(SS, exist_ok=True)
B = json.load(open('/tmp/uibridge229/bridge.json'))
Q = '.ch-list .ch-q'


async def shot(page, name):
    await page.screenshot(path=f'{SS}/{name}.jpeg', quality=30, full_page=False)


async def text(page, tid):
    return (await page.get_by_test_id(tid).inner_text()).strip()


async def desk(pw):
    br, page, bad, logs = await open_as(pw, 'riya', 'desk')
    try:
        await page.goto(BASE + '/home'); await page.get_by_test_id('home-choice-card').wait_for(timeout=30000)
        say('home: Student Choice card shows while a way is open', True)
        await page.goto(BASE + '/choice'); await page.get_by_test_id('choice-way-pick').wait_for(timeout=30000)
        say('choice: both ways shown', await page.get_by_test_id('choice-way-random').is_visible())
        say('choice: today 0 / 5', '0 / 5' in await text(page, 'choice-today'), await text(page, 'choice-today'))
        say('choice: 25+25+25 = 3 ghante', '3 ghante' in await text(page, 'choice-time-note'), await text(page, 'choice-time-note'))
        await shot(page, 'desk_start')
        await page.get_by_test_id('choice-way-pick').click(); await page.get_by_test_id('choice-pick-screen').wait_for()
        await page.get_by_test_id('choice-chapter-TEST_P1').click(); await page.get_by_test_id('choice-chapter-TEST_PO').click()
        await page.get_by_test_id('choice-subject-chemistry').click(); await page.get_by_test_id('choice-chapter-TEST_C1').click()
        say('chapters: 3 ticked', '3 chapters chune' in await text(page, 'choice-pick-bar-count'), await text(page, 'choice-pick-bar-count'))
        await page.get_by_test_id('choice-search-input').fill('kinetic'); await page.wait_for_timeout(300)
        say('search: nothing for kinetic, said so', await page.get_by_test_id('choice-search-none').is_visible())
        await page.get_by_test_id('choice-search-input').fill('chemistry chapter'); await page.wait_for_timeout(300)
        say('search: finds across subjects', await page.get_by_test_id('choice-chapter-TEST_C2').is_visible())
        await page.get_by_test_id('choice-search-clear').click()
        await page.get_by_test_id('choice-pick-bar-go').click(); await page.get_by_test_id('choice-questions-screen').wait_for()
        await page.locator(Q).first.wait_for(timeout=20000)
        n = await page.locator(Q).count()
        say('questions: Physics chapter 1 lists 48 (dropped + bonus left out)', n == 48, n)
        body = await page.get_by_test_id('choice-question-list').inner_text()
        say('questions: never options or solutions', 'TEST_SECRET_SOLUTION' not in body and '(A)' not in body, body[:200])
        await page.locator(Q).nth(0).click(); await page.locator(Q).nth(1).click()
        await page.get_by_test_id('choice-q-chapter-TEST_PO').click(); await page.locator(Q).first.wait_for()
        img = page.locator('.ch-stem-img').first
        await img.wait_for(timeout=20000)
        ok = await page.wait_for_function("() => { const i = document.querySelector('.ch-stem-img'); return i && i.complete && i.naturalWidth > 0; }", timeout=20000)
        say('questions: numerical picture loads', bool(ok))
        say('questions: old-look MCQ words only', 'Find the force on the block.' in await page.get_by_test_id('choice-question-list').inner_text())
        await page.get_by_test_id('choice-q-subject-chemistry').click(); await page.locator(Q).first.wait_for()
        await page.locator(Q).first.click()
        say('bar: 3 / 75 sawaal', '3 / 75' in await text(page, 'choice-questions-bar-count'), await text(page, 'choice-questions-bar-count'))
        say('bar: 2P + 1C = 7 min · 12 marks', '7 min' in await text(page, 'choice-questions-bar-note') and '12 marks' in await text(page, 'choice-questions-bar-note'), await text(page, 'choice-questions-bar-note'))
        await shot(page, 'desk_questions')
        await page.get_by_test_id('choice-questions-bar-go').click(); await page.get_by_test_id('choice-review-sheet').wait_for()
        say('review: total 3 and 7 min', (await text(page, 'choice-review-makeup-total')).startswith('3') and '7 min' in await text(page, 'choice-review-makeup-time'))
        await shot(page, 'desk_review')
        await page.get_by_test_id('choice-make').click(); await page.wait_for_url(re.compile(r'/sets/'), timeout=20000)
        await page.wait_for_timeout(800); await shot(page, 'desk_after_make')
        say('make: stays on the paper page', '/sets/' in page.url and 'step=' not in page.url, page.url)
        await page.get_by_test_id('set-detail-page').wait_for()
        say('paper page: STUDENT CHOICE, 3 Q, 7 min, 12 marks', 'STUDENT CHOICE' in (await page.locator('.eyebrow').first.inner_text()).upper() and await text(page, 'set-question-count') == '3'
            and await text(page, 'set-duration') == '7' and await text(page, 'set-maximum-marks') == '12', await page.locator('.eyebrow').first.inner_text())
        say('paper page: back to Student Choice', 'Student Choice' in await text(page, 'set-back'))
        await shot(page, 'desk_paper')
        await page.get_by_test_id('set-preflight-start-button').click(); await page.wait_for_url(re.compile(r'/attempts/'), timeout=30000)
        say('start: the player opens', '/attempts/' in page.url, page.url)
        await page.wait_for_timeout(1500); await shot(page, 'desk_player')
        await page.goto(BASE + '/choice'); await page.get_by_test_id('choice-way-random').click(); await page.get_by_test_id('choice-random-sheet').wait_for()
        await page.get_by_test_id('choice-random-quick-15').click()
        say('random: 15 = 5+5+5, 36 min', (await text(page, 'choice-random-makeup-total')).startswith('15') and '36 min' in await text(page, 'choice-random-makeup-time'), await text(page, 'choice-random-makeup-time'))
        await page.get_by_test_id('choice-random-input').fill('2')
        say('random: 2 refused on screen', await page.get_by_test_id('choice-random-range').is_visible())
        await page.get_by_test_id('choice-random-input').fill('15')
        await page.get_by_test_id('choice-random-make').click(); await page.wait_for_url(re.compile(r'/sets/'), timeout=20000)
        await page.get_by_test_id('set-duration').wait_for()
        say('random paper page: 15 Q, 36 min', await text(page, 'set-question-count') == '15' and await text(page, 'set-duration') == '36')
        await page.goto(BASE + '/choice'); await page.get_by_test_id('choice-today').wait_for()
        say('choice: today 2 / 5', '2 / 5' in await text(page, 'choice-today'), await text(page, 'choice-today'))
        say('desk: no page overflow', not await page.evaluate(OVERFLOW), await page.evaluate(OVERFLOW))
        say('desk: no console errors', not logs, logs[:3])
    finally:
        await br.close()
    br, page, bad, logs = await open_as(pw, 'owner', 'desk')
    try:
        await page.goto(BASE + '/super-admin/choice'); await page.get_by_test_id('admin-choice-page').wait_for(timeout=30000)
        await page.get_by_test_id('admin-choice-stat-today').wait_for()
        say('owner: stats today 2', await text(page, 'admin-choice-stat-today') == '2', await text(page, 'admin-choice-stat-today'))
        say('owner: pool lists 7 chapters', await page.locator('[data-testid^=admin-choice-chapter-]').count() == 7)
        await shot(page, 'desk_admin')
        await page.get_by_test_id('admin-choice-pick-switch').click(); await page.get_by_test_id('admin-choice-random-switch').click()
        await page.get_by_test_id('admin-choice-save').click(); await page.wait_for_timeout(1500)
        say('owner: saved both Off (revision 2)', 'Revision 2' in await text(page, 'admin-choice-revision'), await text(page, 'admin-choice-revision'))
    finally:
        await br.close()
    br, page, bad, logs = await open_as(pw, 'riya', 'desk')
    try:
        await page.goto(BASE + '/home'); await page.get_by_test_id('exam-home-page').wait_for(timeout=30000); await page.wait_for_timeout(2500)
        say('both Off: Home has no Student Choice card', await page.get_by_test_id('home-choice-card').count() == 0)
        await page.goto(BASE + '/choice'); await page.get_by_test_id('choice-closed').wait_for(timeout=20000)
        say('both Off: /choice says closed', True)
    finally:
        await br.close()


async def mob(pw):
    async with httpx.AsyncClient(base_url=API, cookies=B['owner'], headers={'origin': BASE}) as c:
        cur = (await c.get('/api/admin/choice/jee-main')).json()['data']['settings']
        await c.put('/api/admin/choice/jee-main', json={'expected_revision': cur['revision'], 'pick': True, 'random': True, 'max_questions': 75, 'max_per_subject': None,
                                                        'minutes_per_question': {'Physics': 2.4, 'Chemistry': 1.6, 'Mathematics': 3.2}, 'daily_limit': 5})
    br, page, bad, logs = await open_as(pw, 'riya', 'mob')
    check = "() => [...document.querySelectorAll('body *')].filter(e => e.getBoundingClientRect().right > innerWidth + 1 && !e.closest('.ch-pills')).slice(0,5).map(e => (e.className && e.className.toString()) || e.tagName)"
    try:
        await page.goto(BASE + '/choice'); await page.get_by_test_id('choice-way-pick').wait_for(timeout=30000)
        say('mob: start page no sideways overflow', not await page.evaluate(check), await page.evaluate(check))
        await shot(page, 'mob_start')
        await page.get_by_test_id('choice-way-pick').click(); await page.get_by_test_id('choice-pick-screen').wait_for()
        say('mob: chapters no overflow', not await page.evaluate(check), await page.evaluate(check))
        bar = await page.get_by_test_id('choice-pick-bar').bounding_box()
        say('mob: bottom bar on screen above the tabs', bar and bar['y'] + bar['height'] <= 844 and bar['y'] > 500, bar)
        await shot(page, 'mob_chapters')
        await page.get_by_test_id('choice-chapter-TEST_PO').click(); await page.get_by_test_id('choice-pick-bar-go').click()
        await page.locator(Q).first.wait_for(timeout=20000)
        await page.wait_for_function("() => { const i = document.querySelector('.ch-stem-img'); return i && i.complete && i.naturalWidth > 0; }", timeout=20000)
        say('mob: questions no overflow', not await page.evaluate(check), await page.evaluate(check))
        await shot(page, 'mob_questions')
        await page.goto(BASE + '/choice'); await page.get_by_test_id('choice-way-random').click(); await page.get_by_test_id('choice-random-sheet').wait_for()
        box = await page.get_by_test_id('choice-random-make').bounding_box()
        say('mob: random dialog button reachable', box and box['y'] + box['height'] <= 844, box)
        await shot(page, 'mob_random')
        say('mob: no console errors', not logs, logs[:3])
    finally:
        await br.close()


async def main():
    async with async_playwright() as pw:
        for part in sys.argv[1:] or ['desk', 'mob']:
            try:
                await {'desk': desk, 'mob': mob}[part](pw)
            except Exception as e:  # noqa: BLE001
                say(f'{part}: walk finished without exception', False, repr(e)[:400])
    f = [r for r in RESULT if not r[1]]
    print(f'TOTAL {len(RESULT)} PASS {len(RESULT) - len(f)} FAIL {len(f)}')

asyncio.run(main())
