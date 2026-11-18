"""Dream colleges (up to 5 per exam) and recent full-mock scores, kept with the student's account: every phone and
the browser show the same list. A phone sends its list together with the account list it was edited from, so a
change made on one device never wipes one made on another (or the account's own dreams)."""
import time
from typing import Annotated, List, Literal, Optional

from fastapi import APIRouter, Header, HTTPException
from pydantic import BaseModel, ConfigDict, Field
from pymongo.errors import DuplicateKeyError

DreamExam = Literal["jee", "bitsat", "comedk"]
MAX_DREAMS, MAX_MOCKS = 5, 30


class Dream(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(min_length=1, max_length=80)
    exam: DreamExam
    college: str = Field(max_length=160)
    branch: str = Field(max_length=200)
    need: float = Field(ge=-100, le=400)
    range: Optional[List[float]] = Field(default=None, min_length=2, max_length=2)
    note: str = Field(default="", max_length=200)
    at: float


class Mock(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(min_length=1, max_length=64)
    exam: DreamExam
    score: float
    max: float = Field(gt=0)
    raw: float
    rawMax: float = Field(gt=0)
    title: str = Field(default="Mock", max_length=200)
    at: float


class DreamsIn(BaseModel):
    model_config = ConfigDict(extra="forbid")
    dreams: List[Dream] = Field(max_length=MAX_DREAMS * 3)
    # ids of the account's list the phone made its changes on ([] = the phone had not seen the account's list yet,
    # or an older app build: then its dreams are only added, never removed)
    base: List[str] = Field(default_factory=list, max_length=MAX_DREAMS * 3)


def merge(current: list, base: List[str], mine: list) -> list:
    """The phone's changes applied to the account's current list: dreams it removed (in `base`, not in `mine`) go,
    dreams it added (not in `base`) join while that exam has a free slot, dreams added elsewhere stay."""
    had, here = set(base), {d["id"]: d for d in mine}
    out = [here.get(d["id"], d) for d in current if d["id"] not in had or d["id"] in here]
    for d in mine:
        if d["id"] not in had and all(x["id"] != d["id"] for x in out) and sum(x["exam"] == d["exam"] for x in out) < MAX_DREAMS:
            out.append(d)
    return out


class MocksIn(BaseModel):
    model_config = ConfigDict(extra="forbid")
    mocks: List[Mock] = Field(min_length=1, max_length=MAX_MOCKS)


class CheeredIn(BaseModel):
    model_config = ConfigDict(extra="forbid")
    ids: List[Annotated[str, Field(min_length=1, max_length=80)]] = Field(min_length=1, max_length=MAX_DREAMS * 3)


def make_router(db, rf_user):
    r = APIRouter(prefix="/rf/dream")

    @r.get("")
    async def read(x_rf_user: Optional[str] = Header(None)):
        uid = rf_user(x_rf_user)
        doc = await db.rf_dreams.find_one({"uid": uid}, {"_id": 0, "dreams": 1, "mocks": 1, "cheered": 1}) or {}
        return {"dreams": doc.get("dreams", []), "mocks": doc.get("mocks", []), "cheered": doc.get("cheered", [])}

    @r.put("/dreams")
    async def save_dreams(data: DreamsIn, x_rf_user: Optional[str] = Header(None)):
        """The phone's list after its changes, merged into the account's current list; returns the account's list."""
        uid = rf_user(x_rf_user)
        ids = [d.id for d in data.dreams]
        if len(ids) != len(set(ids)):
            raise HTTPException(400, "Ek college do baar hai.")
        if any(sum(d.exam == e for d in data.dreams) > MAX_DREAMS for e in ("jee", "bitsat", "comedk")):
            raise HTTPException(400, f"Har exam ke {MAX_DREAMS} dream college hi ho sakte hain.")
        mine = [d.model_dump() for d in data.dreams]
        # Two saves at the same moment (two phones): each write only lands on the revision it merged with, else again.
        for _ in range(10):
            doc = await db.rf_dreams.find_one({"uid": uid}, {"_id": 0, "dreams": 1, "rev": 1}) or {}
            rev = doc.get("rev")
            dreams = merge(doc.get("dreams", []), data.base, mine)
            try:
                res = await db.rf_dreams.update_one({"uid": uid, "rev": rev},
                                                    {"$set": {"dreams": dreams, "rev": (rev or 0) + 1, "ts": time.time()}}, upsert=True)
            except DuplicateKeyError:  # the list changed meanwhile (the unique uid blocks a second document)
                continue
            if res.matched_count or res.upserted_id is not None:
                return {"dreams": dreams}
        raise HTTPException(503, "Abhi bahut badlav ek saath aa rahe hain. Thodi der mein phir try hoga.")

    @r.post("/mocks")
    async def add_mocks(data: MocksIn, x_rf_user: Optional[str] = Header(None)):
        """Released full mocks seen on any device; the same mock again replaces its older copy. Newest 30 are kept."""
        uid = rf_user(x_rf_user)
        mocks = list({m.id: m.model_dump() for m in data.mocks}.values())
        await db.rf_dreams.update_one({"uid": uid}, {"$pull": {"mocks": {"id": {"$in": [m["id"] for m in mocks]}}}})
        await db.rf_dreams.update_one({"uid": uid}, {"$push": {"mocks": {"$each": mocks, "$sort": {"at": -1}, "$slice": MAX_MOCKS}}, "$set": {"ts": time.time()}}, upsert=True)
        return {"ok": True}

    @r.post("/cheered")
    async def cheered(data: CheeredIn, x_rf_user: Optional[str] = Header(None)):
        """Dreams whose "Dream Unlocked" celebration has played, so no device plays it again."""
        uid = rf_user(x_rf_user)
        change = {"$addToSet": {"cheered": {"$each": list(dict.fromkeys(data.ids))}}, "$set": {"ts": time.time()}}
        try:
            await db.rf_dreams.update_one({"uid": uid}, change, upsert=True)
        except DuplicateKeyError:  # the account's first document was created at the same moment by another save
            await db.rf_dreams.update_one({"uid": uid}, change)
        return {"ok": True}

    return r
