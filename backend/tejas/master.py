"""Master: exam › mock type › mock. One list per type with five states (Draft, Live, Scheduled, Off, Library)."""
from typing import Annotated, Literal
from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from pydantic import BaseModel, ConfigDict, Field
from .auth import owner, staff
from .db import db, sets, attempts, audit, now
from .canonical import database_now

router = APIRouter(prefix='/api/admin/master', tags=['Master'])
Identity = Annotated[str, Field(min_length=1, max_length=100)]
STATUS = {'draft': 'draft', 'live': 'live', 'scheduled': 'scheduled', 'unlive': 'off', 'paused': 'off', 'ended': 'ended'}
PROCESSING = ('uploading', 'received', 'reading', 'matching', 'paused', 'failed')
FLAGGED = {'$elemMatch': {'flag': {'$nin': ['', None]}}}


class Payload(BaseModel):
    model_config = ConfigDict(extra='forbid', strict=True, allow_inf_nan=False)


class StatusItem(Payload):
    kind: Literal['set', 'book_mock']
    id: Identity


class StatusInput(Payload):
    items: list[StatusItem] = Field(min_length=1, max_length=1000)
    to: Literal['live', 'off', 'scheduled', 'library']
    at: float | None = Field(default=None, gt=0)
    live_exam: bool = False


@router.get('/summary')
async def summary(u=Depends(owner)):
    from .structure import waiting_items
    lists = await fix_list(u)
    report = (await db.tejas_operations.find_one({'id': 'integrity'}, {'_id': 0, 'report.needs_attention': 1}) or {}).get('report') or {}
    waiting = {}
    for w in await waiting_items():
        if w['kind'] == 'book_mock':
            waiting.setdefault(w['destination']['section_id'], {'ready': 0, 'held': 0})['held' if w['state'] == 'held' else 'ready'] += 1
    return {'to_fix': len(lists['items']), 'ready': len(lists['ready']), 'reports': await db.tejas_question_reports.count_documents({'status': 'open'}),
            'health': report.get('needs_attention') or 0, 'waiting': waiting}


@router.get('/fix')
async def fix_list(u=Depends(staff)):
    from .structure import held_mocks, sections, exams
    out = [{'kind': 'book_mock', 'id': m['id'], 'book_id': m['book_id'], 'title': m['label'], 'source': m['book_title'],
            'place': ' › '.join(x for x in ((m.get('destination') or {}).get('exam_name'), (m.get('destination') or {}).get('section_name')) if x),
            'section_id': (m.get('destination') or {}).get('section_id'), 'exam_slug': (m.get('destination') or {}).get('exam_slug'),
            'count': len(m['issues']), 'more': len(m['issues']) >= 8, 'reason': (m['issues'] or [''])[0]} for m in (await held_mocks(u))['items']]
    names = {s['id']: s for s in await sections.find({}, {'_id': 0, 'id': 1, 'name': 1, 'exam_slug': 1}).to_list(2000)}
    exam_names = {e['slug']: e['name'] for e in await exams.find({}, {'_id': 0, 'slug': 1, 'name': 1}).to_list(200)}
    written = {'written': True, 'status': 'draft', 'archived': {'$ne': True}}
    async for s in sets.find({**written, 'questions': FLAGGED}, {'_id': 0, 'id': 1, 'title': 1, 'catalog_section_id': 1, 'questions.flag': 1}).limit(300):
        sec = names.get(s.get('catalog_section_id'), {})
        n = sum(1 for q in s['questions'] if q.get('flag'))
        out.append({'kind': 'written', 'id': s['id'], 'title': s['title'], 'source': 'Written', 'place': ' › '.join(x for x in (exam_names.get(sec.get('exam_slug')), sec.get('name')) if x),
                    'section_id': sec.get('id'), 'exam_slug': sec.get('exam_slug'),
                    'count': n, 'reason': f"{n} question{'s' if n != 1 else ''} marked when the paper was pasted."})
    if u['role'] != 'owner':
        return {'items': out, 'ready': []}
    from .structure import waiting_items
    ready = [{'kind': 'book_mock', 'id': w['id'], 'book_id': w['book_id'], 'title': w['title'], 'source': w['book'],
              'place': f"{w['destination']['exam_name']} › {w['destination']['section_name']}", 'section_id': w['destination']['section_id'],
              'exam_slug': w['destination']['exam_slug'], 'count': w['count']} for w in await waiting_items() if w['kind'] == 'book_mock' and w['state'] == 'ready']
    async for s in sets.find({**written, 'questions.0': {'$exists': True}, 'questions': {'$not': FLAGGED}}, {'_id': 0, 'id': 1, 'title': 1, 'catalog_section_id': 1, 'count': {'$size': '$questions'}}).limit(300):
        sec = names.get(s.get('catalog_section_id'), {})
        ready.append({'kind': 'written', 'id': s['id'], 'title': s['title'], 'source': 'Written', 'place': ' › '.join(x for x in (exam_names.get(sec.get('exam_slug')), sec.get('name')) if x),
                      'section_id': sec.get('id'), 'exam_slug': sec.get('exam_slug'), 'count': s['count']})
    return {'items': out, 'ready': ready}


def set_item(v):
    state = STATUS.get(v['state'], 'off')
    to_fix = v['flags'] if v['written'] else 0
    empty = v['written'] and not v['count']
    return {'kind': 'set', 'id': v['id'], 'title': v['title'], 'status': state, 'to_fix': to_fix, 'empty': empty,
            'count': v['count'], 'minutes': v['minutes'], 'subject': v['subject'], 'start_at': v['start_at'], 'end_at': v['end_at'],
            'live_exam': v['live_exam'], 'locked': v['locked'], 'written': v['written'], 'year': v['year'], 'source': v['source'],
            'replace_pending': v['replace_pending'], 'book_id': v['book_import_id'], 'chapter_book_id': v['chapter_book_id'],
            'editable': v['written']}


@router.get('/types/{sid}/mocks')
async def type_mocks(sid: str, u=Depends(owner)):
    from .structure import section_doc, exams, section_tests, test_view, waiting_items, section_view, exam_view
    s = await section_doc(sid)
    e = await exams.find_one({'_id': s['exam_slug']}, {'_id': 0})
    t = await database_now()
    items = [set_item(test_view(x, t)) for x in await section_tests(s, e['key'])]
    waiting = await waiting_items(sid)
    busy = [w['id'] for w in waiting if w['kind'] == 'book_mock' and w['state'] == 'publishing']
    progress = {p['_id']: {'done': p['done'], 'total': p['total']} for p in await db.tejas_publish_progress.find({'_id': {'$in': busy}}).to_list(len(busy))} if busy else {}
    for w in waiting:
        if w['kind'] == 'import':
            items.append({'kind': 'import', 'id': w['id'], 'title': w['title'], 'status': 'draft', 'to_fix': w['issue_count'], 'count': w['count'],
                          'source': 'import', 'locked': False})
        if w['kind'] != 'book_mock':
            continue
        status = {'ready': 'draft', 'held': 'draft', 'publishing': 'publishing', 'scheduled': 'scheduled'}[w['state']]
        to_fix = 0
        if w['state'] == 'held':
            from .book_imports import question_problems
            from .book_models import BookMock
            row = await db.tejas_book_mocks.find_one({'_id': w['id']})
            qs, general = question_problems(BookMock.from_mongo(row))
            to_fix = max(1, len(qs) + len(general))
        items.append({'kind': 'book_mock', 'id': w['id'], 'title': w['title'], 'status': status, 'to_fix': to_fix, 'key_only': w.get('key_only', 0),
                      'count': w['count'], 'start_at': w['start_at'], 'book_id': w['book_id'], 'source': 'book', 'book': w['book'], 'locked': False, 'cut': w.get('cut'),
                      'subject': w['chapter'].get('subject') or None, 'chapter': w['chapter'] or None, 'subject_missing': bool(w['chapter']) and not w['chapter'].get('subject'),
                      'publish_progress': progress.get(w['id'])})
    uploads = []
    async for b in db.tejas_books.find({'payload.destination.section_id': sid, 'removed': False, 'archived': {'$ne': True}, '$or': [
            {'state': {'$in': [*PROCESSING, 'attention_needed', 'chapters_needed']}}, {'payload.chapters': True, 'state': 'ready'},
            {'state': 'ready', 'restored_at': {'$exists': True}}]},
                                       {'state': 1, 'paused': 1, 'restored_at': 1, 'revision': 1, 'payload.title': 1, 'payload.pages': 1, 'payload.read_pages': 1, 'payload.message': 1, 'payload.chapters': 1}):
        unread, chapters = b['state'] == 'attention_needed', bool(b['payload'].get('chapters'))
        done = b['state'] == 'ready' or bool(unread and await db.tejas_book_mocks.find_one({'book_id': b['_id']}, {'_id': 1}))
        # A read PDF is listed only if it is chapter-wise (rename/split again) or came back from the Library.
        if done and not chapters and not b.get('restored_at'):
            continue
        unread = unread and not done
        made = await db.tejas_book_mocks.count_documents({'book_id': b['_id'], 'archived': {'$ne': True}}) if done else 0
        message = (f"{made} chapters read. Open Chapters to rename them or change where they start." if done and chapters else
                   f"Back from the Library. {made} mock{'s' if made != 1 else ''} read from it, listed in this type." if done else
                   'No questions could be read from this PDF. A scanned (photo) PDF cannot be read by itself: use Write instead.' if unread else b['payload'].get('message', ''))
        paused = bool(b.get('paused')) and b['state'] != 'failed'
        uploads.append({'id': b['_id'], 'kind': 'book', 'title': b['payload']['title'], 'state': 'done' if done else 'failed' if unread else 'paused' if paused else b['state'],
                        'revision': b.get('revision', 0), 'can_retry': b['state'] == 'failed' and not unread,
                        'pages': 0 if done else b['payload'].get('pages', 0), 'read_pages': b['payload'].get('read_pages', 0), 'chapters': chapters, 'message': message,
                        'active': b['state'] in ('received', 'reading', 'matching') and not paused})
    async for c in db.tejas_chapter_books.find({'destination.section_id': sid, 'archived': {'$ne': True}, 'status': {'$in': ['queued', 'organising', 'failed']}},
                                               {'_id': 0, 'id': 1, 'title': 1, 'status': 1, 'message': 1}):
        uploads.append({'id': c['id'], 'kind': 'chapter_book', 'title': c['title'], 'state': c['status'], 'pages': 0, 'read_pages': 0,
                        'message': c.get('message', ''), 'active': c['status'] != 'failed'})
    from .duplicates import section_duplicates
    try:
        dupes = await section_duplicates(sid)
    except Exception:  # noqa: BLE001  a failed check never hides the mocks
        dupes = {}
    for it in items:
        if dupes.get(it['id']):
            it['duplicates'] = dupes[it['id']]
    return {'section': section_view(s), 'exam': exam_view(e), 'items': items, 'uploads': uploads, 'server_now': t}


async def publish_written(s, u, start=None, live_exam=False):
    from .content import publish_validated
    from .written import problems
    issues = problems(s)
    if issues:
        return issues[0]
    change = {}
    if start:
        change['start_at'] = start
        if live_exam:
            from .live_window import window
            change['competition'] = True
            change['last_start_at'], change['end_at'] = window(start, s['rules']['minutes'])
    if change:
        await sets.update_one({'id': s['id']}, {'$set': change, '$inc': {'revision': 1}})
    try:
        await publish_validated(s['id'], {'confirm': True}, u)
    except HTTPException as exc:
        return str(exc.detail)
    return None


async def set_status(s, body, u, t):
    """Returns why this test could not change, or None."""
    from .structure import locked, test_state
    state = test_state(s, t)
    if locked(s) and body.to in ('scheduled', 'library'):
        return 'Verified PYQ papers are locked: only Live or Off.'
    if body.to == 'library':
        from .library import archive_sets
        return None if await archive_sets([s['id']], u['id'], 'Moved to the Library from Master.') else 'This test cannot move to the Library.'
    if body.to == 'off':
        if state == 'draft':
            return 'Drafts are already hidden from students.'
        await sets.update_one({'id': s['id']}, {'$set': {'owner_unlive': True}})
        return None
    if state == 'ended':
        return 'This live exam has ended. Its results stay with the students.'
    if body.to == 'scheduled' and body.live_exam and await attempts.find_one({'set_id': s['id'], 'mode': {'$ne': 'preview'}}, {'_id': 1}):
        return 'Students already took this test, so it cannot become a live exam. Use a fresh mock.'
    start = body.at if body.to == 'scheduled' else None
    if state == 'draft':
        if s.get('written'):
            return await publish_written(s, u, start, body.live_exam)
        if s.get('chapter_book_id'):
            return 'chapter'
        return 'Open its upload to finish it first.'
    change, unset = {}, {'owner_unlive': ''}
    if s.get('live_enabled') is False:
        change['live_enabled'] = True
    if s.get('import_id') or s.get('chapter_book_id'):
        if start and s.get('end_at', 0) <= start:
            return 'Its access ends before that time.'
        if start or (s.get('start_at') or 0) > t:
            change['start_at'] = start or t
    elif start:
        change['start_at'] = start
        if body.live_exam:
            from .live_window import window
            change['competition'] = True
            change['last_start_at'], change['end_at'] = window(start, s['rules']['minutes'])
        elif s.get('competition'):
            change['competition'] = False
            unset.update(last_start_at='', end_at='')
    elif (s.get('start_at') or 0) > t:
        change['start_at'] = t
        if s.get('competition'):
            from .live_window import window
            change['last_start_at'], change['end_at'] = window(t, s['rules']['minutes'])
    # Only a timing change makes a new paper revision; switching On/Off never disturbs students who are about to start.
    update = {'$unset': unset, **({'$set': change} if change else {}), **({'$inc': {'revision': 1}} if 'start_at' in change else {})}
    await sets.update_one({'id': s['id']}, update)
    row = await sets.find_one({'id': s['id']}, {'_id': 0, 'questions': 0})
    if test_state(row, t) not in ('live', 'scheduled'):
        return 'It is still paused by its own upload settings. Open its upload to enable it.'
    return None


async def chapter_books_live(ids, wanted, u):
    """Chapter books publish as a whole; chapters not chosen stay Off until switched on."""
    from .chapter_books import publish_book, ChapterAction, books as chapter_records
    notes = []
    for cid in ids:
        r = await chapter_records.find_one({'id': cid}, {'_id': 0, 'revision': 1})
        if not r:
            notes.append('Its chapter upload was not found.')
            continue
        drafts = [x['id'] for x in await sets.find({'chapter_book_id': cid, 'status': 'draft'}, {'_id': 0, 'id': 1}).to_list(200)]
        try:
            await publish_book(cid, ChapterAction(revision=r['revision']), u)
        except HTTPException as exc:
            notes.append(str(exc.detail))
            continue
        rest = [x for x in drafts if x not in wanted]
        if rest:
            await sets.update_many({'id': {'$in': rest}}, {'$set': {'owner_unlive': True}})
    return notes


@router.post('/status')
async def change_status(body: StatusInput, bg: BackgroundTasks, u=Depends(owner)):
    from .structure import ADMIN_BASE
    t = await database_now()
    if body.to == 'scheduled' and (not body.at or body.at <= t + 30):
        raise HTTPException(422, 'Choose a future date and time.')
    done, skipped, chapter = 0, [], {}
    for item in [i for i in body.items if i.kind == 'set']:
        s = await sets.find_one({'$and': [{'id': item.id}, ADMIN_BASE]}, {'_id': 0})
        if not s:
            skipped.append({'id': item.id, 'title': '', 'reason': 'Not found here any more. Reload.'})
            continue
        kind = (await db.tejas_catalog_sections.find_one({'_id': s.get('catalog_section_id')}, {'kind': 1}) or {}).get('kind')
        reason = 'All India papers go live on their day. Give it a day instead.' if kind == 'aits' and body.to != 'library' else await set_status(s, body, u, t)
        if reason == 'chapter':
            if body.to == 'scheduled':
                reason = 'Tests from a chapter book go Live straight away. Choose Make Live.'
            else:
                chapter.setdefault(s['chapter_book_id'], set()).add(s['id'])
                continue
        if reason:
            skipped.append({'id': item.id, 'title': s.get('display_title') or s['title'], 'reason': reason})
        else:
            done += 1
    if chapter:
        notes = await chapter_books_live(list(chapter), {x for v in chapter.values() for x in v}, u)
        done += sum(len(v) for v in chapter.values()) if not notes else 0
        skipped += [{'id': '', 'title': 'Chapter book', 'reason': n} for n in notes]
    mocks = [i.id for i in body.items if i.kind == 'book_mock']
    if mocks:
        d, s2 = await mock_status(mocks, body, bg, u)
        done += d
        skipped += s2
    await audit(u['id'], f'Master status → {body.to}', ','.join(i.id for i in body.items[:20]), f'{done} changed, {len(skipped)} unchanged')
    words = {'live': 'Live', 'off': 'Off', 'scheduled': 'scheduled', 'library': 'moved to the Library'}[body.to]
    msg = f"{done} mock{'s' if done != 1 else ''} {'set ' if body.to in ('live', 'off') else ''}{words}."
    if body.to == 'live' and mocks:
        msg += ' Uploaded mocks appear for students in a moment.'
    return {'done': done, 'skipped': skipped, 'message': msg}


async def mock_status(ids, body, bg, u):
    from .book_imports import request_publication
    rows = await db.tejas_book_mocks.find({'_id': {'$in': ids}, 'archived': {'$ne': True}}, {'_id': 1, 'book_id': 1, 'label': 1, 'state': 1, 'set_id': 1, 'series_date': 1}).to_list(len(ids))
    books = {b['_id']: b for b in await db.tejas_books.find({'_id': {'$in': list({r['book_id'] for r in rows})}, 'removed': False, 'archived': {'$ne': True}},
                                                           {'payload.destination': 1}).to_list(500)}
    done, skipped, wanted = 0, [], {}
    for r in rows:
        why = None
        dest = (books.get(r['book_id']) or {}).get('payload', {}).get('destination') or {}
        if r['book_id'] not in books:
            why = 'Its upload is in the Library.'
        elif dest.get('series') and (body.to != 'library' or r.get('series_date')):
            why = 'All India papers go live on their day. Give it a day instead.' if body.to != 'library' else 'Free its day first.'
        elif r.get('set_id'):
            why = 'Already built. Reload.'
        elif body.to == 'off':
            why = 'Drafts are already hidden from students.'
        elif body.to in ('live', 'scheduled') and (r['state'] != 'ready'):
            why = 'Fix its marked questions first.' if r['state'] == 'held' else 'Still being checked.'
        if why:
            skipped.append({'id': r['_id'], 'title': r['label'], 'reason': why})
            continue
        if body.to == 'library':
            await db.tejas_book_mocks.update_one({'_id': r['_id'], 'set_id': None}, {'$set': {'archived': True, 'publish_requested': False}})
            done += 1
            continue
        await db.tejas_book_mocks.update_one({'_id': r['_id']}, {'$set': {'live_exam': body.to == 'scheduled' and body.live_exam}})
        wanted.setdefault(r['book_id'], set()).add(r['_id'])
    for bid, mids in wanted.items():
        done += await request_publication(bid, mids, body.at if body.to == 'scheduled' else None, bg, u)
    return done, skipped


@router.post('/uploads/{kind}/{id}/dismiss')
async def dismiss_upload(kind: Literal['book', 'chapter_book'], id: str, u=Depends(owner)):
    """A stopped or unreadable upload leaves the list for the Library; mocks already made from it stay where they are."""
    if kind == 'book':
        done = await db.tejas_books.update_one({'_id': id, 'removed': False, 'archived': {'$ne': True}},
            [{'$set': {'archived': True, 'archived_at': now(), 'paused_before_archive': '$paused', 'paused': True}}])
    else:
        done = await db.tejas_chapter_books.update_one({'id': id, 'archived': {'$ne': True}}, {'$set': {'archived': True, 'archived_at': now()}})
    if not done.modified_count:
        raise HTTPException(404, 'Upload not found. Reload.')
    await audit(u['id'], 'Upload moved to Library from Master', id, kind)
    return {'message': 'Upload moved to the Library. You can restore it from there.'}
