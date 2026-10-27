import hashlib
import json
import os
import uuid
from datetime import datetime, timedelta, timezone

from dotenv import load_dotenv
from pymongo import MongoClient


load_dotenv('/app/backend/.env')

MONGO_URL = (os.environ.get('MONGO_URL') or '').strip().strip('"')
DB_NAME = (os.environ.get('DB_NAME') or '').strip().strip('"')


def digest(token: str) -> str:
    return hashlib.sha256(token.encode('utf-8')).hexdigest()


def ensure_profile(db, uid: str, name: str, coins: int) -> None:
    db.rf_profiles.update_one(
        {'uid': uid},
        {
            '$set': {
                'uid': uid,
                'name': name,
                'coins': coins,
                'owned': [],
                'equipped': {'frame': None, 'entry': None, 'theme': None},
                'avatar': 'av_astronaut',
                'xp': 0,
                'level': 1,
                'level_floor': 0,
                'next_level_xp': 100,
                'streak': 0,
                'best_streak': 0,
                'played_today': False,
                'sessions': 0,
                'duels': 0,
                'wins': 0,
                'cards_correct': 0,
                'badges': [],
                'freezes': 0,
                'quests': [],
            }
        },
        upsert=True,
    )


def insert_grant(db, uid: str, token: str) -> None:
    db.rf_access.delete_many({'uid': uid})
    db.rf_access.insert_one(
        {
            'digest': digest(token),
            'uid': uid,
            'sid': '',
            'expires_at': datetime.now(timezone.utc) + timedelta(minutes=30),
        }
    )


def cleanup_prefix(db, prefix: str) -> None:
    rx = {'$regex': f'^{prefix}'}
    db.rf_access.delete_many({'uid': rx})
    db.rf_sessions.delete_many({'user_id': rx})
    db.rf_duels.delete_many({'players.uid': rx})
    db.rf_profiles.delete_many({'uid': rx})
    db.rf_awards.delete_many({'uid': rx})
    db.rf_learning_events.delete_many({'uid': rx})


def main() -> None:
    if not MONGO_URL or not DB_NAME:
        raise RuntimeError('Missing MONGO_URL/DB_NAME')
    client = MongoClient(MONGO_URL)
    db = client[DB_NAME]
    try:
        # Explicit cleanup of known iter42 fixture UIDs from prior run note.
        old_uids = ['TEST-RF-portrait-uiA-7ba2ac03', 'TEST-RF-portrait-uiB-7ba2ac03']
        for uid in old_uids:
            db.rf_access.delete_many({'uid': uid})
            db.rf_sessions.delete_many({'user_id': uid})
            db.rf_duels.delete_many({'players.uid': uid})
            db.rf_profiles.delete_many({'uid': uid})
            db.rf_awards.delete_many({'uid': uid})
            db.rf_learning_events.delete_many({'uid': uid})

        run = uuid.uuid4().hex[:8]
        uid_a = f'TEST-RF-portrait-uiA-{run}'
        uid_b = f'TEST-RF-portrait-uiB-{run}'
        uid_c = f'TEST-RF-portrait-uiC-{run}'
        cleanup_prefix(db, f'TEST-RF-portrait-uiA-{run}')
        cleanup_prefix(db, f'TEST-RF-portrait-uiB-{run}')
        cleanup_prefix(db, f'TEST-RF-portrait-uiC-{run}')

        token_a = 'uiA-' + uuid.uuid4().hex + uuid.uuid4().hex
        token_b = 'uiB-' + uuid.uuid4().hex + uuid.uuid4().hex
        token_c = 'uiC-' + uuid.uuid4().hex + uuid.uuid4().hex

        ensure_profile(db, uid_a, 'TEST-RF-portrait-uiA', 250)
        ensure_profile(db, uid_b, 'TEST-RF-portrait-uiB', 250)
        ensure_profile(db, uid_c, 'TEST-RF-portrait-uiC', 1000)
        insert_grant(db, uid_a, token_a)
        insert_grant(db, uid_b, token_b)
        insert_grant(db, uid_c, token_c)

        fixture = {'run': run, 'uid_a': uid_a, 'token_a': token_a, 'uid_b': uid_b, 'token_b': token_b, 'uid_c': uid_c, 'token_c': token_c}
        with open('/tmp/iter43_ui_fixture.json', 'w', encoding='utf-8') as f:
            json.dump(fixture, f)
        print(json.dumps({'ok': True, 'fixture': fixture}))
    finally:
        client.close()


if __name__ == '__main__':
    main()
