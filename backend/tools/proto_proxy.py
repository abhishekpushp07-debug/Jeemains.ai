"""Benchmark-only prototype (NOT used by the app): the same /api/jl pass-through as server.py forward_jeelive, but with
an aiohttp upstream client instead of httpx, to measure how much of the proxy's CPU the httpx connection pool costs.

    JEELIVE_API=http://127.0.0.1:9100 uvicorn tools.proto_proxy:app --port 8004 --workers 2
"""
import os

import aiohttp
from dotenv import load_dotenv
from fastapi import FastAPI, Header, Request
from fastapi.responses import Response
from pymongo import AsyncMongoClient

load_dotenv(os.path.join(os.path.dirname(__file__), "..", ".env"))
UP = os.environ["JEELIVE_API"].rstrip("/")
db = AsyncMongoClient(os.environ["MONGO_URL"], maxPoolSize=40)[os.environ["DB_NAME"]]
jars = db.jl_jars
app = FastAPI()
session: aiohttp.ClientSession | None = None


@app.on_event("startup")
async def start():
    global session
    session = aiohttp.ClientSession(connector=aiohttp.TCPConnector(limit=400, keepalive_timeout=45), timeout=aiohttp.ClientTimeout(total=28, connect=4),
                                    cookie_jar=aiohttp.DummyCookieJar(), auto_decompress=False)


@app.api_route("/api/jl/{path:path}", methods=["GET", "POST", "PUT"])
async def proxy(path: str, request: Request, x_jl_sid: str = Header(...)):
    jar = await jars.find_one({"sid": x_jl_sid}, {"_id": 0, "cookies": 1})
    headers = {"Accept": request.headers.get("accept", "application/json")}
    if request.headers.get("content-type"):
        headers["Content-Type"] = request.headers["content-type"]
    if jar and jar.get("cookies"):
        headers["Cookie"] = "; ".join(f"{k}={v}" for k, v in jar["cookies"].items())
    body = await request.body()
    async with session.request(request.method, f"{UP}/{path}", params=request.query_params, data=body or None, headers=headers) as r:
        content = await r.read()
        out = {k: r.headers[k] for k in ("content-type", "cache-control") if k in r.headers}
        return Response(content=content, status_code=r.status, headers=out)
