"""Iter118 B1: grow the weak list via one Solo Sprint PCM round and then verify the
Weak-cards sheet organisation. We play ALL 30 cards with ~14 wrong deliberately,
1 skip, 1 timeout. We reuse the signed-in storage state."""
import asyncio, json, os, re, time
from playwright.async_api import async_playwright

STORAGE = "/tmp/iter116_storage_state.json"
BASE = "https://scale-engine-50k--0gu36hlx.preview.emergentagent.com"
ART = "/app/test_reports/artifacts_iter118"
os.makedirs(ART, exist_ok=True)

async def main():
    results = {"console_errors": [], "api_errors": [], "steps": []}
    cards_payload = None

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        ctx = await browser.new_context(storage_state=STORAGE, viewport={"width": 390, "height": 844})
        page = await ctx.new_page()

        def on_console(msg):
            if msg.type == "error":
                txt = msg.text[:200]
                if "favicon" not in txt.lower():
                    results["console_errors"].append(txt)

        async def on_response(resp):
            try:
                if "/api/rf" in resp.url and resp.status >= 400:
                    results["api_errors"].append(f"{resp.status} {resp.url}")
            except Exception:
                pass

        page.on("console", on_console)
        page.on("response", lambda r: asyncio.create_task(on_response(r)))

        # Capture the session cards
        async def on_resp2(resp):
            nonlocal cards_payload
            try:
                if "/api/rf/sessions" in resp.url and resp.request.method == "POST" and resp.status == 200:
                    j = await resp.json()
                    if "cards" in j and cards_payload is None:
                        cards_payload = j
            except Exception:
                pass
        page.on("response", lambda r: asyncio.create_task(on_resp2(r)))

        # 1) Lobby
        await page.goto(f"{BASE}/rapid", wait_until="domcontentloaded")
        await page.wait_for_timeout(8000)
        # Close rf-daily-popup if present
        try:
            exit_btn = page.get_by_role("button", name=re.compile("EXIT", re.I))
            if await exit_btn.count() > 0:
                await exit_btn.first.click(force=True)
                await page.wait_for_timeout(600)
        except Exception:
            pass

        await page.screenshot(path=f"{ART}/00_lobby.jpeg", quality=40, full_page=False)

        # Capture badge before
        try:
            badge_before = (await page.locator('[data-testid="rf-weak-cards-badge"]').first.inner_text()).strip()
        except Exception:
            badge_before = "N/A"
        results["badge_before"] = badge_before
        results["steps"].append(f"badge_before={badge_before}")

        # 2) Solo Sprint tile
        try:
            await page.locator('[data-testid="rf-start-button"]').first.click(force=True)
            await page.wait_for_timeout(800)
            await page.locator('[data-testid="rf-scope-pcm"]').first.click(force=True)
            await page.wait_for_timeout(400)
            await page.locator('[data-testid="rf-scope-done"]').first.click(force=True)
        except Exception as e:
            results["steps"].append(f"start-solo-FAIL: {e}")
            await page.screenshot(path=f"{ART}/err_start.jpeg", quality=40, full_page=False)
            await browser.close()
            print(json.dumps(results, indent=2))
            return

        # Wait for session page
        try:
            await page.wait_for_selector('[data-testid="rf-card-counter"]', timeout=15000)
        except Exception as e:
            results["steps"].append(f"session-load-FAIL: {e}")
            await page.screenshot(path=f"{ART}/err_session.jpeg", quality=40, full_page=False)
            await browser.close()
            print(json.dumps(results, indent=2))
            return
        await page.wait_for_timeout(1500)

        if not cards_payload:
            # try reading via evaluate from network — fallback
            results["steps"].append("cards_payload missing after session start")
        else:
            cards = cards_payload.get("cards", [])
            results["session_cards_count"] = len(cards)
            # subjects tally
            from collections import Counter
            subj_counter = Counter(c.get("subject") for c in cards)
            results["session_subject_counts"] = dict(subj_counter)

        # 3) Play 30 cards — strategy: alternate right/wrong to achieve ~14 wrong
        # Plan: idx 0: skip; idx 1: timeout; idx 2..15: wrong (14); idx 16..29: right (14)
        tally = {"correct": 0, "incorrect": 0, "skipped": 0, "timeout": 0}
        cards = cards_payload.get("cards", []) if cards_payload else []

        for i in range(30):
            try:
                # Wait for card counter to show i+1
                await page.wait_for_function(
                    f"() => document.querySelector('[data-testid=\"rf-card-counter\"]')?.textContent?.includes('Card {i+1} of')",
                    timeout=25000
                )
            except Exception:
                results["steps"].append(f"card_{i+1}_wait_FAIL")
                break

            if i >= len(cards):
                results["steps"].append(f"card_{i+1}_no_payload")
                break
            right_idx = cards[i].get("answer")

            try:
                if i == 0:
                    # skip
                    await page.wait_for_timeout(400)
                    await page.locator('[data-testid="rf-skip-button"]').first.click(force=True)
                    tally["skipped"] += 1
                elif i == 1:
                    # timeout - wait 21s
                    await page.wait_for_timeout(21000)
                    tally["timeout"] += 1
                elif i < 16:
                    # wrong: pick an option other than right_idx
                    wrong_idx = (right_idx + 1) % 4
                    await page.wait_for_timeout(400)
                    await page.locator(f'[data-testid="rf-option-{wrong_idx}"]').first.click(force=True)
                    tally["incorrect"] += 1
                else:
                    # right
                    await page.wait_for_timeout(400)
                    await page.locator(f'[data-testid="rf-option-{right_idx}"]').first.click(force=True)
                    tally["correct"] += 1
            except Exception as e:
                results["steps"].append(f"card_{i+1}_action_FAIL: {e}")
                break

            # wait for auto-advance (~1s right, ~2.4s wrong/timeout)
            await page.wait_for_timeout(2800)

        results["play_tally"] = tally
        results["steps"].append(f"tally={tally}")

        # 4) Summary
        try:
            await page.wait_for_selector('[data-testid="rf-sum-correct"]', timeout=15000)
            correct = (await page.locator('[data-testid="rf-sum-correct"]').first.inner_text()).strip()
            incorrect = (await page.locator('[data-testid="rf-sum-incorrect"]').first.inner_text()).strip()
            skipped = (await page.locator('[data-testid="rf-sum-skipped"]').first.inner_text()).strip()
            timeout_v = (await page.locator('[data-testid="rf-sum-timeout"]').first.inner_text()).strip()
            results["summary"] = {"correct": correct, "incorrect": incorrect, "skipped": skipped, "timeout": timeout_v}
            await page.screenshot(path=f"{ART}/01_summary.jpeg", quality=40, full_page=False)
        except Exception as e:
            results["steps"].append(f"summary_FAIL: {e}")
            await page.screenshot(path=f"{ART}/err_summary.jpeg", quality=40, full_page=False)

        # 5) Done -> lobby
        try:
            await page.locator('[data-testid="rf-done"]').first.click(force=True)
            await page.wait_for_timeout(2500)
        except Exception as e:
            results["steps"].append(f"done_FAIL: {e}")

        # 6) Check badge after
        try:
            await page.wait_for_selector('[data-testid="rf-weak-cards-badge"]', timeout=8000)
            badge_after = (await page.locator('[data-testid="rf-weak-cards-badge"]').first.inner_text()).strip()
        except Exception:
            badge_after = "N/A"
        results["badge_after"] = badge_after
        results["steps"].append(f"badge_after={badge_after}")
        await page.screenshot(path=f"{ART}/02_lobby_after.jpeg", quality=40, full_page=False)

        # 7) Open weak sheet
        try:
            await page.locator('[data-testid="rf-weak-cards"]').first.click(force=True)
            await page.wait_for_timeout(900)
            await page.screenshot(path=f"{ART}/03_weak_sheet_all.jpeg", quality=40, full_page=False)
            summary_txt = (await page.locator('[data-testid="rf-weak-summary"]').first.inner_text()).strip()
            results["weak_summary"] = summary_txt
            # count chapter rows
            rows = await page.locator('[data-testid^="rf-revise-chapter-"]').count()
            results["weak_rows"] = rows
            # subject tabs
            tabs = await page.locator('[data-testid^="rf-weak-subject-"]').all_inner_texts()
            results["weak_tabs"] = tabs
        except Exception as e:
            results["steps"].append(f"weak_sheet_FAIL: {e}")

        # 8) Topic sprint part
        try:
            await page.locator('[data-testid="rf-weak-part-topics"]').first.click(force=True)
            await page.wait_for_timeout(600)
            await page.screenshot(path=f"{ART}/04_topic_sprint.jpeg", quality=40, full_page=False)
            topics = await page.locator('[data-testid^="rf-weak-topic-"]').count()
            results["topic_count"] = topics
            try:
                start_txt = (await page.get_by_text(re.compile("START SPRINT", re.I)).first.inner_text()).strip()
                results["topic_start_label"] = start_txt
            except Exception:
                pass
        except Exception as e:
            results["steps"].append(f"topic_FAIL: {e}")

        # 9) Save back storage
        try:
            await ctx.storage_state(path=STORAGE)
            os.chmod(STORAGE, 0o600)
        except Exception:
            pass

        await browser.close()

    print(json.dumps(results, indent=2))

asyncio.run(main())
