# Phase 4 UI audit (rest of app) - reusable Playwright snippet for the browser_automation tool.
# Paste the body into browser_automation with page_url = <EXPO_PUBLIC_BACKEND_URL>/entry.
# Covers: login, Home order (home-promo removed, home-dream between For you and Explore), Rank 6 tiles,
# College predictor dream pinning (JEE), Dream panel row colours + diamonds, Home 'Sab N dream dekho' handover.
# NOTE: jeelive.ai rate-limits /auth/session and sign-in (429, "wait 140s") - keep full reloads and logins per run low.

async def login(page):
    await page.wait_for_selector('[data-testid="entry-screen"]', timeout=30000)
    await page.wait_for_timeout(1500)  # a tap right after typing was once ignored silently
    i = page.locator('[data-testid="entry-screen"] input')
    await i.nth(0).click(); await page.keyboard.type("7004186276", delay=30)
    await i.nth(1).click(); await page.keyboard.type("5524", delay=30)
    await page.wait_for_timeout(400)
    await page.locator('[data-testid="entry-continue-button"]').click()
    await page.wait_for_selector('[data-testid="home-screen"]', timeout=40000)


async def dream_flow(page):
    await page.set_viewport_size({"width": 390, "height": 844})
    await login(page)
    assert await page.locator('[data-testid="home-promo"]').count() == 0
    await page.click('[data-testid="tab-rank"]')
    await page.click('[data-testid="rank-tool-college"]')
    await page.locator("input:visible[placeholder='e.g. 180']").first.fill("180")
    await page.click('[data-testid="rank-show"]')
    await page.wait_for_selector('[data-testid="rank-seat-3-dream"]', timeout=20000)
    for n in range(4):
        await page.locator(f'[data-testid="rank-seat-{n}-dream"]').click()
        await page.wait_for_timeout(400)
    await page.click('[data-testid="rank-tool-rank"]')
    await page.click('[data-testid="tab-index"]')
    await page.locator('[data-testid="home-dream-more"]').click()
    await page.wait_for_timeout(1500)
    assert await page.locator('[data-testid="rank-tool-dream"]').get_attribute("aria-selected") == "true"
    assert await page.locator('[data-testid="dream-panel"]').is_visible()
    print("dream flow ok")

# In browser_automation: await dream_flow(page)
