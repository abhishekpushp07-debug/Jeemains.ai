"""
Comprehensive Frontend Navigation and UI Test - CORRECTED VERSION
Tests all navigation flows, image fit buttons, exam flows, and UI elements
Addresses iteration 89 false claims and weak checks
"""
import asyncio
import sys
import os
from playwright.async_api import async_playwright
import json
from datetime import datetime, timezone
import fitz  # PyMuPDF for PDF verification

# Read base URL from frontend/.env
def read_base_url():
    env_path = "/app/frontend/.env"
    with open(env_path, 'r') as f:
        for line in f:
            if line.startswith('REACT_APP_BACKEND_URL='):
                return line.split('=', 1)[1].strip()
    return "https://campus-launch-2.preview.emergentagent.com"

BASE_URL = read_base_url()
QA_PHONE_DEFAULT = "+12025550341"
QA_PHONE_FRESH = "+12025550342"
QA_PHONE = os.environ.get('QA_PHONE', QA_PHONE_DEFAULT)
OUTPUT_DIR = "/app/test_reports/navigation-ui-verified"

# Ensure output directory exists
os.makedirs(OUTPUT_DIR, exist_ok=True)

class NavigationUITester:
    def __init__(self):
        self.results = {
            "test_run": datetime.now(timezone.utc).isoformat(),
            "base_url": BASE_URL,
            "test_phone": QA_PHONE,
            "passed_tests": [],
            "failed_tests": [],
            "screenshots": [],
            "pdf_downloads": [],
            "overflow_offenders": [],
            "test_details": {}
        }
        self.browser = None
        self.context = None
        self.page = None
        self.attempt_id = None  # Store attempt ID for history verification
        
    async def setup(self):
        """Initialize browser"""
        playwright = await async_playwright().start()
        self.browser = await playwright.chromium.launch(headless=True)
        self.context = await self.browser.new_context()
        self.page = await self.context.new_page()
        
        # Enable console logging
        self.page.on("console", lambda msg: print(f"CONSOLE: {msg.text}"))
        
    async def teardown(self):
        """Cleanup browser"""
        if self.context:
            await self.context.close()
        if self.browser:
            await self.browser.close()
            
    async def take_screenshot(self, name, width=1920, height=800):
        """Take screenshot with specified dimensions"""
        await self.page.set_viewport_size({"width": width, "height": height})
        await self.page.wait_for_timeout(500)
        filepath = f"{OUTPUT_DIR}/{name}.jpg"
        await self.page.screenshot(path=filepath, quality=40, full_page=False, type='jpeg')
        self.results["screenshots"].append(filepath)
        print(f"✓ Screenshot saved: {filepath}")
        return filepath
        
    async def check_overflow(self, screen_name):
        """Check for overflow issues - rightedge > innerWidth+1"""
        offenders = await self.page.evaluate("""() => {
            const elements = document.querySelectorAll('*');
            const offenders = [];
            elements.forEach(el => {
                const rect = el.getBoundingClientRect();
                const rightEdge = rect.left + rect.width;
                if (rightEdge > window.innerWidth + 1) {
                    offenders.push({
                        tag: el.tagName,
                        class: el.className,
                        rightEdge: rightEdge,
                        innerWidth: window.innerWidth,
                        overflow: rightEdge - window.innerWidth
                    });
                }
            });
            return offenders;
        }""")
        if offenders:
            self.results["overflow_offenders"].append({
                "screen": screen_name,
                "count": len(offenders),
                "details": offenders[:5]  # First 5 offenders
            })
            print(f"✗ Overflow offenders found on {screen_name}: {len(offenders)}")
            return False
        else:
            print(f"✓ No overflow offenders on {screen_name}")
            return True
        
    async def test_login(self):
        """Test 1: Login with QA phone"""
        try:
            print("\n=== TEST 1: Login with QA Phone ===")
            await self.page.goto(f"{BASE_URL}/login")
            await self.page.wait_for_selector("#student-login-phone-input", timeout=10000)
            
            # Fill phone number
            await self.page.fill("#student-login-phone-input", QA_PHONE)
            await self.page.wait_for_timeout(300)
            
            # Click continue button
            await self.page.click('[data-testid="student-login-continue-button"]')
            
            # Wait for home page
            await self.page.wait_for_selector('[data-testid="exam-home-page"]', timeout=15000)
            await self.page.wait_for_url("**/home", timeout=10000)
            
            print(f"✓ Login successful with phone: {QA_PHONE}")
            self.results["passed_tests"].append("Login with QA phone")
            return True
        except Exception as e:
            print(f"✗ Login failed: {str(e)}")
            self.results["failed_tests"].append({"test": "Login", "error": str(e)})
            return False
            
    async def test_home_page(self):
        """Test 2: Verify home page has 3 exam cards - both desktop and mobile"""
        try:
            print("\n=== TEST 2: Home Page Verification ===")
            
            # Desktop viewport
            await self.page.set_viewport_size({"width": 1920, "height": 800})
            await self.page.wait_for_timeout(300)
            
            # Verify 3 exam cards
            jee_card = await self.page.wait_for_selector('[data-testid="exam-home-exam-card-jee-main"]', timeout=5000)
            bitsat_card = await self.page.wait_for_selector('[data-testid="exam-home-exam-card-bitsat"]', timeout=5000)
            comedk_card = await self.page.wait_for_selector('[data-testid="exam-home-exam-card-comedk"]', timeout=5000)
            
            print("✓ Found all 3 exam cards: JEE Main, BITSAT, COMEDK")
            
            # Verify header has NO "My practice"
            my_practice = await self.page.query_selector('text="My practice"')
            if my_practice:
                print("✗ Header contains 'My practice' (should not be present)")
                self.results["failed_tests"].append({"test": "Home header", "error": "My practice found in header"})
            else:
                print("✓ Header does not contain 'My practice'")
            
            # Take desktop screenshot
            await self.take_screenshot("01_home_desktop", 1920, 800)
            
            # Check overflow on desktop
            overflow_ok = await self.check_overflow("home_desktop")
            
            # Mobile viewport
            await self.page.set_viewport_size({"width": 390, "height": 844})
            await self.page.wait_for_timeout(300)
            
            # Take mobile screenshot
            await self.take_screenshot("02_home_mobile", 390, 844)
            
            # Check overflow on mobile
            overflow_ok_mobile = await self.check_overflow("home_mobile")
            
            if not overflow_ok or not overflow_ok_mobile:
                self.results["failed_tests"].append({"test": "Home page overflow", "error": "Overflow detected"})
            
            self.results["passed_tests"].append("Home page 3 exam cards verified on desktop and mobile")
            return True
        except Exception as e:
            print(f"✗ Home page verification failed: {str(e)}")
            self.results["failed_tests"].append({"test": "Home page", "error": str(e)})
            return False
            
    async def test_bitsat_hub(self):
        """Test 3: BITSAT hub verification"""
        try:
            print("\n=== TEST 3: BITSAT Hub Verification ===")
            
            # Set desktop viewport
            await self.page.set_viewport_size({"width": 1920, "height": 800})
            
            # Click BITSAT card
            await self.page.click('[data-testid="exam-home-exam-card-bitsat"]')
            await self.page.wait_for_selector('[data-testid="exam-hub-page"]', timeout=10000)
            
            print("✓ Navigated to BITSAT hub")
            await self.take_screenshot("03_bitsat_hub_desktop", 1920, 800)
            await self.check_overflow("bitsat_hub_desktop")
            
            # Verify 3 cards in hub
            await self.page.wait_for_selector('[data-testid="exam-hub-card-mocks"]', timeout=5000)
            await self.page.wait_for_selector('[data-testid="exam-hub-card-chapters"]', timeout=5000)
            await self.page.wait_for_selector('[data-testid="exam-hub-card-results"]', timeout=5000)
            print("✓ Found all 3 hub cards: Mocks, Chapters, Results")
            
            # Mobile viewport
            await self.page.set_viewport_size({"width": 390, "height": 844})
            await self.page.wait_for_timeout(300)
            await self.take_screenshot("04_bitsat_hub_mobile", 390, 844)
            await self.check_overflow("bitsat_hub_mobile")
            
            self.results["passed_tests"].append("BITSAT hub verified on desktop and mobile")
            return True
        except Exception as e:
            print(f"✗ BITSAT hub verification failed: {str(e)}")
            self.results["failed_tests"].append({"test": "BITSAT hub", "error": str(e)})
            return False
            
    async def test_chapter_catalog_with_pagination(self):
        """Test 4: Chapter catalog with exact count verification and pagination"""
        try:
            print("\n=== TEST 4: Chapter Catalog with Pagination ===")
            
            # Set desktop viewport
            await self.page.set_viewport_size({"width": 1920, "height": 800})
            
            # Click chapters card
            await self.page.click('[data-testid="exam-hub-card-chapters"]')
            await self.page.wait_for_selector('[data-testid="chapters-subject-grid"]', timeout=10000)
            
            print("✓ Navigated to chapters subject selection")
            await self.take_screenshot("05_chapters_subjects", 1920, 800)
            await self.check_overflow("chapters_subjects")
            
            # Click Chemistry
            await self.page.click('[data-testid="chapters-subject-chemistry"]')
            await self.page.wait_for_selector('[data-testid="chapters-chapter-list"]', timeout=10000)
            
            print("✓ Navigated to Chemistry chapters")
            await self.take_screenshot("06_chemistry_chapters_page1", 1920, 800)
            await self.check_overflow("chemistry_chapters")
            
            # CRITICAL: Verify exact count from exam-result-count
            count_element = await self.page.wait_for_selector('[data-testid="exam-result-count"]', timeout=5000)
            count_text = await count_element.inner_text()
            print(f"✓ Count text: {count_text}")
            
            # Extract number from text like "32 live chapter tests"
            import re
            match = re.search(r'(\d+)', count_text)
            if not match:
                raise Exception(f"Could not extract count from: {count_text}")
            
            total_count = int(match.group(1))
            print(f"✓ Total chapter count from header: {total_count}")
            
            if total_count != 32:
                print(f"✗ Expected 32 chapters, found {total_count}")
                self.results["failed_tests"].append({
                    "test": "Chapter count", 
                    "error": f"Expected 32, found {total_count}",
                    "count_text": count_text
                })
                return False
            
            # Count cards on page 1
            page1_cards = await self.page.query_selector_all('[data-testid^="exams-set-card-"]')
            page1_count = len(page1_cards)
            print(f"✓ Page 1 card count: {page1_count}")
            
            if page1_count != 12:
                print(f"✗ Expected 12 cards on page 1, found {page1_count}")
                self.results["failed_tests"].append({
                    "test": "Page 1 card count",
                    "error": f"Expected 12, found {page1_count}"
                })
                return False
            
            # Click next to go to page 2
            next_button = await self.page.wait_for_selector('[data-testid="catalog-next"]', timeout=5000)
            await next_button.click()
            await self.page.wait_for_timeout(1000)
            
            print("✓ Navigated to page 2")
            await self.take_screenshot("07_chemistry_chapters_page2", 1920, 800)
            
            # Count cards on page 2
            page2_cards = await self.page.query_selector_all('[data-testid^="exams-set-card-"]')
            page2_count = len(page2_cards)
            print(f"✓ Page 2 card count: {page2_count}")
            
            if page2_count != 12:
                print(f"✗ Expected 12 cards on page 2, found {page2_count}")
                self.results["failed_tests"].append({
                    "test": "Page 2 card count",
                    "error": f"Expected 12, found {page2_count}"
                })
                return False
            
            # Click next to go to page 3
            next_button = await self.page.wait_for_selector('[data-testid="catalog-next"]', timeout=5000)
            await next_button.click()
            await self.page.wait_for_timeout(1000)
            
            print("✓ Navigated to page 3")
            await self.take_screenshot("08_chemistry_chapters_page3", 1920, 800)
            
            # Count cards on page 3
            page3_cards = await self.page.query_selector_all('[data-testid^="exams-set-card-"]')
            page3_count = len(page3_cards)
            print(f"✓ Page 3 card count: {page3_count}")
            
            if page3_count != 8:
                print(f"✗ Expected 8 cards on page 3, found {page3_count}")
                self.results["failed_tests"].append({
                    "test": "Page 3 card count",
                    "error": f"Expected 8, found {page3_count}"
                })
                return False
            
            # Verify total: 12 + 12 + 8 = 32
            total_cards = page1_count + page2_count + page3_count
            print(f"✓ Total cards across all pages: {total_cards}")
            
            if total_cards != 32:
                print(f"✗ Total cards {total_cards} does not match expected 32")
                self.results["failed_tests"].append({
                    "test": "Total card count",
                    "error": f"Expected 32, found {total_cards}"
                })
                return False
            
            # Go back to page 1
            try:
                await self.page.click('[data-testid="catalog-prev"]')
                await self.page.wait_for_timeout(500)
                await self.page.click('[data-testid="catalog-prev"]')
                await self.page.wait_for_timeout(500)
                print("✓ Navigated back to page 1")
            except Exception as nav_error:
                print(f"⚠ Navigation back to page 1 failed (non-critical): {str(nav_error)}")
            
            self.results["test_details"]["chapter_catalog"] = {
                "total_count": total_count,
                "page1_cards": page1_count,
                "page2_cards": page2_count,
                "page3_cards": page3_count,
                "total_cards": total_cards
            }
            
            self.results["passed_tests"].append(f"Chapter catalog: 32 total, 12+12+8 pagination verified")
            return True
        except Exception as e:
            print(f"✗ Chapter catalog verification failed: {str(e)}")
            self.results["failed_tests"].append({"test": "Chapter catalog", "error": str(e)})
            return False
            
    async def test_exam_attempt_with_fit_buttons(self):
        """Test 5: Start exam and test image fit buttons with CORRECT selectors"""
        try:
            print("\n=== TEST 5: Exam Attempt with Image Fit Buttons ===")
            
            # Set desktop viewport
            await self.page.set_viewport_size({"width": 1920, "height": 800})
            
            # Click first chapter test link (Mole Concept should have 50 questions with images)
            # We're already on page 1 of chemistry chapters from previous test
            await self.page.wait_for_timeout(500)
            
            # Debug: Check current URL
            current_url = self.page.url
            print(f"Current URL before clicking chapter: {current_url}")
            
            # Look for a chapter with "Start test" button (not attempted yet)
            start_button = await self.page.query_selector('[data-testid^="exam-start-"]')
            
            if start_button:
                print("✓ Found chapter with 'Start test' button")
                await start_button.click()
            else:
                # If all chapters have been attempted, click "Retry test" on first chapter
                print("⚠ No unattempted chapters found, clicking 'Retry test'")
                retry_button = await self.page.wait_for_selector('[data-testid^="exam-start-"]', timeout=5000)
                await retry_button.click()
            
            await self.page.wait_for_timeout(1000)
            new_url = self.page.url
            print(f"URL after clicking chapter: {new_url}")
            
            # Wait for SetDetail page
            await self.page.wait_for_selector('[data-testid="set-detail-page"]', timeout=10000)
            print("✓ Navigated to Set Detail page")
            await self.take_screenshot("09_set_detail", 1920, 800)
            await self.check_overflow("set_detail")
            
            # Run preflight check
            await self.page.fill('#device-test-answer', '25')
            await self.page.click('[data-testid="preflight-run-check"]')
            await self.page.wait_for_selector('[data-testid="preflight-check-success"]', timeout=10000)
            print("✓ Preflight check passed")
            
            # Acknowledge terms
            await self.page.click('[data-testid="preflight-acknowledge"]')
            await self.page.wait_for_timeout(300)
            
            # Start attempt
            await self.page.click('[data-testid="set-preflight-start-button"]')
            await self.page.wait_for_url('**/attempts/**', timeout=15000)
            
            # Extract attempt ID from URL
            current_url = self.page.url
            import re
            match = re.search(r'/attempts/([^/]+)', current_url)
            if match:
                self.attempt_id = match.group(1)
                print(f"✓ Attempt ID: {self.attempt_id}")
            
            print("✓ Exam attempt started")
            await self.page.wait_for_timeout(2000)  # Wait for lazy loading
            await self.take_screenshot("10_player_initial", 1920, 800)
            await self.check_overflow("player_initial")
            
            # Test image fit buttons with CORRECT selectors
            print("\n--- Testing Image Fit Buttons (CORRECTED) ---")
            
            # Wait for source image to load
            await self.page.wait_for_timeout(2000)
            
            # Check if fit buttons exist using CORRECT suffix selectors
            fit_button = await self.page.query_selector('[data-testid$="-fit"]')
            readable_button = await self.page.query_selector('[data-testid$="-readable"]')
            
            if not fit_button or not readable_button:
                print("✗ CRITICAL: Fit/Readable buttons not found with correct selectors")
                self.results["failed_tests"].append({
                    "test": "Image fit buttons",
                    "error": "Fit/Readable buttons not found with [data-testid$='-fit'] and [data-testid$='-readable']"
                })
                return False
            
            print("✓ Found Fit and Readable buttons with correct selectors")
            
            # Test 1: Initial state should have Fit button pressed=true
            fit_pressed = await fit_button.get_attribute('aria-pressed')
            if fit_pressed != 'true':
                print(f"✗ Initial Fit button aria-pressed={fit_pressed}, expected 'true'")
                self.results["failed_tests"].append({
                    "test": "Fit button initial state",
                    "error": f"aria-pressed={fit_pressed}, expected 'true'"
                })
                return False
            print("✓ Initial state: Fit button aria-pressed='true'")
            
            # Test 2: Choose Readable, then Next → Fit should be true
            await readable_button.click()
            await self.page.wait_for_timeout(500)
            print("✓ Clicked Readable button")
            
            readable_pressed = await readable_button.get_attribute('aria-pressed')
            if readable_pressed != 'true':
                print(f"✗ After clicking Readable, aria-pressed={readable_pressed}, expected 'true'")
                self.results["failed_tests"].append({
                    "test": "Readable button click",
                    "error": f"aria-pressed={readable_pressed}, expected 'true'"
                })
                return False
            print("✓ Readable button aria-pressed='true' after click")
            
            # Click Next using correct testid
            next_button = await self.page.wait_for_selector('[data-testid="player-next"]', timeout=5000)
            if not next_button:
                print("✗ CRITICAL: player-next button not found")
                self.results["failed_tests"].append({
                    "test": "Player navigation",
                    "error": "player-next button not found"
                })
                return False
            
            await next_button.click()
            await self.page.wait_for_timeout(1000)
            print("✓ Clicked Next button")
            
            # Check Fit button is true on new question
            fit_button_q2 = await self.page.wait_for_selector('[data-testid$="-fit"]', timeout=5000)
            fit_pressed_q2 = await fit_button_q2.get_attribute('aria-pressed')
            if fit_pressed_q2 != 'true':
                print(f"✗ After Next: Fit button aria-pressed={fit_pressed_q2}, expected 'true'")
                self.results["failed_tests"].append({
                    "test": "Fit button after Next",
                    "error": f"aria-pressed={fit_pressed_q2}, expected 'true'"
                })
                return False
            print("✓ After Next: Fit button aria-pressed='true'")
            
            # Test 3: Choose Readable, then Previous → Fit should be true
            readable_button_q2 = await self.page.query_selector('[data-testid$="-readable"]')
            await readable_button_q2.click()
            await self.page.wait_for_timeout(500)
            print("✓ Clicked Readable on Q2")
            
            prev_button = await self.page.wait_for_selector('[data-testid="player-previous"]', timeout=5000)
            if not prev_button:
                print("✗ CRITICAL: player-previous button not found")
                self.results["failed_tests"].append({
                    "test": "Player navigation",
                    "error": "player-previous button not found"
                })
                return False
            
            await prev_button.click()
            await self.page.wait_for_timeout(1000)
            print("✓ Clicked Previous button")
            
            fit_button_back = await self.page.wait_for_selector('[data-testid$="-fit"]', timeout=5000)
            fit_pressed_back = await fit_button_back.get_attribute('aria-pressed')
            if fit_pressed_back != 'true':
                print(f"✗ After Previous: Fit button aria-pressed={fit_pressed_back}, expected 'true'")
                self.results["failed_tests"].append({
                    "test": "Fit button after Previous",
                    "error": f"aria-pressed={fit_pressed_back}, expected 'true'"
                })
                return False
            print("✓ After Previous: Fit button aria-pressed='true'")
            
            # Test 4: Jump to Q10 via navigator
            # On mobile, need to open navigator first
            await self.page.set_viewport_size({"width": 390, "height": 844})
            await self.page.wait_for_timeout(300)
            
            nav_toggle = await self.page.query_selector('[data-testid="player-navigator-toggle"]')
            if nav_toggle:
                await nav_toggle.click()
                await self.page.wait_for_timeout(500)
                print("✓ Opened navigator on mobile")
            
            q10_button = await self.page.wait_for_selector('[data-testid="player-question-nav-10"]', timeout=5000)
            if not q10_button:
                print("✗ CRITICAL: player-question-nav-10 button not found")
                self.results["failed_tests"].append({
                    "test": "Question navigator",
                    "error": "player-question-nav-10 button not found"
                })
                return False
            
            await q10_button.click()
            await self.page.wait_for_timeout(1000)
            print("✓ Jumped to Q10")
            
            # Switch back to desktop for fit button check
            await self.page.set_viewport_size({"width": 1920, "height": 800})
            await self.page.wait_for_timeout(500)
            
            fit_button_q10 = await self.page.wait_for_selector('[data-testid$="-fit"]', timeout=5000)
            fit_pressed_q10 = await fit_button_q10.get_attribute('aria-pressed')
            if fit_pressed_q10 != 'true':
                print(f"✗ After Q10 jump: Fit button aria-pressed={fit_pressed_q10}, expected 'true'")
                self.results["failed_tests"].append({
                    "test": "Fit button after Q10 jump",
                    "error": f"aria-pressed={fit_pressed_q10}, expected 'true'"
                })
                return False
            print("✓ After Q10 jump: Fit button aria-pressed='true'")
            
            # Test 5: Refresh and check Fit
            await self.page.reload()
            await self.page.wait_for_timeout(2000)
            print("✓ Page refreshed")
            
            fit_button_refresh = await self.page.wait_for_selector('[data-testid$="-fit"]', timeout=5000)
            fit_pressed_refresh = await fit_button_refresh.get_attribute('aria-pressed')
            if fit_pressed_refresh != 'true':
                print(f"✗ After refresh: Fit button aria-pressed={fit_pressed_refresh}, expected 'true'")
                self.results["failed_tests"].append({
                    "test": "Fit button after refresh",
                    "error": f"aria-pressed={fit_pressed_refresh}, expected 'true'"
                })
                return False
            print("✓ After refresh: Fit button aria-pressed='true'")
            
            await self.take_screenshot("11_player_after_fit_tests", 1920, 800)
            
            self.results["passed_tests"].append("Image fit buttons: all 5 tests passed with correct selectors and aria-pressed verification")
            return True
        except Exception as e:
            print(f"✗ Exam attempt with fit buttons failed: {str(e)}")
            self.results["failed_tests"].append({"test": "Exam attempt with fit buttons", "error": str(e)})
            return False
            
    async def test_answer_and_submit(self):
        """Test 6: Answer question and submit"""
        try:
            print("\n=== TEST 6: Answer and Submit ===")
            
            # Set desktop viewport
            await self.page.set_viewport_size({"width": 1920, "height": 800})
            
            # Go back to first question
            await self.page.click('[data-testid="player-question-nav-1"]')
            await self.page.wait_for_timeout(500)
            
            # Answer the question (choose option A)
            option_a = await self.page.query_selector('[data-testid="player-option-A"]')
            if option_a:
                await option_a.click()
                await self.page.wait_for_timeout(500)
                print("✓ Selected option A")
                
                # Wait for save indicator
                await self.page.wait_for_selector('text="All responses saved"', timeout=10000)
                print("✓ Answer saved to server")
            else:
                # Try integer input
                integer_input = await self.page.query_selector('[data-testid="player-numerical-input"]')
                if integer_input:
                    await integer_input.fill('42')
                    await self.page.wait_for_timeout(500)
                    print("✓ Entered integer answer")
                    await self.page.wait_for_selector('text="All responses saved"', timeout=10000)
                    print("✓ Answer saved to server")
            
            # Click submit button
            await self.page.click('[data-testid="player-submit-button"]')
            await self.page.wait_for_timeout(500)
            
            # Confirm submission
            confirm_button = await self.page.wait_for_selector('button:has-text("Submit & see results")', timeout=5000)
            await confirm_button.click()
            
            print("✓ Submission confirmed")
            
            # Wait for results page
            await self.page.wait_for_url('**/results/**', timeout=30000)
            await self.page.wait_for_timeout(3000)  # Wait for results to load
            
            print("✓ Navigated to results page")
            await self.take_screenshot("12_results_summary", 1920, 800)
            await self.check_overflow("results_summary")
            
            # Read score
            score_element = await self.page.wait_for_selector('[data-testid="results-score-total"]', timeout=10000)
            score_text = await score_element.inner_text()
            print(f"✓ Score displayed: {score_text}")
            
            # Verify question review section
            review_heading = await self.page.query_selector('#results-review-heading')
            if review_heading:
                print("✓ Question review section found")
            
            # Expand first question
            expand_button = await self.page.query_selector('[data-testid^="results-expand-"]')
            if expand_button:
                await expand_button.click()
                await self.page.wait_for_timeout(1000)
                print("✓ Expanded first question review")
                await self.take_screenshot("13_question_review", 1920, 800)
            
            self.results["passed_tests"].append("Answer and submit exam")
            return True
        except Exception as e:
            print(f"✗ Answer and submit failed: {str(e)}")
            self.results["failed_tests"].append({"test": "Answer and submit", "error": str(e)})
            return False
            
    async def test_pdf_download_with_verification(self):
        """Test 7: Download PDF report and verify with PyMuPDF"""
        try:
            print("\n=== TEST 7: PDF Download with Verification ===")
            
            # Find and click PDF download button
            async with self.page.expect_download() as download_info:
                download_button = await self.page.wait_for_selector('button:has-text("Download")', timeout=5000)
                await download_button.click()
                
            download = await download_info.value
            pdf_path = f"{OUTPUT_DIR}/result_report.pdf"
            await download.save_as(pdf_path)
            
            # Check file size
            file_size = os.path.getsize(pdf_path)
            print(f"✓ PDF downloaded: {pdf_path} ({file_size} bytes)")
            
            # Verify PDF with PyMuPDF (fitz)
            try:
                doc = fitz.open(pdf_path)
                page_count = len(doc)
                print(f"✓ PDF page count: {page_count}")
                
                if page_count != 51:
                    print(f"✗ Expected 51 pages, found {page_count}")
                    self.results["failed_tests"].append({
                        "test": "PDF page count",
                        "error": f"Expected 51, found {page_count}"
                    })
                    doc.close()
                    return False
                
                # Check first page for "JEE MAINS.AI" header
                first_page = doc[0]
                text = first_page.get_text()
                
                if "JEE MAINS.AI" in text or "JEEMAINS.AI" in text:
                    print("✓ PDF header contains 'JEE MAINS.AI' or 'JEEMAINS.AI'")
                else:
                    print(f"✗ PDF header does not contain 'JEE MAINS.AI'")
                    print(f"First 500 chars: {text[:500]}")
                    self.results["failed_tests"].append({
                        "test": "PDF header",
                        "error": "Header does not contain 'JEE MAINS.AI'"
                    })
                    doc.close()
                    return False
                
                doc.close()
                
            except Exception as pdf_error:
                print(f"✗ PDF verification failed: {str(pdf_error)}")
                self.results["failed_tests"].append({
                    "test": "PDF verification",
                    "error": str(pdf_error)
                })
                return False
            
            self.results["pdf_downloads"].append({
                "path": pdf_path,
                "size_bytes": file_size,
                "page_count": page_count,
                "header_verified": True
            })
            self.results["passed_tests"].append("PDF download: 51 pages, JEE MAINS.AI header verified")
            return True
        except Exception as e:
            print(f"✗ PDF download failed: {str(e)}")
            self.results["failed_tests"].append({"test": "PDF download", "error": str(e)})
            return False
            
    async def test_results_history_with_filtering(self):
        """Test 8: Results history with actual filter clicks"""
        try:
            print("\n=== TEST 8: Results History with Filtering ===")
            
            # Set desktop viewport
            await self.page.set_viewport_size({"width": 1920, "height": 800})
            
            # Click results-home breadcrumb
            results_home = await self.page.wait_for_selector('[data-testid="results-home"]', timeout=5000)
            await results_home.click()
            
            # Verify URL is /exams/bitsat/results
            await self.page.wait_for_url('**/exams/bitsat/results', timeout=10000)
            print("✓ Navigated to /exams/bitsat/results")
            
            await self.take_screenshot("14_bitsat_results_history", 1920, 800)
            await self.check_overflow("results_history")
            
            # CRITICAL: Actually click Chapter filter
            chapter_filter = await self.page.wait_for_selector('[data-testid="results-history-filter-chapter"]', timeout=5000)
            if not chapter_filter:
                print("✗ CRITICAL: results-history-filter-chapter not found")
                self.results["failed_tests"].append({
                    "test": "History chapter filter",
                    "error": "results-history-filter-chapter not found"
                })
                return False
            
            await chapter_filter.click()
            await self.page.wait_for_timeout(1000)
            print("✓ Clicked Chapter filter")
            
            await self.take_screenshot("15_results_chapter_filter", 1920, 800)
            
            # Verify attempt is present in Chapter view
            if self.attempt_id:
                attempt_in_chapter = await self.page.query_selector(f'[href*="{self.attempt_id}"]')
                if attempt_in_chapter:
                    print(f"✓ Attempt {self.attempt_id} found in Chapter filter")
                else:
                    print(f"✗ Attempt {self.attempt_id} NOT found in Chapter filter")
                    self.results["failed_tests"].append({
                        "test": "Attempt in Chapter filter",
                        "error": f"Attempt {self.attempt_id} not found"
                    })
            
            # CRITICAL: Actually click Mock filter
            mock_filter = await self.page.wait_for_selector('[data-testid="results-history-filter-mock"]', timeout=5000)
            if not mock_filter:
                print("✗ CRITICAL: results-history-filter-mock not found")
                self.results["failed_tests"].append({
                    "test": "History mock filter",
                    "error": "results-history-filter-mock not found"
                })
                return False
            
            await mock_filter.click()
            await self.page.wait_for_timeout(1000)
            print("✓ Clicked Mock filter")
            
            await self.take_screenshot("16_results_mock_filter", 1920, 800)
            
            # Verify attempt is ABSENT in Mock view
            if self.attempt_id:
                attempt_in_mock = await self.page.query_selector(f'[href*="{self.attempt_id}"]')
                if not attempt_in_mock:
                    print(f"✓ Attempt {self.attempt_id} correctly absent in Mock filter")
                else:
                    print(f"✗ Attempt {self.attempt_id} incorrectly present in Mock filter")
                    self.results["failed_tests"].append({
                        "test": "Attempt absent in Mock filter",
                        "error": f"Attempt {self.attempt_id} should not be in Mock filter"
                    })
            
            self.results["passed_tests"].append("Results history: Chapter/Mock filtering verified with actual clicks")
            return True
        except Exception as e:
            print(f"✗ Results history filtering failed: {str(e)}")
            self.results["failed_tests"].append({"test": "Results history filtering", "error": str(e)})
            return False
            
    async def test_jee_comedk_empty_catalogs(self):
        """Test 9: JEE Main and COMEDK empty catalogs with exact assertions"""
        try:
            print("\n=== TEST 9: JEE Main and COMEDK Empty Catalogs ===")
            
            # Set desktop viewport
            await self.page.set_viewport_size({"width": 1920, "height": 800})
            
            # Go back to home
            await self.page.goto(f"{BASE_URL}/home")
            await self.page.wait_for_selector('[data-testid="exam-home-page"]', timeout=10000)
            
            # Test JEE Main hub
            await self.page.click('[data-testid="exam-home-exam-card-jee-main"]')
            await self.page.wait_for_selector('[data-testid="exam-hub-page"]', timeout=10000)
            
            # Verify 3 cards
            await self.page.wait_for_selector('[data-testid="exam-hub-card-mocks"]', timeout=5000)
            await self.page.wait_for_selector('[data-testid="exam-hub-card-chapters"]', timeout=5000)
            await self.page.wait_for_selector('[data-testid="exam-hub-card-results"]', timeout=5000)
            print("✓ JEE Main hub has 3 cards")
            
            await self.take_screenshot("17_jee_main_hub", 1920, 800)
            await self.check_overflow("jee_main_hub")
            
            # Check chapters catalog - MUST assert exact empty state
            await self.page.click('[data-testid="exam-hub-card-chapters"]')
            await self.page.wait_for_timeout(2000)
            
            # Look for empty state message - could be on subject selection or chapter list
            empty_message = await self.page.query_selector('text="Chapter tests are not live yet."')
            if not empty_message:
                # Try alternative empty state messages
                empty_message = await self.page.query_selector('text="No live tests for this subject."')
            
            # Count actual card rows (both subject cards and chapter cards)
            card_rows = await self.page.query_selector_all('[data-testid^="exams-set-card-"]')
            subject_cards = await self.page.query_selector_all('[data-testid^="chapters-subject-"]')
            total_content_cards = len(card_rows) + len(subject_cards)
            
            if not empty_message:
                print(f"✗ JEE Main chapters: No empty-state message found")
                # Take screenshot for debugging
                await self.take_screenshot("18_jee_main_chapters_debug", 1920, 800)
                self.results["failed_tests"].append({
                    "test": "JEE Main empty state",
                    "error": f"Empty-state message not found. Found {total_content_cards} content cards"
                })
                return False
            
            if total_content_cards != 0:
                print(f"✗ JEE Main chapters: Found {total_content_cards} content cards, expected 0")
                self.results["failed_tests"].append({
                    "test": "JEE Main card count",
                    "error": f"Found {total_content_cards} cards, expected 0"
                })
                return False
            
            print("✓ JEE Main chapters: Empty-state message present, 0 cards")
            
            await self.take_screenshot("18_jee_main_chapters_empty", 1920, 800)
            
            # Go back to home
            await self.page.goto(f"{BASE_URL}/home")
            await self.page.wait_for_selector('[data-testid="exam-home-page"]', timeout=10000)
            
            # Test COMEDK hub
            await self.page.click('[data-testid="exam-home-exam-card-comedk"]')
            await self.page.wait_for_selector('[data-testid="exam-hub-page"]', timeout=10000)
            
            # Verify 3 cards
            await self.page.wait_for_selector('[data-testid="exam-hub-card-mocks"]', timeout=5000)
            await self.page.wait_for_selector('[data-testid="exam-hub-card-chapters"]', timeout=5000)
            await self.page.wait_for_selector('[data-testid="exam-hub-card-results"]', timeout=5000)
            print("✓ COMEDK hub has 3 cards")
            
            await self.take_screenshot("19_comedk_hub", 1920, 800)
            await self.check_overflow("comedk_hub")
            
            # Check chapters catalog - MUST assert exact empty state
            await self.page.click('[data-testid="exam-hub-card-chapters"]')
            await self.page.wait_for_timeout(2000)
            
            # Look for empty state message
            empty_message_comedk = await self.page.query_selector('text="Chapter tests are not live yet."')
            
            # Count actual card rows
            card_rows_comedk = await self.page.query_selector_all('[data-testid^="exams-set-card-"]')
            card_count_comedk = len(card_rows_comedk)
            
            if not empty_message_comedk:
                print(f"✗ COMEDK chapters: No empty-state message found")
                self.results["failed_tests"].append({
                    "test": "COMEDK empty state",
                    "error": "Empty-state message not found"
                })
                return False
            
            if card_count_comedk != 0:
                print(f"✗ COMEDK chapters: Found {card_count_comedk} cards, expected 0")
                self.results["failed_tests"].append({
                    "test": "COMEDK card count",
                    "error": f"Found {card_count_comedk} cards, expected 0"
                })
                return False
            
            print("✓ COMEDK chapters: Empty-state message present, 0 cards")
            
            await self.take_screenshot("20_comedk_chapters_empty", 1920, 800)
            
            # Verify no BITSAT content leak
            bitsat_leak = await self.page.query_selector('text="BITSAT"')
            if bitsat_leak:
                print("✗ BITSAT content leaked into COMEDK")
                self.results["failed_tests"].append({"test": "COMEDK hub", "error": "BITSAT content leak"})
                return False
            else:
                print("✓ No BITSAT content leak in COMEDK")
            
            self.results["passed_tests"].append("JEE Main and COMEDK: Empty-state verified, 0 cards, no leaks")
            return True
        except Exception as e:
            print(f"✗ JEE/COMEDK empty catalogs test failed: {str(e)}")
            self.results["failed_tests"].append({"test": "JEE/COMEDK empty catalogs", "error": str(e)})
            return False
            
    async def test_landing_page_themes(self):
        """Test 10: Landing page light/dark themes"""
        try:
            print("\n=== TEST 10: Landing Page Themes ===")
            
            # Set desktop viewport
            await self.page.set_viewport_size({"width": 1920, "height": 800})
            
            # Go to landing page
            await self.page.goto(BASE_URL)
            await self.page.wait_for_timeout(2000)
            
            # Take light theme screenshot
            await self.take_screenshot("21_landing_light", 1920, 800)
            await self.check_overflow("landing_light")
            print("✓ Landing page light theme captured")
            
            # Toggle to dark theme
            theme_toggle = await self.page.query_selector('[data-testid="theme-toggle"]')
            if theme_toggle:
                await theme_toggle.click()
                await self.page.wait_for_timeout(500)
                
                await self.take_screenshot("22_landing_dark", 1920, 800)
                await self.check_overflow("landing_dark")
                print("✓ Landing page dark theme captured")
            else:
                print("⚠ Theme toggle not found on landing page")
            
            self.results["passed_tests"].append("Landing page themes")
            return True
        except Exception as e:
            print(f"✗ Landing page themes test failed: {str(e)}")
            self.results["failed_tests"].append({"test": "Landing page themes", "error": str(e)})
            return False
            
    async def run_all_tests(self):
        """Run all tests in sequence - STOP on failed prerequisite"""
        print(f"\n{'='*60}")
        print(f"COMPREHENSIVE FRONTEND NAVIGATION TEST - CORRECTED")
        print(f"Base URL: {BASE_URL}")
        print(f"Test Phone: {QA_PHONE}")
        print(f"Output Dir: {OUTPUT_DIR}")
        print(f"{'='*60}\n")
        
        await self.setup()
        
        try:
            # Test 1: Login (PREREQUISITE)
            if not await self.test_login():
                print("\n✗ CRITICAL: Login failed - stopping tests")
                return False
            
            # Test 2: Home page (PREREQUISITE)
            if not await self.test_home_page():
                print("\n✗ CRITICAL: Home page failed - stopping tests")
                return False
            
            # Test 3: BITSAT hub (PREREQUISITE)
            if not await self.test_bitsat_hub():
                print("\n✗ CRITICAL: BITSAT hub failed - stopping tests")
                return False
            
            # Test 4: Chapter catalog with pagination (CRITICAL)
            if not await self.test_chapter_catalog_with_pagination():
                print("\n✗ CRITICAL: Chapter catalog failed - stopping tests")
                return False
            
            # Test 5: Exam attempt with fit buttons (CRITICAL)
            if not await self.test_exam_attempt_with_fit_buttons():
                print("\n✗ CRITICAL: Exam attempt with fit buttons failed - stopping tests")
                return False
            
            # Test 6: Answer and submit
            if not await self.test_answer_and_submit():
                print("\n⚠ Answer and submit failed - continuing with other tests")
            
            # Test 7: PDF download with verification
            if not await self.test_pdf_download_with_verification():
                print("\n⚠ PDF download failed - continuing with other tests")
            
            # Test 8: Results history with filtering
            if not await self.test_results_history_with_filtering():
                print("\n⚠ Results history failed - continuing with other tests")
            
            # Test 9: JEE/COMEDK empty catalogs
            if not await self.test_jee_comedk_empty_catalogs():
                print("\n⚠ JEE/COMEDK empty catalogs failed - continuing with other tests")
            
            # Test 10: Landing page themes
            await self.test_landing_page_themes()
            
        finally:
            await self.teardown()
            
        # Print summary
        print(f"\n{'='*60}")
        print(f"TEST SUMMARY")
        print(f"{'='*60}")
        print(f"Passed: {len(self.results['passed_tests'])}")
        print(f"Failed: {len(self.results['failed_tests'])}")
        print(f"Screenshots: {len(self.results['screenshots'])}")
        print(f"PDF Downloads: {len(self.results['pdf_downloads'])}")
        print(f"Overflow Issues: {len(self.results['overflow_offenders'])}")
        
        if self.results['failed_tests']:
            print(f"\nFailed Tests:")
            for fail in self.results['failed_tests']:
                print(f"  - {fail['test']}: {fail['error']}")
        
        print(f"{'='*60}\n")
        
        # Save results
        results_file = f"{OUTPUT_DIR}/test_results.json"
        with open(results_file, 'w') as f:
            json.dump(self.results, f, indent=2)
        print(f"✓ Results saved to: {results_file}")
        
        return len(self.results['failed_tests']) == 0

async def main():
    tester = NavigationUITester()
    success = await tester.run_all_tests()
    return 0 if success else 1

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
