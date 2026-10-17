"""
Additional verification tests for PDF reports and specific attempt access.
"""
import requests
import sys
import json
from pathlib import Path
from datetime import datetime, timezone

# Load environment
import os
from dotenv import load_dotenv
load_dotenv(Path(__file__).parent.parent / '.env')
load_dotenv(Path(__file__).parent.parent.parent / 'frontend' / '.env')

BASE_URL = os.environ['REACT_APP_BACKEND_URL']
OWNER_EMAIL = os.environ.get('ADMIN_EMAIL', '')
OWNER_PASSWORD = os.environ.get('ADMIN_PASSWORD', '')

# Known attempt ID from test reports
EXISTING_ATTEMPT_ID = "273f767b-efe3-47b2-9f0f-b14d7ed837be"

# Test phone numbers
TEST_PHONE_OWNER = "+12025550184"  # Phone that owns attempt 273f...
OTHER_PHONE = "+12025550188"  # Different phone for "other student" test

class TestResults:
    def __init__(self):
        self.tests_run = 0
        self.tests_passed = 0
        self.tests_failed = 0
        self.results = []
    
    def record(self, name, passed, details=""):
        self.tests_run += 1
        if passed:
            self.tests_passed += 1
            print(f"✅ {name}")
        else:
            self.tests_failed += 1
            print(f"❌ {name}: {details}")
        self.results.append({
            "test": name,
            "passed": passed,
            "details": details
        })
    
    def summary(self):
        print(f"\n{'='*70}")
        print(f"TESTS COMPLETED: {self.tests_passed}/{self.tests_run} passed, {self.tests_failed} failed")
        print(f"{'='*70}")
        return self.tests_failed == 0

results = TestResults()

def test_existing_attempt_access():
    """Test that existing own result 273f... returns 200"""
    print("\n🔍 Testing existing attempt access...")
    
    # Login with test phone (owner of the attempt)
    session = requests.Session()
    response = session.post(
        f"{BASE_URL}/api/auth/phone",
        json={"phone": TEST_PHONE_OWNER},
        timeout=30
    )
    
    if response.status_code != 200:
        results.record("Phone auth for attempt test", False, f"Status {response.status_code}")
        return
    
    # Try to access the existing attempt
    response = session.get(
        f"{BASE_URL}/api/attempts/{EXISTING_ATTEMPT_ID}",
        timeout=30
    )
    
    results.record(
        f"Existing own result {EXISTING_ATTEMPT_ID[:8]}... returns 200",
        response.status_code == 200,
        f"Status {response.status_code}"
    )
    
    # If successful, check if it has a report job
    if response.status_code == 200:
        attempt_data = response.json()
        if isinstance(attempt_data, dict):
            attempt = attempt_data.get('data', attempt_data)
            print(f"  Attempt status: {attempt.get('status')}, grading: {attempt.get('grading_status')}")

def test_pdf_report_download():
    """Test PDF report download for existing attempt"""
    print("\n🔍 Testing PDF report download...")
    
    # Login with test phone (owner of the attempt)
    session = requests.Session()
    response = session.post(
        f"{BASE_URL}/api/auth/phone",
        json={"phone": TEST_PHONE_OWNER},
        timeout=30
    )
    
    if response.status_code != 200:
        results.record("Phone auth for PDF test", False, f"Status {response.status_code}")
        return
    
    # Report job ID
    report_job_id = f"report-{EXISTING_ATTEMPT_ID}-original"
    
    # Try to download the PDF using the download endpoint
    response = session.get(
        f"{BASE_URL}/api/jobs/{report_job_id}/download",
        timeout=30
    )
    
    results.record(
        "PDF report download returns 200 for owner",
        response.status_code == 200,
        f"Status {response.status_code}"
    )
    
    if response.status_code == 200:
        print(f"  PDF size: {len(response.content)} bytes")
    
    # Now test with other student (should get 404)
    other_session = requests.Session()
    response = other_session.post(
        f"{BASE_URL}/api/auth/phone",
        json={"phone": OTHER_PHONE},
        timeout=30
    )
    
    if response.status_code == 200:
        response = other_session.get(
            f"{BASE_URL}/api/jobs/{report_job_id}/download",
            timeout=30
        )
        
        results.record(
            "PDF report download returns 404 for other student",
            response.status_code in [404, 403],
            f"Status {response.status_code}"
        )
    else:
        results.record("Other student auth", False, f"Status {response.status_code}")

def test_owner_not_throttled():
    """Test that real owner/test student phone is NOT throttled"""
    print("\n🔍 Testing owner phone NOT throttled...")
    
    # Make multiple requests with owner phone (should not be throttled)
    success_count = 0
    for i in range(3):
        response = requests.post(
            f"{BASE_URL}/api/auth/phone",
            json={"phone": TEST_PHONE_OWNER},
            timeout=30
        )
        if response.status_code == 200:
            success_count += 1
    
    results.record(
        "Owner phone NOT throttled (3 requests succeed)",
        success_count == 3,
        f"{success_count}/3 succeeded"
    )

def main():
    print("="*70)
    print("ADDITIONAL VERIFICATION TESTS - PDF & ACCESS")
    print(f"Testing against: {BASE_URL}")
    print("="*70)
    
    # Run all tests
    test_existing_attempt_access()
    test_pdf_report_download()
    test_owner_not_throttled()
    
    # Print summary
    success = results.summary()
    
    # Save results
    output = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "base_url": BASE_URL,
        "summary": {
            "total": results.tests_run,
            "passed": results.tests_passed,
            "failed": results.tests_failed
        },
        "results": results.results
    }
    
    output_path = Path('/app/test_reports/additional_verification.json')
    with open(output_path, 'w') as f:
        json.dump(output, f, indent=2)
    
    print(f"\n📄 Results saved to: {output_path}")
    
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())
