import json
import os
import hashlib

from dotenv import load_dotenv
from pymongo import MongoClient

load_dotenv('/app/backend/.env')

MONGO_URL = os.environ['MONGO_URL'].strip().strip('"')
DB_NAME = os.environ['DB_NAME'].strip().strip('"')


def h(obj):
    return hashlib.sha256(json.dumps(obj, sort_keys=True, default=str).encode()).hexdigest()


FIELDS = ('uid', 'coins', 'owned', 'equipped', 'avatar', 'freezes')


def main():
    report = json.loads(open('/app/backend/rapidfire/portrait_cleanup_report.json', 'r', encoding='utf-8').read())
    before = report['protected_after']
    client = MongoClient(MONGO_URL)
    db = client[DB_NAME]
    try:
        prof_docs = list(db.rf_profiles.find({}, {'_id': 0}).sort('uid', 1))
        profiles = len(prof_docs)
        coins_sum = sum(int(p.get('coins') or 0) for p in prof_docs)
        wallet_ownership = h([{k: p[k] for k in FIELDS if k in p} for p in prof_docs])
        neet_profiles = [{p['uid']: (p.get('exam_stats', {}) or {}).get('NEET')} for p in prof_docs]
        guard = {
            'profiles': profiles,
            'coins_sum': coins_sum,
            'wallet_ownership': wallet_ownership,
            'neet_profile_stats': h(neet_profiles),
        }
        print(json.dumps({'expected': {'profiles': before['profiles'], 'coins_sum': before['coins_sum'], 'wallet_ownership': before['wallet_ownership'], 'neet_profile_stats': before['neet_profile_stats']}, 'actual': guard}))
    finally:
        client.close()


if __name__ == '__main__':
    main()
