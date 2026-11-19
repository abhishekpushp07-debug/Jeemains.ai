# Iteration113: re-run setup_database() (what a fresh code version does at startup) twice, and replay the TTL-retire logic on a scratch TEST collection
import asyncio, os, sys, time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import server  # noqa: E402


async def ttl_retire(coll):
    await coll.create_index([("cid", 1), ("key", 1)], unique=True)
    if (await coll.index_information()).get("ts_1", {}).get("expireAfterSeconds") is not None:
        await coll.drop_index("ts_1")
    await coll.create_index("ts")


async def main():
    db = server.db
    scratch = db["TEST_iter113_link_visits_scratch"]
    try:
        await scratch.create_index("ts", expireAfterSeconds=30 * 86400)  # the old TTL shape
        await scratch.insert_one({"cid": "TEST_c", "key": "TEST_k", "ts": time.time()})
        for i in range(2):
            await ttl_retire(scratch)
            ix = await scratch.index_information()
            print(f"scratch run {i+1}: ts_1={ix.get('ts_1')}, docs={await scratch.count_documents({})}")
            assert "expireAfterSeconds" not in ix["ts_1"]
    finally:
        await scratch.drop()  # scratch collection created by this test only
    before = await db.rf_meta.count_documents({"_id": {"$regex": "^setup:"}})
    for i in range(2):
        t = time.time()
        await server.setup_database()
        print(f"setup_database run {i+1} OK in {time.time()-t:.1f}s")
    lv = await db.rf_link_visits.index_information()
    print("rf_link_visits ts_1:", lv.get("ts_1"), "cid_1_key_1 unique:", lv.get("cid_1_key_1", {}).get("unique"))
    print("gang_reports unique:", (await db.rf_gang_reports.index_information()).get("gang_id_1_uid_1"))
    after = await db.rf_meta.count_documents({"_id": {"$regex": "^setup:"}})
    print("setup markers before/after:", before, after)


asyncio.run(main())
