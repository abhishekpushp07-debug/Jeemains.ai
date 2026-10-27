"""Public app legal information only. No auth, PIN collection or deletion writes.

The immutable source also ships with the native app for offline policy access.
Direct deletion remains unavailable until the canonical owner supplies a contract.
"""
import json
from html import escape
from pathlib import Path

from fastapi import APIRouter
from fastapi.responses import HTMLResponse, JSONResponse

router = APIRouter(prefix="/legal", tags=["Public app information"])
CONTENT_PATH = Path(__file__).resolve().parent.parent / "frontend/src/legal/content.json"
CONTENT = json.loads(CONTENT_PATH.read_text())
HEADERS = {
    "Cache-Control": "no-store, no-transform",
    "X-Content-Type-Options": "nosniff",
    "Referrer-Policy": "no-referrer",
    "X-Frame-Options": "DENY",
    "Content-Security-Policy": "default-src 'none'; style-src 'unsafe-inline'; img-src 'self'; base-uri 'none'; form-action 'none'; frame-ancestors 'none'",
}
CSS = """
:root{color-scheme:dark}*{box-sizing:border-box}body{margin:0;background:#08080a;color:#f8fafc;font:16px/1.7 system-ui,sans-serif}
main{max-width:760px;margin:auto;padding:32px 24px 56px}h1{font-size:32px;line-height:1.2;margin:24px 0}h2{font-size:21px;margin:30px 0 8px}
p{color:#b0b0bf;overflow-wrap:anywhere}a{color:#ff6974;overflow-wrap:anywhere}nav{display:flex;gap:20px;flex-wrap:wrap}nav a{display:inline-flex;min-height:44px;align-items:center}
.brand{font-size:13px;letter-spacing:2px;color:#ff6974;font-weight:800}.note{padding:18px;border:1px solid #906224;border-radius:14px;background:#2a2113;color:#f1bc63}.muted{font-size:13px}
footer{margin-top:32px;border-top:1px solid #2a2a38;padding-top:20px}footer a{display:inline-flex;align-items:center;min-height:44px}
"""


def page(title, body, test_id):
    email = escape(CONTENT["supportEmail"])
    return HTMLResponse(f"""<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>{escape(title)} — JEELIVE.AI</title><style>{CSS}</style></head>
<body><main data-testid="{test_id}"><div data-testid="public-legal-brand" class="brand">JEELIVE.AI</div><nav data-testid="public-legal-navigation" aria-label="Legal pages"><a data-testid="public-privacy-link" href="/api/legal/privacy">Privacy policy</a><a data-testid="public-deletion-link" href="/api/legal/delete-account">Account deletion</a></nav>
<h1 data-testid="public-legal-title">{escape(title)}</h1>{body}<footer><h2 data-testid="public-support-title">Privacy support</h2><a data-testid="public-support-email" href="mailto:{email}">{email}</a><p data-testid="public-email-warning" class="muted">Never email your PIN, passwords or session tokens. Opening an email app does not send a message or delete an account.</p></footer></main></body></html>""", headers=HEADERS)


@router.get("/privacy", response_class=HTMLResponse)
async def privacy():
    sections = "".join(f'<section data-testid="public-privacy-{escape(row["id"])}"><h2 data-testid="public-privacy-heading-{escape(row["id"])}">{escape(row["title"])}</h2><p data-testid="public-privacy-body-{escape(row["id"])}">{escape(row["body"])}</p></section>' for row in CONTENT["sections"])
    return page(CONTENT["privacyTitle"], f'<p data-testid="public-privacy-version" class="muted">Updated {escape(CONTENT["version"])}</p><p data-testid="public-privacy-intro">{escape(CONTENT["intro"])}</p>{sections}', "public-privacy-page")


@router.get("/delete-account", response_class=HTMLResponse)
async def deletion_information():
    info = CONTENT["deletion"]
    body = f'<div class="note" data-testid="public-deletion-unavailable">{escape(info["status"])}</div>'
    body += "".join(f'<p data-testid="public-deletion-{key}">{escape(info[key])}</p>' for key in ("explanation", "scope", "next"))
    return page(info["title"], body, "public-account-deletion-page")


@router.get("/information")
async def information():
    return JSONResponse(CONTENT, headers=HEADERS)