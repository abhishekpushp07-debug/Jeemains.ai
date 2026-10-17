"""
Complete deadline test with manual deadline setting
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
print("DEADLINE TEST WITH MANUAL DEADLINE")
print("=" * 80)

# Connect to MongoDB
client = MongoClient(MONGO_URL)
db = client[DB_NAME]

# Step 1: Create 2-question set
print("\n📦 Step 1: Create 2-question test set")
original_set = db.tejas_sets.find_one({"id": SOURCE_SET_ID}, {"_id": 0})
questions = original_set.get('questions', [])[:2]

test_set_id = f"qa-deadline-{uuid.uuid4()}"
test_set = {
    **original_set,
    "id": test_set_id,
    "title": "Deadline Test (2Q, 30s)",
    "questions": questions,
    "qa_only": True,
    "status": "published",
    "restricted": True,
    "allowed_phones": [PHONE],
}

db.tejas_sets.insert_one(test_set)
print(f"✅ Created set: {test_set_id}")
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

print(f"✅ Authenticated")

# Preflight
response = session.post(
    f"{BASE_URL}/api/sets/{test_set_id}/preflight",
    json={"preview": False, "test_response": "test"}
)

# Start
start_key = f"deadline-test-{int(time.time() * 1000000)}"
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

print(f"✅ Started attempt: {attempt_id}")

# Step 3: Save Q1 answer via API
print("\n💾 Step 3: Save Q1 answer")
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
    print(f"⚠️  Q1 save failed: {response.status_code}")

# Step 4: Set deadline to 30 seconds from now
print("\n⏰ Step 4: Set deadline to 30 seconds from now")
deadline = time.time() + 30

result = db.tejas_attempts.update_one(
    {"id": attempt_id},
    {"$set": {"deadline": deadline}}
)

if result.modified_count > 0:
    print(f"✅ Deadline set to {deadline}")
    print(f"   Expires in 30 seconds")
else:
    print(f"⚠️  Could not update deadline")

# Save context for browser test
context = {
    "test_set_id": test_set_id,
    "attempt_id": attempt_id,
    "phone": PHONE,
    "q1_id": q1_id,
    "q2_id": questions[1]['id'],
    "q2_answer": str(questions[1]['answer']),
    "deadline": deadline
}

with open('/app/test_reports/deadline_manual_context.json', 'w') as f:
    json.dump(context, f, indent=2)

print("\n✅ Setup complete")
print(f"📝 Context saved to /app/test_reports/deadline_manual_context.json")
print(f"📝 Attempt ID: {attempt_id}")
print(f"📝 Test Set ID: {test_set_id}")
print("\n⚠️  Run browser test within 30 seconds!")
