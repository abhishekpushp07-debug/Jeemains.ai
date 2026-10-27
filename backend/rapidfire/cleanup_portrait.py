"""Approved destructive RF-only migration. --apply required; NO question backups.

Raw per-card hash-bound editorial decisions remain, but not rejected card content.
Wallets, ownership, coin awards and all archived NEET documents are fingerprinted
and checked unchanged. No canonical service calls or academic collection writes.
"""
import argparse
import asyncio
from collections import Counter
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path

from dotenv import load_dotenv
from motor.motor_asyncio import AsyncIOMotorClient

ROOT = Path(__file__).parent
load_dotenv(ROOT.parent / '.env')
VERSION = 'rapid_portrait_2026_v1'
FIELDS = ('uid', 'coins', 'owned', 'equipped', 'avatar', 'freezes')
REASONS = {'calculation', 'multistep', 'lengthy', 'borderline', 'ambiguous', 'incorrect', 'missing_diagram', 'recall'}
YDSE = {'268ae8d0-1b26-4ffb-8b93-847bf2e47fff', '991ef196-ea31-4a76-865f-7e47d64955e2', '69299baf-136c-4dab-84fe-d4bfeb62cb56',
        '0a763bd8-22e9-4e1e-a0fb-c64c1dd61b2e', '685c186e-012c-48f2-90a8-4f2fd1063554', '7aebbf0b-d6fe-48dd-b125-19f7b86b7ce5',
        'ffb79b5c-59f9-46df-afd4-ee3b711eaf1f', '21de4a6e-ab34-4405-ab4a-d4c6a174f608', '39be2eb9-6fad-4aaf-81fc-ed806856e65f', '53f31a3d-b5a8-44d1-8410-bee9b475bc2a'}
ELLIPSE = {'b579da18-f5c8-4f4a-b1a7-2ce19951140a', 'c079b6f6-d93a-42a7-a171-035bce179c04', '8e5c4383-960d-4131-9b27-919063c4acae'}


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, ensure_ascii=False, default=str).encode()).hexdigest()


async def protected(db):
    profiles = await db.rf_profiles.find({}, {'_id': 0}).sort('uid', 1).to_list(100000)
    result = {'wallet_ownership': digest([{k: p[k] for k in FIELDS if k in p} for p in profiles]),
              'neet_profile_stats': digest([{p['uid']: p.get('exam_stats', {}).get('NEET')} for p in profiles]),
              'coins_sum': sum(p.get('coins', 0) for p in profiles), 'profiles': len(profiles)}
    for name in ('rf_cards', 'rf_sessions', 'rf_duels', 'rf_learning_events'):
        docs = await db[name].find({'exam': 'NEET'}, {'_id': 0}).sort('_id', 1).to_list(100000)
        result[name + '_neet'] = digest(docs)
    result['coin_awards'] = digest(await db.rf_awards.find({}, {'_id': 0}).sort('_id', 1).to_list(100000))
    return result


def diagram_for(card):
    if card['id'] in YDSE:
        return {'kind': 'ydse', 'caption': 'Double-slit geometry: separation d, screen distance D', 'medium': card['id'] == '268ae8d0-1b26-4ffb-8b93-847bf2e47fff'}
    if card['id'] in ELLIPSE:
        return {'kind': 'ellipse', 'caption': 'Ellipse with horizontal semi-axis a and vertical semi-axis b'}
    if card['prompt'] == 'E on axis of uniformly charged ring at distance x from centre':
        return {'kind': 'charged_ring', 'caption': 'Charged ring Q, radius R, axial observation point P'}
    return card.get('diagram')


async def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--apply', action='store_true')
    args = parser.parse_args()
    client = AsyncIOMotorClient(os.environ['MONGO_URL'])
    db = client[os.environ['DB_NAME']]
    if await db.rf_migrations.find_one({'name': VERSION, 'completed': True}):
        print('Already applied; no further deletions or resets.')
        return
    review = [r for p in sorted((ROOT / 'portrait_review').glob('*.json')) for r in json.loads(p.read_text())]
    decisions = {r['id']: r for r in review}
    files = {p: json.loads(p.read_text()) for p in (ROOT / 'cards').glob('*.json') if not p.name.startswith('biology')}
    cards = [c for rows in files.values() for c in rows]
    assert len(decisions) == len(review) == 7045, 'Incomplete full-bank review: NO deletion allowed'
    saved = await db.rf_migrations.find_one({'name': VERSION})
    if not saved:
        assert {c['id'] for c in cards} == set(decisions), 'Source bank mismatch'
        active = await db.rf_cards.distinct('id', {'exam': 'JEE', 'retired': {'$ne': True}})
        assert set(active) == set(decisions), 'An active DB card has not been reviewed'
        for c in cards:
            r = decisions[c['id']]
            assert r['sha256'] == digest(c), 'Content changed since review'
            assert r['reason_code'] in REASONS and isinstance(r['keep'], bool)
            assert not r['keep'] or (r['estimated_seconds'] <= 15 and r['reason_code'] == 'recall')
    kept = {r['id'] for r in review if r['keep']}
    summary = {'version': VERSION, 'reviewed': len(review), 'kept': len(kept), 'deleted_active_cards': len(review) - len(kept),
               'reasons': dict(Counter(r['reason_code'] for r in review if not r['keep'])),
               'kept_by_subject': dict(Counter(r['subject'] for r in review if r['keep'])),
               'timing_note': 'AI-assisted full-card editorial estimate, not a student timing guarantee.'}
    print(json.dumps(summary, indent=2))
    if not args.apply:
        print('DRY RUN ONLY: source cards, database and history unchanged.')
        return
    await db.rf_maintenance.update_one({'_id': 'portrait-cleanup'}, {'$set': {'active': True}}, upsert=True)
    await asyncio.sleep(3)  # allow pre-existing RF requests to settle before invariant capture
    before = saved['protected_before'] if saved else await protected(db)
    await db.rf_migrations.update_one({'name': VERSION}, {'$setOnInsert': {'protected_before': before, 'started_at': datetime.now(timezone.utc).isoformat()}}, upsert=True)
    diagram_count = 0
    for path, rows in files.items():
        clean = []
        for c in rows:
            if c['id'] not in kept:
                continue
            diagram = diagram_for(c)
            if diagram:
                c['diagram'] = diagram
                diagram_count += 1
            c['review_status'] = 'quick_recall_reviewed_v1'
            clean.append(c)
        # Atomic replacement, no rejected-question archive is created.
        tmp = path.with_suffix('.portrait-tmp')
        tmp.write_text(json.dumps(clean, indent=2, ensure_ascii=False) + '\n')
        tmp.replace(path)
        for c in clean:
            await db.rf_cards.update_one({'id': c['id'], 'exam': 'JEE'}, {'$set': {'diagram': c.get('diagram'), 'review_status': c['review_status'], 'retired': False}})
    deleted = await db.rf_cards.delete_many({'exam': 'JEE', 'id': {'$nin': sorted(kept)}})
    summary['deleted_db_records_including_previously_retired'] = deleted.deleted_count
    summary['diagrams'] = diagram_count
    for name in ('rf_sessions', 'rf_duels', 'rf_learning_events'):
        res = await db[name].delete_many({'exam': 'JEE'})
        summary['deleted_' + name] = res.deleted_count
    # Preserve every wallet record. Reset only match-derived counters; shared
    # balances, owned/equipped cosmetics, freezes, streaks and claimed quests stay.
    async for p in db.rf_profiles.find({}, {'_id': 0}):
        neet = p.get('exam_stats', {}).get('NEET', {})
        neet_sessions = await db.rf_sessions.count_documents({'exam': 'NEET', 'user_id': p['uid'], 'summary.answered': {'$gt': 0}})
        neet_duels = await db.rf_duels.count_documents({'exam': 'NEET', 'status': 'finished', 'players': {'$elemMatch': {'uid': p['uid'], 'answers.0': {'$exists': True}}}})
        fields = {'exam_stats.JEE': {'xp': 0, 'wins': 0, 'cards_correct': 0}, 'xp': neet.get('xp', 0), 'wins': neet.get('wins', 0),
                  'cards_correct': neet.get('cards_correct', 0), 'sessions': neet_sessions, 'duels': neet_duels, 'rival_games': 0}
        if not neet.get('xp'):
            fields['badges'] = [b for b in p.get('badges', []) if b.startswith('streak_')]
            if 'day_stats' in p:
                fields['day_stats'] = {**p['day_stats'], 'sprints': 0, 'correct': 0, 'wins': 0}
        await db.rf_profiles.update_one({'uid': p['uid']}, {'$set': fields})
    # Ephemeral push bus contains only match IDs/timestamps, not currency records.
    await db.rf_events.drop()
    await db.create_collection('rf_events', capped=True, size=32 * 1024 * 1024, max=200000)
    after = await protected(db)
    assert before == after, 'STOP: a protected invariant changed; maintenance intentionally remains enabled'
    assert await db.rf_cards.count_documents({'exam': 'JEE', 'retired': {'$ne': True}}) == len(kept)
    summary.update(protected_before=before, protected_after=after, completed_at=datetime.now(timezone.utc).isoformat(), completed=True)
    await db.rf_migrations.update_one({'name': VERSION}, {'$set': summary})
    (ROOT / 'portrait_cleanup_report.json').write_text(json.dumps(summary, indent=2))
    await db.rf_maintenance.update_one({'_id': 'portrait-cleanup'}, {'$set': {'active': False}})
    print('APPLIED: protected data fingerprints identical.', json.dumps(summary))
    client.close()


if __name__ == '__main__':
    asyncio.run(main())