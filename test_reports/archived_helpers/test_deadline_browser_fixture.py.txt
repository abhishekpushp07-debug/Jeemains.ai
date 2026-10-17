"""
Create deadline test fixture for browser testing
Creates SET ONLY (not attempt) - browser will start attempt
"""
import sys
import json
import os
import uuid
from pymongo import MongoClient
from dotenv import load_dotenv

load_dotenv('/app/backend/.env')
load_dotenv('/app/frontend/.env')

MONGO_URL = os.getenv('MONGO_URL')
DB_NAME = os.getenv('DB_NAME')
PHONE = "+12025550184"

with open('/app/memory/qa_context.json', 'r') as f:
    fixture = json.load(f)

SOURCE_SET_ID = fixture['set_id']

print("=" * 80)
print("CREATE DEADLINE TEST FIXTURE (SET ONLY)")
print("=" * 80)

# Connect to MongoDB
client = MongoClient(MONGO_URL)
db = client[DB_NAME]

# Create 2-question set with rules.minutes = 0.5
print("\n📦 Creating 2-question test set with rules.minutes = 0.5")
original_set = db.tejas_sets.find_one({"id": SOURCE_SET_ID}, {"_id": 0})
questions = original_set.get('questions', [])[:2]

test_set_id = f"qa-timed-browser-{uuid.uuid4()}"
test_set = {
    **original_set,
    "id": test_set_id,
    "title": "Deadline Browser Test (2Q, 30s)",
    "questions": questions,
    "qa_only": True,
    "status": "published",
    "audience": "restricted",
    "allowed_phones": [PHONE],
    "allowed_emails": [],
    "rules": {
        "minutes": 0.5,  # 30 seconds
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

# Save context for browser test
context = {
    "test_set_id": test_set_id,
    "phone": PHONE,
    "q1_id": questions[0]['id'],
    "q1_answer": str(questions[0]['answer']),
    "q2_id": questions[1]['id'],
    "q2_answer": str(questions[1]['answer']),
    "duration_seconds": 30
}

with open('/app/test_reports/deadline_browser_fixture.json', 'w') as f:
    json.dump(context, f, indent=2)

print("\n✅ Fixture created")
print(f"📝 Context saved to /app/test_reports/deadline_browser_fixture.json")
print(f"📝 Test Set ID: {test_set_id}")
print("\n🎯 Ready for browser test!")
print("   Browser will: login → preflight → start → save Q1 → offline Q2 → wait 30s → reconnect")
