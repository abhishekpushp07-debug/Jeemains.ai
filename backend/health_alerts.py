"""Email alerts for the owner (App Health). One server copy at a time checks every CHECK_EVERY seconds and emails
OWNER_ALERT_EMAIL when:
- website: the jeelive.ai website stops answering (its /health check fails) or the website shield has paused calls;
- errors:  the app's own server errors jump (>= 5% of at least 50 calls in the last 5 minutes, website calls not counted);
- packed:  the server is packed (students asked to wait), a copy runs more than 200 ms behind, or Rapid Fire answers slow down;
- jobs:    a background job has missed 5 of its turns, or failed.
A problem has to be seen twice in a row before an email goes; "Fixed" goes once it has been gone for 2 minutes. At most
one problem email per kind every 10 minutes and DAILY_CAP emails a day, so a flapping problem can never flood the inbox.
Counts and timings only: no student's name, number or id is ever put in an email."""
import asyncio
import logging
import os
import re
import time
from datetime import datetime, timedelta, timezone
from html import escape

import httpx
from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import JSONResponse
from pymongo.errors import DuplicateKeyError

from database import take_turn
from health_panel import health_data
from owner_mail import send_email
from owner_panel import NO_STORE, masked, owner_session

logger = logging.getLogger("jeelive")
TO = os.environ.get("OWNER_ALERT_EMAIL", "").strip()
API = os.environ["JEELIVE_API"].rstrip("/")
CHECK_EVERY, OPEN_AFTER, CLOSE_AFTER = 30, 2, 4  # seconds; checks in a row to raise / to clear a problem
COOLDOWN, RETRY_EVERY, DAILY_CAP, TEST_EVERY = 600, 300, 40, 60
IST = timezone(timedelta(hours=5, minutes=30))
HOST = re.compile(r"^[a-z0-9-]+(\.[a-z0-9-]+)+$")
KINDS = {  # id: (row label, problem subject, fixed subject, what the app does meanwhile)
    "website": ("jeelive.ai website down", "jeelive.ai website is down", "jeelive.ai website is answering again",
                "Rapid Fire keeps playing. Tests and results show a plain 'try again in a moment' line, and answers being saved wait safely on the phone."),
    "errors": ("Errors jump", "Errors jumped in the app", "Errors are back to normal",
               "Some students may see 'Something went wrong'. The App Health page shows which part is failing."),
    "packed": ("Server packed or slow", "The server is packed or slow", "The server is back to normal speed",
               "New players may be asked to wait a few seconds. Matches already running keep going."),
    "jobs": ("Background job stopped", "A background job stopped", "Background jobs are running again",
             "Live play continues. Closing old matches or Cup Night may wait until the job runs again."),
}


def own_calls(speed: dict) -> tuple[int, int]:
    """The app's own calls and errors: everything except the website's (tests, results, sign-in) - those are 'website'."""
    count = errors = 0
    for gid, sign in (("all", 1), ("website", -1), ("sign_in", -1)):
        g = speed.get(gid) or {}
        count += sign * g.get("count", 0)
        errors += sign * g.get("errors", 0)
    return count, errors


def problems(d: dict, website_problem: str | None) -> dict:
    """kind -> what is wrong (plain words), from the App Health data and the website check."""
    out, speed, copies = {}, {x["id"]: x for x in d["speed"]}, d["copies"]
    w = d.get("website")
    if website_problem:
        out["website"] = f"The website {website_problem}."
    elif w and w["state"] == "open":
        out["website"] = f"Most website calls are failing ({w['failed']} of {w['calls']} in the last 5 minutes), so the app has paused them for a few seconds."
    count, errors = own_calls(speed)
    if count >= 50 and errors >= 5 and errors * 100 >= 5 * count:
        out["errors"] = f"{errors:,} of {count:,} calls failed in the last 5 minutes ({round(100 * errors / count, 1)}%)."
    busy, lag = [c for c in copies if c["busy"]], max((c["lag_ms"] for c in copies), default=0)
    answers = speed.get("answers") or {}
    if busy:
        out["packed"] = f"{len(busy)} of {len(copies)} server copies are packed, so new players are asked to wait."
    elif lag > 200:
        out["packed"] = f"A server copy is running {lag} ms behind (normal: under 50 ms)."
    elif answers.get("count", 0) >= 20 and (answers.get("p95_ms") or 0) >= 500:
        out["packed"] = f"Rapid Fire answers are slow: 95 of every 100 took up to {answers['p95_ms']} ms (target: 100 ms)."
    oldest = max((c["up_s"] for c in copies), default=0)
    stopped = []
    for j in d["jobs"]:
        if not j["ok"]:
            stopped.append(f"{j['label']} failed on its last run")
        elif j["every_s"] and j["late_s"] > 5 * j["every_s"] and oldest > 2 * j["every_s"] + 60:  # a fresh start is not late
            stopped.append(f"{j['label']} has not run for {round(j['last_s_ago'] / 60)} min (it runs every {j['every_s']} s)")
    if stopped:
        out["jobs"] = "; ".join(stopped) + "."
    return out


async def website_check(http: httpx.AsyncClient) -> str | None:
    try:
        r = await http.get(API + "/health", timeout=10)
    except httpx.TimeoutException:
        return "did not answer within 10 seconds"
    except httpx.HTTPError:
        return "could not be reached"
    return f"answered with error {r.status_code}" if r.status_code >= 400 else None


def ist(ts: float) -> str:
    return datetime.fromtimestamp(ts, IST).strftime("%d %b %Y, %I:%M %p IST")


async def page_link(db) -> tuple[str, str]:
    """(link to the App Health page, subject prefix). The host is the one the owner last opened the page on."""
    host = ((await db.rf_meta.find_one({"_id": "alert:host"}, {"host": 1})) or {}).get("host") or ""
    return (f"https://{host}/api/owner/health" if host else ""), ("[Preview] " if host.endswith(".preview.emergentagent.com") else "")


def snapshot_rows(d: dict) -> list:
    speed = {x["id"]: x for x in d["speed"]}
    p95 = (speed.get("answers") or {}).get("p95_ms")
    count, errors = own_calls(speed)
    s = d["students"]
    return [("Students signed in", f"{s['signed_in']:,}"), ("Playing live now", f"{s['playing_live_now']:,}"), ("Live matches", f"{s['live_matches']:,}"),
            ("Rapid Fire answers p95", f"up to {p95} ms" if p95 else "no answers in 5 min"),
            ("App errors (5 min)", f"{errors:,} of {count:,}"), ("Website", {"closed": "OK", "half": "Checking", "open": "Down"}.get((d.get("website") or {}).get("state"), "No calls")),
            ("Server copies", str(len(d["copies"])))]


def email_html(title: str, lines: list, d: dict, link: str, tone: str) -> str:
    color = {"bad": "#B91C1C", "good": "#15803D", "info": "#1D4ED8"}[tone]
    rows = "".join(f'<tr><td style="padding:6px 0;color:#555">{escape(k)}</td><td style="padding:6px 0;text-align:right;font-weight:bold">{escape(v)}</td></tr>'
                   for k, v in snapshot_rows(d))
    body = "".join(f'<p style="margin:0 0 12px;font-size:15px;line-height:1.5">{escape(x)}</p>' for x in lines)
    button = (f'<p style="margin:20px 0"><a href="{escape(link)}" style="background:#FF3B4F;color:#ffffff;text-decoration:none;font-weight:bold;'
              f'padding:12px 20px;border-radius:999px;display:inline-block">Open App Health</a></p>') if link else (
              '<p style="margin:20px 0;font-size:14px;color:#555">Open your App Health page (the backend link ending in /api/owner/health) for the full picture.</p>')
    return (f'<table role="presentation" width="100%" cellpadding="0" cellspacing="0"><tr><td style="padding:24px;font-family:Arial,sans-serif;color:#111">'
            f'<p style="margin:0 0 6px;font-size:12px;letter-spacing:2px;font-weight:bold;color:#FF3B4F">JEELIVE.AI · APP HEALTH</p>'
            f'<h1 style="margin:0 0 16px;font-size:22px;color:{color}">{escape(title)}</h1>{body}'
            f'<table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="margin-top:8px;border-top:1px solid #eee;font-size:14px">{rows}</table>'
            f'{button}<p style="margin:24px 0 0;font-size:12px;color:#888">Sent by JEELIVE.AI App Health to the app owner. Counts and timings only, '
            f'no student details. JEELIVE.AI never asks for your password by email.</p></td></tr></table>')


async def mail(db, subject: str, html: str, sender=None) -> str:
    """Send one owner email: "sent", "cap" (the day's DAILY_CAP emails already went), "failed" or "no_address".
    Only emails that really went count against the cap."""
    if not TO:
        return "no_address"
    day = "alert:day:" + datetime.now(IST).strftime("%Y-%m-%d")
    if ((await db.rf_meta.find_one({"_id": day}, {"n": 1})) or {}).get("n", 0) >= DAILY_CAP:
        logger.warning("health alert not emailed: %s emails already today", DAILY_CAP)
        return "cap"
    try:
        await (sender or send_email)(to=TO, subject=subject, html=html)
    except Exception:  # noqa: BLE001 - logged; tried again on a later check
        logger.warning("health alert email failed")
        return "failed"
    await db.rf_meta.update_one({"_id": day}, {"$inc": {"n": 1}}, upsert=True)
    return "sent"


async def step(db, found: dict, d: dict, now: float, sender=None):
    """Move each kind one check forward and send the emails its state calls for. A problem that is on and not yet
    emailed (held by the 10-minute gap, or the send failed) is emailed on a later check, at most every RETRY_EVERY."""
    link, prefix = await page_link(db)
    for kind, (_, problem_title, fixed_title, coping) in KINDS.items():
        s = await db.rf_meta.find_one({"_id": "alert:" + kind}) or {}
        detail = found.get(kind)
        upd = {"hits": s.get("hits", 0) + 1 if detail else 0, "clears": 0 if detail else s.get("clears", 0) + 1, "checked": now}
        if detail:
            upd["detail"] = detail
        if detail and not s.get("active") and upd["hits"] >= OPEN_AFTER:
            upd.update(active=True, since=now - CHECK_EVERY * (upd["hits"] - 1), mailed=False)
        state = {**s, **upd}
        if (detail and state.get("active") and not state.get("mailed") and now - s.get("problem_mailed_at", 0) >= COOLDOWN
                and now - s.get("tried_at", 0) >= RETRY_EVERY):
            html = email_html(problem_title, [detail, f"Seen since {ist(state['since'])}.", "Meanwhile: " + coping], d, link, "bad")
            upd["tried_at"] = now
            if await mail(db, f"{prefix}JEELIVE.AI alert: {problem_title}", html, sender) == "sent":
                upd.update(mailed=True, problem_mailed_at=now, last_mail_at=now)
        elif not detail and s.get("active") and upd["clears"] >= CLOSE_AFTER:
            upd.update(active=False, fixed_at=now, tried_at=0)
            if s.get("mailed"):  # 'Fixed' only follows a problem email the owner really got
                minutes = max(1, round((now - s.get("since", now)) / 60))
                html = email_html(fixed_title, [f"Fixed at {ist(now)}, after about {minutes} min.", "Earlier: " + s.get("detail", "")], d, link, "good")
                if await mail(db, f"{prefix}Fixed: {fixed_title}", html, sender) == "sent":
                    upd["last_mail_at"] = now
        await db.rf_meta.update_one({"_id": "alert:" + kind}, {"$set": upd}, upsert=True)


async def check(db, http, sender=None):
    d = await health_data(db)
    await step(db, problems(d, await website_check(http)), d, time.time(), sender)


async def watch(db):
    async with httpx.AsyncClient(follow_redirects=False) as http:
        while True:
            await asyncio.sleep(CHECK_EVERY)
            try:
                if await take_turn(db, "health_alerts", CHECK_EVERY - 5):
                    await check(db, http)
            except Exception:  # noqa: BLE001 - one bad check never stops the next
                logger.exception("health alert check failed")


def make_router(db):
    router = APIRouter(prefix="/owner")
    seen_host = {"host": None}

    async def remember_host(request: Request):
        """Links in the emails point at the host the owner really opened the page on."""
        # The public host (the ingress passes it as X-Forwarded-Host; Host is its internal name), never a host a visitor typed:
        # only owner-signed-in calls get here.
        host = (request.headers.get("x-forwarded-host") or request.headers.get("host") or "").split(",")[0].strip().split(":")[0].lower()
        if host != seen_host["host"] and HOST.match(host) and not host.replace(".", "").isdigit():
            await db.rf_meta.update_one({"_id": "alert:host"}, {"$set": {"host": host}}, upsert=True)
            seen_host["host"] = host

    @router.get("/health/alerts")
    async def status(request: Request):
        await owner_session(db, request)
        await remember_host(request)
        now = time.time()
        docs = {d["_id"][6:]: d async for d in db.rf_meta.find({"_id": {"$in": ["alert:" + k for k in KINDS]}})}
        day = await db.rf_meta.find_one({"_id": "alert:day:" + datetime.now(IST).strftime("%Y-%m-%d")}, {"n": 1})
        checked = max((d.get("checked", 0) for d in docs.values()), default=0)
        return JSONResponse({"to": masked(TO) if TO else "", "every_s": CHECK_EVERY, "sent_today": min((day or {}).get("n", 0), DAILY_CAP),
                             "last_check_s_ago": round(now - checked) if checked else None,
                             "kinds": [{"id": k, "label": KINDS[k][0], "active": bool(docs.get(k, {}).get("active")),
                                        "since_s_ago": round(now - docs[k]["since"]) if docs.get(k, {}).get("active") else None,
                                        "detail": docs[k].get("detail", "") if docs.get(k, {}).get("active") else "",
                                        "last_mail_s_ago": round(now - docs[k]["last_mail_at"]) if docs.get(k, {}).get("last_mail_at") else None} for k in KINDS]},
                            headers=NO_STORE)

    @router.post("/health/alerts/test")
    async def test(request: Request):
        await owner_session(db, request, write=True)
        await remember_host(request)
        if not TO:
            raise HTTPException(503, "No alert email address is set.")
        now = time.time()
        try:
            await db.rf_meta.find_one_and_update({"_id": "alert:test", "at": {"$lt": now - TEST_EVERY}}, {"$set": {"at": now}}, upsert=True)
        except DuplicateKeyError:
            raise HTTPException(429, "A test email was just sent. Please wait a minute.", headers={"Retry-After": str(TEST_EVERY)})
        d = await health_data(db)
        link, prefix = await page_link(db)
        html = email_html("Test email: alerts are working", [
            f"You asked for this test at {ist(now)}. Real alerts come to this address when the jeelive.ai website goes down, errors jump, "
            "the server is packed or slow, or a background job stops, and again when each is fixed.", "Right now:"], d, link, "info")
        result = await mail(db, f"{prefix}JEELIVE.AI test alert", html)
        if result == "cap":
            raise HTTPException(429, f"Today's limit of {DAILY_CAP} alert emails is reached. Emails start again tomorrow.")
        if result != "sent":
            raise HTTPException(502, "The email could not be sent. Please try again in a few minutes.")
        return JSONResponse({"sent": True, "to": masked(TO)}, headers=NO_STORE)

    return router
