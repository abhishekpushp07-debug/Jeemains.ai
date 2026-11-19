# Iteration113: read-only DB check of deployment startup fixes (setup markers kept, link visit TTL removed, gang report unique index)
import asyncio, os, sys
from pathlib import Path
from dotenv import load_dotenv
from pymongo import AsyncMongoClient

load_dotenv(Path(__file__).resolve().parents[1] / ".env")


async def main():
    client = AsyncMongoClient(os.environ["MONGO_URL"])
    db = client[os.environ["DB_NAME"]]
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
    markers = await db.rf_meta.find({"_id": {"$regex": "^setup:"}}).to_list(100)
    print("setup markers:", [(m["_id"], m.get("done"), m.get("ts")) for m in markers])
    lv = await db.rf_link_visits.index_information()
    print("rf_link_visits indexes:", lv)
    gr = await db.rf_gang_reports.index_information()
    print("rf_gang_reports indexes:", gr)
    feed = await db.rf_feed.index_information()
    print("rf_feed index names:", list(feed))
    print("rf_link_visits count:", await db.rf_link_visits.count_documents({}))
    print("rf_gang_reports count:", await db.rf_gang_reports.count_documents({}))
    await client.close()


asyncio.run(main())
