"""Storage health for Super Admin: which store new files go to right now, and how fast each one answers."""

import asyncio, time
from fastapi import APIRouter, Depends, Query
from starlette.concurrency import run_in_threadpool
import tejas_storage as store
from .auth import staff

router = APIRouter(prefix="/api/admin/storage", tags=["Storage health"])
FRESH, SLOW_MS, ALERT_AFTER = 60, 2500, 600
_last = {'at': 0.0, 'result': None}
_running = {'task': None}


async def _check():
    result = await run_in_threadpool(store.probe)
    _last.update(at=time.time(), result=result)
    return result


def summary(result):
    sb, em, st = result['supabase'], result['emergent'], store.STATE
    resting = store.configured() and not store.supabase_on()
    if sb.get('ok') and not resting:
        mode = 'slow' if sb.get('write_ms', 0) + sb.get('read_ms', 0) > SLOW_MS else 'supabase'
    elif em.get('ok'):
        mode = 'emergent'
    else:
        mode = 'down'
    return {'mode': mode, 'checked_at': _last['at'], 'supabase': {**sb, 'configured': store.configured(), 'bucket': store.bucket_name() if store.configured() else '',
            'resting_until': st['down_until'] if resting else 0}, 'emergent': em,
            'writes': dict(st['writes']), 'failovers': st['failovers'], 'last_failover': st['last_failover'], 'backup': backup(st)}


def backup(st):
    """Alert once Supabase has been missing for 10 minutes while new files kept going to Emergent."""
    since, n = st['backup_since'], st['backup_writes']
    return {'since': since, 'writes': n, 'alert': bool(store.configured() and since and n and time.time() - since >= ALERT_AFTER)}


@router.get("/health")
async def health(fresh: bool = Query(False), u=Depends(staff)):
    """Checked at most once a minute (on asking with fresh=true, at most every 10 s), so the badge never loads the stores."""
    age = time.time() - _last['at']
    if _last['result'] is None or age > FRESH or (fresh and age > 10):
        task = _running['task']
        if task is None or task.done():
            task = _running['task'] = asyncio.ensure_future(_check())
        await asyncio.shield(task)
    return summary(_last['result'])
