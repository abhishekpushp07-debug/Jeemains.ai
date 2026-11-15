"""Draft preview: a private copy of an uploaded Draft mock, built the same way publishing builds it, so the owner or a reviewer can take it like a student."""
import hashlib, json, logging
from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from .auth import staff
from .db import db, sets, now, audit
from .book_models import BookMock
from .book_store import load_book, original, identity
from .book_publish import source_questions, base_set

router = APIRouter(prefix='/api/admin/master/preview', tags=['Master'])
previews = db.tejas_draft_previews
STALE = 300


def fingerprint(m):
    return hashlib.sha256(json.dumps([m.label, m.questions, m.rules, m.chapter], sort_keys=True, default=str).encode()).hexdigest()[:32]


async def target(mid, u):
    row = await db.tejas_book_mocks.find_one({'_id': mid, 'archived': {'$ne': True}, 'set_id': None})
    if not row or row.get('published_generation'):
        raise HTTPException(404, 'This Draft is not available to try.')
    m = BookMock.from_mongo(row)
    book = await load_book(m.book_id)
    if await db.tejas_books.find_one({'_id': book.id, 'archived': True}, {'_id': 1}):
        raise HTTPException(404, 'This Draft is not available to try.')
    if not m.questions:
        raise HTTPException(409, 'No question has been read for this mock yet.')
    if not m.rules:
        raise HTTPException(409, 'Its time and marks are not known yet. Open Fix first.')
    return book, m


def view(r):
    return {'state': r['state'], 'set_id': r.get('set_id'), 'left_out': r.get('left_out', []), 'message': r.get('message', '')}


@router.post('/{mid}')
async def open_preview(mid: str, bg: BackgroundTasks, u=Depends(staff)):
    book, m = await target(mid, u)
    pid = identity('draft-preview', m.id, fingerprint(m))
    r = await previews.find_one({'_id': pid})
    if r and (r['state'] == 'ready' or (r['state'] == 'building' and r.get('started_at', 0) > now() - STALE)):
        return view(r)
    await previews.update_one({'_id': pid}, {'$set': {'mock_id': m.id, 'book_id': book.id, 'state': 'building', 'started_at': now(), 'by': u['id'], 'message': '', 'left_out': []}}, upsert=True)
    bg.add_task(build, pid, book.id, m.id)
    await audit(u['id'], 'Draft preview opened', m.id, m.label)
    return {'state': 'building', 'set_id': None, 'left_out': [], 'message': 'Preparing the student view…'}


@router.get('/{mid}')
async def preview_status(mid: str, u=Depends(staff)):
    book, m = await target(mid, u)
    r = await previews.find_one({'_id': identity('draft-preview', m.id, fingerprint(m))})
    if not r:
        raise HTTPException(404, 'The mock changed. Press Try as student again.')
    if r['state'] == 'building' and r.get('started_at', 0) <= now() - STALE:
        r = {**r, 'state': 'failed', 'message': 'Preparing took too long. Press Try as student again.'}
    return view(r)


async def build(pid, book_id, mid):
    try:
        book = await load_book(book_id)
        m = BookMock.from_mongo(await db.tejas_book_mocks.find_one({'_id': mid}))
        questions, left = await source_questions(book, m, await original(book), strict=False)
        if not questions:
            raise ValueError('No question is complete enough to try yet. Fix the marked questions first.')
        dest = book.payload.get('destination')
        # Private: never listed, never startable by students (draft + restricted audience); attempts are 'preview' and stay out of every score and rank.
        data = {**base_set(book, m, questions, dest), 'id': pid, 'version': 1, 'qa_only': True, 'audience': 'restricted', 'live_enabled': False,
                'draft_preview': {'mock_id': m.id, 'book_id': book.id, 'left_out': left, 'total': len(m.questions), 'built_at': now()}}
        await sets.update_one({'id': pid}, {'$setOnInsert': data}, upsert=True)
        await previews.update_one({'_id': pid}, {'$set': {'state': 'ready', 'set_id': pid, 'left_out': left, 'built_at': now()}})
    except Exception as exc:
        if not isinstance(exc, ValueError):
            logging.getLogger(__name__).exception('Draft preview failed (mock=%s)', mid)
        await previews.update_one({'_id': pid}, {'$set': {'state': 'failed', 'message': str(exc)[:300] if isinstance(exc, ValueError) else 'The student view could not be prepared. Try again.'}})
