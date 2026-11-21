# iteration_127 login helper (paste into browser_automation): robust QA learner sign-in on /entry
await page.set_viewport_size({"width": 390, "height": 844})
await page.wait_for_selector('[data-testid="entry-phone-input"]', timeout=30000)
await page.wait_for_timeout(3000)
for sel, val in (('[data-testid="entry-phone-input"]', "7004186276"), ('[data-testid="entry-pin-input"]', "5524")):
    await page.click(sel); await page.keyboard.type(val, delay=60)
    if not (await page.input_value(sel)):
        await page.fill(sel, val)
await page.wait_for_timeout(800)
await page.click('[data-testid="entry-continue-button"]', force=True)
await page.wait_for_timeout(7000)
print("after login", page.url)
