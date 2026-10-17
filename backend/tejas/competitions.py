"""Competition read models from real immutable attempts; no seeded ranks or percentile claims."""
import hashlib
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from .auth import current
from .db import sets, attempts, now

router=APIRouter(prefix='/api/competitions',tags=['Competitions'])

class Competition(BaseModel):
    id:str
    title:str
    exam:str
    count:int
    minutes:int
    start_at:float
    end_at:float
    status:str
    attempt_id:str|None=None
    attempt_status:str|None=None

class CompetitionList(BaseModel):
    items:list[Competition]
    server_now:float

class Ranking(BaseModel):
    rank:int
    learner:str
    score:float
    accuracy:float|None=None
    is_you:bool=False

class Leaderboard(BaseModel):
    competition:Competition
    status:str
    participants:int=0
    graded:int=0
    pending:int=0
    rows:list[Ranking]=[]
    you:Ranking|None=None
    server_now:float
    policy:str='First competition attempt per phone profile. Equal scores share rank (1, 1, 3). Practice retries and previews excluded. Phone ownership is not verified; this is a practice cohort, not an official percentile.'


def item(s,a=None):
    a=a or {}; t=now()
    return Competition(id=s['id'],title=s['title'],exam=s['exam'],count=len(s.get('questions',[])),minutes=s['rules']['minutes'],
        start_at=s['start_at'],end_at=s['end_at'],status='ended' if t>=s['end_at'] else 'unlive' if not s['live_enabled'] else 'scheduled' if t<s['start_at'] else 'live',
        attempt_id=a.get('id'),attempt_status=a.get('status'))


@router.get('',response_model=CompetitionList)
async def catalogue(u=Depends(current)):
    docs=await sets.find({'competition':True,'qa_only':{'$ne':True}},{'_id':0,'id':1,'title':1,'exam':1,'questions.id':1,'rules.minutes':1,'start_at':1,'end_at':1,'live_enabled':1}).sort('start_at',-1).limit(50).to_list(50)
    own=await attempts.find({'user_id':u['id'],'set_id':{'$in':[s['id'] for s in docs]},'mode':'practice','competition_end':{'$exists':True}},{'_id':0,'id':1,'set_id':1,'status':1}).to_list(50)
    own={a['set_id']:a for a in own}
    return CompetitionList(items=[item(s,own.get(s['id'])) for s in docs],server_now=now())


@router.get('/{id}',response_model=Leaderboard)
async def leaderboard(id:str,u=Depends(current)):
    s=await sets.find_one({'id':id,'competition':True,'qa_only':{'$ne':True}},{'_id':0,'id':1,'title':1,'exam':1,'questions.id':1,'rules.minutes':1,'start_at':1,'end_at':1,'live_enabled':1})
    if not s: raise HTTPException(404,'Competition not found.')
    own=await attempts.find_one({'set_id':id,'user_id':u['id'],'mode':'practice','competition_end':{'$exists':True}},{'_id':0,'id':1,'status':1})
    base={'set_id':id,'mode':'practice','competition_ranked':True}
    participants=await attempts.count_documents(base)
    count=await attempts.count_documents({**base,'status':'completed','grading_status':'ready','summary.score':{'$exists':True}})
    common=dict(competition=item(s,own),participants=participants,graded=count,pending=participants-count,server_now=now())
    if now()<s['end_at']: return Leaderboard(status='embargoed',**common)
    # Rank only frozen original ledgers. $rank deliberately does not use elapsed time.
    rows=await attempts.aggregate([
        {'$match':{**base,'status':'completed','grading_status':'ready','summary.score':{'$exists':True}}},
        {'$setWindowFields':{'sortBy':{'summary.score':-1},'output':{'rank':{'$rank':{}}}}},
        {'$facet':{'top':[{'$sort':{'rank':1,'id':1}},{'$limit':50},{'$project':{'_id':0,'id':1,'user_id':1,'summary.score':1,'summary.accuracy':1,'rank':1}}],
                   'you':[{'$match':{'user_id':u['id']}},{'$limit':1},{'$project':{'_id':0,'id':1,'user_id':1,'summary.score':1,'summary.accuracy':1,'rank':1}}]}}
    ]).to_list(1)
    data=rows[0] if rows else {'top':[],'you':[]}
    def rank(r): return Ranking(rank=r['rank'],learner='Learner '+hashlib.sha256((id+r['user_id']).encode()).hexdigest()[:8].upper(),score=r['summary']['score'],accuracy=r['summary'].get('accuracy'),is_you=r['user_id']==u['id'])
    return Leaderboard(status='provisional' if count<participants else 'ready',rows=[rank(r) for r in data['top']],you=rank(data['you'][0]) if data['you'] else None,**common)
