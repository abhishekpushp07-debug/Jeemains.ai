"""
Withdraw old iteration 15 test fixtures
"""
import sys
import json
import os
import requests
from pymongo import MongoClient
from dotenv import load_dotenv

load_dotenv('/app/backend/.env')
load_dotenv('/app/frontend/.env')

BASE_URL = os.getenv('REACT_APP_BACKEND_URL')
MONGO_URL = os.getenv('MONGO_URL')
DB_NAME = os.getenv('DB_NAME')
ADMIN_EMAIL = os.getenv('ADMIN_EMAIL')
ADMIN_PASSWORD = os.getenv('ADMIN_PASSWORD')

print("=" * 80)
print("WITHDRAW OLD TEST FIXTURES")
print("=" * 80)

# Connect to MongoDB
client = MongoClient(MONGO_URL)
db = client[DB_NAME]

# Get all test sets created during iteration 15
test_sets = list(db.tejas_sets.find({
    "$or": [
        {"id": {"$regex": "^qa-timed-"}},
        {"id": {"$regex": "^qa-deadline-"}}
    ]
}, {"_id": 0, "id": 1, "title": 1, "status": 1}))

print(f"\nFound {len(test_sets)} test sets:")
for s in test_sets:
    print(f"  - {s['id']}: {s['title']} ({s['status']})")

# Authenticate as owner
session = requests.Session()
response = session.post(f"{BASE_URL}/api/auth/login", json={
    "email": ADMIN_EMAIL,
    "password": ADMIN_PASSWORD
})

if response.status_code != 200:
    print(f"\n❌ Owner login failed: {response.status_code}")
    sys.exit(1)

print(f"\n✅ Authenticated as owner")

# Withdraw each set
withdrawn_count = 0
for s in test_sets:
    set_id = s['id']
    
    # Update status to 'withdrawn' via MongoDB
    result = db.tejas_sets.update_one(
        {"id": set_id},
        {"$set": {"status": "withdrawn"}}
    )
    
    if result.modified_count > 0:
        print(f"✅ Withdrawn: {set_id}")
        withdrawn_count += 1
    else:
        print(f"⚠️  Already withdrawn or not found: {set_id}")

print(f"\n✅ Withdrawn {withdrawn_count} test sets")
print("\nNote: Sets are marked as 'withdrawn' in database")
print("They will no longer appear in public catalog")
