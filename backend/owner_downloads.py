"""Owner-issued, expiring grants for the fixed owner files (ARTIFACTS: ZIPs and one PDF); no public mint endpoint."""
from datetime import datetime, timezone
from hashlib import sha256
import hmac
import logging
from pathlib import Path
import re

from fastapi import APIRouter, HTTPException
from fastapi.responses import Response
from starlette.concurrency import run_in_threadpool

ROOT = Path(__file__).resolve().parents[1]
ARTIFACT = ROOT / "neetlive" / "exports" / "neetlive-content.zip"
ARTIFACT_TYPE = "neetlive-content-zip"
HANDOFF_TYPE = "rank-mission-handoff-zip"
THEME_GUIDE_TYPE = "glossy-theme-guide-pdf"
SHINE_CODE_TYPE = "shine-web-code-zip"
CEO_KIT_TYPE = "ceo-dashboard-handoff-zip"
# type -> (file, download name, longest grant in hours)
ARTIFACTS = {
    ARTIFACT_TYPE: (ARTIFACT, "neetlive-content.zip", 24),
    HANDOFF_TYPE: (ROOT / "handoff" / "JEELIVE_Rank_Mission_Website_Handoff.zip", "JEELIVE_Rank_Mission_Website_Handoff.zip", 168),
    THEME_GUIDE_TYPE: (ROOT / "handoff" / "theme_guide" / "JEELIVE_App_Glossy_Theme_Guide.pdf", "JEELIVE_App_Glossy_Theme_Guide.pdf", 168),
    SHINE_CODE_TYPE: (ROOT / "handoff" / "theme_guide" / "JEELIVE_Shine_Web_Code.zip", "JEELIVE_Shine_Web_Code.zip", 168),
    CEO_KIT_TYPE: (ROOT / "handoff" / "JEELIVE_CEO_Dashboard_Handoff.zip", "JEELIVE_CEO_Dashboard_Handoff.zip", 168),
}
DOWNLOAD_HEADERS = {"Cache-Control": "private, no-store", "Pragma": "no-cache",
                    "Referrer-Policy": "no-referrer", "X-Content-Type-Options": "nosniff"}


class RedactOwnerDownload(logging.Filter):
    """Keep capability tokens out of application access logs."""
    def filter(self, record):
        if isinstance(record.args, tuple):
            record.args = tuple(re.sub(r"(/api/owner-downloads/)[^\s?]+", r"\1[REDACTED]", arg)
                                if isinstance(arg, str) else arg for arg in record.args)
        return True


def make_router(db):
    router = APIRouter(prefix="/owner-downloads")
    access_log = logging.getLogger("uvicorn.access")
    if not any(isinstance(f, RedactOwnerDownload) for f in access_log.filters):
        access_log.addFilter(RedactOwnerDownload())

    @router.get("/{token}", include_in_schema=False)
    async def download(token: str):
        missing = HTTPException(404, "Download link is invalid, expired or replaced.", headers=DOWNLOAD_HEADERS)
        if not re.fullmatch(r"[a-f0-9]{64}", token):
            raise missing
        digest = sha256(bytes.fromhex(token)).hexdigest()
        grant = await db.owner_download_grants.find_one({
            "token_sha256": digest, "artifact_type": {"$in": list(ARTIFACTS)},
            "revoked_at": None, "expires_at": {"$gt": datetime.now(timezone.utc)},
        }, {"_id": 0, "artifact_sha256": 1, "artifact_type": 1})
        if not grant:
            raise missing
        path, name, _ = ARTIFACTS[grant["artifact_type"]]
        try:
            # Read once, verify once, return those EXACT bytes (no replacement race).
            payload = await run_in_threadpool(path.read_bytes)
        except OSError:
            raise missing
        if not hmac.compare_digest(sha256(payload).hexdigest(), grant["artifact_sha256"]):
            raise missing
        return Response(payload, media_type="application/pdf" if name.endswith(".pdf") else "application/zip", headers={
            **DOWNLOAD_HEADERS, "Content-Disposition": f'attachment; filename="{name}"',
        })

    return router