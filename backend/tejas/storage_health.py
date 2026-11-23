"""Storage health for Super Admin: which store new files go to right now, and how fast each one answers."""

import asyncio, time
from fastapi import APIRouter, Depends, Query
from starlette.concurrency import run_in_threadpool
import tejas_storage as store
from .auth import owner

router = APIRouter(prefix="/api/admin/storage", tags=["Storage health"])
FRESH, SLOW_MS, ALERT_AFTER = 60, 2500, 600
_last = {'at': 0.0, 'result': None}
_running = {'task': None}


async def _check():
    result = await run_in_threadpool(store.probe)
    _last.update(at=time.time(), result=result)
    if result['supabase'].get('ok'):
        from .jobs import wake_storage
        _last['woke'] = await wake_storage()
    return result


def summary(result):
    sb, em, st = result['supabase'], result['emergent'], store.STATE
    resting = store.configured() and not store.supabase_on()
    if not store.configured():
        mode = 'emergent' if em.get('ok') else 'down'
    elif sb.get('ok') and not resting:
        mode = 'slow' if sb.get('write_ms', 0) + sb.get('read_ms', 0) > SLOW_MS else 'supabase'
    else:
        mode = 'waiting'  # new files wait for Supabase; nothing goes to Emergent
    return {'mode': mode, 'checked_at': _last['at'], 'supabase': {**sb, 'configured': store.configured(), 'bucket': store.bucket_name() if store.configured() else '',
            'resting_until': st['down_until'] if resting else 0}, 'emergent': em,
            'writes': dict(st['writes']), 'failovers': st['failovers'], 'last_failover': st['last_failover'], 'backup': backup(st)}


def backup(st):
    """Alert once Supabase has been away for 10 minutes (new work waits for it meanwhile)."""
    since = st['backup_since']
    return {'since': since, 'writes': st['failovers'], 'alert': bool(store.configured() and since and time.time() - since >= ALERT_AFTER)}


@router.post("/retry")
async def retry(u=Depends(owner)):
    """'Abhi phir try karo': checks Supabase now; if it answers, every job waiting for it runs at once."""
    _last['woke'] = 0
    _last['at'] = 0.0  # the owner asked: check Supabase now, not from the last minute's answer
    out = await health(fresh=True, u=u)
    return {**out, 'woke': _last.get('woke', 0)}


@router.get("/health")
async def health(fresh: bool = Query(False), u=Depends(owner)):
    """Checked at most once a minute (on asking with fresh=true, at most every 10 s), so the badge never loads the stores."""
    age = time.time() - _last['at']
    if _last['result'] is None or age > FRESH or (fresh and age > 10):
        task = _running['task']
        if task is None or task.done():
            task = _running['task'] = asyncio.ensure_future(_check())
        await asyncio.shield(task)
    return summary(_last['result'])
