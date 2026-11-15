"""Chapter-wise PDFs in Master: see how a PDF was split into chapters, rename them, pick subjects, or mark where each chapter starts."""
import re
from typing import Literal
from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Response
from pydantic import Field
from starlette.concurrency import run_in_threadpool
from .auth import owner
from .db import db, audit
from .master import Payload
from .book_store import load_book, lock_book, save_book, unlock, mocks_for, original, normalized
from .book_imports import dispatch
from .book_pdf import inspect
from .chapter_reader import labelled, match_subject

router = APIRouter(prefix='/api/admin/master/chapters', tags=['Master'])
SOURCES = {'you': 'Chosen by you', 'upload': 'Chosen at upload', 'pdf': 'Printed in the PDF', 'book': 'Named on the cover or file name', 'name': 'From the chapter name'}
Q1 = re.compile(r'(?m)^\s*(?:Q(?:uestion)?\.?\s*)?0?1\s*[.):](?:\s|$)')
KEY_PAGE = re.compile(r'(?mi)^\s*(?:answers?\s*keys?|answer\s*sheet|answers|(?:detailed\s+|worked\s+)?solutions?)\s*$')


class ChapterName(Payload):
    label: str = Field(min_length=1, max_length=120)
    title: str = Field(min_length=2, max_length=120)
    subject: str = Field(default='', max_length=40)


class ChapterNames(Payload):
    items: list[ChapterName] = Field(min_length=1, max_length=300)


class ChapterRow(Payload):
    title: str = Field(min_length=2, max_length=120)
    subject: str = Field(default='', max_length=40)


class StartRow(Payload):
    page: int = Field(ge=1, le=100000)
    chapter: int = Field(ge=0, le=299)
    role: Literal['question', 'key', 'solution']


class Starts(Payload):
    chapters: list[ChapterRow] = Field(min_length=1, max_length=300)
    starts: list[StartRow] = Field(min_length=1, max_length=1000)


async def chapter_book(id, u):
    book = await load_book(id, u)
    if not book.payload.get('chapters') or (await db.tejas_books.find_one({'_id': id, 'archived': True}, {'_id': 1})):
        raise HTTPException(404, 'This chapter-wise upload is not available.')
    return book


async def exam_subjects(book):
    dest = book.payload['destination']
    return (await db.tejas_catalog_exams.find_one({'_id': dest['exam_slug']}, {'_id': 0, 'subjects': 1}) or {}).get('subjects') or []


def first(pages):
    return min(pages) if pages else None


def chapter_view(m):
    c = m.chapter or {}
    state = 'live' if m.published_generation else 'library' if m.archived else m.state
    return {'id': m.id, 'label': m.label, 'title': c.get('title') or m.label, 'number': c.get('number') or m.order, 'subject': c.get('subject', ''),
            'subject_from': SOURCES.get(c.get('subject_from'), ''), 'count': len(m.questions), 'state': state, 'to_fix': len(m.issues),
            'question_page': first(m.pages.get('question')), 'key_page': first(m.pages.get('key')), 'solution_page': first(m.pages.get('solution')),
            'last_page': max([n for v in m.pages.values() for n in v] or [0]) or None}


def detected_starts(chapters):
    """The split as read now, in the same shape the owner edits."""
    out = []
    for i, c in enumerate(chapters):
        q = c['question_page']
        if q:
            out.append({'page': q, 'chapter': i, 'role': 'question'})
        for role in ('key', 'solution'):
            page = c[role + '_page']
            if page and q and page > q:
                out.append({'page': page, 'chapter': i, 'role': role})
    return sorted(out, key=lambda s: (s['page'], s['chapter']))


@router.get('/{id}')
async def read_chapters(id: str, u=Depends(owner)):
    book = await chapter_book(id, u)
    p, dest = book.payload, book.payload['destination']
    mocks = await mocks_for(book)
    chapters = [chapter_view(m) for m in mocks]
    # Pages where a question 1 is printed (not answer-key or solution pages): usually where a chapter starts.
    restarts = [r['number'] async for r in db.tejas_book_pages.find({'book_id': id}, {'number': 1, 'text': 1}).sort('number', 1)
                if Q1.search(r.get('text') or '') and not KEY_PAGE.search(r.get('text') or '')][:300]
    plan = p.get('chapter_plan') or []
    if plan:
        order = list(dict.fromkeys(e['label'] for e in plan))
        rows = [next(e for e in plan if e['label'] == lab) for lab in order]
        draft = {'chapters': [{'title': r['title'], 'subject': r.get('subject', '')} for r in rows],
                 'starts': [{'page': e['page'], 'chapter': order.index(e['label']), 'role': e['role']} for e in plan]}
    else:
        draft = {'chapters': [{'title': c['title'], 'subject': c['subject']} for c in chapters], 'starts': detected_starts(chapters)}
    return {'id': id, 'title': p['title'], 'state': book.state, 'pages': p.get('pages', 0), 'read_pages': p.get('read_pages', 0), 'message': p.get('message', ''),
            'subject_mode': p.get('subject', ''), 'subjects': await exam_subjects(book), 'exam': {'name': dest['exam_name'], 'slug': dest['exam_slug']},
            'section': {'id': dest['section_id'], 'name': dest['section_name']}, 'plan_source': p.get('plan_source') if plan else 'headings',
            'chapters': chapters, 'restarts': restarts, 'draft': draft, 'locked': any(m.published_generation for m in mocks),
            'reading': book.state in ('received', 'reading', 'matching'), 'bookmarks': len(p.get('bookmarks') or [])}


@router.get('/{id}/asset/page/{number}')
async def page_thumb(id: str, number: int, u=Depends(owner)):
    book = await chapter_book(id, u)
    if not book.payload.get('source_path') or not 1 <= number <= book.payload.get('pages', 0):
        raise HTTPException(404, 'Page not found.')
    data = await run_in_threadpool(inspect, await original(book), 'thumb', number)
    return Response(data['image_bytes'], media_type='image/png', headers={'Cache-Control': 'private, max-age=600'})


@router.put('/{id}/details')
async def save_details(id: str, body: ChapterNames, bg: BackgroundTasks, u=Depends(owner)):
    book = await chapter_book(id, u)
    allowed = await exam_subjects(book)
    book, token = await lock_book(id)
    try:
        mocks = {normalized(m.label): m for m in await mocks_for(book)}
        changes = dict(book.payload.get('chapter_overrides') or {})
        for item in body.items:
            m = mocks.get(normalized(item.label))
            if not m:
                raise HTTPException(404, 'A chapter changed while you were editing. Reload.')
            if m.published_generation:
                continue
            subject = match_subject(item.subject, allowed)
            if item.subject and not subject:
                raise HTTPException(422, f"Choose one of this exam's subjects for {item.title}.")
            changes[normalized(item.label)] = {'title': ' '.join(item.title.split()), 'subject': subject}
        book.payload['chapter_overrides'] = changes
        book.state = 'matching'
        await save_book(book, token)
        await audit(u['id'], 'Chapter names and subjects saved', id, f'{len(body.items)} chapters')
    finally:
        await unlock(book, token)
    await dispatch(book, bg)
    return {'message': 'Saved. Checking the chapters again…'}


async def reread(book, token, note):
    """Read every page again from the start; drafts made from the old split are replaced."""
    if book.state == 'uploading':
        raise HTTPException(409, 'Finish sending the PDF first.')
    if any(m.published_generation for m in await mocks_for(book)):
        raise HTTPException(409, 'Some chapters from this PDF are already Live, so its split is fixed. Upload a corrected PDF with Replace instead.')
    await db.tejas_book_pages.delete_many({'book_id': book.id, 'provenance.kind': {'$ne': 'ai_proposal'}})
    await db.tejas_book_mocks.delete_many({'book_id': book.id, 'published_generation': 0})
    book.payload.update(read_pages=0, message=note)
    book.payload.pop('chapter_overrides', None)
    book.state, book.paused = 'reading', False
    await save_book(book, token)


@router.put('/{id}/starts')
async def save_starts(id: str, body: Starts, bg: BackgroundTasks, u=Depends(owner)):
    book = await chapter_book(id, u)
    allowed = await exam_subjects(book)
    chapters = []
    for c in body.chapters:
        subject = match_subject(c.subject, allowed)
        if c.subject and not subject:
            raise HTTPException(422, f"Choose one of this exam's subjects for {c.title}.")
        chapters.append({'title': ' '.join(c.title.split()), 'subject': subject})
    starts = list({(s.page, s.chapter, s.role): s.model_dump() for s in body.starts}.values())
    if any(s['page'] > book.payload.get('pages', 0) for s in starts) or any(s['chapter'] >= len(chapters) for s in starts):
        raise HTTPException(422, 'A start points to a page or chapter that does not exist.')
    if {s['chapter'] for s in starts if s['role'] == 'question'} != set(range(len(chapters))):
        raise HTTPException(422, 'Every chapter needs the page where its questions start.')
    book, token = await lock_book(id)
    try:
        await reread(book, token, 'Reading the chapters you marked…')
        book.payload.update(chapter_plan=labelled(chapters, starts), plan_source='owner', single_checked=True)
        await save_book(book, token)
        await audit(u['id'], 'Chapter starts marked', id, f'{len(chapters)} chapters, {len(starts)} starts')
    finally:
        await unlock(book, token)
    await dispatch(book, bg)
    return {'message': f'Reading {len(chapters)} chapters again from the pages you marked.'}


@router.delete('/{id}/starts')
async def clear_starts(id: str, bg: BackgroundTasks, u=Depends(owner)):
    book = await chapter_book(id, u)
    if not book.payload.get('chapter_plan'):
        raise HTTPException(409, 'This PDF is already split by its printed headings.')
    book, token = await lock_book(id)
    try:
        await reread(book, token, 'Reading the chapters from the printed headings again…')
        book.payload.pop('chapter_plan', None)
        book.payload.pop('plan_source', None)
        book.payload['single_checked'] = False
        await save_book(book, token)
        await audit(u['id'], 'Chapter starts cleared', id, 'Back to printed headings and bookmarks')
    finally:
        await unlock(book, token)
    await dispatch(book, bg)
    return {'message': 'Reading the PDF again by itself.'}
