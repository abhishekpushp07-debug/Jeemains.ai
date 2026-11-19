from fastapi import FastAPI, APIRouter, Depends, Request, Header, HTTPException
from fastapi.responses import Response, JSONResponse
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from pymongo import AsyncMongoClient, ReturnDocument
from pymongo.asynchronous.collection import AsyncCollection
from pydantic import BaseModel, Field, BeforeValidator, ConfigDict
from typing import Annotated, Literal, Optional, List
from pathlib import Path
from datetime import datetime, timezone
from bson import ObjectId
from pymongo.errors import DuplicateKeyError, OperationFailure
from exam_groups import ACTIVE_EXAMS, Exam, SUBJECTS, require_active_exam, resolve_exam
from revision import record_learning, weak_chapters, weak_topic_deck, make_router as make_revision
from owner_downloads import make_router as make_owner_downloads
from branding import router as branding_router
from marketing_media import router as marketing_router
from legal_pages import router as legal_router
from arena_web import router as arena_web_router
from jl_transport import UpstreamError, canonical_request, make_client
from session_coordination import session_rotation
import login_guard
from client_ip import client_ip
from rf_access import make_access_router, install_access_guard, maintenance_on
from load_guard import ArenaBusy, InflightCounter, arena_gate, busy_response, monitor as load_monitor, raise_fd_limit, snapshot as load_snapshot
from rapid_deck import fresh_deck, seen_cards
from scope import CARD_COUNTS, CARD_SECONDS, Pick, normalise, scope_fields
from metadata_cache import metadata_cache
from performance import ServerTiming, AssetAwareCompression
from cors_config import allowed_origins
import aiohttp, asyncio, hashlib, json, logging, os, random, re, time, uuid

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


# ---------- JEELIVE proxy (every platform signs in through here) ----------
http: aiohttp.ClientSession | None = None
SID_RE = re.compile(r"^[A-Za-z0-9-]{16,64}$")
PASS_HEADERS = ("content-type", "retry-after", "location", "cache-control", "etag", "last-modified", "content-range", "accept-ranges")
JAR_IDLE_DAYS = 90  # a jar no request used for 90 days is removed by Mongo (TTL on seen_at)
JAR_TOUCH_SECONDS = 86400  # seen_at is refreshed at most once a day per jar, not on every request


def jar_field(name: str) -> str:
    """A cookie name as a Mongo field name ('.' and '$' cannot be used in an update path)."""
    return name.replace("%", "%25").replace(".", "%2E").replace("$", "%24")


def cookie_name(field: str) -> str:
    return field.replace("%24", "$").replace("%2E", ".").replace("%25", "%")


async def load_jar(sid: str) -> dict:
    # Always read from Mongo (one indexed read): with several server processes a per-process copy could send a
    # refresh cookie another process has just rotated, which signs the student out.
    jar = await db.jl_jars.find_one({"sid": sid}, {"_id": 0, "cookies": 1, "seen_at": 1})
    if not jar:
        return {}
    now = datetime.now(timezone.utc)
    seen = jar.get("seen_at")
    if not isinstance(seen, datetime) or (now - seen.replace(tzinfo=timezone.utc)).total_seconds() > JAR_TOUCH_SECONDS:
        await db.jl_jars.update_one({"sid": sid}, {"$set": {"seen_at": now}})
    return {cookie_name(k): v for k, v in (jar.get("cookies") or {}).items()}


def cookie_changes(cookies: dict, headers) -> tuple[dict, list]:
    """The cookies a website answer sets (new or changed values) and the ones it expires."""
    sets, gone = {}, []
    for raw in headers.getall("set-cookie", []):
        first, *attrs = raw.split(";")
        if "=" not in first:
            continue
        name, value = first.split("=", 1)
        name, value = name.strip(), value.strip().strip('"')
        if any(a.strip().lower().startswith("max-age=0") for a in attrs) or value == "":
            sets.pop(name, None)
            gone.append(name)
        else:
            if name in gone:
                gone.remove(name)
            if cookies.get(name) != value:
                sets[name] = value
    return sets, gone


async def save_cookie_changes(sid: str, sets: dict, gone: list):
    # One field per cookie, never the whole set: two servers renewing different cookies at the same moment both keep theirs.
    update = {"$set": {**{f"cookies.{jar_field(k)}": v for k, v in sets.items()}, "updated_at": now_iso(), "seen_at": datetime.now(timezone.utc)}}
    if gone:
        update["$unset"] = {f"cookies.{jar_field(k)}": "" for k in gone}
    await db.jl_jars.update_one({"sid": sid}, update, upsert=True)


@api.api_route("/jl/{path:path}", methods=["GET", "POST", "PUT", "PATCH", "DELETE"])
async def jeelive_proxy(path: str, request: Request, x_jl_sid: str = Header(...)):
    if not SID_RE.match(x_jl_sid):
        raise HTTPException(400, "Invalid session handle.")
    async with session_rotation(db, x_jl_sid, path):
        return await forward_jeelive(path, request, x_jl_sid)


async def forward_jeelive(path: str, request: Request, x_jl_sid: str):
    cookies = dict(await load_jar(x_jl_sid))
    headers = {"Accept": request.headers.get("accept", "application/json")}
    if request.headers.get("content-type"):
        headers["Content-Type"] = request.headers["content-type"]
    for name in ("if-none-match", "if-modified-since", "if-range", "range"):
        if request.headers.get(name):
            headers[name] = request.headers[name]
    if cookies:
        headers["Cookie"] = "; ".join(f"{k}={v}" for k, v in cookies.items())
    ip = client_ip(request)  # only the verified student address: entries a caller wrote themselves are never passed on
    if ip:
        headers["X-Forwarded-For"] = ip
    body = await request.body()
    guard, paused = await login_guard.check(db, request, path, body)
    if paused:
        return paused
    try:
        r = await canonical_request(http, request.method, f"{JEELIVE_API}/{path}", path=path,
                                    params=request.query_params, body=body or None, headers=headers)
    except UpstreamError:
        return Response(json.dumps({"data": None, "error": {"code": "upstream_unreachable",
                        "message": "Connection interrupted. Your last saved work is safe. Please try again."},
                        "meta": {"api_version": "1"}}), status_code=503, media_type="application/json", headers={'Cache-Control': 'no-store', 'Vary': 'X-JL-Sid'})
    if guard:
        await login_guard.record(db, guard, r.status_code)
    sets, gone = cookie_changes(cookies, r.headers)
    if path == "auth/logout" and 200 <= r.status_code < 300:
        await db.jl_jars.delete_one({"sid": x_jl_sid})  # signed out: this session handle carries nothing any more
    elif sets or gone:
        await save_cookie_changes(x_jl_sid, sets, gone)
    out = {k: r.headers[k] for k in PASS_HEADERS if k in r.headers}
    out['Vary'] = 'X-JL-Sid'
    if path.startswith('auth/'):
        out['Cache-Control'] = 'no-store'
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
    exam: Optional[Exam] = None
    diagram: Optional[dict] = None
    source_card_id: Optional[str] = None
    provenance: str = ""


MAX_ROUND = max(CARD_COUNTS)


class SessionCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    subject: Literal["Physics", "Chemistry", "Mathematics", "English", "Logical Reasoning", "Biology"] = "Physics"
    chapter: Optional[str] = Field(default=None, max_length=80)
    picks: Optional[List[Pick]] = Field(default=None, max_length=5)  # up to 5 subjects or chapters for a fresh sprint
    count: int = Field(default=30, ge=1, le=MAX_ROUND)  # a fresh sprint is 30, 50 or 100 cards
    card_ids: Optional[List[str]] = Field(default=None, max_length=MAX_ROUND)
    request_id: str = Field(min_length=8, max_length=64)
    exam: Optional[Exam] = None
    diagram_only: bool = False
    revision: bool = False
    weak_topics: bool = False  # Weak Topic Sprint: only the subtopics this student keeps missing


class CardResult(BaseModel):
    card_id: str
    outcome: Literal["correct", "incorrect", "skipped", "timed_out"]
    choice: Optional[int] = Field(default=None, ge=0, le=3)
    ms: int = Field(default=0, ge=0, le=21000)


class SessionComplete(BaseModel):
    model_config = ConfigDict(extra="forbid")
    results: List[CardResult] = Field(max_length=MAX_ROUND)


class RfSession(BaseDocument):
    id: str
    user_id: str
    request_id: str
    subject: str
    chapter: Optional[str] = None
    picks: Optional[List[dict]] = None
    label: Optional[str] = None
    mode: str = "fresh"
    card_ids: List[str]
    status: str = "active"
    results: List[dict] = []
    summary: Optional[dict] = None
    created_at: str = Field(default_factory=now_iso)
    completed_at: Optional[str] = None
    exam: Optional[Exam] = None


def rf_user(x_rf_user: Optional[str]) -> str:
    if not x_rf_user or not re.match(r"^[A-Za-z0-9-]{8,64}$", x_rf_user):
        raise HTTPException(401, "Sign in to use Rapid Fire.")
    return x_rf_user


def _game():
    from gamify import make_router
    return make_router(db, rf_user)


game_router, award = _game()

CARD_HASHES: dict[str, str] = {}  # card file -> content hash already in Mongo (shared by every process via rf_meta)
CARD_KEYS: dict[str, list] = {}


async def sync_cards():
    from pymongo import UpdateOne
    if await maintenance_on(db):
        return
    if not CARD_HASHES:  # first run in this process: what the other servers already synced
        saved = (await db.rf_meta.find_one({"_id": "card_files"}) or {}).get("files", {})
        CARD_HASHES.update({cookie_name(k): v for k, v in saved.items()})
    changed, synced = False, {}
    # NEET is a preserved archive, not an actively synced/live bank in this app.
    for exam, directory in (("JEE", CARDS_DIR),):
        if not directory.exists():
            continue
        keys = sorted(exam + ":" + f.name for f in directory.glob("*.json"))
        for f in directory.glob("*.json"):
            key, raw = exam + ":" + f.name, f.read_bytes()
            digest = hashlib.sha1(raw).hexdigest()
            if CARD_HASHES.get(key) == digest:
                continue
            try:
                cards = [Card(**{**c, "exam": exam}) for c in json.loads(raw) if c["subject"] in SUBJECTS[exam]]
            except Exception:
                logger.warning("Skipping invalid or mid-write card file: %s", f.name)
                continue
            ops = [UpdateOne({"id": c.id}, {"$set": {**c.to_mongo(), "retired": False, "source_file": key}}, upsert=True) for c in cards]
            if ops:
                await db.rf_cards.bulk_write(ops, ordered=False)
                await db.rf_cards.update_many({"exam": exam, "subject": cards[0].subject, "chapter": cards[0].chapter,
                                               "id": {"$nin": [c.id for c in cards]}}, {"$set": {"retired": True}})
                changed = True
            else:
                result = await db.rf_cards.update_many({"source_file": key, "retired": {"$ne": True}}, {"$set": {"retired": True}})
                changed |= bool(result.modified_count)
            CARD_HASHES[key] = synced[key] = digest
        if CARD_KEYS.get(exam) != keys:  # a card file was removed: retire its cards (only when the file list changes)
            result = await db.rf_cards.update_many({"source_file": {"$regex": "^" + exam + ":", "$nin": keys}, "retired": {"$ne": True}}, {"$set": {"retired": True}})
            changed |= bool(result.modified_count)
            CARD_KEYS[exam] = keys
    if synced:
        await db.rf_meta.update_one({"_id": "card_files"}, {"$set": {f"files.{jar_field(k)}": v for k, v in synced.items()}}, upsert=True)
    if changed:
        await metadata_cache.invalidate_prefix(f'{db.name}:')


async def card_sync_loop():
    while True:
        try:
            await sync_cards()
        except Exception as e:  # noqa: BLE001
            logger.warning("card sync failed: %s", e)
        await asyncio.sleep(60)


@api.get("/rf/catalog")
async def rf_catalog(exam: Optional[Exam] = None):
    exam = require_active_exam(exam)
    async def load():
        scope = {"exam": exam}
        rows = await (await db.rf_cards.aggregate([{"$match": {"retired": {"$ne": True}, **scope}}, {"$group": {"_id": {"s": "$subject", "c": "$chapter"}, "n": {"$sum": 1}, "diagrams": {"$sum": {"$cond": [{"$ifNull": ["$diagram", False]}, 1, 0]}}}}])).to_list(1000)
        order = {subject: chapters for subject, chapters in json.loads((ROOT_DIR / "rapidfire" / "chapters.json").read_text()).items() if subject in SUBJECTS[exam]}
        counts = {(r["_id"]["s"], r["_id"]["c"]): r["n"] for r in rows}
        return {"exam": exam, "diagram_count": sum(r["diagrams"] for r in rows), "subjects": [{"name": s, "total": sum(counts.get((s, c), 0) for c in chs),
                              "chapters": [{"name": c, "count": counts.get((s, c), 0)} for c in chs]} for s, chs in order.items()],
                              "exams": {active: SUBJECTS[active] for active in ACTIVE_EXAMS},
                              "review_status": "quick_recall_reviewed_v1",
                              "note": "Full-bank quick-recall suitability pass completed. Answer time is an editorial estimate, not a student timing guarantee."}
    value, state = await metadata_cache.get_or_load(f'{db.name}:catalog:{exam}', load, ttl=60)
    return JSONResponse(value, headers={'X-Cache': state, 'Cache-Control': 'no-cache'})


def public_card(c: Card) -> dict:
    return c.model_dump(exclude={"mongo_id", "syllabus"})


@api.post("/rf/sessions", dependencies=[Depends(arena_gate)])
async def rf_create(data: SessionCreate, x_rf_user: Optional[str] = Header(None)):
    uid = rf_user(x_rf_user)
    scope = None if data.revision or data.card_ids or data.weak_topics else scope_fields(normalise(data.picks, data.subject, data.chapter))
    if scope:
        data.subject, data.chapter = scope["subject"], scope["chapter"]
    exam = resolve_exam(data.exam, data.subject)
    if data.diagram_only:
        raise HTTPException(410, "Diagram sprints are archived in this app.")
    existing = RfSession.from_mongo(await db.rf_sessions.find_one({"user_id": uid, "request_id": data.request_id}))
    if existing:
        resolve_exam(existing.exam, existing.subject)
        cards = [Card.from_mongo(d) for d in await db.rf_cards.find({"id": {"$in": existing.card_ids}}).to_list(MAX_ROUND)]
    else:
        label = None
        if data.weak_topics:
            docs, topics = await weak_topic_deck(db, uid, exam, data.count, await seen_cards(db, uid, exam))
            if not docs:
                raise HTTPException(404, "No weak subtopics yet. Play a few sprints or matches and your Weak Topic Sprint builds itself.")
            data.subject, data.chapter, label = docs[0]["subject"], None, f"Weak Topic Sprint · {len(topics)} subtopic{'s' if len(topics) > 1 else ''}"
            mode = "weak_topics"
        elif data.revision:
            weak = await weak_chapters(db, uid, exam)
            selected = next((row for row in weak if row["subject"] == data.subject and (not data.chapter or row["chapter"] == data.chapter)), None)
            if not selected:
                raise HTTPException(404, "No missed cards left here. Play a sprint to build your revision list.")
            docs = await db.rf_cards.find({"id": {"$in": selected["card_ids"]}, "exam": exam, "retired": {"$ne": True}}, {"_id": 0}).to_list(30)
            docs.sort(key=lambda c: selected["card_ids"].index(c["id"]))
            docs = docs[:min(30, data.count)]
            data.chapter = selected["chapter"]
            mode = "weak_revision"
        elif data.card_ids:
            docs = await db.rf_cards.find({"id": {"$in": data.card_ids}, "exam": exam, "subject": data.subject, "retired": {"$ne": True}}, {"_id": 0}).to_list(MAX_ROUND)
            mode = "repeat_missed"
        else:
            docs = await fresh_deck(db, exam, data.subject, data.chapter, data.count, picks=scope["picks"], uid=uid)
            mode = "diagrams" if data.diagram_only else "fresh"
        if not docs:
            raise HTTPException(404, "No reviewed cards are available for this selection yet.")
        cards = [Card.from_mongo(d) for d in docs]
        existing = RfSession(id=str(uuid.uuid4()), user_id=uid, request_id=data.request_id, subject=data.subject,
                             chapter=data.chapter, exam=exam, mode=mode, card_ids=[c.id for c in cards], **({"picks": scope["picks"], "label": scope["label"]} if scope else {"label": label} if label else {}))
        try:
            await db.rf_sessions.insert_one(existing.to_mongo())
        except DuplicateKeyError:
            return await rf_create(data, x_rf_user)
    by_id = {c.id: c for c in cards}
    return {**existing.model_dump(exclude={"mongo_id", "user_id"}),
            "cards": [public_card(by_id[i]) for i in existing.card_ids if i in by_id], "seconds_per_card": CARD_SECONDS}


@api.post("/rf/sessions/{sid}/complete")
async def rf_complete(sid: str, data: SessionComplete, x_rf_user: Optional[str] = Header(None)):
    uid = rf_user(x_rf_user)
    s = RfSession.from_mongo(await db.rf_sessions.find_one({"id": sid, "user_id": uid}))
    if not s:
        raise HTTPException(404, "Session not found.")
    resolve_exam(s.exam, s.subject)
    if s.status == "completed":
        sm = s.summary or {}
        docs = await db.rf_cards.find({"id": {"$in": s.card_ids}}, {"_id": 0}).to_list(MAX_ROUND)
        await record_learning(db, uid, "solo:" + sid, s.exam, s.results, docs, s.completed_at)
        return {**s.model_dump(exclude={"mongo_id", "user_id"}), "reward": await award(uid, "solo:" + sid, "solo", sm.get("correct", 0), sm.get("total", 0), sm.get("answered", 0), exam=s.exam)}
    cards = {c["id"]: c for c in await db.rf_cards.find({"id": {"$in": s.card_ids}}, {"_id": 0}).to_list(MAX_ROUND)}
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
    await record_learning(db, uid, "solo:" + sid, s.exam, s.results, list(cards.values()), s.completed_at)
    # Diamonds come from fresh sprints only: replays of the same missed cards never earn them.
    gems, best = phoenix([r["outcome"] for r in s.results]) if s.mode == "fresh" else ({}, 0)
    reward = await award(uid, "solo:" + sid, "solo", s.summary["correct"], s.summary["total"], s.summary["answered"], exam=s.exam, diamonds=gems, phoenix_streak=best)
    return {**s.model_dump(exclude={"mongo_id", "user_id"}), "reward": reward}


@api.get("/rf/history")
async def rf_history(exam: Optional[Exam] = None, x_rf_user: Optional[str] = Header(None)):
    uid = rf_user(x_rf_user)
    exam = require_active_exam(exam)
    query = {"user_id": uid, "status": "completed", "exam": exam}
    docs = await db.rf_sessions.find(query, {"_id": 0, "user_id": 0, "results": 0}) \
        .sort("completed_at", -1).limit(20).to_list(20)
    won = {a["ref"]: (a.get("reward") or {}).get("diamonds") or {} for a in
           await db.rf_awards.find({"uid": uid, "ref": {"$in": ["solo:" + d["id"] for d in docs]}}, {"_id": 0, "ref": 1, "reward.diamonds": 1}).to_list(20)}
    for d in docs:
        d["diamonds"] = won.get("solo:" + d["id"], {})
    agg = await (await db.rf_sessions.aggregate([{"$match": query},
                                          {"$group": {"_id": None, "sessions": {"$sum": 1}, "correct": {"$sum": "$summary.correct"},
                                                      "cards": {"$sum": "$summary.total"}}}])).to_list(1)
    totals = agg[0] if agg else {"sessions": 0, "correct": 0, "cards": 0}
    totals.pop("_id", None)
    return {"items": docs, "totals": totals}


@api.get("/rf/sessions/{sid}")
async def rf_get(sid: str, x_rf_user: Optional[str] = Header(None)):
    uid = rf_user(x_rf_user)
    s = RfSession.from_mongo(await db.rf_sessions.find_one({"id": sid, "user_id": uid}))
    if not s:
        raise HTTPException(404, "Session not found.")
    resolve_exam(s.exam, s.subject)
    cards = [Card.from_mongo(d) for d in await db.rf_cards.find({"id": {"$in": s.card_ids}}).to_list(MAX_ROUND)]
    by_id = {c.id: c for c in cards}
    recorded = await db.rf_awards.find_one({'uid': uid, 'ref': 'solo:' + sid}, {'_id': 0, 'reward': 1}) if s.status == 'completed' else None
    return {**s.model_dump(exclude={"mongo_id", "user_id"}), "cards": [public_card(by_id[i]) for i in s.card_ids if i in by_id], 'reward': (recorded or {}).get('reward'), "seconds_per_card": CARD_SECONDS}


from duels import make_router as make_duels  # noqa: E402
from social import make_router as make_social  # noqa: E402
from rooms import make_router as make_rooms  # noqa: E402
from gangs import make_router as make_gangs  # noqa: E402
from gamify import phoenix  # noqa: E402
from leagues import make_router as make_leagues  # noqa: E402
from cups import make_router as make_cups  # noqa: E402
from squads import make_router as make_squads  # noqa: E402
from pin_reset import make_pin_reset  # noqa: E402
from rank_predictor import make_router as make_rank  # noqa: E402
from mission_links import make_router as make_mission_links, ensure_indexes as mission_indexes  # noqa: E402
from dream import make_router as make_dream  # noqa: E402
from daily import make_router as make_daily, ensure_indexes as daily_indexes  # noqa: E402
duel_router, duel_api = make_duels(db, rf_user, public_card, award)
api.include_router(make_daily(db, rf_user, award))
api.include_router(duel_router)
api.include_router(make_social(db, rf_user))
api.include_router(make_rooms(db, rf_user, duel_api["seat"]))
api.include_router(make_gangs(db, rf_user))
api.include_router(make_leagues(db, rf_user))
cups_router = make_cups(db, rf_user, duel_api)
api.include_router(cups_router)
api.include_router(make_squads(db, rf_user))
api.include_router(make_pin_reset(db))
api.include_router(game_router)
api.include_router(make_revision(db, rf_user))
api.include_router(make_owner_downloads(db))
api.include_router(branding_router)
api.include_router(marketing_router)
api.include_router(legal_router)
api.include_router(arena_web_router)
api.include_router(make_rank())
api.include_router(make_mission_links(db, rf_user))
api.include_router(make_dream(db, rf_user))
api.include_router(make_access_router(db, lambda: http))
app.include_router(api)
install_access_guard(app, db)
app.add_middleware(AssetAwareCompression, minimum_size=1024, compresslevel=4)
app.add_middleware(ServerTiming)
app.add_middleware(InflightCounter)
app.add_exception_handler(ArenaBusy, busy_response)
app.add_middleware(CORSMiddleware, allow_credentials=True, allow_origins=allowed_origins(), allow_methods=["*"], allow_headers=["*"], expose_headers=['Server-Timing', 'X-Cache', 'Retry-After'])


@app.get("/api/health/load", include_in_schema=False)
async def health_load():
    """This process's load (no player data): event-loop delay, requests in flight, live sockets, whether new matches wait."""
    return JSONResponse(load_snapshot(), headers={"Cache-Control": "no-store"})


async def cup_night_loop():
    """Cup Night starts at 8 pm IST on its own: every 3 seconds, seat tonight's cups once their moment has come."""
    while True:
        try:
            await cups_router.night_tick()
        except Exception:  # noqa: BLE001 - a bad tick must never stop the next one
            logging.getLogger(__name__).exception("cup night tick failed")
        await asyncio.sleep(3)


async def backfill_cup_crowns():
    """Once: count every cup each player has won, and how many of those beat real players (cups_real arrived after the first cups)."""
    if await db.rf_meta.find_one({"_id": "cup_crowns_v1"}):
        return
    humans = {"$size": {"$filter": {"input": "$players", "cond": {"$ne": ["$$this.bot", True]}}}}
    rows = await db.rf_cups.aggregate([{"$match": {"status": "finished", "champion": {"$type": "string"}}},
                                 {"$group": {"_id": "$champion", "won": {"$sum": 1}, "real": {"$sum": {"$cond": [{"$gt": [humans, 1]}, 1, 0]}}}}])
    async for row in rows:
        if not row["_id"].startswith("bot-"):
            await db.rf_profiles.update_one({"uid": row["_id"]}, {"$set": {"cups_won": row["won"], "cups_real": row["real"]}})
    await db.rf_meta.update_one({"_id": "cup_crowns_v1"}, {"$set": {"ts": time.time()}}, upsert=True)



SETUP_VERSION = hashlib.sha1(b"".join(p.read_bytes() for p in sorted(ROOT_DIR.glob("*.py")))).hexdigest()[:16]


async def take_turn(name: str, seconds: float) -> bool:
    """One server process at a time does `name`; a turn left by a process that stopped runs out after `seconds`."""
    now = time.time()
    try:
        return bool(await db.rf_meta.find_one_and_update({"_id": "turn:" + name, "until": {"$lt": now}}, {"$set": {"until": now + seconds}},
                                                         upsert=True, return_document=ReturnDocument.AFTER))
    except DuplicateKeyError:
        return False


async def sweep():
    """Closes what nobody came back to: matches left waiting or past their end (their rewards are paid now), sprints
    never finished, and cup payouts cut off by a server restart."""
    now = time.time()
    late = {"$or": [{"status": "waiting", "created_ts": {"$lt": now - 1800}}, {"status": "ready", "ends_at": {"$lt": now - 120}}]}
    # Matches of an archived exam cannot be settled (no rewards there); close them so they never fill the batch below.
    await db.rf_duels.update_many({"$and": [late, {"$or": [{"exam": {"$nin": list(ACTIVE_EXAMS)}}, {"exam": {"$exists": False}, "subject": "Biology"}]}]},
                                  {"$set": {"status": "archived", "archived_ts": now}})
    stale = await db.rf_duels.find(late).limit(500).to_list(500)
    for d in stale:
        try:
            await duel_api["settle"](d)
        except Exception as e:  # noqa: BLE001 - one bad match must not stop the rest
            logger.warning("sweep could not close a match: %s", e)
    old = datetime.fromtimestamp(now - 86400, timezone.utc).isoformat()
    await db.rf_sessions.update_many({"status": "active", "created_at": {"$lt": old}}, {"$set": {"status": "expired"}})
    await cups_router.resume_payouts()


async def sweep_loop():
    while True:
        await asyncio.sleep(300 + random.random() * 30)
        try:
            if await take_turn("sweep", 240):
                await sweep()
        except Exception:  # noqa: BLE001
            logger.exception("sweep failed")


@app.on_event("startup")
async def startup():
    global http
    raise_fd_limit()  # one open file per player socket: the 1024 default capped a process at ~1000 players
    asyncio.create_task(load_monitor())
    if os.environ.get("RF_ACCESS_LOG") != "1":  # a log line per request costs real CPU at crowd scale
        logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
        logging.getLogger("uvicorn.error").setLevel(logging.WARNING)
    logging.getLogger("httpx").setLevel(logging.WARNING)  # httpx logs every request at INFO
    http = make_client()
    # Indexes, migrations and the first card sync run once per code version, on one process. The other processes of a
    # big deployment wait for it (at most 30 s) instead of all repeating ~60 index calls and ~14k card writes.
    done = {"_id": "setup:" + SETUP_VERSION, "done": True}
    if not await db.rf_meta.find_one(done, {"_id": 1}):
        if await take_turn("setup:" + SETUP_VERSION, 600):
            await setup_database()
            await db.rf_meta.update_one({"_id": done["_id"]}, {"$set": {"done": True, "ts": time.time()}}, upsert=True)
            # Old version markers stay (a few bytes each); nothing is deleted at startup.
        else:
            for _ in range(30):
                if await db.rf_meta.find_one(done, {"_id": 1}):
                    break
                await asyncio.sleep(1)
    asyncio.create_task(cup_night_loop())
    asyncio.create_task(card_sync_loop())
    asyncio.create_task(sweep_loop())


async def setup_database():
    await db.rf_cards.create_index("id", unique=True)
    await db.rf_access.create_index('digest', unique=True)
    await db.rf_access.create_index('expires_at', expireAfterSeconds=0)
    await db.rf_cards.create_index([("subject", 1), ("chapter", 1)])
    await db.rf_sessions.create_index([("user_id", 1), ("request_id", 1)], unique=True)
    await db.rf_sessions.create_index("id", unique=True)
    await db.rf_sessions.create_index([("user_id", 1), ("status", 1), ("completed_at", -1)])
    await db.jl_jars.create_index("sid", unique=True)
    # Jars nobody used for JAR_IDLE_DAYS are removed; rows from before seen_at existed get the full period from now.
    await db.jl_jars.update_many({"seen_at": None}, {"$set": {"seen_at": datetime.now(timezone.utc)}})
    await db.jl_jars.create_index("seen_at", expireAfterSeconds=JAR_IDLE_DAYS * 86400)
    await db.jl_locks.create_index("until", expireAfterSeconds=60)
    await db.rf_night_seats.create_index([("day", 1), ("group", 1)])
    await db.rf_night_seats.create_index([("day", 1), ("ts", 1)])
    await mission_indexes(db)
    await db.pin_resets.create_index([("phone", 1), ("at", -1)])
    await db.pin_resets.create_index([("ip", 1), ("at", -1)])
    await login_guard.setup(db)
    await db.rf_duels.create_index("id", unique=True)
    await db.rf_duels.create_index("code")
    await db.rf_duels.create_index([("status", 1), ("mode", 1), ("subject", 1), ("created_ts", 1)])
    await db.rf_duels.create_index("players.uid")
    await db.rf_awards.create_index([("uid", 1), ("ref", 1)], unique=True)
    await db.rf_profiles.create_index("uid", unique=True)
    await db.rf_profiles.create_index([("xp", -1)])
    await db.rf_cards.create_index([("exam", 1), ("subject", 1), ("chapter", 1), ("retired", 1)])
    await db.rf_cards.create_index([('exam', 1), ('subject', 1), ('chapter', 1), ('id', 1)])
    await db.rf_sessions.create_index([("user_id", 1), ("exam", 1), ("status", 1), ("completed_at", -1)])
    await db.rf_duels.create_index([("exam", 1), ("status", 1), ("mode", 1), ("subject", 1), ("created_ts", 1)])
    await db.rf_duels.create_index([('players.uid', 1), ('exam', 1), ('status', 1), ('finished_ts', -1)])
    await db.rf_learning_events.create_index([("uid", 1), ("ref", 1)], unique=True)
    # Rapid Fire social layer (profiles, friends, blocks, notices, challenges).
    await db.rf_profiles.create_index("pid", unique=True, partialFilterExpression={"pid": {"$type": "string"}})
    await db.rf_profiles.create_index("phone_hash", sparse=True)
    await db.rf_friends.create_index([("uid", 1), ("fid", 1)], unique=True)
    await db.rf_friends.create_index("fid")
    await db.rf_blocks.create_index([("uid", 1), ("bid", 1)], unique=True)
    await db.rf_blocks.create_index("bid")
    await db.rf_notices.create_index([("uid", 1), ("done", 1), ("ts", -1)])
    await db.rf_challenges.create_index("id", unique=True)
    await db.rf_challenges.create_index([("invites.uid", 1), ("status", 1), ("expires_ts", 1)])
    await db.rf_challenges.create_index([("from_uid", 1), ("status", 1)])
    await db.rf_link_visits.create_index([("cid", 1), ("key", 1)], unique=True)
    # Link visits are kept (one row per phone per link); retire the old 30-day auto-delete index if present.
    if (await db.rf_link_visits.index_information()).get("ts_1", {}).get("expireAfterSeconds") is not None:
        await db.rf_link_visits.drop_index("ts_1")
    await db.rf_link_visits.create_index("ts")
    await db.rf_gangs.create_index("id", unique=True)
    await db.rf_gangs.create_index([("members.uid", 1), ("closed", 1)])
    await db.rf_duels.create_index([("gang_id", 1), ("finished_ts", -1)], sparse=True)
    await db.rf_duels.create_index("challenge_id", sparse=True)
    await db.rf_duels.create_index([("teams.a.id", 1), ("finished_ts", -1)], sparse=True)
    await db.rf_duels.create_index([("teams.b.id", 1), ("finished_ts", -1)], sparse=True)
    await db.rf_feed.create_index([("uid", 1), ("ts", -1)])
    await db.rf_profiles.create_index("friend_code", unique=True, partialFilterExpression={"friend_code": {"$type": "string"}})
    await db.rf_cups.create_index("id", unique=True)
    await db.rf_cups.create_index([("players.uid", 1), ("status", 1)])
    await db.rf_cups.create_index([("invites", 1), ("status", 1)])
    await db.rf_cups.create_index([("kind", 1), ("status", 1), ("scope_key", 1)])
    await db.rf_duels.create_index([("status", 1), ("players.uid", 1)])
    await db.rf_cups.create_index("code", unique=True, partialFilterExpression={"code": {"$type": "string"}})
    await db.rf_cups.create_index([("champion", 1), ("status", 1), ("finished_ts", -1)], sparse=True)
    await db.rf_cups.create_index("night", sparse=True)
    await db.rf_cups.create_index([("night", 1), ("night_no", 1)], sparse=True)
    await backfill_cup_crowns()
    await cups_router.migrate_nights()
    await db.rf_cups.create_index("payout", sparse=True)
    await db.rf_duels.create_index([("team_mode", 1), ("status", 1)], sparse=True)
    # Spectators of a live match, shared by every server (count + 100-watcher limit); rows vanish a minute after the last look.
    await db.rf_watch.create_index([("did", 1), ("ts", 1)])
    await db.rf_watch.create_index("at", expireAfterSeconds=60)
    # Feed rows are kept (reads already show only the last 7 days); retire the old auto-delete index if present.
    if "at_1" in await db.rf_feed.index_information():
        await db.rf_feed.drop_index("at_1")
    await db.rf_learning_events.create_index([("uid", 1), ("exam", 1), ("completed_at", 1), ("ref", 1)])
    for exam in SUBJECTS:
        await db.rf_profiles.create_index([(f"exam_stats.{exam}.xp", -1), ("uid", 1)])
    await db.rf_cards.update_many({"exam": {"$exists": False}, "subject": "Biology"}, {"$set": {"exam": "NEET"}})
    await db.rf_cards.update_many({"exam": {"$exists": False}, "subject": {"$ne": "Biology"}}, {"$set": {"exam": "JEE"}})
    await sync_cards()
    from exam_migration import migrate_exam_data
    await migrate_exam_data(db)
    # Duel live channel must be a capped collection before any event is written (see duels.py tail()).
    from duels import EVENTS_BYTES, EVENTS_MAX
    if "rf_events" not in await db.list_collection_names():
        try:
            await db.create_collection("rf_events", capped=True, size=EVENTS_BYTES, max=EVENTS_MAX)
        except Exception:  # noqa: BLE001
            pass
    elif not (await db.rf_events.options()).get("capped"):
        await db.command("convertToCapped", "rf_events", size=EVENTS_BYTES)
    await db.rf_sessions.create_index([("status", 1), ("created_at", 1)])
    await daily_indexes(db)
    await db.rf_dreams.create_index("uid", unique=True)
    # One report per player per gang (reports are upserted on gang + player). Reports are never deleted at startup: if old
    # duplicate rows block the unique index, they are kept and the index waits (logged) until someone resolves them.
    try:
        await db.rf_gang_reports.create_index([("gang_id", 1), ("uid", 1)], unique=True)
    except OperationFailure as e:
        logger.warning("rf_gang_reports unique index not created (duplicate reports kept): %s", e)


@app.on_event("shutdown")
async def shutdown():
    await metadata_cache.close()
    if http:
        await http.close()
    await client.close()
