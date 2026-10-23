"""Single-PDF chapter books: frozen sources, independently checked chapters, personal timers."""
import asyncio
import hashlib
import json
from pathlib import Path
import tempfile
import uuid
from datetime import datetime, timezone
from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Request, Response
from pydantic import BaseModel, ConfigDict, Field
from pymongo import ReturnDocument
from starlette.concurrency import run_in_threadpool
from .auth import owner, staff, current
from .db import db, sets, files, attempts, uid, now, get, audit
from .sandbox import organise_pdfs
from .content import valid_rules, summary
from .catalog import available, PROJECT
from .derivatives import render_crop
from tejas_storage import put_object, get_object, StorageError

router=APIRouter(prefix='/api',tags=['Chapter exams'])
books=db.tejas_chapter_books
SLOTS=asyncio.Semaphore(1)

class ChapterAction(BaseModel):
    model_config=ConfigDict(extra='forbid',strict=True)
    revision:int=Field(ge=0)

class ChapterLive(ChapterAction):
    live:bool

class ChapterView(BaseModel):
    id:str
    title:str
    chapter_number:int
    subject:str
    count:int
    status:str
    start_page:int
    end_page:int
    key_page:int
    verification:dict
    independent_check:dict|None=None
    revision:int
    start_at:float|None=None
    end_at:float|None=None
    live_enabled:bool=False
    rules:dict=Field(default_factory=dict)
    solution_kind:str='answer_key_only'

class BookView(BaseModel):
    id:str
    title:str
    subject:str=''
    exam:str='BITSAT'
    minutes:int=60
    solution_kind:str='answer_key_only'
    status:str
    message:str=''
    revision:int=0
    count:int=0
    pages:int=0
    chapters:list[ChapterView]=[]
    source_sha256:str=''
    server_now:float

class BookList(BaseModel):
    items:list[BookView]

class ChapterPreview(BaseModel):
    chapter:ChapterView
    questions:list[dict]

class ExamList(BaseModel):
    items:list[dict]
    total:int
    page:int
    pages:int
    subject_counts:dict


def chapter_view(s):
    state='expired' if s.get('end_at',float('inf'))<=now() else ('live' if s.get('live_enabled') else 'unlive') if s.get('start_at') else 'ready' if s.get('independent_check') else 'needs_review'
    return ChapterView(id=s['id'],title=s['title'],chapter_number=s['chapter_number'],subject=s['chapter_subject'],
        count=len(s['questions']),status=state,start_page=s['start_page'],end_page=s['end_page'],key_page=s['key_page'],
        verification=s['verification'],independent_check=s.get('independent_check'),revision=s['revision'],
        start_at=s.get('start_at'),end_at=s.get('end_at'),live_enabled=s.get('live_enabled',False),
        rules=s.get('rules',{}),solution_kind=s.get('solution_kind','answer_key_only'))


# Metadata-only read: polling must not deserialize every question, key and crop.
BOOK_CHAPTER_PROJECT = {key: 1 for key in (
    'id', 'title', 'chapter_number', 'chapter_subject', 'questions.number',
    'start_page', 'end_page', 'key_page', 'verification', 'independent_check',
    'revision', 'start_at', 'end_at', 'live_enabled', 'rules', 'solution_kind',
)}
BOOK_CHAPTER_PROJECT['_id'] = 0

async def book_view(r):
    children=await sets.find({'chapter_book_id':r['id']},BOOK_CHAPTER_PROJECT).sort('chapter_number',1).limit(60).to_list(60)
    status=r['status']
    if status=='organising' and r.get('lease_until',0)<now():status='interrupted'
    return BookView(id=r['id'],title=r['title'],subject=r.get('subject',''),status=status,message=r.get('message',''),
        exam=r.get('exam','BITSAT'),minutes=r.get('minutes',60),solution_kind=r.get('solution_kind','answer_key_only'),
        revision=r.get('revision',0),count=sum(len(s['questions']) for s in children),pages=r.get('pages',0),
        chapters=[chapter_view(s) for s in children],source_sha256=r['source']['sha256'],server_now=now())


def independent_evidence(sha, parsed_sha, chapter, subject):
    path=Path('/app/test_reports/chapter50_recheck.json')
    if not path.exists(): return None
    try: entries=json.loads(path.read_text())['chapters']
    except (ValueError,KeyError): return None
    match=next((e for e in entries if e.get('source_sha256')==sha and e.get('parsed_sha256')==parsed_sha and e.get('chapter_number')==chapter['number'] and e.get('title')==chapter['title'] and e.get('subject','').lower()==subject.lower()),None)
    if match and match.get('status')=='PASS' and match.get('matched_keys')==50 and not match.get('issues'):
        return {'method':'Independent testing-agent source audit','scope':'50 questions, 50 source-key matches, safe source regions; not academic solution certification',
                'source_sha256':sha,'parsed_sha256':parsed_sha,'checked_at':now(),'report':'chapter50_recheck.json'}
    return None


@router.get('/studio/chapter-books',response_model=BookList)
async def list_books(u=Depends(staff)):
    records=await books.find({'qa_only':{'$ne':True}},{'_id':0}).sort('created_at',-1).limit(30).to_list(30)
    return BookList(items=[await book_view(r) for r in records])


@router.post('/studio/chapter-books',response_model=BookView,status_code=202)
async def upload_book(request:Request,bg:BackgroundTasks,u=Depends(owner)):
    async with request.form(max_files=1,max_fields=1) as form:
        if set(form.keys())!={'file','request_id'} or len(form.multi_items())!=2: raise HTTPException(422,'Upload one chapter-book PDF and its request identifier.')
        try: request_id=str(uuid.UUID(str(form['request_id'])))
        except ValueError: raise HTTPException(422,'A UUID upload identifier is required.')
        f=form['file']
        if not hasattr(f,'read') or not (f.filename or '').lower().endswith('.pdf'):raise HTTPException(422,'Choose a searchable PDF chapter book.')
        raw=await f.read(50*1024*1024+1)
        if not raw.startswith(b'%PDF-') or len(raw)>50*1024*1024:raise HTTPException(422,'Use a valid PDF under50MB.')
        sha=hashlib.sha256(raw).hexdigest(); identity=str(uuid.uuid5(uuid.NAMESPACE_URL,u['id']+':chapter:'+sha))
        receipt=str(uuid.uuid5(uuid.NAMESPACE_URL,u['id']+':chapter-request:'+request_id))
        await db.tejas_chapter_uploads.update_one({'id':receipt},{'$setOnInsert':{'id':receipt,'sha256':sha}},upsert=True)
        prior=await db.tejas_chapter_uploads.find_one({'id':receipt})
        if prior['sha256']!=sha:raise HTTPException(409,'That upload identifier belongs to a different file.')
        old=await books.find_one({'id':identity},{'_id':0})
        if old:return await book_view(old)
        if SLOTS.locked():raise HTTPException(429,'A chapter book is processing. Retry shortly.',headers={'Retry-After':'5'})
        fid=str(uuid.uuid5(uuid.UUID(identity),'source'))
        path=await run_in_threadpool(put_object,f'tejas/chapter-books/{identity}/{fid}.pdf',raw)
        source={'id':fid,'path':path,'sha256':sha,'kind':'combined','name':Path(f.filename).name[:160],'size':len(raw),'set_id':identity,'created_at':now(),'is_deleted':False}
        await files.update_one({'id':fid},{'$setOnInsert':source},upsert=True)
        record={'id':identity,'title':Path(f.filename).stem.replace('_',' ')[:160],'source':source,'status':'queued','revision':0,'created_at':now(),'created_by':u['id']}
        await books.update_one({'id':identity},{'$setOnInsert':record},upsert=True)
        bg.add_task(process_book,identity)
        return await book_view(record)


async def process_book(identity):
    async with SLOTS:
        token=uid()
        r=await books.find_one_and_update({'id':identity,'$or':[{'status':{'$in':['queued','failed']}},{'status':'organising','lease_until':{'$lt':now()}}]},
            {'$set':{'status':'organising','lease_token':token,'lease_until':now()+600,'message':'Reading chapters, verifying two key extractions and preserving original notation…'}},return_document=ReturnDocument.AFTER)
        if not r:return
        fence={'id':identity,'status':'organising','lease_token':token}
        try:
            raw=await run_in_threadpool(get_object,r['source']['path'])
            if hashlib.sha256(raw).hexdigest()!=r['source']['sha256']:raise ValueError('Source integrity mismatch.')
            with tempfile.TemporaryDirectory() as directory:
                p=Path(directory)/'book.pdf';p.write_bytes(raw)
                result=await organise_pdfs(p,chapter_book=True)
            if result.get('exam')=='JEE Main':
                result['source_minutes']=result['minutes']
                result['minutes']={'Physics':90,'Mathematics':120,'Chemistry':70}[result['subject']]
                for chapter in result['chapters']: chapter['minutes']=result['minutes']
            parsed_sha=hashlib.sha256(json.dumps(result).encode()).hexdigest()
            for c in result['chapters']:
                if not await books.find_one(fence,{'id':1}):return
                sid=str(uuid.uuid5(uuid.UUID(identity),'chapter:'+str(c['number'])))
                for q in c['questions']:
                    q['id']=str(uuid.uuid5(uuid.UUID(sid),str(q['number'])))
                    for key in ('q_refs','s_refs'):
                        for ref in q[key]:ref['file_id']=r['source']['id']
                exam=result.get('exam','BITSAT')
                worked=result.get('solution_kind')=='supplied_worked'
                rules=valid_rules({'minutes':result.get('minutes',60),'correct':4 if exam=='JEE Main' else 3,'wrong':-1,'skipped':0})
                rules['numeric_rule']='MCQ and integer responses both score +4 correct, −1 wrong and 0 unanswered. Teaching-rubric marks do not affect test scores.' if exam=='JEE Main' else 'Single-correct MCQ: select A, B, C or D. No numeric-entry questions.'
                evidence=independent_evidence(r['source']['sha256'],parsed_sha,c,result['subject'])
                s={'id':sid,'chapter_book_id':identity,'chapter_number':c['number'],'chapter_subject':result['subject'],
                   'title':c['title'],'exam':exam,'test_kind':'chapter','year':'','source':'TEJAS200 chapter-wise original practice. '+('Original worked solutions supplied.' if worked else 'Answer keys supplied; no worked solutions.'),
                   'attribution':'TEJAS200 · Owner-supplied original practice material','questions':c['questions'],'file_ids':[r['source']['id']],
                   'rules':rules,'status':'draft','version':1,'revision':1,'created_at':r['created_at'],'profile_mode':'practice','audience':'all',
                   'rights_upload':True,'rights_publish':True,'rights_report':True,'rights_attested_by':r['created_by'],
                   'competition':False,'live_enabled':False,'solution_kind':'supplied_worked' if worked else 'answer_key_only','verification':c['verification'],
                   'independent_check':evidence,'start_page':c['start_page'],'end_page':c['end_page'],'key_page':c['key_page']}
                await sets.update_one({'id':sid},{'$setOnInsert':s},upsert=True)
            await books.update_one(fence,{'$set':{'status':'ready','subject':result['subject'],'pages':result['pages'],'parsed_sha256':parsed_sha,
                'exam':result.get('exam','BITSAT'),'minutes':result.get('minutes',60),'solution_kind':result.get('solution_kind','answer_key_only'),
                'message':f'{len(result["chapters"])} chapter tests organised. Original PDF images preserve notation. '+('Original worked solutions supplied; no AI generation.' if result.get('solution_kind')=='supplied_worked' else 'Worked solutions are not supplied.')},'$inc':{'revision':1}})
        except Exception as exc:
            message=str(exc)[:450] if isinstance(exc,(ValueError,StorageError)) else 'Processing interrupted. Retry the saved source.'
            await books.update_one(fence,{'$set':{'status':'failed','message':message}})


@router.get('/studio/chapter-books/{id}',response_model=BookView)
async def read_book(id:str,u=Depends(staff)):
    return await book_view(await get(books,id))


@router.post('/studio/chapter-books/{id}/retry',response_model=BookView)
async def retry_book(id:str,bg:BackgroundTasks,u=Depends(owner)):
    r=await get(books,id)
    if r['status'] not in ('failed','queued') and not (r['status']=='organising' and r.get('lease_until',0)<now()):raise HTTPException(409,'Book is processing or already organised.')
    bg.add_task(process_book,id)
    return await book_view(r)


@router.get('/studio/chapter-books/{id}/chapters/{sid}',response_model=ChapterPreview)
async def preview_chapter(id:str,sid:str,u=Depends(staff)):
    s=await sets.find_one({'id':sid,'chapter_book_id':id},{'_id':0})
    if not s:raise HTTPException(404,'Chapter not found.')
    return ChapterPreview(chapter=chapter_view(s),questions=s['questions'])


@router.get('/studio/chapter-books/{id}/chapters/{sid}/questions/{qid}/asset/{kind}/{index}')
async def chapter_asset(id:str,sid:str,qid:str,kind:str,index:int,u=Depends(staff)):
    s=await sets.find_one({'id':sid,'chapter_book_id':id},{'_id':0})
    q=next((q for q in (s or {}).get('questions',[]) if q['id']==qid),None)
    refs=(q or {}).get('q_refs' if kind=='question' else 's_refs',[])
    if kind not in ('question','solution') or not 0<=index<len(refs):raise HTTPException(404,'Source region not found.')
    source=await get(files,refs[index]['file_id'])
    return Response(await run_in_threadpool(render_crop,source,refs[index]),media_type='image/png',headers={'Cache-Control':'private, no-store'})


@router.post('/studio/chapter-books/{id}/publish',response_model=BookView)
async def publish_book(id:str,data:ChapterAction,u=Depends(owner)):
    r=await get(books,id)
    if r['status']!='ready' or data.revision!=r['revision']:raise HTTPException(409,'Reload the organised book before publishing.')
    children=await sets.find({'chapter_book_id':id},{'_id':0}).to_list(60)
    if not children or any(len(s['questions'])!=50 or not s.get('independent_check') or not s['verification'].get('key_checks_agree') for s in children):
        raise HTTPException(409,'Every chapter needs50questions,50source keys and a passing independent per-test recheck before publication.')
    # Claim a durable common start. Repeat publication never extends validity or unpauses a test.
    start=r.get('publication_start')
    if not start:
        claimed=await books.find_one_and_update({'id':id,'revision':data.revision,'publication_start':{'$exists':False}},
            {'$set':{'publication_start':now()}},return_document=ReturnDocument.AFTER)
        r=claimed or await get(books,id);start=r['publication_start']
    for s in children:
        await sets.update_one({'id':s['id'],'start_at':{'$exists':False}},
            {'$set':{'status':'published','start_at':start,'end_at':start+365*86400,'published_at':start,'live_enabled':True,
                     'expires':datetime.fromtimestamp(start+365*86400,timezone.utc).date().isoformat()},'$inc':{'revision':1}})
    await audit(u['id'],'Chapter book published',id,f'{len(children)} independently source-rechecked tests;365-day access; source-specific personal timers and marking')
    return await book_view(await get(books,id))


@router.post('/studio/chapter-books/{id}/chapters/{sid}/live',response_model=BookView)
async def chapter_live(id:str,sid:str,data:ChapterLive,u=Depends(owner)):
    s=await sets.find_one({'id':sid,'chapter_book_id':id},{'_id':0})
    if not s or not s.get('start_at'):raise HTTPException(409,'Publish the verified book first.')
    if data.live and now()>=s['end_at']:raise HTTPException(409,'This test has expired; toggling Live never extends validity.')
    changed=await sets.update_one({'id':sid,'chapter_book_id':id,'revision':data.revision},{'$set':{'live_enabled':data.live},'$inc':{'revision':1}})
    if not changed.modified_count:raise HTTPException(409,'Test changed elsewhere. Reload before retrying.')
    await audit(u['id'],'Chapter test live setting',sid,str(data.live))
    return await book_view(await get(books,id))


async def exam_catalogue(subject,q,page,user=None):
    query=available(user,'BITSAT',q);query['chapter_book_id']={'$exists':True}
    totals_query=available(user,'BITSAT');totals_query['chapter_book_id']={'$exists':True}
    if subject:
        if subject not in ('Physics','Chemistry','Mathematics'):raise HTTPException(422,'Unknown subject.')
        query['chapter_subject']=subject
    total=await sets.count_documents(query);page=max(1,min(page,1000))
    rows=await sets.find(query,PROJECT).sort([('chapter_subject',1),('chapter_number',1),('id',1)]).skip((page-1)*12).limit(12).to_list(12)
    grouped=await sets.aggregate([{'$match':totals_query},{'$group':{'_id':'$chapter_subject','count':{'$sum':1}}}]).to_list(3)
    latest={}
    if user and rows:
        # One newest attempt for EACH visible chapter. A flat 200-row cap could
        # hide another chapter's active attempt behind repeated retries of one set.
        history=await attempts.aggregate([
            {'$match': {'user_id': user['id'], 'set_id': {'$in': [s['id'] for s in rows]}, 'mode': 'practice'}},
            {'$sort': {'set_id': 1, 'started_at': -1, 'id': -1}},
            {'$group': {'_id': '$set_id', 'attempt': {'$first': {'id': '$id', 'set_id': '$set_id', 'status': '$status', 'deadline': '$deadline'}}}},
            {'$replaceRoot': {'newRoot': '$attempt'}},
        ]).to_list(12)
        for a in history:
            if a.get('deadline') and a['deadline']<=now():a['status']='completed'
            latest.setdefault(a['set_id'],a)
    return ExamList(items=[{**summary(s),'attempt':latest.get(s['id'])} for s in rows],total=total,page=page,pages=max(1,(total+11)//12),subject_counts={r['_id']:r['count'] for r in grouped})


@router.get('/chapter-exams',response_model=ExamList)
async def public_exams(subject:str='',q:str='',page:int=1):
    return await exam_catalogue(subject,q,page)


@router.get('/my/chapter-exams',response_model=ExamList)
async def my_exams(subject:str='',q:str='',page:int=1,u=Depends(current)):
    return await exam_catalogue(subject,q,page,u)
