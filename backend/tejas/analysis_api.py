"""Analysis 2.0 API: one request opens the whole analysis. The website and the app use the same calls.
Only the attempt's owner, only after release; other students appear as a name, a score, totals and times, never as answers."""
import json, re, zlib
from datetime import datetime, timezone, timedelta
from bson import Binary
from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query, Response
from starlette.concurrency import run_in_threadpool
from .auth import current
from .attempts import owned
from .corrections import with_grade
from .db import db, attempts, now
from .live_window import answers_sealed
from .analysis import Group, rank_at, num, pct, FILTERS, ANALYSIS_VERSION
from .analysis_build import build_analysis
from .analysis_rules import RULES, VERSION, LEVELS
from .names import names_for
from .request_contracts import LearningsPayload
from . import class_stats, question_records
from tejas_core import score_attempt

router = APIRouter(prefix='/api', tags=['Analysis'])
cache = db.tejas_analysis
timelines = db.tejas_attempt_timeline
learnings = db.tejas_learnings
KEEP_DAYS = 14
TARGET = r'^(topper|top10|average|user:[0-9a-f]{16})$'
VERSION_NAME = r'^[A-Za-z0-9_-]{1,100}$'
LABELS = {'topper': 'Topper', 'top10': 'Top 10% ka average', 'average': 'Class ka average'}
ROW = {'_id': 0, 'user_id': 1, 'handle': 1, 'score': 1, 'submitted_at': 1, 'entry.o': 1, 'entry.secs': 1}
ORDER = [('score', -1), ('submitted_at', 1)]


async def released(id, u):
    a = await owned(id, u)
    if a.get('set_deleted'):
        raise HTTPException(410, 'Yeh test hata diya gaya hai. Sirf Score bacha hai.')
    if a['status'] != 'completed':
        raise HTTPException(409, 'Analysis test submit karne ke baad khulta hai.')
    if answers_sealed(a, a['_database_now']):
        raise HTTPException(403, 'Live exam abhi chal raha hai. Analysis sabka time khatam hone par khulega.')
    if not a.get('ledger'):
        raise HTTPException(409, 'Result abhi ban raha hai. Thodi der mein dobara kholo.', headers={'Retry-After': '2'})
    return a


async def class_state(a, u, bg, version):
    """(what the student is told about the class, class id or None)."""
    t, least = a['_database_now'], RULES['compare']['min_finishers']
    if version != 'original':
        return {'state': 'original_only'}, None
    if a.get('mode') not in class_stats.MODES:
        return {'state': 'none'}, None
    if u.get('access_type') != 'unverified_phone':
        return {'state': 'staff'}, None
    if a.get('competition_end', 0) > t:
        return {'state': 'sealed', 'release_at': a['competition_end']}, None
    cid = a.get('class_indexed') or await class_stats.record(a, t)
    if not cid:
        return {'state': 'none'}, None
    head = await class_stats.ensure(cid, u['id'], a['set_id'], bg)
    if not head or not head.get('computed_at') or head.get('rules_version') != VERSION:
        return {'state': 'preparing', 'min_finishers': least}, cid
    mine = await class_stats.entries.find_one({'_id': cid + ':' + u['id']}, {'_id': 0, 'updated_at': 1})
    included = bool(mine) and mine['updated_at'] <= head['computed_at']
    if not included and head.get('n', 0) < class_stats.SMALL_CLASS:
        return {'state': 'preparing', 'min_finishers': least}, cid
    return {'state': 'ready', 'ranked': True, 'n': head['n'] + (0 if included else 1), 'computed_at': head['computed_at'],
            'min_finishers': least, 'included': included}, cid


def class_subjects(groups, n, least):
    """Subject scores of the class average, the top 10% and the topper, next to the student's own on the Overview."""
    if n < 2:
        return None
    by = {k: {s['name']: s for s in (groups.get(k) or {}).get('subjects', [])} for k in ('average', 'top10', 'topper')}
    wide = n >= least
    return [{'name': name, 'topper': top['score'], 'average': by['average'][name]['score'] if wide and name in by['average'] else None,
             'top10': by['top10'][name]['score'] if wide and name in by['top10'] else None,
             'average_accuracy': by['average'][name]['accuracy'] if wide and name in by['average'] else None} for name, top in by['topper'].items()]


async def load(a, u, bg, version='original'):
    """(analysis, class id, cache key): built once and kept until the key, the class statistics, the time record or the display name change."""
    klass, cid = await class_state(a, u, bg, version)
    tl = await timelines.find_one({'_id': a['id']}, {'_id': 0, 'count': 1}) or {}
    name = u.get('display_name') or ''
    key = a['id'] + ':' + version
    # Chapter names from the join (All India papers, the owner's switch): '' while it is Off, and then nothing here differs from before.
    jod = await question_records.names_mark(a['series_id']) if a.get('series_id') else ''
    mark = [ANALYSIS_VERSION, VERSION, klass['state'], klass.get('computed_at', 0), tl.get('count', 0), name, klass.get('included', True)] + (['jod:' + jod] if jod else [])
    hit = await cache.find_one({'_id': key, 'user_id': u['id'], 'mark': mark}, {'_id': 0, 'z': 1})
    if hit:
        return json.loads(zlib.decompress(hit['z'])), cid, key
    stats = await class_stats.stats.find_one({'_id': cid}, {'_id': 0, 'groups': 0}) if klass['state'] == 'ready' else None
    graded = await with_grade(a, version)
    result = score_attempt(graded)
    if jod:
        names = await question_records.chapter_names([q['id'] for q in result['questions']])
        for q in result['questions']:
            if not q.get('topic') and names.get(q['id']):
                q['topic'] = names[q['id']]  # a label for this analysis only: the paper, the answers and the score are not written
    if stats:
        above = await class_stats.entries.find_one({'cohort_id': cid, 'score': {'$gt': result['summary']['score']}},
                                                   {'_id': 0, 'handle': 1, 'score': 1, 'user_id': 1}, sort=[('score', 1), ('submitted_at', 1)])
        if above:
            above_name = (await names_for([above['user_id']])).get(above['user_id'])
            klass['above'] = {'handle': above['handle'], 'score': above['score'], 'name': above_name or class_stats.learner(above['handle'])}
    events = (await timelines.find_one({'_id': a['id']}, {'_id': 0, 'events': 1}) or {}).get('events')
    hints = await class_stats.hints_for(a['set_id'])
    analysis = await run_in_threadpool(build_analysis, graded, result, stats, RULES, events, hints, klass, {'name': name})
    if stats and klass.get('ranked'):
        groups = (await class_stats.stats.find_one({'_id': cid}, {'_id': 0, 'groups.average.subjects': 1, 'groups.top10.subjects': 1, 'groups.topper.subjects': 1}) or {}).get('groups') or {}
        analysis['overview']['class_subjects'] = class_subjects(groups, stats['n'], RULES['compare']['min_finishers'])
    packed = Binary(zlib.compress(json.dumps(analysis, separators=(',', ':')).encode(), 6))  # about a tenth of the plain size
    await cache.update_one({'_id': key}, {'$set': {'attempt_id': a['id'], 'user_id': u['id'], 'mark': mark, 'z': packed,
                                                 'expires_at': datetime.now(timezone.utc) + timedelta(days=KEEP_DAYS)},
                                        '$unset': {'pdf': '', 'png': ''}}, upsert=True)
    return analysis, cid, key


def versus(you, them, kind, label, extra=None):
    """You against another student or a group: totals only, where the gap is biggest, and what the gap is made of."""
    theirs = {s['name']: s for s in them['subjects']}
    subjects, split = [], []
    for s in you['subjects']:
        o = theirs.get(s['name'])
        if not o:
            continue
        subjects.append({'name': s['name'], 'you': s['score'], 'them': o['score'], 'gap': num(o['score'] - s['score'])})
        mine = s['score'] / s['attempted'] if s['attempted'] else 0
        rate = o['score'] / o['attempted'] if o['attempted'] else 0
        # gap = (their extra attempts at their marks per attempt) + (your attempts at the difference in marks per attempt)
        split.append({'name': s['name'], 'volume': num((o['attempted'] - s['attempted']) * rate), 'quality': num(s['attempted'] * (rate - mine))})
    subjects.sort(key=lambda g: -g['gap'])
    levels = [{'level': l, 'you': you['difficulty'][l]['accuracy'], 'them': them['difficulty'][l]['accuracy']} for l in LEVELS if you['difficulty'][l]['count']]
    return {'available': True, 'kind': kind, 'label': label, 'profile': them, 'gap': num(them['score'] - you['score']),
            'by_subject': subjects, 'by_difficulty': levels, 'split': split,
            'split_total': {k: num(sum(s[k] for s in split)) for k in ('volume', 'quality')}, **(extra or {})}


def times_of(frame, qt):
    return {f['id']: t for f, t in zip(frame, qt)} if qt else None


async def compare_with(analysis, cid, target):
    klass, kind = analysis['class'], target.split(':')[0]
    off = lambda reason: {'available': False, 'kind': kind, 'reason': reason}
    if klass['state'] == 'sealed':
        return off('Compare result release hone ke baad khulega.')
    if klass['state'] != 'ready' or not cid:
        return off('Compare ke liye class ka data abhi taiyaar nahi hai. Thodi der mein dobara dekho.')
    stats = await class_stats.stats.find_one({'_id': cid}, {'_id': 0, 'q': 0})
    you, least = analysis['you'], RULES['compare']['min_finishers']
    if len(stats['frame']) != len(analysis['questions']) + analysis['paper']['not_opened_bonus']:
        return off('Is result ke liye Compare uplabdh nahi hai.')
    if target in LABELS:
        if target == 'topper' and stats['n'] < 2:
            return off('Abhi sirf aapne yeh paper diya hai. Doosra student aate hi Topper se Compare khul jaayega.')
        if target != 'topper' and stats['n'] < least:
            return off(f"Class aur Top 10% ka average kam se kam {least} students ke baad dikhta hai. Abhi {stats['n']} students ne diya hai.")
        group = dict(stats['groups'][target])
        return versus(you, group, target, LABELS[target], {'score': group['score'], 'times': times_of(stats['frame'], group.pop('qt', None)), 'n': group['n']})
    e = await class_stats.entries.find_one({'cohort_id': cid, 'handle': target[5:]}, {'entry': 1, 'score': 1, 'handle': 1, 'user_id': 1})
    if not e or len(e['entry']['o']) != len(stats['frame']):
        return off('Is student ka data abhi jud raha hai. Thodi der mein dobara dekho.' if stats.get('pending') else 'Yeh student is paper ke leaderboard mein nahi mila.')
    group = Group(stats['frame'], stats.get('duration') or 0).add(e['entry'])
    name = (await names_for([e['user_id']])).get(e['user_id']) or class_stats.learner(e['handle'])
    return versus(you, group.profile(you['maximum']), 'user', name,
                  {'score': e['score'], 'handle': e['handle'], 'times': times_of(stats['frame'], group.times()), **rank_at(stats, e['score'])})


async def notes_for(a, u):
    """This attempt's 3 learnings and the ones written after the mock before it."""
    mine = await learnings.find_one({'_id': a['id'], 'user_id': u['id']}, {'_id': 0, 'items': 1}) or {}
    before = await learnings.find_one({'user_id': u['id'], 'submitted_at': {'$lt': a.get('submitted_at') or 0}, 'items.0': {'$exists': True}},
                                      {'items': 1, 'title': 1}, sort=[('submitted_at', -1)])
    return {'mine': mine.get('items', []), 'previous': {'attempt_id': before['_id'], 'title': before.get('title'), 'items': before['items']} if before else None}


@router.get('/attempts/{id}/analysis')
async def read_analysis(id: str, bg: BackgroundTasks, mode: str = Query('personal', pattern='^(personal|comparative)$'),
                        compare: str = Query('topper', pattern=TARGET), score_version: str = Query('original', pattern=VERSION_NAME), u=Depends(current)):
    a = await released(id, u)
    analysis, cid, _ = await load(a, u, bg, score_version)
    if mode == 'comparative':
        analysis['compare'] = await compare_with(analysis, cid, compare)
    return {**analysis, 'view': mode, 'learnings': await notes_for(a, u), 'server_now': a['_database_now']}


@router.get('/attempts/{id}/analysis/questions')
async def analysis_questions(id: str, bg: BackgroundTasks, filter: str = Query('all', pattern='^(all|' + '|'.join(FILTERS) + ')$'),
                             score_version: str = Query('original', pattern=VERSION_NAME), u=Depends(current)):
    analysis, _, _ = await load(await released(id, u), u, bg, score_version)
    rows = [q for q in analysis['questions'] if filter == 'all' or FILTERS[filter](q)]
    return {'filter': filter, 'total': len(rows), 'time_data': analysis['time_data'], 'items': rows}


@router.put('/attempts/{id}/learnings')
async def save_learnings(id: str, data: LearningsPayload, u=Depends(current)):
    """Is test se 3 seekh: private to the student, shown again on the next mock."""
    a = await attempts.find_one({'id': id, 'user_id': u['id'], 'status': 'completed'}, {'_id': 0, 'title': 1, 'exam': 1, 'submitted_at': 1})
    if not a:
        raise HTTPException(404, 'Attempt not found.')
    items = [x for x in (' '.join(item.split()) for item in data.items) if x]
    await learnings.update_one({'_id': id}, {'$set': {'user_id': u['id'], 'title': a.get('title'), 'exam': a.get('exam'),
                                                     'submitted_at': a.get('submitted_at') or 0, 'items': items, 'updated_at': now()}}, upsert=True)
    await cache.update_many({'attempt_id': id}, {'$unset': {'pdf': ''}})
    return {'items': items}


def board_row(e, names, stats, me):
    o = e['entry']['o']
    right, wrong = o.count('c'), o.count('w')
    name = names.get(e['user_id'])
    return {'rank': rank_at(stats, e['score']).get('rank'), 'name': name or class_stats.learner(e['handle']), 'named': bool(name), 'handle': e['handle'],
            'score': e['score'], 'attempted': right + wrong, 'accuracy': pct(right, right + wrong), 'time': e['entry'].get('secs'), 'is_you': e['user_id'] == me}


@router.get('/attempts/{id}/leaderboard')
async def leaderboard(id: str, bg: BackgroundTasks, q: str = Query('', max_length=20), u=Depends(current)):
    """This paper's leaderboard: top 50, the students around you, and a search by name or rank. Names and totals only."""
    analysis, cid, _ = await load(await released(id, u), u, bg)
    klass = analysis['class']
    if klass['state'] != 'ready' or not cid:
        return {'state': klass['state'], 'n': 0, 'rows': [], 'around': [], 'found': [], 'release_at': klass.get('release_at')}
    E = class_stats.entries
    stats = await class_stats.stats.find_one({'_id': cid}, {'_id': 0, 'scores': 1, 'n': 1})
    top = await E.find({'cohort_id': cid}, ROW).sort(ORDER).limit(50).to_list(50)
    mine = await E.find_one({'cohort_id': cid, 'user_id': u['id']}, ROW)
    around = []
    if mine:
        s, t = mine['score'], mine['submitted_at']
        above = await E.find({'cohort_id': cid, '$or': [{'score': {'$gt': s}}, {'score': s, 'submitted_at': {'$lt': t}}]}, ROW).sort([('score', 1), ('submitted_at', -1)]).limit(5).to_list(5)
        below = await E.find({'cohort_id': cid, '$or': [{'score': {'$lt': s}}, {'score': s, 'submitted_at': {'$gt': t}}]}, ROW).sort(ORDER).limit(5).to_list(5)
        around = above[::-1] + [mine] + below
    found, term = [], ' '.join(q.split()).lower()
    if term.isdigit() and len(term) <= 6 and int(term) >= 1:
        found = await E.find({'cohort_id': cid}, ROW).sort(ORDER).skip(int(term) - 1).limit(1).to_list(1)
    elif term:
        code = re.fullmatch(r'(?:learner\s*)?([0-9a-f]{2,16})', term)
        if code:
            found = await E.find({'cohort_id': cid, 'handle': {'$regex': '^' + code.group(1)}}, ROW).limit(20).to_list(20)
        named = await db.tejas_phone_profiles.distinct('id', {'display_key': {'$regex': '^' + re.escape(term)}})
        if named:
            found += await E.find({'cohort_id': cid, 'user_id': {'$in': named[:500]}}, ROW).sort(ORDER).limit(20).to_list(20)
    names = await names_for([e['user_id'] for e in top + around + found])
    view = lambda items: [board_row(e, names, stats, u['id']) for e in items]
    return {'state': 'ready', 'n': stats['n'], 'title': analysis['title'], 'rows': view(top), 'around': view(around), 'found': view(found), 'query': term,
            'you': board_row(mine, names, stats, u['id']) if mine else None, 'min_finishers': klass['min_finishers']}


async def stored(key, field, make):
    """The file made once for this analysis; a changed analysis drops it."""
    hit = await cache.find_one({'_id': key, field: {'$exists': True}}, {'_id': 0, field: 1})
    if hit:
        return bytes(hit[field])
    data = await run_in_threadpool(make)
    await cache.update_one({'_id': key}, {'$set': {field: Binary(data)}})
    return data


@router.get('/attempts/{id}/analysis/report.pdf')
async def report_pdf(id: str, bg: BackgroundTasks, score_version: str = Query('original', pattern=VERSION_NAME), u=Depends(current)):
    from .analysis_pdf import render, file_name
    a = await released(id, u)
    analysis, _, key = await load(a, u, bg, score_version)
    notes = await notes_for(a, u)
    pdf = await stored(key, 'pdf', lambda: render(analysis, notes))
    return Response(pdf, media_type='application/pdf', headers={'Content-Disposition': f'attachment; filename="{file_name(analysis)}.pdf"', 'Cache-Control': 'private, no-store'})


@router.get('/attempts/{id}/analysis/share.png')
async def share_image(id: str, bg: BackgroundTasks, u=Depends(current)):
    from .analysis_pdf import share_png, file_name
    analysis, _, key = await load(await released(id, u), u, bg)
    png = await stored(key, 'png', lambda: share_png(analysis))
    return Response(png, media_type='image/png', headers={'Content-Disposition': f'inline; filename="{file_name(analysis)}.png"', 'Cache-Control': 'private, no-store'})


@router.get('/competitions/{id}/compare/{key}')
async def compare_learner(id: str, key: str, bg: BackgroundTasks, u=Depends(current)):
    """You against one student from this paper's leaderboard. Totals only: the other student's answers are never returned."""
    if not re.fullmatch('[0-9a-f]{16}', key):
        raise HTTPException(404, 'Yeh student is paper ke leaderboard mein nahi mila.')
    mine = await attempts.find_one({'set_id': id, 'user_id': u['id'], 'status': 'completed', 'mode': {'$in': list(class_stats.MODES)},
                                    'competition_end': {'$exists': True}}, {'_id': 0, 'id': 1})
    if not mine:
        raise HTTPException(404, 'Compare ke liye pehle yeh paper khud submit karna hoga.')
    analysis, cid, _ = await load(await released(mine['id'], u), u, bg)
    o = analysis['overview']
    return {'attempt_id': mine['id'], 'title': analysis['title'], 'exam': analysis['exam'], 'time_data': analysis['time_data'], 'copy': analysis['copy'],
            'class': analysis['class'], 'questions': analysis['questions'], 'you': {**analysis['you'], **{k: o.get(k) for k in ('rank', 'of', 'percentile')}},
            'compare': await compare_with(analysis, cid, 'user:' + key)}
