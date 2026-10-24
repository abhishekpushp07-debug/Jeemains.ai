from typing import Any
from pydantic import ConfigDict, Field
from .documents import BaseDocument
from .idempotency import fingerprint

EPOCH_NOW = {'$divide': [{'$toLong': '$$NOW'}, 1000]}


class CanonicalIntegrityError(ValueError):
    pass


async def clocked_one(collection, query, projection):
    if any(value != 0 for key, value in projection.items() if key != '_id'):
        return await collection.find_one(query, {**projection, '_database_now': EPOCH_NOW})
    rows = await collection.aggregate([
        {'$match': query}, {'$limit': 1}, {'$project': projection},
        {'$set': {'_database_now': EPOCH_NOW}},
    ]).to_list(1)
    return rows[0] if rows else None


def source_commitment(attempt):
    return fingerprint({
        'schema': 1, 'attempt_id': attempt['id'], 'user_id': attempt['user_id'],
        'pack_id': attempt.get('pack_id') or fingerprint(attempt['questions']),
        'sealed_seq': attempt.get('sealed_seq', 0), 'answers': attempt.get('answers', {}),
        'rules': attempt['rules'], 'profile': attempt.get('profile', {}),
        'version': attempt.get('version'), 'key_version': attempt.get('key_version'),
    })


def verify_ledger(attempt):
    ledger = attempt.get('ledger') or {}
    expected = ledger.get('source_commitment')
    if expected and expected != source_commitment(attempt):
        raise CanonicalIntegrityError('Frozen ledger does not match its sealed source commitment')


class FrozenLedger(BaseDocument):
    model_config = ConfigDict(populate_by_name=True)
    record_id: str = Field(alias='id')
    attempt_id: str
    user_id: str
    summary: dict[str, Any]
    rows: list[dict[str, Any]]
    engine_version: int
    created_at: float
    source_commitment: str
    source_pack_id: str | None = None
    sealed_seq: int
