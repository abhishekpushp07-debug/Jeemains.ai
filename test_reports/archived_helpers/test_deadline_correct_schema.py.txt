"""
Deadline test with CORRECT schema: rules.minutes (not top-level duration)
RCA confirmed: schema is rules.minutes NOT top-level duration!
"""
import sys
import json
import os
import uuid
import time
import requests
from pymongo import MongoClient
from dotenv import load_dotenv

load_dotenv('/app/backend/.env')
load_dotenv('/app/frontend/.env')

BASE_URL = os.getenv('REACT_APP_BACKEND_URL')
MONGO_URL = os.getenv('MONGO_URL')
DB_NAME = os.getenv('DB_NAME')
PHONE = "+12025550184"

with open('/app/memory/qa_context.json', 'r') as f:
    fixture = json.load(f)

SOURCE_SET_ID = fixture['set_id']

print("=" * 80)
print("DEADLINE TEST WITH CORRECT SCHEMA (rules.minutes)")
print("=" * 80)

# Connect to MongoDB
client = MongoClient(MONGO_URL)
db = client[DB_NAME]

# Step 1: Create 2-question set with rules.minutes = 0.5
print("\n📦 Step 1: Create 2-question test set with rules.minutes = 0.5")
original_set = db.tejas_sets.find_one({"id": SOURCE_SET_ID}, {"_id": 0})
questions = original_set.get('questions', [])[:2]

test_set_id = f"qa-timed-correct-{uuid.uuid4()}"
test_set = {
    **original_set,
    "id": test_set_id,
    "title": "Deadline Test Correct Schema (2Q, 30s)",
    "questions": questions,
    "qa_only": True,
    "status": "published",
    "audience": "restricted",
    "allowed_phones": [PHONE],
    "allowed_emails": [],
    "rules": {
        "minutes": 0.5,  # 30 seconds - CORRECT FIELD!
        "correct": 4,
        "wrong": -1,
        "skipped": 0,
        "navigation": "free",
        "numeric_policy": "integer_exact",
        "solution_release": "after_submit",
        "numeric_rule": "Exact integer value; signs, Unicode minus and leading zeros accepted; up to 20 digits. No decimals or rounding."
    }
}

db.tejas_sets.insert_one(test_set)
print(f"✅ Created set: {test_set_id}")
print(f"   rules.minutes: {test_set['rules']['minutes']}")
print(f"   Q1 ID: {questions[0]['id']}, Answer: {questions[0]['answer']}")
print(f"   Q2 ID: {questions[1]['id']}, Answer: {questions[1]['answer']}")

# Step 2: Start attempt via API
print("\n🚀 Step 2: Start attempt via API")
session = requests.Session()

# Phone auth
response = session.post(f"{BASE_URL}/api/auth/phone", json={"phone": PHONE})
if response.status_code != 200:
    print(f"❌ Phone auth failed: {response.status_code}")
    sys.exit(1)

print(f"✅ Authenticated with phone: {PHONE}")

# Preflight
response = session.post(
    f"{BASE_URL}/api/sets/{test_set_id}/preflight",
    json={"preview": False, "test_response": "test"}
)

if response.status_code != 200:
    print(f"❌ Preflight failed: {response.status_code}")
    sys.exit(1)

print(f"✅ Preflight passed")

# Start
start_key = f"deadline-correct-{int(time.time() * 1000000)}"
start_time = time.time()
response = session.post(
    f"{BASE_URL}/api/sets/{test_set_id}/start",
    json={"start_key": start_key, "device_checked": True, "preview": False}
)

if response.status_code != 200:
    print(f"❌ Start failed: {response.status_code}")
    print(f"   Response: {response.text[:500]}")
    sys.exit(1)

result = response.json()
attempt = result.get('data', result)
attempt_id = attempt.get('id')
started_at = attempt.get('started_at')
deadline = attempt.get('deadline')

print(f"✅ Started attempt: {attempt_id}")
print(f"   started_at: {started_at}")
print(f"   deadline: {deadline}")

# CRITICAL ASSERTION: deadline - started_at should be 30 seconds
if deadline and started_at:
    duration = deadline - started_at
    print(f"\n🔍 ASSERTION: deadline - started_at = {duration} seconds")
    if abs(duration - 30) < 1:
        print(f"✅ PASS: Duration is 30 seconds (rules.minutes * 60)")
    else:
        print(f"❌ FAIL: Expected 30 seconds, got {duration} seconds")
        sys.exit(1)
else:
    print(f"❌ FAIL: Missing deadline or started_at")
    sys.exit(1)

# Step 3: Save Q1 answer via API
print("\n💾 Step 3: Save Q1 answer (correct)")
q1_id = questions[0]['id']
q1_answer = str(questions[0]['answer'])

response = session.put(
    f"{BASE_URL}/api/attempts/{attempt_id}/answers/{q1_id}",
    json={
        "value": q1_answer,
        "marked": False,
        "revision": 1,
        "request_id": f"test-{int(time.time() * 1000000)}"
    }
)

if response.status_code == 200:
    print(f"✅ Q1 answer saved: {q1_answer}")
else:
    print(f"❌ Q1 save failed: {response.status_code}")
    sys.exit(1)

# Save context for browser test
context = {
    "test_set_id": test_set_id,
    "attempt_id": attempt_id,
    "phone": PHONE,
    "q1_id": q1_id,
    "q2_id": questions[1]['id'],
    "q2_answer": str(questions[1]['answer']),
    "started_at": started_at,
    "deadline": deadline,
    "duration_seconds": 30
}

with open('/app/test_reports/deadline_correct_context.json', 'w') as f:
    json.dump(context, f, indent=2)

print("\n✅ Backend test PASSED")
print(f"📝 Context saved to /app/test_reports/deadline_correct_context.json")
print(f"📝 Attempt ID: {attempt_id}")
print(f"📝 Test Set ID: {test_set_id}")
print(f"\n⏰ Deadline expires in ~{int(deadline - time.time())} seconds")
print("\n🎯 Ready for browser test!")
