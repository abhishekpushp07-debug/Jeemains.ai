#!/usr/bin/env python3
"""Create a QA fixture for browser testing"""
import sys
sys.path.insert(0, '/app/backend')

# Load environment variables first
from dotenv import load_dotenv
from pathlib import Path
load_dotenv(Path('/app/backend/.env'))

import asyncio
import uuid
from datetime import datetime, timezone, timedelta
from tejas import db as tejas_db, content, competitions

async def create_qa_fixture():
    """Create a QA fixture with ≥12 questions including MCQ with formula, integer, and wrapped long text"""
    
    # Initialize database
    await tejas_db.indexes()
    
    # Create import ID
    import_id = str(uuid.uuid4())
    
    # Create questions with various types
    questions = []
    
    # MCQ with formula (LaTeX)
    questions.append({
        "id": str(uuid.uuid4()),
        "number": 1,
        "type": "mcq",
        "subject": "Mathematics",
        "topic": "Fractions",
        "text": "What is the value of $\\frac{1}{2}$ + $\\frac{1}{4}$?",
        "options": {"A": "$\\frac{3}{4}$", "B": "$\\frac{1}{2}$", "C": "$\\frac{2}{3}$", "D": "$\\frac{1}{4}$"},
        "answer": "A",
        "disposition": "standard",
        "render_mode": "typed"
    })
    
    # Integer question
    questions.append({
        "id": str(uuid.uuid4()),
        "number": 2,
        "type": "integer",
        "subject": "Physics",
        "topic": "Kinematics",
        "text": "A car travels at 60 km/h for 2 hours. What is the total distance traveled in kilometers?",
        "answer": "120",
        "disposition": "standard",
        "render_mode": "typed"
    })
    
    # MCQ with wrapped long text
    questions.append({
        "id": str(uuid.uuid4()),
        "number": 3,
        "type": "mcq",
        "subject": "Chemistry",
        "topic": "Organic Chemistry",
        "text": "In organic chemistry, the process of converting alkanes to alkenes through the removal of hydrogen atoms is known as dehydrogenation. This process is commonly used in the petrochemical industry to produce important chemical intermediates. Which of the following catalysts is most commonly used for this reaction?",
        "options": {
            "A": "Platinum or palladium on alumina support at high temperatures",
            "B": "Sodium hydroxide in aqueous solution at room temperature",
            "C": "Sulfuric acid as a dehydrating agent under reflux conditions",
            "D": "Zinc dust in the presence of hydrochloric acid"
        },
        "answer": "A",
        "disposition": "standard",
        "render_mode": "typed"
    })
    
    # Add more questions to reach 12+
    for i in range(4, 13):
        if i % 2 == 0:
            # MCQ
            questions.append({
                "id": str(uuid.uuid4()),
                "number": i,
                "type": "mcq",
                "subject": ["Physics", "Chemistry", "Mathematics"][i % 3],
                "topic": f"Topic {i}",
                "text": f"Question {i}: What is the correct answer for this multiple choice question with formula $x^{i}$ = ?",
                "options": {"A": "Option A", "B": "Option B", "C": "Option C", "D": "Option D"},
                "answer": ["A", "B", "C", "D"][i % 4],
                "disposition": "standard",
                "render_mode": "typed"
            })
        else:
            # Integer
            questions.append({
                "id": str(uuid.uuid4()),
                "number": i,
                "type": "integer",
                "subject": ["Physics", "Chemistry", "Mathematics"][i % 3],
                "topic": f"Topic {i}",
                "text": f"Question {i}: Calculate the integer value for this problem.",
                "answer": str(i * 10),
                "disposition": "standard",
                "render_mode": "typed"
            })
    
    # Create import record
    import_record = {
        "id": import_id,
        "title": "QA Browser Test Fixture",
        "format": "xlsx",
        "status": "ready",
        "exam": "JEE Main",
        "duration_minutes": 180,
        "questions": questions,
        "issues": [],
        "created_at": datetime.now(timezone.utc).timestamp(),
        "qa_only": False  # Make it visible for students
    }
    
    # Insert import
    await tejas_db.db.tejas_imports.insert_one(import_record)
    print(f"✓ Created import: {import_id}")
    
    # Create a set (published content)
    set_record = {
        "id": import_id,
        "title": "QA Browser Test Fixture",
        "exam": "JEE Main",
        "duration_minutes": 180,
        "questions": questions,
        "rules": {"correct": 4, "wrong": -1, "skipped": 0, "minutes": 180},
        "revision": 1,
        "status": "published",  # CRITICAL: Must be published to be visible
        "audience": "all",  # Available to all users
        "created_at": datetime.now(timezone.utc).timestamp()
    }
    
    await tejas_db.db.tejas_sets.insert_one(set_record)
    print(f"✓ Created set (published): {import_id}")
    
    # Create a competition for testing
    competition_id = str(uuid.uuid4())
    now = datetime.now(timezone.utc)
    
    competition_record = {
        "id": competition_id,
        "import_id": import_id,
        "title": "QA Browser Test Competition",
        "exam": "JEE Main",
        "start_at": (now - timedelta(hours=1)).timestamp(),  # Started 1 hour ago
        "end_at": (now + timedelta(hours=2)).timestamp(),  # Ends in 2 hours
        "duration_minutes": 180,
        "live_enabled": True,
        "created_at": now.timestamp()
    }
    
    await tejas_db.db.tejas_competitions.insert_one(competition_record)
    print(f"✓ Created competition: {competition_id}")
    
    # Save IDs for testing
    fixture_data = {
        "import_id": import_id,
        "competition_id": competition_id,
        "question_count": len(questions),
        "created_at": now.isoformat()
    }
    
    import json
    with open('/app/test_reports/deep_visual_context.json', 'w') as f:
        json.dump(fixture_data, f, indent=2)
    
    print(f"\n✓ QA Fixture created successfully!")
    print(f"  Import ID: {import_id}")
    print(f"  Competition ID: {competition_id}")
    print(f"  Questions: {len(questions)}")
    print(f"  Saved to: /app/test_reports/deep_visual_context.json")
    
    return fixture_data

if __name__ == "__main__":
    asyncio.run(create_qa_fixture())
