import json
import os

from dotenv import load_dotenv
from pymongo import MongoClient


load_dotenv('/app/backend/.env')
MONGO_URL = (os.environ.get('MONGO_URL') or '').strip().strip('"')
DB_NAME = (os.environ.get('DB_NAME') or '').strip().strip('"')


def cleanup_uid(db, uid: str) -> None:
    db.rf_access.delete_many({'uid': uid})
    db.rf_sessions.delete_many({'user_id': uid})
    db.rf_duels.delete_many({'players.uid': uid})
    db.rf_profiles.delete_many({'uid': uid})
    db.rf_awards.delete_many({'uid': uid})
    db.rf_learning_events.delete_many({'uid': uid})


def main() -> None:
    if not os.path.exists('/tmp/iter43_ui_fixture.json'):
        print('{"ok": true, "note": "no iter43 fixture file"}')
        return
    fixture = json.loads(open('/tmp/iter43_ui_fixture.json', 'r', encoding='utf-8').read())
    uids = [fixture.get('uid_a'), fixture.get('uid_b'), fixture.get('uid_c')]
    client = MongoClient(MONGO_URL)
    db = client[DB_NAME]
    try:
        for uid in uids:
            if isinstance(uid, str) and uid:
                cleanup_uid(db, uid)
        print(json.dumps({'ok': True, 'cleaned_uids': [u for u in uids if u]}))
    finally:
        client.close()


if __name__ == '__main__':
    main()
