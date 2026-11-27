"""One question, one record (pocket C1a). Every question of the All India papers and of the chapter-wise books gets one record under
the address printed on it ('Source: AITS Mock 04 / Q68'). The paper's question and the chapter test's question sit on the same record
when the locks open: same kind, same answer, same subject, words alike. A lock that stays shut sends the question to the owner's list
with the reason; nothing is joined by a guess. Read from the Drafts the PDF reader already made: no AI.
Only this module's own collection is written; a paper, a test, a score or an attempt is never touched. A record stays when its upload goes."""
import collections, hashlib, re
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, ConfigDict
from pymongo import UpdateOne
from pymongo.errors import DuplicateKeyError
from starlette.concurrency import run_in_threadpool
from .auth import owner
from .db import db, now, uid, audit
from .book_store import identity
from . import question_link as L

router = APIRouter(prefix='/api/admin/links', tags=['Question links'])
OP, LEASE, SERIES = 'question-link:', 180, 'AITS Mock'   # SERIES: what a paper's own heading and number stand for when no address is printed on it
SIDE = {'paper': 'AITS paper', 'chapter': 'Chapter-wise'}
COUNTS = ('records', 'linked', 'paper', 'chapter', 'review', 'bare', 'gone', 'changed')
BOOK = {'payload.title': 1, 'payload.destination.series': 1, 'payload.destination.series_id': 1, 'payload.chapters': 1, 'archived': 1}
MOCK = {'book_id': 1, 'label': 1, 'order': 1, 'chapter': 1, 'archived': 1, 'set_id': 1,
        **{'questions.' + k: 1 for k in ('id', 'text', 'type', 'answer', 'original_number', 'number', 'subject')}}
BUSY = 'Jod abhi ban raha hai. Thodi der mein dobara dekhiye.'
NAME_FIELDS = {'qids': 1, 'seen': 1, 'state': 1, 'chapter_ok': 1, 'chapter.name': 1}
SHOW_TTL = 30   # seconds a server remembers the owner's switch before it asks the database again
_shown = {}


def _name(r):
    """The chapter name a record may show on its paper question, or '': joined now, or joined earlier and its chapter upload went away since."""
    return ((r.get('chapter') or {}).get('name') or '') if r.get('state') in ('linked', 'paper') and r.get('chapter_ok') is True else ''


def names_from(rows):
    """{question id: chapter name}. The record a question sits on now decides. A record it sat on before is asked only when it sits on
    none now: an attempt on a paper from before its corrected version."""
    live, old = {}, {}
    for r in rows:
        name = _name(r)
        for q in r.get('qids') or []:
            live[q] = name
        if name:
            for q in r.get('seen') or []:
                old.setdefault(q, name)
    return {**{q: n for q, n in old.items() if q not in live}, **{q: n for q, n in live.items() if n}}


class ShowChapters(BaseModel):
    model_config = ConfigDict(extra='forbid', strict=True)
    on: bool


def _forget(doc):
    """What a run takes off a record: last run's 'changed' mark; and a chapter learned from words that are no longer its words."""
    if 'changed' not in doc:
        return {'$unset': {'changed': ''}}
    if not doc['changed']['words'] or 'chapter' in doc:
        return {}
    return {'$unset': {k: '' for k in ('chapter', 'chapter_ok') if k not in doc}}   # never a field this same run also sets


def recs():
    return db.tejas_question_records


def ops():
    return db.tejas_operations


async def sources(slug):
    """The uploads of one exam that can carry an address: its All India papers and its chapter-wise books, oldest first."""
    out = {}
    async for b in db.tejas_books.find({'payload.destination.exam_slug': slug, 'removed': False}, BOOK).sort([('created_at', 1), ('_id', 1)]):
        p = b.get('payload') or {}
        dest = p.get('destination') or {}
        side = 'paper' if dest.get('series') else 'chapter' if p.get('chapters') else ''
        if side:
            out[b['_id']] = {'side': side, 'title': p.get('title') or '', 'archived': bool(b.get('archived')), 'series_id': dest.get('series_id') or '', 'rank': len(out)}
    return out


async def signature(books):
    """Changes when an upload of the exam, or anything in one of its Drafts, changed: the join is then older than what it was made from."""
    rows = [(m['_id'], m.get('revision', 0), m.get('generation', 1), bool(m.get('archived')), m.get('set_id') or '')
            async for m in db.tejas_book_mocks.find({'book_id': {'$in': list(books)}, 'deleted': {'$ne': True}}, {'revision': 1, 'generation': 1, 'archived': 1, 'set_id': 1}).sort('_id', 1)]
    return hashlib.sha1(repr((sorted((k, v['archived']) for k, v in books.items()), rows)).encode()).hexdigest()


def _where(c):
    name = (c.get('chapter') or {}).get('title') or c['label']
    return f"{SIDE[c['side']]} · {c['book'][:50]} · {name[:50]} · Q{c['number']}"


def _place(c):
    out = {k: c[k] for k in ('side', 'book_id', 'book', 'mock_id', 'label', 'qid', 'number', 'archived', 'set_id')}
    if c.get('chapter'):
        out['chapter'] = c['chapter']['name'] or c['chapter']['title']
    return out


def record(slug, key, claims):
    """One address and every printed copy found under it. The first copy (the paper's, when there is one) is what the others are held against."""
    series, mock, q = key
    first, problems, good = claims[0], [], [claims[0]]
    for c in claims[1:]:
        shut = L.locks(first['read'], c['read'])
        if not shut and first['subject'] and c['subject'] and L.letters(first['subject']) != L.letters(c['subject']):
            shut = {'code': 'subject', 'say': f"Pata wahi, par subject alag: {first['subject']} aur {c['subject']}."}
        if shut:
            problems.append({**shut, 'with': _where(c)})
        else:
            good.append(c)
    for c in claims:
        if c.get('own'):
            problems.append({'code': 'number', 'say': f"Paper mein yeh {c['own']} hai, par is par chhapa pata {c['printed']} hai.", 'with': _where(c)})
    sides, r = {c['side'] for c in claims}, first['read']
    doc = {'exam_slug': slug, 'series': series, 'mock': mock, 'q': q, 'address': first['printed'], 'type': r['type'], 'answer': r['answer'], 'value': r['value'][:300],
           'words_sha': hashlib.sha1(r['letters'].encode()).hexdigest(), 'text': r['words'][:8000], 'subject': next((c['subject'] for c in good if c['subject']), ''),
           'state': 'review' if problems else 'linked' if len(sides) == 2 else first['side'], 'problems': problems[:8], 'first': first['side'],
           'places': [_place(c) for c in claims][:40], 'qids': sorted({c['qid'] for c in claims if c['qid']})[:80],
           'has_paper': 'paper' in sides, 'has_chapter': 'chapter' in sides, 'paper_label': next((c['label'] for c in claims if c['side'] == 'paper'), '')}
    chapter = next((c['chapter'] for c in good if c.get('chapter')), None)
    if chapter:
        doc['chapter'] = chapter
    if doc['state'] != 'paper':
        doc['chapter_ok'] = doc['state'] == 'linked'   # the chapter was proven by open locks against the paper's copy; a paper-only record keeps what it had
    series_id = next((c['series_id'] for c in claims if c.get('series_id')), '')
    if series_id:
        doc['series_id'] = series_id
    return doc


def build(slug, books, mocks, prior, t):
    """({record id: fields}, what the screen shows) from the Drafts of one exam. Plain reading; the same Drafts always give the same records."""
    groups, bare, per = {}, 0, {b: {'mocks': 0, 'questions': 0, 'addressed': 0} for b in books}
    for m in sorted(mocks, key=lambda m: (books[m['book_id']]['rank'], m.get('order') or 0, m['_id'])):
        book, tally = books[m['book_id']], per[m['book_id']]
        side, ch = book['side'], m.get('chapter') or {}
        own = L.mock_number(m.get('label')) if side == 'paper' else None
        tally['mocks'] += 1
        for q in m.get('questions') or []:
            tally['questions'] += 1
            text = q.get('text') or ''
            n = next((v for v in (q.get('original_number'), q.get('number')) if isinstance(v, int) and not isinstance(v, bool)), None)
            found = L.address(text)
            if not found and own and n:
                found = (L.letters(SERIES), own, n, f'{SERIES} {own:02d} / Q{n}')   # a paper that prints no address: its own heading and number are its address
            if not found:
                bare += 1
                continue
            tally['addressed'] += 1
            c = {'side': side, 'book_id': m['book_id'], 'book': book['title'], 'mock_id': m['_id'], 'label': m.get('label') or '', 'qid': q.get('id') or '', 'number': n,
                 'archived': book['archived'] or bool(m.get('archived')), 'set_id': m.get('set_id'), 'printed': found[3], 'series_id': book['series_id'],
                 'subject': ((ch.get('subject') if side == 'chapter' else q.get('subject')) or '').strip(), 'read': L.read(text, q.get('type'), q.get('answer'))}
            if side == 'chapter':
                title = ch.get('title') or ''
                c['chapter'] = {'number': ch.get('number'), 'title': title[:120], 'subject': ch.get('subject') or '', 'name': L.chapter_name(text) or re.sub(r'^\d+[\s.:)-]*', '', title)[:120]}
            elif own and n and (own, n) != found[1:3]:
                c['own'] = f"{m.get('label')} / Q{n}"
            groups.setdefault(found[:3], []).append(c)
    docs, counts, rows = {}, collections.Counter(), {}
    for key, claims in groups.items():
        claims.sort(key=lambda c: c['side'] != 'paper')   # stable: the paper's copy first, then in the order the uploads came
        doc = record(slug, key, claims)
        rid = identity('question-record', slug, *key)
        was = prior.get(rid)
        # Held against what the same side printed last time: a paper arriving beside a chapter copy is not a change.
        if was and was.get('first') == doc['first'] and (was.get('words_sha'), was.get('type'), was.get('answer')) != (doc['words_sha'], doc['type'], doc['answer']):
            doc['changed'] = {'at': t, 'words': was.get('words_sha') != doc['words_sha'], 'type': was.get('type') or '', 'answer': was.get('answer') or ''}
            counts['changed'] += 1
        docs[rid] = doc
        counts[doc['state']] += 1
        if doc['has_paper']:
            row = rows.setdefault(key[:2], {'mock': key[1], 'label': doc['paper_label'] if L.mock_number(doc['paper_label']) == key[1] else '', 'questions': 0, 'linked': 0, 'review': 0})
            row['questions'] += 1
            row['linked'] += doc['state'] == 'linked'
            row['review'] += doc['state'] == 'review'
    summary = {'records': len(docs), 'bare': bare, **{k: counts[k] for k in ('linked', 'paper', 'chapter', 'review', 'changed')},
               'mocks': [rows[k] for k in sorted(rows)],
               'books': [{'title': b['title'], 'side': b['side'], 'archived': b['archived'], **per[i]} for i, b in books.items()]}
    return docs, summary


async def rebuild(slug, actor=''):
    """Reads every Draft of the exam and writes its records. One run at a time on every server; a second press is told so."""
    t, token, run = now(), uid(), uid()
    try:
        await ops().find_one_and_update({'_id': OP + slug, '$or': [{'lease_until': {'$lt': t}}, {'lease_until': {'$exists': False}}]},
                                        {'$set': {'lease': token, 'lease_until': t + LEASE}}, upsert=True)
    except DuplicateKeyError:
        raise HTTPException(409, BUSY) from None
    try:
        books = await sources(slug)
        mark = await signature(books)
        mocks = [m async for m in db.tejas_book_mocks.find({'book_id': {'$in': list(books)}, 'deleted': {'$ne': True}}, MOCK)]
        prior = {r['_id']: r async for r in recs().find({'exam_slug': slug}, {'words_sha': 1, 'type': 1, 'answer': 1, 'first': 1})}
        docs, summary = await run_in_threadpool(build, slug, books, mocks, prior, t)
        # 'changed' says what the last run found different; a run that finds nothing different takes the mark away.
        # 'seen': every question id a record ever had, so an attempt on a paper from before its corrected version still finds its record.
        writes = [UpdateOne({'_id': rid}, {'$set': {**doc, 'run': run, 'updated_at': t}, '$setOnInsert': {'created_at': t}, '$addToSet': {'seen': {'$each': doc['qids']}}, **_forget(doc)}, upsert=True)
                  for rid, doc in docs.items()]
        for i in range(0, len(writes), 500):
            await recs().bulk_write(writes[i:i + 500], ordered=False)
        # A record whose every printed copy went away (upload removed) stays, with its words, answer and chapter; only its places are emptied.
        await recs().update_many({'exam_slug': slug, 'run': {'$ne': run}, 'state': {'$ne': 'gone'}},
                                 {'$set': {'state': 'gone', 'places': [], 'qids': [], 'problems': [], 'has_paper': False, 'has_chapter': False, 'updated_at': t}, '$unset': {'changed': ''}})
        summary['gone'] = await recs().count_documents({'exam_slug': slug, 'state': 'gone'})
        rows = [r async for r in recs().find({'exam_slug': slug}, NAME_FIELDS).sort('_id', 1)]
        summary['named'] = sum(1 for r in rows if _name(r))
        names = hashlib.sha1(repr(sorted(names_from(rows).items())).encode()).hexdigest()   # changes only when a question's chapter name does
        await ops().update_one({'_id': OP + slug, 'lease': token}, {'$set': {'summary': summary, 'signature': mark, 'names_mark': names, 'ran_at': t, 'run': run,
                                                                             'took': round(now() - t, 2)}})
        _shown.clear()
        if actor:
            await audit(actor, 'Question records rebuilt', OP + slug, f"{summary['records']} records; {summary['linked']} joined; {summary['review']} for the owner to look at. No AI; no paper or test was changed.")
        return summary
    finally:
        await ops().update_one({'_id': OP + slug, 'lease': token}, {'$set': {'lease_until': 0}})


async def view(slug):
    from .structure import exams
    e = await exams.find_one({'_id': slug}, {'_id': 0, 'slug': 1, 'name': 1})
    if not e:
        raise HTTPException(404, 'Exam not found.')
    op = await ops().find_one({'_id': OP + slug}) or {}
    books = await sources(slug)
    s = op.get('summary') or {}
    rows = await recs().find({'exam_slug': slug, 'state': 'review'}, {'_id': 1, 'address': 1, 'subject': 1, 'problems': 1, 'places': 1}).sort([('mock', 1), ('q', 1)]).limit(50).to_list(50)
    review = [{'id': r['_id'], 'address': r.get('address', ''), 'subject': r.get('subject', ''),
               'problems': [{'say': p.get('say', ''), 'with': p.get('with', '')} for p in r.get('problems') or []],
               'places': [{'side': p.get('side'), 'book': p.get('book', ''), 'label': p.get('chapter') or p.get('label', ''), 'number': p.get('number')} for p in r.get('places') or []]} for r in rows]
    return {'exam': {'slug': slug, 'name': e.get('name', '')}, 'ran_at': op.get('ran_at'), 'took': op.get('took'),
            'fresh': bool(op.get('signature')) and op['signature'] == await signature(books), 'running': op.get('lease_until', 0) > now(),
            'sources': len(books), 'counts': {k: s.get(k, 0) for k in COUNTS}, 'mocks': s.get('mocks') or [],
            'books': s.get('books') or [{'title': b['title'], 'side': b['side'], 'archived': b['archived']} for b in books.values()],
            'review': review, 'review_more': max(0, s.get('review', 0) - len(review)),
            'named': s.get('named', 0), 'show_chapters': bool(op.get('show_chapters'))}


@router.get('/{slug}')
async def status(slug: str, u=Depends(owner)):
    return await view(slug)


@router.post('/{slug}/run')
async def run(slug: str, u=Depends(owner)):
    """"Jod banao": the records are made again from what the Drafts say now. Pressing it again changes nothing when nothing changed."""
    await view(slug)
    await rebuild(slug, u['id'])
    return await view(slug)


@router.put('/{slug}/analysis')
async def show(slug: str, body: ShowChapters, u=Depends(owner)):
    """The owner's switch (Off as it starts): chapter names from the join in the analysis of this exam's All India papers. A press that changes nothing writes nothing."""
    await view(slug)
    try:
        done = await ops().update_one({'_id': OP + slug, 'show_chapters': {'$ne': True} if body.on else True},
                                      {'$set': {'show_chapters': body.on, 'show_at': now(), 'show_by': u['id']}}, upsert=body.on)
        changed = bool(done.modified_count or done.upserted_id)
    except DuplicateKeyError:   # it is On already
        changed = False
    if changed:
        _shown.clear()
        await audit(u['id'], 'Chapter names in All India analysis ' + ('ON' if body.on else 'OFF'), OP + slug, 'Names and labels only; no score, rank, paper or attempt is changed.')
    return await view(slug)


async def names_mark(series_id):
    """'' while the owner's switch is Off for the exam of this series; else a mark that changes only when the chapter names change."""
    hit = _shown.get(series_id)
    if hit and hit[0] > now():
        return hit[1]
    cfg = await db.tejas_series.find_one({'_id': series_id}, {'exam_slug': 1}) or {}
    op = await ops().find_one({'_id': OP + cfg['exam_slug']}, {'show_chapters': 1, 'names_mark': 1}) if cfg.get('exam_slug') else None
    mark = ((op or {}).get('names_mark') or '') if (op or {}).get('show_chapters') else ''
    if len(_shown) > 500:
        _shown.clear()
    _shown[series_id] = (now() + SHOW_TTL, mark)
    return mark


async def chapter_names(ids):
    """{question id: chapter name} for the questions of a paper that are joined to their chapter-wise copy."""
    ids = list(ids)
    found = names_from([r async for r in recs().find({'$or': [{'qids': {'$in': ids}}, {'seen': {'$in': ids}}]}, NAME_FIELDS).sort('_id', 1)])
    return {q: found[q] for q in ids if q in found}
