"""Compare live preservation hashes against /app/test_reports/automatic_ai_pause_baseline.json (read-only)."""
import asyncio, hashlib, json, os, sys
from pathlib import Path
from dotenv import load_dotenv
load_dotenv(Path(__file__).resolve().parents[1] / '.env')
from motor.motor_asyncio import AsyncIOMotorClient

BASELINE = Path('/app/test_reports/automatic_ai_pause_baseline.json')
QUERIES = {'tejas_sets': {}, 'tejas_attempts': {}, 'tejas_files': {}, 'tejas_question_solutions': {'state': 'ready'}}


async def snapshot():
    client = AsyncIOMotorClient(os.environ['MONGO_URL'])
    db = client[os.environ['DB_NAME']]
    out = {}
    for name, q in QUERIES.items():
        h, n = hashlib.sha256(), 0
        async for d in db[name].find(q, {'_id': 0}).sort('id', 1):
            h.update(json.dumps(d, sort_keys=True, default=str, separators=(',', ':')).encode())
            n += 1
        out[name] = {'count': n, 'sha256': h.hexdigest()}
    out['states'] = {r['_id']: r['count'] async for r in db.tejas_question_solutions.aggregate([{'$group': {'_id': '$state', 'count': {'$sum': 1}}}])}
    out['legacy_ai_states'] = {str(r['_id']): r['count'] async for r in db.tejas_ai_solutions.aggregate([{'$group': {'_id': '$state', 'count': {'$sum': 1}}}])}
    out['ai_jobs'] = {str(r['_id']): r['count'] async for r in db.tejas_jobs.aggregate([{'$match': {'kind': 'ai_solution'}}, {'$group': {'_id': '$status', 'count': {'$sum': 1}}}])}
    client.close()
    return out


def compare(snap):
    base = json.loads(BASELINE.read_text())
    return {k: snap[k] == base[k] for k in QUERIES}


if __name__ == '__main__':
    s = asyncio.run(snapshot())
    print(json.dumps(s, indent=1))
    print('MATCH', compare(s))
