async def run_test(page, output_dir, page_url):
    try:
        import json
        from datetime import datetime, timedelta, timezone

        fx = json.loads(open('/tmp/iter43_ui_fixture.json', 'r', encoding='utf-8').read())
        uid_a = fx['uid_a']
        token_a = fx['token_a']
        token_b = fx['token_b']
        exp = (datetime.now(timezone.utc) + timedelta(minutes=29)).isoformat()

        async def handle_route(route):
            url = route.request.url
            if '/api/jl/auth/session' in url:
                await route.fulfill(status=200, content_type='application/json', body=json.dumps({"user": {"id": uid_a, "name": "TEST-RF-portrait-uiA", "phone": "7000000000", "role": "student", "pin_set": True}}))
                return
            if '/api/jl/auth/me' in url:
                await route.fulfill(status=200, content_type='application/json', body=json.dumps({"id": uid_a, "name": "TEST-RF-portrait-uiA", "phone": "7000000000", "role": "student", "pin_set": True}))
                return
            if '/api/jl/auth/refresh' in url:
                await route.fulfill(status=200, content_type='application/json', body=json.dumps({"ok": True}))
                return
            if '/api/rf/access' in url:
                await route.fulfill(status=200, content_type='application/json', body=json.dumps({"token": token_a, "user_id": uid_a, "expires_at": exp}))
                return
            await route.continue_()

        await page.route('**/*', handle_route)
        await page.set_viewport_size({"width": 390, "height": 844})
        await page.goto('https://jeelive-mobile.preview.emergentagent.com', wait_until='domcontentloaded', timeout=60000)
        await page.wait_for_selector('[data-testid="tab-rapid"]', timeout=30000)
        await page.click('[data-testid="tab-rapid"]', force=True)
        await page.wait_for_selector('[data-testid="rapid-fire-home"]', timeout=30000)
        await page.wait_for_function("""() => /\d+\s+quick-recall\s+cards/i.test(document.querySelector('[data-testid="rf-session-summary"]')?.textContent||'')""", timeout=30000)
        await page.screenshot(path='/app/test_reports/artifacts/iter43_ui_fixture_a_fast/automation_output/20261027_074148_687b3d2fa56c/lobby_390.jpeg', type="jpeg", quality=40, full_page=False)

        await page.click('[data-testid="rf-play-now"]', force=True)
        await page.wait_for_selector('[data-testid="rf-play-sheet"]', timeout=10000)
        await page.click('[data-testid="rf-start-button"]', force=True)
        await page.wait_for_selector('[data-testid="rf-option-0"]', timeout=20000)
        print(f'Counter start: {await page.locator("[data-testid=rf-card-counter]").inner_text()}')
        print(f'Formula before answer: {await page.locator("[data-testid=rf-card-formula]").count()}')
        await page.click('[data-testid="rf-option-0"]', force=True)
        await page.wait_for_selector('[data-testid="rf-feedback"]', timeout=8000)
        print(f'Formula after answer: {await page.locator("[data-testid=rf-card-formula]").count()}')
        await page.screenshot(path='/app/test_reports/artifacts/iter43_ui_fixture_a_fast/automation_output/20261027_074148_687b3d2fa56c/card_390.jpeg', type="jpeg", quality=40, full_page=False)

        await page.click('[data-testid="rf-exit-button"]', force=True)
        await page.wait_for_selector('[data-testid="rf-exit-sheet"]', timeout=8000)
        await page.click('[data-testid="rf-exit-finish"]', force=True)
        await page.wait_for_selector('[data-testid="rf-summary"]', timeout=25000)
        await page.screenshot(path='/app/test_reports/artifacts/iter43_ui_fixture_a_fast/automation_output/20261027_074148_687b3d2fa56c/summary_390.jpeg', type="jpeg", quality=40, full_page=False)

        await page.click('[data-testid="rf-start-another"]', force=True)
        await page.wait_for_selector('[data-testid="rf-card-counter"]', timeout=15000)
        print(f'Counter play-again: {await page.locator("[data-testid=rf-card-counter]").inner_text()}')
        await page.click('[data-testid="rf-exit-button"]', force=True)
        await page.wait_for_selector('[data-testid="rf-exit-sheet"]', timeout=8000)
        await page.click('[data-testid="rf-exit-discard"]', force=True)
        await page.wait_for_selector('[data-testid="rapid-fire-home"]', timeout=15000)

        await page.click('[data-testid="rf-duel-invite"]', force=True)
        await page.wait_for_selector('[data-testid="duel-invite-card"]', timeout=25000)
        code = (await page.locator('[data-testid="duel-code"]').inner_text()).strip()
        joined = await page.evaluate("""async ({code, token_b}) => {
          const r = await fetch('/api/rf/duels/join', {method:'POST', headers:{'Content-Type':'application/json','Authorization':'Bearer '+token_b}, body: JSON.stringify({code, name:'TEST-B', exam:'JEE'})});
          const j = await r.json().catch(()=>({}));
          return {status:r.status, id:j.id||null};
        }""", {"code": code, "token_b": token_b})
        print(f'Join status: {joined["status"]}')
        duel_id = joined['id']

        await page.wait_for_timeout(9000)
        if await page.locator('[data-testid="duel-countdown"]').count() > 0:
            await page.wait_for_timeout(6000)
        await page.wait_for_selector('[data-testid="duel-play"]', timeout=30000)
        await page.screenshot(path='/app/test_reports/artifacts/iter43_ui_fixture_a_fast/automation_output/20261027_074148_687b3d2fa56c/duel_live_390.jpeg', type="jpeg", quality=40, full_page=False)
        await page.click('[data-testid="duel-option-0"]', force=True)
        await page.wait_for_timeout(1000)

        if duel_id:
            await page.evaluate("""async ({duel_id, token_a, token_b}) => {
              for (let i=1;i<30;i++) {
                const a = await fetch(`/api/rf/duels/${duel_id}/answer`, {method:'POST', headers:{'Content-Type':'application/json','Authorization':'Bearer '+token_a}, body: JSON.stringify({index:i, choice:null, outcome:'skipped', ms:800})});
                const b = await fetch(`/api/rf/duels/${duel_id}/answer`, {method:'POST', headers:{'Content-Type':'application/json','Authorization':'Bearer '+token_b}, body: JSON.stringify({index:i, choice:null, outcome:'skipped', ms:900})});
                if (a.status!==200 || b.status!==200) break;
              }
            }""", {"duel_id": duel_id, "token_a": token_a, "token_b": token_b})

        await page.wait_for_selector('[data-testid="duel-result"]', timeout=45000)
        await page.screenshot(path='/app/test_reports/artifacts/iter43_ui_fixture_a_fast/automation_output/20261027_074148_687b3d2fa56c/duel_result_390.jpeg', type="jpeg", quality=40, full_page=False)
        await page.click('[data-testid="duel-done"]', force=True)
        await page.wait_for_selector('[data-testid="rapid-fire-home"]', timeout=20000)

        await page.click('[data-testid="rf-friends-history"]', force=True)
        await page.wait_for_selector('[data-testid="rf-history-screen"]', timeout=20000)
        await page.wait_for_timeout(1000)
        await page.screenshot(path='/app/test_reports/artifacts/iter43_ui_fixture_a_fast/automation_output/20261027_074148_687b3d2fa56c/history_390.jpeg', type="jpeg", quality=40, full_page=False)

        # Get error messages using specific selectors
        error_text = await page.evaluate("""() => {
        const errorElements = Array.from(document.querySelectorAll('.error, [class*="error"], [id*="error"]'));
        return errorElements.map(el => el.textContent).join(', ');
        }""")
        if error_text:
            print(f"Found error message: {error_text}")
        else:
            print("No error messages found on the page")

    except Exception as e:
        print(f'Iter43 fixture A fast failed: {str(e)}')
        await page.screenshot(path='/app/test_reports/artifacts/iter43_ui_fixture_a_fast/automation_output/20261027_074148_687b3d2fa56c/fixture_a_fast_error.jpeg', type="jpeg", quality=40, full_page=False)

