"""Public owner branding only. Never proxies student/source-paper assets."""
import asyncio
import hashlib
import logging
import os
from pathlib import Path

import httpx
from dotenv import load_dotenv
from fastapi import APIRouter, HTTPException
from fastapi.responses import Response

load_dotenv(Path(__file__).parent / ".env")
router = APIRouter(prefix="/brand")
STORAGE_URL = os.environ.get("BRANDING_STORAGE_URL", "").strip().rstrip("/")
LOGO_PATH = "jeelive-ai/uploads/brand/7d979c5b-5d97-4387-99f6-9c6760c17f9f.svg"
LOGO_SHA256 = "4cec3778c23c429e1be0186c71db65da8ceece01ba736a14ed560623560faff2"
ASSETS = {
    "logo": (LOGO_PATH, LOGO_SHA256, "image/svg+xml"),
    "jee": ("jeelive-ai/uploads/brand/65afe9e4-d263-4f1e-bc37-3f4dfe2a7efd.jpg", "78fed1d5429cd179237797887ca36111ac09d07adc6f258e426140d102185269", "image/jpeg"),
    "live": ("jeelive-ai/uploads/brand/a5267b5a-e17c-4318-8b94-312aae0517e3.jpg", "6119a369dc3e147d2641efe6723c2151eed614a2e3cc8cb4dfce6c0e42843e01", "image/jpeg"),
    "bitsat": ("jeelive-ai/uploads/brand/8117d2c8-4830-472a-b142-feb6527c2c73.jpg", "49a885034cefc4848cf42c5cbfea3fdbdce68f08a1638d6ec1250102e75642cb", "image/jpeg"),
    "comedk": ("jeelive-ai/uploads/brand/08fb078a-2e15-4af7-b928-a19a3ad5254e.jpg", "e24682ea5a92814c9b01fbe5a704614ba542004fc0ca1a70a2d16d8338e50028", "image/jpeg"),
}
_storage_key = None
_assets = {}
_lock = asyncio.Lock()


@router.on_event("startup")
async def warm_public_brand():
    # Branding must not delay or break academic/Rapid Fire startup.
    async def warm():
        try:
            await load_logo()
        except (httpx.HTTPError, ValueError, KeyError):
            logging.getLogger("branding").warning("Public brand asset warm-up deferred")
    asyncio.create_task(warm())


async def load_logo(name="logo"):
    global _storage_key
    if not STORAGE_URL:
        raise ValueError("BRANDING_STORAGE_URL is not configured")
    path, expected_hash, _ = ASSETS[name]
    async with _lock:
        if name in _assets:
            return _assets[name]
        async with httpx.AsyncClient(timeout=30) as client:
            for attempt in range(2):
                if not _storage_key:
                    response = await client.post(STORAGE_URL + "/init", json={"emergent_key": os.environ.get("EMERGENT_LLM_KEY")})
                    response.raise_for_status()
                    _storage_key = response.json()["storage_key"]
                response = await client.get(STORAGE_URL + "/objects/" + path, headers={"X-Storage-Key": _storage_key})
                if response.status_code == 503 and attempt == 0:
                    _storage_key = None
                    continue
                response.raise_for_status()
                if hashlib.sha256(response.content).hexdigest() != expected_hash:
                    raise ValueError("Original public artwork integrity check failed")
                _assets[name] = response.content
                return _assets[name]


@router.get("/logo.svg")
async def original_logo():
    return await public_asset_response("logo")


@router.get("/cards/{kind}.jpg")
async def original_card(kind: str):
    if kind not in {"jee", "live", "bitsat", "comedk"}:
        raise HTTPException(404, "Unknown card artwork")
    return await public_asset_response(kind)


async def public_asset_response(name):
    try:
        data = await load_logo(name)
    except (httpx.HTTPError, ValueError, KeyError) as error:
        # Don't expose provider responses or credentials.
        raise HTTPException(503, "Brand asset temporarily unavailable", headers={"Retry-After": "30"}) from error
    _, sha256, media_type = ASSETS[name]
    return Response(data, media_type=media_type, headers={"Cache-Control": "public, max-age=604800", "ETag": f'"{sha256}"', "X-Content-Type-Options": "nosniff"})