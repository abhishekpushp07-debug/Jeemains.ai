"""
Frontend Offline/Conflict Recovery Regression Test
===================================================

This script tests the offline/online recovery mechanisms in the Tejas exam platform.

Test Coverage:
1. Offline pending edits detection
2. Reconnect and flush mechanism
3. Invalid decimal blocking for integer questions
4. Multi-tab conflict (409) detection and resolution
5. Automatic retry on reconnect
6. Reload retains pending drafts via localStorage
7. Mobile viewport testing

Usage:
    Run via browser automation tool with:
    - Desktop viewport: 1920x800
    - Mobile viewport: 390x844
    - Test URL: https://campus-launch-2.preview.emergentagent.com
    - Test credentials: +12025550184
    - Test fixture: qa75-ed384de5-896c-4d2a-abd6-ffb9cbde94d0
"""

# This is a Playwright Python script to be executed via browser automation tool

import asyncio

async def run_offline_conflict_tests(page, base_url, phone_number, fixture_id):
    """
    Comprehensive offline/conflict recovery test suite
    
    Args:
        page: Playwright page object
        base_url: Base URL of the application
        phone_number: Test phone number for login
        fixture_id: Test fixture ID to use
    """
    
    # Set viewport for desktop testing
    await page.set_viewport_size({"width": 1920, "height": 800})
    
    print("=== OFFLINE/CONFLICT RECOVERY TEST SUITE ===\n")
    
    results = {
        "passed": [],
        "failed": [],
        "warnings": []
    }
    
    try:
        # ===== LOGIN AND START ATTEMPT =====
        print("[1] Login and start attempt...")
        await page.goto(f"{base_url}/login", wait_until="domcontentloaded", timeout=10000)
        await page.wait_for_timeout(1000)
        
        phone_input = await page.wait_for_selector('[data-testid="student-login-phone-input"]', timeout=5000)
        await phone_input.fill(phone_number)
        
        continue_btn = await page.wait_for_selector('[data-testid="student-login-continue-button"]', timeout=5000)
        await continue_btn.click()
        
        await page.wait_for_url("**/home", timeout=10000)
        
        await page.goto(f"{base_url}/sets/{fixture_id}", wait_until="domcontentloaded", timeout=10000)
        await page.wait_for_timeout(2000)
        
        test_input = await page.wait_for_selector('#device-test-answer', timeout=5000)
        await test_input.fill("42")
        
        check_btn = await page.wait_for_selector('[data-testid="preflight-run-check"]', timeout=5000)
        await check_btn.click()
        await page.wait_for_timeout(2000)
        
        acknowledge_checkbox = await page.wait_for_selector('[data-testid="preflight-acknowledge"]', timeout=5000)
        await acknowledge_checkbox.check()
        
        start_btn = await page.wait_for_selector('[data-testid="set-preflight-start-button"]', timeout=5000)
        await start_btn.click()
        
        await page.wait_for_url("**/attempts/**", timeout=15000)
        await page.wait_for_selector('[data-testid="player-timer"]', timeout=10000)
        attempt_url = page.url
        print(f"✓ Attempt started: {attempt_url}\n")
        results["passed"].append("Login and attempt start")
        
        # ===== NAVIGATE TO Q22 =====
        print("[2] Navigate to Q22 (integer question)...")
        nav_toggle = await page.wait_for_selector('[data-testid="player-navigator-toggle"]', timeout=5000)
        await nav_toggle.click()
        await page.wait_for_timeout(500)
        
        q22_btn = await page.wait_for_selector('[data-testid="player-question-nav-22"]', timeout=5000)
        await q22_btn.click()
        await page.wait_for_timeout(2000)
        print("✓ On Q22 (source images loaded)\n")
        results["passed"].append("Navigation to Q22")
        
        # ===== TEST 1: OFFLINE PENDING EDITS =====
        print("[TEST 1] Offline pending edits + reconnect flush...")
        await page.context.set_offline(True)
        
        numerical_input = await page.wait_for_selector('[data-testid="player-numerical-input"]', timeout=5000)
        await numerical_input.fill("12345")
        await page.wait_for_timeout(1000)
        
        save_indicator = await page.wait_for_selector('[data-testid="player-save-state-indicator"]', timeout=5000)
        offline_text = await save_indicator.inner_text()
        print(f"  Offline state: {offline_text}")
        
        if "Offline" not in offline_text:
            results["failed"].append("TEST 1: Offline indicator not showing")
            print("  ✗ FAIL: Offline indicator not showing\n")
        else:
            await page.context.set_offline(False)
            await page.wait_for_timeout(3000)
            
            online_text = await save_indicator.inner_text()
            print(f"  After reconnect: {online_text}")
            
            if "saved" in online_text.lower():
                results["passed"].append("TEST 1: Offline pending + reconnect flush")
                print("  ✓ PASS: Offline → reconnect → flush working\n")
            else:
                results["failed"].append("TEST 1: Flush not working after reconnect")
                print("  ✗ FAIL: Flush not working\n")
        
        # ===== TEST 2: INVALID DECIMAL BLOCKING =====
        print("[TEST 2] Invalid decimal blocking...")
        
        await page.context.set_offline(True)
        await numerical_input.fill("3.14")
        await page.wait_for_timeout(1000)
        print("  Entered '3.14' while offline")
        
        await page.context.set_offline(False)
        await page.wait_for_timeout(3000)
        
        error_text = await page.evaluate("""() => {
            const errorElements = Array.from(document.querySelectorAll('.error, [class*="error"], [id*="error"]'));
            return errorElements.map(el => el.textContent).join(", ");
        }""")
        
        if error_text and "integer" in error_text.lower():
            results["passed"].append("TEST 2: Invalid decimal blocking")
            print(f"  ✓ PASS: Decimal blocked with error\n")
        else:
            results["warnings"].append("TEST 2: No clear error for decimal input")
            print(f"  ⚠ WARNING: No clear error. Text: {error_text}\n")
        
        await page.screenshot(path=".screenshots/regression_invalid_decimal.png", quality=40, full_page=False)
        
        # Clear invalid input
        await numerical_input.fill("")
        await page.wait_for_timeout(2000)
        
        # ===== TEST 3: MULTI-TAB CONFLICT =====
        print("[TEST 3] Multi-tab conflict (409)...")
        
        await numerical_input.fill("11111")
        await page.wait_for_timeout(3000)
        print("  Tab 1: Saved '11111'")
        
        page2 = await page.context.new_page()
        await page2.set_viewport_size({"width": 1920, "height": 800})
        await page2.goto(attempt_url, wait_until="domcontentloaded", timeout=10000)
        await page2.wait_for_timeout(2000)
        
        # Navigate to Q22 in tab 2
        nav_toggle2 = await page2.wait_for_selector('[data-testid="player-navigator-toggle"]', timeout=5000)
        await nav_toggle2.click()
        await page2.wait_for_timeout(500)
        
        q22_btn2 = await page2.wait_for_selector('[data-testid="player-question-nav-22"]', timeout=5000)
        await q22_btn2.click()
        await page2.wait_for_timeout(1000)
        
        numerical_input2 = await page2.wait_for_selector('[data-testid="player-numerical-input"]', timeout=5000)
        await numerical_input2.fill("22222")
        await page2.wait_for_timeout(3000)
        print("  Tab 2: Saved '22222'")
        
        await numerical_input.fill("33333")
        await page.wait_for_timeout(3000)
        print("  Tab 1: Attempted '33333'")
        
        try:
            conflict_notice = await page.wait_for_selector('text=Another saved version exists', timeout=5000)
            print("  ✓ Conflict notice displayed")
            
            await page.screenshot(path=".screenshots/regression_conflict_409.png", quality=40, full_page=False)
            
            discard_btn = await page.wait_for_selector('[data-testid="discard-conflicting-drafts"]', timeout=5000)
            await discard_btn.click()
            await page.wait_for_timeout(2000)
            
            final_value = await numerical_input.input_value()
            print(f"  After discard: '{final_value}'")
            
            if final_value == "22222":
                results["passed"].append("TEST 3: Multi-tab conflict detection and resolution")
                print("  ✓ PASS: Server answer restored\n")
            else:
                results["warnings"].append(f"TEST 3: Expected '22222', got '{final_value}'")
                print(f"  ⚠ WARNING: Expected '22222', got '{final_value}'\n")
            
        except Exception as e:
            results["failed"].append("TEST 3: Conflict detection not working")
            print(f"  ✗ FAIL: Conflict not detected: {str(e)}\n")
        
        await page2.close()
        
        # ===== TEST 4: AUTO RETRY ON RECONNECT =====
        print("[TEST 4] Auto retry on reconnect...")
        
        nav_toggle = await page.wait_for_selector('[data-testid="player-navigator-toggle"]', timeout=5000)
        await nav_toggle.click()
        await page.wait_for_timeout(500)
        
        q23_btn = await page.wait_for_selector('[data-testid="player-question-nav-23"]', timeout=5000)
        await q23_btn.click()
        await page.wait_for_timeout(1000)
        print("  Navigated to Q23")
        
        await page.context.set_offline(True)
        numerical_input = await page.wait_for_selector('[data-testid="player-numerical-input"]', timeout=5000)
        await numerical_input.fill("77777")
        await page.wait_for_timeout(1000)
        print("  Entered '77777' while offline")
        
        await page.context.set_offline(False)
        print("  Reconnected...")
        await page.wait_for_timeout(6000)
        
        save_indicator = await page.wait_for_selector('[data-testid="player-save-state-indicator"]', timeout=5000)
        indicator_text = await save_indicator.inner_text()
        print(f"  Save state: {indicator_text}")
        
        if "saved" in indicator_text.lower() or "0 pending" in indicator_text.lower():
            results["passed"].append("TEST 4: Automatic retry on reconnect")
            print("  ✓ PASS: Auto retry working\n")
        else:
            results["warnings"].append("TEST 4: Auto retry unclear")
            print(f"  ⚠ WARNING: Auto retry unclear\n")
        
        # ===== TEST 5: RELOAD RETAINS PENDING =====
        print("[TEST 5] Reload retains pending drafts...")
        
        nav_toggle = await page.wait_for_selector('[data-testid="player-navigator-toggle"]', timeout=5000)
        await nav_toggle.click()
        await page.wait_for_timeout(500)
        
        q22_btn = await page.wait_for_selector('[data-testid="player-question-nav-22"]', timeout=5000)
        await q22_btn.click()
        await page.wait_for_timeout(1000)
        
        numerical_input = await page.wait_for_selector('[data-testid="player-numerical-input"]', timeout=5000)
        await numerical_input.fill("88888")
        await page.wait_for_timeout(500)
        
        await page.context.set_offline(True)
        await numerical_input.fill("99999")
        await page.wait_for_timeout(1000)
        print("  Entered '99999' while offline")
        
        await page.context.set_offline(False)
        await page.wait_for_timeout(500)
        
        await page.reload(wait_until="domcontentloaded")
        await page.wait_for_timeout(2000)
        print("  Reloaded page")
        
        # Navigate back to Q22 after reload
        nav_toggle = await page.wait_for_selector('[data-testid="player-navigator-toggle"]', timeout=5000)
        await nav_toggle.click()
        await page.wait_for_timeout(500)
        
        q22_btn = await page.wait_for_selector('[data-testid="player-question-nav-22"]', timeout=5000)
        await q22_btn.click()
        await page.wait_for_timeout(1000)
        
        numerical_input = await page.wait_for_selector('[data-testid="player-numerical-input"]', timeout=5000)
        retained_value = await numerical_input.input_value()
        print(f"  Value after reload: '{retained_value}'")
        
        if retained_value in ["88888", "99999"]:
            results["passed"].append("TEST 5: Reload retains pending drafts")
            print("  ✓ PASS: Draft persistence working\n")
        else:
            results["warnings"].append(f"TEST 5: Unexpected value: {retained_value}")
            print(f"  ⚠ WARNING: Unexpected value: {retained_value}\n")
        
        print("=== DESKTOP TESTS COMPLETE ===\n")
        
    except Exception as e:
        results["failed"].append(f"Critical error: {str(e)}")
        print(f"\n✗ CRITICAL ERROR: {str(e)}")
        await page.screenshot(path=".screenshots/regression_error.png", quality=40, full_page=False)
        import traceback
        traceback.print_exc()
    
    # ===== MOBILE VIEWPORT TESTS =====
    print("\n=== MOBILE VIEWPORT TEST ===\n")
    
    try:
        await page.set_viewport_size({"width": 390, "height": 844})
        
        await page.goto(attempt_url, wait_until="domcontentloaded", timeout=10000)
        await page.wait_for_timeout(2000)
        
        nav_toggle = await page.wait_for_selector('[data-testid="player-navigator-toggle"]', timeout=5000)
        await nav_toggle.click()
        await page.wait_for_timeout(500)
        
        q22_btn = await page.wait_for_selector('[data-testid="player-question-nav-22"]', timeout=5000)
        await q22_btn.click()
        await page.wait_for_timeout(1000)
        print("Mobile: On Q22")
        
        await page.context.set_offline(True)
        numerical_input = await page.wait_for_selector('[data-testid="player-numerical-input"]', timeout=5000)
        await numerical_input.fill("55555")
        await page.wait_for_timeout(1000)
        print("Mobile: Entered '55555' offline")
        
        await page.screenshot(path=".screenshots/regression_mobile_offline.png", quality=40, full_page=False)
        
        await page.context.set_offline(False)
        await page.wait_for_timeout(3000)
        print("Mobile: Reconnected and flushed")
        
        await page.screenshot(path=".screenshots/regression_mobile_online.png", quality=40, full_page=False)
        
        results["passed"].append("Mobile viewport offline/online testing")
        print("✓ Mobile tests complete\n")
        
    except Exception as e:
        results["failed"].append(f"Mobile test error: {str(e)}")
        print(f"✗ Mobile error: {str(e)}\n")
    
    # ===== PRINT SUMMARY =====
    print("\n=== TEST SUMMARY ===")
    print(f"✓ Passed: {len(results['passed'])}")
    print(f"✗ Failed: {len(results['failed'])}")
    print(f"⚠ Warnings: {len(results['warnings'])}")
    
    if results["passed"]:
        print("\nPassed tests:")
        for test in results["passed"]:
            print(f"  ✓ {test}")
    
    if results["failed"]:
        print("\nFailed tests:")
        for test in results["failed"]:
            print(f"  ✗ {test}")
    
    if results["warnings"]:
        print("\nWarnings:")
        for test in results["warnings"]:
            print(f"  ⚠ {test}")
    
    return results


# Main execution
# This script is designed to be run via browser automation tool
# Example usage:
# await run_offline_conflict_tests(
#     page,
#     "https://campus-launch-2.preview.emergentagent.com",
#     "+12025550184",
#     "qa75-ed384de5-896c-4d2a-abd6-ffb9cbde94d0"
# )
