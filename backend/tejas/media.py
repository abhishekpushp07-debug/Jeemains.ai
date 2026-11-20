"""Question pictures of a paper as signed, public, cache-friendly parts, so a CDN serves the exam-start rush instead of the API.
A link is handed out only to a student whose paper is open; it carries no answers and expires within two days."""

import asyncio, base64, hashlib, hmac, json, os, re, time
from fastapi import APIRouter, HTTPException, Response
from starlette.concurrency import run_in_threadpool
from .cache import ByteCache
from .db import files
from .derivatives import render_crop
from .packs import entry_for

router = APIRouter(prefix="/api")
PART, DAY = 12, 86400
CDN = os.environ.get("MEDIA_CDN_URL", "").rstrip("/")
_KEY = hashlib.sha256(b"tejas-media-v1:" + os.environ["JWT_SECRET"].encode()).digest()
_PACK = re.compile(r"[0-9a-f]{64}")
_NAME = re.compile(r"(\d{1,4})-(\d{1,2})-([0-3])-(\d{10})-([A-Za-z0-9_-]{22})\.bin")
_parts = ByteCache(64 * 1024 * 1024)
_flights = {}
stats = {"links": 0, "served": 0, "built": 0, "coalesced": 0, "rejected": 0}


def picture_refs(questions, bonus_open, cut=False):
    """Pictures of a paper in order: (question id, index, ref, kind). cut=True gives a cut question's pieces instead of its whole picture."""
    out = []
    for q in questions:
        if q.get("bonus") and not bonus_open:
            continue
        pieces = q.get("c_refs") if cut else None
        out += [(q["id"], i, r, "piece" if pieces else "question") for i, r in enumerate(pieces or q.get("q_refs", []))]
    return out


def assemble(total, found):
    items = [{"question_id": qid, "index": i, "size": len(b), **({"kind": kind} if kind != "question" else {})} for qid, i, b, kind in found]
    head = json.dumps({"total": total, "items": items}).encode()
    return len(head).to_bytes(4, "big") + head + b"".join(b for _, _, b, _ in found)


def sign(pack_id, offset, limit, bonus, exp):
    raw = hmac.new(_KEY, f"{pack_id}.{offset}.{limit}.{bonus}.{exp}".encode(), hashlib.sha256).digest()
    return base64.urlsafe_b64encode(raw[:16]).decode().rstrip("=")


async def pack_links(a, cut=False):
    """Every student of one paper on one day gets the same links, so the CDN fetches each part from the server only once."""
    bonus = int(bool(a.get("bonus_unlocked_at"))) | (2 if cut else 0)
    total = len(picture_refs((await entry_for(a["pack_id"])).questions, bonus & 1, cut))
    exp = (int(a["_database_now"] // DAY) + 2) * DAY
    base = f"{CDN}/api/media/pack/{a['pack_id']}"
    stats["links"] += 1
    return {"total": total, "limit": PART, "cdn": bool(CDN), "expires_at": exp,
            "parts": [f"{base}/{o}-{PART}-{bonus}-{exp}-{sign(a['pack_id'], o, PART, bonus, exp)}.bin" for o in range(0, total, PART)]}


def _render(sources, part):
    found = []
    for qid, i, r, kind in part:
        try:
            found.append((qid, i, render_crop(sources[r["file_id"]], r), kind))
        except Exception:
            pass
    return found


async def _build(pack_id, offset, limit, bonus):
    refs = picture_refs((await entry_for(pack_id)).questions, bonus & 1, bool(bonus & 2))
    part = refs[offset:offset + limit]
    if not part:
        return None, False
    ids = list({r["file_id"] for _, _, r, _ in part})
    sources = {f["id"]: f async for f in files.find({"id": {"$in": ids}, "is_deleted": {"$ne": True}}, {"_id": 0})}
    found = await run_in_threadpool(_render, sources, [p for p in part if p[2]["file_id"] in sources])
    body, complete = assemble(len(refs), found), len(found) == len(part)
    if complete:
        _parts.put(f"{pack_id}.{offset}.{limit}.{bonus}", body)
    stats["built"] += 1
    return body, complete


async def part_bytes(pack_id, offset, limit, bonus):
    key = f"{pack_id}.{offset}.{limit}.{bonus}"
    body = _parts.get(key)
    if body is not None:
        return body, True
    flight = _flights.get(key)
    if flight is None:
        flight = _flights[key] = asyncio.ensure_future(_build(pack_id, offset, limit, bonus))
        flight.add_done_callback(lambda _: _flights.pop(key, None))
    else:
        stats["coalesced"] += 1
    return await asyncio.shield(flight)


@router.get("/media/probe.bin")
async def media_probe():
    """Fixed public bytes to check a CDN in front of /api/media: fetch twice through the CDN, the second answer should be a cache HIT."""
    return Response(b"jeelive-media-probe-v1\n", media_type="application/octet-stream", headers={
        "Cache-Control": "public, max-age=300, s-maxage=3600", "Access-Control-Allow-Origin": "*",
        "Cross-Origin-Resource-Policy": "cross-origin", "X-Media-CDN": CDN or "same-server"})


@router.get("/media/pack/{pack_id}/{name}")
async def media_pack(pack_id: str, name: str):
    m = _NAME.fullmatch(name)
    t = time.time()
    if not _PACK.fullmatch(pack_id) or not m:
        stats["rejected"] += 1
        raise HTTPException(404, "Picture not found.")
    offset, limit, bonus, exp, sig = int(m[1]), int(m[2]), int(m[3]), int(m[4]), m[5]
    if not hmac.compare_digest(sig, sign(pack_id, offset, limit, bonus, exp)) or not 1 <= limit <= 16 or not t < exp <= t + 3 * DAY:
        stats["rejected"] += 1
        raise HTTPException(404, "This picture link is not valid. Reload the paper to get fresh links.")
    body, complete = await part_bytes(pack_id, offset, limit, bonus)
    if body is None:
        raise HTTPException(404, "Picture not found.")
    stats["served"] += 1
    age = min(DAY, int(exp - t))
    # A part with a picture that could not render is never cached, so a CDN never keeps a broken copy.
    cache = f"public, max-age={age}, s-maxage={age}, immutable" if complete else "no-store"
    return Response(body, media_type="application/octet-stream", headers={
        "Cache-Control": cache, "ETag": f'"{sig}"', "Access-Control-Allow-Origin": "*",
        "Cross-Origin-Resource-Policy": "cross-origin"})
