"""Owner Library: tests taken away from students, kept with every student's old score, restorable and downloadable."""
import json, logging, os, re, tempfile, zipfile
from datetime import datetime, timezone
from typing import Annotated
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
GUARD = {'test_kind': {'$ne': 'pyq'}, 'series_id': {'$exists': False}, 'series_import': {'$ne': True}}
CLEANUP_ID = 'library-2026-11-bitsat-and-jee-main-chapters'
CLEANUP_SECTIONS = ('bitsat:mocks', 'bitsat:chapters', 'jee-main:chapters')
CLEANUP_REASON = 'Moved to the Library to make way for new content. Students keep their old scores.'


class Payload(BaseModel):
    model_config = ConfigDict(extra='forbid', strict=True, allow_inf_nan=False)


class ArchiveInput(Payload):
    ids: list[Identity] = Field(default_factory=list, max_length=2000)
    section_id: str = Field(default='', max_length=100)
    reason: str = Field(default='', max_length=300)


class RestoreInput(Payload):
    ids: list[Identity] = Field(min_length=1, max_length=2000)


async def archive_sets(ids, actor, reason):
    ids = list(dict.fromkeys(ids))
    if not ids:
        return 0
    done = await sets.update_many({'id': {'$in': ids}, 'archived': {'$ne': True}, **GUARD},
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
    s = await section_doc(section_id)
    if s['kind'] == 'pyq':
        raise HTTPException(409, 'PYQ Papers are never moved to the Library.')
    e = await exams.find_one({'_id': s['exam_slug']}, {'_id': 0})
    ids = [x['id'] for x in await section_tests(s, e['key']) if x.get('test_kind') != 'pyq']
    tests = await archive_sets(ids, actor, reason)
    return {'tests': tests, 'uploads': await archive_sources(section_id, ids)}


async def restore_sets(ids):
    rows = await sets.find({'id': {'$in': ids}, 'archived': True}, {'_id': 0, 'id': 1, **{f: 1 for f, _, _ in SOURCES}}).to_list(2000)
    if not rows:
        return 0
    await sets.update_many({'id': {'$in': [r['id'] for r in rows]}}, {'$unset': {'archived': '', 'archived_at': '', 'archived_by': '', 'archived_reason': ''}})
    for field, name, key in SOURCES:
        owners = list({r[field] for r in rows if r.get(field)})
        if not owners:
            continue
        if name == 'tejas_books':
            change = [{'$set': {'paused': {'$ifNull': ['$paused_before_archive', False]}}}, {'$unset': ['archived', 'archived_at', 'paused_before_archive']}]
        else:
            change = {'$unset': {'archived': '', 'archived_at': ''}}
        await db[name].update_many({key: {'$in': owners}, 'archived': True}, change)
    return len(rows)


async def placed(rows):
    """Exam and section each archived test came from (older tests are placed by their kind)."""
    from .structure import sections, exams, legacy_kind
    names = {s['id']: s for s in await sections.find({}, {'_id': 0, 'id': 1, 'name': 1, 'exam_slug': 1}).to_list(2000)}
    slugs = {e['key']: e for e in await exams.find({}, {'_id': 0, 'slug': 1, 'key': 1, 'name': 1}).to_list(500)}
    out = []
    for r in rows:
        sid = r.get('catalog_section_id')
        if not sid and slugs.get(r.get('exam')) and legacy_kind(r):
            sid = f"{slugs[r['exam']]['slug']}:{legacy_kind(r)}"
        s = names.get(sid)
        out.append((sid if s else '', s['name'] if s else 'Not in any section', s['exam_slug'] if s else (slugs.get(r.get('exam')) or {}).get('slug', '')))
    return out


@router.get('/admin/library')
async def library(u=Depends(owner)):
    from .structure import FIELDS, test_view, exams
    from .canonical import database_now
    t = await database_now()
    rows = await sets.find({'archived': True}, {**FIELDS, 'archived_at': 1, 'archived_reason': 1}).sort('archived_at', -1).limit(3000).to_list(3000)
    taken = {r['_id']: r['n'] for r in await attempts.aggregate([{'$match': {'set_id': {'$in': [r['id'] for r in rows]}, 'mode': {'$ne': 'preview'}}},
                                                                  {'$group': {'_id': '$set_id', 'n': {'$sum': 1}}}]).to_list(None)}
    exam_names = {e['slug']: e['name'] for e in await exams.find({}, {'_id': 0, 'slug': 1, 'name': 1}).to_list(500)}
    items = []
    for r, (sid, sname, eslug) in zip(rows, await placed(rows)):
        items.append({**test_view(r, t), 'section_id': sid, 'section_name': sname, 'exam_slug': eslug, 'exam_name': exam_names.get(eslug, r.get('exam') or ''),
                      'archived_at': r.get('archived_at'), 'reason': r.get('archived_reason', ''), 'attempts': taken.get(r['id'], 0)})
    return {'items': items, 'total': len(items)}


@router.post('/admin/library/archive')
async def archive(body: ArchiveInput, u=Depends(owner)):
    if bool(body.ids) == bool(body.section_id):
        raise HTTPException(422, 'Choose some tests, or a whole section.')
    reason = body.reason.strip() or 'Moved to the Library by the owner.'
    if body.section_id:
        counts = await archive_section(body.section_id, u['id'], reason)
    else:
        pyq = await sets.count_documents({'id': {'$in': body.ids}, 'test_kind': 'pyq'})
        if pyq:
            raise HTTPException(409, 'PYQ papers are never moved to the Library.')
        counts = {'tests': await archive_sets(body.ids, u['id'], reason), 'uploads': 0}
    await audit(u['id'], 'Moved to Library', body.section_id or ','.join(body.ids[:20]), json.dumps(counts))
    return {**counts, 'message': f"{counts['tests']} test{'s' if counts['tests'] != 1 else ''} moved to the Library. Students' old scores are kept."}


@router.post('/admin/library/restore')
async def restore(body: RestoreInput, u=Depends(owner)):
    n = await restore_sets(body.ids)
    await audit(u['id'], 'Restored from Library', ','.join(body.ids[:20]), str(n))
    return {'restored': n, 'message': f"{n} test{'s' if n != 1 else ''} back in {'their' if n != 1 else 'its'} section."}


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


async def cleanup_once():
    """One-time move of BITSAT mocks + chapter-wise and JEE Main chapter-wise into the Library. PYQ is never touched."""
    t = now()
    try:
        await db.tejas_migrations.insert_one({'_id': CLEANUP_ID, 'state': 'running', 'lease_until': t + 600, 'started_at': t})
    except DuplicateKeyError:
        taken = await db.tejas_migrations.update_one({'_id': CLEANUP_ID, 'state': 'running', 'lease_until': {'$lt': t}}, {'$set': {'lease_until': t + 600}})
        if not taken.modified_count:
            return None
    try:
        from .structure import sections
        counts = {}
        for sid in CLEANUP_SECTIONS:
            if await sections.find_one({'_id': sid}):
                counts[sid] = await archive_section(sid, 'system', CLEANUP_REASON)
        await db.tejas_migrations.update_one({'_id': CLEANUP_ID}, {'$set': {'state': 'done', 'finished_at': now(), 'counts': counts}})
        await audit('system', 'One-time Library cleanup', CLEANUP_ID, json.dumps(counts))
        return counts
    except Exception:
        logging.getLogger(__name__).exception('Library cleanup failed; it retries on the next start.')
        await db.tejas_migrations.update_one({'_id': CLEANUP_ID}, {'$set': {'lease_until': 0}})
        return None
