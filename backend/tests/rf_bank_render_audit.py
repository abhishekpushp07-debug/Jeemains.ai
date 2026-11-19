# Read-only audit of the RF card bank: answer-key position spread and risky rendering patterns (English/LR focus)
import os, re, asyncio
from collections import Counter
from dotenv import load_dotenv
from motor.motor_asyncio import AsyncIOMotorClient

load_dotenv('/app/backend/.env')


async def main():
    db = AsyncIOMotorClient(os.environ['MONGO_URL'])[os.environ['DB_NAME']]
    q = {'retired': {'$ne': True}}
    by = {}
    risky = []
    async for c in db.rf_cards.find(q, {'_id': 0, 'id': 1, 'subject': 1, 'prompt': 1, 'options': 1, 'answer': 1, 'chapter': 1}):
        s = c.get('subject')
        by.setdefault(s, Counter())[c.get('answer')] += 1
        texts = [c.get('prompt') or ''] + list(c.get('options') or [])
        if s in ('English', 'Logical Reasoning'):
            for t in texts:
                # underscore touching a letter -> RapidText notation() turns "_x" into a subscript
                if re.search(r'_[a-z0-9+\-]', t, re.I) or re.search(r'[A-Za-z]_', t) or '^' in t or '$' in t or '\\' in t:
                    risky.append((s, c['id'], t[:140]))
                    break
            for o in c.get('options') or []:
                if len(o) > 40:
                    risky.append((s, c['id'], 'LONG OPTION(%d): %s' % (len(o), o)))
    for s, cnt in by.items():
        tot = sum(cnt.values())
        print(s, tot, {k: round(100 * v / tot) for k, v in sorted(cnt.items(), key=lambda x: str(x[0]))})
    print('risky', len(risky))
    for r in [x for x in risky if not x[2].startswith("LONG")]:
        print(r)


asyncio.run(main())
