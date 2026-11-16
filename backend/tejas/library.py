"""Owner Library: tests taken away from students, kept with every student's old score, restorable and downloadable."""
import json, logging, os, re, tempfile, zipfile
from datetime import datetime, timezone
from typing import Annotated, Literal
from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import FileResponse
from pydantic import BaseModel, ConfigDict, Field
from pymongo.errors import DuplicateKeyError
from starlette.background import BackgroundTask
from starlette.concurrency import run_in_threadpool
from .auth import owner
from .db import db, sets, attempts, now, audit
from tejas_storage import get_object

router = APIRouter(prefix='/api', tags=['Library'])
Identity = Annotated[str, Field(min_length=1, max_length=100)]
# set field, source collection, key field in that collection
SOURCES = (('book_import_id', 'tejas_books', '_id'), ('chapter_book_id', 'tejas_chapter_books', 'id'), ('import_id', 'tejas_imports', 'id'))
# Verified PYQ papers never leave; PYQ papers made in Master can.
GUARD = {'$or': [{'test_kind': {'$ne': 'pyq'}}, {'master_pyq': True}], 'series_id': {'$exists': False}, 'series_import': {'$ne': True}}
CLEANUP_ID = 'library-2026-11-bitsat-and-jee-main-chapters'
CLEANUP_SECTIONS = ('bitsat:mocks', 'bitsat:chapters', 'jee-main:chapters')
CLEANUP_REASON = 'Moved to the Library to make way for new content. Students keep their old scores.'
FRESH_ID = 'library-2026-11-fresh-start-keep-jee-main-pyq'
FRESH_REASON = 'Fresh start: cleared for new chapter-wise PYQ and All India Test Series uploads. Students keep their old scores.'
KEEP_SECTION = 'jee-main:pyq'
RAPID = re.compile(r'rapid\s*-?\s*fire', re.I)
# A series paper's day, kept with it in the Library so a restore can put it back on that day.
SERIES_FIELDS = ('series_id', 'series_date', 'series_window', 'series_pattern', 'start_at', 'end_at')


class Payload(BaseModel):
    model_config = ConfigDict(extra='forbid', strict=True, allow_inf_nan=False)


class ArchiveInput(Payload):
    ids: list[Identity] = Field(default_factory=list, max_length=2000)
    section_id: str = Field(default='', max_length=100)
    reason: str = Field(default='', max_length=300)


class UploadRef(Payload):
    kind: Literal['book', 'chapter_book', 'import', 'book_mock']
    id: Identity


class RestoreInput(Payload):
    ids: list[Identity] = Field(default_factory=list, max_length=2000)
    uploads: list[UploadRef] = Field(default_factory=list, max_length=500)


class DeleteInput(RestoreInput):
    confirm: Literal['DELETE']


UPLOADS = {'book': ('tejas_books', '_id'), 'chapter_book': ('tejas_chapter_books', 'id'), 'import': ('tejas_imports', 'id')}
FIELD = {'book': 'book_import_id', 'chapter_book': 'chapter_book_id', 'import': 'import_id'}
BOOK_PARTS = ('tejas_book_pages', 'tejas_book_page_history', 'tejas_book_parts', 'tejas_book_mocks', 'tejas_book_allowances', 'tejas_book_supplements')


async def archive_sets(ids, actor, reason, guard=GUARD):
    ids = list(dict.fromkeys(ids))
    if not ids:
        return 0
    done = await sets.update_many({'id': {'$in': ids}, 'archived': {'$ne': True}, **guard},
        {'$set': {'archived': True, 'archived_at': now(), 'archived_by': actor, 'archived_reason': reason[:300]},
         '$unset': {'replace_pending': ''}})
    return done.modified_count


async def archive_sources(section_id, set_ids):
    """Uploads aimed at the section, and older uploads whose every test is now in the Library."""
    t = now()
    stamp = {'archived': True, 'archived_at': t}
    n = (await db.tejas_books.update_many({'payload.destination.section_id': section_id, 'removed': False, 'archived': {'$ne': True}},
        [{'$set': {**stamp, 'paused_before_archive': '$paused', 'paused': True}}])).modified_count
    for name in ('tejas_chapter_books', 'tejas_imports'):
        n += (await db[name].update_many({'destination.section_id': section_id, 'archived': {'$ne': True}}, {'$set': stamp})).modified_count
    for field, name, key in SOURCES:
        owners = set(await sets.distinct(field, {'id': {'$in': set_ids}, field: {'$nin': [None, '']}}))
        if not owners:
            continue
        busy = set(await sets.distinct(field, {field: {'$in': list(owners)}, 'archived': {'$ne': True}, 'status': {'$ne': 'withdrawn'}}))
        done = owners - busy
        if not done:
            continue
        change = [{'$set': {**stamp, 'paused_before_archive': '$paused', 'paused': True}}] if name == 'tejas_books' else {'$set': stamp}
        n += (await db[name].update_many({key: {'$in': list(done)}, 'archived': {'$ne': True}}, change)).modified_count
    return n


async def archive_section(section_id, actor, reason):
    from .structure import section_doc, exams, section_tests
    from .structure import locked
    s = await section_doc(section_id)
    if s['kind'] == 'pyq':
        raise HTTPException(409, 'A whole PYQ type is never moved to the Library. Move your own PYQ papers one by one.')
    e = await exams.find_one({'_id': s['exam_slug']}, {'_id': 0})
    ids = [x['id'] for x in await section_tests(s, e['key']) if not locked(x)]
    tests = await archive_sets(ids, actor, reason)
    return {'tests': tests, 'uploads': await archive_sources(section_id, ids)}


async def restore_uploads(refs):
    mocks = [r.id for r in refs if r.kind == 'book_mock']
    n = (await db.tejas_book_mocks.update_many({'_id': {'$in': mocks}, 'archived': True}, {'$set': {'archived': False}})).modified_count if mocks else 0
    for kind, (name, key) in UPLOADS.items():
        ids = [r.id for r in refs if r.kind == kind]
        if not ids:
            continue
        if name == 'tejas_books':
            change = [{'$set': {'paused': {'$ifNull': ['$paused_before_archive', False]}, 'restored_at': now()}}, {'$unset': ['archived', 'archived_at', 'paused_before_archive']}]
        else:
            change = {'$unset': {'archived': '', 'archived_at': ''}}
        n += (await db[name].update_many({key: {'$in': ids}, 'archived': True}, change)).modified_count
    return n


async def archived_uploads(rows):
    """Uploads moved to the Library that have no test of their own in it (their mocks were never published)."""
    from .structure import sections, exams
    exam_names = {e['slug']: e['name'] for e in await exams.find({}, {'_id': 0, 'slug': 1, 'name': 1}).to_list(500)}
    known = {s['id']: f"{exam_names.get(s['exam_slug'], '')} › {s['name']}" for s in await sections.find({}, {'_id': 0, 'id': 1, 'name': 1, 'exam_slug': 1}).to_list(2000)}
    where = lambda d: ' › '.join(x for x in (d.get('exam_name'), d.get('section_name')) if x) or known.get(d.get('section_id'), '')
    linked = {f: {r.get(f) for r in rows if r.get(f)} for f, _, _ in SOURCES}
    out = []
    for b in await db.tejas_books.find({'archived': True, 'removed': False}, {'_id': 1, 'payload.title': 1, 'payload.destination': 1, 'archived_at': 1}).to_list(500):
        if b['_id'] not in linked['book_import_id']:
            out.append({'kind': 'book', 'id': b['_id'], 'title': b['payload']['title'], 'place': where(b['payload'].get('destination') or {}), 'archived_at': b.get('archived_at')})
    titles = {b['_id']: b['payload'] for b in await db.tejas_books.find({'removed': False, 'archived': {'$ne': True}}, {'_id': 1, 'payload.title': 1, 'payload.destination': 1}).to_list(5000)}
    for m in await db.tejas_book_mocks.find({'archived': True, 'deleted': {'$ne': True}, 'set_id': None, 'book_id': {'$in': list(titles)}}, {'_id': 1, 'book_id': 1, 'label': 1}).to_list(2000):
        out.append({'kind': 'book_mock', 'id': m['_id'], 'title': m['label'], 'place': where(titles[m['book_id']].get('destination') or {}), 'archived_at': None})
    for name, kind, field in (('tejas_chapter_books', 'chapter_book', 'chapter_book_id'), ('tejas_imports', 'import', 'import_id')):
        for r in await db[name].find({'archived': True}, {'_id': 0, 'id': 1, 'title': 1, 'destination': 1, 'archived_at': 1}).to_list(500):
            if r['id'] not in linked[field]:
                out.append({'kind': kind, 'id': r['id'], 'title': r.get('title', ''), 'place': where(r.get('destination') or {}), 'archived_at': r.get('archived_at')})
    return out


async def restore_sets(ids):
    """Back where they were; a series paper goes back on its day if that day is still free, otherwise without a day."""
    if not ids:
        return 0, 0
    rows = await sets.find({'id': {'$in': ids}, 'archived': True}, {'_id': 0, 'id': 1, 'library_series': 1, **{f: 1 for f, _, _ in SOURCES}}).to_list(2000)
    if not rows:
        return 0, 0
    dayless = 0
    from .series_admin import dates
    ranges = {c['_id']: set(dates(c)) for c in await db.tejas_series.find({}, {'first_date': 1, 'days': 1}).to_list(200)}
    for r in rows:
        day = r.get('library_series') or {}
        if not day:
            continue
        # Back on its day only if the day still belongs to the series and nobody else has it; otherwise it waits without a day.
        free = day.get('series_date') in ranges.get(day.get('series_id'), ()) and not await sets.find_one({'series_id': day.get('series_id'), 'series_date': day['series_date'], 'id': {'$ne': r['id']}}, {'_id': 1})
        try:
            await sets.update_one({'id': r['id']}, {'$set': day, '$unset': {'library_series': ''}} if free else {'$unset': {'library_series': ''}})
        except DuplicateKeyError:
            free = False
            await sets.update_one({'id': r['id']}, {'$unset': {'library_series': ''}})
        dayless += not free
    await sets.update_many({'id': {'$in': [r['id'] for r in rows]}}, {'$unset': {'archived': '', 'archived_at': '', 'archived_by': '', 'archived_reason': ''}})
    for field, name, key in SOURCES:
        owners = list({r[field] for r in rows if r.get(field)})
        if not owners:
            continue
        if name == 'tejas_books':
            change = [{'$set': {'paused': {'$ifNull': ['$paused_before_archive', False]}, 'restored_at': now()}}, {'$unset': ['archived', 'archived_at', 'paused_before_archive']}]
        else:
            change = {'$unset': {'archived': '', 'archived_at': ''}}
        await db[name].update_many({key: {'$in': owners}, 'archived': True}, change)
    return len(rows), dayless


async def placed(rows):
    """Exam and section each archived test came from (older tests are placed by their kind, series papers by their series)."""
    from .structure import sections, exams, legacy_kind
    names = {s['id']: s for s in await sections.find({}, {'_id': 0, 'id': 1, 'name': 1, 'exam_slug': 1}).to_list(2000)}
    slugs = {e['key']: e for e in await exams.find({}, {'_id': 0, 'slug': 1, 'key': 1, 'name': 1}).to_list(500)}
    series = {c['_id']: c.get('section_id') for c in await db.tejas_series.find({}, {'section_id': 1}).to_list(200)}
    out = []
    for r in rows:
        sid = r.get('catalog_section_id') or series.get((r.get('library_series') or {}).get('series_id') or r.get('series_id'))
        if not sid and slugs.get(r.get('exam')) and legacy_kind(r):
            sid = f"{slugs[r['exam']]['slug']}:{legacy_kind(r)}"
        s = names.get(sid)
        out.append((sid if s else '', s['name'] if s else 'Not in any mock type', s['exam_slug'] if s else (slugs.get(r.get('exam')) or {}).get('slug', '')))
    return out


@router.get('/admin/library')
async def library(u=Depends(owner)):
    from .structure import FIELDS, test_view, exams, sections
    from .canonical import database_now
    t = await database_now()
    rows = await sets.find({'archived': True}, {**FIELDS, 'archived_at': 1, 'archived_reason': 1, 'library_series': 1}).sort('archived_at', -1).limit(3000).to_list(3000)
    taken = {r['_id']: r['n'] for r in await attempts.aggregate([{'$match': {'set_id': {'$in': [r['id'] for r in rows]}, 'mode': {'$ne': 'preview'}}},
                                                                  {'$group': {'_id': '$set_id', 'n': {'$sum': 1}}}]).to_list(None)}
    exam_rows = await exams.find({}, {'_id': 0, 'slug': 1, 'name': 1, 'order': 1}).sort('order', 1).to_list(500)
    exam_names = {e['slug']: e['name'] for e in exam_rows}
    kinds = {s['id']: s['kind'] for s in await sections.find({}, {'_id': 0, 'id': 1, 'kind': 1}).to_list(2000)}
    items = []
    for r, (sid, sname, eslug) in zip(rows, await placed(rows)):
        items.append({**test_view(r, t), 'section_id': sid, 'section_name': sname, 'section_kind': kinds.get(sid, 'other'), 'exam_slug': eslug,
                      'exam_name': exam_names.get(eslug, r.get('exam') or ''), 'archived_at': r.get('archived_at'), 'reason': r.get('archived_reason', ''),
                      'attempts': taken.get(r['id'], 0), 'series_date': (r.get('library_series') or {}).get('series_date')})
    fresh = await db.tejas_migrations.find_one({'_id': FRESH_ID, 'state': 'done'}, {'_id': 0, 'finished_at': 1, 'counts': 1})
    return {'items': items, 'total': len(items), 'uploads': await archived_uploads(rows), 'exams': [{'slug': e['slug'], 'name': e['name']} for e in exam_rows],
            'attempts_kept': sum(taken.values()), 'fresh_start': fresh}


@router.post('/admin/library/archive')
async def archive(body: ArchiveInput, u=Depends(owner)):
    if bool(body.ids) == bool(body.section_id):
        raise HTTPException(422, 'Choose some tests, or a whole section.')
    reason = body.reason.strip() or 'Moved to the Library by the owner.'
    if body.section_id:
        counts = await archive_section(body.section_id, u['id'], reason)
    else:
        if await sets.count_documents({'id': {'$in': body.ids}, 'test_kind': 'pyq', 'master_pyq': {'$ne': True}}):
            raise HTTPException(409, 'Verified PYQ papers are never moved to the Library.')
        counts = {'tests': await archive_sets(body.ids, u['id'], reason), 'uploads': 0}
    await audit(u['id'], 'Moved to Library', body.section_id or ','.join(body.ids[:20]), json.dumps(counts))
    return {**counts, 'message': f"{counts['tests']} test{'s' if counts['tests'] != 1 else ''} moved to the Library. Students' old scores are kept."}


@router.post('/admin/library/restore')
async def restore(body: RestoreInput, u=Depends(owner)):
    if not body.ids and not body.uploads:
        raise HTTPException(422, 'Choose what to restore.')
    n, dayless = await restore_sets(body.ids)
    k = await restore_uploads(body.uploads)
    await audit(u['id'], 'Restored from Library', ','.join(body.ids[:20] + [r.id for r in body.uploads[:20]]), f'{n} tests, {k} uploads')
    message = f"{n} test{'s' if n != 1 else ''} back where {'they' if n != 1 else 'it'} came from." if body.ids else f"{k} upload{'s' if k != 1 else ''} back in {'their' if k != 1 else 'its'} mock type."
    if dayless:
        message += f" {dayless} series paper{'s' if dayless != 1 else ''} came back without a day because the day is taken: give {'them' if dayless != 1 else 'it'} a free day in the series."
    return {'restored': n, 'uploads': k, 'without_day': dayless, 'message': message}


@router.post('/admin/library/delete')
async def delete(body: DeleteInput, u=Depends(owner)):
    if not body.ids and not body.uploads:
        raise HTTPException(422, 'Choose what to delete.')
    await check_uploads(body.uploads)
    n, gone = await delete_sets(body.ids)
    k = await delete_uploads(body.uploads) + gone
    await audit(u['id'], 'Deleted from Library', ','.join(body.ids[:20] + [r.id for r in body.uploads[:20]]), f'{n} tests, {k} uploads')
    parts = [f"{n} test{'s' if n != 1 else ''}"] if n or not k else []
    parts += [f"{k} upload{'s' if k != 1 else ''}"] if k else []
    return {'deleted': n, 'uploads': k, 'message': ' and '.join(parts) + " deleted for good. Students keep their score lines."}


async def drop_source(name, key, sid):
    """An upload's records leave the database. The platform file store keeps the original file bytes (it has no delete)."""
    if name == 'tejas_books':
        for part in BOOK_PARTS:
            await db[part].delete_many({'book_id': sid})
        await db.tejas_jobs.delete_many({'set_id': sid, 'kind': 'book_step', 'status': {'$ne': 'running'}})
    await db[name].delete_one({key: sid})


async def delete_sets(ids):
    """Library tests leave for good; each attempt keeps its score line. A source upload in the Library that no test uses any more goes too."""
    from .canonical import database_now
    rows = await sets.find({'id': {'$in': ids}, 'archived': True}, {'_id': 0, 'id': 1, **{f: 1 for f, _, _ in SOURCES}}).to_list(3000)
    keep = [r['id'] for r in rows]
    if not keep:
        return 0, 0
    t = await database_now()
    if await attempts.find_one({'set_id': {'$in': keep}, 'status': 'active', '$or': [{'deadline': 0}, {'deadline': {'$gt': t}}]}, {'_id': 1}):
        raise HTTPException(409, 'A student is still writing one of these tests. Try again when their time is up.')
    await attempts.update_many({'set_id': {'$in': keep}}, {'$set': {'set_deleted': True, 'set_deleted_at': now()}})
    for name in ('tejas_saved_tests', 'tejas_question_solutions', 'tejas_versions'):
        await db[name].delete_many({'set_id': {'$in': keep}})
    await db.tejas_book_mocks.update_many({'set_id': {'$in': keep}}, {'$set': {'archived': True, 'deleted': True}})
    await sets.delete_many({'id': {'$in': keep}, 'archived': True})
    gone = 0
    for field, name, key in SOURCES:
        for sid in {r[field] for r in rows if r.get(field)}:
            if not await sets.find_one({field: sid}, {'_id': 1}) and await db[name].find_one({key: sid, 'archived': True}, {'_id': 1}):
                await drop_source(name, key, sid)
                gone += 1
    return len(keep), gone


async def check_uploads(refs):
    for r in refs:
        if r.kind != 'book_mock' and await sets.find_one({FIELD[r.kind]: r.id, 'archived': {'$ne': True}}, {'_id': 1}):
            raise HTTPException(409, 'Some tests made from this upload are still in Master. Move them to the Library first, then delete.')


async def delete_uploads(refs):
    mocks = [r.id for r in refs if r.kind == 'book_mock']
    n = (await db.tejas_book_mocks.update_many({'_id': {'$in': mocks}, 'archived': True, 'set_id': None}, {'$set': {'deleted': True}})).modified_count if mocks else 0
    for r in refs:
        if r.kind == 'book_mock':
            continue
        name, key = UPLOADS[r.kind]
        if not await db[name].find_one({key: r.id, 'archived': True}, {'_id': 1}):
            continue
        await delete_sets(await sets.distinct('id', {FIELD[r.kind]: r.id}))
        if await db[name].find_one({key: r.id}, {'_id': 1}):
            await drop_source(name, key, r.id)
        n += 1
    return n


def safe(text):
    return re.sub(r'[^A-Za-z0-9 ._()-]+', '-', str(text or 'untitled')).strip(' .-')[:80] or 'untitled'


def build_zip(rows, where, sources):
    tmp = tempfile.NamedTemporaryFile(prefix='library-', suffix='.zip', delete=False)
    manifest = []
    with zipfile.ZipFile(tmp, 'w', zipfile.ZIP_DEFLATED) as z:
        for r, (sid, sname, eslug) in zip(rows, where):
            path = f"tests/{safe(eslug or r.get('exam'))}/{safe(sname)}/{int(r.get('catalog_order') or 0):03d} {safe(r.get('display_title') or r['title'])} [{r['id'][:8]}].json"
            z.writestr(path, json.dumps(r, default=str, ensure_ascii=False, indent=1))
            manifest.append({'id': r['id'], 'title': r.get('display_title') or r['title'], 'exam': r.get('exam'), 'section': sname, 'file': path})
        missing = []
        for kind, title, path in sources:
            try:
                z.writestr(f'originals/{kind}/{safe(title)}{os.path.splitext(path)[1] or ".pdf"}', get_object(path), compress_type=zipfile.ZIP_STORED)
            except Exception:
                missing.append(title)
        z.writestr('manifest.json', json.dumps({'exported_at': datetime.now(timezone.utc).isoformat(), 'tests': manifest, 'originals_unavailable': missing}, indent=1))
        z.writestr('README.txt', 'jeelive.ai Library export.\n\ntests/: every question, option, key, solution and source-page reference, one JSON file per test.\n'
                   'originals/: the PDFs or workbooks they were made from.\nRestore from Super Admin > Library; nothing here is shown to students.\n')
    tmp.close()
    return tmp.name


@router.get('/admin/library/export')
async def export(section_id: str = Query('', max_length=100), u=Depends(owner)):
    rows = await sets.find({'archived': True}, {'_id': 0, 'publication_pending': 0}).limit(3000).to_list(3000)
    where = await placed(rows)
    if section_id:
        keep = [i for i, w in enumerate(where) if w[0] == section_id]
        rows, where = [rows[i] for i in keep], [where[i] for i in keep]
    if not rows:
        raise HTTPException(404, 'Nothing in the Library here yet.')
    sources = []
    ids = lambda field: list({r[field] for r in rows if r.get(field)})
    for b in await db.tejas_books.find({'_id': {'$in': ids('book_import_id')}}, {'payload.title': 1, 'payload.source_path': 1}).to_list(500):
        if b['payload'].get('source_path'):
            sources.append(('books', b['payload']['title'], b['payload']['source_path']))
    for c in await db.tejas_chapter_books.find({'id': {'$in': ids('chapter_book_id')}}, {'_id': 0, 'title': 1, 'source.path': 1}).to_list(500):
        if (c.get('source') or {}).get('path'):
            sources.append(('chapter-books', c['title'], c['source']['path']))
    for i in await db.tejas_imports.find({'id': {'$in': ids('import_id')}}, {'_id': 0, 'title': 1, 'sources': 1}).to_list(500):
        for s in i.get('sources', []):
            if s.get('path'):
                sources.append(('papers', f"{i['title']} - {s.get('kind', 'file')}", s['path']))
    path = await run_in_threadpool(build_zip, rows, where, sources)
    await audit(u['id'], 'Library exported', section_id or 'all', f'{len(rows)} tests, {len(sources)} originals')
    stamp = datetime.now(timezone.utc).strftime('%Y-%m-%d')
    return FileResponse(path, media_type='application/zip', filename=f'jeelive-library-{stamp}.zip', background=BackgroundTask(os.unlink, path))


async def run_once(mid, job, label):
    """Runs a one-time clean-up on exactly one instance; a crashed run is picked up again on a later start."""
    t = now()
    try:
        await db.tejas_migrations.insert_one({'_id': mid, 'state': 'running', 'lease_until': t + 600, 'started_at': t})
    except DuplicateKeyError:
        taken = await db.tejas_migrations.update_one({'_id': mid, 'state': 'running', 'lease_until': {'$lt': t}}, {'$set': {'lease_until': t + 600}})
        if not taken.modified_count:
            return None
    try:
        counts = await job()
        await db.tejas_migrations.update_one({'_id': mid}, {'$set': {'state': 'done', 'finished_at': now(), 'counts': counts}})
        await audit('system', label, mid, json.dumps(counts))
        return counts
    except Exception:
        logging.getLogger(__name__).exception('%s failed; it retries on the next start.', label)
        await db.tejas_migrations.update_one({'_id': mid}, {'$set': {'lease_until': 0}})
        return None


async def cleanup_job():
    from .structure import sections
    counts = {}
    for sid in CLEANUP_SECTIONS:
        if await sections.find_one({'_id': sid}):
            counts[sid] = await archive_section(sid, 'system', CLEANUP_REASON)
    return counts


async def cleanup_once():
    """One-time move of BITSAT mocks + chapter-wise and JEE Main chapter-wise into the Library. PYQ is never touched."""
    return await run_once(CLEANUP_ID, cleanup_job, 'One-time Library cleanup')


async def clear_series(actor, reason):
    """Every series paper goes to the Library with its day noted; every series keeps its dates for new papers."""
    t, n = now(), 0
    async for s in sets.find({'series_id': {'$nin': [None, '']}, 'archived': {'$ne': True}}, {'_id': 0, 'id': 1, **{k: 1 for k in SERIES_FIELDS}}):
        day = {k: s[k] for k in SERIES_FIELDS if s.get(k) is not None}
        n += (await sets.update_one({'id': s['id'], 'archived': {'$ne': True}}, {
            '$set': {'archived': True, 'archived_at': t, 'archived_by': actor, 'archived_reason': reason, 'library_series': day},
            '$unset': {k: '' for k in SERIES_FIELDS}, '$inc': {'revision': 1}})).modified_count
    waiting = await db.tejas_book_mocks.update_many({'set_id': None, 'series_date': {'$nin': [None, '']}},
        {'$set': {'series_date': None, 'series_id': None, 'publish_requested': False, 'release_at': None}, '$inc': {'revision': 1}})
    return {'papers': n, 'waiting_days_freed': waiting.modified_count}


async def clear_uploads(kept):
    """Every upload goes to the Library, except the ones the kept JEE Main PYQ papers came from. Waiting go-Live times are cancelled."""
    t = now()
    stamp, spare = {'archived': True, 'archived_at': t}, {f: list({r[f] for r in kept if r.get(f)}) for f, _, _ in SOURCES}
    n = (await db.tejas_books.update_many({'removed': False, 'archived': {'$ne': True}, '_id': {'$nin': spare['book_import_id']},
        'payload.destination.section_id': {'$ne': KEEP_SECTION}}, [{'$set': {**stamp, 'paused_before_archive': '$paused', 'paused': True}}])).modified_count
    books = await db.tejas_books.distinct('_id', {'archived': True, 'archived_at': t})
    await db.tejas_book_mocks.update_many({'book_id': {'$in': books}, 'set_id': None}, {'$set': {'publish_requested': False, 'release_at': None}})
    for name, field in (('tejas_chapter_books', 'chapter_book_id'), ('tejas_imports', 'import_id')):
        n += (await db[name].update_many({'archived': {'$ne': True}, 'id': {'$nin': spare[field]}, 'destination.section_id': {'$ne': KEEP_SECTION}}, {'$set': stamp})).modified_count
    return n


async def fresh_start(actor='system'):
    """Only JEE Main PYQ stays for students; every other test, series paper and upload goes to the Library. Rapid Fire is never touched."""
    counts = {'series': await clear_series(actor, FRESH_REASON)}
    rows = await sets.find({'archived': {'$ne': True}, 'qa_only': {'$ne': True}}, {'_id': 0, 'id': 1, 'exam': 1, 'test_kind': 1, 'catalog_section_id': 1,
                           'chapter_book_id': 1, 'full_length': 1, 'series_id': 1, **{f: 1 for f, _, _ in SOURCES}}).to_list(None)
    where = await placed(rows)
    pyq = [sid == KEEP_SECTION for _, (sid, _, _) in zip(rows, where)]
    rapid = [bool(RAPID.search(f"{r.get('exam') or ''} {r.get('test_kind') or ''}")) for r in rows]
    keep = [a or b for a, b in zip(pyq, rapid)]
    counts['tests'] = await archive_sets([r['id'] for r, k in zip(rows, keep) if not k], actor, FRESH_REASON, guard={})
    counts['kept'], counts['rapid_fire_kept'] = sum(pyq), sum(rapid)
    counts['uploads'] = await clear_uploads([r for r, k in zip(rows, keep) if k])
    return counts


async def fresh_start_once():
    return await run_once(FRESH_ID, fresh_start, 'Fresh start: only JEE Main PYQ kept for students')


async def run_cleanups():
    await cleanup_once()
    await fresh_start_once()
