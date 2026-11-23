from datetime import datetime, timedelta, timezone
from fastapi import HTTPException
from pymongo import ReturnDocument
from pymongo.errors import DuplicateKeyError, PyMongoError

BUSY = 'Sign-in protection is temporarily unavailable. Retry shortly.'


async def wrong_gate(collection, keys, t, text):
    """429 while any of these keys is in its wait; text(minutes) is the message. Correct tries are never counted."""
    try:
        blocked = await collection.find({'_id': {'$in': [k for k, _ in keys]}, 'blocked_until': {'$gt': t}}, {'blocked_until': 1}).to_list(len(keys))
    except PyMongoError:
        raise HTTPException(503, BUSY, headers={'Retry-After': '3'})
    if blocked:
        wait = max(1, int((max(d['blocked_until'] for d in blocked) - t).total_seconds()) + 1)
        raise HTTPException(429, text(max(1, round(wait / 60))), headers={'Retry-After': str(wait)})


async def count_wrong(collection, keys, t, wait):
    """One wrong try. A key that reaches its limit within `wait` seconds of its first wrong try waits `wait` seconds.
    Returns how many tries the first key has left."""
    fresh = {'$lt': [{'$ifNull': ['$started', datetime.fromtimestamp(0, timezone.utc)]}, t - timedelta(seconds=wait)]}
    left = None
    try:
        for key, limit in keys:
            doc = await collection.find_one_and_update({'_id': key}, [{'$set': {
                'count': {'$cond': [fresh, 1, {'$add': ['$count', 1]}]}, 'started': {'$cond': [fresh, t, '$started']},
                'expires_at': t + timedelta(seconds=2 * wait)}}], upsert=True, return_document=ReturnDocument.AFTER)
            if doc['count'] >= limit:
                await collection.update_one({'_id': key}, {'$set': {'blocked_until': t + timedelta(seconds=wait), 'count': 0}, '$unset': {'started': ''}})
            if left is None:
                left = max(0, limit - doc['count'])
    except PyMongoError:
        raise HTTPException(503, BUSY, headers={'Retry-After': '3'})
    return left


async def increment(collection, key, expires_at):
    try:
        try:
            result = await collection.find_one_and_update(
                {'_id': key}, {'$inc': {'count': 1}, '$setOnInsert': {'expires_at': expires_at}},
                upsert=True, return_document=ReturnDocument.AFTER,
            )
        except DuplicateKeyError:
            result = await collection.find_one_and_update(
                {'_id': key}, {'$inc': {'count': 1}}, return_document=ReturnDocument.AFTER,
            )
    except PyMongoError:
        raise HTTPException(503, 'Sign-in protection is temporarily unavailable. Retry shortly.', headers={'Retry-After': '3'})
    if not result:
        raise HTTPException(503, 'Sign-in protection is temporarily unavailable. Retry shortly.', headers={'Retry-After': '3'})
    return result['count']
