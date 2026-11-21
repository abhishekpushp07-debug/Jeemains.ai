"""Red alert for the Super Admin: the same question twice inside one section and one subject (any chapter of it).
Plain matching of the words the PDF reader already took from the page; no AI. Different sections or subjects never count."""
import hashlib, re, time
from fastapi import APIRouter, Depends, HTTPException
from .auth import staff
from .db import db, sets

router = APIRouter(prefix='/api/admin', tags=['Duplicates'])
MIN_CHARS = 30
_LEAD = re.compile(r'^\s*(?:q(?:uestion)?\s*)?\(?\d{1,3}\)?\s*[.):-]?\s*', re.I)
_cache = {}


def fingerprint(text):
    """Letters and digits of a question, without its printed number. Too short to tell apart: None."""
    words = re.sub(r'[\W_]+', '', _LEAD.sub('', text or '', count=1).lower())
    return hashlib.sha1(words.encode()).hexdigest() if len(words) >= MIN_CHARS else None


def subject_of(name):
    return re.sub(r'\s+', ' ', (name or 'general').strip().lower())


def matches(items):
    """{item id: [{question_id, number, subject, matches: [{id, title, number}]}]} for every question seen more than once."""
    seen = {}
    for it in items:
        for q in it['questions']:
            fp = fingerprint(q['text'])
            if fp:
                seen.setdefault((subject_of(q['subject']), fp), []).append((it, q))
    out = {}
    for group in seen.values():
        if len(group) < 2:
            continue
        for it, q in group:
            others = [{'id': o['id'], 'title': o['title'], 'number': oq['number']} for o, oq in group if (o['id'], oq['id']) != (it['id'], q['id'])]
            out.setdefault(it['id'], []).append({'question_id': q['id'], 'number': q['number'], 'subject': q['subject'], 'matches': others[:5]})
    for rows in out.values():
        rows.sort(key=lambda r: (str(r['subject']), r['number'] or 0))
    return out


async def section_items(sid):
    """Every test of the section a student can or will see, and every uploaded mock waiting to go Live."""
    from .structure import section_doc, exams, section_tests, waiting_items
    s = await section_doc(sid)
    e = await exams.find_one({'_id': s['exam_slug']}, {'_id': 0, 'key': 1})
    # A test being replaced by a new upload is left out: the new copy is meant to repeat it.
    ids = [t['id'] for t in await section_tests(s, e['key']) if not t.get('replace_pending') and t.get('status') != 'withdrawn']
    waiting = [w['id'] for w in await waiting_items(sid) if w['kind'] == 'book_mock']
    items = []
    async for x in sets.find({'id': {'$in': ids}}, {'_id': 0, 'id': 1, 'title': 1, 'display_title': 1, 'questions.id': 1, 'questions.number': 1,
                                                    'questions.subject': 1, 'questions.accessible_text': 1, 'questions.text': 1}):
        items.append({'id': x['id'], 'title': x.get('display_title') or x['title'],
                      'questions': [{'id': q['id'], 'number': q.get('number'), 'subject': q.get('subject'), 'text': q.get('accessible_text') or q.get('text') or ''} for q in x.get('questions', [])]})
    async for m in db.tejas_book_mocks.find({'_id': {'$in': waiting}}, {'_id': 1, 'label': 1, 'chapter': 1, 'questions.id': 1, 'questions.number': 1,
                                                                          'questions.subject': 1, 'questions.text': 1}):
        chapter = m.get('chapter') or {}
        items.append({'id': m['_id'], 'title': chapter.get('title') or m['label'],
                      'questions': [{'id': q['id'], 'number': q.get('number'), 'subject': chapter.get('subject') or q.get('subject'), 'text': q.get('text') or ''}
                                    for q in m.get('questions', [])]})
    return items


async def section_duplicates(sid):
    """Cached for a minute per section: the Master page and the Fix page ask often, papers change rarely."""
    hit = _cache.get(sid)
    if hit and time.time() - hit[0] < 60:
        return hit[1]
    out = matches(await section_items(sid))
    _cache[sid] = (time.time(), out)
    if len(_cache) > 50:
        _cache.pop(min(_cache, key=lambda k: _cache[k][0]))
    return out


def forget(sid):
    _cache.pop(sid, None)


@router.get('/duplicates/mock/{mock_id}')
async def mock_duplicates(mock_id: str, u=Depends(staff)):
    m = await db.tejas_book_mocks.find_one({'_id': mock_id}, {'_id': 1, 'book_id': 1})
    if not m:
        raise HTTPException(404, 'Mock not found.')
    b = await db.tejas_books.find_one({'_id': m['book_id']}, {'payload.destination': 1}) or {}
    dest = (b.get('payload') or {}).get('destination') or {}
    if not dest.get('section_id') or dest.get('series'):
        return {'items': [], 'checked': False}
    forget(dest['section_id'])
    return {'items': (await section_duplicates(dest['section_id'])).get(mock_id, []), 'checked': True}
