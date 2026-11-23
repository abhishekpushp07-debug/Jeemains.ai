"""Mission 'Contacts se invite': friends a student picks on their own phone (the browser's contact picker, Android Chrome).
Only what the student picked is sent, saved with their consent so the team can see who was invited. The student can remove any."""
import phonenumbers
from fastapi import APIRouter, Depends, HTTPException
from pymongo import UpdateOne
from pymongo.errors import BulkWriteError
from .auth import current
from .db import db, uid, now
from .request_contracts import ContactsPayload

router = APIRouter(prefix='/api/mission', tags=['Mission contacts'])
contacts = db.tejas_invite_contacts
MAX = 500
CONSENT = 'student_picked_contact_picker_v1'


def e164(raw):
    try:
        p = phonenumbers.parse(raw, 'IN')
        return phonenumbers.format_number(p, phonenumbers.PhoneNumberFormat.E164) if phonenumbers.is_valid_number(p) else None
    except phonenumbers.NumberParseException:
        return None


def student(u):
    if u.get('access_type') != 'unverified_phone':
        raise HTTPException(403, 'Contacts sirf student account se jodte hain.')
    return u


async def own(user_id):
    rows = await contacts.find({'user_id': user_id}, {'_id': 0, 'id': 1, 'name': 1, 'phone': 1, 'at': 1}).sort('at', -1).limit(MAX).to_list(MAX)
    return {'items': rows, 'max': MAX}


@router.get('/contacts')
async def list_contacts(u=Depends(current)):
    return await own(student(u)['id'])


@router.post('/contacts')
async def save_contacts(data: ContactsPayload, u=Depends(current)):
    student(u)
    picked, seen, skipped = [], set(), 0
    for c in data.contacts:
        phone = next((p for p in map(e164, c.tel) if p), None)
        if not phone or phone == u.get('phone') or phone in seen:
            skipped += 1
            continue
        seen.add(phone)
        picked.append((phone, c.name.strip()[:80]))
    known = set(await contacts.distinct('phone', {'user_id': u['id'], 'phone': {'$in': list(seen)}})) if seen else set()
    room = max(0, MAX - await contacts.count_documents({'user_id': u['id']}))
    fresh = [p for p, _ in picked if p not in known]
    allowed = known | set(fresh[:room])
    t = now()
    ops = [UpdateOne({'user_id': u['id'], 'phone': p}, {'$set': {'name': name, 'updated_at': t},
                     '$setOnInsert': {'id': uid(), 'at': t, 'consent': CONSENT}}, upsert=True) for p, name in picked if p in allowed]
    if ops:
        try:
            await contacts.bulk_write(ops, ordered=False)
        except BulkWriteError as e:
            if any(err.get('code') != 11000 for err in e.details.get('writeErrors', [])):
                raise
    return {'saved': len(ops), 'skipped': skipped + len(fresh) - len(fresh[:room]), 'full': len(fresh) > room, **await own(u['id'])}


@router.delete('/contacts/{id}')
async def remove_contact(id: str, u=Depends(current)):
    await contacts.delete_one({'id': id, 'user_id': student(u)['id']})
    return {'removed': True}
