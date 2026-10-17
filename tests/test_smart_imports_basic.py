"""
Basic smart imports test - health, auth, and quota check
"""
import requests
import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv(Path(__file__).parent.parent / 'backend' / '.env')

BASE_URL = "https://campus-launch-2.preview.emergentagent.com"
ADMIN_EMAIL = os.environ.get('ADMIN_EMAIL')
ADMIN_PASSWORD = os.environ.get('ADMIN_PASSWORD')

def test_health():
    """Test health endpoint"""
    print("\n1. Testing health endpoint...")
    response = requests.get(f"{BASE_URL}/api/health")
    assert response.status_code == 200, f"Health check failed: {response.status_code}"
    data = response.json()
    assert data.get('data', {}).get('status') == 'ok', "Health status not ok"
    print("✅ Health endpoint working")
    return True

def test_openapi():
    """Test OpenAPI endpoint"""
    print("\n2. Testing OpenAPI endpoint...")
    response = requests.get(f"{BASE_URL}/api/openapi.json")
    assert response.status_code == 200, f"OpenAPI check failed: {response.status_code}"
    data = response.json()
    assert 'openapi' in data, "OpenAPI schema missing"
    assert 'paths' in data, "OpenAPI paths missing"
    
    # Check for smart_imports endpoints
    paths = data.get('paths', {})
    assert '/api/studio/auto-imports' in paths, "Smart imports endpoint missing"
    print(f"✅ OpenAPI schema valid (version {data.get('openapi')})")
    print(f"   Found {len(paths)} API endpoints")
    return True

def test_owner_login():
    """Test owner authentication"""
    print("\n3. Testing owner login...")
    session = requests.Session()
    response = session.post(
        f"{BASE_URL}/api/auth/login",
        json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD,
            "name": "Test Owner",
            "exam": "JEE Main",
            "consent": False
        }
    )
    assert response.status_code == 200, f"Login failed: {response.status_code} - {response.text}"
    data = response.json()
    user_data = data.get('data', {})
    assert user_data.get('role') == 'owner', f"Expected owner role, got {user_data.get('role')}"
    print(f"✅ Owner login successful: {user_data.get('email')}")
    return session

def test_quota_status(session):
    """Test AI quota status"""
    print("\n4. Testing AI quota status...")
    response = session.get(f"{BASE_URL}/api/studio/auto-imports")
    assert response.status_code == 200, f"Quota check failed: {response.status_code}"
    data = response.json()
    quota = data.get('data', {}).get('quota', {})
    print(f"✅ AI Quota: {quota.get('used', 0)}/{quota.get('limit', 0)} used")
    print(f"   Remaining: {quota.get('remaining', 0)} calls")
    return quota

def test_imports_list(session):
    """Test listing imports"""
    print("\n5. Testing imports list...")
    response = session.get(f"{BASE_URL}/api/studio/auto-imports")
    assert response.status_code == 200, f"List imports failed: {response.status_code}"
    data = response.json()
    items = data.get('data', {}).get('items', [])
    print(f"✅ Found {len(items)} existing imports")
    return items

def main():
    """Run all basic tests"""
    print("="*80)
    print("SMART IMPORTS BASIC BACKEND TEST")
    print("="*80)
    
    try:
        # Test 1: Health
        test_health()
        
        # Test 2: OpenAPI
        test_openapi()
        
        # Test 3: Authentication
        session = test_owner_login()
        
        # Test 4: Quota
        quota = test_quota_status(session)
        
        # Test 5: List imports
        imports = test_imports_list(session)
        
        print("\n" + "="*80)
        print("✅ ALL BASIC TESTS PASSED")
        print("="*80)
        return 0
        
    except AssertionError as e:
        print(f"\n❌ TEST FAILED: {str(e)}")
        return 1
    except Exception as e:
        print(f"\n❌ UNEXPECTED ERROR: {str(e)}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    exit(main())
