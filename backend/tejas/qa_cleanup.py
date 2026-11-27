"""Owner-only removal of load-test / QA student accounts made through public sign-up, with everything they wrote."""
import re, uuid
from typing import Literal
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, ConfigDict, Field
from .auth import owner, forget_student
from .db import db, attempts, audit

router = APIRouter(prefix='/api/admin/qa', tags=['QA test accounts'])
BY_USER = ('tejas_ledgers', 'tejas_saved_tests', 'tejas_question_reports', 'tejas_reviews', 'tejas_score_versions',
           'tejas_preflight', 'tejas_sessions', 'tejas_jobs', 'tejas_solution_requests',
           'tejas_attempt_timeline', 'tejas_analysis', 'tejas_learnings', 'tejas_events', 'tejas_invite_contacts',
           'tejas_choice_papers', 'tejas_choice_days')
LIMIT = 20000


class TestAccounts(BaseModel):
    model_config = ConfigDict(extra='forbid', strict=True)
    prefix: str = Field(pattern=r'^\+91[6-9][0-9]{5,8}$')
    created_after: float = Field(gt=1.7e9, allow_inf_nan=False)
    dry_run: bool = True
    confirm: Literal['', 'REMOVE TEST ACCOUNTS'] = ''


@router.post('/test-accounts/remove')
async def remove_test_accounts(body: TestAccounts, u=Depends(owner)):
    """Only numbers that start with the given test prefix AND signed up after the given time are touched."""
    if not body.dry_run and body.confirm != 'REMOVE TEST ACCOUNTS':
        raise HTTPException(422, 'Type REMOVE TEST ACCOUNTS to remove them.')
    match = {'phone': {'$regex': '^' + re.escape(body.prefix)}, 'created_at': {'$gte': body.created_after}}
    ids = await db.tejas_phone_profiles.distinct('id', match)
    if len(ids) > LIMIT:
        raise HTTPException(409, f'More than {LIMIT} accounts match. Use a longer prefix.')
    counts = {'accounts': len(ids), 'attempts': await attempts.count_documents({'user_id': {'$in': ids}}) if ids else 0}
    if body.dry_run or not ids:
        return {'dry_run': body.dry_run, 'removed': {} if body.dry_run else counts, 'would_remove': counts}
    cohorts = await db.tejas_cohort_entries.distinct('cohort_id', {'user_id': {'$in': ids}})
    removed = {'cohort_entries': (await db.tejas_cohort_entries.delete_many({'user_id': {'$in': ids}})).deleted_count}
    classes = await db.tejas_class_entries.distinct('cohort_id', {'user_id': {'$in': ids}})
    removed['class_entries'] = (await db.tejas_class_entries.delete_many({'user_id': {'$in': ids}})).deleted_count
    if classes:
        await db.tejas_class_stats.update_many({'_id': {'$in': classes}}, {'$set': {'dirty': True, 'generation': str(uuid.uuid4())}})
    for name in BY_USER:
        removed[name.removeprefix('tejas_')] = (await db[name].delete_many({'user_id': {'$in': ids}})).deleted_count
    removed['attempts'] = (await attempts.delete_many({'user_id': {'$in': ids}})).deleted_count
    removed['accounts'] = (await db.tejas_phone_profiles.delete_many({'id': {'$in': ids}, **match})).deleted_count
    if cohorts:
        # Peer statistics rebuild without the removed test attempts on their next read.
        await db.tejas_cohorts.update_many({'id': {'$in': cohorts}}, {'$set': {'dirty': True, 'generation': str(uuid.uuid4())}})
    for i in ids:
        forget_student(user_id=i)
    await audit(u['id'], 'QA test accounts removed', body.prefix, f"{removed['accounts']} accounts, {removed['attempts']} attempts, {len(cohorts)} peer groups marked for rebuild")
    return {'dry_run': False, 'removed': removed, 'would_remove': counts}
