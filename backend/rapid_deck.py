"""Unique, chapter-balanced fresh Rapid Fire decks, never padded or recycled."""
import random
import re
from fastapi import HTTPException


async def fresh_deck(db, exam, subject, chapter=None, count=30):
    query = {'exam': exam, 'subject': subject, 'retired': {'$ne': True}}
    if chapter:
        query['chapter'] = chapter
    pool = await db.rf_cards.find(query, {'_id': 0}).to_list(12000)
    random.shuffle(pool)
    groups, seen = {}, set()
    for card in pool:
        if card.get('diagram') and card['diagram'].get('kind') not in {'ydse', 'ellipse', 'charged_ring'}:
            continue  # never serve an essential diagram the native app cannot render
        key = re.sub(r'\s+', ' ', card['prompt'].strip().casefold())
        if key in seen:
            continue
        seen.add(key)
        groups.setdefault(card['chapter'], []).append(card)
    if len(seen) < count:
        raise HTTPException(400, f'This selection has {len(seen)} unique quick-recall cards. Choose a mixed subject for a full {count}-card round.')
    keys = list(groups)
    random.shuffle(keys)
    picked = []
    while len(picked) < count:
        for key in keys:
            if groups[key] and len(picked) < count:
                picked.append(groups[key].pop())
    return picked