import math
import re
from fastapi import APIRouter, Depends, HTTPException, Query, Response
from pydantic import BaseModel, Field
from .auth import forget_student, owner
from .db import audit, db, now
from .documents import BaseDocument

router = APIRouter(prefix='/api/admin', tags=['Owner student directory'])
MISSING = 'Yeh student nahi mila. List refresh karke dobara dekhiye.'


class StudentRecord(BaseDocument):
    profile_id: str = Field(alias='id')
    phone: str
    pin_version: int = Field(default=0, ge=0)
    display_name: str = ''
    blocked_at: float | None = None


class StudentView(BaseModel):
    id: str
    phone: str
    pin_version: int
    display_name: str = ''
    blocked: bool = False
    blocked_at: float | None = None


class StudentList(BaseModel):
    items: list[StudentView]
    total: int
    page: int
    pages: int


@router.get('/students', response_model=StudentList)
async def list_students(response: Response, page: int = Query(1, ge=1, le=10000),
                        q: str = Query('', max_length=32, pattern=r'^[+0-9\s()-]*$'), u=Depends(owner)):
    response.headers['Cache-Control'] = 'private, no-store'
    digits = re.sub(r'[^+0-9]', '', q)
    query = {'phone': {'$regex': re.escape(digits)}} if digits else {}
    total = await db.tejas_phone_profiles.count_documents(query)
    records = await db.tejas_phone_profiles.find(query, {'id': 1, 'phone': 1, 'pin_version': 1, 'display_name': 1, 'blocked_at': 1}).sort([('phone', 1), ('id', 1)]).skip((page - 1) * 50).limit(50).to_list(50)
    items = []
    for raw in records:
        record = StudentRecord.from_mongo(raw)
        items.append(StudentView(id=record.profile_id, phone=record.phone, pin_version=record.pin_version, display_name=record.display_name,
                                 blocked=bool(record.blocked_at), blocked_at=record.blocked_at))
    await audit(u['id'], 'student_directory_read', 'student_directory')
    return StudentList(items=items, total=total, page=page, pages=max(1, math.ceil(total / 50)))


@router.post('/students/{id}/block')
async def block_student(id: str, response: Response, u=Depends(owner)):
    """Blocked: signed out on every device, no sign-in and no PIN reset until unblocked. Attempts, scores and ranks stay."""
    response.headers['Cache-Control'] = 'private, no-store'
    done = await db.tejas_phone_profiles.update_one({'id': id, 'blocked_at': None}, {'$set': {'blocked_at': now(), 'blocked_by': u['id']}})
    if not done.matched_count and not await db.tejas_phone_profiles.find_one({'id': id}, {'_id': 1}):
        raise HTTPException(404, MISSING)
    # Sign-in records are kept but switched off, so no device of this student stays signed in, now or after an unblock.
    await db.tejas_sessions.update_many({'user_id': id, 'access_type': 'unverified_phone', 'revoked_at': None}, {'$set': {'revoked_at': now()}})
    forget_student(user_id=id)
    if done.matched_count:
        await audit(u['id'], 'owner_student_blocked', id)
    return {'ok': True, 'blocked': True, 'message': 'Account band ho gaya. Yeh number har device se sign out ho gaya hai. Purane attempt aur rank waise hi hain.'}


@router.delete('/students/{id}/block')
async def unblock_student(id: str, response: Response, u=Depends(owner)):
    response.headers['Cache-Control'] = 'private, no-store'
    done = await db.tejas_phone_profiles.update_one({'id': id, 'blocked_at': {'$ne': None}},
                                                    {'$unset': {'blocked_at': '', 'blocked_by': ''}, '$set': {'unblocked_at': now(), 'unblocked_by': u['id']}})
    if not done.matched_count and not await db.tejas_phone_profiles.find_one({'id': id}, {'_id': 1}):
        raise HTTPException(404, MISSING)
    if done.matched_count:
        await audit(u['id'], 'owner_student_unblocked', id)
    return {'ok': True, 'blocked': False, 'message': 'Account phir se chalu ho gaya. Student apne number aur PIN se dobara sign in kar sakta hai.'}
