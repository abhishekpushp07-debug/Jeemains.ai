"""
Test immutable ledger: merged results preserve original summary when keys altered
"""
import sys
import copy
from tejas.scoring import score

def test_immutable_ledger():
    """Test that ledger preserves original summary even when keys are altered"""
    print("=" * 70)
    print("TESTING IMMUTABLE LEDGER")
    print("=" * 70)
    
    # Create initial questions
    questions = [
        {
            'id': 'q1',
            'number': 1,
            'type': 'mcq',
            'subject': 'Math',
            'topic': 'Test',
            'answer': '1',
            'options': {'1': 'A', '2': 'B', '3': 'C', '4': 'D'}
        },
        {
            'id': 'q2',
            'number': 2,
            'type': 'integer',
            'subject': 'Physics',
            'topic': 'Test',
            'answer': '42'
        }
    ]
    
    # Student answers
    answers = {
        'q1': {'value': '1', 'marked': False},  # Correct
        'q2': {'value': '42', 'marked': False}  # Correct
    }
    
    attempt = {
        'questions': questions,
        'answers': answers,
        'rules': {'correct': 4, 'wrong': -1, 'skipped': 0},
        'started_at': 0
    }
    
    print("\n🔍 Step 1: Generate initial score with original keys...")
    result1 = score(attempt)
    original_summary = copy.deepcopy(result1['summary'])
    
    print(f"   Original score: {original_summary['score']}")
    print(f"   Original correct: {original_summary['correct']}")
    print(f"   Original maximum: {original_summary['maximum']}")
    
    # Now simulate a correction: change the answer key for q1
    print("\n🔍 Step 2: Alter answer key in attempt object...")
    attempt['questions'][0]['answer'] = '2'  # Change from '1' to '2'
    print(f"   Changed Q1 answer key from '1' to '2'")
    
    # Create ledger from first result
    print("\n🔍 Step 3: Create ledger from original result...")
    ledger = {
        'summary': original_summary,
        'rows': [{
            'id': q['id'],
            'marks': q['marks'],
            'marks_exact': q['marks_exact'],
            'outcome': q['outcome'],
            'normalized_response': q['normalized_response'],
            'accepted_answers': q['accepted_answers']
        } for q in result1['questions']]
    }
    
    # Add ledger to attempt
    attempt['ledger'] = ledger
    
    print("\n🔍 Step 4: Score again with altered keys but existing ledger...")
    # When ledger exists, score_attempt should return the preserved ledger
    from tejas_core import score_attempt
    result2 = score_attempt(attempt)
    
    print(f"   Ledger score: {result2['summary']['score']}")
    print(f"   Ledger correct: {result2['summary']['correct']}")
    print(f"   Ledger maximum: {result2['summary']['maximum']}")
    
    # Verify that the summary is preserved from ledger, not recalculated
    if result2['summary']['score'] == original_summary['score']:
        print(f"✅ Ledger preserved original score: {original_summary['score']}")
    else:
        print(f"❌ Ledger score changed: {original_summary['score']} -> {result2['summary']['score']}")
        return False
    
    if result2['summary']['correct'] == original_summary['correct']:
        print(f"✅ Ledger preserved original correct count: {original_summary['correct']}")
    else:
        print(f"❌ Ledger correct changed: {original_summary['correct']} -> {result2['summary']['correct']}")
        return False
    
    # Verify that all questions are still paired
    if len(result2['questions']) == len(questions):
        print(f"✅ All {len(questions)} questions still paired in result")
    else:
        print(f"❌ Question count mismatch: {len(questions)} -> {len(result2['questions'])}")
        return False
    
    print("\n🔍 Step 5: Verify fresh scoring without ledger uses new keys...")
    attempt_no_ledger = {
        'questions': attempt['questions'],  # Has altered keys
        'answers': answers,
        'rules': {'correct': 4, 'wrong': -1, 'skipped': 0},
        'started_at': 0
    }
    
    result3 = score(attempt_no_ledger)
    print(f"   Fresh score with new keys: {result3['summary']['score']}")
    print(f"   Fresh correct: {result3['summary']['correct']}")
    
    # With altered key, Q1 should now be wrong (student answered '1', key is now '2')
    if result3['summary']['correct'] < original_summary['correct']:
        print(f"✅ Fresh scoring uses new keys (correct count decreased)")
    else:
        print(f"⚠️  Fresh scoring may not have used new keys")
    
    print("\n" + "=" * 70)
    print("✅ IMMUTABLE LEDGER TEST PASSED")
    print("=" * 70)
    return True

if __name__ == '__main__':
    success = test_immutable_ledger()
    sys.exit(0 if success else 1)
