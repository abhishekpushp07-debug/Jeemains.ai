"""Stand-in for the jeelive.ai website API, ONLY for load-testing our own server (the /api/jl proxy) without touching
the real website or real students. Answers the mock-test calls the app makes with canned bodies of realistic size:
attempt ~58 KB JSON, question image ~450 KB PNG (measured on a real JEE Main PYQ paper), small JSON for saves.

    python tools/fake_website.py --port 9100 --latency-ms 60     # several copies may share the port (SO_REUSEPORT)
"""
import argparse
import json
import os
import time

from aiohttp import web

QUESTIONS = [{"id": f"q{i:03d}", "number": i + 1, "subject": ("Physics", "Chemistry", "Mathematics")[i // 25], "section": "A",
              "type": "mcq" if i % 25 < 20 else "integer", "text": "", "options": ["A", "B", "C", "D"], "topic": "Previous-year paper",
              "render_mode": "source", "solution_kind": "answer_key_only", "accessible_text": "x" * 600, "bonus": False,
              "typed_options": [], "source_option_labels": ["1", "2", "3", "4"], "asset_count": 1} for i in range(75)]
ASSET = b"\x89PNG\r\n\x1a\n" + os.urandom(450 * 1024)


def envelope(data):
    return {"data": data, "error": None, "meta": {"api_version": "1", "request_id": "fake"}}


def attempt_body(aid):
    return json.dumps(envelope({"id": aid, "title": "Load test paper", "exam": "JEE Main", "status": "active", "deadline": time.time() + 3600,
                                "server_now": time.time(), "answers": {}, "visited": [], "questions": QUESTIONS})).encode()


def make_app(latency):
    async def pause():
        if latency:
            import asyncio
            await asyncio.sleep(latency)

    async def login(request):
        await pause()
        r = web.json_response(envelope({"user": {"id": "load-user", "name": "Load"}}))
        r.set_cookie("jl_access", "a" * 40, httponly=True)
        r.set_cookie("jl_refresh", "r" * 40, httponly=True)
        return r

    async def me(request):
        await pause()
        return web.json_response(envelope({"user": {"id": "load-user", "name": "Load"}}))

    async def attempt(request):
        await pause()
        return web.Response(body=attempt_body(request.match_info["aid"]), content_type="application/json")

    async def asset(request):
        await pause()
        return web.Response(body=ASSET, content_type="image/png", headers={"Cache-Control": "private, no-store"})

    async def answer(request):
        await pause()
        body = await request.json()
        rev = int(body.get("revision", 1))
        return web.json_response(envelope({"accepted": {**body, "revision": rev}, "current_revision": rev, "server_now": time.time()}))

    async def small(request):
        await pause()
        await request.read()
        return web.json_response(envelope({"ok": True, "visited": [], "receipt": "fake", "server_now": time.time()}))

    app = web.Application()
    app.add_routes([web.post("/auth/phone", login), web.get("/auth/me", me), web.get("/auth/session", me),
                    web.get("/attempts/{aid}", attempt), web.get("/attempts/{aid}/results", attempt),
                    web.get("/attempts/{aid}/questions/{qid}/asset/{kind}/{i}", asset),
                    web.put("/attempts/{aid}/answers/{qid}", answer),
                    web.post("/attempts/{aid}/visit", small), web.post("/attempts/{aid}/submit", small)])
    return app


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--port", type=int, default=9100)
    ap.add_argument("--latency-ms", type=float, default=60, help="how long the website takes to answer each call")
    a = ap.parse_args()
    web.run_app(make_app(a.latency_ms / 1000), host="127.0.0.1", port=a.port, reuse_port=True, access_log=None, print=None)
