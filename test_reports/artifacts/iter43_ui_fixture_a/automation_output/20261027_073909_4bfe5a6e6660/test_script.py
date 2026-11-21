async def run_test(page, output_dir, page_url):
    try:
        import json
        from datetime import datetime, timedelta, timezone

        fx = json.loads(open('/tmp/iter43_ui_fixture.json', 'r', encoding='utf-8').read())
        uid_a = fx['uid_a']
        token_a = fx['token_a']
        uid_b = fx['uid_b']
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
            if '/api/rf/access' in url:
                await route.fulfill(status=200, content_type='application/json', body=json.dumps({"token": token_a, "user_id": uid_a, "expires_at": exp}))
                return
            await route.continue_()

        await page.route('**/*', handle_route)
        await page.set_viewport_size({"width": 390, "height": 844})
        print('Step 1: Open app')
        await page.goto('https://rapid-fire-208--04cp9c5d.preview.emergentagent.com', wait_until='domcontentloaded', timeout=60000)
        await page.wait_for_selector('[data-testid="tab-rapid"]', timeout=30000)
        await page.click('[data-testid="tab-rapid"]', force=True)
        await page.wait_for_selector('[data-testid="rapid-fire-home"]', timeout=30000)
        await page.wait_for_function("""() => {
          const n = document.querySelector('[data-testid="rf-session-summary"]')?.textContent || '';
          const btn = document.querySelector('[data-testid="rf-play-now"]');
          const disabled = btn?.getAttribute('aria-disabled') === 'true';
          return /\d+\s+quick-recall\s+cards/i.test(n) && !disabled;
        }""", timeout=30000)
        art_loaded = await page.evaluate("""() => {
          const host = document.querySelector('[data-testid="rf-original-emblem"]');
          if (!host) return false;
          const img = host.querySelector('img');
          if (!img) return true;
          return img.naturalWidth > 0;
        }""")
        print(f'Original art loaded: {art_loaded}')
        await page.screenshot(path='/app/test_reports/artifacts/iter43_ui_fixture_a/automation_output/20261027_073909_4bfe5a6e6660/lobby_390.jpeg', type="jpeg", quality=40, full_page=False)

        print('Step 2: Start solo session and validate 30/20 contract UI')
        await page.click('[data-testid="rf-play-now"]', force=True)
        await page.wait_for_selector('[data-testid="rf-play-sheet"]', timeout=10000)
        await page.click('[data-testid="rf-start-button"]', force=True)
        await page.wait_for_selector('[data-testid="rf-session-screen"]', timeout=20000)
        await page.wait_for_selector('[data-testid="rf-card-counter"]', timeout=20000)
        counter = await page.locator('[data-testid="rf-card-counter"]').inner_text()
        print(f'Counter text: {counter}')
        formula_before = await page.locator('[data-testid="rf-card-formula"]').count()
        print(f'Formula count before answer: {formula_before}')

        found_diagram = False
        for _ in range(14):
            has_diagram = await page.evaluate("""() => {
              const host = document.querySelector('[data-testid="rf-card-diagram"]');
              if (!host) return false;
              return !!host.querySelector('svg,img,canvas,path,g,polygon,circle,ellipse,line,rect,text');
            }""")
            if has_diagram:
                found_diagram = True
                await page.screenshot(path='/app/test_reports/artifacts/iter43_ui_fixture_a/automation_output/20261027_073909_4bfe5a6e6660/diagram_390.jpeg', type="jpeg", quality=40, full_page=False)
                break
            await page.click('[data-testid="rf-skip-button"]', force=True)
            await page.wait_for_timeout(800)
        print(f'Diagram found in solo: {found_diagram}')

        await page.click('[data-testid="rf-option-0"]', force=True)
        await page.wait_for_selector('[data-testid="rf-feedback"]', timeout=8000)
        formula_after = await page.locator('[data-testid="rf-card-formula"]').count()
        print(f'Formula count after answer: {formula_after}')
        await page.screenshot(path='/app/test_reports/artifacts/iter43_ui_fixture_a/automation_output/20261027_073909_4bfe5a6e6660/card_feedback_390.jpeg', type="jpeg", quality=40, full_page=False)

        await page.wait_for_selector('[data-testid="rf-skip-button"]', timeout=5000)
        await page.click('[data-testid="rf-skip-button"]', force=True)
        await page.wait_for_timeout(1200)
        print('Skip action completed')

        print('Step 3: Timeout behavior check (single card)')
        await page.wait_for_timeout(21000)
        timeout_visible = await page.locator('[data-testid="rf-feedback"]').count()
        if timeout_visible > 0:
            txt = await page.locator('[data-testid="rf-feedback"]').first.inner_text()
            print(f'Timeout feedback: {txt}')

        await page.click('[data-testid="rf-exit-button"]', force=True)
        await page.wait_for_selector('[data-testid="rf-exit-sheet"]', timeout=8000)
        await page.click('[data-testid="rf-exit-finish"]', force=True)
        await page.wait_for_selector('[data-testid="rf-summary"]', timeout=30000)
        await page.screenshot(path='/app/test_reports/artifacts/iter43_ui_fixture_a/automation_output/20261027_073909_4bfe5a6e6660/solo_summary_390.jpeg', type="jpeg", quality=40, full_page=False)

        print('Step 4: Start another session must reset to card 1')
        await page.click('[data-testid="rf-start-another"]', force=True)
        await page.wait_for_selector('[data-testid="rf-session-screen"]', timeout=15000)
        await page.wait_for_selector('[data-testid="rf-card-counter"]', timeout=15000)
        counter2 = await page.locator('[data-testid="rf-card-counter"]').inner_text()
        print(f'Counter after play-again: {counter2}')
        await page.click('[data-testid="rf-exit-button"]', force=True)
        await page.wait_for_selector('[data-testid="rf-exit-sheet"]', timeout=8000)
        await page.click('[data-testid="rf-exit-discard"]', force=True)
        await page.wait_for_selector('[data-testid="rapid-fire-home"]', timeout=15000)

        print('Step 5: Duel invite A and join B via real API')
        await page.click('[data-testid="rf-duel-invite"]', force=True)
        await page.wait_for_selector('[data-testid="duel-invite-card"]', timeout=25000)
        code = (await page.locator('[data-testid="duel-code"]').inner_text()).strip()
        print(f'Duel code: {code}')

        join_resp = await page.evaluate("""async ({code, token_b}) => {
          const r = await fetch('/api/rf/duels/join', {
            method: 'POST',
            headers: {'Content-Type':'application/json', 'Authorization': 'Bearer ' + token_b},
            body: JSON.stringify({code, name:'TEST-B', exam:'JEE'})
          });
          const j = await r.json().catch(() => ({}));
          return {status: r.status, body: j};
        }""", {"code": code, "token_b": token_b})
        print(f'Join response status: {join_resp["status"]}')

        await page.wait_for_timeout(7000)
        if await page.locator('[data-testid="duel-countdown"]').count() > 0:
          await page.wait_for_timeout(6000)
        await page.wait_for_selector('[data-testid="duel-play"]', timeout=30000)
        await page.screenshot(path='/app/test_reports/artifacts/iter43_ui_fixture_a/automation_output/20261027_073909_4bfe5a6e6660/duel_live_390.jpeg', type="jpeg", quality=40, full_page=False)

        duel_id = await page.evaluate("""async ({token_a}) => {
          const r = await fetch('/api/rf/duels?exam=JEE&friends_only=true', {headers:{'Authorization':'Bearer '+token_a}});
          const j = await r.json();
          const first = (j.items||[])[0] || {};
          return first.id || null;
        }""", {"token_a": token_a})
        print(f'Duel id from history lookup: {duel_id}')

        await page.click('[data-testid="duel-option-0"]', force=True)
        await page.wait_for_timeout(1200)

        if duel_id:
          await page.evaluate("""async ({duel_id, token_a, token_b}) => {
            for (let i=1;i<30;i++) {
              const pa = await fetch(`/api/rf/duels/${duel_id}/answer`, {
                method:'POST', headers:{'Content-Type':'application/json','Authorization':'Bearer '+token_a},
                body: JSON.stringify({index:i, choice:null, outcome:'skipped', ms:1000})
              });
              if (pa.status !== 200) break;
              const pb = await fetch(`/api/rf/duels/${duel_id}/answer`, {
                method:'POST', headers:{'Content-Type':'application/json','Authorization':'Bearer '+token_b},
                body: JSON.stringify({index:i, choice:null, outcome:'skipped', ms:1000})
              });
              if (pb.status !== 200) break;
            }
          }""", {"duel_id": duel_id, "token_a": token_a, "token_b": token_b})

        await page.wait_for_timeout(4000)
        await page.wait_for_selector('[data-testid="duel-result"]', timeout=30000)
        await page.screenshot(path='/app/test_reports/artifacts/iter43_ui_fixture_a/automation_output/20261027_073909_4bfe5a6e6660/duel_result_390.jpeg', type="jpeg", quality=40, full_page=False)
        await page.click('[data-testid="duel-done"]', force=True)
        await page.wait_for_selector('[data-testid="rapid-fire-home"]', timeout=20000)

        print('Step 6: Friends history populated and review-only open')
        await page.click('[data-testid="rf-friends-history"]', force=True)
        await page.wait_for_selector('[data-testid="rf-history-screen"]', timeout=20000)
        await page.wait_for_timeout(1500)
        await page.screenshot(path='/app/test_reports/artifacts/iter43_ui_fixture_a/automation_output/20261027_073909_4bfe5a6e6660/history_390.jpeg', type="jpeg", quality=40, full_page=False)

        match_count = await page.locator('[data-testid^="rf-history-match-"]').count()
        print(f'History match count: {match_count}')
        if match_count > 0:
          await page.locator('[data-testid^="rf-history-match-"]').first.click(force=True)
          await page.wait_for_timeout(2000)
          if await page.locator('[data-testid="duel-result"]').count() > 0:
              print('History tap reopened existing duel result')
          await page.go_back()
          await page.wait_for_selector('[data-testid="rf-history-screen"]', timeout=15000)

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
        print(f'Iter43 fixture A UI flow failed: {str(e)}')
        await page.screenshot(path='/app/test_reports/artifacts/iter43_ui_fixture_a/automation_output/20261027_073909_4bfe5a6e6660/fixture_a_error.jpeg', type="jpeg", quality=40, full_page=False)

