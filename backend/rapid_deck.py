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


def choose(pools, picks, count):
    """Every pick (a whole subject or one chapter) gets an even share; inside a whole subject every chapter does. No prompt twice."""
    seen, lanes = set(), []
    for p in picks:
        groups = {}
        for row in random.sample(pools[p['subject']], len(pools[p['subject']])):
            if not p['chapter'] or row['chapter'] == p['chapter']:
                groups.setdefault(row['chapter'], []).append(row)
        keys = list(groups)
        random.shuffle(keys)
        lanes.append({'groups': groups, 'keys': keys, 'turn': 0})

    def take(lane):
        while lane['keys']:
            key = lane['keys'][lane['turn'] % len(lane['keys'])]
            if not lane['groups'][key]:
                lane['keys'].remove(key)
                continue
            lane['turn'] += 1
            row = lane['groups'][key].pop()
            if row['fingerprint'] not in seen:
                seen.add(row['fingerprint'])
                return row['id']
        return None

    picked = []
    while len(picked) < count and any(lane['keys'] for lane in lanes):
        for lane in lanes:
            card_id = take(lane) if len(picked) < count else None
            if card_id:
                picked.append(card_id)
    if len(picked) < count:
        raise HTTPException(400, f'This selection has {len(picked)} unique quick-recall cards. Add another chapter for a full {count}-card round.')
    return picked


async def fresh_deck(db, exam, subject, chapter=None, count=30, picks=None):
    """`picks` (up to 5 subjects or chapters) wins over the single subject and chapter."""
    picks = picks or [{'subject': subject, 'chapter': chapter}]
    subjects = list(dict.fromkeys(p['subject'] for p in picks))

    async def forget():
        for s in subjects:
            await metadata_cache.invalidate_prefix(f'{db.name}:pool:{exam}:{s}')

    for attempt in range(2):
        try:
            ids = choose({s: await selection_pool(db, exam, s) for s in subjects}, picks, count)
        except HTTPException:
            if attempt:
                raise
            # A chapter may have gained cards since the metadata snapshot.
            await forget()
            continue
        docs = await db.rf_cards.find({'id': {'$in': ids}, 'exam': exam, 'subject': {'$in': subjects},
                                      'retired': {'$ne': True}}, {'_id': 0}).to_list(count)
        by_id = {c['id']: c for c in docs if not c.get('diagram') or c['diagram'].get('kind') in KINDS}
        if len(by_id) == count and len({fingerprint(c['prompt']) for c in by_id.values()}) == count:
            return [by_id[cid] for cid in ids]
        # Retired/deleted/changed cards are NEVER resurrected by a stale cache.
        await forget()
    raise HTTPException(409, 'The question bank changed. Please start this round again.')