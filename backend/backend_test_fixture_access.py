#!/usr/bin/env python3
"""
Reproduce iteration 10 fixture access failure.
Test phone +12025550184 access to fixture qa75-ed384de5-896c-4d2a-abd6-ffb9cbde94d0
"""
import requests
import sys

BASE_URL = "https://campus-launch-2.preview.emergentagent.com"
PHONE = "+12025550184"
FIXTURE_ID = "qa75-ed384de5-896c-4d2a-abd6-ffb9cbde94d0"

class FixtureAccessTest:
    def __init__(self):
        self.session = requests.Session()
        self.tests_run = 0
        self.tests_passed = 0
        
    def log(self, message, success=None):
        """Log test results"""
        if success is True:
            print(f"✅ {message}")
            self.tests_passed += 1
        elif success is False:
            print(f"❌ {message}")
        else:
            print(f"🔍 {message}")
        self.tests_run += 1 if success is not None else 0
    
    def test_phone_login(self):
        """Test phone login"""
        self.log(f"Testing phone login with {PHONE}")
        try:
            response = self.session.post(
                f"{BASE_URL}/api/auth/phone",
                json={"phone": PHONE},
                timeout=10
            )
            
            # Check cookies
            cookies = self.session.cookies.get_dict()
            self.log(f"Cookies after login: {list(cookies.keys())}")
            
            if response.status_code == 200:
                data = response.json()
                # Handle wrapped response
                user_data = data.get('data', data)
                self.log(f"Phone login successful - User ID: {user_data.get('id')}, Phone: {user_data.get('phone')}", True)
                return True
            else:
                self.log(f"Phone login failed - Status: {response.status_code}, Body: {response.text}", False)
                return False
        except Exception as e:
            self.log(f"Phone login error: {str(e)}", False)
            return False
    
    def test_session_check(self):
        """Verify session is active"""
        self.log("Checking session status")
        try:
            response = self.session.get(f"{BASE_URL}/api/auth/session", timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                # Handle wrapped response
                response_data = data.get('data', data)
                user = response_data.get('user')
                if user:
                    self.log(f"Session active - Phone: {user.get('phone')}, ID: {user.get('id')}", True)
                    return True
                else:
                    self.log("Session check returned no user", False)
                    return False
            else:
                self.log(f"Session check failed - Status: {response.status_code}", False)
                return False
        except Exception as e:
            self.log(f"Session check error: {str(e)}", False)
            return False
    
    def test_catalog_access(self):
        """Test if fixture appears in catalog"""
        self.log("Testing catalog access for JEE Main")
        try:
            response = self.session.get(
                f"{BASE_URL}/api/my/sets?exam=JEE%20Main&q=&page=1",
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                # Handle wrapped response
                response_data = data.get('data', data)
                items = response_data.get('items', [])
                self.log(f"Catalog returned {len(items)} items")
                
                # Check if our fixture is in the list
                fixture_found = any(item.get('id') == FIXTURE_ID for item in items)
                
                if fixture_found:
                    self.log(f"Fixture {FIXTURE_ID} FOUND in catalog", True)
                    return True
                else:
                    self.log(f"Fixture {FIXTURE_ID} NOT FOUND in catalog", False)
                    self.log(f"Available fixtures: {[item.get('id') for item in items]}")
                    return False
            else:
                self.log(f"Catalog access failed - Status: {response.status_code}, Body: {response.text}", False)
                return False
        except Exception as e:
            self.log(f"Catalog access error: {str(e)}", False)
            return False
    
    def test_direct_access(self):
        """Test direct access to fixture via /my/sets/{id}"""
        self.log(f"Testing direct access to /my/sets/{FIXTURE_ID}")
        try:
            response = self.session.get(
                f"{BASE_URL}/api/my/sets/{FIXTURE_ID}",
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                # Handle wrapped response
                response_data = data.get('data', data)
                self.log(f"Direct access successful - Title: {response_data.get('title')}", True)
                return True
            elif response.status_code == 404:
                error_data = response.json()
                error_detail = error_data.get('detail') if isinstance(error_data, dict) else error_data
                self.log(f"Direct access returned 404 - Message: {error_detail}", False)
                return False
            else:
                self.log(f"Direct access failed - Status: {response.status_code}, Body: {response.text}", False)
                return False
        except Exception as e:
            self.log(f"Direct access error: {str(e)}", False)
            return False
    
    def test_public_endpoint(self):
        """Test public endpoint /sets/{id} (should fail for restricted)"""
        self.log(f"Testing public endpoint /sets/{FIXTURE_ID}")
        try:
            response = self.session.get(
                f"{BASE_URL}/api/sets/{FIXTURE_ID}",
                timeout=10
            )
            
            if response.status_code == 404:
                self.log(f"Public endpoint correctly returns 404 - Message: {response.json().get('detail', 'No detail')}", True)
                return True
            elif response.status_code == 200:
                self.log(f"Public endpoint unexpectedly returned 200 - restricted fixture should not be public", False)
                return False
            else:
                self.log(f"Public endpoint returned unexpected status: {response.status_code}", False)
                return False
        except Exception as e:
            self.log(f"Public endpoint error: {str(e)}", False)
            return False
    
    def run_all_tests(self):
        """Run all tests in sequence"""
        print("=" * 80)
        print("FIXTURE ACCESS REPRODUCTION TEST")
        print(f"Phone: {PHONE}")
        print(f"Fixture: {FIXTURE_ID}")
        print(f"Backend: {BASE_URL}")
        print("=" * 80)
        print()
        
        # Test sequence
        if not self.test_phone_login():
            print("\n❌ Cannot proceed - phone login failed")
            return False
        
        print()
        if not self.test_session_check():
            print("\n❌ Cannot proceed - session check failed")
            return False
        
        print()
        self.test_catalog_access()
        
        print()
        self.test_direct_access()
        
        print()
        self.test_public_endpoint()
        
        print()
        print("=" * 80)
        print(f"RESULTS: {self.tests_passed}/{self.tests_run} tests passed")
        print("=" * 80)
        
        return self.tests_passed == self.tests_run

def main():
    tester = FixtureAccessTest()
    success = tester.run_all_tests()
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())
