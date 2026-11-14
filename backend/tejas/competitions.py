"""Competition read models from real immutable attempts; no seeded ranks or percentile claims."""
import hashlib, time
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from .auth import current
from .db import sets, attempts, now
from .canonical import clocked_one, database_now
from .live_window import can_start

router=APIRouter(prefix='/api/competitions',tags=['Competitions'])

class Competition(BaseModel):
    id:str
    title:str
    exam:str
    count:int
    minutes:int
    start_at:float
    end_at:float
    last_start_at:float|None=None
    can_start:bool=True
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


def item(s,a=None,t=None):
    a=a or {}; t=now() if t is None else t
    return Competition(id=s['id'],title=s['title'],exam=s['exam'],count=len(s.get('questions',[])),minutes=s['rules']['minutes'],
        start_at=s['start_at'],end_at=s['end_at'],last_start_at=s.get('last_start_at'),can_start=can_start(s,t),status='ended' if t>=s['end_at'] else 'unlive' if not s['live_enabled'] else 'scheduled' if t<s['start_at'] else 'live',
        attempt_id=a.get('id'),attempt_status=a.get('status'))


@router.get('',response_model=CompetitionList)
async def catalogue(u=Depends(current)):
    docs=await sets.find({'competition':True,'qa_only':{'$ne':True}},{'_id':0,'id':1,'title':1,'exam':1,'questions.id':1,'rules.minutes':1,'start_at':1,'end_at':1,'last_start_at':1,'live_enabled':1}).sort('start_at',-1).limit(50).to_list(50)
    own=await attempts.find({'user_id':u['id'],'set_id':{'$in':[s['id'] for s in docs]},'mode':'practice','competition_end':{'$exists':True}},{'_id':0,'id':1,'set_id':1,'status':1}).to_list(50)
    own={a['set_id']:a for a in own}
    t = await database_now()
    return CompetitionList(items=[item(s,own.get(s['id']),t) for s in docs],server_now=t)


BOARD_SECONDS = 10
_boards = {}


async def standings(id):
    """Shared counts + top 50 from the competition_rank index; reused per process for BOARD_SECONDS."""
    hit = _boards.get(id)
    if hit and hit[0] > time.monotonic():
        return hit[1]
    base = {'set_id': id, 'mode': 'practice', 'competition_ranked': True}
    ranked = {**base, 'status': 'completed', 'grading_status': 'ready', 'summary.score': {'$exists': True}}
    top = await attempts.find(ranked, {'_id': 0, 'id': 1, 'user_id': 1, 'summary.score': 1, 'summary.accuracy': 1}).sort([('summary.score', -1), ('id', 1)]).limit(50).to_list(50)
    for i, r in enumerate(top):
        r['rank'] = top[i - 1]['rank'] if i and r['summary']['score'] == top[i - 1]['summary']['score'] else i + 1
    data = (await attempts.count_documents(base), await attempts.count_documents(ranked), top, ranked)
    _boards[id] = (time.monotonic() + BOARD_SECONDS, data)
    if len(_boards) > 64:
        _boards.pop(next(iter(_boards)))
    return data


@router.get('/{id}',response_model=Leaderboard)
async def leaderboard(id:str,u=Depends(current)):
    s=await clocked_one(sets, {'id':id,'competition':True,'qa_only':{'$ne':True}},{'_id':0,'id':1,'title':1,'exam':1,'questions.id':1,'rules.minutes':1,'start_at':1,'end_at':1,'last_start_at':1,'live_enabled':1})
    if not s: raise HTTPException(404,'Competition not found.')
    own=await attempts.find_one({'set_id':id,'user_id':u['id'],'mode':'practice','competition_end':{'$exists':True}},{'_id':0,'id':1,'status':1})
    participants,count,top,ranked=await standings(id)
    t = s['_database_now']
    common=dict(competition=item(s,own,t),participants=participants,graded=count,pending=participants-count,server_now=t)
    if t<s['end_at']: return Leaderboard(status='embargoed',**common)
    # Equal scores share rank (1, 1, 3): 1 + number of ranked attempts with a strictly higher frozen score.
    mine=await attempts.find_one({**ranked,'user_id':u['id']},{'_id':0,'id':1,'user_id':1,'summary.score':1,'summary.accuracy':1})
    if mine: mine['rank']=1+await attempts.count_documents({**ranked,'summary.score':{'$gt':mine['summary']['score']}})
    def rank(r): return Ranking(rank=r['rank'],learner='Learner '+hashlib.sha256((id+r['user_id']).encode()).hexdigest()[:8].upper(),score=r['summary']['score'],accuracy=r['summary'].get('accuracy'),is_you=r['user_id']==u['id'])
    return Leaderboard(status='provisional' if count<participants else 'ready',rows=[rank(r) for r in top],you=rank(mine) if mine else None,**common)
