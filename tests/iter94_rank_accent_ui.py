# Iteration 94 — Rank tab tool colours + College Predictor cards (run via browser_automation; body of async fn with `page`).
# Login: type phone/PIN with keyboard (page.fill on entry fields does not enable submit reliably).
BASE = "https://share-card-stats--1s9i9qdg.preview.emergentagent.com"
EXPECT = {"rank": ("rp-input", "rp-show", "rgb(255, 214, 10)"), "pct": ("pr-input", "pr-show", "rgb(45, 225, 194)"),
          "target": ("tm-profile", None, "rgb(181, 242, 61)"), "college": ("rank-input", "rank-show", "rgb(255, 79, 174)"),
          "compare": ("cmp-empty", "cmp-go-college", "rgb(76, 195, 255)")}
CSS = """([t]) => { const el=document.querySelector(`[data-testid="${t}"]`); if(!el) return null; const s=getComputedStyle(el); return {bg:s.backgroundColor, bc:s.borderTopColor}; }"""

await page.set_viewport_size({"width": 390, "height": 844})
await page.goto(BASE + "/entry")
await page.wait_for_selector('[data-testid="entry-phone-input"]', timeout=30000)
await page.wait_for_timeout(2500)
await page.click('[data-testid="entry-phone-input"]'); await page.keyboard.type("7004186276", delay=30)
await page.click('[data-testid="entry-pin-input"]'); await page.keyboard.type("5524", delay=30)
await page.click('[data-testid="entry-continue-button"]'); await page.wait_for_timeout(6000)
await page.get_by_text("RANK", exact=True).first.click()
await page.wait_for_selector('[data-testid="rank-tool-rank"]', timeout=30000)
for tool, (form, btn, ink) in EXPECT.items():
    await page.click(f'[data-testid="rank-tool-{tool}"]', force=True); await page.wait_for_timeout(1000)
    head = await page.evaluate(CSS, [f"{form}-head"])
    print(tool, "HEAD OK" if head and head["bg"] == ink else f"HEAD FAIL {head}")
    if btn:
        b = await page.evaluate(CSS, [btn]); print(tool, "BTN OK" if b and b["bg"] == ink else f"BTN FAIL {b}")
# College predictor cards
await page.click('[data-testid="rank-tool-college"]', force=True)
await page.fill('[data-testid="rank-marks-input"]', "180"); await page.click('[data-testid="rank-show"]', force=True)
await page.wait_for_selector('[data-testid="rank-seat-0"]', timeout=30000)
await page.click('[data-testid="rank-seat-1-star"]', force=True); await page.wait_for_timeout(800)
print("star no sheet:", await page.locator('[data-testid="rank-college"]').count() == 0)
await page.click('[data-testid="rank-seat-1-star"]', force=True)  # unstar (cleanup)
await page.click('[data-testid="rank-seat-0"]', force=True); await page.wait_for_selector('[data-testid="rank-college"]')
await page.keyboard.press("Escape"); await page.wait_for_timeout(1000)
print("viewed:", await page.locator('[data-testid="rank-seat-0-viewed"]').count() == 1)
