from fastapi import FastAPI, APIRouter, Request, Header, HTTPException
from fastapi.responses import Response
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
from pydantic import BaseModel, Field, BeforeValidator, ConfigDict
from typing import Annotated, Literal, Optional, List
from pathlib import Path
from datetime import datetime, timezone
from bson import ObjectId
from http.cookiejar import DefaultCookiePolicy
import asyncio, json, logging, os, re, uuid, httpx

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

client = AsyncIOMotorClient(os.environ['MONGO_URL'])
db = client[os.environ['DB_NAME']]
JEELIVE_API = os.environ['JEELIVE_API'].rstrip('/')
CARDS_DIR = ROOT_DIR / 'rapidfire' / 'cards'

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("jeelive")

app = FastAPI()
api = APIRouter(prefix="/api")


@app.get("/health", include_in_schema=False)
@app.head("/health", include_in_schema=False)
async def health():
    return {"status": "ok"}


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


# ---------- JEELIVE proxy (web preview only; native talks to jeelive.ai directly) ----------
http: httpx.AsyncClient | None = None
JAR_CACHE: dict[str, dict] = {}
SID_RE = re.compile(r"^[A-Za-z0-9-]{16,64}$")
PASS_HEADERS = ("content-type", "retry-after", "location", "cache-control")


class CookieJar(BaseDocument):
    sid: str
    cookies: dict = {}
    updated_at: str = Field(default_factory=now_iso)


async def load_jar(sid: str) -> dict:
    if sid in JAR_CACHE:
        return JAR_CACHE[sid]
    jar = CookieJar.from_mongo(await db.jl_jars.find_one({"sid": sid}))
    JAR_CACHE[sid] = jar.cookies if jar else {}
    return JAR_CACHE[sid]


async def save_jar(sid: str, cookies: dict):
    JAR_CACHE[sid] = cookies
    await db.jl_jars.update_one({"sid": sid}, {"$set": CookieJar(sid=sid, cookies=cookies).to_mongo()}, upsert=True)


def apply_set_cookies(cookies: dict, headers: httpx.Headers) -> bool:
    changed = False
    for raw in headers.get_list("set-cookie"):
        first, *attrs = raw.split(";")
        if "=" not in first:
            continue
        name, value = first.split("=", 1)
        name, value = name.strip(), value.strip().strip('"')
        expired = any(a.strip().lower().startswith("max-age=0") for a in attrs) or value == ""
        if expired:
            changed |= cookies.pop(name, None) is not None
        elif cookies.get(name) != value:
            cookies[name] = value
            changed = True
    return changed


@api.api_route("/jl/{path:path}", methods=["GET", "POST", "PUT", "PATCH", "DELETE"])
async def jeelive_proxy(path: str, request: Request, x_jl_sid: str = Header(...)):
    if not SID_RE.match(x_jl_sid):
        raise HTTPException(400, "Invalid session handle.")
    cookies = dict(await load_jar(x_jl_sid))
    headers = {"Accept": request.headers.get("accept", "application/json")}
    if request.headers.get("content-type"):
        headers["Content-Type"] = request.headers["content-type"]
    if cookies:
        headers["Cookie"] = "; ".join(f"{k}={v}" for k, v in cookies.items())
    body = await request.body()
    try:
        r = await http.request(request.method, f"{JEELIVE_API}/{path}", params=request.query_params,
                               content=body or None, headers=headers)
    except httpx.HTTPError:
        return Response(json.dumps({"data": None, "error": {"code": "upstream_unreachable",
                        "message": "Connection interrupted. Your last saved work is safe. Please try again."},
                        "meta": {"api_version": "1"}}), status_code=503, media_type="application/json")
    if apply_set_cookies(cookies, r.headers):
        await save_jar(x_jl_sid, cookies)
    out = {k: r.headers[k] for k in PASS_HEADERS if k in r.headers}
    return Response(content=r.content, status_code=r.status_code, headers=out)


# ---------- Rapid Fire ----------
class Card(BaseDocument):
    id: str
    subject: str
    chapter: str
    topic: str = ""
    prompt: str
    formula: str = ""
    options: List[str]
    answer: int
    explain: str = ""
    review_status: str = "pilot_review_pending"
    syllabus: str = "JEE Main"


class SessionCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    subject: Literal["Physics", "Chemistry", "Mathematics"]
    chapter: Optional[str] = Field(default=None, max_length=80)
    count: int = Field(default=30, ge=1, le=30)
    card_ids: Optional[List[str]] = Field(default=None, max_length=30)
    request_id: str = Field(min_length=8, max_length=64)


class CardResult(BaseModel):
    card_id: str
    outcome: Literal["correct", "incorrect", "skipped", "timed_out"]
    choice: Optional[int] = Field(default=None, ge=0, le=3)
    ms: int = Field(default=0, ge=0, le=21000)


class SessionComplete(BaseModel):
    model_config = ConfigDict(extra="forbid")
    results: List[CardResult] = Field(max_length=30)


class RfSession(BaseDocument):
    id: str
    user_id: str
    request_id: str
    subject: str
    chapter: Optional[str] = None
    mode: str = "fresh"
    card_ids: List[str]
    status: str = "active"
    results: List[dict] = []
    summary: Optional[dict] = None
    created_at: str = Field(default_factory=now_iso)
    completed_at: Optional[str] = None


def rf_user(x_rf_user: Optional[str]) -> str:
    if not x_rf_user or not re.match(r"^[A-Za-z0-9-]{8,64}$", x_rf_user):
        raise HTTPException(401, "Sign in to use Rapid Fire.")
    return x_rf_user


def _game():
    from gamify import make_router
    return make_router(db, rf_user)


game_router, award = _game()

CARD_MTIMES: dict[str, float] = {}


async def sync_cards():
    if not CARDS_DIR.exists():
        return
    for f in CARDS_DIR.glob("*.json"):
        m = f.stat().st_mtime
        if CARD_MTIMES.get(f.name) == m:
            continue
        try:
            cards = [Card(**c) for c in json.loads(f.read_text())]
        except Exception:
            continue  # file mid-write; retry next cycle
        from pymongo import UpdateOne
        ops = [UpdateOne({"id": c.id}, {"$set": c.to_mongo()}, upsert=True) for c in cards]
        if ops:
            await db.rf_cards.bulk_write(ops, ordered=False)
            # cards removed by the verifier must disappear from the live bank too
            await db.rf_cards.delete_many({"subject": cards[0].subject, "chapter": cards[0].chapter, "id": {"$nin": [c.id for c in cards]}})
        CARD_MTIMES[f.name] = m
    CATALOG_CACHE.clear()


async def card_sync_loop():
    while True:
        try:
            await sync_cards()
        except Exception as e:  # noqa: BLE001
            logger.warning("card sync failed: %s", e)
        await asyncio.sleep(60)


CATALOG_CACHE: dict = {}


@api.get("/rf/catalog")
async def rf_catalog():
    if "v" not in CATALOG_CACHE:
        rows = await db.rf_cards.aggregate([{"$group": {"_id": {"s": "$subject", "c": "$chapter"}, "n": {"$sum": 1}}}]).to_list(1000)
        order = json.loads((ROOT_DIR / "rapidfire" / "chapters.json").read_text())
        counts = {(r["_id"]["s"], r["_id"]["c"]): r["n"] for r in rows}
        CATALOG_CACHE["v"] = {"subjects": [{"name": s, "total": sum(counts.get((s, c), 0) for c in chs),
                              "chapters": [{"name": c, "count": counts.get((s, c), 0)} for c in chs]} for s, chs in order.items()],
                              "review_status": "pilot_review_pending",
                              "note": "Formula/concept cards authored for the JEE Main syllabus. Pending owner review during the private pilot."}
    return CATALOG_CACHE["v"]


def public_card(c: Card) -> dict:
    return c.model_dump(exclude={"mongo_id", "syllabus"})


@api.post("/rf/sessions")
async def rf_create(data: SessionCreate, x_rf_user: Optional[str] = Header(None)):
    uid = rf_user(x_rf_user)
    existing = RfSession.from_mongo(await db.rf_sessions.find_one({"user_id": uid, "request_id": data.request_id}))
    if existing:
        cards = [Card.from_mongo(d) for d in await db.rf_cards.find({"id": {"$in": existing.card_ids}}).to_list(30)]
    else:
        if data.card_ids:
            docs = await db.rf_cards.find({"id": {"$in": data.card_ids}, "subject": data.subject}).to_list(30)
            mode = "repeat_missed"
        else:
            match = {"subject": data.subject, **({"chapter": data.chapter} if data.chapter else {})}
            docs = await db.rf_cards.aggregate([{"$match": match}, {"$sample": {"size": data.count}}]).to_list(data.count)
            mode = "fresh"
        if not docs:
            raise HTTPException(404, "No reviewed cards are available for this selection yet.")
        cards = [Card.from_mongo(d) for d in docs]
        existing = RfSession(id=str(uuid.uuid4()), user_id=uid, request_id=data.request_id, subject=data.subject,
                             chapter=data.chapter, mode=mode, card_ids=[c.id for c in cards])
        await db.rf_sessions.insert_one(existing.to_mongo())
    by_id = {c.id: c for c in cards}
    return {**existing.model_dump(exclude={"mongo_id", "user_id"}),
            "cards": [public_card(by_id[i]) for i in existing.card_ids if i in by_id], "seconds_per_card": 20}


@api.post("/rf/sessions/{sid}/complete")
async def rf_complete(sid: str, data: SessionComplete, x_rf_user: Optional[str] = Header(None)):
    uid = rf_user(x_rf_user)
    s = RfSession.from_mongo(await db.rf_sessions.find_one({"id": sid, "user_id": uid}))
    if not s:
        raise HTTPException(404, "Session not found.")
    if s.status == "completed":
        sm = s.summary or {}
        return {**s.model_dump(exclude={"mongo_id", "user_id"}), "reward": await award(uid, "solo:" + sid, "solo", sm.get("correct", 0), sm.get("total", 0), sm.get("answered", 0))}
    cards = {c["id"]: c for c in await db.rf_cards.find({"id": {"$in": s.card_ids}}, {"_id": 0}).to_list(30)}
    seen, rows = set(), []
    for r in data.results:
        if r.card_id not in cards or r.card_id in seen:
            continue
        seen.add(r.card_id)
        outcome = r.outcome
        if outcome in ("correct", "incorrect"):  # server re-derives correctness from the key
            outcome = "correct" if r.choice == cards[r.card_id]["answer"] else "incorrect"
        rows.append({"card_id": r.card_id, "outcome": outcome, "choice": r.choice if outcome in ("correct", "incorrect") else None,
                     "ms": r.ms, "chapter": cards[r.card_id]["chapter"], "topic": cards[r.card_id].get("topic", "")})
    for cid in s.card_ids:
        if cid not in seen:
            rows.append({"card_id": cid, "outcome": "skipped", "choice": None, "ms": 0, "chapter": cards.get(cid, {}).get("chapter", ""), "topic": ""})
    count = lambda k: sum(r["outcome"] == k for r in rows)  # noqa: E731
    correct, incorrect = count("correct"), count("incorrect")
    answered = correct + incorrect
    weak = {}
    for r in rows:
        if r["outcome"] in ("incorrect", "timed_out"):  # only cards actually attempted
            weak[r["topic"] or r["chapter"]] = weak.get(r["topic"] or r["chapter"], 0) + 1
    summary = {"total": len(rows), "correct": correct, "incorrect": incorrect, "skipped": count("skipped"),
               "timed_out": count("timed_out"), "answered": answered, "score": correct,
               "accuracy": round(100 * correct / answered, 1) if answered else None,
               "revise_topics": [k for k, _ in sorted(weak.items(), key=lambda x: -x[1])][:5]}
    await db.rf_sessions.update_one({"id": sid, "status": "active"}, {"$set": {"status": "completed", "results": rows,
                                    "summary": summary, "completed_at": now_iso()}})
    s = RfSession.from_mongo(await db.rf_sessions.find_one({"id": sid}))
    reward = await award(uid, "solo:" + sid, "solo", correct, len(rows), answered)
    return {**s.model_dump(exclude={"mongo_id", "user_id"}), "reward": reward}


@api.get("/rf/history")
async def rf_history(x_rf_user: Optional[str] = Header(None)):
    uid = rf_user(x_rf_user)
    docs = await db.rf_sessions.find({"user_id": uid, "status": "completed"}, {"_id": 0, "user_id": 0, "results": 0}) \
        .sort("completed_at", -1).limit(20).to_list(20)
    agg = await db.rf_sessions.aggregate([{"$match": {"user_id": uid, "status": "completed"}},
                                          {"$group": {"_id": None, "sessions": {"$sum": 1}, "correct": {"$sum": "$summary.correct"},
                                                      "cards": {"$sum": "$summary.total"}}}]).to_list(1)
    totals = agg[0] if agg else {"sessions": 0, "correct": 0, "cards": 0}
    totals.pop("_id", None)
    return {"items": docs, "totals": totals}


@api.get("/rf/sessions/{sid}")
async def rf_get(sid: str, x_rf_user: Optional[str] = Header(None)):
    uid = rf_user(x_rf_user)
    s = RfSession.from_mongo(await db.rf_sessions.find_one({"id": sid, "user_id": uid}))
    if not s:
        raise HTTPException(404, "Session not found.")
    cards = [Card.from_mongo(d) for d in await db.rf_cards.find({"id": {"$in": s.card_ids}}).to_list(30)]
    by_id = {c.id: c for c in cards}
    return {**s.model_dump(exclude={"mongo_id", "user_id"}), "cards": [public_card(by_id[i]) for i in s.card_ids if i in by_id]}


from duels import make_router as make_duels  # noqa: E402
api.include_router(make_duels(db, rf_user, public_card, award))
api.include_router(game_router)
app.include_router(api)
from starlette.middleware.gzip import GZipMiddleware  # noqa: E402
app.add_middleware(GZipMiddleware, minimum_size=1024)
app.add_middleware(CORSMiddleware, allow_credentials=True, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])


@app.on_event("startup")
async def startup():
    global http
    http = httpx.AsyncClient(timeout=httpx.Timeout(30.0, connect=10.0), limits=httpx.Limits(max_connections=200, max_keepalive_connections=50))
    # The shared upstream client must NEVER keep cookies: each learner's jar is per-sid only.
    from http.cookiejar import DefaultCookiePolicy
    http.cookies.jar.set_policy(DefaultCookiePolicy(allowed_domains=[]))
    # Never persist upstream cookies on the shared client; each sid has its own jar (prevents cross-user session leak)
    http.cookies.jar.set_policy(DefaultCookiePolicy(allowed_domains=[]))
    await db.rf_cards.create_index("id", unique=True)
    await db.rf_cards.create_index([("subject", 1), ("chapter", 1)])
    await db.rf_sessions.create_index([("user_id", 1), ("request_id", 1)], unique=True)
    await db.rf_sessions.create_index("id", unique=True)
    await db.rf_sessions.create_index([("user_id", 1), ("status", 1), ("completed_at", -1)])
    await db.jl_jars.create_index("sid", unique=True)
    await db.rf_duels.create_index("id", unique=True)
    await db.rf_duels.create_index("code")
    await db.rf_duels.create_index([("status", 1), ("mode", 1), ("subject", 1), ("created_ts", 1)])
    await db.rf_duels.create_index("players.uid")
    await db.rf_awards.create_index([("uid", 1), ("ref", 1)], unique=True)
    await db.rf_profiles.create_index("uid", unique=True)
    await db.rf_profiles.create_index([("xp", -1)])
    asyncio.create_task(card_sync_loop())


@app.on_event("shutdown")
async def shutdown():
    if http:
        await http.aclose()
    client.close()
