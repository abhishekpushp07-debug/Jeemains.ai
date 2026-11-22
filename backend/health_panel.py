"""App Health page for the owner (Phase 3, Level 7): /api/owner/health (a web page; same sign-in as the deletion panel).

Shows the whole app, every server copy added up (health_stats.beat): how many students are on, the speed of answers,
Rapid Fire and the website calls, the errors, the jeelive.ai website's health (its shield), the background jobs and each
server copy. Counts and timings only: never a student's name, number or id. Refreshes itself every 30 seconds."""
import secrets
import time
from datetime import datetime, timezone
from html import escape

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse, JSONResponse

from health_stats import BOUNDS, LIVE_WINDOW
from owner_panel import NO_STORE, owner_session

GROUPS = (("answers", "Rapid Fire answers"), ("rapid_fire", "Rapid Fire (everything else)"), ("sign_in", "Sign-in"),
          ("website", "Tests and results (website calls)"), ("all", "Whole app"))
JOBS = {"cup_night_tick": ("Cup Night clock", 3), "card_sync": ("Question bank check", 60), "sweep": ("Closing old matches", 330),
        "database_setup": ("Database setup (each release)", None), "warm_up": ("Warm-up after start", None)}
STATE_RANK = {"closed": 0, "half": 1, "open": 2}


def group_of(route: str) -> str:
    if route.startswith("/api/rf/") and route.endswith("/answer"):
        return "answers"
    if route in ("/api/jl/auth/phone", "/api/jl/auth/phone/signup", "/api/rf/access", "/api/jl/auth/me", "/api/jl/auth/refresh"):
        return "sign_in"
    if route.startswith("/api/rf/"):
        return "rapid_fire"
    if route.startswith("/api/jl/"):
        return "website"
    return "other"


def quantile(hist: list, q: float, bounds=BOUNDS):
    total = sum(hist)
    if not total:
        return None
    seen = 0
    for i, n in enumerate(hist):
        seen += n
        if seen >= q * total:
            return bounds[i] if i < len(bounds) else bounds[-1] * 2
    return bounds[-1] * 2


def add(a, b):
    return [x + y for x, y in zip(a, b)] if a else list(b)


def summary(row) -> dict:
    count, errors, hist = row[0], row[1], row[2:]
    return {"count": count, "errors": errors, "error_pct": round(100 * errors / count, 2) if count else 0.0,
            "p50_ms": quantile(hist, 0.5), "p95_ms": quantile(hist, 0.95)}


async def health_data(db) -> dict:
    now = time.time()
    nodes = await db.rf_health_nodes.find({"ts": {"$gt": now - LIVE_WINDOW}}, {"_id": 1, "started": 1, "ts": 1, "load": 1, "routes": 1, "website": 1, "jobs": 1, "later_pending": 1}).to_list(1000)
    groups, routes, website, jobs = {}, {}, None, {}
    for n in nodes:
        for route, row in (n.get("routes") or {}).items():
            routes[route] = add(routes.get(route), row)
            for g in (group_of(route), "all"):
                groups[g] = add(groups.get(g), row)
        w = n.get("website") or {}
        if w:
            website = website or {"state": "closed", "opened": 0, "last_trouble_ts": None, "calls": 0, "failed": 0, "refused": 0, "hist": []}
            if STATE_RANK.get(w.get("state"), 0) > STATE_RANK[website["state"]]:
                website["state"] = w["state"]
            for k in ("opened", "calls", "failed", "refused"):
                website[k] += w.get(k, 0)
            website["hist"] = add(website["hist"], w.get("hist") or [])
            website["last_trouble_ts"] = max(filter(None, [website["last_trouble_ts"], w.get("last_trouble_ts")]), default=None)
        # `seen`: when this run was reported. A copy reports every few seconds, so a 3-second job is judged by how long
        # before its copy's report it last ran (late_s), not by the age of the report itself.
        for name, j in (n.get("jobs") or {}).items():
            if name not in jobs or j["ts"] > jobs[name]["ts"]:
                jobs[name] = {**j, "seen": n["ts"]}
    async for j in db.rf_meta.find({"_id": {"$regex": "^job:"}}, {"_id": 1, "ts": 1, "took_ms": 1, "ok": 1}):
        name = j["_id"][4:]
        if name not in jobs or j["ts"] > jobs[name]["ts"]:
            jobs[name] = {**j, "seen": now}
    signed_in = await (await db.rf_access.aggregate([
        {"$match": {"expires_at": {"$gt": datetime.now(timezone.utc)}}},
        {"$match": {"uid": {"$not": {"$regex": "^TEST"}}}}, {"$group": {"_id": "$uid", "trusted": {"$max": {"$ifNull": ["$trusted", False]}}}},
        {"$group": {"_id": None, "n": {"$sum": 1}, "trusted": {"$sum": {"$cond": ["$trusted", 1, 0]}}}}])).to_list(1)
    live_matches = await db.rf_duels.count_documents({"status": "ready", "ends_at": {"$gt": now}})
    loads = [n.get("load") or {} for n in nodes]
    web = None
    if website:
        web = {k: website[k] for k in ("state", "opened", "calls", "failed", "refused")}
        web.update(p95_ms=quantile(website["hist"], 0.95, (50, 100, 200, 500, 1000, 2000, 5000, 10000)),
                   failed_pct=round(100 * website["failed"] / website["calls"], 2) if website["calls"] else 0.0,
                   last_trouble_s_ago=round(now - website["last_trouble_ts"]) if website["last_trouble_ts"] else None)
    return {
        "at": now, "window_minutes": 5,
        "students": {"signed_in": (signed_in[0]["n"] if signed_in else 0), "kept_playing_while_website_down": (signed_in[0]["trusted"] if signed_in else 0),
                     "playing_live_now": sum(x.get("sockets", 0) for x in loads), "live_matches": live_matches},
        "speed": [{"id": g, "label": label, **summary(groups[g])} for g, label in GROUPS if g in groups],
        "routes": sorted(({"route": r, **summary(row)} for r, row in routes.items()), key=lambda x: -x["count"])[:15],
        "website": web,
        "jobs": [{"id": name, "label": JOBS.get(name, (name.replace("_", " "), None))[0], "every_s": JOBS.get(name, (None, None))[1],
                  "last_s_ago": round(now - j["ts"]), "late_s": round(max(0.0, j["seen"] - j["ts"])), "took_ms": j.get("took_ms"), "ok": j.get("ok", True)} for name, j in sorted(jobs.items())],
        "copies": [{"id": n["_id"][:6], "up_s": round(now - n.get("started", now)), "lag_ms": (n.get("load") or {}).get("lag_sustained_ms", 0),
                    **{k: (n.get("load") or {}).get(k, 0) for k in ("inflight", "inflight_web", "sockets", "busy", "turned_away", "shed", "limited")},
                    "background_work": n.get("later_pending", 0)} for n in sorted(nodes, key=lambda x: x.get("started", 0))],
    }


def make_router(db):
    router = APIRouter(prefix="/owner")

    @router.get("/health", response_class=HTMLResponse, include_in_schema=False)
    async def page():
        nonce = secrets.token_urlsafe(16)
        csp = (f"default-src 'none'; style-src 'unsafe-inline'; script-src 'nonce-{nonce}'; connect-src 'self'; img-src 'self'; "
               "base-uri 'none'; form-action 'none'; frame-ancestors 'none'")
        return HTMLResponse(PAGE.replace("__NONCE__", escape(nonce)), headers={**NO_STORE, "Content-Security-Policy": csp, "X-Frame-Options": "DENY",
                                                                             "Referrer-Policy": "no-referrer", "X-Content-Type-Options": "nosniff", "X-Robots-Tag": "noindex"})

    @router.get("/health/data")
    async def data(request: Request):
        s = await owner_session(db, request)
        return JSONResponse({"who": s["who"], **await health_data(db)}, headers=NO_STORE)

    return router


PAGE = """<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<meta name="robots" content="noindex"><title>App Health — JEELIVE.AI</title><style>
:root{color-scheme:dark}*{box-sizing:border-box}body{margin:0;background:#08080a;color:#f8fafc;font:15px/1.5 system-ui,sans-serif}
main{max-width:1040px;margin:auto;padding:28px 20px 64px}.brand{font-size:12px;letter-spacing:2px;color:#ff6974;font-weight:800}
h1{font-size:28px;line-height:1.2;margin:10px 0 4px}h2{font-size:17px;margin:0 0 10px}p{color:#b0b0bf;margin:6px 0}.muted{color:#8a8a9a;font-size:13px}
.card{border:1px solid #2a2a38;background:#111117;border-radius:16px;padding:18px;margin:16px 0}
.tiles{display:grid;grid-template-columns:repeat(auto-fill,minmax(170px,1fr));gap:12px;margin:16px 0}
.tile{border:1px solid #2a2a38;background:#111117;border-radius:16px;padding:14px 16px}.tile b{display:block;font-size:28px;line-height:1.15;white-space:nowrap;font-variant-numeric:tabular-nums}
.tile span{color:#8a8a9a;font-size:12px;font-weight:700;letter-spacing:.6px;text-transform:uppercase}
.g{color:#4ade80}.a{color:#fbbf24}.r{color:#f87171}.n{color:#f8fafc}
table{width:100%;border-collapse:collapse;font-size:14px;font-variant-numeric:tabular-nums}th{color:#8a8a9a;font-weight:600;text-align:left;padding:6px 8px;border-bottom:1px solid #2a2a38}
td{padding:7px 8px;border-bottom:1px solid #1c1c26}td.num,th.num{text-align:right}td.num{white-space:nowrap}.wrap{overflow-x:auto}.mono{font-family:ui-monospace,monospace;font-size:13px}td.path{overflow-wrap:anywhere}
label{display:block;font-weight:700;font-size:13px;margin:14px 0 6px}input{width:100%;min-height:48px;border-radius:12px;border:1px solid #3a3a4a;background:#0c0c12;color:#f8fafc;font:16px system-ui;padding:0 14px}
button{min-height:44px;border-radius:999px;border:0;padding:0 18px;font:700 14px system-ui;cursor:pointer}.primary{background:#ff3b4f;color:#fff}.ghost{background:transparent;color:#f8fafc;border:1px solid #3a3a4a}
.row{display:flex;gap:10px;flex-wrap:wrap;align-items:center}.spread{justify-content:space-between}.err{color:#ff8b8b;font-weight:600}
.dot{display:inline-block;width:10px;height:10px;border-radius:50%;margin-right:8px;vertical-align:middle}.dg{background:#4ade80}.da{background:#fbbf24}.dr{background:#f87171}
.bar{display:flex;flex-wrap:wrap;gap:10px 16px;align-items:center;justify-content:space-between}.bar p{margin:0}.actions{display:flex;gap:10px;flex-shrink:0}
@media (max-width:480px){main{padding:20px 14px 48px}h1{font-size:24px}.card{padding:14px}table{font-size:13px}th,td{padding:6px 5px}.tile b{font-size:26px}}td.mono:not(.path){white-space:nowrap}
</style></head><body><main data-testid="health-page">
<div class="brand">JEELIVE.AI · OWNER PANEL</div>
<h1 data-testid="health-title">App Health</h1>
<p>The live app right now, every server copy added up. Numbers are counts and timings only: no student's name or number. Updates every 30 seconds.</p>
<section id="login" class="card" data-testid="health-login" hidden>
<p>Sign in with the website owner (or admin) email and password. They are checked by jeelive.ai and not stored here.</p>
<label for="email">Email</label><input id="email" data-testid="health-email" type="email" autocomplete="username">
<label for="password">Password</label><input id="password" data-testid="health-password" type="password" autocomplete="current-password">
<p id="login-error" class="err" data-testid="health-login-error" role="alert"></p>
<button id="login-btn" class="primary" data-testid="health-login-submit">Sign in</button></section>
<section id="panel" hidden>
<div class="bar"><p class="muted"><span id="updated" data-testid="health-updated"></span><span id="who" data-testid="health-who"></span></p>
<div class="actions"><button id="refresh" class="ghost" data-testid="health-refresh">Refresh now</button><button id="logout" class="ghost" data-testid="health-logout">Sign out</button></div></div>
<p id="panel-error" class="err" role="alert"></p>
<div class="tiles" id="tiles" data-testid="health-tiles"></div>
<div class="card" data-testid="health-alerts"><div class="bar"><h2>Email alerts</h2><button id="test-alert" class="ghost" data-testid="health-test-alert">Send a test email</button></div>
<p class="muted" id="alerts-to" data-testid="health-alerts-to"></p><p id="alerts-note" data-testid="health-alerts-note" role="status"></p>
<div class="wrap"><table data-testid="health-alerts-table"><thead><tr><th>Problem</th><th>Now</th><th class="num">Last email</th></tr></thead><tbody id="alerts"></tbody></table></div></div>
<div class="card"><h2>Speed (last 5 minutes)</h2><p class="muted">p95: 95 of every 100 answers were this fast or faster. Green: on target.</p><div class="wrap"><table data-testid="health-speed"><thead><tr><th>Part of the app</th><th class="num">Calls</th><th class="num">Typical</th><th class="num">p95</th><th class="num">Errors</th></tr></thead><tbody id="speed"></tbody></table></div></div>
<div class="card"><h2>jeelive.ai website</h2><div id="website" data-testid="health-website"></div></div>
<div class="card"><h2>Background jobs</h2><div class="wrap"><table data-testid="health-jobs"><thead><tr><th>Job</th><th class="num">Last run</th><th class="num">Took</th><th>Result</th></tr></thead><tbody id="jobs"></tbody></table></div></div>
<div class="card"><h2>Server copies</h2><div class="wrap"><table data-testid="health-copies"><thead><tr><th>Copy</th><th class="num">Up for</th><th class="num">Delay</th><th class="num">Working on</th><th class="num">Live players</th><th>State</th><th class="num">Asked to wait</th></tr></thead><tbody id="copies"></tbody></table></div></div>
<div class="card"><h2>Busiest addresses (last 5 minutes)</h2><div class="wrap"><table data-testid="health-routes"><thead><tr><th>Address</th><th class="num">Calls</th><th class="num">p95</th><th class="num">Errors</th></tr></thead><tbody id="routes"></tbody></table></div></div>
</section></main><script nonce="__NONCE__">
const $=id=>document.getElementById(id);
function el(tag,attrs,...kids){const n=document.createElement(tag);for(const[k,v]of Object.entries(attrs||{})){if(k==="text")n.textContent=v;else n.setAttribute(k,v)}kids.forEach(c=>c!=null&&n.append(c));return n}
async function call(path,opts={}){const r=await fetch("/api/owner/"+path,{credentials:"same-origin",headers:{"Content-Type":"application/json","X-Owner-Panel":"1"},...opts});const b=await r.json().catch(()=>({}));if(!r.ok)throw Object.assign(new Error(typeof b.detail==="string"?b.detail:"Something went wrong. Please try again."),{status:r.status});return b}
function show(signedIn){$("login").hidden=signedIn;$("panel").hidden=!signedIn}
const fmt=n=>n==null?"—":Number(n).toLocaleString();const ms=v=>v==null?"—":(v>=20000?"> 10 s":v>=1000?(v/1000)+" s":"≤ "+v+" ms");
const ago=s=>s==null?"never":s<60?s+" s ago":s<3600?Math.round(s/60)+" min ago":Math.round(s/3600)+" h ago";
const up=s=>s<3600?Math.round(s/60)+" min":s<86400?Math.round(s/3600)+" h":Math.round(s/86400)+" d";
const tone=(v,g,a)=>v==null?"n":v<=g?"g":v<=a?"a":"r";
const TARGET={answers:[100,250],rapid_fire:[200,500],sign_in:[1500,5000],website:[1500,5000],all:[500,1500]};
function tile(label,value,cls,id){return el("div",{class:"tile","data-testid":"health-tile-"+id},el("b",{class:cls,text:value}),el("span",{text:label}))}
function none(body,cols,text,id){if(!body.children.length)body.append(el("tr",{"data-testid":id},el("td",{colspan:String(cols),class:"muted",text})))}
function render(b){$("who").textContent=" · Signed in as "+b.who;$("updated").textContent="Updated "+new Date(b.at*1000).toLocaleTimeString();
const s=b.students,sp=Object.fromEntries(b.speed.map(x=>[x.id,x])),all=sp.all||{},ans=sp.answers||{},w=b.website;
$("tiles").replaceChildren(tile("Students signed in",fmt(s.signed_in),"n","signed-in"),tile("Playing live now",fmt(s.playing_live_now),"n","playing"),tile("Live matches",fmt(s.live_matches),"n","matches"),
tile("Answers p95",ms(ans.p95_ms),"num "+tone(ans.p95_ms,100,250),"answers"),tile("Errors",(all.error_pct||0)+"%",tone(all.error_pct||0,0.5,2),"errors"),
tile("Website",w?{closed:"OK",half:"Checking",open:"Down"}[w.state]:"No calls",w?{closed:"g",half:"a",open:"r"}[w.state]:"n","website"),tile("Server copies",fmt(b.copies.length),"n","copies"));
$("speed").replaceChildren(...b.speed.map(x=>{const t=TARGET[x.id]||[500,1500];return el("tr",{"data-testid":"health-speed-"+x.id},el("td",{text:x.label}),el("td",{class:"num",text:fmt(x.count)}),el("td",{class:"num",text:ms(x.p50_ms)}),el("td",{class:"num "+tone(x.p95_ms,t[0],t[1]),text:ms(x.p95_ms)}),el("td",{class:"num "+tone(x.error_pct,0.5,2),text:fmt(x.errors)+" ("+x.error_pct+"%)"}))}));
none($("speed"),5,"No calls in the last 5 minutes.","health-speed-empty");
const wb=$("website");wb.replaceChildren();if(!w)wb.append(el("p",{class:"muted",text:"No website calls in the last 5 minutes."}));else{const st={closed:["dg","Answering normally"],half:["da","Was down; checking with one call"],open:["dr","Down or very slow: calls are paused for a few seconds, students see a plain 'try again' line, Rapid Fire keeps playing"]}[w.state];
wb.append(el("p",{},el("span",{class:"dot "+st[0]}),st[1]),el("div",{class:"tiles"},tile("Calls (5 min)",fmt(w.calls),"n","web-calls"),tile("Failed",fmt(w.failed)+" ("+w.failed_pct+"%)",tone(w.failed_pct,1,5),"web-failed"),tile("Answered at once (paused)",fmt(w.refused),w.refused?"a":"g","web-refused"),tile("Website p95",ms(w.p95_ms),tone(w.p95_ms,1000,5000),"web-p95")),
el("p",{class:"muted",text:"Last trouble: "+ago(w.last_trouble_s_ago)+" · paused "+w.opened+" time(s) since the copies started · kept playing on a saved session: "+fmt(s.kept_playing_while_website_down)}))}
$("jobs").replaceChildren(...b.jobs.map(j=>{const late=j.every_s?(j.late_s<=2*j.every_s?"g":j.late_s<=5*j.every_s?"a":"r"):"n";return el("tr",{"data-testid":"health-job-"+j.id},el("td",{text:j.label}),el("td",{class:"num "+late,text:ago(j.last_s_ago)}),el("td",{class:"num",text:j.took_ms==null?"—":j.took_ms+" ms"}),el("td",{class:j.ok?"g":"r",text:j.ok?"Worked":"Failed"}))}));none($("jobs"),4,"No job has reported yet.","health-jobs-empty");
$("copies").replaceChildren(...b.copies.map(c=>el("tr",{"data-testid":"health-copy-"+c.id},el("td",{class:"mono",text:c.id}),el("td",{class:"num",text:up(c.up_s)}),el("td",{class:"num "+tone(c.lag_ms,50,200),text:c.lag_ms+" ms"}),el("td",{class:"num",text:fmt(c.inflight)}),el("td",{class:"num",text:fmt(c.sockets)}),el("td",{class:c.busy?"a":"g",text:c.busy?"Packed":"OK"}),el("td",{class:"num",text:fmt(c.turned_away+c.shed)}))));none($("copies"),7,"No server copy has reported yet (each reports every few seconds).","health-copies-empty");
$("routes").replaceChildren(...b.routes.map(r=>el("tr",{},el("td",{class:"mono path",text:r.route.replace(/\//g,"/\u200b")}),el("td",{class:"num",text:fmt(r.count)}),el("td",{class:"num",text:ms(r.p95_ms)}),el("td",{class:"num "+(r.errors?"r":"g"),text:fmt(r.errors)}))));none($("routes"),4,"No calls in the last 5 minutes.","health-routes-empty")}
function renderAlerts(a){$("alerts-to").textContent=a.to?"Emails go to "+a.to+" · checked every "+a.every_s+" s · "+(a.last_check_s_ago==null?"first check within a minute":"last check "+ago(a.last_check_s_ago))+" · "+a.sent_today+" sent today":"No alert email address is set.";
$("alerts").replaceChildren(...a.kinds.map(k=>el("tr",{"data-testid":"health-alert-"+k.id},el("td",{text:k.label}),k.active?el("td",{},el("div",{class:"r",text:"Problem since "+ago(k.since_s_ago).replace(" ago","")}),el("div",{class:"muted",text:k.detail})):el("td",{class:"g",text:"OK"}),el("td",{class:"num",text:k.last_mail_s_ago==null?"—":ago(k.last_mail_s_ago)}))))}
async function load(){$("panel-error").textContent="";try{const[b,a]=await Promise.all([call("health/data",{method:"GET",headers:{}}),call("health/alerts",{method:"GET",headers:{}}).catch(x=>x)]);if(a instanceof Error&&a.status===401)throw a;render(b);if(a instanceof Error){$("alerts-to").textContent="Alert status could not be loaded: "+a.message;$("alerts").replaceChildren()}else renderAlerts(a);show(true)}catch(x){if(x.status===401)show(false);else{show(true);$("panel-error").textContent=x.message}}}
$("test-alert").addEventListener("click",async()=>{const t=$("test-alert"),n=$("alerts-note");t.disabled=true;n.className="muted";n.textContent="Sending…";try{const r=await call("health/alerts/test",{method:"POST",body:"{}"});n.className="g";n.textContent="Test email sent to "+r.to+". It can take a minute to arrive (check spam too).";load()}catch(x){n.className="err";n.textContent=x.message}finally{t.disabled=false}});
$("refresh").addEventListener("click",load);$("logout").addEventListener("click",async()=>{await call("logout",{method:"POST",body:"{}"}).catch(()=>{});show(false)});
async function login(){const b=$("login-btn");b.disabled=true;$("login-error").textContent="";try{await call("session",{method:"POST",body:JSON.stringify({email:$("email").value,password:$("password").value})});$("password").value="";await load()}catch(x){$("login-error").textContent=x.message}finally{b.disabled=false}}
$("login-btn").addEventListener("click",login);$("password").addEventListener("keydown",e=>{if(e.key==="Enter")login()});load();setInterval(()=>{if(!$("panel").hidden&&!document.hidden)load()},30000);
</script></body></html>"""
