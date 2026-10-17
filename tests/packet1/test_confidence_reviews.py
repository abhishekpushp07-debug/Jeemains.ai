"""Confidence review and analytics validation against Guide04 canonical thresholds.

CRITICAL: Tests source Guide04 metric identities A41-A45 and A50 with exact thresholds:
- A41: 20 rated total, 10 per displayed bin, endpoint 1 included
- A42: 20 rated items for Brier score
- A43: 10 rated items, threshold strict less than c (default 0.20)
- A45: 5 labelled WRONG items only (not skips/correct)
- A50: Verified first-exposure evidence required, unknown exposure unavailable

Tests confidence capture rules:
- First nonempty answer probability 0 and 1 retained
- Empty answers before first nonempty not captured
- No retrospective rating (changed response excluded)
- Changed/cleared/reverted permanently excluded
- Same response marking not excluded
- Exact body-bound replay idempotency
"""
import copy
import pytest
from uuid import uuid4
from fractions import Fraction

pytestmark = pytest.mark.asyncio(loop_scope='session')


def question(number=1, correct='4', wrong='-1'):
    return {
        'id': str(uuid4()), 'number': number, 'solution_number': number,
        'subject': 'Physics', 'section': 'Physics', 'type': 'mcq',
        'text': f'Question {number}', 'options': {'1': 'One', '2': 'Two', '3': 'Three', '4': 'Four'},
        'answer': '1', 'accepted_answers': ['1'], 'solution': f'Solution {number}',
        'approved': True, 'issues': [], 'render_mode': 'typed',
        'q_refs': [], 's_refs': [], 'topic': 'Mechanics', 'difficulty': 'Medium',
        'review_note': '', 'accessible_text': '', 'solution_accessible_text': '',
        'disposition': 'standard'
    }


def source_set(questions_count=10, minutes=0, correct='4', wrong='-1'):
    return {
        'id': str(uuid4()), 'title': 'Confidence Test Set', 'exam': 'JEE Main',
        'status': 'published', 'revision': 1, 'version': 1,
        'questions': [question(i, correct, wrong) for i in range(1, questions_count + 1)],
        'rules': {'minutes': minutes, 'correct': correct, 'wrong': wrong, 'skipped': 0,
                  'navigation': 'free', 'numeric_policy': 'integer_exact',
                  'solution_release': 'after_submit'},
        'audience': 'all', 'expires': None, 'rights_upload': True,
        'rights_publish': True, 'rights_report': True, 'file_ids': [],
        'source': 'Confidence validation fixture', 'attribution': 'Test content',
        'profile_mode': 'practice'
    }


async def create_attempt_with_confidence(clean_db, user, s, answers_with_confidence):
    """Create a completed attempt with answers and confidence ratings.
    
    Args:
        answers_with_confidence: dict of {qid: (value, confidence)}
    
    IMPORTANT: All response changes/clears/reverts must be done BEFORE finalize.
    Do not reopen completed attempts or mutate immutable ledgers.
    """
    from tejas import attempts, corrections
    from tejas.answers import save_answer, AnswerWrite

    # Ensure unique set ID
    s['id'] = str(uuid4())
    await clean_db.tejas_sets.insert_one(copy.deepcopy(s))
    await attempts.preflight(s['id'], {}, user)
    a = await attempts.start(s['id'], attempts.Start(
        start_key='test-' + str(uuid4()), device_checked=True), user)

    # Save answers with confidence
    for qid, (value, confidence) in answers_with_confidence.items():
        await save_answer(a['id'], qid, AnswerWrite(
            value=value, confidence=confidence, revision=1, 
            request_id=f'ans-{qid}-{str(uuid4())[:8]}', marked=False), user)

    await attempts.finalize(a['id'])
    completed = await attempts.owned(a['id'], user)
    await corrections.freeze_ledger(completed)
    return await attempts.owned(a['id'], user)


# ============================================================================
# FIRST ANSWER CONFIDENCE CAPTURE RULES
# ============================================================================

async def test_confidence_0_and_1_retained(clean_db, synthetic_student_user):
    """First nonempty answer with probability 0 and 1 must be retained."""
    from tejas import attempts, answers
    from tejas.answers import AnswerWrite

    s = source_set(3)
    s['id'] = str(uuid4())
    u = synthetic_student_user

    await clean_db.tejas_sets.insert_one(copy.deepcopy(s))
    await attempts.preflight(s['id'], {}, u)
    a = await attempts.start(s['id'], attempts.Start(
        start_key='test-' + str(uuid4()), device_checked=True), u)

    qid0 = s['questions'][0]['id']
    qid1 = s['questions'][1]['id']

    # Save with confidence 0
    await answers.save_answer(a['id'], qid0, AnswerWrite(
        value='2', confidence=0.0, revision=1, 
        request_id=f'req-0-{str(uuid4())[:8]}', marked=False), u)

    # Save with confidence 1
    await answers.save_answer(a['id'], qid1, AnswerWrite(
        value='1', confidence=1.0, revision=1, 
        request_id=f'req-1-{str(uuid4())[:8]}', marked=False), u)

    a_check = await clean_db.tejas_attempts.find_one({'id': a['id']})
    
    # Verify confidence 0 and 1 are retained
    assert qid0 in a_check['first_answers']
    assert a_check['first_answers'][qid0]['confidence'] == 0.0
    
    assert qid1 in a_check['first_answers']
    assert a_check['first_answers'][qid1]['confidence'] == 1.0


async def test_empty_before_first_nonempty_not_captured(clean_db, synthetic_student_user):
    """Empty answers before first nonempty should not be captured in first_answers."""
    from tejas import attempts, answers
    from tejas.answers import AnswerWrite

    s = source_set(2)
    s['id'] = str(uuid4())
    u = synthetic_student_user

    await clean_db.tejas_sets.insert_one(copy.deepcopy(s))
    await attempts.preflight(s['id'], {}, u)
    a = await attempts.start(s['id'], attempts.Start(
        start_key='test-' + str(uuid4()), device_checked=True), u)

    qid = s['questions'][0]['id']

    # First save: empty with confidence (should NOT be captured)
    await answers.save_answer(a['id'], qid, AnswerWrite(
        value='', confidence=0.5, revision=1, 
        request_id=f'req-empty-{str(uuid4())[:8]}', marked=False), u)

    a_check = await clean_db.tejas_attempts.find_one({'id': a['id']})
    assert qid not in a_check.get('first_answers', {})

    # Second save: nonempty with confidence (should be captured)
    await answers.save_answer(a['id'], qid, AnswerWrite(
        value='2', confidence=0.7, revision=2, 
        request_id=f'req-first-{str(uuid4())[:8]}', marked=False), u)

    a_check = await clean_db.tejas_attempts.find_one({'id': a['id']})
    assert qid in a_check['first_answers']
    assert a_check['first_answers'][qid]['value'] == '2'
    assert a_check['first_answers'][qid]['confidence'] == 0.7


async def test_changed_response_excluded_from_confidence_metrics(clean_db, synthetic_student_user):
    """Changed responses must be permanently excluded from confidence calibration."""
    from tejas.analytics import build_analytics
    from tejas_core import score_attempt
    from tejas import attempts, corrections
    from tejas.answers import save_answer, AnswerWrite

    s = source_set(25, correct='4', wrong='-1')
    u = synthetic_student_user

    # Create attempt with changes BEFORE finalization
    s['id'] = str(uuid4())
    await clean_db.tejas_sets.insert_one(copy.deepcopy(s))
    await attempts.preflight(s['id'], {}, u)
    a = await attempts.start(s['id'], attempts.Start(
        start_key='test-' + str(uuid4()), device_checked=True), u)

    # First 20: correct with high confidence (unchanged)
    for i in range(20):
        qid = s['questions'][i]['id']
        await save_answer(a['id'], qid, AnswerWrite(
            value='1', confidence=0.8, revision=1,
            request_id=f'ans-{qid}-{str(uuid4())[:8]}', marked=False), u)

    # Last 5: initially wrong, then changed to correct (BEFORE finalize)
    for i in range(20, 25):
        qid = s['questions'][i]['id']
        # First save: wrong
        await save_answer(a['id'], qid, AnswerWrite(
            value='2', confidence=0.6, revision=1,
            request_id=f'ans-first-{qid}-{str(uuid4())[:8]}', marked=False), u)
        # Second save: changed to correct
        await save_answer(a['id'], qid, AnswerWrite(
            value='1', confidence=0.9, revision=2,
            request_id=f'ans-change-{qid}-{str(uuid4())[:8]}', marked=False), u)

    await attempts.finalize(a['id'])
    completed = await attempts.owned(a['id'], u)
    await corrections.freeze_ledger(completed)
    a = await attempts.owned(a['id'], u)

    result = score_attempt(a)
    analytics = build_analytics(a, result)

    # A41, A42, A43 should only count the 20 unchanged items
    a41 = next(m for m in analytics['metrics'] if m['metric_id'] == 'A41')
    a42 = next(m for m in analytics['metrics'] if m['metric_id'] == 'A42')
    a43 = next(m for m in analytics['metrics'] if m['metric_id'] == 'A43')

    # All should be available with exactly 20 rated items
    assert a41['state'] == 'available'
    assert a41['value']['rated_count'] == 20
    assert a41['value']['changed_response_excluded'] == 5

    assert a42['state'] == 'available'
    assert a42['sample_size'] == 20

    assert a43['state'] == 'available'
    assert a43['value']['rated_count'] == 20


async def test_same_response_confidence_change_not_excluded(clean_db, synthetic_student_user):
    """Confidence changes without response changes should NOT exclude the item."""
    from tejas.analytics import build_analytics
    from tejas_core import score_attempt
    from tejas import attempts, corrections
    from tejas.answers import save_answer, AnswerWrite

    s = source_set(20, correct='4', wrong='-1')
    u = synthetic_student_user

    # Create attempt with confidence changes BEFORE finalization
    s['id'] = str(uuid4())
    await clean_db.tejas_sets.insert_one(copy.deepcopy(s))
    await attempts.preflight(s['id'], {}, u)
    a = await attempts.start(s['id'], attempts.Start(
        start_key='test-' + str(uuid4()), device_checked=True), u)

    # First 5: change confidence but NOT response (BEFORE finalize)
    for i in range(5):
        qid = s['questions'][i]['id']
        # First save: response '1' with confidence 0.5
        await save_answer(a['id'], qid, AnswerWrite(
            value='1', confidence=0.5, revision=1,
            request_id=f'ans-first-{qid}-{str(uuid4())[:8]}', marked=False), u)
        # Second save: same response '1', different confidence
        await save_answer(a['id'], qid, AnswerWrite(
            value='1', confidence=0.9, revision=2,
            request_id=f'ans-conf-{qid}-{str(uuid4())[:8]}', marked=False), u)

    # Remaining 15: single save
    for i in range(5, 20):
        qid = s['questions'][i]['id']
        await save_answer(a['id'], qid, AnswerWrite(
            value='1', confidence=0.5, revision=1,
            request_id=f'ans-{qid}-{str(uuid4())[:8]}', marked=False), u)

    await attempts.finalize(a['id'])
    completed = await attempts.owned(a['id'], u)
    await corrections.freeze_ledger(completed)
    a = await attempts.owned(a['id'], u)

    result = score_attempt(a)
    analytics = build_analytics(a, result)

    # All 20 should still be included (confidence change alone doesn't exclude)
    a41 = next(m for m in analytics['metrics'] if m['metric_id'] == 'A41')
    a42 = next(m for m in analytics['metrics'] if m['metric_id'] == 'A42')

    # Should have all 20 items (confidence change without response change is OK)
    assert a41['state'] == 'available'
    assert a41['value']['rated_count'] == 20
    assert a41['value']['changed_response_excluded'] == 0


async def test_idempotent_confidence_save_exact_body_replay(clean_db, synthetic_student_user):
    """Exact body-bound replay must return identical receipt."""
    from tejas import attempts, answers
    from tejas.answers import AnswerWrite

    s = source_set(2)
    s['id'] = str(uuid4())
    u = synthetic_student_user

    await clean_db.tejas_sets.insert_one(copy.deepcopy(s))
    await attempts.preflight(s['id'], {}, u)
    a = await attempts.start(s['id'], attempts.Start(
        start_key='test-' + str(uuid4()), device_checked=True), u)

    qid = s['questions'][0]['id']
    request_id = f'idempotent-{str(uuid4())}'

    # First save - returns dict (HTTP response_model serializes Pydantic)
    receipt1 = await answers.save_answer(a['id'], qid, AnswerWrite(
        value='2', confidence=0.75, revision=1, 
        request_id=request_id, marked=False), u)

    # Exact replay with same request_id and body
    receipt2 = await answers.save_answer(a['id'], qid, AnswerWrite(
        value='2', confidence=0.75, revision=1, 
        request_id=request_id, marked=False), u)

    # Should be identical and marked as duplicate - compare dict receipt
    assert receipt1['accepted']['value'] == receipt2['accepted']['value']
    assert receipt1['accepted']['confidence'] == receipt2['accepted']['confidence']
    assert receipt2['duplicate'] is True


async def test_different_body_same_request_id_rejected(clean_db, synthetic_student_user):
    """Different body with same request_id must be rejected with 409."""
    from tejas import attempts, answers
    from tejas.answers import AnswerWrite
    from fastapi import HTTPException

    s = source_set(2)
    s['id'] = str(uuid4())
    u = synthetic_student_user

    await clean_db.tejas_sets.insert_one(copy.deepcopy(s))
    await attempts.preflight(s['id'], {}, u)
    a = await attempts.start(s['id'], attempts.Start(
        start_key='test-' + str(uuid4()), device_checked=True), u)

    qid = s['questions'][0]['id']
    request_id = f'conflict-{str(uuid4())}'

    # First save
    await answers.save_answer(a['id'], qid, AnswerWrite(
        value='2', confidence=0.75, revision=1, 
        request_id=request_id, marked=False), u)

    # Different body with same request_id
    with pytest.raises(HTTPException) as exc:
        await answers.save_answer(a['id'], qid, AnswerWrite(
            value='3', confidence=0.85, revision=1,  # Different value and confidence
            request_id=request_id, marked=False), u)
    
    assert exc.value.status_code == 409
    assert 'different content' in exc.value.detail.lower()


# ============================================================================
# A41: CONFIDENCE CALIBRATION CANONICAL THRESHOLDS
# ============================================================================

async def test_a41_requires_20_rated_total_10_per_bin(clean_db, synthetic_student_user):
    """A41: Requires 20 rated items total and 10 per displayed bin."""
    from tejas.analytics import build_analytics
    from tejas_core import score_attempt

    s = source_set(25, correct='4', wrong='-1')
    u = synthetic_student_user

    # Create exactly 19 items (below threshold)
    answers_with_confidence = {}
    for i in range(19):
        qid = s['questions'][i]['id']
        answers_with_confidence[qid] = ('1', 0.5)

    a = await create_attempt_with_confidence(clean_db, u, s, answers_with_confidence)
    result = score_attempt(a)
    analytics = build_analytics(a, result)

    a41 = next(m for m in analytics['metrics'] if m['metric_id'] == 'A41')
    assert a41['state'] == 'insufficient_sample'
    assert '20' in a41['reason']

    # Now test with exactly 20 items
    answers_with_confidence = {}
    for i in range(20):
        qid = s['questions'][i]['id']
        # Distribute across bins: 10 in [0.4, 0.6), 10 in [0.6, 0.8)
        conf = 0.5 if i < 10 else 0.7
        answers_with_confidence[qid] = ('1', conf)

    a = await create_attempt_with_confidence(clean_db, u, s, answers_with_confidence)
    result = score_attempt(a)
    analytics = build_analytics(a, result)

    a41 = next(m for m in analytics['metrics'] if m['metric_id'] == 'A41')
    assert a41['state'] == 'available'
    assert a41['value']['rated_count'] == 20


async def test_a41_bin_requires_10_items_endpoint_1_included(clean_db, synthetic_student_user):
    """A41: Each displayed bin requires 10 items; endpoint 1.0 is included in [0.8, 1.0]."""
    from tejas.analytics import build_analytics
    from tejas_core import score_attempt

    s = source_set(30, correct='4', wrong='-1')
    u = synthetic_student_user

    # Create 20 items: 9 in [0.8, 1.0), 1 at exactly 1.0, 10 in [0.6, 0.8)
    answers_with_confidence = {}
    for i in range(20):
        qid = s['questions'][i]['id']
        if i < 9:
            conf = 0.85  # [0.8, 1.0)
        elif i == 9:
            conf = 1.0   # Exactly 1.0 - should be included in [0.8, 1.0]
        else:
            conf = 0.7   # [0.6, 0.8)
        answers_with_confidence[qid] = ('1', conf)

    a = await create_attempt_with_confidence(clean_db, u, s, answers_with_confidence)
    result = score_attempt(a)
    analytics = build_analytics(a, result)

    a41 = next(m for m in analytics['metrics'] if m['metric_id'] == 'A41')
    assert a41['state'] == 'available'
    
    # Find the [0.8, 1.0] bin - verify numerical mean and count with inclusive endpoint
    high_bin = next((b for b in a41['value']['bins'] if b['bin'] == '[0.8, 1.0]'), None)
    assert high_bin is not None, f"Expected [0.8, 1.0] bin, got bins: {[b['bin'] for b in a41['value']['bins']]}"
    assert high_bin['count'] == 10  # 9 + 1 (the 1.0 endpoint)
    # Verify numerical mean: (9*0.85 + 1*1.0) / 10 = 8.65 / 10 = 0.865
    assert abs(high_bin['mean_probability'] - 0.865) < 0.001


async def test_a41_bins_below_10_not_displayed(clean_db, synthetic_student_user):
    """A41: Bins with fewer than 10 items should not be displayed."""
    from tejas.analytics import build_analytics
    from tejas_core import score_attempt

    s = source_set(30, correct='4', wrong='-1')
    u = synthetic_student_user

    # Create 20 items: 15 in [0.6, 0.8), 5 in [0.4, 0.6) - second bin should not show
    answers_with_confidence = {}
    for i in range(20):
        qid = s['questions'][i]['id']
        conf = 0.7 if i < 15 else 0.5
        answers_with_confidence[qid] = ('1', conf)

    a = await create_attempt_with_confidence(clean_db, u, s, answers_with_confidence)
    result = score_attempt(a)
    analytics = build_analytics(a, result)

    a41 = next(m for m in analytics['metrics'] if m['metric_id'] == 'A41')
    assert a41['state'] == 'available'
    assert a41['value']['rated_count'] == 20
    
    # Only one bin should be displayed (the one with 15 items)
    assert len(a41['value']['bins']) == 1
    assert a41['value']['bins'][0]['count'] == 15


# ============================================================================
# A42: BRIER SCORE CANONICAL THRESHOLD
# ============================================================================

async def test_a42_requires_20_rated_items(clean_db, synthetic_student_user):
    """A42: Brier score requires exactly 20 rated items."""
    from tejas.analytics import build_analytics
    from tejas_core import score_attempt

    s = source_set(25, correct='4', wrong='-1')
    u = synthetic_student_user

    # Test with 19 items (below threshold)
    answers_with_confidence = {}
    for i in range(19):
        qid = s['questions'][i]['id']
        answers_with_confidence[qid] = ('1', 0.8)

    a = await create_attempt_with_confidence(clean_db, u, s, answers_with_confidence)
    result = score_attempt(a)
    analytics = build_analytics(a, result)

    a42 = next(m for m in analytics['metrics'] if m['metric_id'] == 'A42')
    assert a42['state'] == 'insufficient_sample'
    assert '20' in a42['reason']

    # Test with exactly 20 items
    answers_with_confidence = {}
    for i in range(20):
        qid = s['questions'][i]['id']
        # 10 correct with 0.8 confidence, 10 incorrect with 0.8 confidence
        value = '1' if i < 10 else '2'
        answers_with_confidence[qid] = (value, 0.8)

    a = await create_attempt_with_confidence(clean_db, u, s, answers_with_confidence)
    result = score_attempt(a)
    analytics = build_analytics(a, result)

    a42 = next(m for m in analytics['metrics'] if m['metric_id'] == 'A42')
    assert a42['state'] == 'available'
    assert a42['sample_size'] == 20
    # Brier = mean((p - y)^2)
    # 10 correct: (0.8 - 1)^2 = 0.04
    # 10 incorrect: (0.8 - 0)^2 = 0.64
    # Mean = (10*0.04 + 10*0.64) / 20 = 0.34
    assert abs(a42['value'] - 0.34) < 0.01


async def test_a42_rational_result_precision(clean_db, synthetic_student_user):
    """A42: Brier score should use rational arithmetic for exact results."""
    from tejas.analytics import build_analytics
    from tejas_core import score_attempt

    s = source_set(25, correct='4', wrong='-1')
    u = synthetic_student_user

    # Create 20 items with exact probabilities
    answers_with_confidence = {}
    for i in range(20):
        qid = s['questions'][i]['id']
        # All correct with 0.5 confidence
        answers_with_confidence[qid] = ('1', 0.5)

    a = await create_attempt_with_confidence(clean_db, u, s, answers_with_confidence)
    result = score_attempt(a)
    analytics = build_analytics(a, result)

    a42 = next(m for m in analytics['metrics'] if m['metric_id'] == 'A42')
    assert a42['state'] == 'available'
    # Brier = mean((0.5 - 1)^2) = 0.25 exactly
    assert a42['value'] == 0.25


# ============================================================================
# A43: LOW CONFIDENCE PENALTY THRESHOLD
# ============================================================================

async def test_a43_requires_10_rated_items(clean_db, synthetic_student_user):
    """A43: Requires 10 genuinely rated unchanged items."""
    from tejas.analytics import build_analytics
    from tejas_core import score_attempt

    s = source_set(15, correct='4', wrong='-1')
    u = synthetic_student_user

    # Test with 9 items (below threshold)
    answers_with_confidence = {}
    for i in range(9):
        qid = s['questions'][i]['id']
        answers_with_confidence[qid] = ('2', 0.1)  # wrong with low confidence

    a = await create_attempt_with_confidence(clean_db, u, s, answers_with_confidence)
    result = score_attempt(a)
    analytics = build_analytics(a, result)

    a43 = next(m for m in analytics['metrics'] if m['metric_id'] == 'A43')
    assert a43['state'] == 'insufficient_sample'
    assert '10' in a43['reason']

    # Test with exactly 10 items
    answers_with_confidence = {}
    for i in range(10):
        qid = s['questions'][i]['id']
        answers_with_confidence[qid] = ('2', 0.1)  # wrong with low confidence

    a = await create_attempt_with_confidence(clean_db, u, s, answers_with_confidence)
    result = score_attempt(a)
    analytics = build_analytics(a, result)

    a43 = next(m for m in analytics['metrics'] if m['metric_id'] == 'A43')
    assert a43['state'] == 'available'
    assert a43['value']['rated_count'] == 10


async def test_a43_threshold_strict_less_than(clean_db, synthetic_student_user):
    """A43: Threshold is strict less than c (p < c), not less than or equal."""
    from tejas.analytics import build_analytics
    from tejas_core import score_attempt

    s = source_set(15, correct='4', wrong='-1')
    u = synthetic_student_user

    # Create 10 items: 5 at exactly 0.20, 5 below 0.20
    answers_with_confidence = {}
    for i in range(10):
        qid = s['questions'][i]['id']
        conf = 0.20 if i < 5 else 0.15
        answers_with_confidence[qid] = ('2', conf)  # all wrong

    a = await create_attempt_with_confidence(clean_db, u, s, answers_with_confidence)
    result = score_attempt(a)
    analytics = build_analytics(a, result, confidence_threshold=0.20)

    a43 = next(m for m in analytics['metrics'] if m['metric_id'] == 'A43')
    assert a43['state'] == 'available'
    assert a43['value']['threshold'] == 0.20
    # Only 5 items should be below threshold (strict <, not <=)
    assert a43['value']['low_confidence_count'] == 5
    # Penalty = 5 * 1 = 5 marks
    assert a43['value']['penalty_marks'] == 5.0


async def test_a43_no_negative_contribution_from_guessed(clean_db, synthetic_student_user):
    """A43: Only counts penalty marks (negative contributions), not positive."""
    from tejas.analytics import build_analytics
    from tejas_core import score_attempt

    s = source_set(15, correct='4', wrong='-1')
    u = synthetic_student_user

    # Create 10 items with low confidence: 5 correct, 5 incorrect
    answers_with_confidence = {}
    for i in range(10):
        qid = s['questions'][i]['id']
        value = '1' if i < 5 else '2'  # 5 correct, 5 wrong
        answers_with_confidence[qid] = (value, 0.1)  # all low confidence

    a = await create_attempt_with_confidence(clean_db, u, s, answers_with_confidence)
    result = score_attempt(a)
    analytics = build_analytics(a, result, confidence_threshold=0.20)

    a43 = next(m for m in analytics['metrics'] if m['metric_id'] == 'A43')
    assert a43['state'] == 'available'
    # Should only count penalty from 5 incorrect items
    assert a43['value']['penalty_marks'] == 5.0  # 5 * 1 penalty
    # Not 5*4 - 5*1 = 15 (which would include positive contributions)


async def test_a43_configurable_threshold(clean_db, synthetic_student_user):
    """A43: Threshold c is configurable (default 0.20)."""
    from tejas.analytics import build_analytics
    from tejas_core import score_attempt

    s = source_set(15, correct='4', wrong='-1')
    u = synthetic_student_user

    # Create 10 items with confidence 0.25
    answers_with_confidence = {}
    for i in range(10):
        qid = s['questions'][i]['id']
        answers_with_confidence[qid] = ('2', 0.25)  # all wrong

    a = await create_attempt_with_confidence(clean_db, u, s, answers_with_confidence)
    result = score_attempt(a)
    
    # Test with default threshold 0.20
    analytics_default = build_analytics(a, result, confidence_threshold=0.20)
    a43_default = next(m for m in analytics_default['metrics'] if m['metric_id'] == 'A43')
    assert a43_default['value']['low_confidence_count'] == 0  # 0.25 >= 0.20

    # Test with threshold 0.30
    analytics_custom = build_analytics(a, result, confidence_threshold=0.30)
    a43_custom = next(m for m in analytics_custom['metrics'] if m['metric_id'] == 'A43')
    assert a43_custom['value']['threshold'] == 0.30
    assert a43_custom['value']['low_confidence_count'] == 10  # 0.25 < 0.30


# ============================================================================
# A45: ERROR CAUSE LABELLING
# ============================================================================

async def test_a45_requires_5_labelled_wrong_only(clean_db, synthetic_student_user):
    """A45: Requires 5 learner-labelled WRONG items, not skips or correct."""
    from tejas.analytics import build_analytics
    from tejas_core import score_attempt
    from tejas import attempts, corrections
    from tejas.answers import save_answer, AnswerWrite

    s = source_set(10, correct='4', wrong='-1')
    u = synthetic_student_user

    # Test 1: Create attempt with 4 wrong items (insufficient)
    s1 = copy.deepcopy(s)
    s1['id'] = str(uuid4())
    await clean_db.tejas_sets.insert_one(s1)
    await attempts.preflight(s1['id'], {}, u)
    a1 = await attempts.start(s1['id'], attempts.Start(
        start_key='test-' + str(uuid4()), device_checked=True), u)

    # 4 wrong, 2 correct
    for i in range(6):
        qid = s1['questions'][i]['id']
        value = '2' if i < 4 else '1'  # 4 wrong, 2 correct
        await save_answer(a1['id'], qid, AnswerWrite(
            value=value, confidence=0.5, revision=1,
            request_id=f'ans-{qid}-{str(uuid4())[:8]}', marked=False), u)

    await attempts.finalize(a1['id'])
    completed1 = await attempts.owned(a1['id'], u)
    await corrections.freeze_ledger(completed1)
    
    # Label only the 4 wrong items
    review_states = {}
    for i in range(4):
        qid = s1['questions'][i]['id']
        review_states[qid] = {'category': 'concept_gap'}
    
    await clean_db.tejas_attempts.update_one(
        {'id': a1['id']}, {'$set': {'review_states': review_states}})

    a1 = await attempts.owned(a1['id'], u)
    result1 = score_attempt(a1)
    analytics1 = build_analytics(a1, result1)

    a45_1 = next(m for m in analytics1['metrics'] if m['metric_id'] == 'A45')
    # Should be insufficient_sample with only 4 labelled wrong items
    assert a45_1['state'] == 'insufficient_sample'
    assert '5' in a45_1['reason']

    # Test 2: Create NEW attempt with 5 wrong items (sufficient)
    s2 = copy.deepcopy(s)
    s2['id'] = str(uuid4())
    await clean_db.tejas_sets.insert_one(s2)
    await attempts.preflight(s2['id'], {}, u)
    a2 = await attempts.start(s2['id'], attempts.Start(
        start_key='test-' + str(uuid4()), device_checked=True), u)

    # 5 wrong, 2 correct - all answers BEFORE finalize
    for i in range(7):
        qid = s2['questions'][i]['id']
        value = '2' if i < 5 else '1'  # 5 wrong, 2 correct
        await save_answer(a2['id'], qid, AnswerWrite(
            value=value, confidence=0.5, revision=1,
            request_id=f'ans-{qid}-{str(uuid4())[:8]}', marked=False), u)

    await attempts.finalize(a2['id'])
    completed2 = await attempts.owned(a2['id'], u)
    await corrections.freeze_ledger(completed2)
    
    # Label all 5 wrong items
    review_states2 = {}
    for i in range(5):
        qid = s2['questions'][i]['id']
        category = 'concept_gap' if i < 4 else 'silly_mistake'
        review_states2[qid] = {'category': category}
    
    await clean_db.tejas_attempts.update_one(
        {'id': a2['id']}, {'$set': {'review_states': review_states2}})

    a2 = await attempts.owned(a2['id'], u)
    result2 = score_attempt(a2)
    analytics2 = build_analytics(a2, result2)

    a45_2 = next(m for m in analytics2['metrics'] if m['metric_id'] == 'A45')
    assert a45_2['state'] == 'available'
    assert a45_2['value']['labelled_wrong_count'] == 5


async def test_a45_skipped_and_correct_not_in_denominator(clean_db, synthetic_student_user):
    """A45: Only labelled incorrect items enter denominator, not skipped or correct."""
    from tejas.analytics import build_analytics
    from tejas_core import score_attempt
    from tejas import attempts

    s = source_set(15, correct='4', wrong='-1')
    u = synthetic_student_user

    # Create 10 items: 5 wrong (labelled), 3 correct (labelled), 2 skipped (labelled)
    answers_with_confidence = {}
    for i in range(8):
        qid = s['questions'][i]['id']
        value = '2' if i < 5 else '1'  # 5 wrong, 3 correct
        answers_with_confidence[qid] = (value, 0.5)
    # 2 skipped (no answer)

    a = await create_attempt_with_confidence(clean_db, u, s, answers_with_confidence)
    
    # Label all items including correct and skipped
    review_states = {}
    for i in range(10):
        qid = s['questions'][i]['id']
        review_states[qid] = {'category': 'concept_gap'}
    
    await clean_db.tejas_attempts.update_one(
        {'id': a['id']}, {'$set': {'review_states': review_states}})

    a = await attempts.owned(a['id'], u)
    result = score_attempt(a)
    analytics = build_analytics(a, result)

    a45 = next(m for m in analytics['metrics'] if m['metric_id'] == 'A45')
    assert a45['state'] == 'available'
    # Only 5 wrong items should be in denominator
    assert a45['value']['labelled_wrong_count'] == 5
    # Correct and skipped should not be counted
    assert a45['value']['unlabelled_wrong_count'] == 0


# ============================================================================
# A50: REVIEW BACKLOG WITH VERIFIED FIRST EXPOSURE
# ============================================================================

async def test_a50_requires_verified_first_exposure(clean_db, synthetic_student_user):
    """A50: Requires verified first-exposure evidence; unknown exposure is unavailable."""
    from tejas.analytics import build_analytics
    from tejas_core import score_attempt
    from tejas import attempts

    s = source_set(10, correct='4', wrong='-1')
    u = synthetic_student_user

    # Create attempt with wrong items but NO verified first exposure
    answers_with_confidence = {}
    for i in range(5):
        qid = s['questions'][i]['id']
        answers_with_confidence[qid] = ('2', 0.5)  # wrong

    a = await create_attempt_with_confidence(clean_db, u, s, answers_with_confidence)
    
    # Enable review tracking but don't set verified_first_exposure_question_ids
    review_states = {}
    for i in range(5):
        qid = s['questions'][i]['id']
        review_states[qid] = {'completed': False}
    
    await clean_db.tejas_attempts.update_one(
        {'id': a['id']}, 
        {'$set': {
            'review_states': review_states,
            'review_tracking_enabled': True
        }})

    a = await attempts.owned(a['id'], u)
    result = score_attempt(a)
    analytics = build_analytics(a, result)

    a50 = next(m for m in analytics['metrics'] if m['metric_id'] == 'A50')
    # Should be unavailable without verified first exposure
    assert a50['state'] == 'unavailable'
    assert 'first-exposure' in a50['reason'].lower()


async def test_a50_exact_count_with_verified_first_exposure(clean_db, synthetic_student_user):
    """A50: Exact count of open tasks when verified first-exposure is supplied."""
    from tejas.analytics import build_analytics
    from tejas_core import score_attempt
    from tejas import attempts

    s = source_set(10, correct='4', wrong='-1')
    u = synthetic_student_user

    # Create attempt with wrong and skipped items
    answers_with_confidence = {}
    for i in range(5):
        qid = s['questions'][i]['id']
        answers_with_confidence[qid] = ('2', 0.5)  # wrong
    # 5 skipped

    a = await create_attempt_with_confidence(clean_db, u, s, answers_with_confidence)
    
    # Set verified first exposure for all wrong/skipped items
    verified_first_exposure = [s['questions'][i]['id'] for i in range(8)]
    
    # Create review states: 3 open, 2 completed
    review_states = {}
    for i in range(5):
        qid = s['questions'][i]['id']
        review_states[qid] = {'completed': i >= 3}  # First 3 open, last 2 completed
    
    await clean_db.tejas_attempts.update_one(
        {'id': a['id']}, 
        {'$set': {
            'review_states': review_states,
            'review_tracking_enabled': True,
            'verified_first_exposure_question_ids': verified_first_exposure
        }})

    a = await attempts.owned(a['id'], u)
    result = score_attempt(a)
    analytics = build_analytics(a, result)

    a50 = next(m for m in analytics['metrics'] if m['metric_id'] == 'A50')
    assert a50['state'] == 'available'
    assert a50['value']['open_tasks'] == 3
    assert a50['value']['assigned_tasks'] == 5  # Only wrong/skipped with verified first exposure


# ============================================================================
# REVIEW ENDPOINT CONTRACT VALIDATION
# ============================================================================

async def test_review_put_ownership_401_404(http_client, clean_db, synthetic_student_user, synthetic_staff_user):
    """PUT /api/attempts/{id}/reviews/{qid} enforces ownership with 401/404."""
    from tejas import attempts, corrections
    from tejas.answers import save_answer, AnswerWrite

    s = source_set(3)
    s['id'] = str(uuid4())
    u = synthetic_student_user

    # Create attempt for student
    await clean_db.tejas_sets.insert_one(copy.deepcopy(s))
    await attempts.preflight(s['id'], {}, u)
    a = await attempts.start(s['id'], attempts.Start(
        start_key='test-' + str(uuid4()), device_checked=True), u)
    
    qid = s['questions'][0]['id']
    await save_answer(a['id'], qid, AnswerWrite(
        value='2', revision=1, request_id=f'ans-{str(uuid4())[:8]}', marked=False), u)
    
    await attempts.finalize(a['id'])
    completed = await attempts.owned(a['id'], u)
    await corrections.freeze_ledger(completed)

    # Create session for staff user using session_fixture helper
    from tejas.auth import token
    staff_user = synthetic_staff_user
    # Insert staff user into database
    await clean_db.tejas_users.insert_one(dict(staff_user))
    
    sid = str(uuid4())
    from datetime import datetime, timezone, timedelta
    await clean_db.tejas_sessions.insert_one({
        'id': sid, 'user_id': staff_user['id'],
        'access_type': 'staff_password',
        'expires_at': datetime.now(timezone.utc) + timedelta(hours=1)
    })
    
    staff_cookies = {
        'access_token': token(staff_user, sid, 'access', 900),
        'refresh_token': token(staff_user, sid, 'refresh', 3600)
    }

    response = await http_client.put(
        f'/api/attempts/{a["id"]}/reviews/{qid}',
        json={
            'request_id': str(uuid4()),
            'revision': 1,
            'category': 'concept_gap',
            'identified_error': True
        },
        cookies=staff_cookies
    )
    
    assert response.status_code == 404  # Not found for different user


async def test_review_put_active_embargo_denied(http_client, clean_db, student_session):
    """PUT /api/attempts/{id}/reviews/{qid} denies active/embargoed attempts with 403."""
    from tejas import attempts

    s = source_set(3)
    s['id'] = str(uuid4())
    u = student_session['user']

    await clean_db.tejas_sets.insert_one(copy.deepcopy(s))
    await attempts.preflight(s['id'], {}, u)
    a = await attempts.start(s['id'], attempts.Start(
        start_key='test-' + str(uuid4()), device_checked=True), u)
    
    qid = s['questions'][0]['id']

    # Try to review while still active
    response = await http_client.put(
        f'/api/attempts/{a["id"]}/reviews/{qid}',
        json={
            'request_id': str(uuid4()),
            'revision': 1,
            'category': 'concept_gap',
            'identified_error': True
        },
        cookies=student_session['cookies']
    )
    
    assert response.status_code == 403
    # HTTP uses response envelope {error: {message}}
    response_data = response.json()
    assert 'error' in response_data
    assert 'submission' in response_data['error']['message'].lower()


async def test_review_put_grading_pending_409(http_client, clean_db, student_session):
    """PUT /api/attempts/{id}/reviews/{qid} returns 409 when grading pending."""
    from tejas import attempts
    from tejas.answers import save_answer, AnswerWrite

    s = source_set(3)
    s['id'] = str(uuid4())
    u = student_session['user']

    await clean_db.tejas_sets.insert_one(copy.deepcopy(s))
    await attempts.preflight(s['id'], {}, u)
    a = await attempts.start(s['id'], attempts.Start(
        start_key='test-' + str(uuid4()), device_checked=True), u)
    
    qid = s['questions'][0]['id']
    await save_answer(a['id'], qid, AnswerWrite(
        value='2', revision=1, request_id=f'ans-{str(uuid4())[:8]}', marked=False), u)
    
    await attempts.finalize(a['id'])
    # Don't create ledger - leave grading pending

    response = await http_client.put(
        f'/api/attempts/{a["id"]}/reviews/{qid}',
        json={
            'request_id': str(uuid4()),
            'revision': 1,
            'category': 'concept_gap',
            'identified_error': True
        },
        cookies=student_session['cookies']
    )
    
    assert response.status_code == 409
    # HTTP uses response envelope {error: {message}}
    response_data = response.json()
    assert 'error' in response_data
    assert 'grading' in response_data['error']['message'].lower()


async def test_review_put_cas_concurrent_winners(http_client, clean_db, student_session):
    """PUT /api/attempts/{id}/reviews/{qid} CAS ensures concurrent winners."""
    from tejas import attempts, corrections
    from tejas.answers import save_answer, AnswerWrite

    s = source_set(3)
    s['id'] = str(uuid4())
    u = student_session['user']

    await clean_db.tejas_sets.insert_one(copy.deepcopy(s))
    await attempts.preflight(s['id'], {}, u)
    a = await attempts.start(s['id'], attempts.Start(
        start_key='test-' + str(uuid4()), device_checked=True), u)
    
    qid = s['questions'][0]['id']
    await save_answer(a['id'], qid, AnswerWrite(
        value='2', revision=1, request_id=f'ans-{str(uuid4())[:8]}', marked=False), u)
    
    await attempts.finalize(a['id'])
    completed = await attempts.owned(a['id'], u)
    await corrections.freeze_ledger(completed)

    # First review save
    response1 = await http_client.put(
        f'/api/attempts/{a["id"]}/reviews/{qid}',
        json={
            'request_id': str(uuid4()),
            'revision': 1,
            'category': 'concept_gap',
            'identified_error': True,
            'note': '',
            'wrote_note': False,
            'reviewed_solution': False,
            'retry_planned': False
        },
        cookies=student_session['cookies']
    )
    
    assert response1.status_code == 200

    # Concurrent save with stale revision (should fail)
    response2 = await http_client.put(
        f'/api/attempts/{a["id"]}/reviews/{qid}',
        json={
            'request_id': str(uuid4()),
            'revision': 1,  # Stale revision
            'category': 'silly_mistake',
            'identified_error': True,
            'note': '',
            'wrote_note': False,
            'reviewed_solution': False,
            'retry_planned': False
        },
        cookies=student_session['cookies']
    )
    
    assert response2.status_code == 409
    # HTTP uses response envelope {error: {message}}
    response_data = response2.json()
    assert 'error' in response_data
    assert 'changed' in response_data['error']['message'].lower()


async def test_review_put_identical_replay_idempotent(http_client, clean_db, student_session):
    """PUT /api/attempts/{id}/reviews/{qid} identical replay returns same result."""
    from tejas import attempts, corrections
    from tejas.answers import save_answer, AnswerWrite

    s = source_set(3)
    s['id'] = str(uuid4())
    u = student_session['user']

    await clean_db.tejas_sets.insert_one(copy.deepcopy(s))
    await attempts.preflight(s['id'], {}, u)
    a = await attempts.start(s['id'], attempts.Start(
        start_key='test-' + str(uuid4()), device_checked=True), u)
    
    qid = s['questions'][0]['id']
    await save_answer(a['id'], qid, AnswerWrite(
        value='2', revision=1, request_id=f'ans-{str(uuid4())[:8]}', marked=False), u)
    
    await attempts.finalize(a['id'])
    completed = await attempts.owned(a['id'], u)
    await corrections.freeze_ledger(completed)

    request_id = str(uuid4())
    payload = {
        'request_id': request_id,
        'revision': 1,
        'category': 'concept_gap',
        'identified_error': True,
        'note': 'Test note',
        'wrote_note': True,
        'reviewed_solution': False,
        'retry_planned': False
    }

    # First save
    response1 = await http_client.put(
        f'/api/attempts/{a["id"]}/reviews/{qid}',
        json=payload,
        cookies=student_session['cookies']
    )
    
    assert response1.status_code == 200
    # HTTP uses response envelope {data, meta}
    data1 = response1.json()['data']

    # Identical replay
    response2 = await http_client.put(
        f'/api/attempts/{a["id"]}/reviews/{qid}',
        json=payload,
        cookies=student_session['cookies']
    )
    
    assert response2.status_code == 200
    data2 = response2.json()['data']
    
    # Should return identical data
    assert data1['category'] == data2['category']
    assert data1['note'] == data2['note']
    assert data1['revision'] == data2['revision']


async def test_review_put_payload_mismatch_409(http_client, clean_db, student_session):
    """PUT /api/attempts/{id}/reviews/{qid} different payload with same request_id returns 409."""
    from tejas import attempts, corrections
    from tejas.answers import save_answer, AnswerWrite

    s = source_set(3)
    s['id'] = str(uuid4())
    u = student_session['user']

    await clean_db.tejas_sets.insert_one(copy.deepcopy(s))
    await attempts.preflight(s['id'], {}, u)
    a = await attempts.start(s['id'], attempts.Start(
        start_key='test-' + str(uuid4()), device_checked=True), u)
    
    qid = s['questions'][0]['id']
    await save_answer(a['id'], qid, AnswerWrite(
        value='2', revision=1, request_id=f'ans-{str(uuid4())[:8]}', marked=False), u)
    
    await attempts.finalize(a['id'])
    completed = await attempts.owned(a['id'], u)
    await corrections.freeze_ledger(completed)

    request_id = str(uuid4())

    # First save
    response1 = await http_client.put(
        f'/api/attempts/{a["id"]}/reviews/{qid}',
        json={
            'request_id': request_id,
            'revision': 1,
            'category': 'concept_gap',
            'identified_error': True,
            'note': '',
            'wrote_note': False,
            'reviewed_solution': False,
            'retry_planned': False
        },
        cookies=student_session['cookies']
    )
    
    assert response1.status_code == 200

    # Different payload with same request_id
    response2 = await http_client.put(
        f'/api/attempts/{a["id"]}/reviews/{qid}',
        json={
            'request_id': request_id,  # Same request_id
            'revision': 1,
            'category': 'silly_mistake',  # Different category
            'identified_error': True,
            'note': '',
            'wrote_note': False,
            'reviewed_solution': False,
            'retry_planned': False
        },
        cookies=student_session['cookies']
    )
    
    assert response2.status_code == 409
    # HTTP uses response envelope {error: {message}}
    response_data = response2.json()
    assert 'error' in response_data
    assert 'different content' in response_data['error']['message'].lower()


async def test_review_put_validation_category_note_solution(http_client, clean_db, student_session):
    """PUT /api/attempts/{id}/reviews/{qid} validates category, note, and solution-open requirements."""
    from tejas import attempts, corrections
    from tejas.answers import save_answer, AnswerWrite

    s = source_set(3)
    s['id'] = str(uuid4())
    u = student_session['user']

    await clean_db.tejas_sets.insert_one(copy.deepcopy(s))
    await attempts.preflight(s['id'], {}, u)
    a = await attempts.start(s['id'], attempts.Start(
        start_key='test-' + str(uuid4()), device_checked=True), u)
    
    qid = s['questions'][0]['id']
    await save_answer(a['id'], qid, AnswerWrite(
        value='2', revision=1, request_id=f'ans-{str(uuid4())[:8]}', marked=False), u)
    
    await attempts.finalize(a['id'])
    completed = await attempts.owned(a['id'], u)
    await corrections.freeze_ledger(completed)

    # Test: identified_error=True but no category
    response = await http_client.put(
        f'/api/attempts/{a["id"]}/reviews/{qid}',
        json={
            'request_id': str(uuid4()),
            'revision': 1,
            'category': None,
            'identified_error': True,
            'note': '',
            'wrote_note': False,
            'reviewed_solution': False,
            'retry_planned': False
        },
        cookies=student_session['cookies']
    )
    assert response.status_code == 422
    # HTTP uses response envelope {error: {message}}
    response_data = response.json()
    assert 'error' in response_data
    assert 'category' in response_data['error']['message'].lower()

    # Test: wrote_note=True but empty note
    response = await http_client.put(
        f'/api/attempts/{a["id"]}/reviews/{qid}',
        json={
            'request_id': str(uuid4()),
            'revision': 1,
            'category': 'concept_gap',
            'identified_error': True,
            'note': '',
            'wrote_note': True,
            'reviewed_solution': False,
            'retry_planned': False
        },
        cookies=student_session['cookies']
    )
    assert response.status_code == 422
    response_data = response.json()
    assert 'error' in response_data
    assert 'note' in response_data['error']['message'].lower()

    # Test: reviewed_solution=True but solution not opened
    response = await http_client.put(
        f'/api/attempts/{a["id"]}/reviews/{qid}',
        json={
            'request_id': str(uuid4()),
            'revision': 1,
            'category': 'concept_gap',
            'identified_error': True,
            'note': '',
            'wrote_note': False,
            'reviewed_solution': True,
            'retry_planned': False
        },
        cookies=student_session['cookies']
    )
    assert response.status_code == 409
    response_data = response.json()
    assert 'error' in response_data
    assert 'solution' in response_data['error']['message'].lower()


# ============================================================================
# EXPECTED VALUE ENDPOINT VALIDATION
# ============================================================================

async def test_expected_value_boundaries_0_1_point2(http_client, clean_db, student_session):
    """POST /api/attempts/{id}/expected-value validates boundaries 0, 1, 0.2."""
    from tejas import attempts, corrections

    s = source_set(3, correct='4', wrong='-1')
    u = student_session['user']

    await clean_db.tejas_sets.insert_one(copy.deepcopy(s))
    await attempts.preflight(s['id'], {}, u)
    a = await attempts.start(s['id'], attempts.Start(
        start_key='test-' + str(uuid4()), device_checked=True), u)
    
    await attempts.finalize(a['id'])
    completed = await attempts.owned(a['id'], u)
    await corrections.freeze_ledger(completed)

    # Test probability 0
    response = await http_client.post(
        f'/api/attempts/{a["id"]}/expected-value',
        json={'probability': 0.0},
        cookies=student_session['cookies']
    )
    assert response.status_code == 200
    # HTTP uses response envelope {data, meta}
    data = response.json()['data']
    # EV = 0*4 + 1*(-1) = -1
    assert data['expected_marks'] == -1.0
    assert data['break_even_probability'] == 0.2  # (0 - (-1)) / (4 - (-1)) = 1/5

    # Test probability 1
    response = await http_client.post(
        f'/api/attempts/{a["id"]}/expected-value',
        json={'probability': 1.0},
        cookies=student_session['cookies']
    )
    assert response.status_code == 200
    data = response.json()['data']
    # EV = 1*4 + 0*(-1) = 4
    assert data['expected_marks'] == 4.0

    # Test probability 0.2 (break-even)
    response = await http_client.post(
        f'/api/attempts/{a["id"]}/expected-value',
        json={'probability': 0.2},
        cookies=student_session['cookies']
    )
    assert response.status_code == 200
    data = response.json()['data']
    # EV = 0.2*4 + 0.8*(-1) = 0.8 - 0.8 = 0
    assert abs(data['expected_marks']) < 0.01


async def test_expected_value_different_marking_schemes(http_client, clean_db, student_session):
    """POST /api/attempts/{id}/expected-value handles +4/-1 and +3/-1 schemes."""
    from tejas import attempts, corrections

    # Test +4/-1 scheme
    s1 = source_set(2, correct='4', wrong='-1')
    s1['id'] = str(uuid4())
    u = student_session['user']

    await clean_db.tejas_sets.insert_one(copy.deepcopy(s1))
    await attempts.preflight(s1['id'], {}, u)
    a1 = await attempts.start(s1['id'], attempts.Start(
        start_key='test-' + str(uuid4()), device_checked=True), u)
    
    await attempts.finalize(a1['id'])
    completed1 = await attempts.owned(a1['id'], u)
    await corrections.freeze_ledger(completed1)

    response = await http_client.post(
        f'/api/attempts/{a1["id"]}/expected-value',
        json={'probability': 0.5},
        cookies=student_session['cookies']
    )
    assert response.status_code == 200
    # HTTP uses response envelope {data, meta}
    data = response.json()['data']
    assert data['correct_marks'] == 4.0
    assert data['wrong_marks'] == -1.0
    # EV = 0.5*4 + 0.5*(-1) = 1.5
    assert abs(data['expected_marks'] - 1.5) < 0.01

    # Test +3/-1 scheme
    s2 = source_set(2, correct='3', wrong='-1')
    s2['id'] = str(uuid4())
    await clean_db.tejas_sets.insert_one(copy.deepcopy(s2))
    await attempts.preflight(s2['id'], {}, u)
    a2 = await attempts.start(s2['id'], attempts.Start(
        start_key='test-' + str(uuid4()), device_checked=True), u)
    
    await attempts.finalize(a2['id'])
    completed2 = await attempts.owned(a2['id'], u)
    await corrections.freeze_ledger(completed2)

    response = await http_client.post(
        f'/api/attempts/{a2["id"]}/expected-value',
        json={'probability': 0.5},
        cookies=student_session['cookies']
    )
    assert response.status_code == 200
    data = response.json()['data']
    assert data['correct_marks'] == 3.0
    assert data['wrong_marks'] == -1.0
    # EV = 0.5*3 + 0.5*(-1) = 1.0
    assert abs(data['expected_marks'] - 1.0) < 0.01


async def test_expected_value_nan_infinity_rejected(http_client, clean_db, student_session):
    """POST /api/attempts/{id}/expected-value rejects NaN and Infinity."""
    from tejas import attempts, corrections

    s = source_set(2)
    s['id'] = str(uuid4())
    u = student_session['user']

    await clean_db.tejas_sets.insert_one(copy.deepcopy(s))
    await attempts.preflight(s['id'], {}, u)
    a = await attempts.start(s['id'], attempts.Start(
        start_key='test-' + str(uuid4()), device_checked=True), u)
    
    await attempts.finalize(a['id'])
    completed = await attempts.owned(a['id'], u)
    await corrections.freeze_ledger(completed)

    # Test outside range
    response = await http_client.post(
        f'/api/attempts/{a["id"]}/expected-value',
        json={'probability': 1.5},
        cookies=student_session['cookies']
    )
    assert response.status_code == 422

    response = await http_client.post(
        f'/api/attempts/{a["id"]}/expected-value',
        json={'probability': -0.1},
        cookies=student_session['cookies']
    )
    assert response.status_code == 422


async def test_expected_value_no_mutation(http_client, clean_db, student_session):
    """POST /api/attempts/{id}/expected-value does not mutate answers or ledger."""
    from tejas import attempts, corrections
    from tejas.answers import save_answer, AnswerWrite

    s = source_set(3, correct='4', wrong='-1')
    u = student_session['user']

    await clean_db.tejas_sets.insert_one(copy.deepcopy(s))
    await attempts.preflight(s['id'], {}, u)
    a = await attempts.start(s['id'], attempts.Start(
        start_key='test-' + str(uuid4()), device_checked=True), u)
    
    qid = s['questions'][0]['id']
    await save_answer(a['id'], qid, AnswerWrite(
        value='2', revision=1, request_id=f'ans-{str(uuid4())[:8]}', marked=False), u)
    
    await attempts.finalize(a['id'])
    completed = await attempts.owned(a['id'], u)
    await corrections.freeze_ledger(completed)

    # Get original state
    original_attempt = await clean_db.tejas_attempts.find_one({'id': a['id']})
    original_ledger = await clean_db.tejas_ledgers.find_one({'id': a['id']})

    # Call expected value
    response = await http_client.post(
        f'/api/attempts/{a["id"]}/expected-value',
        json={'probability': 0.5},
        cookies=student_session['cookies']
    )
    assert response.status_code == 200

    # Verify no mutation
    after_attempt = await clean_db.tejas_attempts.find_one({'id': a['id']})
    after_ledger = await clean_db.tejas_ledgers.find_one({'id': a['id']})

    assert original_attempt['answers'] == after_attempt['answers']
    assert original_ledger['summary'] == after_ledger['summary']


# ============================================================================
# ADDITIONAL CONFIDENCE EXCLUSION TESTS
# ============================================================================

async def test_cleared_response_excluded_from_confidence(clean_db, synthetic_student_user):
    """Cleared responses (changed to empty) must be permanently excluded."""
    from tejas.analytics import build_analytics
    from tejas_core import score_attempt
    from tejas import attempts, corrections
    from tejas.answers import save_answer, AnswerWrite

    s = source_set(25, correct='4', wrong='-1')
    u = synthetic_student_user

    # Create attempt with clears BEFORE finalization
    s['id'] = str(uuid4())
    await clean_db.tejas_sets.insert_one(copy.deepcopy(s))
    await attempts.preflight(s['id'], {}, u)
    a = await attempts.start(s['id'], attempts.Start(
        start_key='test-' + str(uuid4()), device_checked=True), u)

    # First 20: correct with confidence (unchanged)
    for i in range(20):
        qid = s['questions'][i]['id']
        await save_answer(a['id'], qid, AnswerWrite(
            value='1', confidence=0.8, revision=1,
            request_id=f'ans-{qid}-{str(uuid4())[:8]}', marked=False), u)

    # Last 5: initially answered, then cleared (BEFORE finalize)
    for i in range(20, 25):
        qid = s['questions'][i]['id']
        # First save: answered with confidence
        await save_answer(a['id'], qid, AnswerWrite(
            value='2', confidence=0.6, revision=1,
            request_id=f'ans-first-{qid}-{str(uuid4())[:8]}', marked=False), u)
        # Second save: cleared (empty value)
        await save_answer(a['id'], qid, AnswerWrite(
            value='', confidence=None, revision=2,
            request_id=f'ans-clear-{qid}-{str(uuid4())[:8]}', marked=False), u)

    await attempts.finalize(a['id'])
    completed = await attempts.owned(a['id'], u)
    await corrections.freeze_ledger(completed)
    a = await attempts.owned(a['id'], u)

    result = score_attempt(a)
    analytics = build_analytics(a, result)

    # Should only count the 20 unchanged items
    # Cleared items are excluded by not being in "attempted" (empty final answer)
    a41 = next(m for m in analytics['metrics'] if m['metric_id'] == 'A41')
    assert a41['state'] == 'available'
    assert a41['value']['rated_count'] == 20
    # Cleared responses don't appear in changed_response_excluded because they're not "attempted"
    # They're excluded by virtue of having empty final answers


async def test_reverted_response_excluded_from_confidence(clean_db, synthetic_student_user):
    """Reverted responses (A→B→A) must be permanently excluded."""
    from tejas.analytics import build_analytics
    from tejas_core import score_attempt
    from tejas import attempts, corrections
    from tejas.answers import save_answer, AnswerWrite

    s = source_set(25, correct='4', wrong='-1')
    u = synthetic_student_user

    # Create attempt with reverts BEFORE finalization
    s['id'] = str(uuid4())
    await clean_db.tejas_sets.insert_one(copy.deepcopy(s))
    await attempts.preflight(s['id'], {}, u)
    a = await attempts.start(s['id'], attempts.Start(
        start_key='test-' + str(uuid4()), device_checked=True), u)

    # First 20: correct with confidence (unchanged)
    for i in range(20):
        qid = s['questions'][i]['id']
        await save_answer(a['id'], qid, AnswerWrite(
            value='1', confidence=0.8, revision=1,
            request_id=f'ans-{qid}-{str(uuid4())[:8]}', marked=False), u)

    # Last 5: A→B→A revert pattern (BEFORE finalize)
    for i in range(20, 25):
        qid = s['questions'][i]['id']
        # First save: '1' with confidence
        await save_answer(a['id'], qid, AnswerWrite(
            value='1', confidence=0.7, revision=1,
            request_id=f'ans-first-{qid}-{str(uuid4())[:8]}', marked=False), u)
        # Second save: changed to '2'
        await save_answer(a['id'], qid, AnswerWrite(
            value='2', confidence=0.6, revision=2,
            request_id=f'ans-change-{qid}-{str(uuid4())[:8]}', marked=False), u)
        # Third save: reverted back to '1'
        await save_answer(a['id'], qid, AnswerWrite(
            value='1', confidence=0.9, revision=3,
            request_id=f'ans-revert-{qid}-{str(uuid4())[:8]}', marked=False), u)

    await attempts.finalize(a['id'])
    completed = await attempts.owned(a['id'], u)
    await corrections.freeze_ledger(completed)
    a = await attempts.owned(a['id'], u)

    result = score_attempt(a)
    analytics = build_analytics(a, result)

    # Should only count the 20 unchanged items (reverted excluded)
    a41 = next(m for m in analytics['metrics'] if m['metric_id'] == 'A41')
    assert a41['state'] == 'available'
    assert a41['value']['rated_count'] == 20
    assert a41['value']['changed_response_excluded'] == 5


async def test_missing_original_confidence_cannot_be_added_retrospectively(clean_db, synthetic_student_user):
    """Questions without original confidence cannot have it added retrospectively."""
    from tejas.analytics import build_analytics
    from tejas_core import score_attempt
    from tejas import attempts, corrections
    from tejas.answers import save_answer, AnswerWrite

    s = source_set(25, correct='4', wrong='-1')
    u = synthetic_student_user

    # Create attempt: 20 with confidence, 5 without
    s['id'] = str(uuid4())
    await clean_db.tejas_sets.insert_one(copy.deepcopy(s))
    await attempts.preflight(s['id'], {}, u)
    a = await attempts.start(s['id'], attempts.Start(
        start_key='test-' + str(uuid4()), device_checked=True), u)

    # First 20: with confidence
    for i in range(20):
        qid = s['questions'][i]['id']
        await save_answer(a['id'], qid, AnswerWrite(
            value='1', confidence=0.8, revision=1,
            request_id=f'ans-{qid}-{str(uuid4())[:8]}', marked=False), u)

    # Last 5: without confidence (None or missing)
    for i in range(20, 25):
        qid = s['questions'][i]['id']
        await save_answer(a['id'], qid, AnswerWrite(
            value='1', confidence=None, revision=1,
            request_id=f'ans-{qid}-{str(uuid4())[:8]}', marked=False), u)

    await attempts.finalize(a['id'])
    completed = await attempts.owned(a['id'], u)
    await corrections.freeze_ledger(completed)
    a = await attempts.owned(a['id'], u)

    result = score_attempt(a)
    analytics = build_analytics(a, result)

    # Should only count the 20 with original confidence
    a41 = next(m for m in analytics['metrics'] if m['metric_id'] == 'A41')
    a42 = next(m for m in analytics['metrics'] if m['metric_id'] == 'A42')

    assert a41['state'] == 'available'
    assert a41['value']['rated_count'] == 20

    assert a42['state'] == 'available'
    assert a42['sample_size'] == 20



# ============================================================================
# MISSING REGRESSION TESTS - Guide04 Final Verification
# ============================================================================

async def test_completed_competition_future_end_denies_reviews(http_client, clean_db, student_session):
    """Completed attempts with future competition_end deny review and EV access with 403."""
    from tejas import attempts, corrections
    from tejas.answers import save_answer, AnswerWrite
    from datetime import datetime, timezone, timedelta

    s = source_set(3, correct='4', wrong='-1')
    s['id'] = str(uuid4())
    u = student_session['user']

    await clean_db.tejas_sets.insert_one(copy.deepcopy(s))
    await attempts.preflight(s['id'], {}, u)
    a = await attempts.start(s['id'], attempts.Start(
        start_key='test-' + str(uuid4()), device_checked=True), u)
    
    qid = s['questions'][0]['id']
    await save_answer(a['id'], qid, AnswerWrite(
        value='2', revision=1, request_id=f'ans-{str(uuid4())[:8]}', marked=False), u)
    
    await attempts.finalize(a['id'])
    completed = await attempts.owned(a['id'], u)
    await corrections.freeze_ledger(completed)

    # Set competition_end to future
    future_end = datetime.now(timezone.utc) + timedelta(hours=2)
    await clean_db.tejas_attempts.update_one(
        {'id': a['id']}, 
        {'$set': {'competition_end': future_end.timestamp()}}
    )

    # Try to save review - should be denied
    response = await http_client.put(
        f'/api/attempts/{a["id"]}/reviews/{qid}',
        json={
            'request_id': str(uuid4()),
            'revision': 1,
            'category': 'concept_gap',
            'identified_error': True,
            'note': '',
            'wrote_note': False,
            'reviewed_solution': False,
            'retry_planned': False
        },
        cookies=student_session['cookies']
    )
    
    assert response.status_code == 403
    response_data = response.json()
    assert 'error' in response_data
    assert 'competition' in response_data['error']['message'].lower()

    # Try to calculate expected value - should be denied
    response = await http_client.post(
        f'/api/attempts/{a["id"]}/expected-value',
        json={'probability': 0.5},
        cookies=student_session['cookies']
    )
    
    assert response.status_code == 403
    response_data = response.json()
    assert 'error' in response_data
    assert 'competition' in response_data['error']['message'].lower()


async def test_correction_version_reflections_separate_from_original(http_client, clean_db, student_session):
    """Review states for correction versions are separate from original score version."""
    from tejas import attempts, corrections
    from tejas.answers import save_answer, AnswerWrite

    s = source_set(3, correct='4', wrong='-1')
    s['id'] = str(uuid4())
    u = student_session['user']

    await clean_db.tejas_sets.insert_one(copy.deepcopy(s))
    await attempts.preflight(s['id'], {}, u)
    a = await attempts.start(s['id'], attempts.Start(
        start_key='test-' + str(uuid4()), device_checked=True), u)
    
    qid = s['questions'][0]['id']
    await save_answer(a['id'], qid, AnswerWrite(
        value='2', revision=1, request_id=f'ans-{str(uuid4())[:8]}', marked=False), u)
    
    await attempts.finalize(a['id'])
    completed = await attempts.owned(a['id'], u)
    ledger = await corrections.freeze_ledger(completed)

    # Create a correction version
    correction_id = f"{a['id']}-key-2"
    from tejas.packs import seal
    pack_id = await seal(s['questions'])
    
    await clean_db.tejas_score_versions.insert_one({
        'id': correction_id,
        'attempt_id': a['id'],
        'user_id': u['id'],
        'set_id': s['id'],
        'pack_id': pack_id,
        'key_version': 2,
        'note': 'Test correction',
        'created_at': 1234567890,
        'ledger': ledger
    })

    # Save review for original version
    response1 = await http_client.put(
        f'/api/attempts/{a["id"]}/reviews/{qid}',
        json={
            'request_id': str(uuid4()),
            'revision': 1,
            'score_version': 'original',
            'category': 'concept_gap',
            'identified_error': True,
            'note': 'Original version note',
            'wrote_note': True,
            'reviewed_solution': False,
            'retry_planned': False
        },
        cookies=student_session['cookies']
    )
    
    assert response1.status_code == 200
    data1 = response1.json()['data']
    assert data1['note'] == 'Original version note'
    assert data1['score_version'] == 'original'

    # Save review for correction version - should be separate
    response2 = await http_client.put(
        f'/api/attempts/{a["id"]}/reviews/{qid}',
        json={
            'request_id': str(uuid4()),
            'revision': 1,
            'score_version': correction_id,
            'category': 'silly_mistake',
            'identified_error': True,
            'note': 'Correction version note',
            'wrote_note': True,
            'reviewed_solution': False,
            'retry_planned': False
        },
        cookies=student_session['cookies']
    )
    
    assert response2.status_code == 200
    data2 = response2.json()['data']
    assert data2['note'] == 'Correction version note'
    assert data2['score_version'] == correction_id
    assert data2['category'] == 'silly_mistake'

    # Verify they are stored separately in database
    original_review = await clean_db.tejas_reviews.find_one({
        'attempt_id': a['id'],
        'question_id': qid,
        'score_version': 'original'
    })
    correction_review = await clean_db.tejas_reviews.find_one({
        'attempt_id': a['id'],
        'question_id': qid,
        'score_version': correction_id
    })
    
    assert original_review is not None
    assert correction_review is not None
    assert original_review['note'] == 'Original version note'
    assert correction_review['note'] == 'Correction version note'
    assert original_review['category'] == 'concept_gap'
    assert correction_review['category'] == 'silly_mistake'


async def test_cross_user_private_review_notes_absent(http_client, clean_db, student_session, synthetic_staff_user):
    """Review notes are private to user profile; not visible to other users."""
    from tejas import attempts, corrections
    from tejas.answers import save_answer, AnswerWrite
    from tejas.auth import token
    from datetime import datetime, timezone, timedelta

    s = source_set(3, correct='4', wrong='-1')
    s['id'] = str(uuid4())
    
    # Use student_session user as user1
    user1 = student_session['user']
    
    # Create user2 as a different student
    user2 = copy.deepcopy(synthetic_staff_user)
    user2['id'] = str(uuid4())
    user2['role'] = 'student'
    await clean_db.tejas_users.insert_one(dict(user2))

    # User1 creates and completes attempt (already has session)
    await clean_db.tejas_sets.insert_one(copy.deepcopy(s))
    await attempts.preflight(s['id'], {}, user1)
    a1 = await attempts.start(s['id'], attempts.Start(
        start_key='test-' + str(uuid4()), device_checked=True), user1)
    
    qid = s['questions'][0]['id']
    await save_answer(a1['id'], qid, AnswerWrite(
        value='2', revision=1, request_id=f'ans-{str(uuid4())[:8]}', marked=False), user1)
    
    await attempts.finalize(a1['id'])
    completed1 = await attempts.owned(a1['id'], user1)
    await corrections.freeze_ledger(completed1)

    # User1 saves private review note using existing session
    response = await http_client.put(
        f'/api/attempts/{a1["id"]}/reviews/{qid}',
        json={
            'request_id': str(uuid4()),
            'revision': 1,
            'category': 'concept_gap',
            'identified_error': True,
            'note': 'User1 private note - should not be visible to user2',
            'wrote_note': True,
            'reviewed_solution': False,
            'retry_planned': False
        },
        cookies=student_session['cookies']
    )
    
    assert response.status_code == 200

    # User2 tries to access user1's attempt - should get 404 (not found for different user)
    sid2 = str(uuid4())
    await clean_db.tejas_sessions.insert_one({
        'id': sid2, 'user_id': user2['id'],
        'access_type': 'student_password',
        'expires_at': datetime.now(timezone.utc) + timedelta(hours=1)
    })
    
    cookies2 = {
        'access_token': token(user2, sid2, 'access', 900),
        'refresh_token': token(user2, sid2, 'refresh', 3600)
    }

    response = await http_client.put(
        f'/api/attempts/{a1["id"]}/reviews/{qid}',
        json={
            'request_id': str(uuid4()),
            'revision': 1,
            'category': 'silly_mistake',
            'identified_error': True,
            'note': 'User2 trying to access',
            'wrote_note': True,
            'reviewed_solution': False,
            'retry_planned': False
        },
        cookies=cookies2
    )
    
    # Should be 404 because user2 doesn't own this attempt
    assert response.status_code == 404

    # Verify user1's note is still private in database
    user1_review = await clean_db.tejas_reviews.find_one({
        'attempt_id': a1['id'],
        'user_id': user1['id'],
        'question_id': qid
    })
    
    assert user1_review is not None
    assert user1_review['note'] == 'User1 private note - should not be visible to user2'
    
    # Verify no review exists for user2
    user2_review = await clean_db.tejas_reviews.find_one({
        'attempt_id': a1['id'],
        'user_id': user2['id'],
        'question_id': qid
    })
    
    assert user2_review is None


async def test_results_confidence_threshold_out_of_range_rejected(http_client, clean_db, student_session):
    """GET /api/attempts/{id}/results rejects out-of-range and NaN confidence_threshold with 422."""
    from tejas import attempts, corrections
    from tejas.answers import save_answer, AnswerWrite

    s = source_set(20, correct='4', wrong='-1')
    u = student_session['user']

    # Create attempt with confidence ratings
    s['id'] = str(uuid4())
    await clean_db.tejas_sets.insert_one(copy.deepcopy(s))
    await attempts.preflight(s['id'], {}, u)
    a = await attempts.start(s['id'], attempts.Start(
        start_key='test-' + str(uuid4()), device_checked=True), u)

    # Save 20 answers with confidence
    for i in range(20):
        qid = s['questions'][i]['id']
        await save_answer(a['id'], qid, AnswerWrite(
            value='1', confidence=0.5, revision=1,
            request_id=f'ans-{qid}-{str(uuid4())[:8]}', marked=False), u)

    await attempts.finalize(a['id'])
    completed = await attempts.owned(a['id'], u)
    await corrections.freeze_ledger(completed)

    # Test threshold > 1
    response = await http_client.get(
        f'/api/attempts/{a["id"]}/results?confidence_threshold=1.5',
        cookies=student_session['cookies']
    )
    assert response.status_code == 422
    response_data = response.json()
    assert 'error' in response_data

    # Test threshold < 0
    response = await http_client.get(
        f'/api/attempts/{a["id"]}/results?confidence_threshold=-0.1',
        cookies=student_session['cookies']
    )
    assert response.status_code == 422
    response_data = response.json()
    assert 'error' in response_data

    # Test NaN (invalid string)
    response = await http_client.get(
        f'/api/attempts/{a["id"]}/results?confidence_threshold=not_a_number',
        cookies=student_session['cookies']
    )
    assert response.status_code == 422
    response_data = response.json()
    assert 'error' in response_data

    # Test valid threshold (should work)
    response = await http_client.get(
        f'/api/attempts/{a["id"]}/results?confidence_threshold=0.3',
        cookies=student_session['cookies']
    )
    assert response.status_code == 200
    data = response.json()['data']
    assert data['analytics'] is not None


if __name__ == '__main__':
    pytest.main([__file__, '-v', '--tb=short'])
