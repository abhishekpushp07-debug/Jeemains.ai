# Iteration113: duplicate rows block a unique index -> the error is an OperationFailure (what setup_database catches); rows are kept
import asyncio, os
from pathlib import Path
from dotenv import load_dotenv
from pymongo import AsyncMongoClient
from pymongo.errors import OperationFailure

load_dotenv(Path(__file__).resolve().parents[1] / ".env")


async def main():
    client = AsyncMongoClient(os.environ["MONGO_URL"])
    coll = client[os.environ["DB_NAME"]]["TEST_iter113_gang_reports_scratch"]
    try:
        await coll.insert_many([{"gang_id": "TEST_g", "uid": "TEST_u"}, {"gang_id": "TEST_g", "uid": "TEST_u"}])
        try:
            await coll.create_index([("gang_id", 1), ("uid", 1)], unique=True)
            print("UNEXPECTED: index created despite duplicates")
        except OperationFailure as e:
            print("caught OperationFailure:", type(e).__name__, e.code)
        print("rows kept:", await coll.count_documents({}))
    finally:
        await coll.drop()
        await client.close()


asyncio.run(main())
