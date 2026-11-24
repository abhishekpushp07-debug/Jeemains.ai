import asyncio, math, re
from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Request, Response, Query
from pymongo.errors import DuplicateKeyError
from starlette.concurrency import run_in_threadpool
from .auth import owner, current, staff
from .db import db, sets, now, audit
from .canonical import database_now
from .book_models import UploadInput, PageRepair, RuleRepair, Control, Allowance, RangeMap, QuestionFix, MockConfirm, CutFix, Book, BookPage, BookMock, UploadPart, BookAllowance
from .book_store import CHUNK, normalized, identity, digest, load_book, book_view, lock_book, save_book, unlock, fence, original, enqueue_book, mocks_for, save_mock
from .book_pdf import inspect, inspect_many
from .book_cuts import slot

router=APIRouter(prefix='/api',tags=['Source-first book publishing'])


async def dispatch(book,bg):
    # Every owner-requested run re-attempts publications that were held earlier; the worker's own chain never does.
    await db.tejas_book_mocks.update_many({'book_id':book.id,'publish_hold':{'$nin':['',None]}},{'$set':{'publish_hold':''}})
    job=await enqueue_book(book)
    from .jobs import run_job
    bg.add_task(run_job,job['id'])


@router.get('/admin/books')
async def listing(u=Depends(owner)):
    rows=await db.tejas_books.find({'owner_id':u['id'],'removed':False,'archived':{'$ne':True}}).sort('created_at',-1).limit(50).to_list(50)
    return {'items':[await book_view(Book.from_mongo(r),False) for r in rows], 'limits':{'bytes':100*1024*1024,'pages':None,'mocks':None},'model':__import__('tejas.astra',fromlist=['MODEL']).MODEL}


@router.post('/admin/books')
async def create(body:UploadInput,bg:BackgroundTasks,u=Depends(owner)):
    if not body.filename.lower().endswith('.pdf'):raise HTTPException(422,'Choose a PDF book.')
    if body.release_at and body.release_at<=await database_now():raise HTTPException(422,'Choose a future schedule or immediate publication.')
    id=identity('book',u['id'],body.sha256,body.edition.strip())
    # The same PDF may go to another section, or come back after its first copy moved to the Library.
    while (existing:=await db.tejas_books.find_one({'_id':id})):
        book=Book.from_mongo(existing)
        if book.removed:raise HTTPException(409,'This PDF was uploaded before and its access was removed, so it cannot be imported again.')
        same=(book.payload.get('destination') or {}).get('section_id')==body.section_id
        if not existing.get('archived') and same:
            if book.state=='failed':
                # The same PDF chosen again after a failure carries on from its saved pages instead of doing nothing.
                book,token=await lock_book(id)
                try:
                    book.paused=False;book.state='received' if not book.payload.get('source_path') else 'reading' if book.payload.get('read_pages',0)<book.payload.get('pages',0) else 'matching'
                    book.payload['message']='Same PDF chosen again. Carrying on from the saved pages.';await save_book(book,token)
                finally:await unlock(book,token)
                await audit(u['id'],'Book retry',id,'Same PDF uploaded again after a failure')
                await dispatch(book,bg)
            return await book_view(book)
        # A half-sent copy moved to the Library carries on from the parts it already has.
        if same and book.state=='uploading':
            await db.tejas_books.update_one({'_id':id,'archived':True},[{'$set':{'paused':{'$ifNull':['$paused_before_archive',False]}}},{'$unset':['archived','archived_at','paused_before_archive']}])
            await audit(u['id'],'Book upload resumed',id,'Half-sent copy taken back from the Library')
            return await book_view(await load_book(id,u))
        id=identity(id,'next',body.section_id)
    from .structure import destination, mark_replacing
    replace=['all'] if body.replace_all else body.replace_ids
    dest=await destination(body.section_id,('list','chapters'),replace,body.year)
    extra={}
    if dest['layout']=='chapters':
        # Chapter-wise PDF: every chapter becomes its own test; subject read from the PDF unless chosen here.
        from .chapter_reader import match_subject
        allowed=(await db.tejas_catalog_exams.find_one({'_id':dest['exam_slug']},{'subjects':1}) or {}).get('subjects') or []
        extra={'chapters':True,'subject':match_subject(body.subject,allowed)}
        if body.subject and not extra['subject']:raise HTTPException(422,'Choose one of this exam’s subjects, or Read from the PDF.')
    elif body.subject:raise HTTPException(422,'A subject is chosen only for chapter-wise PDFs.')
    book=Book(id=id,owner_id=u['id'],created_at=now(),updated_at=now(),payload=body.model_dump(exclude={'replace_ids','replace_all','year','subject'})|{'auto_publish':False,'destination':dest,'rights_attested_at':now(),'rights_attested_by':u['id'],'cut_engine':True}|extra)
    try:await db.tejas_books.insert_one(book.to_mongo())
    except DuplicateKeyError:return await book_view(await load_book(id,u))
    await mark_replacing(dest,body.title)
    await audit(u['id'],'Book upload initiated',id,f"Rights confirmed; destination {dest['exam_name']} › {dest['section_name']}; publication only on owner request")
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
    # A PDF must be a PDF inside too, not only by its name. A part that is already saved keeps its own check below.
    if number==0 and not raw.startswith(b'%PDF-') and not await db.tejas_book_parts.find_one({'_id':pid},{'_id':1}):
        raise HTTPException(422,'Yeh file PDF nahi hai. Asli PDF chuniye; sirf naam badalne se kaam nahi chalega.')
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
async def page_list(id:str,page:int=Query(1,ge=1),u=Depends(owner)):
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
        source=await original(book)
        clips=await run_in_threadpool(inspect_many,source,[{'action':'clip_text','page':number,'rect':r.rect} for r in body.regions],40) if body.regions else []
        for r,data in zip(body.regions,clips):
            if data.get('error'):raise HTTPException(422,data['error'])
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
        rows=await db.tejas_book_pages.find({'book_id':id,'number':{'$gte':body.first_page,'$lte':body.last_page}}).sort('number',1).to_list(None)
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
async def preview_crop(id:str,mid:str,qid:str,kind:str,index:int,u=Depends(staff)):
    book=await load_book(id)
    row=await db.tejas_book_mocks.find_one({'_id':mid,'book_id':id})
    if not row or (u['role']!='owner' and row['state']!='held'):raise HTTPException(404,'Mock not found.')
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
            wait=book.payload.get('storage_wait') or {}
            if wait.get('stuck'):book.payload['storage_wait']={'since':wait['since'],'at':now(),'retrying':True}  # the row says "trying again" until this try ends
            run=True
        elif body.action=='publish_ready':
            if book.state=='uploading':raise HTTPException(409,'Finish transferring the PDF first.')
            if (book.payload.get('destination') or {}).get('series'):raise HTTPException(409,'All India mocks go live on their day. Give each ready mock a day instead.')
            if body.release_at and body.release_at<=await database_now():raise HTTPException(422,'Choose a future date and time, or publish now.')
            picked=[m for m in await mocks_for(book) if m.state=='ready' and not m.issues and m.published_generation!=m.generation and (not body.mock_id or m.id==body.mock_id)]
            if not picked:raise HTTPException(409,'This mock is not ready. Fix its held problems first.' if body.mock_id else 'No mocks are ready yet. Held mocks stay private until their problems are fixed.')
            for m in picked:
                m.publish_requested=True;m.release_at=body.release_at;m.revision+=1;await save_mock(m)
            book.paused=False;book.state='matching';run=True
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
                mock.state='scheduled' if (mock.release_at or book.payload.get('release_at') or 0)>stamp else 'published'
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


async def request_publication(bid,wanted,release_at,bg,u):
    """Ask the worker to publish ready mocks of one section book (all of them when `wanted` is None)."""
    await load_book(bid,u);book,token=await lock_book(bid);picked=[]
    try:
        if book.state!='uploading' and not (book.payload.get('destination') or {}).get('series'):
            picked=[m for m in await mocks_for(book) if m.state=='ready' and not m.issues and m.published_generation!=m.generation
                    and not m.publish_requested and not m.archived and (wanted is None or m.id in wanted)]
            for m in picked:
                m.publish_requested=True;m.release_at=release_at;m.revision+=1;await save_mock(m)
            if picked:
                book.paused=False;book.state='matching';await save_book(book,token)
                await audit(u['id'],'Book publish_ready',bid,f'{len(picked)} ready mocks'+(' scheduled' if release_at else ''))
    finally:await unlock(book,token)
    if picked:await dispatch(book,bg)
    return len(picked)


def cut_view(q, mock):
    """What the fix tool shows for one question's cut: its page region, the pieces students get, or why it is held."""
    cut=q.get('cut')
    if not cut:return None
    own=mock.cuts.get(slot(q.get('coverage_key',''))) or {}
    return {'status':cut['status'],'reason':cut.get('reason',''),'arrangement':cut.get('arrangement',''),'mode':cut.get('mode','auto'),'accept_outside':bool(cut.get('accept_outside')),
            'region':cut['region'],'labels':cut.get('labels',[]),'parts':cut.get('parts',[]),'frames':cut.get('frames',[]),'draft':own.get('boxes') or cut.get('draft') or {}}


def question_problems(mock, everything=False):
    """Group a held mock's blocking issues by the question they concern; everything=True lists clean questions too."""
    out,used=[],set()
    for q in mock.questions:
        n=q['original_number'];pages=sorted({r['page'] for r in q['source_regions']['question']})
        # Warnings on its solution or key pages belong to this question too (e.g. 'Page 309, Q11').
        spages=sorted({r['page'] for k in ('solution','key') for r in q['source_regions'].get(k,[])}-set(pages))
        near=set(pages)|({pages[-1]+1} if pages else set())|set(spages)
        mine=[]
        for i,x in enumerate(mock.issues):
            m=re.match(r'Page (\d+)(?:, |: )Q(\d+)\b',x)
            if (m and int(m.group(2))==n and int(m.group(1)) in near) or x.startswith(f"{q['subject']} Q{n}:"):
                mine.append(x);used.add(i)
        if mine or everything:
            out.append({'id':q['id'],'subject':q['subject'],'section':q['section'],'number':n,'type':q['type'],'options':list(q.get('options',{})),'typed_options':q.get('typed_options',{}),
                'answer':q.get('answer',''),'issues':mine,'pages':pages,'solution_pages':spages,'next_page':pages[-1]+1 if pages else None,
                'question_images':len(q['source_regions']['question']),'solution_images':len(q['source_regions']['solution']),
                'cut':cut_view(q,mock),'has_key':bool(q['source_regions']['solution']),'confirmed':q.get('coverage_key') in mock.confirmed,'key_only_allowed':f"{q['subject']}|{q['section']}|{n}" not in mock.original_solution_identities})
    return out,[x for i,x in enumerate(mock.issues) if i not in used]


@router.get('/admin/books/{id}/mocks/{mid}/problems')
async def mock_problems(id:str,mid:str,every:bool=Query(False,alias='all'),u=Depends(staff)):
    await load_book(id);row=await db.tejas_book_mocks.find_one({'_id':mid,'book_id':id})
    if not row or (u['role']!='owner' and row['state']!='held'):raise HTTPException(404,'Mock not found.')
    mock=BookMock.from_mongo(row);questions,general=question_problems(mock,every and u['role']=='owner')
    return {'id':mock.id,'label':(mock.chapter or {}).get('title') or mock.label,'state':mock.state,'revision':mock.revision,'questions':questions,'general':general,
            'total':len(mock.questions),'rules_missing':not mock.rules,'frozen':mock.published_generation==mock.generation,'pages':mock.pages,'cut_summary':mock.cut_summary or None}


@router.get('/admin/books/{id}/mocks/{mid}/page/{number}')
async def mock_page(id:str,mid:str,number:int,u=Depends(staff)):
    """One page that holds this mock's questions, for the fix tool's boxes and the proof view."""
    book=await load_book(id)
    row=await db.tejas_book_mocks.find_one({'_id':mid,'book_id':id},{'state':1,'pages':1,'questions.cut.region.page':1,'questions.cut.parts.page':1})
    if not row or (u['role']!='owner' and row['state']!='held'):raise HTTPException(404,'Mock not found.')
    cuts=[q.get('cut') or {} for q in row.get('questions',[])]
    allowed=set((row.get('pages') or {}).get('question',[]))|{c['region']['page'] for c in cuts if c.get('region')}|{p['page'] for c in cuts for p in c.get('parts',[])}
    if number not in allowed:raise HTTPException(404,'This page holds no question of this mock.')
    try:data=await run_in_threadpool(inspect,await original(book),'page',number)
    except ValueError as exc:raise HTTPException(422,str(exc)) from None
    return Response(data['image_bytes'],media_type='image/png',headers={'Cache-Control':'private, no-store'})


@router.post('/admin/books/{id}/mocks/{mid}/cut')
async def cut_question(id:str,mid:str,body:CutFix,bg:BackgroundTasks,u=Depends(staff)):
    """Fix tool: check boxes drawn by hand (save=false is the live preview), keep them, choose the whole-picture look, or go back to the engine's own cut."""
    book=await load_book(id)
    def target(row):
        if not row or (u['role']!='owner' and row['state']!='held'):raise HTTPException(404,'Mock not found.')
        mock=BookMock.from_mongo(row)
        if mock.published_generation==mock.generation:raise HTTPException(409,'Published mocks are frozen. Create a corrected version first.')
        q=next((x for x in mock.questions if x['id']==body.question_id),None)
        if not q:raise HTTPException(404,'This question is no longer in the mock. Reload.')
        if not q.get('cut'):raise HTTPException(409,'Yeh mock naye cutter se pehle padha gaya tha. Iske sawaal kaatne ke liye PDF dobara upload karo.')
        return mock,q
    mock,q=target(await db.tejas_book_mocks.find_one({'_id':mid,'book_id':id}))
    if u['role']!='owner' and (body.mode=='whole' or body.accept_outside):raise HTTPException(403,'Poori picture wala look ya override sirf owner chun sakta hai.')
    region=q['cut']['region'];over={'mode':'whole'}
    # An option the owner typed needs no picture, so it needs no box.
    labels=[x for x in q.get('options',{}) if x not in q.get('typed_options',{})] if q['type']=='mcq' else []
    if body.mode=='boxes':
        need=['q',*labels]
        if set(body.boxes)!=set(need) or any(len(b)!=4 or not (0<=b[0]<b[2]<=1 and 0<=b[1]<b[3]<=1) for b in body.boxes.values()):
            raise HTTPException(422,'Sawaal ka ek box banao'+(' aur options '+', '.join(labels)+' me har ek ka ek box' if labels else '')+'.')
        boxes={k:[round(float(x),5) for x in body.boxes[k]] for k in need}
        try:result=(await run_in_threadpool(inspect_many,await original(book),[{'action':'boxes','page':region['page'],'rect':region['rect'],'labels':labels,'boxes':boxes}],1))[0]
        except ValueError as exc:raise HTTPException(422,str(exc)) from None
        if result.get('error'):raise HTTPException(422,result['error'])
        c=result['cut'];outside=bool(c.get('outside'))
        reason=c.get('reason') or ('Is sawaal ka kuch chhapa hua hissa kisi bhi box me nahi aaya.' if outside and not body.accept_outside else '')
        checked={'ok':c['status']=='manual' and not reason,'reason':reason,'outside':outside,'page':region['page'],'size':c.get('size'),'pieces':c.get('pieces',{})}
        if not body.save:return checked
        if not checked['ok']:raise HTTPException(422,reason)
        over={'mode':'boxes','page':region['page'],'boxes':boxes,'accept_outside':bool(body.accept_outside and outside)}
    elif not body.save:return {'ok':True,'reason':'','outside':False,'page':region['page'],'pieces':{}}
    await load_book(id);book,token=await lock_book(id)
    try:
        mock,q=target(await db.tejas_book_mocks.find_one({'_id':mid,'book_id':id}))
        if mock.revision!=body.revision:raise HTTPException(409,'This mock was rechecked a moment ago. Reload and try again.')
        key=slot(q['coverage_key'])
        if body.mode=='auto':mock.cuts.pop(key,None)
        else:mock.cuts[key]=over
        mock.revision+=1;await save_mock(mock)
        book.state='matching';await save_book(book,token)
        note={'boxes':'boxes drawn by hand','whole':'shown as one whole picture','auto':'back to the automatic cut'}[body.mode]
        await audit(u['id'],'Book question cut',mid,f"{mock.label} {q['subject']} Q{q['original_number']}: {note}"+(' · owner override: marks outside the boxes accepted' if over.get('accept_outside') else ''))
    finally:await unlock(book,token)
    if not book.paused:await dispatch(book,bg)
    return {'ok':True,'saved':True,'message':f"{q['subject']} Q{q['original_number']} save ho gaya. {mock.label} dobara check ho raha hai…"}


@router.post('/admin/books/{id}/mocks/{mid}/fix')
async def fix_question(id:str,mid:str,body:QuestionFix,bg:BackgroundTasks,u=Depends(staff)):
    await load_book(id);book,token=await lock_book(id)
    try:
        row=await db.tejas_book_mocks.find_one({'_id':mid,'book_id':id})
        if not row:raise HTTPException(404,'Mock not found.')
        mock=BookMock.from_mongo(row)
        if u['role']!='owner' and mock.state!='held':raise HTTPException(404,'Mock not found.')
        if body.confirmed and u['role']!='owner':raise HTTPException(403,'Only the owner can clear the warnings of a question.')
        if mock.revision!=body.revision:raise HTTPException(409,'This mock was rechecked a moment ago. Reload and try again.')
        if mock.published_generation==mock.generation:raise HTTPException(409,'Published mocks are frozen. Create a corrected version first.')
        q=next((x for x in mock.questions if x['id']==body.question_id),None)
        if not q:raise HTTPException(404,'This question is no longer in the mock. Reload.')
        mcq=body.response_type=='mcq';labels=list(dict.fromkeys(body.option_labels)) if mcq else []
        answer=body.answer.strip().upper() if mcq else body.answer.strip()
        if mcq and (len(labels)<2 or answer not in labels):raise HTTPException(422,'Tick at least two printed options and choose the correct one among them.')
        if not mcq and not re.fullmatch(r'[+-]?\d{1,20}',answer):raise HTTPException(422,'A numerical answer must be a whole number, for example 12 or -3.')
        texts={k:v.strip() for k,v in body.option_texts.items() if mcq and k in labels and v.strip()}
        if any(len(v)>2000 for v in texts.values()):raise HTTPException(422,'Keep each typed option under 2,000 characters.')
        n=q['original_number'];label=normalized(mock.label);ident=(normalized(q['subject']),normalized(q['section']),n)
        coverage=f"{q['subject']}|{q['section']}|{n}"
        if body.key_only:
            if coverage in mock.original_solution_identities:raise HTTPException(409,'This book prints a worked solution for this question. Attach it in the page editor instead.')
            if not mock.rules:raise HTTPException(409,'Confirm this mock’s rules first, then mark key-only questions.')
        qpages=sorted({r['page'] for r in q['source_regions']['question']})
        near=set(qpages)|({qpages[-1]+1} if qpages else set())
        raw={r['_id']:r for r in await db.tejas_book_pages.find({'book_id':id,'number':{'$in':sorted(near|{p for v in mock.pages.values() for p in v})}}).to_list(None)}
        pages=sorted((BookPage.from_mongo(r) for r in raw.values()),key=lambda p:p.number)
        mine=lambda r:normalized(r.mock)==label and r.number==n
        exact=lambda r:(normalized(r.subject),normalized(r.section or r.subject),r.number)==ident
        keys=[(p,r) for p in pages for r in p.regions if mine(r) and r.role in ('key','solution') and exact(r)] or \
             [(p,r) for p in pages for r in p.regions if mine(r) and r.role in ('key','solution')]
        if not keys:raise HTTPException(409,'No printed answer key was found for this question. Open the page editor and mark where its key is printed.')
        changed={}
        for p in pages:
            for r in p.regions:
                if mine(r) and r.role=='question' and exact(r):
                    r.response_type=body.response_type;r.complete=True;r.checked=True;r.option_labels=[] if r.continuation else labels
                    r.option_texts={} if r.continuation else texts
                    changed[p.number]=p
            if p.number in near:
                kept=[x for x in p.issues if not re.match(rf'Q{n}\b',x)]
                if kept!=p.issues:p.issues=kept;changed[p.number]=p
        for p,r in keys:
            r.answer=answer;r.checked=True;changed[p.number]=p
        note=f"Quick fix: {mock.label} {q['subject']} Q{n} = {answer} ({body.response_type})"+(f" · typed options {','.join(texts)}" if texts else '')
        for p in changed.values():
            p.revision+=1;p.provenance={'kind':'owner_repair','actor':u['id'],'at':now(),'note':note,'previous':p.provenance.get('kind','native')}
            await fence(book,token)
            await db.tejas_book_page_history.update_one({'_id':identity(p.id,p.revision)},{'$setOnInsert':{'book_id':id,'before':raw[p.id],'after':p.to_mongo(),'note':note,'actor':u['id']}},upsert=True)
            await db.tejas_book_pages.replace_one({'_id':p.id},p.to_mongo())
        if body.key_only:
            if mock.rules.get('solution_policy')=='original_expected':mock.rules['solution_policy']='mixed'
            if mock.rules.get('solution_policy')=='mixed' and coverage not in mock.rules.setdefault('key_only',[]):mock.rules['key_only'].append(coverage)
        if body.confirmed and coverage not in mock.confirmed:mock.confirmed.append(coverage)
        if body.key_only or body.confirmed:
            mock.revision+=1;await save_mock(mock)
        book.state='matching';await save_book(book,token)
        await audit(u['id'],'Book question quick fix',mid,note+(' · key only' if body.key_only else '')+(' · owner checked, warnings cleared' if body.confirmed else ''))
    finally:await unlock(book,token)
    if not book.paused:await dispatch(book,bg)
    return {'ok':True,'message':f"Saved {q['subject']} Q{n}. Rechecking {mock.label}…"}


@router.post('/admin/books/{id}/mocks/{mid}/confirm-all')
async def confirm_all(id:str,mid:str,body:MockConfirm,bg:BackgroundTasks,u=Depends(owner)):
    """Owner override for a whole Draft mock: every question was checked by eye, so the reader's warnings about questions no longer hold it."""
    await load_book(id,u);book,token=await lock_book(id)
    try:
        row=await db.tejas_book_mocks.find_one({'_id':mid,'book_id':id})
        if not row:raise HTTPException(404,'Mock not found.')
        mock=BookMock.from_mongo(row)
        if mock.revision!=body.revision:raise HTTPException(409,'This mock was rechecked a moment ago. Reload and try again.')
        if mock.published_generation==mock.generation:raise HTTPException(409,'Published mocks are frozen. Create a corrected version first.')
        mock.confirmed=list(dict.fromkeys(mock.confirmed+[q['coverage_key'] for q in mock.questions if q.get('coverage_key')]))
        mock.revision+=1;await save_mock(mock)
        book.state='matching';await save_book(book,token)
        await audit(u['id'],'Book mock owner override',mid,f'{mock.label}: owner checked all {len(mock.questions)} questions; their warnings cleared')
    finally:await unlock(book,token)
    if not book.paused:await dispatch(book,bg)
    return {'ok':True,'message':f'Warnings cleared for {mock.label}. Rechecking…'}


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
            selected=await db.tejas_book_pages.find({'book_id':id,'number':{'$in':targets}},{'regions.mock':1}).to_list(None)
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
    rows=await sets.find(query,PROJECT|{'book_series_title':1,'test_kind':1,'full_length':1}).sort('mock_number',1).to_list(None)
    if not rows:raise HTTPException(404,'No released mocks in this series.')
    from .structure import path_for, visibility
    await visibility()
    return {'id':id,'title':rows[0]['book_series_title'],'published_count':len(rows),'path':await path_for(rows[0]),'items':[summary(s) for s in rows]}
