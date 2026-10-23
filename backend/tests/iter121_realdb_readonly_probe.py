"""TEST-ONLY READ-ONLY probe (iteration 121) of the configured preview DB. Only find/count; no writes.
Checks: baseline counts, docs lacking `id` (would break ContentRecord), and whether the importer's inventory() would
skip or 409 against existing target IDs for the current owner principal.
"""
import os, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from dotenv import load_dotenv
load_dotenv(Path(__file__).resolve().parents[1] / '.env')
from pymongo import MongoClient
from tejas import jee_transfer as J

db = MongoClient(os.environ['MONGO_URL'])[os.environ['DB_NAME']]
print('counts', {c: db[c].count_documents({}) for c in ('tejas_sets', 'tejas_chapter_books', 'tejas_files', 'tejas_users', 'tejas_attempts', 'tejas_sessions')})
print('no-id docs', {c: db[c].count_documents({'id': {'$exists': False}}) for c in J.COLLECTIONS})
print('receipt exists', db.tejas_content_transfers.count_documents({}) if 'tejas_content_transfers' in db.list_collection_names() else 0)
owners = list(db.tejas_users.find({'role': 'owner'}, {'_id': 0, 'id': 1, 'email': 1}))
print('owners', owners)
data = J.load_bundle()
for o in owners:
    tgt = J.target_records(data, o)
    res = {}
    for n in J.COLLECTIONS:
        exp = {d['id']: J.digest(d) for d in tgt[n]}
        rows = list(db[n].find({'id': {'$in': list(exp)}}))
        same = sum(1 for r in rows if J.digest(J.content(r)) == exp[r['id']])
        res[n] = (len(rows), same)
    print('owner', o.get('email'), 'present/identical', res)
bad = 0
for n in J.COLLECTIONS:
    for r in db[n].find({}):
        try:
            J.content(r)
        except Exception as e:
            bad += 1
            if bad < 4:
                print('content() fails', n, r.get('_id'), type(e).__name__, str(e)[:150])
print('content() failures', bad)
