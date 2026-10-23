"""Canonical request identities; never log the underlying body."""
import hashlib
import json
from fastapi import HTTPException


def fingerprint(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(',', ':'), allow_nan=False).encode()).hexdigest()


def verify_start(existing, set_id, data):
    if existing.get('mode') == 'retry':
        raise HTTPException(409, 'This identifier belongs to a revision attempt, not a new start.')
    expected = fingerprint({'operation': 'start', 'set_id': set_id, **data.model_dump(exclude={'start_key'})})
    stored = existing.get('start_receipts', {}).get(fingerprint(data.start_key)) or existing.get('start_fingerprint')
    if stored:
        mismatch = stored != expected
    else:
        mismatch = existing['set_id'] != set_id or (existing.get('mode') == 'preview') != data.preview
    if mismatch:
        raise HTTPException(409, 'This start identifier was already used for a different request.')
    return expected



async def bind_start_alias(existing, set_id, data):
    """Resuming still applies a start command: bind its retry key durably."""
    from .db import attempts
    from pymongo.errors import DuplicateKeyError
    key = fingerprint(data.start_key)
    body = fingerprint({'operation': 'start', 'set_id': set_id, **data.model_dump(exclude={'start_key'})})
    try:
        updated = await attempts.update_one(
            {'id': existing['id'], f'start_receipts.{key}': {'$exists': False},
             '$expr': {'$lt': [{'$size': {'$ifNull': ['$start_request_keys', []]}}, 1024]}},
            {'$set': {f'start_receipts.{key}': body}, '$addToSet': {'start_request_keys': data.start_key}},
        )
    except DuplicateKeyError:
        raise HTTPException(409, 'This start identifier belongs to another attempt.')
    if not updated.modified_count:
        latest = await attempts.find_one({'id': existing['id']}, {f'start_receipts.{key}': 1})
        if (latest or {}).get('start_receipts', {}).get(key) != body:
            raise HTTPException(409, 'This start identifier conflicts or the resume history limit was reached.')


async def bind_retry_alias(existing, start_key, body):
    """Bind every accepted resume key, including a racing resume, before returning success."""
    from .db import attempts
    from pymongo.errors import DuplicateKeyError
    key = fingerprint(start_key)
    try:
        updated = await attempts.update_one(
            {'id': existing['id'], 'retry_fingerprint': body,
             f'retry_receipts.{key}': {'$exists': False},
             '$expr': {'$lt': [{'$size': {'$ifNull': ['$start_request_keys', []]}}, 1024]}},
            {'$set': {f'retry_receipts.{key}': body}, '$addToSet': {'start_request_keys': start_key}},
        )
    except DuplicateKeyError:
        raise HTTPException(409, 'This retry identifier belongs to another attempt.')
    if not updated.modified_count:
        latest = await attempts.find_one({'id': existing['id']}, {f'retry_receipts.{key}': 1})
        if (latest or {}).get('retry_receipts', {}).get(key) != body:
            raise HTTPException(409, 'This retry identifier conflicts or the resume history limit was reached.')
