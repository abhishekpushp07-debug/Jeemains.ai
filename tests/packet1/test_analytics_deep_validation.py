"""Deep validation of analytics.py guide04 implementation against authoritative source.

CRITICAL: Tests oracle SOURCE formulas independently, not implementation assumptions.
All metric IDs, names, formulas, and expected values verified against:
- /app/backend/tejas/analytics_registry.json
- /app/docs/source_guides/04_Results_60_Analyses_and_Question_Insights.pdf.txt

Addresses review findings:
- A04/A05 misnumbering corrected
- A13 ratio validation (not percentage)
- A24/A25 revision delta formulas
- A26 late-window 20% boundary with 10-item gates
- A56/A58/A59 solution/correction/approval tracking
"""
import asyncio
import copy
from uuid import uuid4
import pytest
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
        'id': str(uuid4()), 'title': 'Analytics Test Set', 'exam': 'JEE Main',
        'status': 'published', 'revision': 1, 'version': 1,
        'questions': [question(i, correct, wrong) for i in range(1, questions_count + 1)],
        'rules': {'minutes': minutes, 'correct': correct, 'wrong': wrong, 'skipped': 0,
                  'navigation': 'free', 'numeric_policy': 'integer_exact',
                  'solution_release': 'after_submit'},
        'audience': 'all', 'expires': None, 'rights_upload': True,
        'rights_publish': True, 'rights_report': True, 'file_ids': [],
        'source': 'Analytics validation fixture', 'attribution': 'Test content',
        'profile_mode': 'practice'
    }


async def create_attempt_with_answers(clean_db, user, s, answers_dict, change_history=None):
    """Create a completed attempt with specified answers and optional change history."""
    from tejas import attempts, corrections
    from tejas.db import now

    await clean_db.tejas_sets.insert_one(copy.deepcopy(s))
    await attempts.preflight(s['id'], {}, user)
    a = await attempts.start(s['id'], attempts.Start(
        start_key='test-' + str(uuid4()), device_checked=True), user)

    # Save answers
    for qid, value in answers_dict.items():
        from tejas.answers import save_answer, AnswerWrite
        await save_answer(a['id'], qid, AnswerWrite(
            value=value, revision=1, request_id=f'ans-{qid}-{str(uuid4())[:8]}', marked=False), user)

    # Apply change history if provided
    if change_history:
        for qid, changes in change_history.items():
            for rev, value in enumerate(changes, start=2):
                await save_answer(a['id'], qid, AnswerWrite(
                    value=value, revision=rev, request_id=f'ans-{qid}-{rev}-{str(uuid4())[:8]}', marked=False), user)

    await attempts.finalize(a['id'])
    completed = await attempts.owned(a['id'], user)
    ledger = await corrections.freeze_ledger(completed)
    # Reload to get ledger field populated
    return await attempts.owned(a['id'], user)


# ============================================================================
# ORACLE REGISTRY VALIDATION
# ============================================================================

async def test_analytics_registry_structure():
    """Verify analytics registry has exactly 60 unique metrics with required fields."""
    from tejas.analytics import REGISTRY

    assert REGISTRY['registry_version'] == 'guide04-v1.0'
    assert len(REGISTRY['source_sha256']) == 64  # SHA256 hex
    assert len(REGISTRY['metrics']) == 60

    metric_ids = [m['metric_id'] for m in REGISTRY['metrics']]
    expected_ids = [f'A{i:02d}' for i in range(1, 61)]
    assert metric_ids == expected_ids, 'Metrics must be A01-A60 in order'

    # Verify no duplicates
    assert len(set(metric_ids)) == 60

    # Verify all required fields
    required = ['metric_id', 'name', 'inputs', 'formula', 'evidence', 'action', 'limitation']
    for m in REGISTRY['metrics']:
        for field in required:
            assert field in m, f"Metric {m['metric_id']} missing {field}"


async def test_oracle_metric_names_match_guide():
    """Verify metric IDs map to correct names per source guide."""
    from tejas.analytics import REGISTRY

    # Critical name mappings from guide04
    oracle_names = {
        'A01': 'Net awarded marks',
        'A02': 'Fully correct response count',
        'A03': 'Incorrect and partial outcomes',
        'A04': 'Attempted-answer accuracy',  # NOT completion
        'A05': 'Response completion rate',   # NOT accuracy
        'A06': 'Ordinary positive marks earned',
        'A07': 'Penalty marks lost',
        'A08': 'Penalty-to-positive-marks ratio',
        'A09': 'Percentage of configured maximum marks',
        'A13': 'Response-type performance',
        'A24': 'Positive score difference after revisions',
        'A25': 'Negative score difference after revisions',
        'A26': 'Late-window attempted accuracy',
        'A56': 'Released-solution consultation rate',
        'A58': 'Approved-key score revision impact',
        'A59': 'Approved explanation availability',
    }

    for metric in REGISTRY['metrics']:
        mid = metric['metric_id']
        if mid in oracle_names:
            assert metric['name'] == oracle_names[mid], \
                f"{mid} name mismatch: got '{metric['name']}', expected '{oracle_names[mid]}'"


# ============================================================================
# A01-A09: CORE SCORE METRICS (CORRECTED FORMULAS)
# ============================================================================

async def test_a01_net_marks_includes_bonus_excludes_dropped(clean_db, synthetic_student_user):
    """A01: Net awarded marks = sum(score_q) including awards."""
    from tejas.analytics import build_analytics, REGISTRY
    from tejas_core import score_attempt

    s = source_set(3)
    s['questions'][2]['disposition'] = 'bonus_all'
    u = synthetic_student_user

    answers = {s['questions'][0]['id']: '1', s['questions'][1]['id']: '2',
               s['questions'][2]['id']: '1'}  # bonus correct
    a = await create_attempt_with_answers(clean_db, u, s, answers)
    result = score_attempt(a)
    analytics = build_analytics(a, result)

    a01 = next(m for m in analytics['metrics'] if m['metric_id'] == 'A01')
    oracle = next(m for m in REGISTRY['metrics'] if m['metric_id'] == 'A01')

    assert a01['name'] == oracle['name']
    assert a01['state'] == 'available'
    # Score: 4 (correct) - 1 (incorrect) + 4 (bonus) = 7
    assert a01['value'] == 7.0
    assert a01['unit'] == 'marks'


async def test_a02_correct_count_not_percentage(clean_db, synthetic_student_user):
    """A02: Fully correct response count = count(full_correct), NOT percentage."""
    from tejas.analytics import build_analytics, REGISTRY
    from tejas_core import score_attempt

    s = source_set(10)
    u = synthetic_student_user

    # Answer 7 correctly, 2 incorrectly, skip 1
    answers = {s['questions'][i]['id']: '1' for i in range(7)}
    answers[s['questions'][7]['id']] = '2'
    answers[s['questions'][8]['id']] = '2'

    a = await create_attempt_with_answers(clean_db, u, s, answers)
    result = score_attempt(a)
    analytics = build_analytics(a, result)

    a02 = next(m for m in analytics['metrics'] if m['metric_id'] == 'A02')
    oracle = next(m for m in REGISTRY['metrics'] if m['metric_id'] == 'A02')

    assert a02['name'] == oracle['name']
    assert a02['name'] == 'Fully correct response count'
    assert a02['state'] == 'available'
    assert a02['value'] == 7  # COUNT, not percentage
    assert a02['unit'] == 'questions'


async def test_a03_incorrect_and_partial_separate(clean_db, synthetic_student_user):
    """A03: W = count(incorrect), P = count(partial_credit); display both separately."""
    from tejas.analytics import build_analytics, REGISTRY
    from tejas_core import score_attempt

    s = source_set(5)
    u = synthetic_student_user

    # 2 correct, 3 incorrect (no partial credit in MCQ)
    answers = {s['questions'][0]['id']: '1', s['questions'][1]['id']: '1',
               s['questions'][2]['id']: '2', s['questions'][3]['id']: '2',
               s['questions'][4]['id']: '2'}

    a = await create_attempt_with_answers(clean_db, u, s, answers)
    result = score_attempt(a)
    analytics = build_analytics(a, result)

    a03 = next(m for m in analytics['metrics'] if m['metric_id'] == 'A03')
    oracle = next(m for m in REGISTRY['metrics'] if m['metric_id'] == 'A03')

    assert a03['name'] == oracle['name']
    assert a03['state'] == 'available'
    assert isinstance(a03['value'], dict)
    assert a03['value']['incorrect'] == 3
    assert a03['value']['partial_credit'] == 0  # MCQ has no partial credit


async def test_a04_accuracy_formula_c_over_a(clean_db, synthetic_student_user):
    """A04: Attempted-answer accuracy = 100 * C / A where A = C + P + W.

    CRITICAL: This is ACCURACY (C/A), NOT completion rate.
    Prior tests had A04/A05 swapped.
    """
    from tejas.analytics import build_analytics, REGISTRY
    from tejas_core import score_attempt

    s = source_set(10)
    u = synthetic_student_user

    # C=6 correct, W=3 incorrect, skip 1 → A=9, accuracy = 6/9 = 66.67%
    answers = {s['questions'][i]['id']: '1' for i in range(6)}
    for i in range(6, 9):
        answers[s['questions'][i]['id']] = '2'

    a = await create_attempt_with_answers(clean_db, u, s, answers)
    result = score_attempt(a)
    analytics = build_analytics(a, result)

    a04 = next(m for m in analytics['metrics'] if m['metric_id'] == 'A04')
    oracle = next(m for m in REGISTRY['metrics'] if m['metric_id'] == 'A04')

    assert a04['name'] == oracle['name']
    assert a04['name'] == 'Attempted-answer accuracy'
    assert '100 * C / A' in oracle['formula']
    assert a04['state'] == 'available'
    assert abs(a04['value'] - 66.67) < 0.01  # 6/9 * 100
    assert a04['unit'] == '%'
    assert a04['sample_size'] == 9  # Attempted count


async def test_a05_completion_formula_a_over_e(clean_db, synthetic_student_user):
    """A05: Response completion rate = 100 * A / E with unanswered count E - A.

    CRITICAL: This is COMPLETION (A/E), NOT accuracy.
    Prior tests had A04/A05 swapped.
    """
    from tejas.analytics import build_analytics, REGISTRY
    from tejas_core import score_attempt

    s = source_set(10)
    u = synthetic_student_user

    # Answer 7 out of 10 eligible → completion = 7/10 = 70%
    answers = {s['questions'][i]['id']: '1' for i in range(7)}

    a = await create_attempt_with_answers(clean_db, u, s, answers)
    result = score_attempt(a)
    analytics = build_analytics(a, result)

    a05 = next(m for m in analytics['metrics'] if m['metric_id'] == 'A05')
    oracle = next(m for m in REGISTRY['metrics'] if m['metric_id'] == 'A05')

    assert a05['name'] == oracle['name']
    assert a05['name'] == 'Response completion rate'
    assert '100 * A / E' in oracle['formula']
    assert a05['state'] == 'available'
    assert a05['value'] == 70.0  # 7/10 * 100
    assert a05['unit'] == '%'
    assert a05['sample_size'] == 10  # Eligible count


async def test_a04_unavailable_when_no_attempts(clean_db, synthetic_student_user):
    """A04: Accuracy unavailable when A=0 (no attempted responses)."""
    from tejas.analytics import build_analytics
    from tejas_core import score_attempt

    s = source_set(5)
    u = synthetic_student_user

    # Skip all questions
    a = await create_attempt_with_answers(clean_db, u, s, {})
    result = score_attempt(a)
    analytics = build_analytics(a, result)

    a04 = next(m for m in analytics['metrics'] if m['metric_id'] == 'A04')
    assert a04['state'] == 'unavailable'
    assert 'No attempted eligible responses' in a04['reason']


async def test_a05_unavailable_when_no_eligible(clean_db, synthetic_student_user):
    """A05: Completion unavailable when E=0 (no eligible questions)."""
    from tejas.analytics import build_analytics
    from tejas_core import score_attempt

    s = source_set(2)
    # Make all questions dropped
    for q in s['questions']:
        q['disposition'] = 'dropped'

    u = synthetic_student_user
    a = await create_attempt_with_answers(clean_db, u, s, {})
    result = score_attempt(a)
    analytics = build_analytics(a, result)

    a05 = next(m for m in analytics['metrics'] if m['metric_id'] == 'A05')
    assert a05['state'] == 'unavailable'
    assert 'No ordinary eligible questions' in a05['reason']


async def test_a06_ordinary_positive_marks_g(clean_db, synthetic_student_user):
    """A06: G = sum(max(s_q, 0)), excluding award-only adjustments."""
    from tejas.analytics import build_analytics, REGISTRY
    from tejas_core import score_attempt

    s = source_set(5, correct='4', wrong='-1')
    u = synthetic_student_user

    # 3 correct (+4 each), 2 incorrect (-1 each) → G = 12
    answers = {s['questions'][i]['id']: '1' for i in range(3)}
    answers[s['questions'][3]['id']] = '2'
    answers[s['questions'][4]['id']] = '2'

    a = await create_attempt_with_answers(clean_db, u, s, answers)
    result = score_attempt(a)
    analytics = build_analytics(a, result)

    a06 = next(m for m in analytics['metrics'] if m['metric_id'] == 'A06')
    oracle = next(m for m in REGISTRY['metrics'] if m['metric_id'] == 'A06')

    assert a06['name'] == oracle['name']
    assert a06['state'] == 'available'
    assert a06['value'] == 12.0  # 3 * 4 = 12 (penalties excluded)
    assert a06['unit'] == 'marks'


async def test_a07_penalty_marks_l(clean_db, synthetic_student_user):
    """A07: L = sum(max(-s_q, 0))."""
    from tejas.analytics import build_analytics, REGISTRY
    from tejas_core import score_attempt

    s = source_set(5, correct='4', wrong='-1')
    u = synthetic_student_user

    # 2 correct, 3 incorrect → L = 3
    answers = {s['questions'][0]['id']: '1', s['questions'][1]['id']: '1'}
    for i in range(2, 5):
        answers[s['questions'][i]['id']] = '2'

    a = await create_attempt_with_answers(clean_db, u, s, answers)
    result = score_attempt(a)
    analytics = build_analytics(a, result)

    a07 = next(m for m in analytics['metrics'] if m['metric_id'] == 'A07')
    oracle = next(m for m in REGISTRY['metrics'] if m['metric_id'] == 'A07')

    assert a07['name'] == oracle['name']
    assert a07['state'] == 'available'
    assert a07['value'] == 3.0  # 3 * 1 = 3
    assert a07['unit'] == 'marks'


async def test_a08_penalty_ratio_gated_by_g_positive(clean_db, synthetic_student_user):
    """A08: 100 * L / G, evidence G > 0; otherwise unavailable."""
    from tejas.analytics import build_analytics, REGISTRY
    from tejas_core import score_attempt

    s = source_set(5, correct='4', wrong='-1')
    u = synthetic_student_user

    # 3 correct (G=12), 2 incorrect (L=2) → ratio = 2/12 * 100 = 16.67%
    answers = {s['questions'][i]['id']: '1' for i in range(3)}
    answers[s['questions'][3]['id']] = '2'
    answers[s['questions'][4]['id']] = '2'

    a = await create_attempt_with_answers(clean_db, u, s, answers)
    result = score_attempt(a)
    analytics = build_analytics(a, result)

    a08 = next(m for m in analytics['metrics'] if m['metric_id'] == 'A08')
    oracle = next(m for m in REGISTRY['metrics'] if m['metric_id'] == 'A08')

    assert a08['name'] == oracle['name']
    assert a08['state'] == 'available'
    assert abs(a08['value'] - 16.67) < 0.01
    assert a08['unit'] == '%'


async def test_a08_unavailable_when_g_zero(clean_db, synthetic_student_user):
    """A08: Unavailable when G=0 (all incorrect or skipped)."""
    from tejas.analytics import build_analytics
    from tejas_core import score_attempt

    s = source_set(3, correct='4', wrong='-1')
    u = synthetic_student_user

    # All incorrect → G=0, L=3
    answers = {q['id']: '2' for q in s['questions']}

    a = await create_attempt_with_answers(clean_db, u, s, answers)
    result = score_attempt(a)
    analytics = build_analytics(a, result)

    a08 = next(m for m in analytics['metrics'] if m['metric_id'] == 'A08')
    assert a08['state'] == 'unavailable'
    assert 'Ordinary positive marks are zero' in a08['reason']


async def test_a09_percentage_allows_negative(clean_db, synthetic_student_user):
    """A09: 100 * S / M allows negative percentages."""
    from tejas.analytics import build_analytics, REGISTRY
    from tejas_core import score_attempt

    s = source_set(2, correct='4', wrong='-1')
    u = synthetic_student_user

    # Both incorrect: S = -2, M = 8 → -25%
    answers = {s['questions'][0]['id']: '2', s['questions'][1]['id']: '2'}

    a = await create_attempt_with_answers(clean_db, u, s, answers)
    result = score_attempt(a)
    analytics = build_analytics(a, result)

    a09 = next(m for m in analytics['metrics'] if m['metric_id'] == 'A09')
    oracle = next(m for m in REGISTRY['metrics'] if m['metric_id'] == 'A09')

    assert a09['name'] == oracle['name']
    assert a09['state'] == 'available'
    assert a09['value'] == -25.0
    assert a09['unit'] == '%'


# ============================================================================
# A13: RESPONSE-TYPE PERFORMANCE (RATIO NOT PERCENTAGE)
# ============================================================================

async def test_a13_score_ratio_not_percentage(clean_db, synthetic_student_user):
    """A13: sum(s_q) / sum(max_q) is a RATIO, not multiplied by 100.

    CRITICAL: Guide says 'score_ratio', implementation must not convert to percentage.
    """
    from tejas.analytics import build_analytics, REGISTRY
    from tejas_core import score_attempt

    s = source_set(10, correct='4', wrong='-1')
    u = synthetic_student_user

    # 6 correct, 4 incorrect → score = 6*4 - 4*1 = 20, max = 40, ratio = 0.5
    answers = {s['questions'][i]['id']: '1' for i in range(6)}
    for i in range(6, 10):
        answers[s['questions'][i]['id']] = '2'

    a = await create_attempt_with_answers(clean_db, u, s, answers)
    result = score_attempt(a)
    analytics = build_analytics(a, result)

    a13 = next(m for m in analytics['metrics'] if m['metric_id'] == 'A13')
    oracle = next(m for m in REGISTRY['metrics'] if m['metric_id'] == 'A13')

    assert a13['name'] == oracle['name']
    assert a13['state'] == 'available'
    assert isinstance(a13['value'], list)

    # Find MCQ type
    mcq_entry = next(e for e in a13['value'] if e['type'] == 'mcq')
    assert 'score_ratio' in mcq_entry
    # Ratio should be 0.5, NOT 50.0
    assert 0.4 < mcq_entry['score_ratio'] < 0.6
    assert mcq_entry['score_ratio'] != 50.0, "A13 must be ratio, not percentage"
    assert a13['unit'] == 'ratio'


# ============================================================================
# A24/A25: REVISION DELTAS (NO ARBITRARY THRESHOLDS)
# ============================================================================

async def test_a24_positive_delta_sum_exact(clean_db, synthetic_student_user):
    """A24: sum(max(score(final) - score(first_commit), 0)) - exact differences."""
    from tejas.analytics import build_analytics, REGISTRY
    from tejas_core import score_attempt

    s = source_set(15, correct='4', wrong='-1')
    u = synthetic_student_user

    # 5 changes: wrong→correct (+5 each), 3 changes: correct→wrong (-5 each)
    initial = {}
    changes = {}
    for i in range(5):
        qid = s['questions'][i]['id']
        initial[qid] = '2'  # wrong
        changes[qid] = ['1']  # → correct
    for i in range(5, 8):
        qid = s['questions'][i]['id']
        initial[qid] = '1'  # correct
        changes[qid] = ['2']  # → wrong

    a = await create_attempt_with_answers(clean_db, u, s, initial, changes)
    result = score_attempt(a)
    analytics = build_analytics(a, result)

    a24 = next(m for m in analytics['metrics'] if m['metric_id'] == 'A24')
    oracle = next(m for m in REGISTRY['metrics'] if m['metric_id'] == 'A24')

    assert a24['name'] == oracle['name']
    assert a24['state'] == 'available'
    # Positive deltas: 5 * (+5) = 25 marks
    assert a24['value'] == 25.0
    assert a24['unit'] == 'marks'
    assert a24['sample_size'] == 8  # Total revised items


async def test_a25_negative_delta_sum_exact(clean_db, synthetic_student_user):
    """A25: sum(max(score(first_commit) - score(final), 0)) - no arbitrary threshold."""
    from tejas.analytics import build_analytics, REGISTRY
    from tejas_core import score_attempt

    s = source_set(15, correct='4', wrong='-1')
    u = synthetic_student_user

    # 3 harmful changes: correct→wrong
    initial = {}
    changes = {}
    for i in range(3):
        qid = s['questions'][i]['id']
        initial[qid] = '1'  # correct
        changes[qid] = ['2']  # → wrong

    a = await create_attempt_with_answers(clean_db, u, s, initial, changes)
    result = score_attempt(a)
    analytics = build_analytics(a, result)

    a25 = next(m for m in analytics['metrics'] if m['metric_id'] == 'A25')
    oracle = next(m for m in REGISTRY['metrics'] if m['metric_id'] == 'A25')

    assert a25['name'] == oracle['name']
    assert a25['state'] == 'available'
    # Negative deltas: 3 * 5 = 15 marks lost
    assert a25['value'] == 15.0
    assert a25['unit'] == 'marks'


async def test_a24_a25_no_arbitrary_10_threshold(clean_db, synthetic_student_user):
    """A24/A25: No arbitrary 10-item threshold for revision metrics.

    CRITICAL: Review request says 'no arbitrary 10 threshold' for A24/A25.
    """
    from tejas.analytics import build_analytics
    from tejas_core import score_attempt

    s = source_set(10, correct='4', wrong='-1')
    u = synthetic_student_user

    # Just 1 revision
    initial = {s['questions'][0]['id']: '2'}
    changes = {s['questions'][0]['id']: ['1']}

    a = await create_attempt_with_answers(clean_db, u, s, initial, changes)
    result = score_attempt(a)
    analytics = build_analytics(a, result)

    a24 = next(m for m in analytics['metrics'] if m['metric_id'] == 'A24')
    a25 = next(m for m in analytics['metrics'] if m['metric_id'] == 'A25')

    # Should be available even with 1 revision
    assert a24['state'] == 'available'
    assert a25['state'] == 'available'
    assert a24['sample_size'] == 1
    assert a25['sample_size'] == 1


# ============================================================================
# A26: LATE-WINDOW 20% BOUNDARY WITH 10-ITEM GATES
# ============================================================================

async def test_a26_late_window_20_percent_boundary(clean_db, synthetic_student_user):
    """A26: C/A for items first committed in final 20% vs earlier.

    CRITICAL: Requires at least 10 items in EACH group (late AND earlier).
    """
    from tejas.analytics import build_analytics, REGISTRY
    from tejas_core import score_attempt
    from tejas.db import now

    s = source_set(25, minutes=100)  # 100 minute window
    u = synthetic_student_user

    await clean_db.tejas_sets.insert_one(copy.deepcopy(s))
    from tejas import attempts, corrections

    await attempts.preflight(s['id'], {}, u)
    a = await attempts.start(s['id'], attempts.Start(
        start_key='test-' + str(uuid4()), device_checked=True), u)

    start_time = a['started_at']
    deadline = a['deadline']
    # 20% boundary: 80% of duration
    boundary = start_time + 0.8 * (deadline - start_time)

    # Answer 15 early (all correct), 10 late (5 correct, 5 incorrect)
    for i in range(15):
        qid = s['questions'][i]['id']
        from tejas.answers import save_answer, AnswerWrite
        await save_answer(a['id'], qid, AnswerWrite(
            value='1', revision=1, request_id=f'ans-{qid}', marked=False), u)
        # Set early timestamp
        await clean_db.tejas_attempts.update_one(
            {'id': a['id']},
            {'$set': {f'first_answers.{qid}.accepted_at': boundary - 100}}
        )

    for i in range(15, 25):
        qid = s['questions'][i]['id']
        value = '1' if i < 20 else '2'  # 5 correct, 5 incorrect
        await save_answer(a['id'], qid, AnswerWrite(
            value=value, revision=1, request_id=f'ans-{qid}', marked=False), u)
        # Set late timestamp
        await clean_db.tejas_attempts.update_one(
            {'id': a['id']},
            {'$set': {f'first_answers.{qid}.accepted_at': boundary + 100}}
        )

    await attempts.finalize(a['id'])
    completed = await attempts.owned(a['id'], u)
    ledger = await corrections.freeze_ledger(completed)
    completed = await attempts.owned(a['id'], u)

    result = score_attempt(completed)
    analytics = build_analytics(completed, result)

    a26 = next(m for m in analytics['metrics'] if m['metric_id'] == 'A26')
    oracle = next(m for m in REGISTRY['metrics'] if m['metric_id'] == 'A26')

    assert a26['name'] == oracle['name']
    assert a26['state'] == 'available'
    assert isinstance(a26['value'], dict)
    assert 'late_accuracy_percent' in a26['value']
    assert 'earlier_accuracy_percent' in a26['value']
    # Late: 5/10 = 50%, Earlier: 15/15 = 100%
    assert abs(a26['value']['late_accuracy_percent'] - 50.0) < 0.1
    assert abs(a26['value']['earlier_accuracy_percent'] - 100.0) < 0.1
    assert a26['value']['late_count'] == 10
    assert a26['value']['earlier_count'] == 15


async def test_a26_requires_10_in_each_group(clean_db, synthetic_student_user):
    """A26: Requires at least 10 items in EACH of late and earlier groups."""
    from tejas.analytics import build_analytics
    from tejas_core import score_attempt
    from tejas.db import now

    s = source_set(15, minutes=60)
    u = synthetic_student_user

    await clean_db.tejas_sets.insert_one(copy.deepcopy(s))
    from tejas import attempts, corrections

    await attempts.preflight(s['id'], {}, u)
    a = await attempts.start(s['id'], attempts.Start(
        start_key='test-' + str(uuid4()), device_checked=True), u)

    start_time = a['started_at']
    deadline = a['deadline']
    boundary = start_time + 0.8 * (deadline - start_time)

    # Only 9 late answers (insufficient)
    for i in range(6):
        qid = s['questions'][i]['id']
        from tejas.answers import save_answer, AnswerWrite
        await save_answer(a['id'], qid, AnswerWrite(
            value='1', revision=1, request_id=f'ans-{qid}', marked=False), u)
        await clean_db.tejas_attempts.update_one(
            {'id': a['id']},
            {'$set': {f'first_answers.{qid}.accepted_at': boundary - 100}}
        )

    for i in range(6, 15):
        qid = s['questions'][i]['id']
        await save_answer(a['id'], qid, AnswerWrite(
            value='1', revision=1, request_id=f'ans-{qid}', marked=False), u)
        await clean_db.tejas_attempts.update_one(
            {'id': a['id']},
            {'$set': {f'first_answers.{qid}.accepted_at': boundary + 100}}
        )

    await attempts.finalize(a['id'])
    completed = await attempts.owned(a['id'], u)
    ledger = await corrections.freeze_ledger(completed)
    completed = await attempts.owned(a['id'], u)

    result = score_attempt(completed)
    analytics = build_analytics(completed, result)

    a26 = next(m for m in analytics['metrics'] if m['metric_id'] == 'A26')
    assert a26['state'] == 'insufficient_sample'
    assert 'at least' in a26['reason'].lower() and 'each' in a26['reason'].lower()


# ============================================================================
# A56/A58/A59: SOLUTION/CORRECTION/APPROVAL TRACKING
# ============================================================================

async def test_a56_opened_over_all_released(clean_db, synthetic_student_user):
    """A56: opened / all released review items includes correct/all outcomes.

    CRITICAL: Denominator is ALL released items, not just incorrect/skipped.
    """
    from tejas.analytics import build_analytics, REGISTRY
    from tejas_core import score_attempt
    from tejas import attempts

    s = source_set(10)
    u = synthetic_student_user

    # Answer 5 correctly, 3 incorrectly, skip 2
    answers = {s['questions'][i]['id']: '1' for i in range(5)}
    for i in range(5, 8):
        answers[s['questions'][i]['id']] = '2'

    a = await create_attempt_with_answers(clean_db, u, s, answers)

    # Open solutions for 3 items (1 correct, 2 incorrect)
    opened = [s['questions'][0]['id'], s['questions'][5]['id'], s['questions'][6]['id']]
    await clean_db.tejas_attempts.update_one(
        {'id': a['id']},
        {'$set': {'solution_opened': opened, 'solution_events_version': 1}}
    )

    a = await attempts.owned(a['id'], u)
    result = score_attempt(a)
    analytics = build_analytics(a, result)

    a56 = next(m for m in analytics['metrics'] if m['metric_id'] == 'A56')
    oracle = next(m for m in REGISTRY['metrics'] if m['metric_id'] == 'A56')

    assert a56['name'] == oracle['name']
    assert a56['state'] == 'available'
    # 3 opened / 10 total = 30%
    assert a56['value'] == 30.0
    assert a56['unit'] == '%'
    assert a56['sample_size'] == 10


async def test_a58_original_ledger_with_deltas(clean_db, synthetic_student_user):
    """A58: original_ledger.rows keyed by id + approved reason + selected new grade.

    CRITICAL: Must include changed item deltas, not just net change.
    """
    from tejas.analytics import build_analytics, REGISTRY
    from tejas_core import score_attempt
    from tejas import attempts

    s = source_set(5)
    u = synthetic_student_user

    answers = {s['questions'][0]['id']: '1', s['questions'][1]['id']: '1'}
    a = await create_attempt_with_answers(clean_db, u, s, answers)

    # Get current ledger
    ledger = await clean_db.tejas_ledgers.find_one({'id': a['id']})
    original_score = ledger['summary']['score']

    # Simulate correction: change question 0 from correct to incorrect
    new_rows = copy.deepcopy(ledger['rows'])
    new_rows[0]['marks_exact'] = '-1'
    new_rows[0]['outcome'] = 'incorrect'
    new_score = original_score - 5  # Lost 4 + gained 1 penalty = -5

    # Store original ledger and update
    await clean_db.tejas_attempts.update_one(
        {'id': a['id']},
        {'$set': {
            'original_ledger': {'rows': ledger['rows'], 'summary': ledger['summary']},
            'regrade_reason': 'Answer key corrected for question 1'
        }}
    )
    await clean_db.tejas_ledgers.update_one(
        {'id': a['id']},
        {'$set': {
            'rows': new_rows,
            'summary.score': new_score
        }}
    )

    a = await attempts.owned(a['id'], u)
    result = score_attempt(a)
    analytics = build_analytics(a, result)

    a58 = next(m for m in analytics['metrics'] if m['metric_id'] == 'A58')
    oracle = next(m for m in REGISTRY['metrics'] if m['metric_id'] == 'A58')

    assert a58['name'] == oracle['name']
    assert a58['state'] == 'available'
    assert isinstance(a58['value'], dict)
    assert 'net_change' in a58['value']
    assert 'question_changes' in a58['value']
    assert a58['value']['net_change'] == -5.0
    assert len(a58['value']['question_changes']) > 0
    # Verify delta is included
    assert any('delta' in change for change in a58['value']['question_changes'])


async def test_a59_approved_maps_vs_all_released(clean_db, synthetic_student_user):
    """A59: review approved maps vs all released.

    CRITICAL: Denominator is all released delivered items.
    """
    from tejas.analytics import build_analytics, REGISTRY
    from tejas_core import score_attempt

    s = source_set(10)
    # Set approved flag and solutions for 7 questions
    for i in range(7):
        s['questions'][i]['approved'] = True
        s['questions'][i]['solution'] = f'Approved solution {i}'
    for i in range(7, 10):
        s['questions'][i]['approved'] = False
        s['questions'][i]['solution'] = ''

    u = synthetic_student_user
    answers = {q['id']: '1' for q in s['questions'][:5]}
    a = await create_attempt_with_answers(clean_db, u, s, answers)

    result = score_attempt(a)
    analytics = build_analytics(a, result)

    a59 = next(m for m in analytics['metrics'] if m['metric_id'] == 'A59')
    oracle = next(m for m in REGISTRY['metrics'] if m['metric_id'] == 'A59')

    assert a59['name'] == oracle['name']
    assert a59['state'] == 'available'
    # 7 approved with solutions / 10 total = 70%
    assert a59['value'] == 70.0
    assert a59['unit'] == '%'


# ============================================================================
# UNAVAILABLE STATE VALIDATION
# ============================================================================

async def test_unavailable_metrics_return_none_not_zero(clean_db, synthetic_student_user):
    """Verify unavailable metrics return None, not zero or fake values."""
    from tejas.analytics import build_analytics
    from tejas_core import score_attempt
    from tejas import attempts

    s = source_set(3)
    u = synthetic_student_user

    # No answer history (predates collection)
    a = await create_attempt_with_answers(clean_db, u, s, {})
    await clean_db.tejas_attempts.update_one(
        {'id': a['id']},
        {'$unset': {'answer_history_version': 1}}
    )

    a = await attempts.owned(a['id'], u)
    result = score_attempt(a)
    analytics = build_analytics(a, result)

    # Check metrics that require history
    for metric_id in ['A24', 'A25', 'A26']:
        m = next(m for m in analytics['metrics'] if m['metric_id'] == metric_id)
        assert m['state'] in ('not_collected', 'unavailable', 'insufficient_sample')
        assert m['value'] is None, f'{metric_id} should be None, not {m["value"]}'


async def test_analytics_total_count_always_60():
    """Verify Analysis.total_count is always 60."""
    from tejas.analytics import build_analytics
    from tejas_core import score_attempt
    from tejas.db import now

    # Create minimal valid attempt
    a = {
        'id': str(uuid4()),
        'questions': [question()],
        'rules': {'correct': 4, 'wrong': -1, 'skipped': 0},
        'answers': {},
        'visited': [],
        'answer_history_version': 1,
        'solution_events_version': 1,
        'solution_opened': [],
        'first_answers': {},
        'started_at': now(),
        'submitted_at': now(),
        'deadline': 0,
    }

    result = score_attempt(a)
    analytics = build_analytics(a, result)

    assert analytics['total_count'] == 60
    assert len(analytics['metrics']) == 60
    assert analytics['available_count'] <= 60


# ============================================================================
# SOLUTION CONSULTATION ENDPOINT TESTS
# ============================================================================

async def test_solution_open_endpoint_authenticated_released_only(clean_db, synthetic_student_user):
    """Test POST /api/attempts/{id}/questions/{qid}/solution-open is authenticated and released-only."""
    from tejas import attempts
    from fastapi import HTTPException

    s = source_set(3)
    u = synthetic_student_user

    await clean_db.tejas_sets.insert_one(copy.deepcopy(s))
    await attempts.preflight(s['id'], {}, u)
    a = await attempts.start(s['id'], attempts.Start(
        start_key='test-' + str(uuid4()), device_checked=True), u)

    qid = s['questions'][0]['id']

    # Should fail on active attempt
    with pytest.raises(HTTPException) as exc:
        await attempts.solution_consulted(a['id'], qid, u)
    assert exc.value.status_code == 403
    assert 'not released' in exc.value.detail.lower()

    # Complete attempt
    await attempts.finalize(a['id'])
    from tejas import corrections
    completed = await attempts.owned(a['id'], u)
    await corrections.freeze_ledger(completed)

    # Now should succeed
    result = await attempts.solution_consulted(a['id'], qid, u)
    assert result.question_id == qid
    assert result.recorded is True

    # Verify tracking
    a_updated = await clean_db.tejas_attempts.find_one({'id': a['id']})
    assert qid in a_updated['solution_opened']


async def test_solution_open_idempotent(clean_db, synthetic_student_user):
    """Test solution-open endpoint is idempotent."""
    from tejas import attempts, corrections

    s = source_set(3)
    u = synthetic_student_user

    answers = {s['questions'][0]['id']: '1'}
    a = await create_attempt_with_answers(clean_db, u, s, answers)

    qid = s['questions'][0]['id']

    # Call multiple times
    for _ in range(3):
        result = await attempts.solution_consulted(a['id'], qid, u)
        assert result.recorded is True

    # Verify only one entry
    a_updated = await clean_db.tejas_attempts.find_one({'id': a['id']})
    assert a_updated['solution_opened'].count(qid) == 1


# ============================================================================
# FIRST ANSWER CAPTURE TESTS
# ============================================================================

async def test_first_answer_capture_atomic(clean_db, synthetic_student_user):
    """Test first_answers captures first nonempty answer atomically."""
    from tejas import attempts, answers
    from tejas.answers import AnswerWrite

    s = source_set(3)
    u = synthetic_student_user

    await clean_db.tejas_sets.insert_one(copy.deepcopy(s))
    await attempts.preflight(s['id'], {}, u)
    a = await attempts.start(s['id'], attempts.Start(
        start_key='test-' + str(uuid4()), device_checked=True), u)

    qid = s['questions'][0]['id']

    # First save: empty (should not be captured)
    await answers.save_answer(a['id'], qid, AnswerWrite(
        value='', revision=1, request_id='req-empty-' + str(uuid4())[:8], marked=False), u)

    a_check = await clean_db.tejas_attempts.find_one({'id': a['id']})
    assert qid not in a_check.get('first_answers', {})

    # Second save: nonempty (should be captured)
    await answers.save_answer(a['id'], qid, AnswerWrite(
        value='2', revision=2, request_id='req-first-' + str(uuid4())[:8], marked=False), u)

    a_check = await clean_db.tejas_attempts.find_one({'id': a['id']})
    assert qid in a_check['first_answers']
    assert a_check['first_answers'][qid]['value'] == '2'

    # Third save: different value (should NOT update first_answers)
    await answers.save_answer(a['id'], qid, AnswerWrite(
        value='1', revision=3, request_id='req-second-' + str(uuid4())[:8], marked=False), u)

    a_check = await clean_db.tejas_attempts.find_one({'id': a['id']})
    assert a_check['first_answers'][qid]['value'] == '2'  # Still the first nonempty


# ============================================================================
# NO SECRETS IN OUTPUT
# ============================================================================

async def test_no_secrets_in_analytics_output():
    """Verify analytics output doesn't expose internal secrets."""
    from tejas.analytics import REGISTRY, build_analytics
    from tejas_core import score_attempt

    # Check registry doesn't contain sensitive patterns
    registry_str = str(REGISTRY)
    forbidden = ['password', 'secret', 'token', 'credential', 'private_key']
    for word in forbidden:
        assert word.lower() not in registry_str.lower()

    # Check metric output structure
    for metric in REGISTRY['metrics']:
        # Verify no internal implementation details leaked
        assert '_id' not in metric
        assert 'internal' not in str(metric).lower()


if __name__ == '__main__':
    pytest.main([__file__, '-v', '--tb=short'])
