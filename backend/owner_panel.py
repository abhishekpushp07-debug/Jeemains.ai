"""Owner panel for account-deletion requests: /api/owner/deletions (a web page, for a computer or a phone browser).

Only the website owner (or the website's admin team) gets in: the email + password are checked by the website itself
(/auth/login), and that account must be allowed to read the website's student list (an owner-only page). This server
keeps no owner password, and the website session is ended right after the check. The panel then has its own 8-hour
cookie (HttpOnly, Secure, SameSite=Strict, path /api/owner) that is kept here only as a hash. Every change also needs
the X-Owner-Panel header (a page on another site cannot send it) and is written into the request's history.
Marking a request done or cancelled removes the stored phone number and name from it.
"""
import hashlib
import json
import os
import secrets
from datetime import datetime, timedelta, timezone
from html import escape
from typing import Literal

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import HTMLResponse, JSONResponse
from pydantic import BaseModel, ConfigDict, Field
from pymongo import ReturnDocument

from account_deletion import RID_RE, end_session, new_cookies
from client_ip import client_ip
from jl_transport import UpstreamError, canonical_request

API = os.environ['JEELIVE_API'].rstrip('/')
COOKIE, SESSION_HOURS = "jl_owner", 8
FAIL_LIMIT, FAIL_WINDOW = 10, timedelta(minutes=15)
NO_STORE = {"Cache-Control": "no-store"}


class OwnerLogin(BaseModel):
    model_config = ConfigDict(extra='forbid')
    email: str = Field(min_length=3, max_length=254)
    password: str = Field(min_length=1, max_length=128)


class Decision(BaseModel):
    model_config = ConfigDict(extra='forbid')
    note: str = Field(default="", max_length=300)


def _now():
    return datetime.now(timezone.utc)


def _hash(value: str) -> str:
    return hashlib.sha256(value.encode()).hexdigest()


def _iso(value):
    return value.replace(tzinfo=timezone.utc).isoformat() if isinstance(value, datetime) else None


def masked(email: str) -> str:
    name, _, domain = email.partition("@")
    return (name[:2] + "***@" + domain) if domain else "owner"


def row(doc: dict) -> dict:
    due = doc["due_at"].replace(tzinfo=timezone.utc)
    return {"id": doc["id"], "state": doc["state"], "website_user_id": doc["uid"], "name": doc.get("name") or "", "phone": doc.get("phone") or "",
            "phone_last4": doc.get("phone_last4") or "", "source": doc.get("source", "app"), "requested_at": _iso(doc["requested_at"]),
            "due_at": _iso(due), "days_left": (due - _now()).days, "completed_at": _iso(doc.get("completed_at")), "note": doc.get("note") or "",
            "sessions_ended": doc.get("sessions_ended", 0), "erased": doc.get("erased") or {},
            "history": [{"at": _iso(h["at"]), "event": h["event"], "by": h.get("by", "")} for h in doc.get("history", [])]}


def make_router(db, client):
    router = APIRouter(prefix="/owner")

    async def owner(request: Request, write: bool = False) -> dict:
        if write and request.headers.get("x-owner-panel") != "1":
            raise HTTPException(403, "Open the owner panel page to make changes.")
        token = request.cookies.get(COOKIE, "")
        s = await db.owner_sessions.find_one({"digest": _hash(token), "expires_at": {"$gt": _now()}}, {"_id": 0}) if 20 <= len(token) <= 128 else None
        if not s:
            raise HTTPException(401, "Please sign in to the owner panel.")
        return s

    @router.get("/deletions", response_class=HTMLResponse, include_in_schema=False)
    async def panel():
        nonce = secrets.token_urlsafe(16)
        csp = (f"default-src 'none'; style-src 'unsafe-inline'; script-src 'nonce-{nonce}'; connect-src 'self'; img-src 'self'; "
               "base-uri 'none'; form-action 'none'; frame-ancestors 'none'")
        return HTMLResponse(PAGE.replace("__NONCE__", escape(nonce)), headers={**NO_STORE, "Content-Security-Policy": csp, "X-Frame-Options": "DENY",
                                                                             "Referrer-Policy": "no-referrer", "X-Content-Type-Options": "nosniff", "X-Robots-Tag": "noindex"})

    @router.post("/session")
    async def sign_in(data: OwnerLogin, request: Request):
        ip = _hash(client_ip(request))
        if await db.owner_login_fails.count_documents({"ip": ip, "at": {"$gte": _now() - FAIL_WINDOW}}) >= FAIL_LIMIT:
            raise HTTPException(429, "Too many wrong tries. Please wait 15 minutes.", headers={"Retry-After": "900"})
        headers = {"Content-Type": "application/json", "Accept": "application/json"}
        try:
            r = await canonical_request(client(), "POST", f"{API}/auth/login", path="auth/login", params=None,
                                        body=json.dumps({"email": data.email.strip(), "password": data.password}).encode(), headers=headers)
        except UpstreamError:
            raise HTTPException(503, "The website did not answer. Please try again.")
        cookie = new_cookies(r.headers)
        try:
            if not r.is_success or not cookie:
                await db.owner_login_fails.insert_one({"ip": ip, "at": _now()})
                raise HTTPException(401, "Email or password is wrong.")
            try:  # only the owner / admin team may read the website's student list
                probe = await canonical_request(client(), "GET", f"{API}/admin/students", path="admin/students", params={"q": "0000000000"},
                                                body=None, headers={"Accept": "application/json", "Cookie": cookie})
            except UpstreamError:
                raise HTTPException(503, "The website did not answer. Please try again.")
            if probe.status_code != 200:
                await db.owner_login_fails.insert_one({"ip": ip, "at": _now()})
                raise HTTPException(403, "This account cannot open the owner panel.")
        finally:
            await end_session(client(), cookie)
        token = secrets.token_urlsafe(32)
        who = masked(data.email.strip().lower())
        await db.owner_sessions.insert_one({"digest": _hash(token), "who": who, "expires_at": _now() + timedelta(hours=SESSION_HOURS)})
        response = JSONResponse({"ok": True, "who": who}, headers=NO_STORE)
        response.set_cookie(COOKIE, token, max_age=SESSION_HOURS * 3600, httponly=True, secure=True, samesite="strict", path="/api/owner")
        return response

    @router.post("/logout")
    async def sign_out(request: Request):
        await db.owner_sessions.delete_many({"digest": _hash(request.cookies.get(COOKIE, ""))})
        response = JSONResponse({"ok": True}, headers=NO_STORE)
        response.delete_cookie(COOKIE, path="/api/owner", secure=True, httponly=True, samesite="strict")
        return response

    @router.get("/deletion-requests")
    async def requests_list(request: Request, view: Literal["pending", "done"] = "pending"):
        s = await owner(request)
        query = {"active": True} if view == "pending" else {"active": {"$ne": True}}
        docs = await db.account_deletions.find(query, {"_id": 0}).sort("requested_at", 1 if view == "pending" else -1).limit(500).to_list(500)
        overdue = await db.account_deletions.count_documents({"active": True, "due_at": {"$lt": _now()}})
        return JSONResponse({"who": s["who"], "view": view, "items": [row(d) for d in docs], "pending": await db.account_deletions.count_documents({"active": True}),
                             "overdue": overdue}, headers=NO_STORE)

    @router.post("/deletion-requests/{rid}/{action}")
    async def decide(rid: str, action: Literal["complete", "cancel"], data: Decision, request: Request):
        s = await owner(request, write=True)
        if not RID_RE.match(rid):
            raise HTTPException(404, "No request has this number.")
        state, event = ("owner_completed", "website_account_deleted") if action == "complete" else ("cancelled", "cancelled")
        now = _now()
        doc = await db.account_deletions.find_one_and_update(
            {"id": rid, "active": True, "state": "owner_pending"},
            {"$set": {"state": state, "completed_at": now, "note": data.note.strip()}, "$unset": {"active": "", "phone": "", "name": ""},
             "$push": {"history": {"at": now, "event": event, "by": s["who"]}}},
            projection={"_id": 0}, return_document=ReturnDocument.AFTER)
        if not doc:
            raise HTTPException(409, "This request is not waiting any more (already done, cancelled or still being erased).")
        return JSONResponse(row(doc), headers=NO_STORE)

    return router


async def ensure_indexes(db):
    await db.owner_sessions.create_index("digest", unique=True)
    await db.owner_sessions.create_index("expires_at", expireAfterSeconds=0)
    await db.owner_login_fails.create_index([("ip", 1), ("at", -1)])
    await db.owner_login_fails.create_index("at", expireAfterSeconds=int(FAIL_WINDOW.total_seconds()) * 2)


PAGE = """<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<meta name="robots" content="noindex"><title>Owner panel — account deletions — JEELIVE.AI</title><style>
:root{color-scheme:dark}*{box-sizing:border-box}body{margin:0;background:#08080a;color:#f8fafc;font:15px/1.6 system-ui,sans-serif}
main{max-width:880px;margin:auto;padding:28px 20px 64px}.brand{font-size:12px;letter-spacing:2px;color:#ff6974;font-weight:800}
h1{font-size:28px;line-height:1.2;margin:10px 0 6px}p{color:#b0b0bf;margin:6px 0}.muted{color:#8a8a9a;font-size:13px}
.card{border:1px solid #2a2a38;background:#111117;border-radius:16px;padding:18px;margin:16px 0}
label{display:block;font-weight:700;font-size:13px;margin:14px 0 6px}input{width:100%;min-height:48px;border-radius:12px;border:1px solid #3a3a4a;background:#0c0c12;color:#f8fafc;font:16px system-ui;padding:0 14px}
button{min-height:44px;border-radius:999px;border:0;padding:0 18px;font:700 14px system-ui;cursor:pointer}button:disabled{opacity:.5;cursor:default}
.primary{background:#ff3b4f;color:#fff}.ghost{background:transparent;color:#f8fafc;border:1px solid #3a3a4a}.ok{background:#22c55e;color:#04210f}
.row{display:flex;gap:10px;flex-wrap:wrap;align-items:center}.spread{justify-content:space-between}.err{color:#ff8b8b;font-weight:600}
.tabs button{background:#16161e;color:#cfcfe0;border:1px solid #2a2a38}.tabs button[aria-selected=true]{background:#f8fafc;color:#08080a}
.chip{display:inline-block;border-radius:999px;padding:2px 10px;font-size:12px;font-weight:800;letter-spacing:.5px}
.wait{background:#2a2113;color:#f1bc63}.late{background:#3b1216;color:#ff8b8b}.done{background:#0f2a19;color:#6ee7a0}.off{background:#22222c;color:#b0b0bf}
.kv{display:grid;grid-template-columns:150px 1fr;gap:4px 12px;margin:12px 0;font-size:14px}.kv b{color:#8a8a9a;font-weight:600}.mono{font-family:ui-monospace,monospace;overflow-wrap:anywhere}
ol{color:#b0b0bf;padding-left:20px;margin:8px 0}details{margin-top:10px;color:#b0b0bf;font-size:13px}
</style></head><body><main data-testid="owner-panel">
<div class="brand" data-testid="owner-brand">JEELIVE.AI · OWNER PANEL</div>
<h1 data-testid="owner-title">Account deletion requests</h1>
<p>Students ask for deletion in the app (or on the public web page) with their mobile number and PIN. Their Rapid Fire data is already erased and they are signed out. You delete the website account, then mark it here. Target: within 30 days.</p>
<section id="login" class="card" data-testid="owner-login" hidden>
<p>Sign in with the website owner (or admin) email and password. They are checked by jeelive.ai and not stored here.</p>
<label for="email">Email</label><input id="email" data-testid="owner-email" type="email" autocomplete="username">
<label for="password">Password</label><input id="password" data-testid="owner-password" type="password" autocomplete="current-password">
<p id="login-error" class="err" data-testid="owner-login-error" role="alert"></p>
<button id="login-btn" class="primary" data-testid="owner-login-submit">Sign in</button></section>
<section id="panel" hidden>
<div class="row spread"><div class="row tabs" role="tablist"><button id="tab-pending" role="tab" data-testid="owner-tab-pending" aria-selected="true">Waiting</button><button id="tab-done" role="tab" data-testid="owner-tab-done" aria-selected="false">Done</button></div>
<div class="row"><span id="who" class="muted" data-testid="owner-who"></span><button id="logout" class="ghost" data-testid="owner-logout">Sign out</button></div></div>
<p id="summary" data-testid="owner-summary"></p>
<div class="card" data-testid="owner-steps"><b>How to finish a request</b><ol><li>On the website, find the student by the phone number (or the website user id) and delete that account.</li><li>Come back and press <b>Website account deleted</b>. The stored number and name are then removed from this request.</li><li>Asked by mistake? Press <b>Cancel request</b>: they can sign in again (their Rapid Fire progress is already gone).</li></ol></div>
<p id="panel-error" class="err" data-testid="owner-panel-error" role="alert"></p>
<div id="list" data-testid="owner-list"></div></section>
</main><script nonce="__NONCE__">
const $=id=>document.getElementById(id);let view="pending";
function el(tag,attrs,...kids){const n=document.createElement(tag);for(const[k,v]of Object.entries(attrs||{})){if(k==="text")n.textContent=v;else if(k==="on")n.addEventListener("click",v);else n.setAttribute(k,v)}kids.forEach(c=>c&&n.append(c));return n}
const day=s=>s?new Date(s).toLocaleString(undefined,{day:"numeric",month:"short",year:"numeric",hour:"2-digit",minute:"2-digit"}):"—";
async function call(path,opts={}){const r=await fetch("/api/owner/"+path,{credentials:"same-origin",headers:{"Content-Type":"application/json","X-Owner-Panel":"1"},...opts});const b=await r.json().catch(()=>({}));if(!r.ok)throw Object.assign(new Error(typeof b.detail==="string"?b.detail:"Something went wrong. Please try again."),{status:r.status});return b}
function show(signedIn){$("login").hidden=signedIn;$("panel").hidden=!signedIn}
function chip(it){if(it.state==="owner_completed")return el("span",{class:"chip done",text:"WEBSITE ACCOUNT DELETED"});if(it.state==="cancelled")return el("span",{class:"chip off",text:"CANCELLED"});if(it.state==="erasing")return el("span",{class:"chip wait",text:"ERASING"});return it.days_left<0?el("span",{class:"chip late",text:"OVERDUE"}):el("span",{class:"chip wait",text:it.days_left+" DAYS LEFT"})}
function kv(rows){const g=el("div",{class:"kv"});rows.forEach(([k,v,mono])=>{g.append(el("b",{text:k}),el("span",{class:mono?"mono":"",text:v||"—"}))});return g}
function card(it){const erased=Object.entries(it.erased||{}).filter(([,n])=>n).map(([k,n])=>k.replace(/_/g," ")+" "+n).join(" · ");
const c=el("article",{class:"card","data-testid":"owner-request-"+it.id},el("div",{class:"row spread"},el("b",{class:"mono",text:it.id}),chip(it)),
kv([["Name",it.name],["Phone",it.phone||(it.phone_last4?"ending "+it.phone_last4:""),true],["Website user id",it.website_user_id,true],["Asked from",it.source==="web"?"Public web page":"App"],["Asked on",day(it.requested_at)],["Finish by",day(it.due_at)],["Finished",it.completed_at?day(it.completed_at):""],["Rapid Fire erased",erased||"nothing stored"],["Devices signed out",String(it.sessions_ended||0)],["Note",it.note]]));
if(it.state==="owner_pending"){const err=el("p",{class:"err",role:"alert"});const act=(a,q)=>async e=>{if(!confirm(q))return;e.target.disabled=true;err.textContent="";try{await call("deletion-requests/"+it.id+"/"+a,{method:"POST",body:"{}"});await load()}catch(x){err.textContent=x.message;e.target.disabled=false;if(x.status===401)show(false)}};
c.append(el("div",{class:"row"},el("button",{class:"ok","data-testid":"owner-complete-"+it.id,text:"Website account deleted",on:act("complete","Have you deleted this account on the website? This removes the stored number and name here.")}),el("button",{class:"ghost","data-testid":"owner-cancel-"+it.id,text:"Cancel request",on:act("cancel","Cancel this request? The student can sign in again.")})),err)}
const h=el("details",{},el("summary",{text:"History"}));(it.history||[]).forEach(x=>h.append(el("div",{text:day(x.at)+" · "+x.event.replace(/_/g," ")+(x.by?" · "+x.by:"")})));c.append(h);return c}
async function load(){$("panel-error").textContent="";try{const b=await call("deletion-requests?view="+view,{method:"GET",headers:{}});show(true);$("who").textContent="Signed in as "+b.who;
$("summary").textContent=b.pending+" waiting"+(b.overdue?" · "+b.overdue+" overdue":"");const list=$("list");list.replaceChildren();
if(!b.items.length)list.append(el("p",{class:"muted","data-testid":"owner-empty",text:view==="pending"?"No requests are waiting. Nothing to do.":"Nothing finished yet."}));b.items.forEach(it=>list.append(card(it)))}
catch(x){if(x.status===401)show(false);else $("panel-error").textContent=x.message}}
function tab(v){view=v;$("tab-pending").setAttribute("aria-selected",v==="pending");$("tab-done").setAttribute("aria-selected",v==="done");load()}
$("tab-pending").addEventListener("click",()=>tab("pending"));$("tab-done").addEventListener("click",()=>tab("done"));
$("logout").addEventListener("click",async()=>{await call("logout",{method:"POST",body:"{}"}).catch(()=>{});show(false)});
async function login(){const b=$("login-btn");b.disabled=true;$("login-error").textContent="";try{await call("session",{method:"POST",body:JSON.stringify({email:$("email").value,password:$("password").value})});$("password").value="";await load()}catch(x){$("login-error").textContent=x.message}finally{b.disabled=false}}
$("login-btn").addEventListener("click",login);$("password").addEventListener("keydown",e=>{if(e.key==="Enter")login()});load();
</script></body></html>"""
