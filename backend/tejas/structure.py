"""Owner-managed exam → section → test placement. Students only reach shown exams and live tests."""
import hashlib, re, secrets, time, uuid
from typing import Annotated, Literal
from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Path, Query
from pydantic import BaseModel, ConfigDict, Field
from pymongo import UpdateOne
from .auth import current, owner, staff
from .db import db, sets, now, audit, SafeIndexes
from .canonical import database_now


class Payload(BaseModel):
    model_config = ConfigDict(extra='forbid', strict=True, allow_inf_nan=False)


router = APIRouter(prefix='/api', tags=['Exam structure'])
exams = db.tejas_catalog_exams
sections = db.tejas_catalog_sections
previews = db.tejas_section_previews
PREVIEW_DAYS = 7

CHAPTER_FILTER = {'$or': [
    {'chapter_book_id': {'$exists': True, '$nin': [None, '']}},
    {'test_kind': 'chapter'},
]}
MOCK_FILTER = {'$and': [
    {'$or': [{'chapter_book_id': {'$exists': False}}, {'chapter_book_id': None}, {'chapter_book_id': ''}]},
    {'$or': [{'test_kind': 'mock'}, {'full_length': True}]},
    {'test_kind': {'$nin': ['chapter', 'pyq']}},
]}
UNPLACED = {'$or': [{'catalog_section_id': {'$exists': False}}, {'catalog_section_id': {'$in': [None, '']}}]}
LEGACY = {'pyq': {'test_kind': 'pyq'}, 'chapters': CHAPTER_FILTER, 'mocks': MOCK_FILTER}
LIVE_FLAG = {'$or': [{'live_enabled': {'$ne': False}}, {'test_kind': 'pyq'}]}
ADMIN_BASE = {'qa_only': {'$ne': True}, 'status': {'$ne': 'withdrawn'}, 'is_deleted': {'$ne': True}, 'archived': {'$ne': True},
              'series_id': {'$exists': False}, 'series_import': {'$ne': True}}
SERIES_SECTION = 'jee-main:aits'
SINGLE_KINDS = ('pyq', 'mocks', 'chapters', 'aits')
EXAM_RULES = {'JEE Main': (180, 4, -1), 'BITSAT': (180, 3, -1), 'COMEDK': (180, 1, 0)}
ORDER = [('catalog_order', 1), ('chapter_subject', 1), ('chapter_number', 1), ('mock_number', 1), ('created_at', -1), ('id', 1)]
BUILTIN = (
    ('jee-main', 'JEE Main', 'JEE', ['Physics', 'Chemistry', 'Mathematics'], ('pyq', 'mocks', 'chapters')),
    ('bitsat', 'BITSAT', 'BITS', ['Physics', 'Chemistry', 'Mathematics', 'English', 'Logical reasoning'], ('mocks', 'chapters')),
    ('comedk', 'COMEDK', 'COMEDK', ['Physics', 'Chemistry', 'Mathematics'], ('mocks', 'chapters')),
)
RULE_EXAMS = ('JEE Main', 'BITSAT', 'COMEDK')
SECTION_DEFAULTS = {
    'pyq': ('PYQ Papers', 'Choose an exam date and shift. Start a full paper or revisit your results.', 'list'),
    'mocks': ('Mock Tests', 'Live, full-length papers. Practice the complete test in one sitting.', 'list'),
    'chapters': ('Chapter-wise Tests', 'Choose a subject, pick a chapter and build understanding.', 'chapters'),
    'aits': ('All India Test Series', 'One paper a day with an all-India rank.', 'list'),
}
Color = Literal['teal', 'amber', 'violet', 'rose', 'lime', 'sky']
Name = Annotated[str, Field(min_length=2, max_length=60)]
Subject = Annotated[str, Field(min_length=1, max_length=40)]
Identity = Annotated[str, Field(min_length=1, max_length=100)]
_seen = {'at': -1e9, 'keys': frozenset(), 'sections': frozenset(), 'exam_by_key': {}, 'section_names': {}}


class ExamInput(Payload):
    name: Name
    short: str = Field(min_length=1, max_length=16)
    subjects: list[Subject] = Field(min_length=1, max_length=12)
    color: Color


class ExamPatch(Payload):
    name: Name | None = None
    short: str | None = Field(default=None, min_length=1, max_length=16)
    subjects: list[Subject] | None = Field(default=None, min_length=1, max_length=12)
    color: Color | None = None
    shown: bool | None = None


Clock = Annotated[str, Field(pattern=r'^([01]\d|2[0-3]):[0-5]\d$')]


class SectionInput(Payload):
    name: Name
    description: str = Field(default='', max_length=160)
    layout: Literal['list', 'chapters']
    kind: Literal['pyq', 'mocks', 'chapters', 'aits', 'custom'] = 'custom'
    minutes: int | None = Field(default=None, gt=0, le=1440)
    correct: float | None = Field(default=None, gt=0, le=100)
    wrong: float | None = Field(default=None, ge=-100, le=0)
    first_date: str | None = Field(default=None, pattern=r'^\d{4}-\d{2}-\d{2}$')
    days: int | None = Field(default=None, ge=1, le=366)
    open_time: Clock | None = None
    last_start: Clock | None = None


class SectionPatch(Payload):
    name: Name | None = None
    description: str | None = Field(default=None, max_length=160)
    hidden: bool | None = None
    minutes: int | None = Field(default=None, gt=0, le=1440)
    correct: float | None = Field(default=None, gt=0, le=100)
    wrong: float | None = Field(default=None, ge=-100, le=0)


class OrderInput(Payload):
    ids: list[Identity] = Field(min_length=1, max_length=1000)


class TestPatch(Payload):
    title: str | None = Field(default=None, min_length=2, max_length=160)
    live: bool | None = None
    section_id: Identity | None = None


class PublishItem(Payload):
    kind: Literal['book', 'book_mock', 'chapter_book']
    id: Identity


class PublishInput(Payload):
    items: list[PublishItem] = Field(default_factory=list, max_length=500)
    section_id: str = Field(default='', max_length=100)
    release_at: float | None = Field(default=None, gt=0)


def slugify(text):
    return re.sub(r'[^a-z0-9]+', '-', text.lower()).strip('-')[:40]


def legacy_kind(s):
    if s.get('test_kind') == 'pyq':
        return 'pyq'
    if s.get('chapter_book_id') or s.get('test_kind') == 'chapter':
        return 'chapters'
    if s.get('test_kind') == 'mock' or s.get('full_length') is True:
        return 'mocks'
    return None


def rule_exam(dest):
    return dest['exam_key'] if dest['exam_key'] in RULE_EXAMS else 'Custom'


def exam_view(e):
    return {k: e.get(k) for k in ('slug', 'key', 'name', 'short', 'subjects', 'color', 'builtin', 'shown', 'order')}


def section_view(s):
    return {k: s.get(k) for k in ('id', 'exam_slug', 'slug', 'name', 'description', 'layout', 'kind', 'builtin', 'hidden', 'order', 'defaults', 'series_id')}


def default_rules(exam_key, kind):
    minutes, correct, wrong = EXAM_RULES.get(exam_key, (180, 4, -1))
    return {'minutes': 60 if kind == 'chapters' else minutes, 'correct': correct, 'wrong': wrong}


async def seed():
    await SafeIndexes(sections).create_index([('exam_slug', 1), ('slug', 1)], unique=True)
    await SafeIndexes(sets).create_index('catalog_section_id', sparse=True)
    await SafeIndexes(previews).create_index([('section_id', 1), ('created_at', -1)])
    for order, (slug, key, short, subjects, kinds) in enumerate(BUILTIN, 1):
        await exams.update_one({'_id': slug}, {'$setOnInsert': {'slug': slug, 'key': key, 'name': key, 'short': short,
            'subjects': subjects, 'color': slug, 'builtin': True, 'shown': True, 'order': order, 'created_at': now()}}, upsert=True)
        for position, kind in enumerate(kinds, 1):
            name, description, layout = SECTION_DEFAULTS[kind]
            sid = f'{slug}:{kind}'
            await sections.update_one({'_id': sid}, {'$setOnInsert': {'id': sid, 'exam_slug': slug, 'slug': kind, 'kind': kind,
                'name': name, 'description': description, 'layout': layout, 'builtin': True, 'hidden': False,
                'order': position, 'created_at': now()}}, upsert=True)
    from .series_admin import seed_jee
    await seed_jee()
    for e in await exams.find({'key': {'$in': list(EXAM_RULES)}}, {'_id': 0, 'slug': 1, 'key': 1}).to_list(10):
        async for s in sections.find({'exam_slug': e['slug'], 'defaults': {'$exists': False}}, {'_id': 1, 'kind': 1}):
            await sections.update_one({'_id': s['_id'], 'defaults': {'$exists': False}}, {'$set': {'defaults': default_rules(e['key'], s['kind'])}})
    await visibility(force=True)


async def visibility(force=False):
    if force or time.monotonic() - _seen['at'] > 5:
        hidden = await exams.find({'shown': False}, {'_id': 0, 'slug': 1, 'key': 1}).to_list(500)
        ids = await sections.distinct('id', {'exam_slug': {'$in': [e['slug'] for e in hidden]}}) if hidden else []
        names = {e['key']: (e['slug'], e.get('name') or e['key']) for e in await exams.find({}, {'_id': 0, 'slug': 1, 'key': 1, 'name': 1}).to_list(500)}
        places = {s['id']: s['name'] for s in await sections.find({}, {'_id': 0, 'id': 1, 'name': 1}).to_list(2000)}
        _seen.update(at=time.monotonic(), keys=frozenset(e['key'] for e in hidden), sections=frozenset(ids), exam_by_key=names, section_names=places)
    return _seen


def place_line(s):
    """What students read under a test's name: where it sits, e.g. 'BITSAT · Chapter-wise Tests · Physics'. Never a file name."""
    slug, name = _seen['exam_by_key'].get(s.get('exam'), ('', s.get('exam') or ''))
    sid = s.get('catalog_section_id') or (f'{slug}:{legacy_kind(s)}' if slug and legacy_kind(s) else '')
    if not sid and s.get('series_id') and slug:
        sid = f'{slug}:aits'
    parts = [name, _seen['section_names'].get(sid)]
    if legacy_kind(s) == 'chapters':
        parts.append(s.get('chapter_subject'))
    elif s.get('test_kind') == 'pyq':
        parts.append(str(s.get('pyq_year') or s.get('year') or '') or None)
    return ' · '.join(p for p in parts if p)


def hidden_clause(user):
    if (user or {}).get('role') == 'owner' or not _seen['keys']:
        return None
    return {'exam': {'$nin': sorted(_seen['keys'])}, 'catalog_section_id': {'$nin': sorted(_seen['sections'])}}


async def hidden_from(s, user):
    if (user or {}).get('role') == 'owner':
        return False
    seen = await visibility()
    return s.get('exam') in seen['keys'] or s.get('catalog_section_id') in seen['sections']


async def exam_doc(slug, user=None):
    e = await exams.find_one({'_id': slug}, {'_id': 0})
    if not e or (not e['shown'] and (user or {}).get('role') != 'owner'):
        raise HTTPException(404, 'This exam is not available.')
    return e


async def exam_sections(slug, include_hidden=False):
    q = {'exam_slug': slug} if include_hidden else {'exam_slug': slug, 'hidden': False}
    return await sections.find(q, {'_id': 0}).sort([('order', 1), ('created_at', 1)]).to_list(200)


async def section_doc(sid):
    s = await sections.find_one({'_id': sid}, {'_id': 0})
    if not s:
        raise HTTPException(404, 'Section not found.')
    return s


async def section_by_slug(exam_slug, slug, user):
    s = await sections.find_one({'exam_slug': exam_slug, 'slug': slug}, {'_id': 0})
    if not s or (s['hidden'] and (user or {}).get('role') != 'owner'):
        raise HTTPException(404, 'This section is not available.')
    return s


def placement(section, exam_key):
    own = {'catalog_section_id': section['id']}
    legacy = LEGACY.get(section['kind']) if section.get('builtin') else None
    return {'$or': [own, {'$and': [UNPLACED, {'exam': exam_key}, legacy]}]} if legacy else own


def live_query(user, exam, section, search=''):
    from .catalog import available
    q = available(user, '', search)
    q['qa_only'] = {'$ne': True}
    q['$and'].extend([placement(section, exam['key']), LIVE_FLAG])
    return q


async def destination(section_id, layouts=('list', 'chapters'), replace=None, year=None):
    s = await sections.find_one({'_id': section_id}, {'_id': 0}) if section_id else None
    if not s:
        raise HTTPException(422, 'Choose the exam and mock type this upload belongs to.')
    if s['layout'] not in layouts:
        raise HTTPException(422, 'This file does not fit that mock type.')
    e = await exams.find_one({'_id': s['exam_slug']}, {'_id': 0})
    dest = {'section_id': s['id'], 'section_name': s['name'], 'section_slug': s['slug'], 'layout': s['layout'],
            'exam_slug': e['slug'], 'exam_key': e['key'], 'exam_name': e['name'],
            'defaults': s.get('defaults') or default_rules(e['key'], s['kind'])}
    if s['kind'] == 'aits':
        if replace:
            raise HTTPException(422, 'Change All India papers from their days instead.')
        return {**dest, 'series': True, 'series_id': s.get('series_id')}
    if s['kind'] == 'pyq':
        if not year:
            raise HTTPException(422, 'Enter the year of this PYQ paper.')
        dest.update(pyq=True, year=int(year))
    if replace:
        present = [x['id'] for x in await section_tests(s, e['key']) if not locked(x)]
        ids = present if list(replace) == ['all'] else list(dict.fromkeys(replace))
        if not ids:
            raise HTTPException(409, 'There is nothing in this section to replace.')
        if set(ids) - set(present):
            raise HTTPException(409, 'Some tests to replace are no longer in this section. Reload and choose again.')
        orders = [r['catalog_order'] for r in await sets.find({'id': {'$in': ids}}, {'_id': 0, 'catalog_order': 1}).to_list(len(ids))
                  if isinstance(r.get('catalog_order'), (int, float))]
        dest.update(replaces=ids, replace_order=int(min(orders)) if orders else None)
    return dest


async def mark_replacing(dest, title):
    if dest and dest.get('replaces'):
        await sets.update_many({'id': {'$in': dest['replaces']}, 'archived': {'$ne': True}}, {'$set': {'replace_pending': title[:160]}})


async def apply_replacement(dest, actor, title):
    """Old tests leave for the Library only once their replacement is published."""
    if dest and dest.get('replaces'):
        from .library import archive_sets
        await archive_sets(dest['replaces'], actor, f'Replaced by {title}'[:300])


async def next_order(section_id):
    s = await section_doc(section_id)
    e = await exams.find_one({'_id': s['exam_slug']}, {'_id': 0, 'key': 1})
    row = await sets.find_one({'$and': [placement(s, e['key']), {'catalog_order': {'$type': 'number'}}]},
                              {'_id': 0, 'catalog_order': 1}, sort=[('catalog_order', -1)])
    return int((row or {}).get('catalog_order', 0)) + 1


async def path_for(s):
    sid = s.get('catalog_section_id')
    if not sid:
        e = await exams.find_one({'key': s.get('exam')}, {'_id': 0, 'slug': 1})
        kind = legacy_kind(s)
        sid = f"{e['slug']}:{kind}" if e and kind else None
    found = await sections.find_one({'_id': sid}, {'_id': 0, 'exam_slug': 1, 'slug': 1}) if sid else None
    return f"/exams/{found['exam_slug']}/{found['slug']}" if found else None


def test_state(s, t):
    from .content import permitted
    if s.get('status') == 'draft':
        return 'draft'
    if s.get('owner_unlive'):
        return 'unlive'
    if s.get('end_at') is not None and s['end_at'] <= t:
        return 'ended'
    if s.get('start_at') is not None and s['start_at'] > t:
        return 'scheduled'
    if s.get('status') == 'published' and (s.get('live_enabled') is not False or s.get('test_kind') == 'pyq') and permitted({**s, 'audience': 'all'}, at=t):
        return 'live'
    return 'paused'


def source_of(s):
    for key, label in (('book_import_id', 'book'), ('mock_book_id', 'mock_book'), ('import_id', 'import'), ('chapter_book_id', 'chapter_book')):
        if s.get(key):
            return label
    return 'pyq' if s.get('test_kind') == 'pyq' else 'manual'


FLAGS = {'$size': {'$filter': {'input': {'$ifNull': ['$questions', []]}, 'cond': {'$ne': [{'$ifNull': ['$$this.flag', '']}, '']}}}}
FIELDS = {'_id': 0, 'id': 1, 'title': 1, 'display_title': 1, 'exam': 1, 'status': 1, 'test_kind': 1, 'full_length': 1,
          'written': 1, 'master_pyq': 1, 'competition': 1, 'last_start_at': 1, 'pyq_year': 1, 'flags': FLAGS,
          'chapter_book_id': 1, 'chapter_subject': 1, 'chapter_number': 1, 'mock_number': 1, 'catalog_section_id': 1,
          'catalog_order': 1, 'live_enabled': 1, 'owner_unlive': 1, 'start_at': 1, 'end_at': 1, 'expires': 1, 'audience': 1,
          'import_id': 1, 'book_import_id': 1, 'mock_book_id': 1, 'series_import': 1, 'series_date': 1, 'rules.minutes': 1,
          'pyq_date': 1, 'replace_pending': 1, 'count': {'$size': {'$ifNull': ['$questions', []]}}}


def test_view(s, t):
    return {'id': s['id'], 'title': s.get('display_title') or s['title'], 'original_title': s['title'], 'exam': s.get('exam'),
            'state': test_state(s, t), 'source': source_of(s), 'count': s.get('count', 0), 'minutes': (s.get('rules') or {}).get('minutes'),
            'subject': s.get('chapter_subject'), 'chapter_number': s.get('chapter_number'), 'mock_number': s.get('mock_number'),
            'catalog_order': s.get('catalog_order'), 'start_at': s.get('start_at'), 'end_at': s.get('end_at'), 'pyq_date': s.get('pyq_date'),
            'book_import_id': s.get('book_import_id'), 'import_id': s.get('import_id'), 'chapter_book_id': s.get('chapter_book_id'),
            'test_kind': s.get('test_kind'), 'replace_pending': s.get('replace_pending'), 'written': bool(s.get('written')),
            'locked': locked(s), 'flags': s.get('flags', 0), 'live_exam': bool(s.get('competition')), 'year': s.get('pyq_year')}


def locked(s):
    """The verified PYQ papers: only Live or Off, never edited, replaced or moved to the Library."""
    return s.get('test_kind') == 'pyq' and not s.get('master_pyq')


async def section_tests(section, exam_key):
    return await sets.find({'$and': [ADMIN_BASE, placement(section, exam_key)]}, FIELDS).sort(ORDER).limit(1000).to_list(1000)


# Student structure

@router.get('/catalog/exams')
async def student_exams(u=Depends(current)):
    await visibility()
    q = {} if u.get('role') == 'owner' else {'shown': True}
    rows = await exams.find(q, {'_id': 0}).sort([('order', 1), ('created_at', 1)]).to_list(200)
    return {'items': [exam_view(e) for e in rows]}


@router.get('/catalog/exams/{slug}')
async def student_exam(slug: str, u=Depends(current)):
    await visibility()
    e = await exam_doc(slug, u)
    from .series_admin import visible_series
    from .live_series import SERIES_ID
    open_series = {c['section_id']: c['id'] for c in await visible_series()}
    found = []
    for s in await exam_sections(slug):
        if s['kind'] == 'aits':
            # A test series opens inside its own exam; only JEE Main also has the Home banner.
            if s['id'] in open_series:
                sid = open_series[s['id']]
                found.append({**section_view(s), 'live_count': 0, 'series_path': '/series/all-india-jee' if sid == SERIES_ID else '/series/' + sid})
            continue
        count = await sets.count_documents(live_query(u, e, s))
        if count:
            found.append({**section_view(s), 'live_count': count})
    return {**exam_view(e), 'sections': found}


# Owner administration

async def admin_exams():
    return await exams.find({}, {'_id': 0}).sort([('order', 1), ('created_at', 1)]).to_list(200)


@router.get('/admin/catalog')
async def admin_catalog(u=Depends(owner)):
    t = await database_now()
    rows = await admin_exams()
    slug_by_key = {e['key']: e['slug'] for e in rows}
    all_sections = await sections.find({}, {'_id': 0}).sort([('order', 1), ('created_at', 1)]).to_list(2000)
    known = {s['id'] for s in all_sections}
    tally = {}
    async for s in sets.find(ADMIN_BASE, {k: v for k, v in FIELDS.items() if k not in ('count', 'flags')}).limit(50000):
        sid = s.get('catalog_section_id')
        if not sid:
            kind, slug = legacy_kind(s), slug_by_key.get(s.get('exam'))
            sid = f'{slug}:{kind}' if kind and slug else None
        bucket = tally.setdefault(sid if sid in known else ('unplaced', slug_by_key.get(s.get('exam'))), {'total': 0, 'live': 0, 'draft': 0})
        state = test_state(s, t)
        bucket['total'] += 1
        bucket['live'] += state == 'live'
        bucket['draft'] += state == 'draft'
    empty = {'total': 0, 'live': 0, 'draft': 0}
    return {'items': [{**exam_view(e), 'unplaced': tally.get(('unplaced', e['slug']), empty)['total'],
                       'sections': [{**section_view(s), 'counts': tally.get(s['id'], empty)} for s in all_sections if s['exam_slug'] == e['slug']]}
                      for e in rows], 'colors': list(Color.__args__)}


@router.post('/admin/catalog/exams')
async def create_exam(body: ExamInput, u=Depends(owner)):
    name = ' '.join(body.name.split())
    if name.casefold() == 'custom' or await exams.find_one({'key': {'$regex': f'^{re.escape(name)}$', '$options': 'i'}}):
        raise HTTPException(409, 'An exam with this name already exists.')
    base = slugify(body.short) or slugify(name) or 'exam'
    slug, n = base, 1
    while await exams.find_one({'_id': slug}):
        n += 1
        slug = f'{base}-{n}'
    last = await exams.find_one({}, {'_id': 0, 'order': 1}, sort=[('order', -1)])
    doc = {'slug': slug, 'key': name, 'name': name, 'short': body.short.strip(), 'subjects': [x.strip() for x in body.subjects],
           'color': body.color, 'builtin': False, 'shown': False, 'order': (last or {}).get('order', 0) + 1, 'created_at': now(), 'created_by': u['id']}
    await exams.insert_one({'_id': slug, **doc})
    await visibility(force=True)
    await audit(u['id'], 'Exam created (hidden from students)', slug, name)
    return {**exam_view(doc), 'sections': []}


@router.patch('/admin/catalog/exams/{slug}')
async def update_exam(slug: str, body: ExamPatch, u=Depends(owner)):
    e = await exams.find_one({'_id': slug}, {'_id': 0})
    if not e:
        raise HTTPException(404, 'Exam not found.')
    if e['builtin']:
        raise HTTPException(422, 'JEE Main, BITSAT and COMEDK keep their name, colours and Home visibility.')
    change = {k: v for k, v in body.model_dump(exclude_unset=True).items() if v is not None}
    if 'name' in change:
        change['name'] = ' '.join(change['name'].split())
    if not change:
        raise HTTPException(422, 'Nothing to change.')
    await exams.update_one({'_id': slug}, {'$set': change})
    await visibility(force=True)
    await audit(u['id'], 'Exam updated', slug, ', '.join(f'{k}={v}' for k, v in change.items())[:900])
    return exam_view({**e, **change})


@router.post('/admin/catalog/exams/{slug}/sections')
async def create_section(slug: str, body: SectionInput, u=Depends(owner)):
    e = await exams.find_one({'_id': slug}, {'_id': 0})
    if not e:
        raise HTTPException(404, 'Exam not found.')
    kind = body.kind
    if kind in SINGLE_KINDS and await sections.find_one({'exam_slug': slug, 'kind': kind}):
        raise HTTPException(409, f'{e["name"]} already has this mock type. Open it instead.')
    layout = 'chapters' if kind == 'chapters' else body.layout if kind == 'custom' else 'list'
    rules = default_rules(e['key'], kind)
    rules.update({k: v for k, v in (('minutes', body.minutes), ('correct', body.correct), ('wrong', body.wrong)) if v is not None})
    name = ' '.join(body.name.split())
    base = slugify(name) or 'section'
    if base == 'results':
        base = 'results-tests'
    candidate, n = base, 1
    while await sections.find_one({'exam_slug': slug, 'slug': candidate}):
        n += 1
        candidate = f'{base}-{n}'
    last = await sections.find_one({'exam_slug': slug}, {'_id': 0, 'order': 1}, sort=[('order', -1)])
    sid = str(uuid.uuid4())
    doc = {'id': sid, 'exam_slug': slug, 'slug': candidate, 'kind': kind, 'name': name, 'description': body.description.strip(),
           'layout': layout, 'builtin': False, 'hidden': False, 'order': (last or {}).get('order', 0) + 1, 'created_at': now(), 'created_by': u['id'],
           'defaults': rules}
    if kind == 'aits':
        from .series_admin import create_series
        doc['series_id'] = await create_series(e, sid, body, rules)
    await sections.insert_one({'_id': sid, **doc})
    await visibility(force=True)
    await audit(u['id'], 'Section created', sid, f'{slug} › {name}')
    return {**section_view(doc), 'counts': {'total': 0, 'live': 0, 'draft': 0}}


@router.patch('/admin/catalog/sections/{sid}')
async def update_section(sid: str, body: SectionPatch, u=Depends(owner)):
    s = await section_doc(sid)
    change = {k: v for k, v in body.model_dump(exclude_unset=True).items() if v is not None}
    rules = {k: change.pop(k) for k in ('minutes', 'correct', 'wrong') if k in change}
    if rules:
        e = await exams.find_one({'_id': s['exam_slug']}, {'_id': 0, 'key': 1})
        change['defaults'] = {**(s.get('defaults') or default_rules(e['key'], s['kind'])), **rules}
    if 'name' in change:
        change['name'] = ' '.join(change['name'].split())
    if not change:
        raise HTTPException(422, 'Nothing to change.')
    await sections.update_one({'_id': sid}, {'$set': change})
    await audit(u['id'], 'Section updated', sid, ', '.join(f'{k}={v}' for k, v in change.items())[:900])
    return section_view(await section_doc(sid))


@router.post('/admin/catalog/exams/{slug}/sections/order')
async def order_sections(slug: str, body: OrderInput, u=Depends(owner)):
    current_ids = set(await sections.distinct('id', {'exam_slug': slug}))
    if set(body.ids) != current_ids or len(body.ids) != len(current_ids):
        raise HTTPException(409, 'Sections changed elsewhere. Reload and try again.')
    await sections.bulk_write([UpdateOne({'_id': sid}, {'$set': {'order': i}}) for i, sid in enumerate(body.ids, 1)])
    await audit(u['id'], 'Sections reordered', slug)
    return {'ids': body.ids}


@router.get('/admin/catalog/sections/{sid}/tests')
async def admin_section_tests(sid: str, u=Depends(owner)):
    s = await section_doc(sid)
    e = await exams.find_one({'_id': s['exam_slug']}, {'_id': 0})
    t = await database_now()
    return {'section': section_view(s), 'exam': exam_view(e), 'items': [test_view(x, t) for x in await section_tests(s, e['key'])]}


@router.get('/admin/catalog/exams/{slug}/unplaced')
async def admin_unplaced(slug: str, u=Depends(owner)):
    e = await exams.find_one({'_id': slug}, {'_id': 0})
    if not e:
        raise HTTPException(404, 'Exam not found.')
    known = set(await sections.distinct('id', {'exam_slug': slug}))
    t = await database_now()
    rows = await sets.find({'$and': [ADMIN_BASE, UNPLACED, {'exam': e['key']}]}, FIELDS).sort([('created_at', -1)]).limit(500).to_list(500)
    return {'items': [test_view(x, t) for x in rows if f"{slug}:{legacy_kind(x)}" not in known]}


@router.post('/admin/catalog/sections/{sid}/order')
async def order_tests(sid: str, body: OrderInput, u=Depends(owner)):
    s = await section_doc(sid)
    e = await exams.find_one({'_id': s['exam_slug']}, {'_id': 0})
    present = [x['id'] for x in await section_tests(s, e['key'])]
    if set(body.ids) != set(present) or len(body.ids) != len(present):
        raise HTTPException(409, 'Tests in this section changed elsewhere. Reload and try again.')
    await sets.bulk_write([UpdateOne({'id': tid}, {'$set': {'catalog_order': i}}) for i, tid in enumerate(body.ids, 1)])
    await audit(u['id'], 'Section tests reordered', sid)
    return {'ids': body.ids}


async def exam_slug_of(s):
    if s.get('catalog_section_id'):
        found = await sections.find_one({'_id': s['catalog_section_id']}, {'_id': 0, 'exam_slug': 1})
        if found:
            return found['exam_slug']
    e = await exams.find_one({'key': s.get('exam')}, {'_id': 0, 'slug': 1})
    return e['slug'] if e else None


NOT_LIVE_NOTE = {
    'draft': 'Not published yet. Finish its review and publish it from its upload.',
    'scheduled': 'Scheduled. It opens to students at its start time.',
    'ended': 'Its time window has ended.',
    'paused': 'Still paused by its own schedule or upload controls. Open its upload to enable it.',
}


@router.patch('/admin/catalog/tests/{id}')
async def update_test(id: str, body: TestPatch, u=Depends(owner)):
    s = await sets.find_one({'$and': [{'id': id}, ADMIN_BASE]}, {'_id': 0, 'questions': 0})
    if not s:
        raise HTTPException(404, 'Test not found here. All India series papers are managed in Schedule & Live.')
    change, unset, notes = {}, {}, []
    if locked(s) and (body.title is not None or body.section_id is not None):
        raise HTTPException(409, 'Verified PYQ papers are locked. You can only switch them Live or Off.')
    if body.title is not None:
        change['display_title'] = ' '.join(body.title.split())
        notes.append('title=' + change['display_title'])
    if body.live is not None:
        if body.live:
            unset['owner_unlive'] = ''
        else:
            change['owner_unlive'] = True
        notes.append('live=' + str(body.live))
    if body.section_id is not None:
        target = await section_doc(body.section_id)
        if target['exam_slug'] != await exam_slug_of(s):
            raise HTTPException(409, 'Move tests within the same exam.')
        if target['kind'] == 'aits':
            raise HTTPException(409, 'Give All India papers a day from the series instead.')
        if target['kind'] == 'pyq' and s.get('test_kind') != 'pyq':
            raise HTTPException(409, 'Only PYQ papers belong in a PYQ type. Upload or write the paper there with its year.')
        change.update(catalog_section_id=target['id'], catalog_order=await next_order(target['id']))
        notes.append('section=' + target['id'])
    if not notes:
        raise HTTPException(422, 'Nothing to change.')
    await sets.update_one({'id': id}, {**({'$set': change} if change else {}), **({'$unset': unset} if unset else {})})
    await audit(u['id'], 'Test placement updated', id, '; '.join(notes)[:900])
    t = await database_now()
    row = await sets.find_one({'id': id}, FIELDS)
    view = test_view(row, t)
    return {**view, 'note': NOT_LIVE_NOTE.get(view['state'], '') if body.live else ''}


@router.get('/admin/overview')
async def overview(u=Depends(owner)):
    books = await db.tejas_books.find({'owner_id': u['id'], 'removed': False, 'archived': {'$ne': True}},
        {'_id': 1, 'state': 1, 'paused': 1, 'payload.title': 1, 'payload.pages': 1, 'payload.read_pages': 1,
         'payload.destination': 1, 'updated_at': 1}).sort('updated_at', -1).limit(100).to_list(100)
    mocks = await db.tejas_book_mocks.find({'book_id': {'$in': [b['_id'] for b in books]}, 'state': {'$in': ['ready', 'held']}},
        {'_id': 1, 'book_id': 1, 'label': 1, 'state': 1, 'issues': {'$slice': 1}}).to_list(5000)
    title = {b['_id']: b['payload']['title'] for b in books}
    return {
        'processing': [{'id': b['_id'], 'title': b['payload']['title'], 'state': b['state'], 'paused': b.get('paused', False),
                        'pages': b['payload'].get('pages', 0), 'read_pages': b['payload'].get('read_pages', 0),
                        'destination': b['payload'].get('destination')}
                       for b in books if b['state'] in ('uploading', 'received', 'reading', 'matching', 'paused', 'failed')][:10],
        'ready': sum(m['state'] == 'ready' for m in mocks),
        'held': sum(m['state'] == 'held' for m in mocks),
        'held_items': [{'id': m['_id'], 'book_id': m['book_id'], 'book_title': title.get(m['book_id'], ''), 'label': m['label'],
                        'reason': (m.get('issues') or [''])[0]} for m in mocks if m['state'] == 'held'][:6],
        'ready_books': sorted({m['book_id'] for m in mocks if m['state'] == 'ready'}),
        'open_reports': await db.tejas_question_reports.count_documents({'status': 'open'}),
    }


@router.get('/admin/review/held')
async def held_mocks(u=Depends(staff)):
    rows = await db.tejas_book_mocks.find({'state': 'held', 'archived': {'$ne': True}}, {'_id': 1, 'book_id': 1, 'label': 1, 'chapter.title': 1, 'issues': {'$slice': 8}}).sort('book_id', 1).limit(300).to_list(300)
    books = {b['_id']: b for b in await db.tejas_books.find({'_id': {'$in': list({r['book_id'] for r in rows})}, 'removed': False, 'archived': {'$ne': True}},
             {'_id': 1, 'payload.title': 1, 'payload.destination': 1}).to_list(300)}
    return {'items': [{'id': r['_id'], 'book_id': r['book_id'], 'label': (r.get('chapter') or {}).get('title') or r['label'], 'issues': r.get('issues', []),
                       'book_title': books[r['book_id']]['payload']['title'], 'destination': books[r['book_id']]['payload'].get('destination')}
                      for r in rows if r['book_id'] in books]}


# Shareable read-only section preview (titles, order and status only)

def token_hash(token):
    return hashlib.sha256(token.encode()).hexdigest()


async def active_link(sid, t):
    return await previews.find_one({'section_id': sid, 'revoked': False, 'expires_at': {'$gt': t}},
                                   {'_id': 0, 'expires_at': 1}, sort=[('created_at', -1)])


@router.get('/admin/catalog/sections/{sid}/preview-link')
async def preview_link_status(sid: str, u=Depends(owner)):
    await section_doc(sid)
    row = await active_link(sid, await database_now())
    return {'active': bool(row), 'expires_at': (row or {}).get('expires_at')}


@router.post('/admin/catalog/sections/{sid}/preview-link')
async def create_preview_link(sid: str, u=Depends(owner)):
    s = await section_doc(sid)
    t = await database_now()
    await previews.update_many({'section_id': sid, 'revoked': False}, {'$set': {'revoked': True, 'revoked_at': t}})
    token = secrets.token_urlsafe(24)
    expires = t + PREVIEW_DAYS * 86400
    await previews.insert_one({'_id': token_hash(token), 'section_id': sid, 'created_by': u['id'], 'created_at': t,
                               'expires_at': expires, 'revoked': False})
    await audit(u['id'], 'Section preview link created (old link stopped)', sid, f"{s['exam_slug']} › {s['name']}")
    return {'token': token, 'expires_at': expires}


@router.delete('/admin/catalog/sections/{sid}/preview-link')
async def revoke_preview_link(sid: str, u=Depends(owner)):
    await section_doc(sid)
    t = await database_now()
    done = await previews.update_many({'section_id': sid, 'revoked': False}, {'$set': {'revoked': True, 'revoked_at': t}})
    if done.modified_count:
        await audit(u['id'], 'Section preview link turned off', sid)
    return {'active': False, 'expires_at': None}


def waiting_state(m, release, t):
    if m['state'] == 'held':
        return 'held'
    if m.get('publish_requested'):
        return 'scheduled' if (release or 0) > t else 'publishing'
    return 'ready'


async def waiting_mocks(sid, t):
    books = await db.tejas_books.find({'payload.destination.section_id': sid, 'removed': False, 'archived': {'$ne': True}},
                                      {'_id': 1, 'payload.title': 1, 'payload.release_at': 1}).sort('created_at', 1).to_list(200)
    rank = {b['_id']: i for i, b in enumerate(books)}
    book = {b['_id']: b['payload'] for b in books}
    rows = await db.tejas_book_mocks.find({'book_id': {'$in': list(rank)}, 'state': {'$in': ['ready', 'held']}, 'set_id': None, 'archived': {'$ne': True}},
        {'_id': 0, 'book_id': 1, 'label': 1, 'chapter': 1, 'order': 1, 'state': 1, 'publish_requested': 1, 'release_at': 1, 'rules.minutes': 1,
         'count': {'$size': {'$ifNull': ['$questions', []]}}}).to_list(5000)
    rows.sort(key=lambda m: (rank[m['book_id']], m['order']))
    out = []
    for m in rows:
        release = m.get('release_at') or book[m['book_id']].get('release_at')
        out.append({'title': (m.get('chapter') or {}).get('title') or m['label'], 'state': waiting_state(m, release, t), 'count': m.get('count', 0),
                    'minutes': (m.get('rules') or {}).get('minutes'), 'subject': None, 'book': book[m['book_id']].get('title'),
                    'start_at': release if m.get('publish_requested') else None})
    return out


@router.get('/preview/sections/{token}')
async def section_preview(token: str = Path(min_length=20, max_length=64, pattern=r'^[A-Za-z0-9_-]+$')):
    t = await database_now()
    link = await previews.find_one({'_id': token_hash(token)}, {'_id': 0})
    s = await sections.find_one({'_id': link['section_id']}, {'_id': 0}) if link and not link['revoked'] and link['expires_at'] > t else None
    if not s:
        raise HTTPException(404, 'This preview link has expired or was turned off. Ask the owner for a new link.')
    e = await exams.find_one({'_id': s['exam_slug']}, {'_id': 0})
    items = [{**{k: v[k] for k in ('title', 'state', 'count', 'minutes', 'subject', 'start_at')}, 'book': None}
             for v in (test_view(x, t) for x in await section_tests(s, e['key']))]
    items += await waiting_mocks(s['id'], t)
    return {'exam': {'name': e['name'], 'short': e['short'], 'color': e['color'], 'shown': e['shown']},
            'section': {'name': s['name'], 'description': s.get('description', ''), 'layout': s['layout'], 'hidden': s['hidden']},
            'items': items, 'live_count': sum(i['state'] == 'live' for i in items),
            'expires_at': link['expires_at'], 'server_now': t}


@router.get('/admin/schedule/timed')
async def timed_tests(u=Depends(owner)):
    t = await database_now()
    rows = await sets.find({'$and': [ADMIN_BASE, {'status': 'published'}, {'$or': [{'start_at': {'$gt': t}}, {'competition': True, 'end_at': {'$gt': t}}]}]},
                           FIELDS).sort('start_at', 1).limit(200).to_list(200)
    return {'items': [test_view(x, t) for x in rows], 'server_now': t}


# Ready-to-publish desk: book mocks, paper uploads and chapter books that are checked but not yet live

async def waiting_items(sid=''):
    t = await database_now()
    where = {'payload.destination.section_id': sid} if sid else {'payload.destination.section_id': {'$exists': True}}
    books = await db.tejas_books.find({**where, 'removed': False, 'archived': {'$ne': True}, 'payload.destination.series': {'$ne': True}},
        {'_id': 1, 'payload.title': 1, 'payload.release_at': 1, 'payload.destination': 1}).sort('created_at', 1).to_list(300)
    rank = {b['_id']: i for i, b in enumerate(books)}
    info = {b['_id']: b['payload'] for b in books}
    rows = await db.tejas_book_mocks.find({'book_id': {'$in': list(rank)}, 'state': {'$in': ['ready', 'held']}, 'set_id': None, 'archived': {'$ne': True}},
        {'_id': 1, 'book_id': 1, 'label': 1, 'chapter': 1, 'order': 1, 'state': 1, 'publish_requested': 1, 'release_at': 1,
         'issue': {'$arrayElemAt': ['$issues', 0]}, 'issue_count': {'$size': {'$ifNull': ['$issues', []]}}, 'cut_summary': 1,
         'key_only': {'$size': {'$filter': {'input': {'$ifNull': ['$questions', []]}, 'cond': {'$eq': ['$$this.solution_kind', 'answer_key_only']}}}},
         'count': {'$size': {'$ifNull': ['$questions', []]}}}).to_list(5000)
    rows.sort(key=lambda m: (rank[m['book_id']], m['order']))
    out = []
    for m in rows:
        p = info[m['book_id']]
        release = m.get('release_at') or p.get('release_at')
        out.append({'kind': 'book_mock', 'id': m['_id'], 'book_id': m['book_id'], 'title': (m.get('chapter') or {}).get('title') or m['label'], 'book': p['title'], 'chapter': m.get('chapter') or {},
                    'state': waiting_state(m, release, t), 'count': m.get('count', 0), 'key_only': m.get('key_only', 0), 'unit': 'questions', 'issue': m.get('issue') or '',
                    'issue_count': m.get('issue_count', 0), 'start_at': release if m.get('publish_requested') else None, 'destination': p['destination'], 'cut': m.get('cut_summary') or None})
    dq = {'destination.section_id': sid} if sid else {'destination.section_id': {'$exists': True}}
    recs = await db.tejas_imports.find({**dq, 'status': 'ready', 'archived': {'$ne': True}, 'destination.series': {'$ne': True}, 'qa_only': {'$ne': True}},
        {'_id': 0, 'id': 1, 'title': 1, 'destination': 1, 'issue_count': {'$size': {'$ifNull': ['$issues', []]}},
         'count': {'$size': {'$ifNull': ['$questions', []]}}}).to_list(500)
    made = set(await sets.distinct('id', {'id': {'$in': [r['id'] for r in recs]}}))
    out += [{'kind': 'import', 'id': r['id'], 'title': r['title'], 'book': 'Paper / Excel upload', 'state': 'held' if r['issue_count'] else 'ready',
             'count': r['count'], 'unit': 'questions', 'issue': 'Open the upload to fix its source issues.' if r['issue_count'] else '',
             'issue_count': r['issue_count'], 'start_at': None, 'destination': r['destination']} for r in recs if r['id'] not in made]
    for r in await db.tejas_chapter_books.find({**dq, 'status': 'ready', 'archived': {'$ne': True}, 'qa_only': {'$ne': True}},
                                                {'_id': 0, 'id': 1, 'title': 1, 'destination': 1}).to_list(300):
        drafts = await sets.count_documents({'chapter_book_id': r['id'], 'start_at': {'$exists': False}, 'archived': {'$ne': True}})
        if drafts:
            out.append({'kind': 'chapter_book', 'id': r['id'], 'title': r['title'], 'book': 'Chapter book', 'state': 'ready', 'count': drafts,
                        'unit': 'chapters', 'issue': '', 'issue_count': 0, 'start_at': None, 'destination': r['destination']})
    return out


@router.get('/admin/catalog/waiting')
async def waiting(section_id: str = Query('', max_length=100), u=Depends(owner)):
    return {'items': await waiting_items(section_id)}


@router.post('/admin/publish-ready')
async def publish_ready_items(body: PublishInput, bg: BackgroundTasks, u=Depends(owner)):
    if body.release_at and body.release_at <= await database_now():
        raise HTTPException(422, 'Choose a future date and time, or publish now.')
    items = [(i.kind, i.id) for i in body.items] or [(x['kind'], x['id']) for x in await waiting_items(body.section_id)
                                                     if x['state'] == 'ready' and x['kind'] != 'import']
    if not items:
        raise HTTPException(409, 'Nothing here is ready yet. Held items stay private until their problems are fixed.')
    from .book_imports import request_publication
    wanted = {}
    for kind, id in items:
        if kind == 'book':
            wanted[id] = None
        elif kind == 'book_mock':
            m = await db.tejas_book_mocks.find_one({'_id': id}, {'book_id': 1})
            if not m:
                raise HTTPException(404, 'Mock not found.')
            if wanted.get(m['book_id'], set()) is not None:
                wanted.setdefault(m['book_id'], set()).add(id)
    done, notes = 0, []
    for bid, ids in wanted.items():
        done += await request_publication(bid, ids, body.release_at, bg, u)
    for kind, id in items:
        if kind != 'chapter_book':
            continue
        if body.release_at:
            notes.append('Chapter books publish straight away. Choose Now for them.')
            continue
        from .chapter_books import publish_book, ChapterAction, books as chapter_records
        r = await chapter_records.find_one({'id': id}, {'_id': 0, 'revision': 1})
        if not r:
            raise HTTPException(404, 'Chapter book not found.')
        try:
            await publish_book(id, ChapterAction(revision=r['revision']), u)
            done += 1
        except HTTPException as exc:
            notes.append(str(exc.detail))
    if not done:
        raise HTTPException(409, notes[0] if notes else 'Nothing could be published. Held mocks stay private until their problems are fixed.')
    when = 'scheduled for the chosen time' if body.release_at else 'publishing now. They appear to students in a moment'
    return {'requested': done, 'notes': notes, 'message': f"{done} item{'s' if done != 1 else ''} {when}."}
