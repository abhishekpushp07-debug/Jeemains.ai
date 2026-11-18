"""Load-test accounts on the configured database: seed them before a staged load test, remove them (and all they wrote) after.
seed:   python tools/load_accounts.py seed +91600197 1500 [FIRST]  (prints the created_after stamp to use for remove)
remove: python tools/load_accounts.py remove +91600197 STAMP     (dry run first, then the real removal through qa_cleanup)
"""
import asyncio, sys, time
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from dotenv import load_dotenv  # noqa: E402
load_dotenv(Path(__file__).resolve().parents[1] / '.env')
from tejas.db import db, uid  # noqa: E402
from tejas.auth import hash_pin  # noqa: E402
from tejas.phone import PhoneProfile  # noqa: E402
from tejas.qa_cleanup import TestAccounts, remove_test_accounts  # noqa: E402

PIN = '4826'


def phone(prefix, i):
    return prefix + str(i).zfill(10 - (len(prefix) - 3))


async def seed(prefix, count, first=0):
    stamp = time.time()
    hashed = hash_pin(PIN)
    docs = []
    for i in range(first, first + count):
        pid = uid()
        docs.append(PhoneProfile.from_mongo({'_id': pid, 'id': pid, 'phone': phone(prefix, i), 'name': f'Load {i}', 'pin_hash': hashed,
                                             'created_at': stamp, 'consent_at': stamp, 'last_seen_at': stamp}).to_mongo())
    await db.tejas_phone_profiles.insert_many(docs, ordered=False)
    print('seeded', count, 'created_after', stamp - 1)


async def remove(prefix, created_after):
    who = {'id': 'load-test-cleanup'}
    dry = await remove_test_accounts(TestAccounts(prefix=prefix, created_after=created_after), u=who)
    print('dry run', dry)
    real = await remove_test_accounts(TestAccounts(prefix=prefix, created_after=created_after, dry_run=False, confirm='REMOVE TEST ACCOUNTS'), u=who)
    print('removed', real)


if __name__ == '__main__':
    what, prefix = sys.argv[1], sys.argv[2]
    asyncio.run(seed(prefix, int(sys.argv[3]), int(sys.argv[4]) if len(sys.argv) > 4 else 0) if what == 'seed' else remove(prefix, float(sys.argv[3])))
