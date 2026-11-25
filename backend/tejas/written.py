"""Mocks written in Master: one question at a time, or a whole pasted paper split into questions. No AI."""
import io, re
from typing import Annotated, Literal
from fastapi import APIRouter, Depends, File, HTTPException, Response, UploadFile
from pydantic import BaseModel, ConfigDict, Field
from starlette.concurrency import run_in_threadpool
from .auth import owner, staff
from .db import db, sets, files, now, uid, audit
from .canonical import database_now
from tejas_storage import put_object, get_object

router = APIRouter(prefix='/api/admin/master', tags=['Written mocks'])
LETTERS = 'ABCDE'
NUMBER = re.compile(r'^[+-]?\d{1,20}$')
FileId = Annotated[str, Field(max_length=100)]
SUBJECTS = {'physics': 'Physics', 'chemistry': 'Chemistry', 'mathematics': 'Mathematics', 'maths': 'Mathematics', 'math': 'Mathematics',
            'biology': 'Biology', 'botany': 'Botany', 'zoology': 'Zoology', 'english': 'English', 'english proficiency': 'English',
            'logical reasoning': 'Logical reasoning', 'reasoning': 'Logical reasoning'}


class Payload(BaseModel):
    model_config = ConfigDict(extra='forbid', strict=True, allow_inf_nan=False)


class WrittenInput(Payload):
    title: str = Field(min_length=2, max_length=160)
    minutes: int | None = Field(default=None, gt=0, le=1440)
    correct: float | None = Field(default=None, gt=0, le=100)
    wrong: float | None = Field(default=None, ge=-100, le=0)
    subject: str = Field(default='', max_length=40)
    chapter: str = Field(default='', max_length=120)
    year: int | None = Field(default=None, ge=1990, le=2100)
    exam_date: str = Field(default='', pattern=r'^(\d{4}-\d{2}-\d{2})?$')
    shift: int | None = Field(default=None, ge=0, le=9)


class WrittenPatch(Payload):
    title: str | None = Field(default=None, min_length=2, max_length=160)
    minutes: int | None = Field(default=None, gt=0, le=1440)
    correct: float | None = Field(default=None, gt=0, le=100)
    wrong: float | None = Field(default=None, ge=-100, le=0)
    year: int | None = Field(default=None, ge=1990, le=2100)
    exam_date: str | None = Field(default=None, pattern=r'^(\d{4}-\d{2}-\d{2})?$')
    shift: int | None = Field(default=None, ge=0, le=9)


class OptionInput(Payload):
    text: str = Field(default='', max_length=4000)
    image: FileId = ''


class QuestionInput(Payload):
    id: str = Field(default='', max_length=100)
    subject: str = Field(min_length=1, max_length=40)
    chapter: str = Field(default='', max_length=120)
    text: str = Field(default='', max_length=20000)
    image: FileId = ''
    type: Literal['mcq', 'integer']
    options: list[OptionInput] = Field(default_factory=list, max_length=5)
    answer: str = Field(min_length=1, max_length=40)
    solution: str = Field(default='', max_length=20000)
    solution_image: FileId = ''


class PasteInput(Payload):
    text: str = Field(min_length=10, max_length=400000)
    subject: str = Field(default='', max_length=40)


async def math_ok(*texts):
    from .reports import validate_typed_math
    if not any('$' in t for t in texts):
        return True
    try:
        await run_in_threadpool(validate_typed_math, {'text': '\n'.join(texts)})
        return True
    except ValueError:
        return False


def problems(s):
    """Why a written mock cannot go live yet (empty when it can)."""
    qs = s.get('questions', [])
    if not qs:
        return ['Add at least one question.']
    flagged = [q for q in qs if q.get('flag')]
    if flagged:
        return [f"{len(flagged)} question{'s' if len(flagged) != 1 else ''} to fix: " + ', '.join(f"Q{q['number']}" for q in flagged[:10])]
    return []


def unchecked(exc, so):
    """Supabase could not be asked about the photos: nothing is said about any of them and the mock stays as it is."""
    import tejas_storage as store
    code, scope = getattr(exc, 'code', None), store.scope_of(exc)
    why = store.explain(code, scope)[0] if scope in ('away', 'blocked') else 'Supabase ne is mock ki photo ki list nahi di' + (f' ({code})' if code else '')
    return f'Is mock ki photo abhi jaanchi nahi ja saki ({why}), {so}. Thodi der baad phir koshish kijiye.'


async def photo_trouble(s, so, only=None):
    """Why this written mock cannot be shown to students, or None. Every photo is read back from storage itself (never from this
    server's memory) and matched by its fingerprint, and all of them are in one store. `so` says what did not happen because of it.
    With `only`, just those photos are proven (the new ones of a mock that is already Live) and the one-store rule is not applied:
    a Live mock that still has photos in the old store must stay editable until those can be copied for it.
    Reads only: nothing is saved, copied or removed here. A verified JEE Main PYQ paper is never checked."""
    import tejas_storage as store
    from .picture_proof import prove, picture_ids, GONE, CHANGED
    kept = lambda q, k: [r for r in q.get(k) or [] if r.get('file_id') in only]  # noqa: E731
    paper = s if only is None else {**s, 'questions': [{**q, 'q_refs': kept(q, 'q_refs'), 's_refs': kept(q, 's_refs')} for q in s.get('questions', [])]}
    try:
        proof = await prove(paper, full=True)
    except store.StorageError as exc:
        return unchecked(exc, so)
    if proof is None:
        return None

    def named(hit):
        qs = [f"Q{q['number']}" for q in s.get('questions', []) if any(hit(r.get('file_id')) for k in ('q_refs', 's_refs') for r in q.get(k) or [])]
        return ', '.join(qs[:10]) + (' aur baaki' if len(qs) > 10 else '')
    bad = proof['bad']
    if bad:
        parts = [f'{who} ki photo {text}' for who, text in ((named(lambda f: bad.get(f) in GONE), 'storage mein nahi mili'),
                                                             (named(lambda f: bad.get(f) in CHANGED), 'storage mein badli hui mili'),
                                                             (named(lambda f: bad.get(f) == 'unread'), 'storage se padhi nahi ja saki')) if who]
        return f"{'; '.join(parts) or 'Is mock ki ek photo storage mein saabit nahi hui'}, {so}. Edit mein woh photo hata kar dobara lagaiye."
    if only is not None:
        return None
    rows = await files.find({'id': {'$in': picture_ids(s)}}, {'_id': 0, 'id': 1, 'path': 1}).to_list(None)
    in_supabase = {f['id'] for f in rows if str(f.get('path') or '').startswith(store.SB)}
    in_emergent = {f['id'] for f in rows} - in_supabase
    if in_supabase and in_emergent:
        old, there = ('Emergent', in_emergent) if store.configured() else ('Supabase', in_supabase)   # the store new photos do not go to
        return (f'Is mock ki photo do storage mein bati hain ({len(in_supabase)} Supabase mein, {len(in_emergent)} Emergent mein), {so}. '
                f'{named(lambda f: f in there)} ki photo purane storage ({old}) mein hai: Edit mein use hata kar dobara lagaiye.')
    return None


LIVE_SO = 'isliye yeh badlav save nahi hua (Live paper jaisa tha waisa hi hai)'


async def live_photos(s, questions, ids):
    """A Live mock is changed only when its photos can be read, and a new photo is first proven in storage itself. Otherwise nothing is
    saved, so students never get a changed paper that has no version or a question whose photo is not there."""
    from tejas_storage import StorageError
    from .content import validate_refs
    paper = {**s, 'questions': questions, 'file_ids': ids}
    new = set(ids) - {r['file_id'] for q in s.get('questions', []) for k in ('q_refs', 's_refs') for r in q.get(k) or []}
    why = await photo_trouble(paper, LIVE_SO, new) if new else None
    if not why:
        try:
            seen = {}
            for q in questions:
                await validate_refs(paper, q, seen)
        except StorageError as exc:
            why = await photo_trouble(paper, LIVE_SO, set(ids)) or unchecked(exc, LIVE_SO)
    if why:
        raise HTTPException(409, why)


async def written_doc(id, u=None):
    s = await sets.find_one({'id': id, 'written': True, 'archived': {'$ne': True}}, {'_id': 0})
    # Reviewers reach only drafts that still have marked questions.
    if not s or (u and u['role'] != 'owner' and (s['status'] != 'draft' or not any(q.get('flag') for q in s.get('questions', [])))):
        raise HTTPException(404, 'Mock not found.')
    return s


async def guard_series(s):
    if s.get('series_date'):
        from .live_series import set_window
        if await database_now() >= set_window(s)['opens_at']:
            raise HTTPException(409, 'This series day has opened, so its paper stays as it is.')


def ref(fid, label):
    return {'file_id': fid, 'page': 1, 'rect': [0, 0, 1, 1], 'prerendered': True, 'label': label}


def check_input(body, exam):
    if not body.text.strip() and not body.image:
        raise HTTPException(422, 'Type the question or add its photo.')
    answer = body.answer.strip()
    if body.type == 'mcq':
        if len(body.options) < 2 or any(not o.text.strip() and not o.image for o in body.options):
            raise HTTPException(422, 'Give every option some text or a photo, at least two options.')
        if answer.upper() not in LETTERS[:len(body.options)]:
            raise HTTPException(422, 'Choose the correct option.')
    else:
        if exam == 'BITSAT':
            raise HTTPException(422, 'BITSAT questions need options.')
        if not NUMBER.fullmatch(answer):
            raise HTTPException(422, 'A numerical answer must be a whole number, for example 12 or -3.')


def build(body, number, qid, flag=''):
    mcq = body.type == 'mcq'
    answer = body.answer.strip().upper() if mcq else body.answer.strip()
    options = {LETTERS[i]: o.text.strip() or f'Option {LETTERS[i]} (see its figure)' for i, o in enumerate(body.options)} if mcq else {}
    q_refs = ([ref(body.image, '')] if body.image else []) + [ref(o.image, f'Option {LETTERS[i]}') for i, o in enumerate(body.options) if mcq and o.image]
    worked = bool(body.solution.strip() or body.solution_image)
    solution = body.solution.strip() or (f'Answer: {answer}. See the worked solution figure.' if body.solution_image else f'Answer: {answer}.')
    text = body.text.strip() or 'See the figure.'
    return {'id': qid, 'number': number, 'subject': body.subject.strip(), 'section': body.subject.strip(), 'chapter': body.chapter.strip(),
            'type': body.type, 'text': text, 'options': options, 'answer': answer, 'solution': solution,
            'solution_kind': 'supplied_worked' if worked else 'answer_key_only', 'render_mode': 'written',
            'q_refs': q_refs, 's_refs': [ref(body.solution_image, 'Solution')] if body.solution_image else [],
            'approved': True, 'issues': [], 'solution_number': number, 'accessible_text': text, 'solution_accessible_text': solution,
            'disposition': 'standard', 'flag': flag, 'input': body.model_dump()}


async def save_questions(s, questions, u, note):
    for i, q in enumerate(questions, 1):
        q['number'] = q['solution_number'] = i
    ids = sorted({r['file_id'] for q in questions for k in ('q_refs', 's_refs') for r in q[k]})
    if s['status'] == 'published':
        await live_photos(s, questions, ids)
    done = await sets.update_one({'id': s['id'], 'revision': s['revision']},
                                 {'$set': {'questions': questions, 'file_ids': ids, 'updated_at': now()}, '$inc': {'revision': 1}})
    if not done.modified_count:
        raise HTTPException(409, 'This mock changed a moment ago. Reload and try again.')
    if s['status'] == 'published':
        from .content import publish_validated
        await publish_validated(s['id'], {'confirm': True}, u)
    await audit(u['id'], 'Written mock edited', s['id'], note)


async def owned_images(s, body):
    wanted = {x for x in [body.image, body.solution_image, *(o.image for o in body.options)] if x}
    if wanted and await files.count_documents({'id': {'$in': list(wanted)}, 'set_id': s['id']}) != len(wanted):
        raise HTTPException(422, 'A photo belongs to another mock. Add it again here.')


def view(s, extra=None):
    from .structure import test_state
    return {**{k: s.get(k) for k in ('id', 'title', 'exam', 'status', 'rules', 'catalog_section_id', 'chapter_subject', 'chapter_title',
                                     'pyq_year', 'pyq_date', 'pyq_shift', 'series_date', 'revision', 'version', 'test_kind')},
            'questions': [{k: q.get(k) for k in ('id', 'number', 'subject', 'chapter', 'type', 'text', 'options', 'answer', 'solution', 'flag', 'input', 'q_refs', 's_refs')} for q in s.get('questions', [])],
            'problems': problems(s), 'state': test_state(s, now()), **(extra or {})}


# Creating and reading

@router.post('/types/{sid}/written')
async def create_written(sid: str, body: WrittenInput, u=Depends(owner)):
    from .structure import section_doc, exams, next_order, default_rules
    from .content import valid_rules
    s = await section_doc(sid)
    e = await exams.find_one({'_id': s['exam_slug']}, {'_id': 0})
    rules = {**(s.get('defaults') or default_rules(e['key'], s['kind']))}
    rules.update({k: v for k, v in (('minutes', body.minutes), ('correct', body.correct), ('wrong', body.wrong)) if v is not None})
    doc = {'id': uid(), 'title': ' '.join(body.title.split()), 'exam': e['key'], 'written': True, 'status': 'draft', 'version': 0, 'revision': 1,
           'questions': [], 'file_ids': [], 'rules': valid_rules({'minutes': rules['minutes'], 'correct': rules['correct'], 'wrong': rules['wrong'], 'skipped': 0}),
           'source': 'Written by the owner in Super Admin', 'attribution': 'Owner-written content', 'rights_upload': True, 'rights_publish': True,
           'rights_report': True, 'audience': 'all', 'allowed_emails': [], 'allowed_phones': [], 'expires': '', 'live_enabled': True,
           'profile_mode': 'practice', 'test_kind': 'mock', 'full_length': True, 'catalog_section_id': sid, 'created_at': now(), 'created_by': u['id']}
    if s['kind'] != 'aits':
        doc['catalog_order'] = await next_order(sid)
    if s['layout'] == 'chapters':
        if not body.subject.strip() or not body.chapter.strip():
            raise HTTPException(422, 'Choose the subject and name the chapter.')
        n = await sets.count_documents({'catalog_section_id': sid, 'chapter_subject': body.subject.strip()})
        doc.update(test_kind='chapter', full_length=False, chapter_subject=body.subject.strip(), chapter_title=body.chapter.strip(), chapter_number=n + 1)
    if s['kind'] == 'pyq':
        if not body.year:
            raise HTTPException(422, 'Enter the year of this PYQ paper.')
        doc.update(test_kind='pyq', master_pyq=True, pyq_year=body.year, pyq_date=body.exam_date, pyq_shift=body.shift or 0)
    await sets.insert_one(dict(doc))
    await audit(u['id'], 'Written mock created (draft)', doc['id'], f"{e['name']} › {s['name']}")
    return {'id': doc['id']}


@router.get('/written/{id}')
async def read_written(id: str, u=Depends(staff)):
    from .structure import sections, exams
    s = await written_doc(id, u)
    sec = await sections.find_one({'_id': s.get('catalog_section_id')}, {'_id': 0, 'id': 1, 'name': 1, 'kind': 1, 'layout': 1, 'exam_slug': 1}) or {}
    e = await exams.find_one({'key': s['exam']}, {'_id': 0, 'slug': 1, 'name': 1, 'subjects': 1}) or {}
    return view(s, {'section': sec, 'exam_info': e})


@router.patch('/written/{id}')
async def update_written(id: str, body: WrittenPatch, u=Depends(owner)):
    s = await written_doc(id)
    await guard_series(s)
    change = {}
    if body.title:
        change['title'] = ' '.join(body.title.split())
    for k in ('minutes', 'correct', 'wrong'):
        if getattr(body, k) is not None:
            change['rules.' + k] = getattr(body, k)
    if s.get('series_date') and any(k.startswith('rules.') for k in change):
        raise HTTPException(409, 'A series paper keeps the series time and marks.')
    if s.get('master_pyq'):
        change.update({f: v for f, v in (('pyq_year', body.year), ('pyq_date', body.exam_date), ('pyq_shift', body.shift)) if v is not None})
    if not change:
        raise HTTPException(422, 'Nothing to change.')
    if s['status'] == 'published':
        await live_photos(s, s.get('questions', []), s.get('file_ids', []))
    await sets.update_one({'id': id, 'revision': s['revision']}, {'$set': change, '$inc': {'revision': 1}})
    if s['status'] == 'published':
        from .content import publish_validated
        await publish_validated(id, {'confirm': True}, u)
    await audit(u['id'], 'Written mock details changed', id, ', '.join(change))
    return view(await written_doc(id))


# Questions

@router.put('/written/{id}/questions')
async def save_question(id: str, body: QuestionInput, u=Depends(staff)):
    s = await written_doc(id, u)
    await guard_series(s)
    check_input(body, s['exam'])
    await owned_images(s, body)
    if not await math_ok(body.text, body.solution, *(o.text for o in body.options)):
        raise HTTPException(422, 'The maths between $ signs could not be read. Check the $ signs and brackets.')
    qs = list(s.get('questions', []))
    at = next((i for i, q in enumerate(qs) if q['id'] == body.id), None) if body.id else None
    if body.id and at is None:
        raise HTTPException(404, 'This question is no longer in the mock. Reload.')
    if u['role'] != 'owner' and (at is None or not qs[at].get('flag')):
        raise HTTPException(403, 'Reviewers fix marked questions only.')
    q = build(body, (at if at is not None else len(qs)) + 1, body.id or uid())
    if at is None:
        qs.append(q)
    else:
        qs[at] = q
    await save_questions(s, qs, u, f"Q{q['number']} saved")
    left = len([x for x in qs if x.get('flag')])
    return {'id': q['id'], 'number': q['number'], 'flags': left,
            'message': f"Q{q['number']} saved." + (' Students get the new version from their next start.' if s['status'] == 'published' else '')}


@router.delete('/written/{id}/questions/{qid}')
async def delete_question(id: str, qid: str, u=Depends(owner)):
    s = await written_doc(id)
    await guard_series(s)
    qs = [q for q in s.get('questions', []) if q['id'] != qid]
    if len(qs) == len(s.get('questions', [])):
        raise HTTPException(404, 'Question not found.')
    if not qs and s['status'] == 'published':
        raise HTTPException(409, 'A live mock needs at least one question. Switch it Off first.')
    await save_questions(s, qs, u, f'Question {qid} removed')
    return {'message': 'Question removed.'}


@router.post('/written/{id}/images')
async def upload_image(id: str, file: UploadFile = File(...), u=Depends(staff)):
    await written_doc(id, u)
    raw = await file.read(6 * 1024 * 1024 + 1)
    if len(raw) > 6 * 1024 * 1024:
        raise HTTPException(413, 'Photo 6 MB ke andar chuniye.')
    def to_png(data):
        from PIL import Image
        img = Image.open(io.BytesIO(data))
        if img.format not in ('PNG', 'JPEG', 'MPO', 'WEBP'):  # MPO is what many phone cameras call their JPG
            raise ValueError('format')
        img.load()
        if img.width * img.height > 40_000_000:
            raise ValueError('too large')
        img = img.convert('RGBA' if img.mode in ('RGBA', 'LA', 'P') else 'RGB')
        out = io.BytesIO()
        img.save(out, 'PNG', optimize=True)
        return out.getvalue(), img.width, img.height
    try:
        png, w, h = await run_in_threadpool(to_png, raw)
    except Exception:
        raise HTTPException(422, 'PNG, JPG ya WebP photo chuniye.') from None
    import hashlib
    from .png_small import shrink_many
    png = (await run_in_threadpool(shrink_many, [png]))[0]
    digest = hashlib.sha256(png).hexdigest()
    fid = uid()
    path = await run_in_threadpool(put_object, f'jeelive/written/{id}/{fid}.png', png, 'image/png')
    await files.insert_one({'id': fid, 'set_id': id, 'path': path, 'kind': 'rendered_png', 'sha256': digest, 'width': w, 'height': h,
                            'filename': (file.filename or 'photo')[:120], 'created_at': now(), 'created_by': u['id']})
    return {'id': fid, 'width': w, 'height': h}


@router.get('/written/{id}/images/{fid}')
async def read_image(id: str, fid: str, u=Depends(staff)):
    await written_doc(id, u)
    f = await files.find_one({'id': fid, 'set_id': id}, {'_id': 0, 'path': 1})
    if not f:
        raise HTTPException(404, 'Photo not found.')
    return Response(await run_in_threadpool(get_object, f['path']), media_type='image/png', headers={'Cache-Control': 'private, max-age=3600'})


# Whole-paper paste

SUBJECT_LINE = re.compile(r'^\s*(?:(?:part|section)\s*[-–:]?\s*[A-Z0-9]{0,3}\s*[-–:.]?\s*)?([A-Za-z ]{4,25}?)\s*(?:section|part)?\s*[:.]?\s*$', re.I)
QUESTION = re.compile(r'^\s*(?:Q(?:uestion|ues)?\.?\s*)?(\d{1,3})\s*[.):\]]\s*(.*)$', re.I)
OPTION = re.compile(r'^\s*(?:\(\s*([A-Da-d1-4])\s*\)|([A-Da-d])\s*[).\]])\s*(.*)$')
INLINE_OPTIONS = re.compile(r'\(\s*([A-Da-d1-4])\s*\)')
LABEL = {'1': 'A', '2': 'B', '3': 'C', '4': 'D'}
ANSWER = re.compile(r'^\s*(?:ans(?:wer)?|correct\s+(?:answer|option)|key)\s*[:.\-–]\s*\(?\s*([A-Da-d]|[+-]?\d+(?:\.\d+)?)\s*\)?\s*\.?\s*$', re.I)
SOLUTION = re.compile(r'^\s*(?:sol(?:ution|n)?|explanation|hint)\s*[:.\-–]\s*(.*)$', re.I)
KEY_HEAD = re.compile(r'^\s*(?:answer\s*keys?|answers|key)\s*[:.\-–]?\s*$', re.I)
SOLUTIONS_HEAD = re.compile(r'^\s*(?:(?:hints?\s*(?:and|&)\s*)?solutions?|explanations?|detailed\s+solutions?)\s*[:.\-–]?\s*$', re.I)
KEY_PAIR = re.compile(r'(\d{1,3})\s*[.):\-–]?\s*\(?\s*([A-Da-d]|[+-]?\d+(?:\.\d+)?)\s*\)?(?=\s|,|;|$)')


def subject_of(line):
    m = SUBJECT_LINE.match(line)
    return SUBJECTS.get(' '.join(m.group(1).lower().split())) if m else None


def parse_paper(text, fallback=''):
    questions, keys, sols = [], {}, {}
    mode, subject, cur, field, sol_key = 'q', fallback, None, None, None
    for raw in text.replace('\r', '').split('\n'):
        line = raw.strip()
        if not line:
            continue
        if KEY_HEAD.match(line):
            mode, cur = 'key', None
            continue
        if SOLUTIONS_HEAD.match(line):
            mode, cur, sol_key = 'sol', None, None
            continue
        found = subject_of(line) if len(line) <= 40 else None
        if found:
            subject = found
            continue
        if mode == 'key':
            for n, a in KEY_PAIR.findall(line):
                keys[(subject, int(n))] = a.upper()
            continue
        start = QUESTION.match(line)
        if mode == 'sol':
            if start:
                sol_key = (subject, int(start.group(1)))
                sols[sol_key] = [start.group(2)]
            elif sol_key:
                sols[sol_key].append(line)
            continue
        if start and not (cur and field == 'option' and OPTION.match(line)):
            cur = {'n': int(start.group(1)), 'subject': subject, 'text': [start.group(2)], 'options': {}, 'answer': '', 'solution': []}
            questions.append(cur)
            field = 'text'
            line = ''
        if not cur or not line:
            continue
        a, sm = ANSWER.match(line), SOLUTION.match(line)
        if a:
            cur['answer'] = a.group(1).upper()
        elif sm:
            field = 'solution'
            cur['solution'].append(sm.group(1))
        elif field != 'solution' and len(INLINE_OPTIONS.findall(line)) >= 2:
            parts = INLINE_OPTIONS.split(line)
            if parts[0].strip():
                cur['text'].append(parts[0].strip())
            for i in range(1, len(parts) - 1, 2):
                cur['numeric'] = cur.get('numeric') or parts[i] in LABEL
                cur['options'][LABEL.get(parts[i], parts[i].upper())] = parts[i + 1].strip()
            field = 'option'
        elif field != 'solution' and OPTION.match(line):
            o = OPTION.match(line)
            label = o.group(1) or o.group(2)
            cur['numeric'] = cur.get('numeric') or label in LABEL
            cur['last'] = LABEL.get(label, label.upper())
            cur['options'][cur['last']] = o.group(3).strip()
            field = 'option'
        elif field == 'option':
            cur['options'][cur.get('last') or list(cur['options'])[-1]] += ' ' + line
        else:
            cur[field].append(line)
    by_number = {}
    for q in questions:
        by_number.setdefault(q['n'], []).append(q)
    def lookup(table, q):
        if (q['subject'], q['n']) in table:
            return table[(q['subject'], q['n'])]
        loose = [v for (s, n), v in table.items() if n == q['n']]
        return loose[0] if len(loose) == 1 and len(by_number[q['n']]) == 1 else None
    out = []
    for q in questions:
        answer = q['answer'] or lookup(keys, q) or ''
        solution = ' '.join(q['solution']).strip() or ' '.join(lookup(sols, q) or []).strip()
        letters = [x for x in LETTERS if x in q['options']]
        kind = 'mcq' if len(letters) >= 2 else 'integer'
        if kind == 'mcq' and q.get('numeric') and answer in LABEL:
            answer = LABEL[answer]
        flag = ''
        if not ' '.join(q['text']).strip():
            flag = 'The question text was not found.'
        elif not q['subject']:
            flag = 'Choose the subject.'
        elif not answer:
            flag = 'No answer was found for it.'
        elif kind == 'mcq' and answer not in letters:
            flag = 'The answer does not match its options.'
        elif kind == 'integer' and not NUMBER.fullmatch(answer):
            flag = 'The answer is not a whole number. Decimal answers are not supported.' if re.fullmatch(r'[+-]?\d+\.\d+', answer) else 'Options were not found.'
        out.append({'subject': q['subject'] or fallback or 'General', 'text': ' '.join(q['text']).strip(), 'type': kind,
                    'options': [{'text': q['options'][x], 'image': ''} for x in letters] if kind == 'mcq' else [],
                    'answer': answer or '?', 'solution': solution, 'flag': flag})
    return out


@router.post('/written/{id}/paste')
async def paste(id: str, body: PasteInput, u=Depends(owner)):
    s = await written_doc(id)
    if s['status'] == 'published':
        raise HTTPException(409, 'Paste into a draft. A live mock changes one complete question at a time.')
    await guard_series(s)
    fallback = body.subject.strip() or s.get('chapter_subject') or ''
    if not fallback:
        e = await db.tejas_catalog_exams.find_one({'key': s['exam']}, {'_id': 0, 'subjects': 1}) or {}
        fallback = e['subjects'][0] if len(e.get('subjects', [])) == 1 else ''
    parsed = parse_paper(body.text, fallback)
    if not parsed:
        raise HTTPException(422, 'No numbered questions were found. Number each question like "1." or "Q1." and try again.')
    if len(parsed) + len(s.get('questions', [])) > 600:
        raise HTTPException(422, 'A mock can have at most 600 questions.')
    qs = list(s.get('questions', []))
    for p in parsed:
        if s['exam'] == 'BITSAT' and p['type'] == 'integer' and not p['flag']:
            p['flag'] = 'BITSAT questions need options.'
        if not p['flag'] and not await math_ok(p['text'], p['solution'], *(o['text'] for o in p['options'])):
            p['flag'] = 'The maths between $ signs could not be read.'
        body_in = QuestionInput.model_construct(id='', subject=p['subject'], chapter=s.get('chapter_title', ''), text=p['text'], image='',
                                                type=p['type'], options=[OptionInput.model_construct(**o) for o in p['options']],
                                                answer=p['answer'], solution=p['solution'], solution_image='')
        qs.append(build(body_in, len(qs) + 1, uid(), p['flag']))
    await save_questions(s, qs, u, f'{len(parsed)} questions pasted')
    flagged = sum(1 for p in parsed if p['flag'])
    return {'added': len(parsed), 'flags': flagged,
            'message': f"{len(parsed)} questions added." + (f' {flagged} marked to fix.' if flagged else ' All of them look complete.')}


@router.post('/written/{id}/excel')
async def excel(id: str, file: UploadFile = File(...), u=Depends(owner)):
    """Rows of the Excel template become ordinary written questions; unclear rows are marked to fix."""
    import tempfile
    from pathlib import Path
    from .sandbox import organise_pdfs
    s = await written_doc(id)
    if s['status'] == 'published':
        raise HTTPException(409, 'Import into a draft. A live mock changes one complete question at a time.')
    await guard_series(s)
    raw = await file.read(10 * 1024 * 1024 + 1)
    def is_xlsx(data):
        import zipfile
        try:
            names = set(zipfile.ZipFile(io.BytesIO(data)).namelist())
        except zipfile.BadZipFile:
            return False
        return {'[Content_Types].xml', 'xl/workbook.xml'} <= names
    if len(raw) > 10 * 1024 * 1024 or not (file.filename or '').lower().endswith('.xlsx') or not is_xlsx(raw):
        raise HTTPException(422, '10 MB tak ki .xlsx template file chuniye.')
    with tempfile.TemporaryDirectory(prefix='written-xlsx-') as directory:
        path = Path(directory) / 'questions.xlsx'
        path.write_bytes(raw)
        try:
            result = await organise_pdfs(path, None, 'xlsx')
        except ValueError as exc:
            raise HTTPException(422, str(exc)[:300]) from None
    rows = result.get('questions', [])
    if not rows:
        raise HTTPException(422, (result.get('issues') or [{}])[0].get('message') or 'No questions were found in this workbook.')
    if len(rows) + len(s.get('questions', [])) > 600:
        raise HTTPException(422, 'A mock can have at most 600 questions.')
    qs = list(s.get('questions', []))
    for r in rows:
        mcq = r['type'] == 'mcq'
        flags = [m for m in r.get('issues', []) if m != 'Matched solution text is required.']
        body = QuestionInput.model_construct(id='', subject=r.get('subject') or 'General', chapter=r.get('topic', ''), text=r.get('text', ''), image='',
            type='mcq' if mcq else 'integer', options=[OptionInput.model_construct(text=str(r['options'].get(x, '')), image='') for x in 'ABCD'] if mcq else [],
            answer=str(r.get('answer') or '?'), solution=r.get('solution', ''), solution_image='')
        qs.append(build(body, len(qs) + 1, uid(), flags[0] if flags else ''))
    await save_questions(s, qs, u, f'{len(rows)} questions imported from Excel')
    flagged = sum(1 for q in qs[-len(rows):] if q['flag'])
    return {'added': len(rows), 'flags': flagged, 'message': f"{len(rows)} questions added from Excel." + (f' {flagged} marked to fix.' if flagged else '')}
