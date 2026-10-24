from fastapi import HTTPException
from pymongo import ReturnDocument
from pymongo.errors import DuplicateKeyError


async def increment(collection, key, expires_at):
    try:
        result = await collection.find_one_and_update(
            {'_id': key}, {'$inc': {'count': 1}, '$setOnInsert': {'expires_at': expires_at}},
            upsert=True, return_document=ReturnDocument.AFTER,
        )
    except DuplicateKeyError:
        result = await collection.find_one_and_update(
            {'_id': key}, {'$inc': {'count': 1}}, return_document=ReturnDocument.AFTER,
        )
    if not result:
        raise HTTPException(503, 'Sign-in protection is temporarily unavailable. Retry shortly.', headers={'Retry-After': '3'})
    return result['count']
