import math
import re
from fastapi import APIRouter, Depends, Query, Response
from pydantic import BaseModel, Field
from .auth import owner
from .db import audit, db
from .documents import BaseDocument

router = APIRouter(prefix='/api/admin', tags=['Owner student directory'])


class StudentRecord(BaseDocument):
    profile_id: str = Field(alias='id')
    phone: str
    pin_version: int = Field(default=0, ge=0)
    display_name: str = ''


class StudentView(BaseModel):
    id: str
    phone: str
    pin_version: int
    display_name: str = ''


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
    records = await db.tejas_phone_profiles.find(query, {'id': 1, 'phone': 1, 'pin_version': 1, 'display_name': 1}).sort([('phone', 1), ('id', 1)]).skip((page - 1) * 50).limit(50).to_list(50)
    items = []
    for raw in records:
        record = StudentRecord.from_mongo(raw)
        items.append(StudentView(id=record.profile_id, phone=record.phone, pin_version=record.pin_version, display_name=record.display_name))
    await audit(u['id'], 'student_directory_read', 'student_directory')
    return StudentList(items=items, total=total, page=page, pages=max(1, math.ceil(total / 50)))
