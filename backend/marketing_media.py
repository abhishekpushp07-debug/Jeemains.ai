"""Read-only, fixed allowlist for owner-approved public campaign assets."""
import asyncio
import hashlib
import json
import os
from pathlib import Path
import re
import tempfile

import httpx
from dotenv import load_dotenv
from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import Response, StreamingResponse

load_dotenv(Path(__file__).with_name(".env"))
router = APIRouter(prefix="/marketing")
MANIFEST = Path(__file__).with_name("marketing_manifest.json")
CACHE = Path(tempfile.gettempdir()) / "jeelive-public-campaign"
ALLOWED = {"vertical.mp4", "landscape.mp4", "vertical.webm", "landscape.webm", "poster-vertical.jpg", "poster-landscape.jpg", "launch-pack.zip", "vertical-mobile.mp4", "landscape-mobile.mp4"}
_locks = {name: asyncio.Lock() for name in ALLOWED}
_storage_key = None
_verified = set()


def asset_record(name):
    if name not in ALLOWED or not MANIFEST.exists():
        raise HTTPException(404, "Campaign asset not found")
    record = json.loads(MANIFEST.read_text()).get("assets", {}).get(name)
    if not record:
        raise HTTPException(404, "Campaign asset not found")
    return record


async def cached_asset(name, record):
    global _storage_key
    target = CACHE / (record["sha256"] + Path(name).suffix)
    async with _locks[name]:
        if target in _verified and target.exists() and target.stat().st_size == record["bytes"]:
            return target
        CACHE.mkdir(parents=True, exist_ok=True)
        storage = (os.environ.get("BRANDING_STORAGE_URL") or "").strip().rstrip("/")
        if not storage:
            raise HTTPException(503, "Campaign asset temporarily unavailable")
        try:
            async with httpx.AsyncClient(timeout=httpx.Timeout(120, connect=15)) as client:
                for attempt in range(2):
                    if not _storage_key:
                        response = await client.post(storage + "/init", json={"emergent_key": os.environ.get("EMERGENT_LLM_KEY")})
                        response.raise_for_status()
                        _storage_key = response.json()["storage_key"]
                    response = await client.get(storage + "/objects/" + record["path"], headers={"X-Storage-Key": _storage_key})
                    if response.status_code == 503 and attempt == 0:
                        _storage_key = None
                        continue
                    response.raise_for_status()
                    break
                data = response.content
                if len(data) != record["bytes"] or hashlib.sha256(data).hexdigest() != record["sha256"]:
                    raise ValueError("Campaign integrity mismatch")
                await asyncio.to_thread(target.write_bytes, data)
                _verified.add(target)
                return target
        except (httpx.HTTPError, KeyError, ValueError, OSError) as error:
            raise HTTPException(503, "Campaign asset temporarily unavailable", headers={"Retry-After": "30"}) from error


def byte_range(value, size):
    invalid = HTTPException(416, "Requested range not satisfiable", headers={"Content-Range": f"bytes */{size}", "Accept-Ranges": "bytes"})
    if len(value) > 128:
        raise invalid
    match = re.fullmatch(r"bytes=([0-9]*)-([0-9]*)", value.strip())
    if not match or not any(match.groups()):
        raise invalid
    first, last = match.groups()
    if not first:
        suffix = int(last)
        if suffix <= 0:
            raise invalid
        return max(0, size - suffix), size - 1
    start, end = int(first), min(int(last), size - 1) if last else size - 1
    if start >= size or end < start:
        raise invalid
    return start, end


async def chunks(path, start, length):
    handle = await asyncio.to_thread(path.open, "rb")
    try:
        await asyncio.to_thread(handle.seek, start)
        while length:
            data = await asyncio.to_thread(handle.read, min(length, 262144))
            if not data:
                break
            length -= len(data)
            yield data
    finally:
        await asyncio.to_thread(handle.close)


@router.api_route("/launch/{name}", methods=["GET", "HEAD"])
async def campaign_asset(name: str, request: Request):
    record = asset_record(name)
    etag = f'"{record["sha256"]}"'
    headers = {"Accept-Ranges": "bytes", "Cache-Control": "public, max-age=300", "ETag": etag, "X-Content-Type-Options": "nosniff"}
    if request.headers.get("if-none-match") == etag:
        return Response(status_code=304, headers=headers)
    size = record["bytes"]
    start, end, status = 0, size - 1, 200
    range_header = request.headers.get("range")
    if request.method == "GET" and range_header and request.headers.get("if-range", etag) == etag:
        start, end = byte_range(range_header, size)
        status = 206
        headers["Content-Range"] = f"bytes {start}-{end}/{size}"
    download = request.query_params.get("download") == "1" or name.endswith(".zip")
    disposition = "attachment" if download else "inline"
    # Download links are files, not a request to open an inline video decoder.
    media_type = "application/octet-stream" if download and record["content_type"].startswith("video/") else record["content_type"]
    headers["Content-Disposition"] = f'{disposition}; filename="{record["filename"]}"'
    headers["Content-Length"] = str(end - start + 1)
    if request.method == "HEAD":
        return Response(status_code=status, media_type=media_type, headers=headers)
    path = await cached_asset(name, record)
    return StreamingResponse(chunks(path, start, end - start + 1), status_code=status, media_type=media_type, headers=headers)