"""The Rapid Fire cards a phone keeps for itself (27 Nov 2026).

  GET /api/rf/bank?exam=JEE                               the list: one part per subject, with the hash of its bytes
  GET /api/rf/bank/part?exam=JEE&subject=Physics&h=<hash>  one subject's playable cards, the ones a sprint deals from

The app asks for the list when it opens and fetches only the parts whose hash it does not have. With the cards on the
phone a Solo Sprint is dealt there: at once on a slow line, and with no line at all (the round comes up afterwards,
POST /api/rf/sessions/offline in sprints.py). Signed-in students only, like every /api/rf door, and shed first when the
server is packed (load_guard.BACKGROUND): nothing here is urgent.

A part is built once per server copy and kept gzipped in memory (JEE: under 2 MB in all). Whether the cards changed is
looked at at most once a minute, from two things that are already at hand: the card files' own hashes (rf_meta
"card_files", written by card_bank.sync_cards: a card's words changed) and the ids a sprint deals from right now
(rapid_deck.selection_pool, kept in memory there: a card was added or retired). So the 16,000 cards are read again only
when something really changed (and in any case every half hour)."""
import asyncio
import gzip
import hashlib
import json
import time
from collections import Counter
from typing import Optional

from fastapi import APIRouter, Header, HTTPException
from fastapi.responses import Response

from database import ROOT_DIR
from exam_groups import SUBJECTS, Exam, require_active_exam
from rapid_deck import KINDS, selection_pool
from scope import CARD_COUNTS, CARD_SECONDS

KEEP = ("id", "chapter", "topic", "prompt", "formula", "options", "answer", "explain")  # + "diagram" when a card has one
CHECK_SECONDS, REBUILD_SECONDS = 60, 1800
_built: dict = {}  # exam -> {"mark", "checked", "at", "parts": {subject: part}}
_lock = asyncio.Lock()


def pack(exam: str, subject: str, cards: list, order: list) -> dict:
    """One subject's part: the same cards in the same order give the same bytes, so every server copy says the same hash."""
    rank = {chapter: i for i, chapter in enumerate(order)}
    cards = sorted(cards, key=lambda c: (rank.get(c["chapter"], len(rank)), c["chapter"], c["id"]))
    raw = json.dumps({"exam": exam, "subject": subject, "cards": cards}, ensure_ascii=False, separators=(",", ":")).encode()
    counts = Counter(c["chapter"] for c in cards)
    chapters = [{"name": c, "count": counts.get(c, 0)} for c in order] + [{"name": c, "count": n} for c, n in sorted(counts.items()) if c not in rank]
    return {"subject": subject, "hash": hashlib.sha256(raw).hexdigest()[:20], "cards": len(cards), "bytes": len(raw), "chapters": chapters, "gz": gzip.compress(raw, 6)}


async def _mark(db, exam: str) -> str:
    files = (await db.rf_meta.find_one({"_id": "card_files"}, {"_id": 0, "files": 1}) or {}).get("files") or {}
    mark = hashlib.sha1(json.dumps(files, sort_keys=True).encode())
    for subject in SUBJECTS[exam]:
        pool = await selection_pool(db, exam, subject)
        for chapter in sorted(pool):
            mark.update(("\n" + chapter + "\n" + "\n".join(sorted(row[0] for row in pool[chapter]))).encode())
    return mark.hexdigest()


async def parts(db, exam: str) -> dict:
    now, kept = time.monotonic(), _built.get(exam)
    if kept and now - kept["checked"] < CHECK_SECONDS:
        return kept["parts"]
    async with _lock:
        now, kept = time.monotonic(), _built.get(exam)
        if kept and now - kept["checked"] < CHECK_SECONDS:
            return kept["parts"]
        mark = await _mark(db, exam)
        if kept and kept["mark"] == mark and now - kept["at"] < REBUILD_SECONDS:
            kept["checked"] = now
            return kept["parts"]
        order = json.loads((ROOT_DIR / "rapidfire" / "chapters.json").read_text())
        made = {}
        for subject in SUBJECTS[exam]:
            cards = []
            async for c in db.rf_cards.find({"exam": exam, "subject": subject, "retired": {"$ne": True}}, {"_id": 0, "diagram": 1, **{k: 1 for k in KEEP}}).batch_size(2000):
                if c.get("diagram") and c["diagram"].get("kind") not in KINDS:
                    continue  # the same cards a sprint leaves out (rapid_deck.selection_pool)
                row = {"id": c["id"], "chapter": c["chapter"], "topic": c.get("topic") or "", "prompt": c["prompt"], "formula": c.get("formula") or "",
                       "options": c["options"], "answer": c["answer"], "explain": c.get("explain") or ""}
                if c.get("diagram"):
                    row["diagram"] = c["diagram"]
                cards.append(row)
            made[subject] = await asyncio.to_thread(pack, exam, subject, cards, order.get(subject, []))
        _built[exam] = {"mark": mark, "checked": now, "at": now, "parts": made}
        return made


def make_router(db, rf_user):
    r = APIRouter(prefix="/rf")

    @r.get("/bank")
    async def bank(exam: Optional[Exam] = None, x_rf_user: Optional[str] = Header(None)):
        rf_user(x_rf_user)
        exam = require_active_exam(exam)
        built = await parts(db, exam)
        return {"exam": exam, "seconds_per_card": CARD_SECONDS, "counts": list(CARD_COUNTS),
                "parts": [{k: p[k] for k in ("subject", "hash", "cards", "bytes", "chapters")} for p in built.values() if p["cards"]]}

    @r.get("/bank/part")
    async def bank_part(subject: str, h: str, exam: Optional[Exam] = None, x_rf_user: Optional[str] = Header(None)):
        rf_user(x_rf_user)
        exam = require_active_exam(exam)
        part = (await parts(db, exam)).get(subject)
        if not part or not part["cards"]:
            raise HTTPException(404, "No such part.")
        if h != part["hash"]:  # the cards changed after the phone read the list (or another server copy is a minute behind)
            raise HTTPException(409, "The cards changed. Ask for the list again.")
        return Response(part["gz"], media_type="application/json", headers={"Content-Encoding": "gzip", "Vary": "Accept-Encoding"})

    return r
