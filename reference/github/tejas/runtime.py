"""Application budgets only: not a claim of provisioned fleet capacity."""
import os


def budget(name, default, minimum, maximum):
    raw = os.environ.get(name, str(default))
    try:
        value = int(raw)
    except ValueError as exc:
        raise RuntimeError(f"{name} must be an integer") from exc
    if not minimum <= value <= maximum:
        raise RuntimeError(f"{name} must be between {minimum} and {maximum}")
    return value


DB_POOL = budget('TEJAS_DB_POOL_SIZE', 32, 4, 128)
DB_WAIT_MS = budget('TEJAS_DB_WAIT_MS', 2000, 100, 10000)
MAX_ANSWER_COMMANDS = budget('TEJAS_MAX_ANSWER_COMMANDS', 10000, 1000, 12000)
JOB_ATTEMPTS = budget('TEJAS_JOB_ATTEMPTS', 3, 1, 5)
JOB_LEASE_SECONDS = budget('TEJAS_JOB_LEASE_SECONDS', 900, 60, 3600)
INLINE_JOBS = os.environ.get('TEJAS_INLINE_JOBS', 'true').lower() == 'true'
LANE_LIMITS = {
    'grade': budget('TEJAS_GRADE_CONCURRENCY', 2, 1, 8),
    'report': budget('TEJAS_REPORT_CONCURRENCY', 1, 1, 4),
    'extract': budget('TEJAS_EXTRACT_CONCURRENCY', 1, 1, 2),
    'regrade': budget('TEJAS_REGRADE_CONCURRENCY', 1, 1, 2),
    'ai_solution': budget('TEJAS_AI_SOLUTION_CONCURRENCY', 1, 1, 2),
    'smart_prepare': budget('TEJAS_SMART_PREPARE_CONCURRENCY', 1, 1, 1),
    'smart_page': budget('TEJAS_SMART_PAGE_CONCURRENCY', 1, 1, 1),
    'cohort': budget('TEJAS_COHORT_CONCURRENCY', 1, 1, 2),
}
