"""Student Choice: the question bank a student builds a paper from (GET /api/choice/bank, GET /api/choice/chapters/<id>).

A student picks chapters and then questions (shown without options), or asks for a random mock; jeelive.ai then makes a
real paper of them, which is started, solved, marked and analysed like every other paper. The questions live on
jeelive.ai. This file reads its two doors (the bank: subjects and their chapters; one chapter's questions without
options and answers), keeps each answer for a few minutes, and hands the app only what it can draw, in the shape it
knows: the app in a student's hand cannot be changed without a new build, this server can. Making the paper is the
student's own request and goes through the website proxy (/api/jl/choice/papers), not through here.

For signed-in students only: a request needs the same short-lived grant Rapid Fire uses (rf_access.py: made only from a
session the website verified), and the website's doors are read with that student's own website session. The answer is
the same for every student, so one student's read serves the others for a few minutes.

The doors are described in memory/WEBSITE_CHOICE_NOTE.md. Until the website has them the bank answers {"ready": false}
and the app says so.

For the owner's eyes on the preview only: with the row rf_meta {"_id": "choice:sample", "value": true}, and the website's
doors still missing, the bank and the questions come from the `choice_sample` collection (made-up questions written by
backend/tests/choice_sample.py). The production database has no such row."""
import os
import re
import time

from fastapi import APIRouter, HTTPException, Path, Request
from starlette.responses import JSONResponse

from fast_json import FastJSONResponse
from jl_transport import canonical_request
from matched import ID, _id, _text, site_data
from metadata_cache import MetadataCache
from rf_access import verified_grant

SUBJECTS = ("Physics", "Chemistry", "Mathematics")
TYPES = ("mcq", "integer")
# The owner's rules (26 Nov 2026): a paper has at most 75 questions; +4 for a right answer, -1 for a wrong one; time is
# given per question by its subject, so that 25 + 25 + 25 questions get 60 + 40 + 80 = 180 minutes.
MAX_QUESTIONS = 75
MARKS = {"correct": 4, "wrong": -1}
MINUTES = {"Physics": 2.4, "Chemistry": 1.6, "Mathematics": 3.2}
MAX_CHAPTERS, MAX_ITEMS, MAX_PAGES, MAX_STEM = 120, 300, 6, 4
PRIVATE = {"Cache-Control": "private, max-age=60"}
BUSY = "The website is not answering right now. Please try again in a moment."
SAMPLE_META = "choice:sample"
cache = MetadataCache()
_sample = {"value": False, "read": float("-inf")}


def _count(value, top: int) -> int:
    return value if isinstance(value, int) and not isinstance(value, bool) and 0 <= value <= top else 0


def _size(value):
    """A picture's width or height in print points (the website's pieces are sized so): a positive number."""
    return round(float(value), 1) if isinstance(value, (int, float)) and not isinstance(value, bool) and 0 < value <= 20000 else None


def _stem(value) -> list:
    """The question's own pictures (never its options), as {url, w, h}: https only; w and h only when both are given."""
    out = []
    for row in value if isinstance(value, list) else []:
        url = _text(row.get("url") if isinstance(row, dict) else row, 900)
        if not url.startswith("https://") or re.search(r"\s", url):
            continue
        w, h = (_size(row.get("w")), _size(row.get("h"))) if isinstance(row, dict) else (None, None)
        out.append({"url": url, "w": w if w and h else None, "h": h if w and h else None})
        if len(out) == MAX_STEM:
            break
    return out


def shape_chapters(rows) -> list:
    """A subject's chapters in the website's order: each needs an id, a name and at least one question."""
    out, seen = [], set()
    for row in rows if isinstance(rows, list) else []:
        if not isinstance(row, dict):
            continue
        cid, title, count = _id(row.get("id")), _text(row.get("title"), 120), _count(row.get("count"), 5000)
        if not cid or cid in seen or not title or not count or len(out) == MAX_CHAPTERS:
            continue
        seen.add(cid)
        out.append({"id": cid, "n": _count(row.get("number"), 999) or None, "title": title, "count": count,
                    "mcq": _count(row.get("mcq"), count), "integer": _count(row.get("integer"), count)})
    return out


def shape_bank(data, sample: bool = False):
    """The bank as the app shows it. None when it has no chapter at all (then there is nothing to choose from)."""
    if not isinstance(data, dict):
        return None
    subjects = []
    for name in SUBJECTS:  # always Physics, Chemistry, Mathematics, in that order; anything else is not shown
        row = next((s for s in data.get("subjects") or [] if isinstance(s, dict) and s.get("name") == name), None)
        chapters = shape_chapters(row.get("chapters")) if row else []
        if chapters:
            subjects.append({"name": name, "chapters": chapters})
    if not subjects:
        return None
    top, each, per = data.get("max_questions"), data.get("max_per_subject"), data.get("minutes_per_question")
    minutes = {s: float(per[s]) if isinstance(per, dict) and isinstance(per.get(s), (int, float)) and not isinstance(per[s], bool) and 0.5 <= per[s] <= 10 else MINUTES[s]
               for s in SUBJECTS}
    return {"ready": True, "sample": sample, "exam": _text(data.get("exam"), 40) or "JEE Main",
            # The website may lower the top (never raise it past the owner's 75), and may add a top per subject.
            "max_questions": _count(top, MAX_QUESTIONS) or MAX_QUESTIONS, "max_per_subject": _count(each, MAX_QUESTIONS) or None,
            "minutes": minutes, "marks": MARKS, "subjects": subjects}


def shape_question(row):
    """One question for the list: its id, its number in the chapter, its kind, and its words or its pictures. Never its
    options, its answer or its solution: whatever else the website sends stays here."""
    if not isinstance(row, dict):
        return None
    qid, text, stem = _id(row.get("id")), _text(row.get("text"), 3000), _stem(row.get("stem"))
    if not qid or (not text and not stem):
        return None
    return {"id": qid, "n": _count(row.get("number"), 9999) or None, "type": row.get("type") if row.get("type") in TYPES else "mcq", "text": text, "stem": stem}


def shape_chapter(chapter_id: str, pages: list):
    """A chapter's questions from the website's pages (the first page names the chapter). None when there is none."""
    head = pages[0].get("chapter") if pages and isinstance(pages[0], dict) and isinstance(pages[0].get("chapter"), dict) else {}
    items, seen = [], set()
    for page in pages:
        for row in (page.get("items") if isinstance(page, dict) else None) or []:
            q = shape_question(row)
            if q and q["id"] not in seen and len(items) < MAX_ITEMS:
                seen.add(q["id"])
                items.append(q)
    if not items:
        return None
    return {"id": chapter_id, "title": _text(head.get("title"), 120), "subject": head.get("subject") if head.get("subject") in SUBJECTS else "",
            "total": len(items), "items": items}


def minutes_for(counts: dict, per: dict = MINUTES) -> int:
    """The time a paper gets: each question brings its subject's minutes; the sum is rounded up to a whole minute."""
    total = sum(per.get(s, MINUTES["Physics"]) * n for s, n in counts.items())
    return int(-(-round(total, 4) // 1))


class NeedsSession(Exception):
    """The website did not accept this student's session (its access cookie has run out): the app renews it and asks again."""


def make_router(db, client):
    r = APIRouter()

    async def student(request: Request) -> str:
        """The session handle of the signed-in student who asks. 401 for anyone else."""
        try:
            grant = await verified_grant(db, request.headers.get("authorization", "").removeprefix("Bearer "))
        except HTTPException:
            raise HTTPException(401, "Please sign in again.")
        return grant.get("sid") or ""

    async def site(sid: str, path: str, params=None):
        """One read of a website door as this student: (status, its answer). Only the access cookie is sent, so the
        website can never rotate the student's session here."""
        base, http = os.environ.get("JEELIVE_API", "").rstrip("/"), client()
        if not base or http is None:
            raise HTTPException(503, BUSY)
        jar = await db.jl_jars.find_one({"sid": sid}, {"_id": 0, "cookies.access_token": 1}) if sid else None
        cookie = ((jar or {}).get("cookies") or {}).get("access_token")
        headers = {"Accept": "application/json"}
        if isinstance(cookie, str) and cookie and not re.search(r"[\r\n;]", cookie):
            headers["Cookie"] = "access_token=" + cookie
        res = await canonical_request(http, "GET", f"{base}/{path}", path=path, params=params, body=None, headers=headers)
        if res.status_code in (401, 403):
            raise NeedsSession()
        try:
            return res.status_code, site_data(res.json()) if res.is_success else None
        except ValueError:
            return res.status_code, None

    async def sample_on() -> bool:
        if time.monotonic() - _sample["read"] > 60:
            row = await db.rf_meta.find_one({"_id": SAMPLE_META}, {"value": 1})
            _sample.update(value=bool(row and row.get("value") is True), read=time.monotonic())
        return _sample["value"]

    async def sample_bank():
        docs = await db.choice_sample.find({}, {"questions.text": 0, "questions.stem": 0}).sort("n", 1).to_list(MAX_CHAPTERS)
        rows = [{"name": s, "chapters": [{"id": d["_id"], "number": d.get("n"), "title": d.get("title"), "count": len(d.get("questions") or []),
                                          "mcq": sum(1 for q in d.get("questions") or [] if q.get("type") != "integer"),
                                          "integer": sum(1 for q in d.get("questions") or [] if q.get("type") == "integer")}
                                         for d in docs if d.get("subject") == s]} for s in SUBJECTS]
        return shape_bank({"exam": "JEE Main", "subjects": rows}, sample=True)

    async def load_bank(sid: str):
        status, data = await site(sid, "choice/bank", {"exam": "jee-main"})
        bank = shape_bank(data) if status == 200 else None
        if bank:
            return bank
        if status in (404, 405) and await sample_on():  # the website has no such door yet, and this is the owner's preview
            return await sample_bank() or {"ready": False}
        if status >= 500:
            raise HTTPException(503, BUSY)
        return {"ready": False}

    async def load_chapter(sid: str, chapter_id: str):
        pages = []
        for number in range(1, MAX_PAGES + 1):
            status, data = await site(sid, f"choice/chapters/{chapter_id}/questions", {"page": str(number)})
            if status != 200 or not isinstance(data, dict):
                if number == 1 and status in (404, 405) and await sample_on():
                    doc = await db.choice_sample.find_one({"_id": chapter_id})
                    return shape_chapter(chapter_id, [{"chapter": doc, "items": [{**q, "number": q.get("n")} for q in doc.get("questions") or []]}]) if doc else None
                if status >= 500:
                    raise HTTPException(503, BUSY)
                break
            pages.append(data)
            if number >= _count(data.get("pages"), MAX_PAGES):
                break
        return shape_chapter(chapter_id, pages) if pages else None

    async def answer(request: Request, key: str, load, ttl: int):
        sid = await student(request)
        try:
            data, _ = await cache.get_or_load(key, lambda: load(sid), ttl=ttl)
        except NeedsSession:
            return JSONResponse({"detail": "Please sign in again.", "code": "website_session"}, status_code=401, headers={"Cache-Control": "no-store"})
        return data

    @r.get("/choice/bank")
    async def bank(request: Request):
        data = await answer(request, "bank", load_bank, 60)
        return data if isinstance(data, JSONResponse) else FastJSONResponse(data, headers=PRIVATE)

    @r.get("/choice/chapters/{chapter_id}")
    async def chapter(request: Request, chapter_id: str = Path(..., pattern=ID)):
        # Kept for five minutes: far less than the day the website's picture links live.
        data = await answer(request, "chapter:" + chapter_id, lambda sid: load_chapter(sid, chapter_id), 300)
        if isinstance(data, JSONResponse):
            return data
        if not data:
            raise HTTPException(404, "This chapter has no questions to choose from.")
        return FastJSONResponse(data, headers=PRIVATE)

    return r
