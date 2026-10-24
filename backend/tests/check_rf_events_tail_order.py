# rf_events live channel: does a tailable cursor with filter {_id > last_id} drop later-inserted events
# whose client-generated ObjectId sorts lower (another server process, same second)? Uses a temp DB.
import asyncio
import os
import time

from bson import ObjectId
from motor.motor_asyncio import AsyncIOMotorClient
from pymongo import CursorType


async def main():
    c = AsyncIOMotorClient(os.environ["MONGO_URL"])
    db = c["TEST_rf_events_order_tmp"]
    await db.drop_collection("rf_events")
    await db.create_collection("rf_events", capped=True, size=1024 * 1024)
    now = int(time.time())
    hi = ObjectId(f"{now:08x}" + "ff" * 5 + "000001")  # "server B" own event: high random part
    lo = ObjectId(f"{now:08x}" + "00" * 5 + "000001")  # "server A" event, same second, lower random part
    await db.rf_events.insert_one({"_id": hi, "did": "own", "node": "B"})
    last_id = hi
    got = []

    async def tail():
        cur = db.rf_events.find({"_id": {"$gt": last_id}}, cursor_type=CursorType.TAILABLE_AWAIT).max_await_time_ms(300)
        end = time.time() + 3
        while cur.alive and time.time() < end:
            async for ev in cur:
                got.append(ev["did"])
            await asyncio.sleep(0.05)

    t = asyncio.create_task(tail())
    await asyncio.sleep(0.5)
    await db.rf_events.insert_one({"_id": lo, "did": "from-A-same-second", "node": "A"})
    await db.rf_events.insert_one({"did": "from-A-later", "node": "A"})
    await t
    print("received:", got)
    print("DROPPED same-second lower-_id event" if "from-A-same-second" not in got else "OK no drop")
    await c.drop_database("TEST_rf_events_order_tmp")


asyncio.run(main())
