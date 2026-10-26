async def run_test(page, output_dir, page_url):
    page.on("console", lambda msg: print(f"CONSOLE: {msg.type}: {msg.text}"))

    try:
        await page.set_viewport_size({"width": 390, "height": 844})
        await page.wait_for_timeout(800)
        if await page.locator('[data-testid="entry-phone-input"]').count() > 0:
            await page.fill('[data-testid="entry-phone-input"]', '9000000001')
            await page.click('[data-testid="entry-continue-button"]', force=True)
            await page.wait_for_timeout(1800)

        fixture_catalogue = {
            "items": [
                {"id": "fixture-new", "year": 2024, "exam_date": "2024-01-27", "shift": 1, "count": 90, "minutes": 180, "maximum": 300, "attempt": None, "latest_result_id": None, "attempt_count": 0},
                {"id": "fixture-active", "year": 2024, "exam_date": "2024-01-29", "shift": 2, "count": 90, "minutes": 180, "maximum": 300, "attempt": {"id": "att-active-1", "status": "active"}, "latest_result_id": "res-old-1", "attempt_count": 1},
                {"id": "fixture-completed", "year": 2023, "exam_date": "2023-04-11", "shift": 1, "count": 90, "minutes": 180, "maximum": 300, "attempt": {"id": "att-completed-1", "status": "completed"}, "latest_result_id": "res-completed-1", "attempt_count": 2},
                {"id": "fixture-expired", "year": 2022, "exam_date": "2022-07-23", "shift": 2, "count": 90, "minutes": 180, "maximum": 300, "attempt": {"id": "att-expired-1", "status": "expired"}, "latest_result_id": "res-expired-1", "attempt_count": 2},
                {"id": "fixture-grading", "year": 2021, "exam_date": "2021-02-24", "shift": 1, "count": 90, "minutes": 180, "maximum": 300, "attempt": {"id": "att-grading-1", "status": "grading"}, "latest_result_id": None, "attempt_count": 1},
                {"id": "fixture-unavailable", "year": 2020, "exam_date": "2020-09-03", "shift": 1, "count": 0, "minutes": 180, "maximum": 300, "attempt": None, "latest_result_id": None, "attempt_count": 0, "live_enabled": False},
                {"id": "fixture-failstart", "year": 2019, "exam_date": "2019-01-12", "shift": 1, "count": 90, "minutes": 180, "maximum": 300, "attempt": None, "latest_result_id": None, "attempt_count": 0}
            ],
            "years": [2024, 2023, 2022, 2021, 2020, 2019],
            "total": 7,
            "source_note": "TEST FIXTURE ONLY"
        }

        start_calls = {"fixture-new": 0, "fixture-completed": 0, "fixture-failstart": 0}
        preflight_calls = {"fixture-new": 0, "fixture-completed": 0, "fixture-failstart": 0}
        start_keys = []

        import json

        async def route_handler(route, request):
            url = request.url
            method = request.method

            if '/api/jl/pyq/jee-main' in url and method == 'GET':
                await route.fulfill(status=200, content_type='application/json', body=json.dumps({"data": fixture_catalogue, "error": None, "meta": {"api_version": "1"}}))
                return

            if '/api/jl/my/sets/' in url and method == 'GET':
                await route.fulfill(status=200, content_type='application/json', body='{"data":{"attempt":null,"live_enabled":true},"error":null,"meta":{"api_version":"1"}}')
                return

            if '/api/jl/sets/' in url and '/preflight' in url and method == 'POST':
                for k in preflight_calls.keys():
                    if f'/{k}/' in url:
                        preflight_calls[k] += 1
                await route.fulfill(status=200, content_type='application/json', body='{"data":{"ok":true},"error":null,"meta":{"api_version":"1"}}')
                return

            if '/api/jl/sets/' in url and '/start' in url and method == 'POST':
                body_data = request.post_data_json or {}
                if '/fixture-new/' in url:
                    start_calls['fixture-new'] += 1
                    await route.fulfill(status=200, content_type='application/json', body='{"data":{"id":"attempt-new-1","status":"active"},"error":null,"meta":{"api_version":"1"}}')
                    return
                if '/fixture-completed/' in url:
                    start_calls['fixture-completed'] += 1
                    await route.fulfill(status=200, content_type='application/json', body='{"data":{"id":"attempt-reattempt-1","status":"active"},"error":null,"meta":{"api_version":"1"}}')
                    return
                if '/fixture-failstart/' in url:
                    start_calls['fixture-failstart'] += 1
                    start_keys.append(body_data.get('start_key'))
                    if start_calls['fixture-failstart'] == 1:
                        await route.fulfill(status=503, content_type='application/json', body='{"error":{"message":"temporary upstream timeout"}}')
                        return
                    await route.fulfill(status=200, content_type='application/json', body='{"data":{"id":"attempt-failstart-1","status":"active"},"error":null,"meta":{"api_version":"1"}}')
                    return

            if '/api/jl/attempts/' in url and method == 'GET':
                aid = url.split('/api/jl/attempts/')[-1].split('?')[0]
                payload = {"data": {"id": aid, "status": "active", "title": f"Fixture Attempt {aid}", "server_now": 1793008777, "deadline": None, "rules": {}, "questions": [{"id": "q1", "number": 1, "type": "single", "subject": "Physics", "options": {"A": "1", "B": "2", "C": "3", "D": "4"}, "asset_count": 0, "render_mode": "text", "text": "Fixture question"}], "answers": {}, "visited": [], "confidence_observations": {}}, "error": None, "meta": {"api_version": "1"}}
                await route.fulfill(status=200, content_type='application/json', body=json.dumps(payload))
                return

            if '/api/jl/attempts/' in url and ('/visit' in url or '/submit' in url or '/answers/' in url):
                await route.fulfill(status=200, content_type='application/json', body='{"data":{"server_now":1793008777,"accepted":{"revision":1},"current_revision":1,"visited":[]},"error":null,"meta":{"api_version":"1"}}')
                return

            await route.continue_()

        await page.route('**/*', route_handler)
        await page.goto('https://jeelive-mobile.preview.emergentagent.com/pyq')
        await page.wait_for_selector('[data-testid="pyq-paper-fixture-new"]', timeout=12000)

        assert await page.locator('[data-testid="pyq-start-button-fixture-new"]').count() > 0
        assert await page.locator('[data-testid="pyq-continue-button-fixture-active"]').count() > 0
        assert await page.locator('[data-testid="pyq-result-button-fixture-completed"]').count() > 0
        assert await page.locator('[data-testid="pyq-reattempt-button-fixture-completed"]').count() > 0

        await page.locator('[data-testid="pyq-paper-fixture-grading"]').scroll_into_view_if_needed()
        await page.wait_for_timeout(300)
        await page.locator('[data-testid="pyq-paper-fixture-unavailable"]').scroll_into_view_if_needed()
        await page.wait_for_timeout(300)

        grading_wait_count = await page.locator('[data-testid="pyq-awaiting-result-fixture-grading"]').count()
        unavailable_start_count = await page.locator('[data-testid="pyq-start-button-fixture-unavailable"]').count()
        print(f"grading wait label count: {grading_wait_count}")
        print(f"unavailable start button count: {unavailable_start_count}")

        # one-tap start for new
        await page.locator('[data-testid="pyq-paper-fixture-new"]').scroll_into_view_if_needed()
        await page.click('[data-testid="pyq-start-button-fixture-new"]', force=True)
        await page.wait_for_url('**/attempt/attempt-new-1', timeout=8000)
        assert start_calls['fixture-new'] == 1 and preflight_calls['fixture-new'] == 1

        await page.go_back()
        await page.wait_for_selector('[data-testid="pyq-screen"]', timeout=10000)

        # continue path should not start
        before_start = dict(start_calls)
        await page.click('[data-testid="pyq-continue-button-fixture-active"]', force=True)
        await page.wait_for_url('**/attempt/att-active-1', timeout=8000)
        assert start_calls == before_start

        await page.go_back()
        await page.wait_for_selector('[data-testid="pyq-screen"]', timeout=10000)

        # tap spam on reattempt
        await page.locator('[data-testid="pyq-paper-fixture-completed"]').scroll_into_view_if_needed()
        await page.click('[data-testid="pyq-reattempt-button-fixture-completed"]', force=True)
        await page.click('[data-testid="pyq-reattempt-button-fixture-completed"]', force=True)
        await page.wait_for_timeout(900)
        assert start_calls['fixture-completed'] == 1

        await page.go_back()
        await page.wait_for_selector('[data-testid="pyq-screen"]', timeout=10000)

        # failed start and same-key retry
        await page.locator('[data-testid="pyq-paper-fixture-failstart"]').scroll_into_view_if_needed()
        await page.click('[data-testid="pyq-start-button-fixture-failstart"]', force=True)
        await page.wait_for_timeout(1000)
        await page.click('[data-testid="pyq-start-button-fixture-failstart"]', force=True)
        await page.wait_for_timeout(1000)

        assert start_calls['fixture-failstart'] == 2
        assert len(start_keys) == 2 and start_keys[0] == start_keys[1]
        print("retry key persisted across failed->retry start")

        await page.screenshot(path='/app/test_reports/artifacts_iter32/automation_output/20261026_100255_024bf34ca9b2/fixture_pyq_states.jpeg', type="jpeg", quality=40, full_page=False)

        error_text = await page.evaluate("""() => {
        const errorElements = Array.from(document.querySelectorAll('.error, [class*="error"], [id*="error"]'));
        return errorElements.map(el => el.textContent).join(", ");
        }""")
        if error_text:
            print(f"Found error message: {error_text}")
        else:
            print("No error messages found on the page")

        print("Fixture flow pass")

    except Exception as e:
        print(f"Fixture flow failed: {str(e)}")
        await page.screenshot(path='/app/test_reports/artifacts_iter32/automation_output/20261026_100255_024bf34ca9b2/fixture_flow_error_retry.jpeg', type="jpeg", quality=40, full_page=False)

