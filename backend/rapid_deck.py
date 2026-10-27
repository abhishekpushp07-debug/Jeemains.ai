"""Balanced decks: cache only selection metadata; fetch 30 authoritative cards."""
import hashlib
import random
import re
from fastapi import HTTPException
from metadata_cache import metadata_cache

KINDS = {'ydse', 'ellipse', 'charged_ring'}


def fingerprint(prompt):
    return hashlib.sha256(re.sub(r'\s+', ' ', prompt.strip().casefold()).encode()).hexdigest()


async def selection_pool(db, exam, subject):
    async def load():
        rows = await db.rf_cards.find({'exam': exam, 'subject': subject, 'retired': {'$ne': True}},
                                     {'_id': 0, 'id': 1, 'chapter': 1, 'prompt': 1, 'diagram.kind': 1}).to_list(12000)
        return [{'id': c['id'], 'chapter': c['chapter'], 'fingerprint': fingerprint(c['prompt'])}
                for c in rows if not c.get('diagram') or c['diagram'].get('kind') in KINDS]
    return (await metadata_cache.get_or_load(f'{db.name}:pool:{exam}:{subject}', load, ttl=120))[0]


def choose(pool, chapter, count):
    groups, seen = {}, set()
    for row in random.sample(pool, len(pool)):
        if (chapter and row['chapter'] != chapter) or row['fingerprint'] in seen:
            continue
        seen.add(row['fingerprint'])
        groups.setdefault(row['chapter'], []).append(row['id'])
    if len(seen) < count:
        raise HTTPException(400, f'This selection has {len(seen)} unique quick-recall cards. Choose a mixed subject for a full {count}-card round.')
    keys, picked = list(groups), []
    random.shuffle(keys)
    while len(picked) < count:
        for key in keys:
            if groups[key] and len(picked) < count:
                picked.append(groups[key].pop())
    return picked


async def fresh_deck(db, exam, subject, chapter=None, count=30):
    for attempt in range(2):
        try:
            ids = choose(await selection_pool(db, exam, subject), chapter, count)
        except HTTPException:
            if attempt:
                raise
            # A chapter may have gained cards since the metadata snapshot.
            await metadata_cache.invalidate_prefix(f'{db.name}:pool:{exam}:{subject}')
            continue
        docs = await db.rf_cards.find({'id': {'$in': ids}, 'exam': exam, 'subject': subject,
                                      'retired': {'$ne': True}}, {'_id': 0}).to_list(count)
        by_id = {c['id']: c for c in docs if not c.get('diagram') or c['diagram'].get('kind') in KINDS}
        if len(by_id) == count and len({fingerprint(c['prompt']) for c in by_id.values()}) == count:
            return [by_id[cid] for cid in ids]
        # Retired/deleted/changed cards are NEVER resurrected by a stale cache.
        await metadata_cache.invalidate_prefix(f'{db.name}:pool:{exam}:{subject}')
    raise HTTPException(409, 'The question bank changed. Please start this round again.')