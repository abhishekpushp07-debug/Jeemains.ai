"""
Iteration 28 Frontend Audit - Narrow Recheck
AUDIT ONLY - NO FIXES

Corrects iteration 27 issues:
- Timer was untimed (retry mode), now tests actual deadline with 120s timer
- Desktop viewport was wrong, now uses EXACT 1920x800 and 390x844
- Math options only code review, now runtime tests with actual KaTeX rendering
- Staff credentials leaked, now uses ONLY phone +12025550184

Test scenario:
1. Phone login with +12025550184
2. Route /api/attempts/<UUID> to synthetic 2-question attempt
3. Q1: MCQ with math options, Q2: integer
4. server_now = fixed start, deadline = start + 120s
5. Route callback returns elapsed server_now, deadline stays FIXED
6. Intercept /visit to return visited only (no real save)

Assertions:
a. Stem contains rendered .katex; MCQ option raw vs rendered math
b. Wait 4s, capture timer, reload (server_now +4s), deadline NOT RESET
c. Seed draft key with 'null', assert Object.entries error, then reset
"""

import asyncio
import json
import time

# Synthetic attempt UUID
SYNTHETIC_ATTEMPT_ID = "00000000-0000-4000-8000-000000000028"
SYNTHETIC_Q1_ID = "11111111-1111-4111-8111-111111111111"
SYNTHETIC_Q2_ID = "22222222-2222-4222-8222-222222222222"

# Fixed wall clock start time (current time when test starts)
WALL_START = None
USER_ID = None

def create_synthetic_attempt(server_now, user_id):
    """Create synthetic 2-question attempt with 120s deadline"""
    return {
        "id": SYNTHETIC_ATTEMPT_ID,
        "user_id": user_id,
        "set_id": "synthetic-set-id",
        "title": "Synthetic Math Test",
        "exam": "JEE Main",
        "mode": "practice",
        "version": "2024",
        "rules": {
            "minutes": 2,
            "correct": 4,
            "wrong": -1,
            "partial": 0
        },
        "started_at": WALL_START,
        "deadline": WALL_START + 120,
        "status": "active",
        "answers": {},
        "visited": [],
        "profile": {
            "exam": "JEE Main",
            "year": "2024",
            "source": "Synthetic test data for audit"
        },
        "questions": [
            {
                "id": SYNTHETIC_Q1_ID,
                "number": 1,
                "subject": "Mathematics",
                "type": "mcq",
                "stem": "$x^2$",
                "text": "x squared",
                "render_mode": "typed",
                "options": {
                    "1": "$\\frac{1}{2}$",
                    "2": "0.5"
                },
                "q_refs": []
            },
            {
                "id": SYNTHETIC_Q2_ID,
                "number": 2,
                "subject": "Mathematics",
                "type": "integer",
                "stem": "What is 5 + 5?",
                "text": "What is 5 + 5?",
                "render_mode": "typed",
                "q_refs": []
            }
        ],
        "server_now": server_now,
        "count": 2
    }

print("=" * 80)
print("ITERATION 28 FRONTEND AUDIT - NARROW RECHECK")
print("=" * 80)
print("AUDIT ONLY - NO FIXES")
print("Credentials: phone-only test profile (+12025550184)")
print("=" * 80)

try:
    # Step 1: Phone login
    print("\n[STEP 1] Phone login with +12025550184")
    await page.goto("https://campus-launch-2.preview.emergentagent.com/")
    await page.wait_for_timeout(1000)
    
    # Check if already logged in
    try:
        await page.wait_for_selector("text=My practice", timeout=3000)
        print("✓ Already logged in")
    except:
        print("Not logged in, proceeding with phone login...")
        
        # Click login/get started
        try:
            login_btn = await page.wait_for_selector("text=Get started", timeout=3000)
            await login_btn.click()
        except:
            try:
                login_btn = await page.wait_for_selector("text=Log in", timeout=3000)
                await login_btn.click()
            except:
                print("✗ Could not find login button")
                raise Exception("Login button not found")
        
        await page.wait_for_timeout(1000)
        
        # Enter phone number
        phone_input = await page.wait_for_selector("input[type='tel'], input[placeholder*='phone'], input[name='phone']", timeout=5000)
        await phone_input.fill("+12025550184")
        print("✓ Entered phone number: +12025550184")
        
        # Submit
        submit_btn = await page.wait_for_selector("button[type='submit'], button:has-text('Continue'), button:has-text('Access')", timeout=5000)
        await submit_btn.click()
        await page.wait_for_timeout(2000)
        
        # Wait for home page
        await page.wait_for_selector("text=My practice", timeout=10000)
        print("✓ Phone login successful")
    
    # Get user ID from session
    session_data = await page.evaluate("""
        async () => {
            const response = await fetch('/api/auth/session', {
                credentials: 'include'
            });
            const data = await response.json();
            return data.user;
        }
    """)
    USER_ID = session_data['id']
    print(f"✓ User ID: {USER_ID}")
    
    # Set wall start time
    WALL_START = time.time()
    print(f"✓ Wall start time: {WALL_START}")
    
    # Step 2: Setup route interception
    print("\n[STEP 2] Setting up route interception for synthetic attempt")
    
    request_count = {"get_attempt": 0}
    
    async def handle_attempt_route(route):
        """Route handler for /api/attempts/<UUID>"""
        request_count["get_attempt"] += 1
        elapsed = time.time() - WALL_START
        server_now = WALL_START + elapsed
        
        attempt_data = create_synthetic_attempt(server_now, USER_ID)
        
        print(f"  → GET /api/attempts/{SYNTHETIC_ATTEMPT_ID} (request #{request_count['get_attempt']})")
        print(f"    server_now: {server_now:.2f} (elapsed: {elapsed:.2f}s)")
        print(f"    deadline: {attempt_data['deadline']} (FIXED at start + 120s)")
        
        await route.fulfill(
            status=200,
            content_type="application/json",
            body=json.dumps(attempt_data)
        )
    
    async def handle_visit_route(route):
        """Route handler for /api/attempts/<UUID>/visit - return visited only"""
        body = await route.request.post_data_json()
        qid = body.get("question_id")
        print(f"  → POST /api/attempts/{SYNTHETIC_ATTEMPT_ID}/visit (question: {qid})")
        print(f"    MOCKED TEST DATA - no real save")
        
        await route.fulfill(
            status=200,
            content_type="application/json",
            body=json.dumps({"visited": [qid]})
        )
    
    # Register routes
    await page.route(f"**/api/attempts/{SYNTHETIC_ATTEMPT_ID}", handle_attempt_route)
    await page.route(f"**/api/attempts/{SYNTHETIC_ATTEMPT_ID}/visit", handle_visit_route)
    print("✓ Route interception configured (MOCKED TEST DATA)")
    
    # Step 3: Navigate to synthetic attempt
    print(f"\n[STEP 3] Navigate to /attempts/{SYNTHETIC_ATTEMPT_ID}")
    await page.goto(f"https://campus-launch-2.preview.emergentagent.com/attempts/{SYNTHETIC_ATTEMPT_ID}")
    await page.wait_for_timeout(2000)
    
    # Wait for player to load
    await page.wait_for_selector("[data-testid='player-timer']", timeout=10000)
    print("✓ Player loaded")
    
    # ASSERTION A: Stem contains rendered .katex; check MCQ option raw vs rendered math
    print("\n[ASSERTION A] KaTeX rendering verification")
    print("-" * 80)
    
    # Check stem for rendered KaTeX
    stem_element = await page.wait_for_selector("[data-testid='player-question-stem']", timeout=5000)
    stem_html = await stem_element.inner_html()
    
    has_katex = ".katex" in stem_html or "katex" in stem_html.lower()
    print(f"  Stem HTML contains KaTeX: {has_katex}")
    
    if has_katex:
        print("  ✓ Stem contains rendered .katex class")
    else:
        print("  ✗ WARNING: Stem does not contain .katex class")
        print(f"  Stem HTML preview: {stem_html[:200]}...")
    
    # Check MCQ options - raw vs rendered
    print("\n  Checking MCQ options:")
    option_1_element = await page.wait_for_selector("[data-testid='player-option-1']", timeout=5000)
    option_1_parent = await option_1_element.evaluate_handle("el => el.closest('label')")
    option_1_html = await option_1_parent.inner_html()
    option_1_text = await option_1_parent.inner_text()
    
    print(f"  Option 1 raw value: '$\\\\frac{{1}}{{2}}$'")
    print(f"  Option 1 visible text: '{option_1_text.strip()}'")
    print(f"  Option 1 contains KaTeX: {'.katex' in option_1_html or 'katex' in option_1_html.lower()}")
    
    if "$\\frac{1}{2}$" in option_1_text or "\\frac" in option_1_text:
        print("  ✗ Option 1 shows RAW TeX string (not rendered)")
    elif "katex" in option_1_html.lower():
        print("  ✓ Option 1 has KaTeX rendering")
    else:
        print("  ? Option 1 rendering unclear")
    
    option_2_element = await page.wait_for_selector("[data-testid='player-option-2']", timeout=5000)
    option_2_parent = await option_2_element.evaluate_handle("el => el.closest('label')")
    option_2_text = await option_2_parent.inner_text()
    
    print(f"  Option 2 raw value: '0.5'")
    print(f"  Option 2 visible text: '{option_2_text.strip()}'")
    
    # Screenshot - Desktop 1920x800
    print("\n  Taking screenshot - Desktop 1920x800")
    await page.set_viewport_size({"width": 1920, "height": 800})
    await page.wait_for_timeout(400)  # Dark theme wait
    await page.screenshot(path="/app/docs/audit/tests/assertion_a_desktop_1920x800.png", quality=40, full_page=False)
    print("  ✓ Screenshot saved: assertion_a_desktop_1920x800.png")
    
    # Screenshot - Mobile 390x844
    print("  Taking screenshot - Mobile 390x844")
    await page.set_viewport_size({"width": 390, "height": 844})
    await page.wait_for_timeout(400)  # Dark theme wait
    await page.screenshot(path="/app/docs/audit/tests/assertion_a_mobile_390x844.png", quality=40, full_page=False)
    print("  ✓ Screenshot saved: assertion_a_mobile_390x844.png")
    
    # Reset to desktop for next tests
    await page.set_viewport_size({"width": 1920, "height": 800})
    
    # ASSERTION B: Timer sync and deadline persistence
    print("\n[ASSERTION B] Timer sync and deadline persistence")
    print("-" * 80)
    
    # Capture initial timer
    timer_element = await page.wait_for_selector("[data-testid='player-timer']", timeout=5000)
    timer_initial = await timer_element.inner_text()
    print(f"  Initial timer: {timer_initial}")
    
    if timer_initial.strip().lower() == "untimed":
        print("  ✗ FAIL: Timer shows 'Untimed' - this is the iteration 27 bug!")
        print("  Expected: HH:MM:SS format with actual countdown")
    else:
        print(f"  ✓ Timer shows timed value: {timer_initial}")
    
    # Wait 4 seconds
    print("\n  Waiting 4 seconds...")
    await page.wait_for_timeout(4000)
    
    # Capture timer after 4s
    timer_after_4s = await timer_element.inner_text()
    print(f"  Timer after 4s: {timer_after_4s}")
    
    # Reload page (this will trigger new GET with server_now +4s advanced)
    print("\n  Reloading page (new GET with server_now +4s advanced)...")
    print(f"  Expected: deadline stays FIXED at {WALL_START + 120}")
    print(f"  Expected: timer continues from ~01:56, NOT reset to 02:00")
    
    await page.reload()
    await page.wait_for_timeout(2000)
    
    # Capture timer after reload
    timer_element_reload = await page.wait_for_selector("[data-testid='player-timer']", timeout=5000)
    timer_after_reload = await timer_element_reload.inner_text()
    print(f"  Timer after reload: {timer_after_reload}")
    
    # Parse timers to check if deadline was reset
    def parse_timer(timer_str):
        """Parse HH:MM:SS to seconds"""
        if timer_str.strip().lower() == "untimed":
            return None
        parts = timer_str.strip().split(":")
        if len(parts) == 3:
            return int(parts[0]) * 3600 + int(parts[1]) * 60 + int(parts[2])
        return None
    
    initial_seconds = parse_timer(timer_initial)
    after_4s_seconds = parse_timer(timer_after_4s)
    after_reload_seconds = parse_timer(timer_after_reload)
    
    print(f"\n  Timer analysis:")
    print(f"    Initial: {timer_initial} ({initial_seconds}s)" if initial_seconds else f"    Initial: {timer_initial} (untimed)")
    print(f"    After 4s: {timer_after_4s} ({after_4s_seconds}s)" if after_4s_seconds else f"    After 4s: {timer_after_4s} (untimed)")
    print(f"    After reload: {timer_after_reload} ({after_reload_seconds}s)" if after_reload_seconds else f"    After reload: {timer_after_reload} (untimed)")
    
    if initial_seconds and after_reload_seconds:
        if after_reload_seconds >= 118:  # Close to 120 (02:00)
            print("  ✗ FAIL: Timer was RESET to ~120s after reload (deadline extended)")
        elif after_reload_seconds < initial_seconds:
            print("  ✓ PASS: Timer continued countdown, deadline NOT RESET")
        else:
            print("  ? UNCLEAR: Timer behavior unexpected")
    else:
        print("  ✗ FAIL: Timer is untimed, cannot verify deadline persistence")
    
    # Screenshot after reload
    print("\n  Taking screenshot after reload - Desktop 1920x800")
    await page.screenshot(path="/app/docs/audit/tests/assertion_b_after_reload_1920x800.png", quality=40, full_page=False)
    print("  ✓ Screenshot saved: assertion_b_after_reload_1920x800.png")
    
    # ASSERTION C: Draft key with 'null' value causes Object.entries error
    print("\n[ASSERTION C] Draft key with 'null' value - Object.entries error")
    print("-" * 80)
    
    # Seed draft key with 'null' (string literal, not null value)
    draft_key = f"tejas-draft-{USER_ID}-{SYNTHETIC_ATTEMPT_ID}"
    print(f"  Draft key: {draft_key}")
    print(f"  Setting localStorage['{draft_key}'] = 'null' (string)")
    
    await page.evaluate(f"""
        localStorage.setItem('{draft_key}', 'null');
    """)
    print("  ✓ Draft key seeded with 'null'")
    
    # Reload page
    print("\n  Reloading page to trigger Object.entries error...")
    await page.reload()
    await page.wait_for_timeout(2000)
    
    # Check for error message
    error_text = await page.evaluate("""() => {
        const errorElements = Array.from(document.querySelectorAll('.error, [class*="error"], [id*="error"]'));
        return errorElements.map(el => el.textContent).join(", ");
    }""")
    
    print(f"\n  Error detection:")
    if error_text:
        print(f"  ✓ Found error message: {error_text}")
        if "object" in error_text.lower() or "entries" in error_text.lower():
            print("  ✓ Error mentions 'object' or 'entries' - likely Object.entries error")
        else:
            print("  ? Error found but doesn't mention Object.entries")
    else:
        print("  ✗ No error messages found on the page")
        print("  Expected: 'Cannot convert undefined or null to object' or similar")
    
    # Screenshot with error
    print("\n  Taking screenshot with error - Desktop 1920x800")
    await page.screenshot(path="/app/docs/audit/tests/assertion_c_null_error_1920x800.png", quality=40, full_page=False)
    print("  ✓ Screenshot saved: assertion_c_null_error_1920x800.png")
    
    # Reset storage (remove only synthetic key)
    print("\n  Resetting storage (removing only synthetic key)...")
    await page.evaluate(f"""
        localStorage.removeItem('{draft_key}');
    """)
    print("  ✓ Synthetic draft key removed")
    
    # Reload healthy control
    print("\n  Reloading page for healthy control...")
    await page.reload()
    await page.wait_for_timeout(2000)
    
    # Check no error
    error_text_after = await page.evaluate("""() => {
        const errorElements = Array.from(document.querySelectorAll('.error, [class*="error"], [id*="error"]'));
        return errorElements.map(el => el.textContent).join(", ");
    }""")
    
    if error_text_after:
        print(f"  ✗ Error still present: {error_text_after}")
    else:
        print("  ✓ No error messages - healthy control confirmed")
    
    # Screenshot healthy control
    print("\n  Taking screenshot healthy control - Desktop 1920x800")
    await page.screenshot(path="/app/docs/audit/tests/assertion_c_healthy_1920x800.png", quality=40, full_page=False)
    print("  ✓ Screenshot saved: assertion_c_healthy_1920x800.png")
    
    # Final mobile screenshot
    print("\n  Taking final screenshot - Mobile 390x844")
    await page.set_viewport_size({"width": 390, "height": 844})
    await page.wait_for_timeout(400)
    await page.screenshot(path="/app/docs/audit/tests/assertion_c_healthy_390x844.png", quality=40, full_page=False)
    print("  ✓ Screenshot saved: assertion_c_healthy_390x844.png")
    
    print("\n" + "=" * 80)
    print("ITERATION 28 FRONTEND AUDIT COMPLETE")
    print("=" * 80)
    print("All assertions executed:")
    print("  A. KaTeX rendering verification - COMPLETED")
    print("  B. Timer sync and deadline persistence - COMPLETED")
    print("  C. Draft key null error - COMPLETED")
    print("\nTest report will be generated at:")
    print("  /app/test_reports/iteration_28_frontend_audit.json")
    print("\nTest script persisted at:")
    print("  /app/docs/audit/tests/iteration_28_frontend_audit.py")
    print("=" * 80)

except Exception as e:
    print(f"\n✗ ERROR: {str(e)}")
    import traceback
    traceback.print_exc()
    
    # Emergency screenshot
    try:
        await page.screenshot(path="/app/docs/audit/tests/error_state.png", quality=40, full_page=False)
        print("Emergency screenshot saved: error_state.png")
    except:
        pass
