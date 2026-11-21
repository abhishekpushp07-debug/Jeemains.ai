import asyncio, hashlib, os, tempfile, time, uuid
from pathlib import Path
from fastapi import HTTPException
from pymongo import ReturnDocument
from starlette.concurrency import run_in_threadpool
from .db import db, now, users
from .canonical import EPOCH_NOW
from .book_models import Book, BookPage, BookMock, BookAllowance
from .auth import owner, staff
from tejas_storage import get_object

CHUNK=512*1024
CACHE=Path(tempfile.gettempdir())/'jeelive-book-originals'


def remember(raw, sha):
    CACHE.mkdir(mode=0o700,exist_ok=True)
    target=CACHE/f'{sha}.pdf'
    fd,tmp=tempfile.mkstemp(dir=CACHE,suffix='.part')
    with os.fdopen(fd,'wb') as f:f.write(raw)
    os.replace(tmp,target)
    try:
        # Only the 6 newest stay, but a PDF used in the last 15 minutes is never removed: another request may be reading it right now.
        fresh=time.time()-900
        for old in sorted(CACHE.glob('*.pdf'),key=lambda p:p.stat().st_mtime)[:-6]:
            if old!=target and old.stat().st_mtime<fresh:old.unlink(missing_ok=True)
    except OSError:pass
    return target


def cached(sha, size, path):
    target=CACHE/f'{sha}.pdf'
    try:
        if target.stat().st_size==size:
            os.utime(target);return target
    except OSError:pass
    raw=get_object(path)
    if digest(raw)!=sha:raise ValueError('Original book integrity check failed; processing is held.')
    return remember(raw,sha)


def identity(*parts):
    return str(uuid.uuid5(uuid.NAMESPACE_URL,':'.join(str(x) for x in parts)))


def digest(raw):return hashlib.sha256(raw).hexdigest()


def normalized(value):return ' '.join(value.split()).casefold()


async def load_book(id, actor=None, include_removed=False):
    query={'_id':id}
    if actor:query['owner_id']=actor['id']
    if not include_removed:query['removed']=False
    row=await db.tejas_books.find_one(query)
    if not row:raise HTTPException(404,'Book not found.')
    return Book.from_mongo(row)


async def principal(book):
    actor=await users.find_one({'id':book.owner_id},{'_id':0})
    if not actor or actor.get('staff_auth_held'):raise HTTPException(403,'Publishing owner permission is no longer available.')
    await owner(await staff(actor))
    return actor


async def lock_book(id, revision=None):
    token=str(uuid.uuid4());query={'_id':id,'removed':False,'$expr':{'$lte':[{'$ifNull':['$lock_until',0]},EPOCH_NOW]}}
    if revision is not None:query['revision']=revision
    row=await db.tejas_books.find_one_and_update(query,[{'$set':{'lock_token':token,'lock_until':{'$add':[EPOCH_NOW,900]}}}],return_document=ReturnDocument.AFTER)
    if not row:raise HTTPException(409,'This book changed or is processing a batch. Reload and retry; saved work is retained.',headers={'Retry-After':'3'})
    return Book.from_mongo(row),token


async def lock_book_waiting(id, seconds=30):
    """Waits a little for the PDF's running batch (for example building the last paper) instead of failing at once."""
    for _ in range(int(seconds / 1.5)):
        try:
            return await lock_book(id)
        except HTTPException as e:
            if e.status_code != 409:
                raise
            await asyncio.sleep(1.5)
    raise HTTPException(409, 'This PDF is still finishing earlier work, such as building the last paper. Wait a minute, then press Give a day again. Nothing was lost.', headers={'Retry-After': '30'})


async def fence(book, token):
    await principal(book)
    if not await db.tejas_books.find_one({'_id':book.id,'lock_token':token,'removed':False,'$expr':{'$gt':['$lock_until',EPOCH_NOW]}}):
        raise HTTPException(409,'Book processing lease expired. Retry from saved progress.')


async def save_book(book, token):
    await fence(book,token)
    book.revision+=1;book.updated_at=now()
    result=await db.tejas_books.update_one({'_id':book.id,'lock_token':token,'$expr':{'$gt':['$lock_until',EPOCH_NOW]}},{'$set':book.model_dump(exclude={'id'})})
    if not result.modified_count:raise HTTPException(409,'Book changed while saving.')


async def unlock(book, token):
    await db.tejas_books.update_one({'_id':book.id,'lock_token':token},{'$unset':{'lock_token':'','lock_until':''}})


async def original(book):
    p=book.payload
    return await run_in_threadpool(cached,p['sha256'],p['size'],p['source_path'])


async def renew(book, token):
    result=await db.tejas_books.update_one({'_id':book.id,'lock_token':token,'removed':False,'$expr':{'$gt':['$lock_until',EPOCH_NOW]}},[{'$set':{'lock_until':{'$add':[EPOCH_NOW,900]}}}])
    if not result.matched_count:raise HTTPException(409,'Book processing lease expired. Retry from saved progress.')


async def pages_for(book):
    return [BookPage.from_mongo(r) async for r in db.tejas_book_pages.find({'book_id':book.id}).sort('number',1)]


async def mocks_for(book):
    return [BookMock.from_mongo(r) async for r in db.tejas_book_mocks.find({'book_id':book.id}).sort('order',1)]


async def save_mock(mock):
    await db.tejas_book_mocks.replace_one({'_id':mock.id},mock.to_mongo(),upsert=True)


async def enqueue_book(book):
    from .jobs import enqueue
    return await enqueue('book_step',book.owner_id,book.id,{'key':book.id+':'+str(book.revision),'book_id':book.id})


async def book_view(book, detail=True):
    p=book.payload
    items=await mocks_for(book) if detail else []
    from .canonical import database_now
    stamp=await database_now()
    for m in items:
        if m.state=='scheduled' and (m.release_at or p.get('release_at') or 0)<=stamp:
            m.state='published'
    counts={s:sum(m.state==s for m in items) for s in ('held','ready','published','paused','scheduled')}
    parts=await db.tejas_book_parts.find({'book_id':book.id},{'_id':0,'number':1}).to_list(None) if book.state=='uploading' else []
    allowances=[BookAllowance.from_mongo(r).model_dump(exclude={'owner_id','book_id'}) async for r in db.tejas_book_allowances.find({'book_id':book.id}).sort('created_at',-1).limit(20)] if detail else []
    linked={s['id']:s for s in await db.tejas_sets.find({'book_import_id':book.id},{'_id':0,'id':1,'archived':1,'series_date':1}).to_list(None)} if detail else {}
    series=bool((p.get('destination') or {}).get('series')) and (p['destination'].get('series_id') or 'all-india-jee-2026-27')=='all-india-jee-2026-27'
    if series:from .live_series import series_problem
    return {'id':book.id,'title':p['title'],'filename':p['filename'],'state':book.state,'revision':book.revision,
        'size':p['size'],'sha256':p['sha256'],'edition':p.get('edition',''),'chunk_size':CHUNK,'received_parts':sorted(r['number'] for r in parts),
        'pages':p.get('pages',0),'read_pages':p.get('read_pages',0),'scanned_pages':p.get('scanned_pages',0),
        'message':p.get('message',''),'auto_publish':p['auto_publish'],'paused':book.paused,'destination':p.get('destination'),
        'release_at':p.get('release_at'),'competitive':p.get('competitive',False),'closes_at':p.get('closes_at'),
        'counts':{'detected':len(items),**counts,'complete':counts['ready']+counts['published']+counts['scheduled'],
                  'awaiting_budget':sum(a['state']=='budget_required' for a in allowances)},
        'mocks':[m.model_dump(exclude={'book_id','questions'}) | {'count':len(m.questions),
            'original_solutions':sum(q.get('solution_kind')=='supplied_worked' for q in m.questions),
            'key_only':sum(q.get('solution_kind')=='answer_key_only' for q in m.questions),
            'archived':bool(linked.get(m.set_id,{}).get('archived')),
            'series_date':linked[m.set_id].get('series_date') if m.set_id in linked else m.series_date,
            'series_problem':series_problem(m) if series and m.state=='ready' else None} for m in items],
        'allowances':allowances,'created_at':book.created_at,'metrics':p.get('metrics',{}),
        'pricing_notice':'A credible per-page currency price is not available. Only the explicitly approved request allowance is used.',
        'retention_notice':'Remove import removes access; it does not permanently erase stored objects. Historical result assets are retained.'}
