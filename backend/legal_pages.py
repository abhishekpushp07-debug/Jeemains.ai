"""Public app legal information, and the public account-deletion page (Google Play asks for one that works without
the app). That page posts to /api/account/delete-request (account_deletion.py), which checks the PIN with the website;
this module itself stores nothing.

The same source file also ships with the native app for offline policy access.
"""
import json
import secrets
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
.step{padding:14px 16px;border:1px solid #2a2a38;border-radius:14px;margin:10px 0;background:#111117}.step h2{font-size:16px;margin:0 0 4px}.step p{margin:0}
form{margin:28px 0;padding:20px;border:1px solid #3b1216;border-radius:16px;background:#140b0d}label{display:block;font-weight:700;font-size:14px;margin:16px 0 6px}
input[type=tel],input[type=password],input[type=text]{width:100%;min-height:50px;border-radius:12px;border:1px solid #3a3a4a;background:#0c0c12;color:#f8fafc;font:17px system-ui;padding:0 14px}
.check{display:flex;gap:10px;align-items:flex-start;margin:16px 0;font-weight:400}.check input{width:22px;height:22px;margin-top:3px}
button{min-height:50px;width:100%;border-radius:999px;border:0;background:#ff3b4f;color:#fff;font:800 16px system-ui;margin-top:8px;cursor:pointer}button:disabled{opacity:.5}
.err{color:#ff8b8b;font-weight:600}.ok{padding:18px;border:1px solid #1f6b3d;border-radius:14px;background:#0f2a19;color:#c9f5d9}.ok b{font-family:ui-monospace,monospace;font-size:20px;color:#fff}
"""


def page(title, body, test_id, script=""):
    email = escape(CONTENT["supportEmail"])
    headers = HEADERS
    if script:  # only the deletion page runs a script: its own, by nonce, talking only to this server
        nonce = secrets.token_urlsafe(16)
        headers = {**HEADERS, "Content-Security-Policy": f"default-src 'none'; style-src 'unsafe-inline'; img-src 'self'; script-src 'nonce-{nonce}'; connect-src 'self'; base-uri 'none'; form-action 'none'; frame-ancestors 'none'"}
        script = f'<script nonce="{nonce}">{script}</script>'
    return HTMLResponse(f"""<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>{escape(title)} — JEELIVE.AI</title><style>{CSS}</style></head>
<body><main data-testid="{test_id}"><div data-testid="public-legal-brand" class="brand">JEELIVE.AI</div><nav data-testid="public-legal-navigation" aria-label="Legal pages"><a data-testid="public-privacy-link" href="/api/legal/privacy">Privacy policy</a><a data-testid="public-deletion-link" href="/api/legal/delete-account">Account deletion</a></nav>
<h1 data-testid="public-legal-title">{escape(title)}</h1>{body}<footer><h2 data-testid="public-support-title">Privacy support</h2><a data-testid="public-support-email" href="mailto:{email}">{email}</a><p data-testid="public-email-warning" class="muted">Never email your PIN, passwords or session tokens. Opening an email app does not send a message or delete an account.</p></footer></main>{script}</body></html>""", headers=headers)


@router.get("/privacy", response_class=HTMLResponse)
async def privacy():
    sections = "".join(f'<section data-testid="public-privacy-{escape(row["id"])}"><h2 data-testid="public-privacy-heading-{escape(row["id"])}">{escape(row["title"])}</h2><p data-testid="public-privacy-body-{escape(row["id"])}">{escape(row["body"])}</p></section>' for row in CONTENT["sections"])
    return page(CONTENT["privacyTitle"], f'<p data-testid="public-privacy-version" class="muted">Updated {escape(CONTENT["version"])}</p><p data-testid="public-privacy-intro">{escape(CONTENT["intro"])}</p>{sections}', "public-privacy-page")


@router.get("/delete-account", response_class=HTMLResponse)
async def deletion_page():
    info = CONTENT["deletion"]
    body = f'<p data-testid="public-deletion-explanation">{escape(info["explanation"])}</p>'
    body += "".join(f'<section class="step" data-testid="public-deletion-step-{escape(s["id"])}"><h2>{escape(s["title"])}</h2><p>{escape(s["body"])}</p></section>' for s in info["steps"])
    body += f'<p data-testid="public-deletion-retained" class="muted">{escape(info["retained"])}</p>'
    body += """<form id="delete-form" data-testid="public-deletion-form" novalidate>
<label for="phone">Registered mobile number</label><input id="phone" data-testid="public-deletion-phone" type="tel" inputmode="tel" autocomplete="tel" maxlength="16" placeholder="10-digit mobile number">
<label for="pin">4-digit PIN</label><input id="pin" data-testid="public-deletion-pin" type="password" inputmode="numeric" autocomplete="current-password" maxlength="4" placeholder="4 digits">
<label for="confirm">Type DELETE to confirm</label><input id="confirm" data-testid="public-deletion-confirm" type="text" autocomplete="off" autocapitalize="characters" maxlength="6" placeholder="DELETE">
<label class="check"><input id="agree" data-testid="public-deletion-agree" type="checkbox"><span>I understand this cannot be undone.</span></label>
<p id="error" class="err" data-testid="public-deletion-error" role="alert"></p>
<button id="submit" type="submit" data-testid="public-deletion-submit">Delete my account</button></form>
<div id="done" class="ok" data-testid="public-deletion-done" role="status" hidden></div>"""
    return page(info["title"], body, "public-account-deletion-page", DELETE_SCRIPT)


DELETE_SCRIPT = """const $=id=>document.getElementById(id);
$("delete-form").addEventListener("submit",async e=>{e.preventDefault();const phone=$("phone").value.replace(/[\\s()-]/g,""),pin=$("pin").value,err=$("error");err.textContent="";
if(!/^\\+?[0-9]{8,15}$/.test(phone))return err.textContent="Enter your registered mobile number.";if(!/^[0-9]{4}$/.test(pin))return err.textContent="Your PIN is exactly 4 digits.";
if($("confirm").value.trim().toUpperCase()!=="DELETE")return err.textContent="Type DELETE to confirm.";if(!$("agree").checked)return err.textContent="Tick the box to confirm.";
const b=$("submit");b.disabled=true;b.textContent="Deleting…";
try{const r=await fetch("/api/account/delete-request",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({phone,pin,confirm:"DELETE"})});const d=await r.json().catch(()=>({}));
if(!r.ok)throw new Error(typeof d.detail==="string"?d.detail:"Couldn't finish. Nothing was deleted. Please try again.");
$("pin").value="";$("delete-form").hidden=true;const box=$("done");box.hidden=false;const due=new Date(d.due_at).toLocaleDateString(undefined,{day:"numeric",month:"long",year:"numeric"});
box.replaceChildren(Object.assign(document.createElement("p"),{textContent:"Request number"}),Object.assign(document.createElement("b"),{textContent:d.request_id}),
Object.assign(document.createElement("p"),{textContent:"Your Rapid Fire data is deleted and you are signed out. Your website account will be deleted by "+due+". Keep the request number to ask about it."}))}
catch(x){err.textContent=x.message||"Connection interrupted. Nothing was deleted.";b.disabled=false;b.textContent="Delete my account"}});"""


@router.get("/information")
async def information():
    return JSONResponse(CONTENT, headers=HEADERS)