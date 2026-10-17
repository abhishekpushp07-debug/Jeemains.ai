"""Anonymous materialized peer statistics. Frozen scores are never modified."""
import hashlib,json,math,uuid
from fractions import Fraction
from typing import Literal
from fastapi import APIRouter,Depends,HTTPException,BackgroundTasks
from pydantic import BaseModel,Field,ConfigDict
from pymongo.errors import DuplicateKeyError
from .db import db,attempts,sets,now
from .auth import current
from .attempts import owned

router=APIRouter(prefix='/api/attempts',tags=['Peer comparison'])
MIN_SAMPLE=100
NTA_REFERENCE={'year':2026,'exam':'JEE Main Paper 1','unique_appeared':1538468,
 'notice_date':'2026-04-20','page':3,
 'url':'https://cdnbbsr.s3waas.gov.in/s3f8e59f4b2fe7c5705bf878bbd494ccdf/uploads/2026/04/20260420809492136.pdf',
 'scope':'Unique candidates who appeared across both 2026 sessions, not registrations.'}

class CohortResponse(BaseModel):
    state:str
    sample_size:int=0
    minimum_sample:int=MIN_SAMPLE
    rank:int|None=None
    percentile:float|None=None
    rank_formula:str='1 + number of eligible first-attempt profiles with a strictly higher score. Ties share rank.'
    percentile_formula:str='100 × profiles scoring at or below your first-attempt score / eligible profiles. Ties are included.'
    scope:str='First submitted original practice attempt per phone profile, same paper/content/key/rules snapshot. Profiles are not verified unique individuals; this is not an official percentile.'
    provisional:bool=True
    reason:str=''
    compared_attempt_id:str|None=None
    compared_score:float|None=None
    viewing_retry:bool=False
    computed_at:float|None=None
    distribution:list[dict]=Field(default_factory=list)
    questions:list[dict]=Field(default_factory=list)

class RankScenario(BaseModel):
    model_config=ConfigDict(extra='forbid')
    percentile_low:float=Field(ge=0,le=100,allow_inf_nan=False)
    percentile_high:float=Field(ge=0,le=100,allow_inf_nan=False)

class AIRResponse(BaseModel):
    state:str='scenario_only'
    approximate_rank_low:int
    approximate_rank_high:int
    reference:dict
    method:str='For each user-supplied national-percentile endpoint: ceil((100 − percentile) × unique appeared / 100), bounded to 1..N.'
    limitation:str='Illustrative rank range, not an official AIR or calibrated mock-score prediction. Ties, shifts, best-session normalization and current-year participation can change actual rank. Platform percentile is never substituted for NTA percentile.'


def identity(a):
    data={k:a.get(k) for k in ('set_id','version','pack_id','rules')}
    return str(uuid.uuid5(uuid.NAMESPACE_URL,'jeemains-cohort:'+json.dumps(data,sort_keys=True,default=str)))

async def record(a,ledger):
    if a.get('mode')!='practice' or a.get('status')!='completed' or not ledger:return False
    if a.get('competition_end',0)>now():return False
    cohort=identity(a);qidmeta={q['id']:q for q in a.get('questions',[])}
    doc={'id':str(uuid.uuid5(uuid.NAMESPACE_URL,cohort+':'+a['user_id'])), 'cohort_id':cohort,'user_id':a['user_id'],
         'attempt_id':a['id'],'submitted_at':a['submitted_at'],'score':ledger['summary']['score'],
         'score_exact':ledger['summary'].get('score_exact',str(ledger['summary']['score'])),
         'maximum':ledger['summary']['maximum'],'updated_at':now(),
         'items':[{'id':r['id'],'number':qidmeta.get(r['id'],{}).get('number'),
                   'type':qidmeta.get(r['id'],{}).get('type','mcq'), 'outcome':r['outcome'],
                   'response':r.get('normalized_response','') if qidmeta.get(r['id'],{}).get('type')=='mcq' else '',
                   'option_keys':list(qidmeta.get(r['id'],{}).get('options',{}))} for r in ledger['rows']]}
    match={'cohort_id':cohort,'user_id':a['user_id']}
    try:await db.tejas_cohort_entries.update_one(match,{'$setOnInsert':doc},upsert=True)
    except DuplicateKeyError:pass
    await db.tejas_cohort_entries.update_one({**match,'$or':[{'submitted_at':{'$gt':doc['submitted_at']}},
        {'submitted_at':doc['submitted_at'],'attempt_id':{'$gt':a['id']}}]}, {'$set':doc})
    await db.tejas_cohorts.update_one({'id':cohort},{'$set':{'dirty':True,'generation':str(uuid.uuid4()),'set_id':a['set_id'],'version':a['version'],'rules':a['rules'],'pack_id':a.get('pack_id')},'$setOnInsert':{'created_at':now()}},upsert=True)
    await attempts.update_one({'id':a['id']},{'$set':{'cohort_indexed':True}})
    return True

async def refresh(job):
    from .jobs import require_lease
    from .packs import hydrate
    cid=job['payload']['cohort_id'];scope=job['payload']['scope']
    # Bounded, resumable legacy backfill. Never scans all content or other exams.
    match={'set_id':scope['set_id'],'version':scope['version'],'status':'completed','mode':'practice','cohort_indexed':{'$ne':True}}
    legacy=await attempts.find(match,{'_id':0,'command_receipts':0,'response_schema':0}).sort([('submitted_at',1),('id',1)]).limit(200).to_list(200)
    for a in legacy:
        await require_lease(job)
        ledger=await db.tejas_ledgers.find_one({'id':a['id']},{'_id':0})
        if ledger:await record(await hydrate(a),ledger)
    pending=await attempts.count_documents(match)
    state=await db.tejas_cohorts.find_one({'id':cid}) or {}
    pipeline=[{'$match':{'cohort_id':cid}}, {'$facet':{
        'meta':[{'$group':{'_id':None,'n':{'$sum':1},'maximum':{'$max':'$maximum'}}}],
        'scores':[{'$group':{'_id':'$score_exact','count':{'$sum':1}}}],
        'outcomes':[{'$unwind':'$items'},{'$group':{'_id':{'q':'$items.id','outcome':'$items.outcome'},'count':{'$sum':1},'number':{'$first':'$items.number'},'type':{'$first':'$items.type'},'options':{'$first':'$items.option_keys'}}}],
        'choices':[{'$unwind':'$items'},{'$match':{'items.type':'mcq','items.response':{'$ne':''}}},{'$group':{'_id':{'q':'$items.id','choice':'$items.response'},'count':{'$sum':1}}}],
    }}]
    result=(await db.tejas_cohort_entries.aggregate(pipeline,allowDiskUse=True,maxTimeMS=20000).to_list(1))[0]
    n=result['meta'][0]['n'] if result['meta'] else 0;maximum=result['meta'][0]['maximum'] if result['meta'] else 0
    question_map={}
    for item in result['outcomes']:
        key=item['_id']['q'];q=question_map.setdefault(key,{'id':key,'number':item['number'],'type':item['type'],'correct':0,'incorrect':0,'skipped':0,'bonus':0,'dropped':0,'option_counts':{s:0 for s in item.get('options',[])}})
        q[item['_id']['outcome']]=item['count']
    for item in result['choices']:
        q=question_map.get(item['_id']['q'])
        if q and item['_id']['choice'] in q['option_counts']:q['option_counts'][item['_id']['choice']]=item['count']
    for q in question_map.values():
        q['denominator']=n;q['correct_percent']=round(100*q['correct']/n,2) if n else None
        q['incorrect_percent']=round(100*q['incorrect']/n,2) if n else None;q['skipped_percent']=round(100*q['skipped']/n,2) if n else None
    scores=[{'score_exact':x['_id'],'score':float(Fraction(x['_id'])),'count':x['count']} for x in result['scores']]
    scores.sort(key=lambda x:Fraction(x['score_exact']))
    distribution=[]
    if scores:
        lo=min(x['score'] for x in scores);hi=max(maximum,max(x['score'] for x in scores));width=max(1,(hi-lo)/10)
        for i in range(10):
            lower=lo+i*width;upper=lo+(i+1)*width
            count=sum(x['count'] for x in scores if lower<=x['score'] and (x['score']<upper or i==9 and x['score']<=upper))
            distribution.append({'lower':round(lower,2),'upper':round(upper,2),'label':f'{lower:g}–{upper:g}','count':count})
    await require_lease(job)
    await db.tejas_cohort_snapshots.update_one({'id':cid},{'$set':{'sample_size':n,'maximum':maximum,'scores':scores,'distribution':distribution,
        'questions':sorted(question_map.values(),key=lambda x:x['number'] or 0),'computed_at':now(),'backfill_remaining':pending}},upsert=True)
    await db.tejas_cohorts.update_one({'id':cid,'generation':state.get('generation')},{'$set':{'dirty':bool(pending),'last_built_at':now()}})
    return f'Compared {n} eligible first-attempt profiles. Remaining legacy records: {pending}.'

async def _released(id,u):
    a=await owned(id,u)
    if a['status']!='completed':raise HTTPException(409,'Comparison becomes available after submission.')
    if a.get('competition_end',0)>now():raise HTTPException(403,'Results are under embargo until the competition ends.')
    return a

@router.get('/{id}/cohort',response_model=CohortResponse)
async def read(id:str,bg:BackgroundTasks,score_version:str='original',u=Depends(current)):
    a=await _released(id,u)
    if score_version!='original':return CohortResponse(state='unavailable',reason='This comparison uses the original frozen key. Select Original result; corrections are not mixed into its cohort.')
    retry=a.get('mode')=='retry'
    if retry:
        a=await owned(a['parent_attempt'],u)
    if a.get('mode')!='practice':return CohortResponse(state='unavailable',reason='This peer comparison is for original practice attempts; competition standings remain separate.')
    if not a.get('ledger'):return CohortResponse(state='preparing',reason='Your frozen scoring ledger is still being prepared.')
    if not a.get('cohort_indexed'):await record(a,a['ledger'])
    cid=identity(a);state=await db.tejas_cohorts.find_one({'id':cid}) or {}
    snap=await db.tejas_cohort_snapshots.find_one({'id':cid},{'_id':0})
    first=await db.tejas_cohort_entries.find_one({'cohort_id':cid,'user_id':u['id']},{'_id':0,'items':0})
    if not snap or state.get('dirty') or first and first.get('updated_at',0)>snap.get('computed_at',0):
        from .jobs import enqueue,run_job
        job=await enqueue('cohort',u['id'],a['set_id'],{'cohort_id':cid,'scope':{'set_id':a['set_id'],'version':a['version']},'key':cid+'-'+str(int(now()//10))})
        if job['status'] in ('queued','running'):bg.add_task(run_job,job['id'])
        if not snap:return CohortResponse(state='preparing',reason='Preparing comparable first-attempt statistics. Your score is already sealed.')
    n=snap['sample_size'];common={'sample_size':n,'computed_at':snap['computed_at'],'viewing_retry':retry,
        'compared_attempt_id':first.get('attempt_id') if first else None,'compared_score':first.get('score') if first else None}
    paper=await sets.find_one({'id':a['set_id']},{'end_at':1}) or {}
    closed=bool(paper.get('end_at') and paper['end_at']<=now())
    pending=await attempts.count_documents({'set_id':a['set_id'],'version':a['version'],'status':'completed','grading_status':{'$ne':'ready'}}) if closed else 0
    common['provisional']=not closed or pending>0 or bool(snap.get('backfill_remaining')) or bool(state.get('dirty'))
    if n<MIN_SAMPLE:return CohortResponse(state='insufficient_sample',reason=f'Peer percentages and standings appear after {MIN_SAMPLE} comparable first-attempt profiles. Your own question review remains available.',**common)
    if not first or first.get('updated_at',0)>snap['computed_at']:return CohortResponse(state='preparing',reason='Updating your first-attempt comparison.',**common)
    score=Fraction(first['score_exact']);better=sum(x['count'] for x in snap['scores'] if Fraction(x['score_exact'])>score)
    below=sum(x['count'] for x in snap['scores'] if Fraction(x['score_exact'])<=score)
    return CohortResponse(state='available',rank=1+better,percentile=round(100*below/n,2),distribution=snap['distribution'],questions=snap['questions'],**common)

@router.post('/{id}/air-scenario',response_model=AIRResponse)
async def air_scenario(id:str,body:RankScenario,u=Depends(current)):
    a=await _released(id,u)
    if a.get('exam')!='JEE Main' or a.get('test_kind')!='mock':raise HTTPException(409,'National rank scenarios are not meaningful for chapter, non-JEE or unclassified practice tests.')
    if body.percentile_low>body.percentile_high:raise HTTPException(400,'Lower percentile must not exceed upper percentile.')
    total=NTA_REFERENCE['unique_appeared']
    rank=lambda p:max(1,min(total,math.ceil((100-p)*total/100)))
    return AIRResponse(approximate_rank_low=rank(body.percentile_high),approximate_rank_high=rank(body.percentile_low),reference=NTA_REFERENCE)
