# Helper for forgot-PIN tests: inspect/cleanup pin_resets rows for FAKE numbers only (by exact sha256 phone key)
import hashlib
import os
import sys
from pymongo import MongoClient
from dotenv import load_dotenv

load_dotenv('/app/backend/.env')
db = MongoClient(os.environ['MONGO_URL'])[os.environ['DB_NAME']]


def key(v: str) -> str:
    return hashlib.sha256(v.encode()).hexdigest()


if __name__ == '__main__':
    cmd = sys.argv[1]
    if cmd == 'stats':
        print('total rows', db.pin_resets.count_documents({}))
        for r in db.pin_resets.find({}, {'_id': 0, 'phone': 0}).sort('at', -1).limit(15):
            print(r.get('ip', '')[:10], r['at'], r['result'])
    elif cmd == 'show':
        for n in sys.argv[2:]:
            print(n, [(r.get('ip', '')[:12], r['result']) for r in db.pin_resets.find({'phone': key(n[-10:])}, {'_id': 0})])
    elif cmd == 'ipcheck':
        print('rows with spoofed ip', sys.argv[2], db.pin_resets.count_documents({'ip': key(sys.argv[2])}))
    elif cmd == 'cleanup':
        for n in sys.argv[2:]:
            assert n.startswith('99999'), 'only fake numbers'
            print(n, 'deleted', db.pin_resets.delete_many({'phone': key(n[-10:])}).deleted_count)
