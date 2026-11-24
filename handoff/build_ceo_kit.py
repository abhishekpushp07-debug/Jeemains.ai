"""Builds the CEO dashboard hand-off kit: one small ZIP for the agent that builds the separate CEO dashboard project.

Run:  cd /app/backend && python ../handoff/build_ceo_kit.py
The documents are the ones kept in /app/memory (one source). The two sample answers are real in shape; every personal
value in them is masked. No token and no phone number is written into the kit.
"""
import asyncio
import json
import os
import shutil
import sys
import zipfile
from pathlib import Path

ROOT = Path("/app")
BACK = ROOT / "backend"
KIT = ROOT / "handoff" / "JEELIVE_CEO_Dashboard_Handoff"
ZIP = ROOT / "handoff" / "JEELIVE_CEO_Dashboard_Handoff.zip"
sys.path.insert(0, str(BACK))

CHECK = '''#!/usr/bin/env bash
# Proves the app's CEO API answers. The token is typed here by the owner; it is never written into a file.
#   BASE=https://jeelive-mobile.emergent.host/api  TOKEN=...  bash check_ceo_api.sh
set -u
: "${BASE:?set BASE to the app server address ending in /api}"
: "${TOKEN:?set TOKEN to the CEO_API_TOKEN value}"
code() { curl -s -o /dev/null -w "%{http_code}" "$@"; }
echo "no token          -> $(code "$BASE/ceo/overview")   (401 = closed, as it should be; 503 = token not set on that server; 404 = that server is not published yet)"
echo "wrong token       -> $(code -H "Authorization: Bearer wrong" "$BASE/ceo/overview")   (401)"
echo "overview          -> $(code -H "Authorization: Bearer $TOKEN" "$BASE/ceo/overview")   (200)"
echo "users, 5 a page   -> $(code -H "Authorization: Bearer $TOKEN" "$BASE/ceo/users?limit=5")   (200)"
curl -s -H "Authorization: Bearer $TOKEN" "$BASE/ceo/overview"; echo
'''


async def samples():
    """Real answers from this server's CEO API with a one-off local token; names, ids and codes are masked."""
    from dotenv import load_dotenv
    load_dotenv(BACK / ".env")
    os.environ["CEO_API_TOKEN"] = token = "kit-build-" + os.urandom(16).hex()  # this process only
    import httpx
    from fastapi import FastAPI
    from motor.motor_asyncio import AsyncIOMotorClient
    import ceo_api
    db = AsyncIOMotorClient(os.environ["MONGO_URL"])[os.environ["DB_NAME"]]
    app = FastAPI()
    app.include_router(ceo_api.make_router(db), prefix="/api")
    head = {"Authorization": f"Bearer {token}"}
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://kit") as c:
        overview = (await c.get("/api/ceo/overview", headers=head)).json()
        users = (await c.get("/api/ceo/users", headers=head, params={"limit": 3})).json()
        closed = (await c.get("/api/ceo/overview")).status_code
    for i, row in enumerate(users["items"], 1):
        row.update(uid=f"<canonical user id {i}>", name=f"<student {i}>", player_code=f"P<code {i}>", phone_last4=None)
    assert closed == 401
    return overview, users


def main():
    if KIT.exists():
        shutil.rmtree(KIT)
    (KIT / "app_server_reference").mkdir(parents=True)
    (KIT / "examples").mkdir()
    shutil.copy2(ROOT / "memory" / "CEO_DASHBOARD.md", KIT / "START_HERE_CEO_DASHBOARD.md")
    shutil.copy2(ROOT / "memory" / "WEBSITE_AGENT_BRIEF.md", KIT / "WHO_BUILDS_WHAT.md")
    shutil.copy2(BACK / "ceo_api.py", KIT / "app_server_reference" / "ceo_api.py")
    overview, users = asyncio.run(samples())
    note = "Shape of a real answer from the app server. Names, ids and codes are masked; never show these numbers, call the server."
    for name, url, body in (("overview", "/api/ceo/overview", overview), ("users_page", "/api/ceo/users?limit=3", users)):
        (KIT / "examples" / f"{name}.json").write_text(json.dumps(
            {"note": note, "request": {"method": "GET", "url": url, "headers": {"Authorization": "Bearer <CEO_API_TOKEN>"}}, "response": body},
            ensure_ascii=False, indent=2), encoding="utf-8")
    (KIT / "check_ceo_api.sh").write_text(CHECK, encoding="utf-8")
    (KIT / "README.md").write_text(
        "# JEELIVE.AI · CEO dashboard hand-off kit\n\n"
        "For the agent building the separate CEO dashboard project. Read in this order:\n\n"
        "1. `START_HERE_CEO_DASHBOARD.md` — the two servers, the app's CEO API, what to track and from where, how to build it, privacy.\n"
        "2. `WHO_BUILDS_WHAT.md` — the ownership table of the three projects (app, website, dashboard) and what the website adds.\n"
        "3. `examples/` — two real-shaped answers of the app's CEO API (personal values masked).\n"
        "4. `app_server_reference/ceo_api.py` — the app server's code for those two endpoints (read-only reference; do not copy it into the dashboard).\n"
        "5. `check_ceo_api.sh` — four curl checks once you have the address and the token.\n\n"
        "The dashboard needs two secrets, entered by the owner in the dashboard project (never in code or chat): the app's "
        "`CEO_API_TOKEN`, and the website's own owner token. Contacts (phone numbers) come only from the website.\n",
        encoding="utf-8")
    text = "".join(f.read_text(encoding="utf-8") for f in KIT.rglob("*") if f.is_file())
    assert "kit-build-" not in text, "the one-off token leaked into the kit"
    if ZIP.exists():
        ZIP.unlink()
    with zipfile.ZipFile(ZIP, "w", zipfile.ZIP_DEFLATED, compresslevel=9) as z:
        for f in sorted(KIT.rglob("*")):
            if f.is_file():
                z.write(f, f.relative_to(KIT.parent))
    print("files:", sum(1 for f in KIT.rglob("*") if f.is_file()), "zip bytes:", ZIP.stat().st_size)


if __name__ == "__main__":
    main()
