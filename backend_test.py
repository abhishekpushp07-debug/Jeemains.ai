#!/usr/bin/env python3
"""
Backend API Testing for JEE Advanced Paper Source Module
Tests all main API endpoints for functionality
"""
import requests
import sys
import json
from datetime import datetime

# Use the public backend URL from frontend .env
BASE_URL = "https://campus-launch-2.preview.emergentagent.com"
API_PREFIX = "/api"
ADMIN_PREFIX = "/api/admin/jea"

class JEAAPITester:
    def __init__(self):
        self.base_url = BASE_URL
        self.tests_run = 0
        self.tests_passed = 0
        self.failed_tests = []
        self.results = {}

    def log_result(self, test_name, success, response_data=None, error=None):
        """Log test result"""
        self.tests_run += 1
        if success:
            self.tests_passed += 1
            print(f"✅ {test_name}: PASSED")
        else:
            print(f"❌ {test_name}: FAILED - {error}")
            self.failed_tests.append({"test": test_name, "error": str(error)})
        
        self.results[test_name] = {
            "status": "PASSED" if success else "FAILED", 
            "data": response_data,
            "error": str(error) if error else None
        }

    def test_health(self):
        """Test /api/health endpoint"""
        try:
            response = requests.get(f"{self.base_url}{API_PREFIX}/health", timeout=10)
            success = response.status_code == 200
            data = response.json() if success else None
            self.log_result("Health Check", success, data, 
                          f"Status {response.status_code}" if not success else None)
            return success, data
        except Exception as e:
            self.log_result("Health Check", False, None, e)
            return False, None

    def test_stats(self):
        """Test /api/admin/jea/stats endpoint"""
        try:
            response = requests.get(f"{self.base_url}{ADMIN_PREFIX}/stats", timeout=10)
            success = response.status_code == 200
            data = response.json() if success else None
            
            # Validate stats structure
            if success and data:
                required_keys = ["catalogs", "questions", "yearspec_sections"]
                if all(key in data for key in required_keys):
                    self.log_result("Stats API", success, data)
                else:
                    self.log_result("Stats API", False, data, "Missing required keys in stats response")
                    return False, data
            else:
                self.log_result("Stats API", success, data, 
                              f"Status {response.status_code}" if not success else None)
            return success, data
        except Exception as e:
            self.log_result("Stats API", False, None, e)
            return False, None

    def test_catalog_list(self):
        """Test /api/admin/jea/catalog endpoint"""
        try:
            response = requests.get(f"{self.base_url}{ADMIN_PREFIX}/catalog", timeout=10)
            success = response.status_code == 200
            data = response.json() if success else None
            
            # Should return an array (empty initially)
            if success and isinstance(data, list):
                self.log_result("Catalog List", success, {"count": len(data)})
            else:
                self.log_result("Catalog List", False, data, 
                              f"Expected array, got {type(data)}" if success else f"Status {response.status_code}")
            return success, data
        except Exception as e:
            self.log_result("Catalog List", False, None, e)
            return False, None

    def test_archive_sync(self):
        """Test /api/admin/jea/archive/sync endpoint (may fail due to external fetch)"""
        try:
            response = requests.post(
                f"{self.base_url}{ADMIN_PREFIX}/archive/sync?start_year=2021&end_year=2025&language=EN", 
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                self.log_result("Archive Sync", True, data)
                return True, data
            elif response.status_code == 400:
                # Expected if external fetch is disabled
                data = response.json()
                if "External fetch disabled" in data.get("detail", ""):
                    self.log_result("Archive Sync", True, data, "External fetch disabled (expected)")
                    return True, data
                else:
                    self.log_result("Archive Sync", False, data, f"Status 400: {data.get('detail')}")
                    return False, data
            elif response.status_code == 502:
                # Expected if external fetch fails
                data = response.json()
                self.log_result("Archive Sync", True, data, "External fetch failed (expected)")
                return True, data
            else:
                self.log_result("Archive Sync", False, None, f"Status {response.status_code}")
                return False, None
        except Exception as e:
            self.log_result("Archive Sync", False, None, e)
            return False, None

    def test_yearspec_list(self):
        """Test /api/admin/jea/yearspec endpoint"""
        try:
            response = requests.get(f"{self.base_url}{ADMIN_PREFIX}/yearspec", timeout=10)
            success = response.status_code == 200
            data = response.json() if success else None
            
            if success and isinstance(data, list):
                self.log_result("YearSpec List", success, {"count": len(data)})
            else:
                self.log_result("YearSpec List", False, data,
                              f"Expected array, got {type(data)}" if success else f"Status {response.status_code}")
            return success, data
        except Exception as e:
            self.log_result("YearSpec List", False, None, e)
            return False, None

    def test_questions_list(self):
        """Test /api/admin/jea/questions endpoint"""
        try:
            response = requests.get(f"{self.base_url}{ADMIN_PREFIX}/questions", timeout=10)
            success = response.status_code == 200
            data = response.json() if success else None
            
            if success and isinstance(data, list):
                self.log_result("Questions List", success, {"count": len(data)})
            else:
                self.log_result("Questions List", False, data,
                              f"Expected array, got {type(data)}" if success else f"Status {response.status_code}")
            return success, data
        except Exception as e:
            self.log_result("Questions List", False, None, e)
            return False, None

    def test_audit_logs(self):
        """Test /api/admin/jea/audit-logs endpoint"""
        try:
            response = requests.get(f"{self.base_url}{ADMIN_PREFIX}/audit-logs", timeout=10)
            success = response.status_code == 200
            data = response.json() if success else None
            
            if success and isinstance(data, list):
                self.log_result("Audit Logs", success, {"count": len(data)})
            else:
                self.log_result("Audit Logs", False, data,
                              f"Expected array, got {type(data)}" if success else f"Status {response.status_code}")
            return success, data
        except Exception as e:
            self.log_result("Audit Logs", False, None, e)
            return False, None

    def test_auto_assign_subjects(self):
        """Test auto-assign subjects functionality"""
        # First get catalogs to find a PARSED one
        try:
            response = requests.get(f"{self.base_url}{ADMIN_PREFIX}/catalog", timeout=10)
            if response.status_code == 200:
                catalogs = response.json()
                parsed_catalogs = [cat for cat in catalogs if cat.get("status") == "PARSED"]
                
                if not parsed_catalogs:
                    self.log_result("Auto-Assign Subjects", True, None, "No PARSED catalogs found (expected)")
                    return True, None
                
                # Test auto-assign on first PARSED catalog
                catalog = parsed_catalogs[0]
                response = requests.post(
                    f"{self.base_url}{ADMIN_PREFIX}/catalog/{catalog['id']}/auto-assign-subjects", 
                    timeout=30
                )
                
                if response.status_code == 200:
                    data = response.json()
                    expected_keys = ["total_questions", "assigned", "skipped", "by_subject", "details"]
                    if all(key in data for key in expected_keys):
                        self.log_result("Auto-Assign Subjects", True, data)
                        return True, data
                    else:
                        self.log_result("Auto-Assign Subjects", False, data, "Missing keys in response")
                        return False, data
                else:
                    error_data = response.json() if response.headers.get('content-type', '').startswith('application/json') else None
                    self.log_result("Auto-Assign Subjects", False, error_data, f"Status {response.status_code}")
                    return False, error_data
            else:
                self.log_result("Auto-Assign Subjects", False, None, "Could not fetch catalogs")
                return False, None
        except Exception as e:
            self.log_result("Auto-Assign Subjects", False, None, e)
            return False, None

    def test_detect_question_subject(self):
        """Test detect subject for individual question"""
        # First get questions to test detection
        try:
            response = requests.get(f"{self.base_url}{ADMIN_PREFIX}/questions", timeout=10)
            if response.status_code == 200:
                questions = response.json()
                
                if not questions:
                    self.log_result("Detect Question Subject", True, None, "No questions found (expected)")
                    return True, None
                
                # Test detection on first question
                question = questions[0]
                response = requests.post(
                    f"{self.base_url}{ADMIN_PREFIX}/questions/{question['id']}/detect-subject", 
                    timeout=15
                )
                
                if response.status_code == 200:
                    data = response.json()
                    expected_keys = ["current_subject", "detected_subject", "confidence", "matched_keywords"]
                    if all(key in data for key in expected_keys):
                        self.log_result("Detect Question Subject", True, data)
                        return True, data
                    else:
                        self.log_result("Detect Question Subject", False, data, "Missing keys in response")
                        return False, data
                else:
                    error_data = response.json() if response.headers.get('content-type', '').startswith('application/json') else None
                    self.log_result("Detect Question Subject", False, error_data, f"Status {response.status_code}")
                    return False, error_data
            else:
                self.log_result("Detect Question Subject", False, None, "Could not fetch questions")
                return False, None
        except Exception as e:
            self.log_result("Detect Question Subject", False, None, e)
            return False, None

    def run_all_tests(self):
        """Run all API tests"""
        print(f"🔍 Testing JEE Advanced Paper Source Module APIs")
        print(f"📍 Base URL: {self.base_url}")
        print("=" * 60)
        
        # Test basic endpoints
        self.test_health()
        self.test_stats()
        self.test_catalog_list()
        self.test_archive_sync()
        self.test_yearspec_list()
        self.test_questions_list()
        self.test_audit_logs()
        
        # Test new Auto-Assign Subject features
        self.test_auto_assign_subjects()
        self.test_detect_question_subject()
        
        print("=" * 60)
        print(f"📊 Test Summary: {self.tests_passed}/{self.tests_run} tests passed")
        
        if self.failed_tests:
            print("\n❌ Failed Tests:")
            for fail in self.failed_tests:
                print(f"  - {fail['test']}: {fail['error']}")
        
        return self.tests_passed, self.tests_run, self.results

def main():
    tester = JEAAPITester()
    passed, total, results = tester.run_all_tests()
    
    # Print results for debugging
    print(f"\n🔍 Detailed Results:")
    for test_name, result in results.items():
        status = result["status"]
        print(f"  {test_name}: {status}")
        if result.get("data"):
            print(f"    Data: {json.dumps(result['data'], indent=2)[:200]}...")
    
    return 0 if passed == total else 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)