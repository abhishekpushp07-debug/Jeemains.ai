"""This process's one MongoDB connection, and the small helpers every module shares.

Imported first by server.py, so backend/.env is loaded before any other module reads its settings."""
import os
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Annotated, Optional

from bson import ObjectId
from dotenv import load_dotenv
from pydantic import BaseModel, BeforeValidator, ConfigDict, Field
from pymongo import AsyncMongoClient, ReturnDocument
from pymongo.asynchronous.collection import AsyncCollection
from pymongo.errors import DuplicateKeyError

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')


class Collections:
    """`db.<name>` makes a new collection object on every access in PyMongo; the busiest paths do that thousands of
    times a second, so each collection object is made once and reused. Everything else goes straight to the database."""
    def __init__(self, database):
        self._db = database

    def __getattr__(self, name):
        value = getattr(self._db, name)
        if isinstance(value, AsyncCollection):
            self.__dict__[name] = value
        return value

    def __getitem__(self, name):
        return self._db[name]


# Native PyMongo async driver: no thread pool per query (about half the CPU of Motor per database call).
# 40 connections per process are plenty for async calls of 1-2 ms, and keep many servers x processes inside the
# database's connection limit (a full pool on every process of a big fleet would be refused by the database).
client = AsyncMongoClient(os.environ['MONGO_URL'], maxPoolSize=int(os.environ.get('MONGO_MAX_POOL', '40')))
db = Collections(client[os.environ['DB_NAME']])


# ---------- Mongo model helpers ----------
PyObjectId = Annotated[str, BeforeValidator(lambda v: str(v) if isinstance(v, ObjectId) else v)]


class BaseDocument(BaseModel):
    model_config = ConfigDict(populate_by_name=True, extra="ignore")
    mongo_id: Optional[PyObjectId] = Field(default=None, alias="_id", exclude=True)

    def to_mongo(self) -> dict:
        return self.model_dump(exclude={"mongo_id"})

    @classmethod
    def from_mongo(cls, doc: dict):
        return cls.model_validate(doc) if doc else None


def now_iso():
    return datetime.now(timezone.utc).isoformat()


def to_field(name: str) -> str:
    """A cookie or file name as a Mongo field name ('.' and '$' cannot be used in an update path)."""
    return name.replace("%", "%25").replace(".", "%2E").replace("$", "%24")


def from_field(field: str) -> str:
    return field.replace("%24", "$").replace("%2E", ".").replace("%25", "%")


async def take_turn(db, name: str, seconds: float) -> bool:
    """One server process at a time does `name`; a turn left by a process that stopped runs out after `seconds`."""
    now = time.time()
    try:
        return bool(await db.rf_meta.find_one_and_update({"_id": "turn:" + name, "until": {"$lt": now}}, {"$set": {"until": now + seconds}},
                                                         upsert=True, return_document=ReturnDocument.AFTER))
    except DuplicateKeyError:
        return False
