"""
Setup script for browser deadline test
Creates a 2-question timed set and saves context for browser test
"""
import sys
import json
import os
import uuid
from pymongo import MongoClient
from dotenv import load_dotenv

# Load environment variables
load_dotenv('/app/backend/.env')

# Configuration
MONGO_URL = os.getenv('MONGO_URL', 'mongodb://localhost:27017')
DB_NAME = os.getenv('DB_NAME', 'test_database')

# Load fixture data
with open('/app/memory/qa_context.json', 'r') as f:
    fixture = json.load(f)

SOURCE_SET_ID = fixture['set_id']
PHONE = fixture['phone']

print("=" * 80)
print("BROWSER DEADLINE TEST SETUP")
print("=" * 80)

# Connect to MongoDB
client = MongoClient(MONGO_URL)
db = client[DB_NAME]

# Get original set
original_set = db.tejas_sets.find_one({"id": SOURCE_SET_ID}, {"_id": 0})
if not original_set:
    print(f"❌ FAIL: Could not find source set {SOURCE_SET_ID}")
    sys.exit(1)

questions = original_set.get('questions', [])
if len(questions) < 2:
    print(f"❌ FAIL: Source set has less than 2 questions")
    sys.exit(1)

# Take first 2 questions
two_questions = questions[:2]

# Create new set ID
test_set_id = f"qa-timed-2q-{uuid.uuid4()}"

# Clone with modifications
test_set = {
    **original_set,
    "id": test_set_id,
    "title": "QA Timed Test (2 questions, 0.5 min)",
    "questions": two_questions,
    "qa_only": True,
    "status": "published",
    "restricted": True,
    "allowed_phones": [PHONE],
    "duration": 0.5,  # 0.5 minutes = 30 seconds
    "version": 1,
    "revision": 0,
}

db.tejas_sets.insert_one(test_set)

print(f"✅ Created timed QA set: {test_set_id}")
print(f"   Questions: 2")
print(f"   Duration: 0.5 minutes (30 seconds)")
print(f"   Q1 ID: {two_questions[0]['id']}")
print(f"   Q1 Correct: {two_questions[0]['answer']}")
print(f"   Q2 ID: {two_questions[1]['id']}")
print(f"   Q2 Correct: {two_questions[1]['answer']}")

# Save context for browser test
test_context = {
    "test_set_id": test_set_id,
    "phone": PHONE,
    "q1_id": two_questions[0]['id'],
    "q1_correct": two_questions[0]['answer'],
    "q2_id": two_questions[1]['id'],
    "q2_correct": two_questions[1]['answer'],
    "duration_seconds": 30
}

with open('/app/test_reports/deadline_browser_context.json', 'w') as f:
    json.dump(test_context, f, indent=2)

print(f"\n✅ Test context saved to /app/test_reports/deadline_browser_context.json")
print("=" * 80)
