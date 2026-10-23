"""Private post-release study records; never mutate answers or academic ledgers."""
from fractions import Fraction
from typing import Literal
import uuid
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, ConfigDict, Field
from pymongo import ReturnDocument
from pymongo.errors import DuplicateKeyError
from .auth import current
from .db import db, now
from .idempotency import fingerprint

router=APIRouter(prefix='/api/attempts', tags=['Private study review'])
reviews=db.tejas_reviews
CATEGORIES={'concept_gap':'Concept gap','calculation':'Calculation error','silly_mistake':'Silly mistake','time_pressure':'Time pressure','misread':'Misread question','guess':'Guess','other':'Other'}
Category=Literal['concept_gap','calculation','silly_mistake','time_pressure','misread','guess','other']

class ReviewWrite(BaseModel):
    model_config=ConfigDict(extra='forbid',strict=True)
    request_id:str=Field(min_length=8,max_length=100)
    revision:int=Field(ge=1,le=65)
    score_version:str=Field(default='original',min_length=1,max_length=100)
    category:Category|None=None
    note:str=Field(default='',max_length=500)
    identified_error:bool=False
    wrote_note:bool=False
    reviewed_solution:bool=False
    retry_planned:bool=False

class ReviewState(BaseModel):
    question_id:str
    score_version:str='original'
    revision:int
    category:Category|None=None
    note:str=''
    identified_error:bool=False
    wrote_note:bool=False
    reviewed_solution:bool=False
    retry_planned:bool=False
    completed:bool=False
    updated_at:float

class ProbabilityInput(BaseModel):
    model_config=ConfigDict(extra='forbid',strict=True)
    probability:float=Field(ge=0,le=1,allow_inf_nan=False)

class ExpectedValue(BaseModel):
    probability:float
    correct_marks:float
    wrong_marks:float
    skipped_marks:float
    expected_marks:float
    expected_exact:str
    break_even_probability:float
    hypothetical:bool=True
    note:str='Uses your probability assumption and this attempt’s frozen ordinary marking rule. Not a prediction, admission estimate, or instruction to attempt a question.'

async def released(id,u,score_version='original'):
    from .attempts import owned
    from .corrections import with_grade
    a=await owned(id,u)
    if a['status']!='completed' or a.get('competition_end',0)>now():
        raise HTTPException(403,'Study review unlocks after submission and the competition window closes.')
    if not a.get('ledger'):
        raise HTTPException(409,'Wait for grading before reviewing this attempt.')
    return await with_grade(a,score_version)

async def states_for(a):
    data=await reviews.find({'attempt_id':a['id'],'user_id':a['user_id'],'score_version':a.get('score_version','original')},{'_id':0,'receipts':0}).limit(300).to_list(300)
    return {r['question_id']:ReviewState(**r).model_dump() for r in data}

def review_summary(a,rows):
    assigned=[q['id'] for q in rows if q['outcome'] in ('incorrect','skipped') or q.get('marked')]
    states=a.get('review_states',{})
    return {'states':states,'assigned':assigned,'completed':sum(bool(states.get(qid,{}).get('completed')) for qid in assigned),'categories':CATEGORIES,
            'policy':'Four explicit reflection steps per assigned question. Completion records your review actions, not mastery. Notes and categories are private to your profile.'}

@router.put('/{id}/reviews/{qid}',response_model=ReviewState)
async def save_review(id:str,qid:str,data:ReviewWrite,u=Depends(current)):
    a=await released(id,u,data.score_version)
    if not any(q['id']==qid for q in a['questions']):raise HTTPException(404,'Question not found.')
    if data.identified_error and data.category is None:raise HTTPException(422,'Choose your own category before confirming this step.')
    if data.wrote_note and not data.note.strip():raise HTTPException(422,'Write a note before confirming this step.')
    if data.reviewed_solution and qid not in set(a.get('review_solution_opened',[])+a.get('solution_opened',[])):
        raise HTTPException(409,'Open this question’s released solution before confirming your review.')
    rid=str(uuid.uuid5(uuid.NAMESPACE_URL,f'review:{u["id"]}:{id}:{qid}:{data.score_version}'))
    command=fingerprint(data.request_id);body=fingerprint(data.model_dump())
    old=await reviews.find_one({'id':rid},{'_id':0})
    def replay(record):
        receipt=(record or {}).get('receipts',{}).get(command)
        if receipt:
            if receipt['body']!=body:raise HTTPException(409,'This review save identifier was already used for different content.')
            return ReviewState(**receipt['accepted'])
        return None
    duplicate=replay(old)
    if duplicate:return duplicate
    if data.revision!=(old or {}).get('revision',0)+1:raise HTTPException(409,'This reflection changed in another tab. Reload the saved version before editing.')
    if len((old or {}).get('receipts',{}))>=64:raise HTTPException(409,'This question reached its review history limit. Your last saved reflection remains safe.')
    state=ReviewState(question_id=qid,**data.model_dump(exclude={'request_id'}),
        completed=all([data.identified_error,data.wrote_note,data.reviewed_solution,data.retry_planned]),updated_at=now()).model_dump()
    receipt={'body':body,'accepted':state}
    if old is None:
        try:
            await reviews.insert_one({'id':rid,'attempt_id':id,'user_id':u['id'],**state,'receipts':{command:receipt}})
            return ReviewState(**state)
        except DuplicateKeyError:pass
    else:
        changed=await reviews.find_one_and_update({'id':rid,'revision':data.revision-1,f'receipts.{command}':{'$exists':False}},
            {'$set':{**state,f'receipts.{command}':receipt}},return_document=ReturnDocument.AFTER)
        if changed:return ReviewState(**state)
    duplicate=replay(await reviews.find_one({'id':rid},{'_id':0}))
    if duplicate:return duplicate
    raise HTTPException(409,'Another review save won. Reload before retrying; no notes were overwritten.')

@router.post('/{id}/expected-value',response_model=ExpectedValue)
async def expected_value(id:str,data:ProbabilityInput,u=Depends(current)):
    a=await released(id,u)
    p=Fraction(str(data.probability));c=Fraction(str(a['rules']['correct']));w=Fraction(str(a['rules']['wrong']));s=Fraction(str(a['rules'].get('skipped',0)))
    if c<=w:raise HTTPException(409,'This rule adapter does not support the single-correct calculator.')
    ev=p*c+(1-p)*w
    return ExpectedValue(probability=data.probability,correct_marks=float(c),wrong_marks=float(w),skipped_marks=float(s),expected_marks=float(ev),expected_exact=str(ev),break_even_probability=float((s-w)/(c-w)))
