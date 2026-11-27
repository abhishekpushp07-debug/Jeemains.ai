"""Student Choice (JEE Main): a student makes his own paper from the live JEE Main chapter-wise questions.
Door A GET /api/choice/bank, door B GET /api/choice/chapters/{id}/questions, door C POST /api/choice/papers: the exact
contract of the app's book (docs/app_book_v3/BOOK.md Part 1.6). A made paper lives in tejas_choice_papers, never in
tejas_sets, so no catalogue, Master, Library or owner count lists it; attempts.py opens it for its owner only.
Its questions are copied from the chapter tests on its first Start and never change after that."""
import asyncio, base64, copy, hashlib, hmac, math, random, re, time, uuid
from collections import OrderedDict
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Query, Response
from pymongo.errors import DuplicateKeyError
from starlette.concurrency import run_in_threadpool
from .auth import current, owner
from .cache import ByteCache
from .canonical import clocked_one, database_now
from .db import db, sets, files, now, audit
from .live_series import IST
from .request_contracts import ChoicePaperPayload, ChoiceSettingsPayload

router = APIRouter(prefix='/api', tags=['Student Choice'])
settings_coll = db.tejas_choice_settings
papers = db.tejas_choice_papers
days = db.tejas_choice_days

SUBJECTS = ('Physics', 'Chemistry', 'Mathematics')
SHORT = {'Physics': 'Physics', 'Chemistry': 'Chemistry', 'Mathematics': 'Maths'}
EXAMS = {'jee-main': 'JEE Main'}
MINUTES = {'Physics': 2.4, 'Chemistry': 1.6, 'Mathematics': 3.2}
DEFAULTS = {'pick': False, 'random': False, 'max_questions': 75, 'max_per_subject': None, 'minutes': MINUTES, 'daily_limit': 5}
TOP, PAGE, MAX_PAGES, MAX_STEM, TEXT, DAY = 75, 50, 6, 4, 3000, 86400
ID = re.compile(r'[A-Za-z0-9_-]{6,80}')
KEY = re.compile(r'[A-Za-z0-9_-]{8,100}')

TOO_MANY = 'Ek paper me zyada se zyada {n} sawaal ho sakte hain.'
GONE = 'Chune hue sawaalon me se kuch ab available nahi hain. Dobara chuno.'
RANGE = '3 se {n} ke beech ginti likho.'
DAILY = 'Aaj ke {n} paper ban chuke hain. Kal naya paper bana sakte ho.'
STALE = 'Is paper ke kuch sawaal ab available nahi hain. Naya paper bana lo.'
CLOSED = 'Paper banana abhi band hai.'
LOADING = 'Sawaal abhi load nahi ho paaye. Dobara try karo.'
NONE_PICKED = 'Kam se kam ek sawaal chuno.'
PER_SUBJECT = '{s} ke zyada se zyada {n} sawaal ho sakte hain. Koi hatao, tab naya chuno.'
FEW = 'Abhi {s} ke sirf {n} sawaal hain. Kam ginti likho.'
BAD_KEY = 'Paper ban nahi paaya. Dobara try karo.'
NO_EXAM = 'Is exam ke liye Student Choice abhi nahi hai.'
NO_CHAPTER = 'Is chapter ke sawaal abhi yahan nahi khul paaye. Doosra chapter chuno, ya thodi der mein dobara dekho.'

_settings, _pool, _views, _frozen = {}, {'at': -1e9, 'value': None}, OrderedDict(), OrderedDict()
_pool_lock = asyncio.Lock()
_pictures, _flights = ByteCache(48 * 1024 * 1024), {}


def reset():
    """Forget every in-memory copy (tests, and after an owner change)."""
    _settings.clear(); _views.clear(); _frozen.clear(); _pictures.data.clear(); _pictures.size = 0
    _pool.update(at=-1e9, value=None)


def ist_day(t):
    return datetime.fromtimestamp(t, IST).date().isoformat()


def minutes_for(counts, per):
    """Each question brings its subject's minutes; the sum is rounded up to a whole minute (book Part 1.4)."""
    return int(math.ceil(round(sum(per[s] * n for s, n in counts.items()), 4)))


def split_of(n, subjects):
    """Equal over the subjects; one or two left over go to the first ones (Physics, then Chemistry)."""
    return {s: n // len(subjects) + (1 if i < n % len(subjects) else 0) for i, s in enumerate(subjects)}


def token_of(set_id, qid):
    """The question's stable id in Student Choice and in every paper made from it (a UUID, like every question id)."""
    return str(uuid.uuid5(uuid.NAMESPACE_URL, f'jeelive-choice-question:{set_id}:{qid}'))


# ------------------------------------------------------------------ settings (one document per exam)

def view_settings(doc):
    out = {**DEFAULTS, **{k: doc[k] for k in DEFAULTS if k in doc}}
    out['minutes'] = {s: float((out.get('minutes') or {}).get(s, MINUTES[s])) for s in SUBJECTS}
    return {**out, 'revision': doc.get('revision', 0), 'updated_at': doc.get('updated_at'), 'updated_by': doc.get('updated_by')}


async def settings_of(exam):
    hit = _settings.get(exam)
    if hit and hit[0] > time.monotonic():
        return hit[1]
    value = view_settings(await settings_coll.find_one({'_id': exam}, {'_id': 0}) or {})
    _settings[exam] = (time.monotonic() + 15, value)
    return value


# ------------------------------------------------------------------ the pool: live JEE Main chapter-wise tests

def choosable(q):
    return q.get('type') in ('mcq', 'integer') and q.get('disposition', 'standard') != 'dropped' and not q.get('bonus')


def chapter_title(s):
    title = (s.get('display_title') or s.get('title') or '').strip()
    n = s.get('chapter_number')
    return re.sub(rf'^0*{n}\s+(?=\S)', '', title) if isinstance(n, int) and n > 0 else title


async def _load_pool():
    from .exam_navigation import classify_set
    from .structure import ORDER, exam_doc, live_query, section_by_slug, visibility
    out = {'chapters': {}, 'questions': {}, 'by_subject': {s: [] for s in SUBJECTS}, 'bank': {s: {'mcq': [], 'integer': []} for s in SUBJECTS}}
    await visibility()
    try:
        exam = await exam_doc('jee-main')
        section = await section_by_slug('jee-main', 'chapters', None)
    except HTTPException:
        return out  # the owner has hidden JEE Main or its chapter-wise section: nothing to choose from
    fields = {'_id': 0, 'id': 1, 'title': 1, 'display_title': 1, 'chapter_number': 1, 'chapter_subject': 1, 'chapter_book_id': 1, 'test_kind': 1,
              'full_length': 1, 'status': 1, 'live_enabled': 1, 'revision': 1, 'version': 1, 'rights_report': 1,
              'questions.id': 1, 'questions.number': 1, 'questions.type': 1, 'questions.disposition': 1, 'questions.bonus': 1}
    async for s in sets.find(live_query(None, exam, section), fields).sort(ORDER).limit(600):
        subject = s.get('chapter_subject')
        if classify_set(s) != 'chapter' or subject not in SUBJECTS or s.get('status') != 'published' or s.get('live_enabled') is False:
            continue
        order = len(out['by_subject'][subject])
        qs = [q for q in s.get('questions', []) if choosable(q) and q.get('id')]
        if not qs:
            continue
        out['by_subject'][subject].append(s['id'])
        out['chapters'][s['id']] = {'id': s['id'], 'title': chapter_title(s), 'subject': subject, 'number': s.get('chapter_number'), 'order': order,
                                    'revision': s.get('revision'), 'count': len(qs), 'mcq': sum(q['type'] == 'mcq' for q in qs),
                                    'integer': sum(q['type'] == 'integer' for q in qs)}
        for q in qs:
            token = token_of(s['id'], q['id'])
            out['questions'][token] = {'token': token, 'set_id': s['id'], 'question_id': q['id'], 'subject': subject, 'type': q['type'],
                                       'order': order, 'number': q.get('number') or 0}
            out['bank'][subject][q['type']].append(token)
    return out


async def pool():
    if _pool['value'] is not None and time.monotonic() - _pool['at'] < 30:
        return _pool['value']
    async with _pool_lock:
        if _pool['value'] is None or time.monotonic() - _pool['at'] >= 30:
            _pool.update(value=await _load_pool(), at=time.monotonic())
    return _pool['value']


# ------------------------------------------------------------------ door B: a chapter's questions, never options

QUESTION_FIELDS = {'_id': 0, 'id': 1, 'title': 1, 'display_title': 1, 'chapter_number': 1, 'chapter_subject': 1, 'revision': 1, 'exam': 1,
                   'status': 1, 'test_kind': 1, 'chapter_book_id': 1,
                   **{f'questions.{k}': 1 for k in ('id', 'number', 'type', 'text', 'render_mode', 'c_refs', 'q_refs', 'disposition', 'bonus', 'options')}}
_HEAD = re.compile(r'^\s*(Q\s*\d+\s*\.?|(single|multiple|one or more)\s+(option\s+)?correct.*|integer\s+(type|response|answer).*|numerical.*)\s*$', re.I)
_OPTION = re.compile(r'(?:^|\s)\(\s*A\s*\)')


def typed_words(text, cut_options):
    """The question's own words: the printed 'Q 4.' and 'Single correct' lines go, and for a picture MCQ everything from '(A)'."""
    from tejas_core import without_source
    lines = without_source(str(text or '')).split('\n')
    while lines and (not lines[0].strip() or _HEAD.match(lines[0])):
        lines.pop(0)
    words = '\n'.join(lines).strip()
    if cut_options:
        m = _OPTION.search(words)
        if not m:
            return None
        words = words[:m.start()].strip()
    return words[:TEXT] or None


def rect_size(ref):
    r = ref.get('rect')
    if isinstance(r, (list, tuple)) and len(r) == 4 and all(isinstance(x, (int, float)) for x in r) and r[2] > r[0] and r[3] > r[1]:
        return round(r[2] - r[0], 1), round(r[3] - r[1], 1)
    return None, None


def listed(q):
    """(text, [ref with w/h]) as the list shows it, or None. The server picks the pieces; a link never names a crop."""
    if q.get('c_refs'):
        pieces = [r for r in q['c_refs'] if r.get('part') == 'q' and r.get('file_id')][:MAX_STEM]
        if pieces:
            return '', [{'ref': r, 'w': r.get('w'), 'h': r.get('h')} for r in pieces]
    refs = [r for r in q.get('q_refs') or [] if r.get('file_id')]
    mode = q.get('render_mode')
    if mode == 'source' or (refs and mode != 'written'):
        if q['type'] == 'integer' and refs:
            return '', [{'ref': r, 'w': rect_size(r)[0], 'h': rect_size(r)[1]} for r in refs[:MAX_STEM]]
        words = typed_words(q.get('text'), cut_options=q['type'] == 'mcq')
        return (words, []) if words else None
    if mode == 'written':
        labels = set(q.get('options') or {})
        refs = [r for r in refs if str(r.get('label', '')).strip().upper() not in labels][:MAX_STEM]
        words = (str(q.get('text') or '').strip())[:TEXT]
        return (words, [{'ref': r, 'w': rect_size(r)[0], 'h': rect_size(r)[1]} for r in refs]) if words or refs else None
    words = typed_words(q.get('text'), cut_options=False)
    return (words, []) if words else None


async def chapter_view(set_id, revision=None):
    """A chapter test's listable questions in its order, built once per revision."""
    key = (set_id, revision)
    hit = _views.get(key)
    if hit is not None:
        _views.move_to_end(key)
        return hit
    query = {'id': set_id, 'status': 'published', **({'revision': revision} if revision is not None else {})}
    s = await sets.find_one(query, QUESTION_FIELDS)
    if not s or s.get('exam') != 'JEE Main':
        return None
    items, by_token = [], {}
    for q in s.get('questions', []):
        if not choosable(q) or not q.get('id'):
            continue
        shown = listed(q)
        if not shown:
            continue
        item = {'token': token_of(set_id, q['id']), 'number': q.get('number') or len(items) + 1, 'type': q['type'], 'text': shown[0], 'stems': shown[1]}
        items.append(item)
        by_token[item['token']] = item
    view = {'id': set_id, 'title': chapter_title(s), 'subject': s.get('chapter_subject'), 'items': items[:MAX_PAGES * PAGE], 'by_token': by_token}
    _views[key] = view
    while len(_views) > 160:
        _views.popitem(last=False)
    return view


def _sig(set_id, token, index, exp):
    from .media import _KEY
    raw = hmac.new(_KEY, f'choice-v1.{set_id}.{token}.{index}.{exp}'.encode(), hashlib.sha256).digest()
    return base64.urlsafe_b64encode(raw[:16]).decode().rstrip('=')


def picture_base():
    import os
    from urllib.parse import urlsplit
    from .media import CDN
    if CDN:
        return CDN
    u = urlsplit(os.environ['FRONTEND_URL'])
    return f'https://{u.netloc}'


def stem_links(set_id, item, exp):
    base = picture_base()
    out = []
    for i, st in enumerate(item['stems']):
        link = {'url': f"{base}/api/media/choice/{set_id}/{item['token']}/{i}-{exp}-{_sig(set_id, item['token'], i, exp)}"}
        if isinstance(st.get('w'), (int, float)) and isinstance(st.get('h'), (int, float)) and st['w'] > 0 and st['h'] > 0:
            link.update(w=st['w'], h=st['h'])
        out.append(link)
    return out


# ------------------------------------------------------------------ door A

@router.get('/choice/bank')
async def bank(exam: str = Query('', max_length=40), u=Depends(current)):
    """Which ways are open. 404 = both closed. Never 5xx: any trouble here reads as closed, so the app's chapter list never fails."""
    try:
        s = await settings_of(exam) if exam in EXAMS else None
        if s and (s['pick'] or s['random']):
            return {'pick': bool(s['pick']), 'random': bool(s['random']), 'max_questions': int(s['max_questions']),
                    'max_per_subject': s['max_per_subject'], 'minutes_per_question': dict(s['minutes'])}
    except Exception:  # noqa: BLE001
        pass
    raise HTTPException(404, 'Student Choice abhi band hai.')


# ------------------------------------------------------------------ door B

@router.get('/choice/chapters/{set_id}/questions')
async def chapter_questions(set_id: str, page: int = Query(1, ge=1, le=1000), u=Depends(current)):
    try:
        s = await settings_of('jee-main')
        live = await pool()
        chapter = live['chapters'].get(set_id) if s['pick'] and ID.fullmatch(set_id) else None
        view = await chapter_view(set_id, chapter['revision']) if chapter else None
    except Exception:  # noqa: BLE001
        raise HTTPException(503, LOADING)
    if not view or not view['items']:
        raise HTTPException(404, NO_CHAPTER)
    pages = min(MAX_PAGES, math.ceil(len(view['items']) / PAGE))
    if page > pages:
        raise HTTPException(404, NO_CHAPTER)
    exp = (int(time.time() // DAY) + 2) * DAY
    rows = view['items'][(page - 1) * PAGE:page * PAGE]
    return {'chapter': {'id': set_id, 'title': chapter['title'][:120], 'subject': chapter['subject']}, 'pages': pages,
            'items': [{'id': it['token'], 'number': max(1, min(9999, int(it['number']))), 'type': it['type'], 'text': it['text'] or '',
                       'stem': stem_links(set_id, it, exp)} for it in rows]}


_NAME = re.compile(r'(\d{1,2})-(\d{10})-([A-Za-z0-9_-]{22})')


async def picture_bytes(ref):
    from .derivatives import render_crop
    from .pictures import webp_of
    f = await files.find_one({'id': ref['file_id'], 'is_deleted': {'$ne': True}}, {'_id': 0})
    if not f:
        return None
    key = hashlib.sha256(repr((f.get('sha256') or f.get('path'), sorted(ref.items(), key=str))).encode()).hexdigest()
    hit = _pictures.get(key)
    if hit is not None:
        return hit
    flight = _flights.get(key)
    if flight is None:
        async def build():
            raw = await run_in_threadpool(render_crop, f, ref)
            light = await run_in_threadpool(webp_of, raw)
            return _pictures.put(key, light or raw)
        flight = _flights[key] = asyncio.ensure_future(build())
        flight.add_done_callback(lambda _: _flights.pop(key, None))
    return await asyncio.shield(flight)


@router.get('/media/choice/{set_id}/{token}/{name}')
async def choice_picture(set_id: str, token: str, name: str):
    """A listed question's own piece, public and cookie-free while its signed link lives (24 to 48 hours)."""
    m, t = _NAME.fullmatch(name), time.time()
    if not m or not ID.fullmatch(set_id) or not re.fullmatch(r'[0-9a-f]{8}-[0-9a-f]{4}-5[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}', token):
        raise HTTPException(404, 'Picture not found.')
    index, exp, sig = int(m[1]), int(m[2]), m[3]
    if not hmac.compare_digest(sig, _sig(set_id, token, index, exp)) or not t < exp <= t + 3 * DAY:
        raise HTTPException(404, 'This picture link is not valid. Reload the list to get fresh links.')
    view = await chapter_view(set_id)
    item = (view or {}).get('by_token', {}).get(token)
    if not item or index >= len(item['stems']):
        raise HTTPException(404, 'Picture not found.')
    from tejas_storage import StorageError
    from .canonical import CanonicalIntegrityError
    try:
        got = await picture_bytes(item['stems'][index]['ref'])
    except StorageError:
        raise HTTPException(503, 'Is sawaal ki picture abhi load nahi hui. Dobara try karo.') from None
    except (ValueError, KeyError, CanonicalIntegrityError):
        raise HTTPException(404, 'Picture not found.') from None
    if not got:
        raise HTTPException(404, 'Picture not found.')
    age = max(60, min(DAY, int(exp - t)))
    kind = 'image/webp' if got[:4] == b'RIFF' else 'image/png'
    return Response(got, media_type=kind, headers={'Cache-Control': f'public, max-age={age}, s-maxage={age}, immutable',
                                                         'Access-Control-Allow-Origin': '*', 'Cross-Origin-Resource-Policy': 'cross-origin'})


# ------------------------------------------------------------------ door C

def paper_id(user_id, key):
    return str(uuid.uuid5(uuid.NAMESPACE_URL, f'jeelive-choice:{user_id}:{key}'))


def ordered(items):
    rank = {s: i for i, s in enumerate(SUBJECTS)}
    return sorted(items, key=lambda x: (rank[x['subject']], 0 if x['type'] == 'mcq' else 1, x['order'], x['number'], x['token']))


def draw(live, counts, cap):
    """Random questions of each subject across all its chapters, about 4 MCQ to 1 numerical (JEE Main: 20 + 5)."""
    rng, out = random.SystemRandom(), []
    for subject, n in counts.items():
        mcq, num = list(live['bank'][subject]['mcq']), list(live['bank'][subject]['integer'])
        have = len(mcq) + len(num)
        if n > have or (cap and n > cap):
            raise HTTPException(422, FEW.format(s=SHORT[subject], n=min(have, cap or have)))
        want_num = min(len(num), round(n / 5))
        want_mcq = min(len(mcq), n - want_num)
        want_num = n - want_mcq
        out += [live['questions'][t] for t in rng.sample(mcq, want_mcq) + rng.sample(num, want_num)]
    return out


async def reserve(user_id, day, key, limit):
    """One of today's papers for this student, counted once per request_key. False when today's papers are used up."""
    _id = f'{user_id}:{day}'
    try:
        done = await days.update_one({'_id': _id, 'keys': {'$ne': key}, 'count': {'$lt': limit}},
                                     {'$inc': {'count': 1}, '$push': {'keys': key}, '$setOnInsert': {'user_id': user_id, 'day': day}}, upsert=True)
        return bool(done.matched_count or done.upserted_id)
    except DuplicateKeyError:
        doc = await days.find_one({'_id': _id}, {'keys': 1})
        return bool(doc and key in doc.get('keys', []))


async def made_today(user_id, t=None):
    doc = await days.find_one({'_id': f'{user_id}:{ist_day(t or await database_now())}'}, {'count': 1})
    return int((doc or {}).get('count', 0))


@router.post('/choice/papers')
async def make_paper(data: ChoicePaperPayload, u=Depends(current)):
    if data.exam not in EXAMS:
        raise HTTPException(422, NO_EXAM)
    if not KEY.fullmatch(data.request_key):
        raise HTTPException(422, BAD_KEY)
    pid = paper_id(u['id'], data.request_key)
    found = await papers.find_one({'id': pid, 'user_id': u['id']}, {'_id': 0, 'id': 1})
    if found:
        return {'set_id': found['id']}
    s = await settings_of(data.exam)
    if data.mode not in ('pick', 'random') or not s[data.mode]:
        raise HTTPException(409, CLOSED)
    top, cap, per = min(TOP, int(s['max_questions'])), s['max_per_subject'], s['minutes']
    live = await pool()
    if data.mode == 'pick':
        ids = data.question_ids or []
        if not ids:
            raise HTTPException(422, NONE_PICKED)
        if len(ids) > top:
            raise HTTPException(422, TOO_MANY.format(n=top))
        if len(set(ids)) != len(ids) or any(i not in live['questions'] for i in ids):
            raise HTTPException(422, GONE)
        items = [live['questions'][i] for i in ids]
        if cap:
            for subject in SUBJECTS:
                if sum(x['subject'] == subject for x in items) > cap:
                    raise HTTPException(422, PER_SUBJECT.format(s=SHORT[subject], n=cap))
    else:
        n = data.count
        if not isinstance(n, int) or isinstance(n, bool) or not 3 <= n <= top:
            raise HTTPException(422, RANGE.format(n=top))
        present = [x for x in SUBJECTS if live['bank'][x]['mcq'] or live['bank'][x]['integer']]
        if not present:
            raise HTTPException(422, GONE)
        if n < len(present):
            raise HTTPException(422, RANGE.format(n=top))
        items = draw(live, split_of(n, present), cap)
    items = ordered(items)
    counts = {x: sum(i['subject'] == x for i in items) for x in SUBJECTS}
    t = await database_now()
    if not await reserve(u['id'], ist_day(t), data.request_key, int(s['daily_limit'])):
        raise HTTPException(429, DAILY.format(n=int(s['daily_limit'])))
    from .content import valid_rules
    count = len(items)
    rules = valid_rules({'minutes': minutes_for(counts, per), 'correct': 4, 'wrong': -1, 'skipped': 0})
    d = datetime.fromtimestamp(t, IST)
    doc = {'_id': pid, 'id': pid, 'user_id': u['id'], 'exam': EXAMS[data.exam], 'exam_slug': data.exam, 'mode': data.mode,
           'request_key': data.request_key, 'title': f'Student Choice · {count} Q · {d.day} {d:%b}', 'rules': rules, 'count': count,
           'maximum': count * 4, 'counts': counts, 'types': {k: sum(i['type'] == k for i in items) for k in ('mcq', 'integer')},
           'items': [{k: i[k] for k in ('token', 'set_id', 'question_id', 'subject', 'type')} for i in items],
           'test_kind': 'choice', 'version': 1, 'revision': 1, 'day': ist_day(t), 'created_at': t}
    try:
        await papers.insert_one(doc)
    except DuplicateKeyError:
        pass
    return {'set_id': pid}


# ------------------------------------------------------------------ the made paper, as attempts.py reads it

async def own_paper(id, u, projection=None):
    if not isinstance(id, str) or not ID.fullmatch(id):
        return None
    return await papers.find_one({'id': id, 'user_id': u['id']}, projection or {'_id': 0, 'items': 0, 'questions': 0})


def header_of(p):
    return {'id': p['id'], 'title': p['title'], 'exam': p['exam'], 'status': 'published', 'audience': 'all', 'rules': p['rules'],
            'version': p.get('version', 1), 'revision': p.get('revision', 1), 'test_kind': 'choice', 'year': '',
            'rights_report': bool(p.get('rights_report')), 'attribution': '', 'source': 'Student Choice: your own paper of JEE Main chapter-wise questions.',
            'created_at': p['created_at']}


async def paper_page(id, u):
    """GET /api/my/sets/{id} for a made paper: its owner only; anyone else gets the usual 'not available'."""
    p = await own_paper(id, u)
    if not p:
        raise HTTPException(404, 'This set is not available to your account.')
    blank = dict.fromkeys(('full_length', 'mock_number', 'series_id', 'series_date', 'series_window', 'pyq_year', 'chapter_book_id',
                           'chapter_number', 'chapter_subject', 'solution_kind', 'start_at', 'end_at', 'live_enabled', 'catalog_section_id'))
    return {**blank, 'id': p['id'], 'exam': p['exam'], 'year': '', 'status': 'published', 'rules': p['rules'], 'version': p.get('version', 1),
            'attribution': '', 'created_at': p['created_at'], 'test_kind': 'choice', 'title': p['title'], 'source': 'JEE Main · Student Choice',
            'count': p['count'], 'approved_count': p['count'], 'subjects': [x for x in SUBJECTS if p['counts'].get(x)], 'types': p['types'],
            'maximum': p['maximum'], 'catalog_path': None, 'choice': {'mode': p['mode'], 'counts': p['counts']}}


async def build_questions(p):
    """The paper's questions, copied from its chapter tests: each keeps its subject, pieces, key and solution."""
    live = await pool()
    wanted = {i['set_id'] for i in p['items']}
    if any(sid not in live['chapters'] for sid in wanted):
        raise HTTPException(409, STALE)
    docs = {s['id']: s async for s in sets.find({'id': {'$in': list(wanted)}, 'status': 'published'},
                                                 {'_id': 0, 'id': 1, 'version': 1, 'rights_report': 1, 'questions': 1})}
    out, rights = [], True
    for n, it in enumerate(p['items'], 1):
        s = docs.get(it['set_id'])
        q = next((x for x in (s or {}).get('questions', []) if x.get('id') == it['question_id']), None)
        if not q or not choosable(q):
            raise HTTPException(409, STALE)
        rights = rights and bool(s.get('rights_report'))
        c = copy.deepcopy(q)
        for k in ('ai_solution', 'scoring', 'bonus'):
            c.pop(k, None)
        c.update(id=it['token'], number=n, subject=it['subject'], section=it['subject'],
                 topic=q.get('topic') or live['chapters'][it['set_id']]['title'], disposition='standard',
                 source_set_id=s['id'], source_question_id=q['id'], source_number=q.get('number'), source_version=s.get('version', 1),
                 source_section=q.get('section'))
        out.append(c)
    return out, rights


async def frozen(p):
    """The paper as papers.Paper: frozen on its first Start (a chapter edit later never changes a started paper)."""
    from .papers import Paper, unique_refs
    hit = _frozen.get(p['id'])
    if hit is not None:
        _frozen.move_to_end(p['id'])
        return hit
    doc = await papers.find_one({'id': p['id']}, {'_id': 0, 'questions': 1})
    questions = (doc or {}).get('questions')
    if not questions:
        built, rights = await build_questions(await papers.find_one({'id': p['id']}, {'_id': 0}))
        done = await papers.update_one({'id': p['id'], 'questions': {'$exists': False}},
                                       {'$set': {'questions': built, 'rights_report': rights, 'frozen_at': now()}})
        questions = built if done.modified_count else (await papers.find_one({'id': p['id']}, {'_id': 0, 'questions': 1}))['questions']
    entry = Paper(questions, unique_refs(questions))
    _frozen[p['id']] = entry
    while len(_frozen) > 64:
        _frozen.popitem(last=False)
    return entry


async def start_parts(id, u):
    """(header with _database_now, Paper) for POST /api/sets/{id}/start, or (None, None) when this student has no such paper."""
    if not isinstance(id, str) or not ID.fullmatch(id):
        return None, None
    p = await clocked_one(papers, {'id': id, 'user_id': u['id']}, {'_id': 0, 'items': 0, 'questions': 0})
    if not p:
        return None, None
    t = p.pop('_database_now')
    entry = await frozen(p)
    p = await papers.find_one({'id': id}, {'_id': 0, 'items': 0, 'questions': 0})
    return {**header_of(p), '_database_now': t}, entry


async def preflight_paper(id, u, data):
    p = await own_paper(id, u)
    if not p:
        raise HTTPException(404, 'This set is not available.')
    t = await database_now()
    if not (await papers.find_one({'id': id}, {'_id': 0, 'frozen_at': 1}) or {}).get('frozen_at'):
        live = await pool()
        items = (await papers.find_one({'id': id}, {'_id': 0, 'items': 1}))['items']
        if any(i['token'] not in live['questions'] for i in items):
            raise HTTPException(409, STALE)
    await db.tejas_preflight.update_one({'user_id': u['id'], 'set_id': id},
                                        {'$set': {'revision': p.get('revision', 1), 'at': t, 'test_response': str(data.get('test_response', ''))[:30]}}, upsert=True)
    return {'ok': True, 'message': 'Connection checked. No attempt or timer has started.', 'server_now': t}


def source_of(q):
    """Where a made paper's question came from: (set id, question id, number, version), or None for any other paper."""
    if q.get('source_set_id') and q.get('source_question_id'):
        return q['source_set_id'], q['source_question_id'], q.get('source_number'), q.get('source_version', 1)
    return None


async def ai_tags(a):
    """{question id in the paper: (tag, fingerprint-ready copy)} from the chapter tests the questions came from."""
    by_set = {}
    for q in a['questions']:
        src = source_of(q)
        if src:
            by_set.setdefault(src[0], []).append((q, src[1]))
    out = {}
    for sid, rows in by_set.items():
        doc = await sets.find_one({'id': sid}, {'_id': 0, 'questions.id': 1, 'questions.ai_solution': 1}) or {'questions': []}
        tags = {x['id']: x.get('ai_solution') for x in doc['questions']}
        for q, qid in rows:
            out[q['id']] = (tags.get(qid), {**q, 'id': qid})
    return out


# ------------------------------------------------------------------ the website's own page data

@router.get('/choice/home')
async def home(u=Depends(current)):
    """Everything the website's Student Choice screens need in one read: the open ways, the chapters, today's count and
    the student's own state of each chapter test (for the random-only step 2)."""
    from .db import attempts
    s = await settings_of('jee-main')
    live = await pool()
    t = await database_now()
    ids = list(live['chapters'])
    latest = {}
    if ids:
        async for r in attempts.aggregate([
                {'$match': {'user_id': u['id'], 'set_id': {'$in': ids}, 'mode': 'practice'}},
                {'$sort': {'set_id': 1, 'started_at': -1, 'id': -1}},
                {'$group': {'_id': '$set_id', 'id': {'$first': '$id'}, 'status': {'$first': '$status'}, 'deadline': {'$first': '$deadline'}}}]):
            done = r['status'] != 'active' or (r.get('deadline') and r['deadline'] <= t)
            latest[r['_id']] = {'id': r['id'], 'status': 'completed' if done else 'active', 'resumable': not done, 'result_available': bool(done)}
    rules = {}
    if ids:
        async for x in sets.find({'id': {'$in': ids}}, {'_id': 0, 'id': 1, 'rules.minutes': 1, 'rules.correct': 1, 'rules.wrong': 1}):
            rules[x['id']] = x.get('rules') or {}
    subjects = [{'name': name, 'chapters': [{**{k: live['chapters'][cid][k] for k in ('id', 'number', 'title', 'count', 'mcq', 'integer')},
                                             'test': {'minutes': rules.get(cid, {}).get('minutes'), 'correct': rules.get(cid, {}).get('correct'),
                                                      'wrong': rules.get(cid, {}).get('wrong')},
                                             'attempt': latest.get(cid)} for cid in live['by_subject'][name]]} for name in SUBJECTS]
    return {'pick': bool(s['pick']), 'random': bool(s['random']), 'max_questions': int(s['max_questions']), 'max_per_subject': s['max_per_subject'],
            'minutes_per_question': dict(s['minutes']), 'daily_limit': int(s['daily_limit']), 'made_today': await made_today(u['id'], t),
            'chapters': sum(len(x['chapters']) for x in subjects), 'questions': sum(c['count'] for x in subjects for c in x['chapters']),
            'subjects': subjects, 'server_now': t}


# ------------------------------------------------------------------ Super Admin › JEE Main › Student Choice

async def stats(exam):
    t = await database_now()
    today = ist_day(t)
    base = {'exam_slug': exam}
    by_mode = {r['_id']: r['n'] async for r in papers.aggregate([{'$match': base}, {'$group': {'_id': '$mode', 'n': {'$sum': 1}}}])}
    creators = await papers.aggregate([{'$match': base}, {'$group': {'_id': '$user_id'}}, {'$count': 'n'}]).to_list(1)
    creators_today = await papers.aggregate([{'$match': {**base, 'day': today}}, {'$group': {'_id': '$user_id'}}, {'$count': 'n'}]).to_list(1)
    return {'today': await papers.count_documents({**base, 'day': today}), 'total': sum(by_mode.values()), 'pick': by_mode.get('pick', 0),
            'random': by_mode.get('random', 0), 'creators': (creators or [{}])[0].get('n', 0),
            'creators_today': (creators_today or [{}])[0].get('n', 0), 'started': await papers.count_documents({**base, 'frozen_at': {'$exists': True}}),
            'day': today}


@router.get('/admin/choice/{exam}')
async def owner_view(exam: str, u=Depends(owner)):
    if exam not in EXAMS:
        raise HTTPException(404, NO_EXAM)
    _pool.update(at=-1e9)
    live = await pool()
    return {'exam': EXAMS[exam], 'settings': await settings_of(exam) if exam in _settings else view_settings(await settings_coll.find_one({'_id': exam}, {'_id': 0}) or {}),
            'pool': [{'name': name, 'chapters': [{k: live['chapters'][c][k] for k in ('id', 'number', 'title', 'count', 'mcq', 'integer')}
                                                 for c in live['by_subject'][name]]} for name in SUBJECTS],
            'stats': await stats(exam)}


@router.put('/admin/choice/{exam}')
async def owner_save(exam: str, data: ChoiceSettingsPayload, u=Depends(owner)):
    if exam not in EXAMS:
        raise HTTPException(404, NO_EXAM)
    for s in SUBJECTS:
        if not 0.5 <= getattr(data.minutes_per_question, s) <= 10:
            raise HTTPException(422, 'Minutes per question must be between 0.5 and 10.')
    if not 1 <= data.max_questions <= TOP:
        raise HTTPException(422, f'The most questions in one paper must be from 1 to {TOP}.')
    if data.max_per_subject is not None and not 1 <= data.max_per_subject <= TOP:
        raise HTTPException(422, f'The top per subject must be from 1 to {TOP}, or empty.')
    if not 1 <= data.daily_limit <= 50:
        raise HTTPException(422, 'Papers a student may make in a day must be from 1 to 50.')
    value = {'pick': data.pick, 'random': data.random, 'max_questions': data.max_questions, 'max_per_subject': data.max_per_subject,
             'minutes': {s: round(float(getattr(data.minutes_per_question, s)), 2) for s in SUBJECTS}, 'daily_limit': data.daily_limit}
    t = now()
    try:
        done = await settings_coll.update_one({'_id': exam, 'revision': data.expected_revision} if data.expected_revision else
                                              {'_id': exam, 'revision': {'$in': [None, 0]}},
                                              {'$set': {**value, 'updated_by': u['id'], 'updated_at': t}, '$inc': {'revision': 1}},
                                              upsert=not data.expected_revision)
    except DuplicateKeyError:
        done = None
    if not done or not (done.matched_count or done.upserted_id):
        raise HTTPException(409, 'These settings changed a moment ago. Reload and save again.')
    _settings.pop(exam, None)
    await audit(u['id'], 'Student Choice settings saved', exam,
                ', '.join(f'{k}={v}' for k, v in value.items())[:900])
    return {'message': 'Saved. The website follows at once; the app within 2 to 4 minutes.', 'settings': await settings_of(exam)}
