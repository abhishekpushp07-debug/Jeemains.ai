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
    """One subject's playable cards, by chapter: {chapter: [[card id, short prompt fingerprint], ...]}.
    Kept small on purpose (a third of the size of one row per card with a full fingerprint) so every subject stays in memory."""
    async def load():
        groups = {}
        async for c in db.rf_cards.find({'exam': exam, 'subject': subject, 'retired': {'$ne': True}},
                                        {'_id': 0, 'id': 1, 'chapter': 1, 'prompt': 1, 'diagram.kind': 1}).batch_size(2000):
            if not c.get('diagram') or c['diagram'].get('kind') in KINDS:
                groups.setdefault(c['chapter'], []).append([c['id'], fingerprint(c['prompt'])[:16]])
        return groups
    return (await metadata_cache.get_or_load(f'{db.name}:pool:{exam}:{subject}', load, ttl=120))[0]


async def seen_cards(db, uid, exam):
    """Cards this student met in their recent rounds (solo sprints and matches): dealt again only after the unseen ones."""
    ids = set()
    async for s in db.rf_sessions.find({'user_id': uid, 'exam': exam}, {'_id': 0, 'card_ids': 1}).sort('created_at', -1).limit(40):
        ids.update(s.get('card_ids') or [])
    async for e in db.rf_learning_events.find({'uid': uid, 'exam': exam, 'ref': {'$regex': '^duel:'}}, {'_id': 0, 'results.card_id': 1}).sort('completed_at', -1).limit(40):
        ids.update(r['card_id'] for r in e.get('results') or [])
    return ids


def choose(pools, picks, count, avoid=frozenset()):
    """Every pick (a whole subject or one chapter) gets an even share; inside a whole subject every chapter does. No prompt twice.
    Inside each chapter the cards in `avoid` (already seen by this student) come last.
    Only the chapters a round really draws from are touched: a 30-card round never shuffles a 5,000-card subject."""
    seen, lanes = set(), []
    for p in picks:
        groups = pools[p['subject']]
        keys = [k for k in ([p['chapter']] if p['chapter'] else groups) if groups.get(k)]
        random.shuffle(keys)
        lanes.append({'groups': groups, 'keys': keys, 'turn': 0, 'left': {}})

    def draw(lane, key):
        """One more card of this chapter, in random order, unseen cards first. None once the chapter is used up."""
        left = lane['left'].get(key)
        if left is None:  # first card wanted from this chapter: split it once (the shared pool itself is never changed)
            rows = lane['groups'][key]
            left = lane['left'][key] = ([r for r in rows if r[0] not in avoid], [r for r in rows if r[0] in avoid])
        for rows in left:
            if rows:
                i = random.randrange(len(rows))
                rows[i], rows[-1] = rows[-1], rows[i]
                return rows.pop()
        return None

    def take(lane):
        while lane['keys']:
            key = lane['keys'][lane['turn'] % len(lane['keys'])]
            row = draw(lane, key)
            if row is None:
                lane['keys'].remove(key)
                continue
            lane['turn'] += 1
            if row[1] not in seen:
                seen.add(row[1])
                return row[0]
        return None

    picked = []
    while len(picked) < count and any(lane['keys'] for lane in lanes):
        for lane in lanes:
            card_id = take(lane) if len(picked) < count else None
            if card_id:
                picked.append(card_id)
    if len(picked) < count:
        raise HTTPException(400, f'This selection has {len(picked)} unique quick-recall cards. Add another chapter or choose fewer cards for a {count}-card round.')
    return picked


async def fresh_deck(db, exam, subject, chapter=None, count=30, picks=None, uid=None):
    """`picks` (up to 5 subjects or chapters) wins over the single subject and chapter. With `uid`, unseen cards come first."""
    picks = picks or [{'subject': subject, 'chapter': chapter}]
    subjects = list(dict.fromkeys(p['subject'] for p in picks))
    avoid = await seen_cards(db, uid, exam) if uid else frozenset()

    async def forget():
        for s in subjects:
            await metadata_cache.invalidate_prefix(f'{db.name}:pool:{exam}:{s}')

    for attempt in range(2):
        try:
            ids = choose({s: await selection_pool(db, exam, s) for s in subjects}, picks, count, avoid)
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