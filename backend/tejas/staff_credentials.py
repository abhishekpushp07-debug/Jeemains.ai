"""Staff credential fencing and an explicit operator-only rotation primitive.

Not an HTTP endpoint. Phone-only student sessions are a separate identity plane.
No password, hash, token, email or phone is returned in receipts.
"""
from datetime import datetime, timezone
from typing import Literal
from uuid import UUID
import bcrypt
from fastapi.concurrency import run_in_threadpool
from pydantic import BaseModel, ConfigDict, EmailStr, TypeAdapter
from pymongo import ReturnDocument, WriteConcern
from pymongo.errors import PyMongoError
from .db import users, sessions

MAX_GENERATION = 2**63 - 1


def generation(record):
    value = record.get('credential_generation', 0)
    if type(value) is not int or not 0 <= value < MAX_GENERATION:
        raise ValueError('Invalid staff credential generation')
    return value


def check_session_generation(session, user, token_access_type=None):
    if token_access_type == 'unverified_phone':
        if session.get('access_type') != 'unverified_phone':
            raise ValueError('Identity plane mismatch')
        return
    if session.get('access_type') == 'unverified_phone' or user.get('staff_auth_held') is True:
        raise ValueError('Staff session is unavailable')
    if generation(session) != generation(user):
        raise ValueError('Staff session predates credential rotation')


class RotationReceipt(BaseModel):
    model_config = ConfigDict(extra='forbid', frozen=True)
    operation_id: str
    account_id: str
    prior_generation: int
    new_generation: int
    committed_at_utc: datetime
    logical_session_revocation: Literal['COMMITTED'] = 'COMMITTED'
    physical_cleanup: Literal['COMPLETE','RETRY_REQUIRED']
    deleted_session_count: int | None
    note: str


class RotationConflict(ValueError):
    pass


async def rotate_staff_credential(account_id, expected_generation, replacement_password, operation_id, *, replacement_email=None, owner_selected_password=False):
    if str(UUID(account_id)) != account_id or str(UUID(operation_id)) != operation_id:
        raise ValueError('Use canonical account and operation UUIDs')
    if type(expected_generation) is not int or not 0 <= expected_generation < MAX_GENERATION - 1:
        raise ValueError('Invalid expected generation')
    if type(owner_selected_password) is not bool:
        raise ValueError('Operator exception must be an explicit boolean')
    if owner_selected_password and replacement_email is None:
        raise ValueError('Owner-selected exception requires an explicit owner identity update')
    email = str(TypeAdapter(EmailStr).validate_python(replacement_email)).lower() if replacement_email is not None else None
    minimum = 8 if owner_selected_password else 16
    if not isinstance(replacement_password, str) or not minimum <= len(replacement_password) <= 64 or len(replacement_password.encode('utf-8')) > 64:
        raise ValueError(f'Use a {minimum}–64 character replacement within 64 UTF-8 bytes')
    hashed = await run_in_threadpool(lambda: bcrypt.hashpw(replacement_password.encode('utf-8'), bcrypt.gensalt()).decode())
    epoch_filter = {'credential_generation': expected_generation} if expected_generation else {
        '$or': [{'credential_generation': 0}, {'credential_generation': {'$exists': False}}]}
    result = await users.with_options(write_concern=WriteConcern(w='majority', j=True)).find_one_and_update(
        {'id':account_id, 'role':'owner' if email is not None or owner_selected_password else {'$in':['owner','reviewer']}, **epoch_filter},
        {'$set': {'password_hash': hashed, 'credential_generation': expected_generation + 1,
                  'credential_rotation_operation_id': operation_id,
                  **({'email': email} if email is not None else {}),
                  'owner_selected_password_exception': owner_selected_password},
         '$currentDate': {'credential_rotated_at': True}},
        return_document=ReturnDocument.AFTER, projection={'_id':0,'id':1,'credential_generation':1,'credential_rotated_at':1},
    )
    if result is None:
        raise RotationConflict('Account state changed or is not an eligible staff account; no credential was changed')
    committed_at = result['credential_rotated_at'].replace(tzinfo=timezone.utc)
    # New-generation sessions are retained. A delayed old-generation insertion
    # remains unusable even if it appears after physical cleanup completes.
    stale = {'user_id':account_id, 'access_type':{'$ne':'unverified_phone'}, '$or':[
        {'credential_generation':{'$lt':expected_generation + 1}},
        {'credential_generation':{'$exists':False}},
    ]}
    try:
        deleted = (await sessions.delete_many(stale)).deleted_count
        cleanup = 'COMPLETE'
    except PyMongoError:
        deleted, cleanup = None, 'RETRY_REQUIRED'
    return RotationReceipt(operation_id=operation_id, account_id=account_id,
        prior_generation=expected_generation, new_generation=expected_generation + 1,
        committed_at_utc=committed_at, physical_cleanup=cleanup, deleted_session_count=deleted,
        note='Generation fencing is authoritative; physical deletion is cleanup. Update the protected bootstrap secret separately. No student credential or phone session was changed.')
