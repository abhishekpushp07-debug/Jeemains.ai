import os, time, uuid
from datetime import datetime
from motor.motor_asyncio import AsyncIOMotorClient
from fastapi import HTTPException
from .runtime import DB_POOL, DB_WAIT_MS
from pymongo.write_concern import WriteConcern

client = AsyncIOMotorClient(
    os.environ["MONGO_URL"], maxPoolSize=DB_POOL, minPoolSize=0,
    maxConnecting=2, waitQueueTimeoutMS=DB_WAIT_MS,
    serverSelectionTimeoutMS=5000, connectTimeoutMS=5000, socketTimeoutMS=15000,
    tz_aware=True,
)
# A requested acknowledgement policy, NOT proof of replicated/multi-AZ durability.
# The preview is standalone; quorum/failover qualification remains a release gate.
db = client.get_database(os.environ["DB_NAME"], write_concern=WriteConcern(w="majority", j=True, wtimeout=5000))
users = db.tejas_users
sessions = db.tejas_sessions
sets = db.tejas_sets
attempts = db.tejas_attempts
files = db.tejas_files
jobs = db.tejas_jobs
audits = db.tejas_audits


def uid():
    return str(uuid.uuid4())


def now():
    return time.time()


def clean(v):
    if isinstance(v, dict):
        return {k: clean(x) for k, x in v.items() if k != "_id"}
    if isinstance(v, list):
        return [clean(x) for x in v]
    if isinstance(v, datetime):
        return v.isoformat()
    return v


async def get(coll, id):
    projection = {"_id": 0}
    if coll.name == "tejas_attempts":
        projection.update({"command_receipts": 0, "response_schema": 0})
    d = await coll.find_one({"id": id}, projection)
    if not d:
        raise HTTPException(404, "This item is unavailable or does not exist.")
    if coll.name == "tejas_attempts" and d.get("pack_id"):
        from .packs import hydrate

        d = await hydrate(d)
    if coll.name == "tejas_attempts" and d.get("status") == "completed":
        ledger = await db.tejas_ledgers.find_one({"id": id}, {"_id": 0})
        if ledger:
            d["ledger"] = ledger
    return d


async def audit(actor, action, resource, detail=""):
    await audits.insert_one(
        {
            "id": uid(),
            "actor": actor,
            "action": action,
            "resource": resource,
            "detail": detail[:2000],
            "at": now(),
        }
    )


async def indexes():
    for name in ('tejas_smart_imports', 'tejas_smart_papers', 'tejas_smart_questions',
                 'tejas_smart_keys', 'tejas_ai_solutions', 'tejas_ai_settings',
                 'tejas_ai_daily', 'tejas_ai_limits', 'tejas_cohorts', 'tejas_cohort_snapshots',
                 'tejas_cohort_entries'):
        await db[name].create_index('id', unique=True)
    await db.tejas_smart_imports.create_index('request_key', unique=True)
    await db.tejas_smart_imports.create_index([('owner_id', 1), ('created_at', -1)])
    await db.tejas_smart_papers.create_index([('import_id', 1), ('created_at', 1)])
    await db.tejas_smart_questions.create_index([('paper_id', 1), ('source_page', 1), ('original_number', 1)])
    await db.tejas_smart_questions.create_index([('import_id', 1), ('source_page', -1)])
    await db.tejas_ai_solutions.create_index([('auto_import_id', 1), ('state', 1)])
    await db.tejas_ai_limits.create_index('expires_at', expireAfterSeconds=0)
    await db.tejas_ai_daily.create_index('expires_at', expireAfterSeconds=0)
    await db.tejas_cohort_entries.create_index([('cohort_id', 1), ('user_id', 1)], unique=True)
    await db.tejas_cohort_entries.create_index([('cohort_id', 1), ('score', -1)])
    await attempts.create_index([('set_id', 1), ('version', 1), ('status', 1), ('mode', 1), ('cohort_indexed', 1), ('submitted_at', 1), ('id', 1)])
    await db.tejas_chapter_books.create_index('id', unique=True)
    await db.tejas_chapter_uploads.create_index('id', unique=True)
    await sets.create_index([('chapter_book_id',1),('chapter_number',1)])
    await db.tejas_reviews.create_index('id', unique=True)
    await db.tejas_reviews.create_index([('user_id',1),('attempt_id',1),('score_version',1)])
    await db.tejas_imports.create_index('id', unique=True)
    await db.tejas_imports.create_index([('created_at', -1)])
    await attempts.create_index([('set_id',1),('mode',1),('competition_ranked',1),('summary.score',-1)])
    await db.tejas_phone_profiles.create_index("id", unique=True)
    await db.tejas_phone_profiles.create_index("phone", unique=True)
    await db.tejas_phone_limits.create_index("expires_at", expireAfterSeconds=0)
    for c in [
        users,
        sessions,
        sets,
        attempts,
        files,
        jobs,
        audits,
        db.tejas_ledgers,
        db.tejas_score_versions,
    ]:
        await c.create_index("id", unique=True)
    await users.create_index("email", unique=True)
    await sessions.create_index("expires_at", expireAfterSeconds=0)
    await sets.create_index([("status", 1), ("exam", 1)])
    await attempts.create_index([("user_id", 1), ("started_at", -1)])
    await attempts.create_index([('user_id', 1), ('mode', 1), ('set_id', 1), ('started_at', -1), ('id', -1)], name='chapter_attempt_latest')
    await attempts.create_index([('user_id', 1), ('exam', 1), ('started_at', -1), ('id', -1)], name='exam_attempt_history')
    await attempts.create_index([("user_id", 1), ("start_key", 1)], unique=True)
    await attempts.create_index([("user_id", 1), ("start_request_keys", 1)], unique=True, partialFilterExpression={"start_request_keys": {"$exists": True}})
    await attempts.create_index(
        [("user_id", 1), ("set_id", 1), ("mode", 1)],
        unique=True,
        partialFilterExpression={"status": "active"},
    )
    await attempts.create_index([("status", 1), ("deadline", 1)])
    await sets.create_index(
        [("status", 1), ("audience", 1), ("exam", 1), ("created_at", -1)]
    )
    await db.tejas_preflight.create_index([("user_id", 1), ("set_id", 1)], unique=True)

    await jobs.create_index([("status", 1), ("lease_until", 1)])
    await audits.create_index([("resource", 1), ("at", -1)])
    await db.tejas_login_limits.create_index("expires_at", expireAfterSeconds=0)
    await db.tejas_score_versions.create_index(
        [("attempt_id", 1), ("user_id", 1), ("created_at", -1)]
    )
    await attempts.create_index([("set_id", 1), ("status", 1), ("version", 1)])
    await jobs.create_index([("set_id", 1), ("created_at", -1)])
    await files.create_index([("set_id", 1), ("created_at", -1)])

    await attempts.create_index([("status", 1), ("grading_status", 1), ("submitted_at", 1)])
    await jobs.create_index([("kind", 1), ("status", 1), ("next_run_at", 1), ("created_at", 1)])
