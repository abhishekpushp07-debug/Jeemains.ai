import asyncio, math
from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Request, Response, Query
from pymongo.errors import DuplicateKeyError
from starlette.concurrency import run_in_threadpool
from .auth import owner, current
from .db import db, sets, now, audit
from .canonical import database_now
from .book_models import UploadInput, PageRepair, RuleRepair, Control, Allowance, RangeMap, Book, BookPage, BookMock, UploadPart, BookAllowance
from .book_store import CHUNK, normalized, identity, digest, load_book, book_view, lock_book, save_book, unlock, fence, original, enqueue_book, mocks_for, save_mock
from .book_pdf import inspect

router=APIRouter(prefix='/api',tags=['Source-first book publishing'])


async def dispatch(book,bg):
    job=await enqueue_book(book)
    from .jobs import run_job
    bg.add_task(run_job,job['id'])


@router.get('/admin/books')
async def listing(u=Depends(owner)):
    rows=await db.tejas_books.find({'owner_id':u['id'],'removed':False}).sort('created_at',-1).limit(50).to_list(50)
    return {'items':[await book_view(Book.from_mongo(r),False) for r in rows], 'limits':{'bytes':50*1024*1024,'pages':1000,'mocks':50},'model':__import__('tejas.astra',fromlist=['MODEL']).MODEL}


@router.post('/admin/books')
async def create(body:UploadInput,u=Depends(owner)):
    if not body.filename.lower().endswith('.pdf'):raise HTTPException(422,'Choose a PDF book.')
    if body.release_at and body.release_at<=await database_now():raise HTTPException(422,'Choose a future schedule or immediate publication.')
    id=identity('book',u['id'],body.sha256,body.edition.strip())
    existing=await db.tejas_books.find_one({'_id':id})
    if existing:
        book=Book.from_mongo(existing)
        if book.removed:raise HTTPException(409,'Access was removed from this import. Use a new edition label to deliberately create a new import.')
        return await book_view(book)
    book=Book(id=id,owner_id=u['id'],created_at=now(),updated_at=now(),payload=body.model_dump()|{'rights_attested_at':now(),'rights_attested_by':u['id']})
    try:await db.tejas_books.insert_one(book.to_mongo())
    except DuplicateKeyError:return await book_view(await load_book(id,u))
    await audit(u['id'],'Book upload initiated',id,'Rights confirmed; automatic clean publication selected='+str(body.auto_publish))
    return await book_view(book)


@router.get('/admin/books/{id}')
async def read(id:str,u=Depends(owner)):
    return await book_view(await load_book(id,u))


@router.put('/admin/books/{id}/parts/{number}')
async def part(id:str,number:int,request:Request,sha256:str=Query(...,pattern=r'^[a-f0-9]{64}$'),u=Depends(owner)):
    book=await load_book(id,u)
    if book.state!='uploading':raise HTTPException(409,'Upload is already complete; open its progress.')
    total=math.ceil(book.payload['size']/CHUNK)
    if not 0<=number<total:raise HTTPException(422,'Part number is outside this file.')
    if request.headers.get('content-type','').split(';')[0]!='application/octet-stream':raise HTTPException(415,'Use binary upload parts.')
    if request.headers.get('content-encoding','identity')!='identity':raise HTTPException(415,'Encoded parts are not accepted.')
    expected=min(CHUNK,book.payload['size']-number*CHUNK);data=bytearray()
    async def receive():
        async for chunk in request.stream():
            data.extend(chunk)
            if len(data)>expected:raise HTTPException(413,'Upload part exceeds its declared size.')
    try:await asyncio.wait_for(receive(),30)
    except asyncio.TimeoutError:raise HTTPException(408,'Upload part interrupted. Retry this part.') from None
    if len(data)!=expected:raise HTTPException(422,'Upload part is incomplete.')
    raw=bytes(data)
    if digest(raw)!=sha256:raise HTTPException(422,'Upload part checksum mismatch. Retry this part; no bytes were saved.')
    pid=identity(id,'part',number)
    value=UploadPart(id=pid,book_id=id,number=number,sha256=digest(raw),data=raw)
    try:await db.tejas_book_parts.insert_one(value.to_mongo())
    except DuplicateKeyError:
        old=UploadPart.from_mongo(await db.tejas_book_parts.find_one({'_id':pid}))
        if old.sha256!=value.sha256:raise HTTPException(409,'This part belongs to different bytes. Reselect the exact original file.')
    return {'number':number,'received_bytes':expected}


@router.post('/admin/books/{id}/complete')
async def complete(id:str,bg:BackgroundTasks,u=Depends(owner)):
    await load_book(id,u);book,token=await lock_book(id)
    try:
        if book.state=='uploading':
            count=await db.tejas_book_parts.count_documents({'book_id':id})
            if count!=math.ceil(book.payload['size']/CHUNK):raise HTTPException(409,'Some parts are missing. Reselect the same file to resume.')
            book.state='received';book.payload['message']='Transfer complete. Validating the original PDF.';await save_book(book,token)
    finally:await unlock(book,token)
    if book.state in ('received','reading','matching'):await dispatch(book,bg)
    return await book_view(book)


@router.get('/admin/books/{id}/pages')
async def page_list(id:str,page:int=Query(1,ge=1,le=1000),u=Depends(owner)):
    book=await load_book(id,u)
    rows=await db.tejas_book_pages.find({'book_id':id}).sort('number',1).skip((page-1)*25).limit(25).to_list(25)
    return {'items':[BookPage.from_mongo(r).model_dump(exclude={'text','context','regions'}) | {'region_count':len(r.get('regions',[]))} for r in rows],'total':book.payload.get('pages',0),'page':page}


@router.get('/admin/books/{id}/pages/{number}')
async def page_detail(id:str,number:int,u=Depends(owner)):
    await load_book(id,u);row=await db.tejas_book_pages.find_one({'book_id':id,'number':number})
    if not row:raise HTTPException(404,'Page has not been read yet.')
    return BookPage.from_mongo(row).model_dump()


@router.get('/admin/books/{id}/pages/{number}/image')
async def page_image(id:str,number:int,u=Depends(owner)):
    book=await load_book(id,u)
    data=await run_in_threadpool(inspect,await original(book),'page',number)
    return Response(data['image_bytes'],media_type='image/png',headers={'Cache-Control':'private, no-store'})


@router.put('/admin/books/{id}/pages/{number}')
async def repair_page(id:str,number:int,body:PageRepair,bg:BackgroundTasks,u=Depends(owner)):
    await load_book(id,u);book,token=await lock_book(id)
    try:
        row=await db.tejas_book_pages.find_one({'book_id':id,'number':number})
        if not row:raise HTTPException(404,'Page not found.')
        page=BookPage.from_mongo(row)
        if page.revision!=body.revision:raise HTTPException(409,'Page changed elsewhere. Reload before saving.')
        mocks=await mocks_for(book)
        frozen={normalized(m.label) for m in mocks if m.published_generation==m.generation}
        if any(normalized(r.mock) in frozen for r in page.regions+body.regions):raise HTTPException(409,'Published regions are frozen. Create a corrected version for that mock before editing.')
        if body.classification in ('questions','solutions','answer_key','mixed') and not body.regions:raise HTTPException(422,'Mapped content needs source regions.')
        raw=await original(book)
        for r in body.regions:
            data=await run_in_threadpool(inspect,raw,'crop',number,r.rect)
            if not page.scanned:r.text=data['text']
            if r.role!='question':r.option_labels=[]
            if r.role in ('question','key','solution') and (not r.mock or not r.subject or not r.number):raise HTTPException(422,'Every source item needs its mock, subject and printed number.')
        page.classification=body.classification;page.regions=body.regions;page.issues=body.issues;page.revision+=1
        page.provenance={'kind':'owner_repair','actor':u['id'],'at':now(),'note':body.note,'previous':page.provenance.get('kind','native')}
        await fence(book,token)
        await db.tejas_book_page_history.insert_one({'_id':identity(page.id,page.revision),'book_id':id,'before':row,'after':page.to_mongo(),'note':body.note,'actor':u['id']})
        await db.tejas_book_pages.replace_one({'_id':page.id,'revision':body.revision},page.to_mongo())
        book.state='matching';await save_book(book,token)
        await audit(u['id'],'Book page repaired',id,f'Page {number}: '+body.note)
    finally:await unlock(book,token)
    if not book.paused:await dispatch(book,bg)
    return page.model_dump()


@router.post('/admin/books/{id}/map-range')
async def map_range(id:str,body:RangeMap,bg:BackgroundTasks,u=Depends(owner)):
    await load_book(id,u);book,token=await lock_book(id,body.revision)
    try:
        if body.first_page>body.last_page or body.last_page>book.payload.get('read_pages',0):raise HTTPException(422,'Choose a received page range in reading order.')
        mocks=await mocks_for(book)
        frozen={normalized(m.label) for m in mocks if m.published_generation==m.generation}
        rows=await db.tejas_book_pages.find({'book_id':id,'number':{'$gte':body.first_page,'$lte':body.last_page}}).sort('number',1).to_list(1000)
        if normalized(body.mock) in frozen or any(normalized(r.get('mock','')) in frozen for row in rows for r in row.get('regions',[])):
            raise HTTPException(409,'Create corrected versions before remapping published regions.')
        for row in rows:
            page=BookPage.from_mongo(row)
            for r in page.regions:
                if r.role=='ignore':continue
                r.mock=body.mock
                if body.subject:r.subject=body.subject;r.section=body.subject
                if r.role not in ('instructions','shared'):r.role=body.role
                r.checked=False
            page.revision+=1
            page.provenance={'kind':'owner_repair','actor':u['id'],'at':now(),'note':body.note}
            page.issues=list(dict.fromkeys(page.issues+['Range reassigned; confirm the original regions and associations.']))
            await fence(book,token)
            await db.tejas_book_pages.replace_one({'_id':page.id},page.to_mongo())
        book.state='matching';await save_book(book,token)
        await audit(u['id'],'Book range mapped',id,f'Pages {body.first_page}–{body.last_page}: '+body.note)
    finally:await unlock(book,token)
    if not book.paused:await dispatch(book,bg)
    return await book_view(book)


@router.get('/admin/books/{id}/mocks/{mid}')
async def mock_detail(id:str,mid:str,u=Depends(owner)):
    await load_book(id,u);row=await db.tejas_book_mocks.find_one({'_id':mid,'book_id':id})
    if not row:raise HTTPException(404,'Mock not found.')
    return BookMock.from_mongo(row).model_dump()


@router.get('/admin/books/{id}/mocks/{mid}/questions/{qid}/asset/{kind}/{index}')
async def preview_crop(id:str,mid:str,qid:str,kind:str,index:int,u=Depends(owner)):
    book=await load_book(id,u)
    row=await db.tejas_book_mocks.find_one({'_id':mid,'book_id':id})
    if not row:raise HTTPException(404,'Mock not found.')
    mock=BookMock.from_mongo(row)
    q=next((q for q in mock.questions if q['id']==qid),None)
    refs=(q or {}).get('source_regions',{}).get(kind,[]) if kind in ('question','solution') else []
    if not 0<=index<len(refs):raise HTTPException(404,'Source region not found.')
    ref=refs[index]
    data=await run_in_threadpool(inspect,await original(book),'crop',ref['page'],ref['rect'])
    return Response(data['image_bytes'],media_type='image/png',headers={'Cache-Control':'private, no-store'})


@router.put('/admin/books/{id}/mocks/{mid}/rules')
async def rules(id:str,mid:str,body:RuleRepair,bg:BackgroundTasks,u=Depends(owner)):
    await load_book(id,u);book,token=await lock_book(id)
    try:
        row=await db.tejas_book_mocks.find_one({'_id':mid,'book_id':id})
        if not row:raise HTTPException(404,'Mock not found.')
        mock=BookMock.from_mongo(row)
        if mock.revision!=body.revision:raise HTTPException(409,'Mock changed elsewhere. Reload before saving.')
        if mock.published_generation==mock.generation:raise HTTPException(409,'Create a corrected version; published rules and keys stay immutable.')
        if any(not 1<=p<=book.payload.get('pages',0) for p in body.rules.source_pages):raise HTTPException(422,'Rule evidence pages must belong to this book.')
        mock.rules=body.rules.model_dump();mock.revision+=1;await save_mock(mock)
        book.state='matching';await save_book(book,token)
        await audit(u['id'],'Book rules clarified',mid,body.rules.note)
    finally:await unlock(book,token)
    if not book.paused:await dispatch(book,bg)
    return mock.model_dump()


@router.post('/admin/books/{id}/control')
async def control(id:str,body:Control,bg:BackgroundTasks,u=Depends(owner)):
    await load_book(id,u);book,token=await lock_book(id,body.revision);run=False
    try:
        if body.action=='pause':book.paused=True;book.state='paused'
        elif body.action=='remove':
            book.paused=True
            await sets.update_many({'book_import_id':id},{'$set':{'status':'withdrawn','live_enabled':False}})
            await save_book(book,token)
            await db.tejas_books.update_one({'_id':id,'lock_token':token},{'$set':{'removed':True,'state':'removed'}})
            await audit(u['id'],'Book remove',id,body.reason or 'Owner removed source access; history retained.')
            return {'removed':True,'message':'Access removed, not physically erased. Historical results and their assets are retained.'}
        elif body.action in ('resume','retry','publish'):
            if book.state=='uploading':raise HTTPException(409,'Finish transferring the PDF first.')
            book.paused=False;book.state='received' if not book.payload.get('source_path') else 'reading' if book.payload.get('read_pages',0)<book.payload.get('pages',0) else 'matching'
            if body.action=='publish':book.payload['auto_publish']=True
            run=True
        else:
            row=await db.tejas_book_mocks.find_one({'_id':body.mock_id,'book_id':id})
            if not row:raise HTTPException(404,'Mock not found.')
            mock=BookMock.from_mongo(row)
            if not body.reason.strip():raise HTTPException(422,'Record the reason for this publishing change.')
            if body.action=='pause_mock':
                if mock.set_id:await sets.update_one({'id':mock.set_id,'book_import_id':id},{'$set':{'status':'withdrawn','live_enabled':False}})
                mock.state='paused'
            elif body.action=='resume_mock':
                if mock.state!='paused' or mock.published_generation!=mock.generation or not mock.set_id:raise HTTPException(409,'Only a paused, unchanged published mock can resume.')
                stamp=await database_now()
                if book.payload.get('competitive') and stamp>=book.payload['closes_at']:raise HTTPException(409,'The competitive window has closed; publish a new edition instead.')
                await sets.update_one({'id':mock.set_id,'book_import_id':id},{'$set':{'status':'published','live_enabled':True}})
                mock.state='scheduled' if (book.payload.get('release_at') or 0)>stamp else 'published'
            elif body.action=='new_version':
                if mock.published_generation!=mock.generation:raise HTTPException(409,'A draft version already exists.')
                mock.generation+=1;mock.state='held';mock.issues=['Corrected version created; repair source pages and recheck before publication.']
                book.paused=True;book.state='paused'
            elif body.action=='release_now':
                if book.payload.get('competitive'):raise HTTPException(409,'Competitive windows cannot launch late. Create a new edition with a future schedule.')
                mock.release_override=True;mock.missed_release=False;book.state='matching';run=True
            mock.revision+=1;await save_mock(mock)
        await save_book(book,token);await audit(u['id'],'Book '+body.action,id,body.reason)
    finally:await unlock(book,token)
    if run and not book.paused:await dispatch(book,bg)
    return await book_view(book)


@router.post('/admin/books/{id}/allowances')
async def allowance(id:str,body:Allowance,bg:BackgroundTasks,u=Depends(owner)):
    await load_book(id,u);book,token=await lock_book(id,body.revision)
    try:
        if book.payload.get('read_pages',0)!=book.payload.get('pages',-1):raise HTTPException(409,'Finish inspection before approving paid work.')
        targets=list(dict.fromkeys(body.pages if body.purpose=='reading' else body.question_ids))
        if not targets:raise HTTPException(422,'Select the exact pages or questions to process.')
        if body.purpose=='reading':
            if any(not 1<=p<=book.payload['pages'] for p in targets):raise HTTPException(422,'Selected pages must belong to this book.')
            published={normalized(m.label) for m in await mocks_for(book) if m.published_generation==m.generation}
            selected=await db.tejas_book_pages.find({'book_id':id,'number':{'$in':targets}}).to_list(1000)
            if any(normalized(r.get('mock','')) in published for p in selected for r in p.get('regions',[])):raise HTTPException(409,'Create a corrected mock version before re-reading published regions.')
        else:
            papers=await sets.find({'book_import_id':id,'questions.id':{'$in':targets}},{'questions':1}).to_list(100)
            eligible={q['id'] for s in papers for q in s['questions'] if q.get('solution_kind')=='answer_key_only' and not q.get('ai_solution') and q.get('answer')}
            if not set(targets)<=eligible:raise HTTPException(422,'Only complete, published key-only questions without saved explanations are eligible.')
        aid=identity(id,body.request_id)
        existing=await db.tejas_book_allowances.find_one({'_id':aid})
        if existing:
            a=BookAllowance.from_mongo(existing)
            if a.targets!=targets or a.max_requests!=body.max_requests or a.purpose!=body.purpose:raise HTTPException(409,'This approval identifier belongs to different work.')
        else:
            a=BookAllowance(id=aid,book_id=id,owner_id=u['id'],purpose=body.purpose,targets=targets,max_requests=body.max_requests,created_at=now())
            await db.tejas_book_allowances.insert_one(a.to_mongo())
        book.state='matching';await save_book(book,token)
        await audit(u['id'],'Book AI allowance approved',id,f'{body.purpose}: {len(targets)} targets, at most {body.max_requests} requests')
    finally:await unlock(book,token)
    if not book.paused:await dispatch(book,bg)
    return await book_view(book)


@router.get('/book-series')
async def series_list(u=Depends(current)):
    from .catalog import available
    query=available(u);query['book_import_id']={'$exists':True}
    rows=await sets.aggregate([{'$match':query},{'$group':{'_id':'$book_import_id','title':{'$first':'$book_series_title'},'published_count':{'$sum':1}}},{'$limit':100}]).to_list(100)
    return {'items':[{'id':r['_id'],'title':r['title'],'published_count':r['published_count']} for r in rows]}


@router.get('/book-series/{id}')
async def series_detail(id:str,u=Depends(current)):
    from .catalog import available,PROJECT
    from .content import summary
    query=available(u);query['book_import_id']=id
    rows=await sets.find(query,PROJECT|{'book_series_title':1}).sort('mock_number',1).limit(50).to_list(50)
    if not rows:raise HTTPException(404,'No released mocks in this series.')
    return {'id':id,'title':rows[0]['book_series_title'],'published_count':len(rows),'items':[summary(s) for s in rows]}
