"""Iteration 66 helper: put tonight's Cup Night start N seconds from now (doc must exist). Usage: python _iter66_night_at.py 600"""
import asyncio
import os
import sys
import time

from dotenv import load_dotenv
from motor.motor_asyncio import AsyncIOMotorClient

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
load_dotenv(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".env"))
from cups import night_of  # noqa: E402


async def main(sec):
    db = AsyncIOMotorClient(os.environ["MONGO_URL"])[os.environ["DB_NAME"]]
    r = await db.rf_cup_nights.update_one({"_id": night_of(time.time())[0], "status": "open"}, {"$set": {"start_ts": time.time() + sec}})
    print("moved", r.modified_count)


asyncio.run(main(float(sys.argv[1])))
