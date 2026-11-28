"""JLive Command server events: the facts this server reports to the owner's dashboard (Connect → JLive App).

- Off until JLIVE_TRACKING_SECRET_KEY is set (the dashboard's secret key; it lives only in this server's environment).
- Sent only after the database write succeeded, in the background, with a 2 s limit. A slow or missing dashboard never
  slows or breaks a student's request, and nothing here ever raises into one.
- Only real students: the website's account id (a UUID). This project's test profiles (TEST…, qa…) are never sent.
- No personal data: props are scalars only (never a phone, name, PIN or token).
- event_id is made from the event's own identity (the match, the claim, the request) when there is one, so a retried
  request sends the same id and the dashboard counts it once.
- Never a test or attempt event: the website is the one that knows about papers and attempts.
"""
import asyncio
import logging
import os
import re
import uuid
from datetime import datetime, timezone
from typing import Optional

import httpx

log = logging.getLogger("jl_track")
COLLECTOR = os.environ.get("JLIVE_COLLECTOR_URL", "https://tribeapp.pro").rstrip("/") + "/api/collect/v1/server"
WEBSITE_ID = re.compile(r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$")  # the dashboard's rule (lowercase)
NAMESPACE = uuid.UUID("6f1c0d3e-7a43-4c39-9b54-2f8e0a5d1c77")
_client: Optional[httpx.AsyncClient] = None
_running: set = set()  # the sends under way (a task nobody holds could be dropped before it ends)


def _secret() -> str:
    return os.environ.get("JLIVE_TRACKING_SECRET_KEY", "").strip()


def _props(props: Optional[dict]) -> dict:
    """Scalars only, at most 30 keys, strings cut at 200 characters."""
    out = {}
    for k, v in (props or {}).items():
        if len(out) >= 30:
            break
        if v is None or isinstance(v, (bool, int, float)):
            out[str(k)[:60]] = v
        elif isinstance(v, str):
            out[str(k)[:60]] = v[:200]
    return out


async def _send(event: dict) -> None:
    global _client
    try:
        if _client is None:
            _client = httpx.AsyncClient(timeout=2)
        res = await _client.post(COLLECTOR, json={"events": [event]}, headers={"Authorization": f"Bearer {_secret()}"})
        if res.status_code >= 400:
            log.info("jl_track %s answered %s", event["event_name"], res.status_code)
    except Exception as e:  # noqa: BLE001 - the dashboard being away never matters to a student
        log.info("jl_track %s not sent (%s)", event.get("event_name"), type(e).__name__)


def track_server(name: str, uid: str, props: Optional[dict] = None, key: Optional[str] = None) -> None:
    """Schedules one event and returns at once. `key` = what makes this event the same event on a retry."""
    try:
        if not _secret() or not isinstance(uid, str) or not WEBSITE_ID.match(uid):
            return
        event = {"event_id": str(uuid.uuid5(NAMESPACE, f"{name}|{uid}|{key}") if key else uuid.uuid4()), "event_name": name,
                 "occurred_at": datetime.now(timezone.utc).isoformat(timespec="milliseconds").replace("+00:00", "Z"),
                 "uid": uid, "props": _props(props)}
        task = asyncio.get_running_loop().create_task(_send(event))
        _running.add(task)
        task.add_done_callback(_running.discard)
    except Exception:  # noqa: BLE001
        pass


def track_wallet(uid: str, deltas: dict, reason: str, key: Optional[str] = None, **extra) -> None:
    """wallet_entry_posted for every currency that moved: deltas like {"coins": 40, "xp": 120, "diamonds.red": 1}
    (negative for a spend). Nothing is sent for a currency that did not move."""
    for what, delta in deltas.items():
        if not delta:
            continue
        currency, _, colour = what.partition(".")
        track_server("wallet_entry_posted", uid, {"currency": currency, **({"colour": colour} if colour else {}), "delta": delta, "reason": reason, **extra},
                     key=f"{key}|{what}" if key else None)
