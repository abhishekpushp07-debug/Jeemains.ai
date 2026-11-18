"""Display name: what a student is called on leaderboards, in Compare and on their own report. Never the phone number."""
import hashlib, re
from datetime import datetime, timezone, timedelta
from fastapi import APIRouter, Depends, HTTPException
from .auth import current, owner, forget_student
from .db import audit, db, now
from .rate_limits import increment
from .request_contracts import NamePayload

router = APIRouter(prefix='/api', tags=['Display name'])
profiles = db.tejas_phone_profiles
CHANGES_PER_DAY = 3
BLOCKED = ('fuck', 'shit', 'bitch', 'bastard', 'chutiya', 'chutiye', 'madarchod', 'bhenchod', 'behenchod', 'bhosdi', 'gandu', 'gaand', 'randi',
           'lund', 'lauda', 'harami', 'kamina', 'sex', 'porn', 'nude', 'admin', 'jeelive', 'official', 'owner', 'support')


def clean(raw):
    """2 to 20 letters, digits and spaces. Nothing that looks like a phone number, nothing abusive, nothing that looks official."""
    name = ' '.join(raw.split())
    if not name:
        return ''
    if not 2 <= len(name) <= 20 or any(not (ch.isalnum() or ch == ' ') for ch in name):
        raise HTTPException(422, 'Naam 2 se 20 akshar ka rakho: sirf akshar, ank aur space.')
    packed = name.replace(' ', '').lower()
    if re.search(r'\d{6,}', packed):
        raise HTTPException(422, 'Naam mein phone number jaisa kuch mat likho.')
    if any(word in packed for word in BLOCKED):
        raise HTTPException(422, 'Yeh naam nahi rakh sakte. Koi doosra naam likho.')
    return name


async def names_for(user_ids):
    ids = list({i for i in user_ids if i})
    if not ids:
        return {}
    found = await profiles.find({'id': {'$in': ids}, 'display_name': {'$type': 'string'}}, {'_id': 0, 'id': 1, 'display_name': 1}).to_list(len(ids))
    return {p['id']: p['display_name'] for p in found if p['display_name']}


@router.put('/profile/display-name')
async def set_display_name(data: NamePayload, u=Depends(current)):
    if u.get('access_type') != 'unverified_phone':
        raise HTTPException(403, 'Display naam sirf student account ke liye hai.')
    name = clean(data.name)
    stamp = now()
    key = hashlib.sha256(f"display-name:{u['id']}:{int(stamp // 86400)}".encode()).hexdigest()
    if await increment(db.tejas_phone_limits, key, datetime.now(timezone.utc) + timedelta(days=2)) > CHANGES_PER_DAY:
        raise HTTPException(429, f'Naam din mein {CHANGES_PER_DAY} baar hi badal sakta hai. Kal dobara try karo.')
    change = {'$set': {'display_name': name, 'display_key': name.lower(), 'display_name_at': stamp}} if name else {'$unset': {'display_name': '', 'display_key': ''}}
    await profiles.update_one({'id': u['id']}, change)
    forget_student(user_id=u['id'])
    return {'display_name': name}


@router.delete('/admin/students/{id}/display-name')
async def remove_display_name(id: str, u=Depends(owner)):
    done = await profiles.update_one({'id': id}, {'$unset': {'display_name': '', 'display_key': ''}, '$set': {'display_name_removed_at': now()}})
    if not done.matched_count:
        raise HTTPException(404, 'Student not found.')
    forget_student(user_id=id)
    await audit(u['id'], 'student_display_name_removed', id)
    return {'ok': True}
