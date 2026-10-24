"""Atomic practice save + durable body-bound receipt + attempt sequence.
This implements the custom autosave policy, NOT the V5 explicit-commit/lease protocol.
"""
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, ConfigDict, Field
from pymongo import ReturnDocument
from .auth import current
from .db import attempts, get, now
from .idempotency import fingerprint
from .runtime import MAX_ANSWER_COMMANDS
from .canonical import EPOCH_NOW, clocked_one
from tejas_core import normalize_answer

router = APIRouter(prefix='/api/attempts', tags=['Acknowledged answers'])


class AnswerWrite(BaseModel):
    model_config = ConfigDict(extra='forbid', strict=True)
    value: str = Field(default='', max_length=30)
    marked: bool = False
    confidence: float | None = Field(default=None, ge=0, le=1, allow_inf_nan=False)
    revision: int = Field(ge=1, le=MAX_ANSWER_COMMANDS + 1)
    request_id: str = Field(min_length=8, max_length=100)


class AcceptedAnswer(AnswerWrite):
    normalized_value: str
    accepted_at: float
    server_seq: int | None = None


class AnswerReceipt(BaseModel):
    accepted: AcceptedAnswer
    server_now: float
    current_revision: int
    duplicate: bool = False
    command_state: str = 'applied'


def receipt_result(receipt, body_hash, current_revision, server_now=None):
    if receipt['payload_hash'] != body_hash:
        raise HTTPException(409, 'This save identifier was already used for different content or revision.')
    return {'accepted': receipt['accepted'], 'server_now': now() if server_now is None else server_now, 'duplicate': True, 'current_revision': current_revision}


@router.put('/{id}/answers/{qid}', response_model=AnswerReceipt)
async def save_answer(id: str, qid: str, data: AnswerWrite, u=Depends(current)):
    try:
        UUID(qid)
    except ValueError:
        raise HTTPException(404, 'Question not found.')
    key = fingerprint({'qid': qid, 'request_id': data.request_id})
    body = data.model_dump(exclude_none=True)
    body_hash = fingerprint(body)
    projection = {'_id': 0, 'id': 1, 'user_id': 1, 'status': 1, 'deadline': 1, 'pack_id': 1,
                  f'answers.{qid}': 1, f'response_schema.{qid}': 1,
                  f'command_receipts.{key}': 1, 'command_count': 1, 'rules.bonus_rule': 1, 'bonus_unlocked_at': 1}
    a = await clocked_one(attempts, {'id': id, 'user_id': u['id']}, projection)
    if not a:
        raise HTTPException(404, 'Attempt not found.')
    old = a.get('answers', {}).get(qid, {})
    existing = a.get('command_receipts', {}).get(key)
    if existing:
        return receipt_result(existing, body_hash, old.get('revision', 0), a['_database_now'])
    # Compatibility: historical attempts may have only their latest acknowledged response.
    if old.get('request_id') == data.request_id:
        if any(old.get(k) != v for k, v in body.items()):
            raise HTTPException(409, 'This save identifier was already used for different content or revision.')
        return {'accepted': old, 'server_now': a['_database_now'], 'duplicate': True, 'current_revision': old['revision']}
    if a['status'] != 'active' or (a['deadline'] and a['_database_now'] >= a['deadline']):
        if a['status'] == 'active':
            from .attempts import finalize
            await finalize(id, 'time_limit')
        raise HTTPException(409, 'The attempt has ended. Late drafts are not accepted or scored.')
    q = a.get('response_schema', {}).get(qid)
    if not q:
        if a.get('pack_id'):
            from .packs import question
            q = await question(a['pack_id'], qid)
        else:
            full = await get(attempts, id)
            q = next((x for x in full['questions'] if x['id'] == qid), None)
    if not q:
        raise HTTPException(404, 'Question does not belong to this attempt.')
    bonus_gate = {}
    if (a.get('rules') or {}).get('bonus_rule'):
        unlocked = bool(a.get('bonus_unlocked_at'))
        if q.get('bonus') and not unlocked:
            raise HTTPException(409, 'Bonus questions open only after all 130 main questions are answered and you confirm entry.')
        if not q.get('bonus') and unlocked:
            raise HTTPException(409, 'Main answers are locked because you entered the bonus section.')
        bonus_gate = {'bonus_unlocked_at': {'$exists': bool(q.get('bonus'))}}
    try:
        value = normalize_answer(data.value, q['type'])
    except ValueError as exc:
        raise HTTPException(400, str(exc))
    if value and q['type'] == 'mcq' and value not in q['options']:
        raise HTTPException(400, 'Choose an available option.')
    if data.revision != old.get('revision', 0) + 1:
        raise HTTPException(409, 'Another tab or device changed this answer. Reload the saved response before editing.')
    if a.get('command_count', 0) >= MAX_ANSWER_COMMANDS:
        raise HTTPException(409, 'This practice attempt reached its save-history limit. Existing saved answers are safe; submit or contact support.')
    epoch = EPOCH_NOW
    guard = {'id': id, 'user_id': u['id'], 'status': 'active', **bonus_gate,
             f'command_receipts.{key}': {'$exists': False},
             '$expr': {'$and': [
                 {'$or': [{'$eq': ['$deadline', 0]}, {'$gt': ['$deadline', epoch]}]},
                 {'$lt': [{'$ifNull': ['$command_count', 0]}, MAX_ANSWER_COMMANDS]}]},
             '$or': [{f'answers.{qid}.revision': data.revision - 1}] + ([{f'answers.{qid}': {'$exists': False}}] if data.revision == 1 else [])}
    updated = await attempts.find_one_and_update(guard, [
        {'$set': {f'answers.{qid}': {'$literal': {**body, 'normalized_value': value}},
                  'server_seq': {'$add': [{'$ifNull': ['$server_seq', 0]}, 1]},
                  'command_count': {'$add': [{'$ifNull': ['$command_count', 0]}, 1]}}},
        {'$set': {f'answers.{qid}.accepted_at': epoch, f'answers.{qid}.server_seq': '$server_seq',
                  'visited': {'$setUnion': [{'$ifNull': ['$visited', []]}, [qid]]}}},
        {'$set': {f'first_answers.{qid}': {'$cond': [
            {'$ne': [f'$answers.{qid}.normalized_value', '']},
            {'$ifNull': [f'$first_answers.{qid}', f'$answers.{qid}']},
            {'$ifNull': [f'$first_answers.{qid}', '$$REMOVE']}]} }},
        {'$set': {'confidence_changed_questions': {'$cond': [
            {'$and': [{'$ne': [{'$ifNull': [f'$first_answers.{qid}.confidence', None]}, None]},
                      {'$ne': [f'$first_answers.{qid}.normalized_value', f'$answers.{qid}.normalized_value']}]},
            {'$setUnion': [{'$ifNull': ['$confidence_changed_questions', []]}, [qid]]},
            {'$ifNull': ['$confidence_changed_questions', []]}]}}},
        {'$set': {f'command_receipts.{key}': {'payload_hash': {'$literal': body_hash}, 'accepted': f'$answers.{qid}'}}},
    ], projection={'_id': 0, f'answers.{qid}': 1}, return_document=ReturnDocument.AFTER)
    if not updated:
        # Concurrent identical delivery may have won the CAS; recover its original receipt.
        latest = await clocked_one(attempts, {'id': id, 'user_id': u['id']}, {'_id': 0, f'command_receipts.{key}': 1, f'answers.{qid}.revision': 1})
        existing = (latest or {}).get('command_receipts', {}).get(key)
        if existing:
            return receipt_result(existing, body_hash, latest.get('answers', {}).get(qid, {}).get('revision', 0), latest['_database_now'])
        raise HTTPException(409, 'Save conflict or deadline reached. Reconnect to check the accepted response.')
    return {'accepted': updated['answers'][qid], 'server_now': updated['answers'][qid]['accepted_at'], 'current_revision': data.revision}
