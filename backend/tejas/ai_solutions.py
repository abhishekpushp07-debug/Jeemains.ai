"""Versioned AI explanations supplement, never replace, sealed scoring ledgers."""
import hashlib,json,uuid
from fastapi import APIRouter,Depends,HTTPException,BackgroundTasks
from pydantic import BaseModel,Field
from .db import db,files,attempts,get,now
from .auth import current
from .attempts import owned
from .astra import MODEL,PROMPT_VERSION,solve_and_check

router=APIRouter(prefix='/api/attempts',tags=['Worked solutions'])

class SolutionResponse(BaseModel):
    state:str
    id:str|None=None
    question_id:str
    source_kind:str='AI-generated supplement'
    model:str=MODEL
    answer:str|None=None
    steps:list[dict]=Field(default_factory=list)
    summary:str|None=None
    verification:str|None=None
    issues:list[str]=Field(default_factory=list)
    checked_at:float|None=None
    disclosure:str='Two separate Astra passes are checked for agreement and against the supplied key. AI agreement does not guarantee correctness; your sealed score is never changed.'


def fingerprint(q):
    source={k:q.get(k) for k in ('id','type','text','options','answer','q_refs')}
    return str(uuid.uuid5(uuid.NAMESPACE_URL,PROMPT_VERSION+':'+json.dumps(source,sort_keys=True,default=str)))

async def images_for(q):
    from starlette.concurrency import run_in_threadpool
    from .derivatives import render_crop
    output=[]
    for ref in q.get('q_refs',[])[:6]:
        f=await get(files,ref['file_id'])
        output.append(await run_in_threadpool(render_crop,f,ref,1.4))
    if len(q.get('q_refs',[]))>6:raise ValueError('Question spans more source regions than the verified solver budget.')
    return output

async def process(job):
    from .mock_solutions import require_solving_enabled
    require_solving_enabled()
    from .jobs import require_lease
    sid=job['payload']['solution_id']
    doc=await db.tejas_ai_solutions.find_one({'id':sid},{'_id':0})
    if not doc:raise ValueError('Solution request no longer exists.')
    if doc.get('state')=='verified':return 'Verified solution already available.'
    await db.tejas_ai_solutions.update_one({'id':sid},{'$set':{'state':'solving','updated_at':now()}})
    try:
        result=await solve_and_check(doc['question'],await images_for(doc['question']))
        await require_lease(job)
        await db.tejas_ai_solutions.update_one({'id':sid},{'$set':{**result,'state':result['status'],'checked_at':now(),'updated_at':now()}})
        if doc.get('auto_import_id'):
            from .smart_imports import reconcile
            await reconcile(doc['auto_import_id'])
        return 'Separate Astra checks complete. '+('Ready.' if result['status']=='verified' else 'Needs source/key review; no score was changed.')
    except Exception:
        await db.tejas_ai_solutions.update_one({'id':sid,'state':'solving'},{'$set':{'state':'failed','issues':['The solution could not be safely completed. Retry is available; no answer or score was changed.'],'updated_at':now()}})
        raise

async def ensure(q,user_id,set_id,auto_import_id=None):
    from .mock_solutions import require_solving_enabled
    require_solving_enabled()
    from .jobs import enqueue
    sid=fingerprint(q)
    await db.tejas_ai_solutions.update_one({'id':sid},{'$setOnInsert':{'id':sid,'question_id':q['id'],'question':q,'state':'queued','created_at':now(),
        'requested_by':user_id,'set_id':set_id,'auto_import_id':auto_import_id,'model':MODEL,'prompt_version':PROMPT_VERSION}},upsert=True)
    doc=await db.tejas_ai_solutions.find_one({'id':sid},{'_id':0})
    if doc['state'] in ('queued','failed'):
        job=await enqueue('ai_solution',doc['requested_by'],set_id,{'solution_id':sid,'key':sid})
        if job['status']=='failed':
            await db.tejas_jobs.update_one({'id':job['id'],'status':'failed'},{'$set':{'status':'queued','attempts':0,'next_run_at':0,'error':''}})
            job['status']='queued'
        await db.tejas_ai_solutions.update_one({'id':sid},{'$set':{'job_id':job['id'],'state':'queued'}})
        doc.update(job_id=job['id'],state='queued')
    return doc

async def released_question(id,qid,u):
    a=await owned(id,u)
    if a['status']!='completed':raise HTTPException(409,'Worked solutions unlock after submission.')
    if a.get('competition_end',0)>a['_database_now']:raise HTTPException(403,'Worked solutions remain hidden until the competition ends.')
    q=next((q for q in a['questions'] if q['id']==qid),None)
    if not q:raise HTTPException(404,'Question not in this attempt.')
    return a,q


def public(doc,qid):
    if not doc:return SolutionResponse(state='not_requested',question_id=qid)
    ready=doc.get('state')=='verified'
    return SolutionResponse(state=doc.get('state','queued'),id=doc['id'],question_id=qid,
        answer=doc.get('answer') if ready else None,steps=doc.get('steps',[]) if ready else [],
        summary=doc.get('summary') if ready else None,verification=doc.get('verification') if ready else None,
        issues=doc.get('issues',[]),checked_at=doc.get('checked_at'))

@router.get('/{id}/solutions/{qid}',response_model=SolutionResponse)
async def read(id:str,qid:str,u=Depends(current)):
    a,q=await released_question(id,qid,u)
    return public(await db.tejas_ai_solutions.find_one({'id':fingerprint(q)},{'_id':0}),qid)

@router.post('/{id}/solutions/{qid}',response_model=SolutionResponse)
async def request_solution(id:str,qid:str,bg:BackgroundTasks,u=Depends(current)):
    # Students only read saved explanations; this route never starts solving.
    raise HTTPException(410,'AI generation is paused. Only previously saved solutions are available.')
