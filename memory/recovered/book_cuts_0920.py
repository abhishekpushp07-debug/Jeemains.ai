"""PDF Engine 2.0: the saved cut of every question (its question picture and one picture per option).
Worked out once per page region and kept. No AI anywhere."""
import asyncio, time
from starlette.concurrency import run_in_threadpool
from .db import db, now
from .book_store import identity
from .book_pdf import run
from .book_cutter import CUT_VERSION

cuts = db.tejas_book_cuts
BATCH, LANES, SECONDS = 12, 3, 50
SHOWN = ('ok', 'manual', 'trim')


def slot(coverage_key):
    return identity('cut-slot', coverage_key)


def cut_key(sha, item):
    return identity('cut', CUT_VERSION, sha, item['action'], item['page'], item['rect'], ''.join(item['labels']), ''.join(item.get('typed') or []), sorted((item.get('boxes') or {}).items()))


def requests(q, regions, over):
    """Worker requests for one question. regions: [(page, rect, prints options)] in reading order."""
    mcq = q['type'] == 'mcq'
    options = list(q.get('options', {})) if mcq else []
    # An option the owner typed needs no picture, so it needs no box.
    drawn = [x for x in options if x not in q.get('typed_options', {})]
    marked = [i for i, r in enumerate(regions) if r[2]] if mcq else []
    at = marked[-1] if marked else len(regions) - 1
    items = []
    for i, (page, rect, _) in enumerate(regions):
        if i == at and over.get('mode') == 'boxes' and over.get('page') == page:
            items.append({'action': 'boxes', 'page': page, 'rect': rect, 'labels': drawn, 'boxes': over['boxes']})
        else:
            own = i == at and bool(options)
            items.append({'action': 'cut', 'page': page, 'rect': rect, 'labels': options if own else [], **({'typed': [x for x in options if x not in drawn]} if own and len(drawn) < len(options) else {})})
    return items, at, drawn


def assemble(sha, regions, items, at, drawn, over, found):
    out = {'status': 'trim', 'reason': '', 'arrangement': '', 'mode': over.get('mode', 'auto'), 'accept_outside': bool(over.get('accept_outside')),
           'region': {'page': regions[at][0], 'rect': regions[at][1]}, 'labels': drawn, 'parts': []}
    if out['mode'] == 'whole':
        return {**out, 'status': 'whole'}
    # A held cut keeps the boxes the engine got as far as drawing, so the fix tool starts from them.
    held = lambda reason, cut=None: {**out, 'status': 'held', 'reason': reason, 'parts': [],
                                     'draft': {k: v['rect'] for k, v in ((cut or {}).get('pieces') or {}).items()} or (cut or {}).get('draft') or {}}
    for i, item in enumerate(items):
        cut = found[cut_key(sha, item)]
        own = i == at and bool(item['labels'] or item['action'] == 'boxes')
        if i == at:
            # The printed boxes of the page, so the fix tool can pick a whole box with one tap.
            out['frames'] = cut.get('frames', [])
        if cut['status'] == 'held' or (own and cut['status'] not in ('ok', 'manual')):
            return held(cut.get('reason') or 'Page ka yeh hissa kat nahi paya.', cut if own else None)
        if own:
            if cut.get('outside') and not over.get('accept_outside'):
                return held('Is sawaal ka kuch chhapa hua hissa kisi bhi box me nahi aaya.', cut)
            out.update(status=cut['status'], arrangement=cut.get('arrangement', ''))
        out['parts'] += [{'part': k, 'page': item['page'], 'size': cut['size'], **cut['pieces'][k]} for k in ['q', *item['labels']] if k in cut['pieces']]
    out['parts'].sort(key=lambda p: p['part'] != 'q')
    if not any(p['part'] == 'q' for p in out['parts']):
        return held('Options ke upar kuch chhapa nahi hai, isliye sawaal ki picture nahi bani.')
    return out


async def work(source, group):
    try:
        return await run_in_threadpool(run, source, group)
    except ValueError as exc:
        return [{'error': str(exc)}] * len(group)


async def cut_mock(book, mock, questions, targets, source, deadline, keep_alive):
    """Sets q['cut'] on every question. False when the time for this pass ran out before every region was cut."""
    sha, plans, wanted = book.payload['sha256'], {}, {}
    for q in questions:
        over = mock.cuts.get(slot(q['coverage_key'])) or {}
        plans[q['id']] = (*requests(q, targets[q['id']], over), over)
        if over.get('mode') != 'whole':
            wanted.update({cut_key(sha, item): item for item in plans[q['id']][0]})
    found = {r['_id']: r['cut'] async for r in cuts.find({'_id': {'$in': list(wanted)}})}
    missing = [k for k in wanted if k not in found]
    while missing and time.monotonic() < deadline:
        chunk, missing = missing[:BATCH * LANES], missing[BATCH * LANES:]
        groups = [chunk[i:i + BATCH] for i in range(0, len(chunk), BATCH)]
        for group, results in zip(groups, await asyncio.gather(*(work(source, [wanted[k] for k in g]) for g in groups))):
            for key, r in zip(group, results):
                if r.get('cut'):
                    found[key] = r['cut']
                    await cuts.update_one({'_id': key}, {'$setOnInsert': {'book_id': book.id, 'cut': r['cut'], 'at': now()}}, upsert=True)
                else:
                    # A page that could not be opened is not remembered: the next check tries it again.
                    found[key] = {'status': 'held', 'reason': r.get('error') or 'Page ka yeh hissa padha nahi ja saka.', 'pieces': {}}
        await keep_alive()
    if missing:
        return False
    for q in questions:
        items, at, drawn, over = plans[q['id']]
        q['cut'] = assemble(sha, targets[q['id']], items, at, drawn, over, found)
    return True


def cut_summary(questions, confirmed):
    """The counts on a mock's row: cut cleanly, need the owner's eye, shown as one whole picture by the owner's choice."""
    held = sum(q['cut']['status'] == 'held' and q['coverage_key'] not in confirmed for q in questions)
    whole = sum(q['cut']['status'] == 'whole' or (q['cut']['status'] == 'held' and q['coverage_key'] in confirmed) for q in questions)
    return {'engine': CUT_VERSION, 'total': len(questions), 'clean': len(questions) - held - whole, 'held': held, 'whole': whole,
            'by_hand': sum(q['cut']['status'] == 'manual' for q in questions)}

