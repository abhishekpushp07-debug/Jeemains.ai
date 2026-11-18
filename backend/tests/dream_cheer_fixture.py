"""QA fixture for the "Dream Unlocked" celebration on the approved QA learner (local rf_dreams only, never the website).
seed: saves the account's dream document to /tmp (0600), then adds one TEST full mock (JEE, 207/300, taken now) that
crosses three of its JEE dreams (205, 204, 204) and clears the celebrated list, so Home plays the show once.
cleanup: puts the saved document back exactly (the TEST mock and any celebrated marks go).
Run: python backend/tests/dream_cheer_fixture.py seed|cleanup"""
import asyncio
import json
import os
import sys
import time
from pathlib import Path

from dotenv import load_dotenv
from motor.motor_asyncio import AsyncIOMotorClient

load_dotenv(Path(__file__).parent.parent / ".env")
UID = "75d720a0-215f-4b63-a98d-d4a072249cff"  # QA learner 7004186276
BACKUP = Path("/tmp/dream_cheer_backup.json")
MOCK = {"id": "TEST-cheer-mock", "exam": "jee", "score": 207.0, "max": 300.0, "raw": 207.0, "rawMax": 300.0, "title": "TEST Dream cheer mock"}


async def main(cmd):
    db = AsyncIOMotorClient(os.environ["MONGO_URL"])[os.environ["DB_NAME"]]
    if cmd == "seed":
        doc = await db.rf_dreams.find_one({"uid": UID}, {"_id": 0})
        if not BACKUP.exists():
            BACKUP.write_text(json.dumps(doc))
            BACKUP.chmod(0o600)
        mock = {**MOCK, "at": time.time() * 1000}
        await db.rf_dreams.update_one({"uid": UID}, {"$pull": {"mocks": {"id": MOCK["id"]}}, "$unset": {"cheered": ""}})
        await db.rf_dreams.update_one({"uid": UID}, {"$push": {"mocks": {"$each": [mock], "$sort": {"at": -1}, "$slice": 30}}})
        print("seeded: TEST mock 207/300 now; celebrated list cleared")
    elif cmd == "cleanup":
        if not BACKUP.exists():
            print("nothing to restore")
            return
        doc = json.loads(BACKUP.read_text())
        if doc:
            await db.rf_dreams.replace_one({"uid": UID}, doc)
        else:  # the account had no dream document before seeding
            await db.rf_dreams.delete_one({"uid": UID})
        BACKUP.unlink()
        print("restored original dream document")


asyncio.run(main(sys.argv[1] if len(sys.argv) > 1 else ""))
