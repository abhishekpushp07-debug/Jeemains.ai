"""TEST-ONLY read-only snapshot of customer DB counts (iteration 118). Usage: python iter118_realdb_snapshot.py [save|compare]"""
import json, os, sys
from pathlib import Path
from dotenv import load_dotenv
from pymongo import MongoClient

load_dotenv(Path(__file__).resolve().parents[1] / '.env')
DB = MongoClient(os.environ['MONGO_URL'])[os.environ['DB_NAME']]
OUT = '/tmp/iter118_realdb_snapshot.json'
COLLS = ['tejas_sets', 'tejas_questions', 'tejas_attempts', 'tejas_sessions', 'users', 'tejas_users',
         'tejas_phone_profiles', 'tejas_login_limits', 'tejas_phone_limits']


def snap():
    names = set(DB.list_collection_names())
    out = {c: DB[c].estimated_document_count() for c in COLLS if c in names}
    out['_session_ids_hash'] = hash(tuple(sorted(str(d.get('id')) for d in DB[[c for c in names if 'session' in c][0]].find({}, {'id': 1})))) if any('session' in c for c in names) else None
    out['_collections_with_session'] = sorted(c for c in names if 'session' in c or 'user' in c or 'limit' in c or 'phone' in c)
    for c in out['_collections_with_session']:
        out['count_' + c] = DB[c].estimated_document_count()
    return out


if __name__ == '__main__':
    s = snap()
    if sys.argv[1:] == ['compare']:
        old = json.load(open(OUT))
        s.pop('_session_ids_hash'); old.pop('_session_ids_hash')
        print('SAME' if s == old else 'DIFF', json.dumps({k: (old.get(k), s.get(k)) for k in set(s) | set(old) if old.get(k) != s.get(k)}))
    else:
        json.dump(s, open(OUT, 'w')); print(json.dumps(s))
