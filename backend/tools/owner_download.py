"""Trusted-workspace CLI only. Issue/revoke owner ZIP grants without learner credentials."""
import argparse
from datetime import datetime, timedelta, timezone
from hashlib import sha256
import json
import os
from pathlib import Path
import secrets
import sys
from urllib.parse import urlparse
import uuid

from dotenv import dotenv_values, load_dotenv
from pymongo import MongoClient

BACKEND = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND))
from owner_downloads import ARTIFACT, ARTIFACT_TYPE  # noqa: E402


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=["issue", "revoke"])
    parser.add_argument("--grant-id", help="Public grant identifier to revoke, never the bearer token")
    parser.add_argument("--hours", type=int, default=24, choices=range(1, 25))
    parser.add_argument("--base-url", help="HTTPS backend base URL; defaults to this workspace's configured URL")
    args = parser.parse_args()
    load_dotenv(BACKEND / ".env")
    client = MongoClient(os.environ["MONGO_URL"])
    grants = client[os.environ["DB_NAME"]].owner_download_grants
    grants.create_index("token_sha256", unique=True)
    grants.create_index("expires_at", expireAfterSeconds=0)
    grants.create_index("id", unique=True)
    if args.action == "revoke":
        if not args.grant_id:
            parser.error("--grant-id is required for revocation")
        result = grants.update_one({"id": args.grant_id}, {"$set": {"revoked_at": datetime.now(timezone.utc)}})
        print(json.dumps({"revoked": bool(result.matched_count)}))
        return
    base = (args.base_url or dotenv_values(BACKEND.parent / "frontend" / ".env").get("EXPO_PUBLIC_BACKEND_URL") or "").rstrip("/")
    parsed = urlparse(base)
    if parsed.scheme != "https" or not parsed.netloc or parsed.query or parsed.fragment:
        parser.error("A valid HTTPS backend URL is required")
    payload = ARTIFACT.read_bytes()
    raw = secrets.token_bytes(32)
    now = datetime.now(timezone.utc)
    expires = now + timedelta(hours=args.hours)
    grant_id = str(uuid.uuid4())
    grants.insert_one({"id": grant_id, "token_sha256": sha256(raw).hexdigest(), "artifact_type": ARTIFACT_TYPE,
                       "artifact_sha256": sha256(payload).hexdigest(), "created_at": now, "expires_at": expires,
                       "revoked_at": None, "issued_for": "workspace-owner"})
    # Emit only on explicit operator request. Do not copy this bearer URL into source, app UI or memory files.
    print(json.dumps({"download_url": f"{base}/api/owner-downloads/{raw.hex()}",
                      "expires_at": expires.isoformat(), "grant_id": grant_id, "bytes": len(payload)}))


if __name__ == "__main__":
    main()