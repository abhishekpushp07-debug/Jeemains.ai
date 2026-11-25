"""Delete for good an upload that never reached students: its record, its Draft mocks and their fixes, the PDF pieces on the
server and its own folder in Supabase. The row leaves at once; the clean-up runs behind (Supabase first, the upload's own record
last) and the 15-minute check finishes it if a server stops or Supabase is away. Owner only, after typing DELETE."""
import asyncio, logging
from typing import Literal
from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from pydantic import BaseModel, ConfigDict
from pymongo import ReturnDocument
from starlette.concurrency import run_in_threadpool
from .auth import owner
from .db import db, sets, attempts, jobs, files, now, audit
from .canonical import EPOCH_NOW
from .library import BOOK_PARTS
import tejas_storage as store

router = APIRouter(prefix='/api/admin/master/uploads/book', tags=['Master'])
log = logging.getLogger(__name__)
LEASE, STEP_WAIT, FORCE, LATE = 300, 60, 1200, 900
REACHED = 'Is upload se students ke liye test ban chuka hai (Live, Scheduled, Off ya Library). Aisa upload poora delete nahi hota; iske Draft mock Library mein bheje ja sakte hain.'
IN_LIBRARY = 'Yeh upload Library mein hai. Use Library se hataiye.'
MARK = {'deleting': {'$exists': True}}


class DeleteUpload(BaseModel):
    model_config = ConfigDict(extra='forbid', strict=True)
    confirm: Literal['DELETE']


class StillWorking(Exception):
    pass


async def reached_students(ids):
    """Of these uploads, the ones from which a test was ever made (Live, Scheduled, Off or in the Library, even one deleted there since)."""
    ids = list(ids)
    if not ids:
        return set()
    made = set(await sets.distinct('book_import_id', {'book_import_id': {'$in': ids}}))
    built = set(await db.tejas_book_mocks.distinct('book_id', {'book_id': {'$in': ids}, '$or': [
        {'set_id': {'$ne': None}}, {'published_generation': {'$gt': 0}}, {'history.0': {'$exists': True}}]}))
    return made | built


async def target(id, u):
    row = await db.tejas_books.find_one({'_id': id, 'owner_id': u['id'], 'removed': False})
    if not row:
        raise HTTPException(404, 'Upload nahi mila. Page reload kijiye.')
    return row


async def facts(row):
    """What leaves with this upload, counted, for the box the owner reads before typing DELETE."""
    id, p = row['_id'], row['payload']
    mocks = await db.tejas_book_mocks.find({'book_id': id}, {'pages': 1, 'confirmed': 1, 'cuts': 1, 'archived': 1, 'series_date': 1}).to_list(None)
    repaired = set(await db.tejas_book_pages.distinct('number', {'book_id': id, 'provenance.kind': 'owner_repair'}))
    fixed = sum(1 for m in mocks if m.get('confirmed') or m.get('cuts') or any(n in repaired for numbers in (m.get('pages') or {}).values() for n in numbers))
    pictures = await files.count_documents({'book_import_id': id})
    in_supabase = await files.count_documents({'book_import_id': id, 'path': {'$regex': '^sb://'}})
    source = p.get('source_path') or ''
    why = IN_LIBRARY if row.get('archived') else REACHED if await reached_students([id]) else ''
    return {'id': id, 'title': p.get('title', ''), 'allowed': not why, 'reason': why, 'mocks': len(mocks), 'fixed': fixed,
            'in_library': sum(1 for m in mocks if m.get('archived')), 'days': sum(1 for m in mocks if m.get('series_date')),
            'pages': max(p.get('pages') or 0, await db.tejas_book_pages.count_documents({'book_id': id})),
            'original': 'supabase' if source.startswith(store.SB) else 'emergent' if source else 'server',
            'pictures': {'supabase': in_supabase, 'emergent': pictures - in_supabase}, 'supabase': store.configured(),
            'replaces': bool((p.get('destination') or {}).get('replaces'))}


@router.get('/{id}/delete')
async def delete_facts(id: str, u=Depends(owner)):
    return await facts(await target(id, u))


@router.post('/{id}/delete')
async def delete_upload(id: str, body: DeleteUpload, bg: BackgroundTasks, u=Depends(owner)):
    row = await target(id, u)
    what = await facts(row)
    if not what['allowed']:
        raise HTTPException(409, what['reason'])
    t = now()
    # From this moment the upload is in no list and no step can save into it (its lock is taken away). The same PDF may be sent again at once.
    marked = await db.tejas_books.update_one({'_id': id, 'owner_id': u['id'], 'removed': False, 'archived': {'$ne': True}}, {
        '$set': {'removed': True, 'paused': True, 'state': 'removed',
                 'deleting': {'at': t, 'by': u['id'], 'tries': 0, 'lease_until': 0, 'error': '', 'storage_removed': 0,
                              'facts': {k: what[k] for k in ('mocks', 'fixed', 'pages', 'pictures', 'original')}}},
        '$unset': {'lock_token': '', 'lock_until': ''}})
    if not marked.modified_count:
        raise HTTPException(404, 'Upload nahi mila. Page reload kijiye.')
    # What pointed at it lets go now: a day given to one of its Drafts, and the mark on an old mock it was going to replace.
    await db.tejas_book_mocks.update_many({'book_id': id}, {'$set': {'series_date': None, 'series_id': None, 'publish_requested': False, 'release_at': None}, '$inc': {'revision': 1}})
    replaces = (row['payload'].get('destination') or {}).get('replaces')
    if replaces:
        await sets.update_many({'id': {'$in': replaces}, 'replace_pending': row['payload'].get('title', '')[:160]}, {'$unset': {'replace_pending': ''}})
    await audit(u['id'], 'Upload delete requested', id, row['payload'].get('title', '')[:160])
    bg.add_task(sweep, id)
    return {'deleted': True, 'message': 'Upload delete ho gaya. Safai peeche chal rahi hai; wahi PDF aap abhi dobara upload kar sakte hain.'}


def clear_storage(id, half_sent):
    if not store.supabase_on():
        raise store.StorageError('Supabase abhi jawab nahi de raha; safai uske lautne par hogi.')
    store.sb_end_upload(half_sent)
    return store.sb_empty(f'jeelive/books/{id}/')


async def drop_records(row):
    """The upload's records, each narrowed to this one upload; never a whole collection."""
    id, p = row['_id'], row['payload']
    await files.delete_many({'book_import_id': id})
    previews = await db.tejas_draft_previews.distinct('_id', {'book_id': id})
    if previews:
        # "Try as student" copies: the owner's own trial attempts keep their line, like every attempt of a deleted test.
        await attempts.update_many({'set_id': {'$in': previews}}, {'$set': {'set_deleted': True, 'set_deleted_at': now()}})
        for name in ('tejas_saved_tests', 'tejas_question_solutions', 'tejas_versions'):
            await db[name].delete_many({'set_id': {'$in': previews}})
        await sets.delete_many({'id': {'$in': previews}, 'draft_preview.book_id': id})
        await db.tejas_draft_previews.delete_many({'book_id': id})
    mocks = await db.tejas_book_mocks.distinct('_id', {'book_id': id})
    if mocks:
        await db.tejas_publish_progress.delete_many({'_id': {'$in': mocks}})
    for part in BOOK_PARTS:
        await db[part].delete_many({'book_id': id})
    sha = p.get('sha256')
    if sha and not await db.tejas_books.find_one({'payload.sha256': sha, '_id': {'$ne': id}, 'removed': False}, {'_id': 1}):
        from .book_store import CACHE
        try:
            (CACHE / f'{sha}.pdf').unlink(missing_ok=True)   # this server's own copy of the PDF, unless the same PDF is in use by another upload
        except OSError:
            pass


async def call_off(row):
    """A mock of this upload became a test in the very moment of the delete, so it has reached students: nothing is removed and the upload comes back."""
    id = row['_id']
    await db.tejas_books.update_one({'_id': id, **MARK}, {'$set': {'removed': False, 'paused': False, 'state': 'matching',
        'payload.message': 'Delete radd hua: isi pal iska ek mock students ke liye ban gaya. Kuch nahi hataya gaya.'}, '$unset': {'deleting': ''}})
    await audit(row['deleting']['by'], 'Upload delete called off', id, 'A mock of it was built for students at that moment; nothing was removed.')
    from .book_models import Book
    from .book_store import enqueue_book
    await enqueue_book(Book.from_mongo(await db.tejas_books.find_one({'_id': id})))
    return 'called_off'


async def work(row):
    id, p, d = row['_id'], row['payload'], row['deleting']
    # 0. A step that was running on this PDF stops at its next check. Nothing is removed while it may still write.
    running = {'kind': 'book_step', 'payload.book_id': id, 'status': 'running', '$expr': {'$gt': ['$lease_until', EPOCH_NOW]}}
    waited = 0
    while now() - d['at'] < FORCE and await jobs.find_one(running, {'_id': 1}):
        if waited >= STEP_WAIT:
            raise StillWorking('Is PDF ka chal raha kadam abhi ruk raha hai.')
        await asyncio.sleep(1)
        waited += 1
    if await reached_students([id]):
        return await call_off(row)
    await jobs.delete_many({'kind': 'book_step', 'payload.book_id': id, 'status': {'$ne': 'running'}})
    # 1. Supabase first: the upload's own folder is listed, those names are removed, and it is listed again (it must be empty).
    if store.configured():
        gone = await run_in_threadpool(clear_storage, id, (p.get('transfer') or {}).get('url'))
        await db.tejas_books.update_one({'_id': id, **MARK}, [{'$set': {'deleting.storage_removed': {'$add': [{'$ifNull': ['$deleting.storage_removed', 0]}, gone]},
                                                                      'deleting.lease_until': {'$add': [EPOCH_NOW, LEASE]}}}])
        d['storage_removed'] = d.get('storage_removed', 0) + gone
    # 2. Its records. 3. Last of all the upload's own record: until then an unfinished clean-up can always be found and finished.
    await drop_records(row)
    await db.tejas_books.delete_one({'_id': id, 'removed': True, **MARK})
    f = d.get('facts') or {}
    await audit(d['by'], 'Upload deleted for good', id, f"{p.get('title', '')[:120]}: {f.get('mocks', 0)} Draft mocks ({f.get('fixed', 0)} with owner fixes), {f.get('pages', 0)} pages, "
                f"{sum((f.get('pictures') or {}).values())} picture records, {d.get('storage_removed', 0)} files removed from Supabase")
    return True


async def sweep(id):
    """One run of a deleted upload's clean-up. It can be run again at any point and carries on from what is left; one run at a time."""
    row = await db.tejas_books.find_one_and_update({'_id': id, **MARK, '$expr': {'$lte': [{'$ifNull': ['$deleting.lease_until', 0]}, EPOCH_NOW]}},
        [{'$set': {'deleting.lease_until': {'$add': [EPOCH_NOW, LEASE]}, 'deleting.tries': {'$add': [{'$ifNull': ['$deleting.tries', 0]}, 1]}}}], return_document=ReturnDocument.AFTER)
    if not row:
        return None
    try:
        return await work(row)
    except Exception as exc:  # noqa: BLE001  the clean-up stays open and is tried again; nothing is half-forgotten
        log.warning('Clean-up of a deleted upload did not finish (book=%s, try %s): %s', id, row['deleting'].get('tries'), str(exc)[:200],
                    exc_info=not isinstance(exc, (store.StorageError, StillWorking)))
        await db.tejas_books.update_one({'_id': id, **MARK}, {'$set': {'deleting.lease_until': 0, 'deleting.error': str(exc)[:240], 'deleting.tried_at': now()}})
        if row['deleting'].get('tries', 0) < 4:
            from .jobs import run_later
            run_later(sweep, id, seconds=60)
        return False


async def resume():
    """Unfinished clean-ups carry on: at the 15-minute check and when Supabase answers again."""
    done = 0
    async for b in db.tejas_books.find(MARK, {'_id': 1}).limit(50):
        done += bool(await sweep(b['_id']))
    return done


async def pending():
    """For the Machine panel: clean-ups still open, and why the oldest ones wait."""
    t = now()
    rows = await db.tejas_books.find(MARK, {'payload.title': 1, 'deleting': 1}).sort('deleting.at', 1).limit(20).to_list(20)
    return {'count': len(rows), 'late': any(t - r['deleting']['at'] > LATE for r in rows),
            'items': [{'title': r['payload'].get('title', '')[:160], 'minutes': int((t - r['deleting']['at']) // 60), 'error': (r['deleting'].get('error') or '')[:200]} for r in rows[:5]]}
