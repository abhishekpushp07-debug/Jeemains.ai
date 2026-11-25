"""Machine status for the owner: storage, the scheduled check, failed work and uploads stuck for 15 minutes."""
import os, shutil, tempfile
from fastapi import APIRouter, Depends, Response
from .auth import owner
from .db import db, jobs, files, now
from . import storage_health

router = APIRouter(prefix='/api/admin/machine', tags=['Machine status'])
STUCK_SECONDS, CRON_LATE_SECONDS, DAY = 900, 2700, 86400
WORKING = ('received', 'reading', 'matching')
FIELDS = {'state': 1, 'revision': 1, 'updated_at': 1, 'payload.title': 1, 'payload.pages': 1, 'payload.read_pages': 1, 'payload.message': 1, 'payload.storage_wait': 1}


def book_row(b, t):
    p = b.get('payload') or {}
    w = p.get('storage_wait') or {}
    return {'id': b['_id'], 'title': p.get('title', ''), 'state': b['state'], 'revision': b.get('revision', 0), 'read_pages': p.get('read_pages', 0),
            'pages': p.get('pages', 0), 'minutes': max(0, int((t - b.get('updated_at', t)) // 60)), 'message': (p.get('message') or '')[:200],
            **({'waiting_minutes': max(0, int((t - w['since']) // 60)), 'kind': w.get('kind') or 'away', 'reason': w.get('reason', ''), 'next': w.get('next', ''),
                'stuck': bool(w.get('stuck')), 'mock': w.get('mock', ''), 'more': max(0, len(w.get('mocks') or {}) - 1), 'what': w.get('what', '')} if w else {})}


@router.get('/status')
async def status(response: Response, u=Depends(owner)):
    response.headers['Cache-Control'] = 'private, no-store'
    t = now()
    store = await storage_health.health(fresh=False, u=u)
    last = (await db.tejas_operations.find_one({'id': 'maintenance'}, {'_id': 0, 'last_run': 1}) or {}).get('last_run') or 0
    open_books = {'removed': False, 'archived': {'$ne': True}}
    held = [book_row(b, t) async for b in db.tejas_books.find({**open_books, 'paused': {'$ne': True}, 'payload.storage_wait': {'$exists': True},
                                                                       'payload.storage_wait.retrying': {'$ne': True}}, FIELDS).limit(40)]
    # Waiting for Supabase to come back is one list; a file Supabase keeps returning ("Atki hai") is another, with its own Dobara chalao.
    waiting, stuck_files = [b for b in held if not b['stuck']], [b for b in held if b['stuck'] and b['kind'] != 'hang']
    # A PDF whose step went silent three times in a row, and how many silent steps were let go in the last 24 hours.
    hung = [b for b in held if b['stuck'] and b['kind'] == 'hang']
    day_hangs = await db.tejas_step_hangs.count_documents({'at': {'$gte': t - DAY}})
    last_hang = await db.tejas_step_hangs.find_one({}, {'_id': 0, 'at': 1, 'title': 1, 'where': 1, 'last_beat': 1, 'freed': 1}, sort=[('at', -1)]) if day_hangs else None
    waiting_jobs = await jobs.count_documents({'status': 'queued', 'storage_waits': {'$gt': 0}, 'next_run_at': {'$gt': 0}, 'stuck': {'$ne': True}})
    # A Dobara chalao that has not finished in 15 minutes is listed here too, so a try that never ran cannot stay hidden.
    stuck = [book_row(b, t) async for b in db.tejas_books.find({**open_books, 'paused': {'$ne': True}, 'state': {'$in': WORKING}, 'updated_at': {'$lt': t - STUCK_SECONDS},
                                                                '$or': [{'payload.storage_wait': {'$exists': False}}, {'payload.storage_wait.retrying': True}]},
                                                              FIELDS).sort('updated_at', 1).limit(20)]
    failed_books = [book_row(b, t) async for b in db.tejas_books.find({**open_books, 'state': 'failed'}, FIELDS).sort('updated_at', -1).limit(20)]
    failed_jobs = {row['_id']: row['n'] async for row in jobs.aggregate([{'$match': {'status': 'failed', 'created_at': {'$gte': t - DAY}}},
                                                                         {'$group': {'_id': '$kind', 'n': {'$sum': 1}}}])}
    from .book_delete import pending
    deletes = await pending()   # uploads deleted for good whose clean-up is still open
    disk = shutil.disk_usage(tempfile.gettempdir())
    cron = {'configured': bool(os.environ.get('WEBHOOK_CRON_SECRET')), 'last_run': last, 'minutes_ago': int((t - last) // 60) if last else None,
            'late': not last or t - last > CRON_LATE_SECONDS}
    failed_total = sum(failed_jobs.values())
    attention = bool(stuck or stuck_files or hung or failed_books or failed_total or cron['late'] or waiting or store['mode'] in ('down', 'waiting') or store['backup']['alert'] or deletes['late'])
    return {'attention': attention, 'storage_mode': store['mode'], 'cron': cron, 'failed_jobs': failed_jobs, 'failed_total': failed_total,
            'storage_waiting': waiting, 'storage_waiting_jobs': waiting_jobs, 'storage_stuck': stuck_files,
            'hung_books': hung, 'step_hangs': {'day': day_hangs, 'last': last_hang}, 'delete_pending': deletes, 'storage_errors': await storage_health.errors(),
            'failed_books': failed_books, 'stuck': stuck, 'disk': {'free': disk.free, 'total': disk.total},
            'files_saved': await files.estimated_document_count(), 'checked_at': t}
