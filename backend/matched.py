"""Matched: the JEE Main questions that matched ours (GET /api/matched, GET /api/matched/<shift>), open to everyone.

After a JEE Main shift, the owner's side (a matching machine and a super-admin page, built later) writes ONE document
per shift into the `matched_shifts` collection: the questions of that shift that matched ours, each with the question(s)
of ours it matched. This file only READS that collection; nothing here writes to it. The document is described in
memory/MATCHED_CONTRACT.md.

The app in a student's hand cannot be changed without a new build, so this server is the adapter between whatever is
written into the collection and what the app can draw: every document goes through `shape_shift`, and only the fields
the app knows, in the shapes and sizes it can show, leave the server. A badly made question is left out (and not
counted); it can never break the screen. A shift is shown only while its `published` is true.

This file also says when Home shows the Matched card in place of the All India series card (`card_on`, asked for by
app_switches.py): from the day after the series' last day. That day comes from the website's own public schedule, read
here every 15 minutes and kept in Mongo, so a restart or a website outage still knows it."""
import asyncio
import logging
import os
import re
import time
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, HTTPException, Path

from fast_json import FastJSONResponse
from jl_transport import canonical_request
from metadata_cache import MetadataCache

logger = logging.getLogger("jeelive")
IST = timezone(timedelta(hours=5, minutes=30))
SHIFT_ID = r"^\d{4}-\d{2}-\d{2}-s[1-9]$"  # the exam day in India + the shift: 2027-01-25-s1
DAY = re.compile(r"^\d{4}-\d{2}-\d{2}$")
SUBJECTS = ("Physics", "Chemistry", "Mathematics")
LETTERS = "ABCDEF"
MAX_SHIFTS, MAX_ITEMS, MAX_OURS, MAX_OPTIONS, MAX_IMAGES = 200, 150, 4, 6, 6
PUBLIC = {"Cache-Control": "public, max-age=60"}
SERIES_META = "matched:aits_last_day"
SERIES_PATH = "series/all-india-jee"
# Its own small cache: the Rapid Fire one is sized for the card pools and must not lose a pool to a Matched shift.
cache = MetadataCache()


def _text(value, limit: int) -> str:
    return value.replace("\x00", "").strip()[:limit] if isinstance(value, str) else ""


def _number(value, top: int):
    return value if isinstance(value, int) and not isinstance(value, bool) and 0 < value <= top else None


def _images(value) -> list:
    """Pictures as {url, w, h}: https only (the page is public, so is the picture); w and h only when both are given."""
    out = []
    for row in value if isinstance(value, list) else []:
        url = _text(row.get("url") if isinstance(row, dict) else row, 600)
        if not url.startswith("https://") or re.search(r"\s", url):
            continue
        w, h = (_number(row.get("w"), 20000), _number(row.get("h"), 20000)) if isinstance(row, dict) else (None, None)
        out.append({"url": url, "w": w if w and h else None, "h": h if w and h else None})
        if len(out) == MAX_IMAGES:
            break
    return out


def _options(value) -> list:
    """Option texts in their order. Either every option has words or none is shown: one left out would move the letters."""
    options = [_text(o, 1500) for o in (value if isinstance(value, list) else [])[:MAX_OPTIONS]]
    return options if all(options) else []


def _right(value, count: int):
    """Which option is right, as its place in the list from 0. Written as the place from 1 (2) or as its letter ("B")."""
    if isinstance(value, str) and len(value.strip()) == 1:
        place = LETTERS.find(value.strip().upper())
    elif isinstance(value, int) and not isinstance(value, bool):
        place = value - 1
    else:
        return None
    return place if 0 <= place < count else None


def _side(value, ours: bool = False):
    """One question (the JEE one, or one of ours): its words, options and pictures, and its solution when given (which
    option is right, the answer in words, the worked solution and its pictures). None when there is nothing to show."""
    if not isinstance(value, dict):
        return None
    options = _options(value.get("options"))
    side = {"text": _text(value.get("text"), 6000), "options": options, "images": _images(value.get("images")),
            "correct": _right(value.get("correct"), len(options)), "answer": _text(value.get("answer"), 300),
            "solution": _text(value.get("solution"), 6000), "solution_images": _images(value.get("solution_images"))}
    if not side["text"] and not side["images"]:
        return None
    if ours:
        side.update(source=_text(value.get("source"), 80), tag=_text(value.get("tag"), 40))
    return side


def shape_item(row):
    """One matched question: the JEE question and at least one of ours. None when either is missing."""
    if not isinstance(row, dict):
        return None
    jee, ours = _side(row.get("jee")), row.get("ours")
    ours = [s for s in (_side(o, True) for o in (ours if isinstance(ours, list) else [ours])[:MAX_OURS]) if s]
    if not jee or not ours:
        return None
    return {"n": _number(row.get("n"), 300), "subject": row.get("subject") if row.get("subject") in SUBJECTS else "",
            "chapter": _text(row.get("chapter"), 80), "jee": jee, "ours": ours}


def shape_shift(doc):
    """A shift as the app shows it; the day and the shift number come from its id. None for a document that is not a shift."""
    sid = doc.get("_id") if isinstance(doc, dict) else None
    if not isinstance(sid, str) or not re.match(SHIFT_ID, sid):
        return None
    try:
        datetime.strptime(sid[:10], "%Y-%m-%d")
    except ValueError:
        return None
    rows = doc.get("items") if isinstance(doc.get("items"), list) else []
    # In the paper's order; questions without a number keep the order they were written in, after the numbered ones.
    items = sorted((i for i in (shape_item(r) for r in rows[:MAX_ITEMS]) if i), key=lambda i: (i["n"] is None, i["n"] or 0))
    asked, stamp = _number(doc.get("asked"), 300), doc.get("updated_at")
    return {"id": sid, "day": sid[:10], "shift": int(sid[-1]), "asked": asked if asked and asked >= len(items) else None, "matched": len(items),
            "subjects": [{"name": s, "n": n} for s in SUBJECTS if (n := sum(1 for i in items if i["subject"] == s))],
            "updated_at": int(stamp) if isinstance(stamp, (int, float)) and not isinstance(stamp, bool) and stamp > 0 else 0, "items": items}


async def load_index(db) -> dict:
    """Every published shift, newest first, without its questions."""
    docs = await db.matched_shifts.find({"published": True}).sort("_id", -1).to_list(MAX_SHIFTS)
    shifts = [s for s in (shape_shift(d) for d in docs) if s]
    return {"total": sum(s["matched"] for s in shifts), "updated_at": max((s["updated_at"] for s in shifts), default=0),
            "shifts": [{k: v for k, v in s.items() if k != "items"} for s in shifts]}


async def load_shift(db, shift_id: str):
    doc = await db.matched_shifts.find_one({"_id": shift_id, "published": True})
    return shape_shift(doc) if doc else None


def make_router(db):
    r = APIRouter()

    @r.get("/matched")
    async def index():
        data, _ = await cache.get_or_load("index", lambda: load_index(db), ttl=60)
        return FastJSONResponse(data, headers=PUBLIC)

    @r.get("/matched/{shift_id}")
    async def shift(shift_id: str = Path(..., pattern=SHIFT_ID)):
        data, _ = await cache.get_or_load("shift:" + shift_id, lambda: load_shift(db, shift_id), ttl=60)
        if not data:
            raise HTTPException(404, "This shift is not here.")
        return FastJSONResponse(data, headers=PUBLIC)

    return r


# ---- When Home shows the Matched card -------------------------------------------------------------------------------
_series = {"last": None, "loaded": False}  # the All India series' last day, as this process last knew it
MODES = ("on", "off", "auto")
CARD_META = "matched:card"  # rf_meta: {"_id": "matched:card", "value": "on" | "off" | "auto"}
_owner = {"value": None, "read": float("-inf")}


def ist_day() -> str:
    return datetime.now(IST).strftime("%Y-%m-%d")


def over(last, today: str) -> bool:
    """The series is over from the day after its last day."""
    return bool(last) and today > last


async def _load_copy(db):
    row = await db.rf_meta.find_one({"_id": SERIES_META}, {"value": 1})
    value = row.get("value") if row else None
    if not _series["last"] and isinstance(value, str) and DAY.match(value):
        _series["last"] = value
    _series["loaded"] = True


def card_mode(owner, code: str) -> str:
    """The switch kept in Mongo wins over the one in the code when it is one of the three words."""
    return owner if owner in MODES else code


async def _owner_mode(db):
    """The switch kept in Mongo (rf_meta, CARD_META), read again at most once a minute."""
    if time.monotonic() - _owner["read"] > 60:
        row = await db.rf_meta.find_one({"_id": CARD_META}, {"value": 1})
        _owner.update(value=row.get("value") if row else None, read=time.monotonic())
    return _owner["value"]


async def card_on(db, code: str) -> bool:
    """`code` is the switch in the code (app_switches.MATCHED_CARD): "on", "off", or "auto" = from the day after the series
    ends. The same three words kept in Mongo win over it, so the card can be switched without a server publish.
    Never waits for the website and never fails: when nothing is known yet the answer is no."""
    mode = code
    try:
        mode = card_mode(await _owner_mode(db), code)
        if mode == "auto" and not _series["loaded"]:
            await _load_copy(db)
    except Exception as e:  # noqa: BLE001 - the switches answer also carries other switches; it must still go out
        logger.warning("matched: card switch not read: %s", type(e).__name__)
    return over(_series["last"], ist_day()) if mode == "auto" else mode == "on"


async def refresh_series(db, client) -> bool:
    """Reads the series' last day from the website's public schedule; writes it to Mongo when it changed."""
    base, http = os.environ.get("JEELIVE_API", "").rstrip("/"), client()
    if not base or http is None:
        return False
    r = await canonical_request(http, "GET", f"{base}/{SERIES_PATH}", path=SERIES_PATH, params=None, body=None, headers={"Accept": "application/json"})
    if not r.is_success:
        return False
    body = r.json()
    data = body.get("data") if isinstance(body, dict) and isinstance(body.get("data"), dict) else body
    last = data.get("last_date") if isinstance(data, dict) else None
    if not isinstance(last, str) or not DAY.match(last):
        return False
    if last != _series["last"]:
        _series["last"] = last
        await db.rf_meta.update_one({"_id": SERIES_META}, {"$set": {"value": last, "ts": time.time()}}, upsert=True)
    _series["loaded"] = True
    return True


async def watch_series(db, client):
    """Started once per server process: keeps the series' last day current (every 15 minutes; sooner after a miss)."""
    while True:
        ok = False
        try:
            if not _series["loaded"]:
                await _load_copy(db)
            ok = await refresh_series(db, client)
        except asyncio.CancelledError:
            raise
        except Exception as e:  # noqa: BLE001 - the website or Mongo did not answer: the last known day stays in use
            logger.warning("matched: series schedule not read: %s", type(e).__name__)
        await asyncio.sleep(900 if ok else 120)
