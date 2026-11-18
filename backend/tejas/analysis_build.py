"""Analysis v2 builder: the whole analysis JSON from one graded attempt, its time record and the class statistics.
Pure: no database, no clock and no AI in here, so the website, the app and the PDF always show the same numbers."""
import math
from collections import Counter
from .analysis import (ANALYSIS_VERSION, PACE_POINTS, Group, clock, stretches, visits, entry_of, frame_for, rows_of, rank_at,
                       performance, potential, next_three, journey, class_view, num, pct)
from .analysis_rules import RULES, VERSION, TAGS, LEVELS, COPY
from .scoring import canonical


def look_of(r, seen):
    """Which visit the first answer came in (1 = on the first look)."""
    if r['at'] < 0 or not seen:
        return None
    for i, v in enumerate(seen):
        if v['end'] + 5 >= r['at']:
            return i + 1
    return len(seen)


def ledger(rows, summary):
    """Marks ka hisaab: earned, cut, and left behind in wrong and unanswered questions."""
    negative = -sum(r['marks'] for r in rows if r['marks'] < 0)
    return {'earned': num(sum(r['marks'] for r in rows if r['marks'] > 0)), 'negative': num(negative),
            'left_wrong': num(sum(r['pos'] for r in rows if r['outcome'] == 'incorrect')),
            'left_skipped': num(sum(r['pos'] for r in rows if r['outcome'] == 'skipped')),
            'net': summary['score'], 'maximum': summary['maximum'], 'no_negative': num(summary['score'] + negative)}


def verdict(you, led, pot, timed):
    """One line that says where most marks went, from this attempt's own numbers."""
    acc, wrong, skipped = you['accuracy'], you['incorrect'], you['skipped']
    if not you['attempted']:
        return {'tone': 'mute', 'section': 'qs', 'text': 'Is attempt mein koi jawab nahi diya gaya. Agli baar pakke sawaal sabse pehle karo.'}
    if not wrong and not skipped:
        return {'tone': 'good', 'section': 'time', 'text': f"{led['maximum']} mein se {led['net']}: har sawaal sahi. Ab speed par kaam karo."}
    head = f'Accuracy {acc}% zabardast thi, lekin ' if acc >= 85 else f'Accuracy {acc}% theek rahi, ' if acc >= 60 else f'Accuracy sirf {acc}% rahi: '
    careless = next(s for s in pot['steps'] if s['key'] == 'careless')
    lost_wrong = led['negative'] + led['left_wrong']
    if led['left_skipped'] >= lost_wrong:
        return {'tone': 'warn', 'section': 'time' if timed else 'performance',
                'text': head + f"{skipped} sawaal chhoot gaye. Sabse zyada marks ({led['left_skipped']}) yahin reh gaye."}
    if timed and careless['marks'] * 2 >= lost_wrong:
        return {'tone': 'bad', 'section': 'quality',
                'text': head + f"{len(careless['questions'])} Careless galti se {careless['marks']} marks gaye. Jaldbaazi sabse mehngi padi."}
    return {'tone': 'bad' if acc < 60 else 'warn', 'section': 'potential',
            'text': head + f"{wrong} galat jawab se {led['negative']} marks kate aur {led['left_wrong']} marks reh gaye."}


def distribution(stats, score, extra=0):
    """Everyone's scores in 10 bands, with the band this student stands in."""
    scores = [(s, c) for s, c in stats.get('scores') or []] + ([(score, 1)] if extra else [])
    n = sum(c for _, c in scores)
    if n < 2:
        return None
    low, high = min(0, min(s for s, _ in scores)), max(stats.get('maximum') or 0, max(s for s, _ in scores))
    width = max(1, (high - low) / 10)
    bins = []
    for i in range(10):
        a, b = low + i * width, low + (i + 1) * width
        inside = lambda s: a <= s and (s < b or (i == 9 and s <= b))
        bins.append({'from': round(a), 'to': round(b), 'count': sum(c for s, c in scores if inside(s)), 'you': inside(score)})
    run, median = 0, None
    for s, c in sorted(scores):
        run += c
        if run * 2 >= n:
            median = s
            break
    return {'bins': bins, 'n': n, 'average': num(sum(s * c for s, c in scores) / n), 'median': num(median), 'top': num(max(s for s, _ in scores))}


def weak_chapters(rows, table):
    """Chapters by the marks that went in wrong and unanswered questions."""
    by = {}
    for r, t in zip(rows, table):
        if not t['topic'] or r['outcome'] not in ('incorrect', 'skipped'):
            continue
        g = by.setdefault((r['subject'], t['topic']), {'subject': r['subject'], 'name': t['topic'], 'wrong': 0, 'skipped': 0, 'lost': 0, 'questions': []})
        wrong = r['outcome'] == 'incorrect'
        g['wrong' if wrong else 'skipped'] += 1
        g['lost'] += r['pos'] - r['neg'] if wrong else r['pos']
        g['questions'].append(r['id'])
    return sorted(({**g, 'lost': num(g['lost'])} for g in by.values()), key=lambda g: -g['lost'])


def _close(items):
    c = sum(r['outcome'] == 'correct' for r in items)
    return {'count': len(items), 'correct': c, 'accuracy': pct(c, len(items)), 'time': round(sum(r['time'] or 0 for r in items)), 'questions': [r['id'] for r in items]}


def time_more(rows, look, entry, you):
    """Off-screen time, answers given on the first look against answers given after coming back, and where the time went against the paper's weight."""
    groups = {'first': [], 'return': []}
    for r in rows:
        if look.get(r['id']) and r['outcome'] in ('correct', 'incorrect'):
            groups['first' if look[r['id']] == 1 else 'return'].append(r)
    on = entry.get('on') or 0
    total = sum(g['maximum'] for g in you['subjects']) or 1
    return {'off_screen': max(0, entry['secs'] - on), 'first_look': {k: _close(v) for k, v in groups.items()},
            'share': [{'name': g['name'], 'time_pct': pct(g['time'] or 0, on), 'weight_pct': pct(g['maximum'], total), 'score': g['score'], 'maximum': g['maximum']} for g in you['subjects']]}


def last_stretch(rows, entry, rules=RULES):
    """Accuracy in the last 20% of the time used against the rest: only when both sides have enough answers."""
    x = rules['extra']
    cut = entry['secs'] * (1 - x['last_share'])
    answered = [r for r in rows if r['at'] >= 0 and r['outcome'] in ('correct', 'incorrect')]
    late, early = [r for r in answered if r['at'] >= cut], [r for r in answered if r['at'] < cut]
    if len(late) < x['last_min'] or len(early) < x['last_min']:
        return None
    return {'from': round(cut), 'early': _close(early), 'late': _close(late)}


def answer_changes(rows, by, first):
    """What changing an answer did: wrong to right, right to wrong, wrong to wrong, and answers cleared."""
    groups, delta = {k: [] for k in ('w2r', 'r2w', 'w2w', 'r2s', 'w2s')}, 0
    for r in rows:
        q = by[r['id']]
        was, final = (first.get(r['id']) or {}).get('normalized_value', ''), q.get('normalized_response') or ''
        if r['outcome'] not in ('correct', 'incorrect', 'skipped') or not was or was == final:
            continue
        try:
            right = was in {canonical(v, q['type']) for v in (q.get('accepted_answers') or [q.get('answer')])}
        except ValueError:
            continue
        if not final:
            key, d = ('r2s', -r['pos']) if right else ('w2s', -r['neg'])
        elif r['outcome'] == 'correct':
            key, d = 'w2r', r['pos'] - r['neg']
        else:
            key, d = ('r2w', r['neg'] - r['pos']) if right else ('w2w', 0)
        groups[key].append(r['id'])
        delta += d
    return {'groups': groups, 'marks': num(delta), 'total': sum(len(v) for v in groups.values())}


def streaks(rows):
    """Longest run of right and of wrong answers, in the order the student actually answered."""
    best, run, last = {'correct': 0, 'incorrect': 0}, 0, None
    for r in sorted((r for r in rows if r['at'] >= 0 and r['outcome'] in best), key=lambda r: r['at']):
        run = run + 1 if r['outcome'] == last else 1
        last = r['outcome']
        best[last] = max(best[last], run)
    return best if last else None


def pace_split(rows, duration):
    out = {k: [0] * (PACE_POINTS + 1) for k in ('correct', 'incorrect')}
    if not duration:
        return None
    for r in rows:
        if r['at'] >= 0 and r['outcome'] in out:
            out[r['outcome']][min(PACE_POINTS, math.ceil(r['at'] * PACE_POINTS / duration))] += 1
    for series in out.values():
        for i in range(1, len(series)):
            series[i] += series[i - 1]
    return out


def build_analysis(attempt, result, stats=None, rules=RULES, events=None, hints=None, klass=None, student=None):
    a, summary, questions = attempt, result['summary'], result['questions']
    by = {q['id']: q for q in questions}
    klass = klass or {'state': 'none'}
    extra = 0 if klass.get('included', True) else 1
    minutes = (a.get('rules') or {}).get('minutes') or 0
    start, end = clock(a)
    duration = round(minutes * 60) or round(end - start)
    st = stretches(events, set(by), start, end, rules['stretch_cap'])
    timed = bool(st)
    entry = entry_of(a, questions, by, st, summary)
    frame = (stats or {}).get('frame')
    if not frame or [f['id'] for f in frame] != [q['id'] for q in questions]:
        stats, frame = None, frame_for(questions, None, minutes, a['rules'], hints, rules)
    least = rules['compare']['min_finishers']
    qstats = stats['q'] if stats and stats['n'] >= least else {}
    rows = [r for r in rows_of(entry, frame, rules) if r['o'] != 'u']
    vs = visits(st)
    vq = {}
    for v in vs:
        vq.setdefault(v['q'], []).append(v)
    look = {r['id']: look_of(r, vq.get(r['id'])) for r in rows}
    first = a.get('first_answers') or {}
    table = []
    for r in rows:
        q = by[r['id']]
        label = lambda v, q=q: (q.get('source_option_labels') or {}).get(v, v)
        was, final = (first.get(r['id']) or {}).get('normalized_value', ''), q.get('normalized_response') or ''
        table.append({'id': r['id'], 'number': q['number'], 'subject': r['subject'], 'topic': q.get('topic') or '', 'type': q['type'],
                      'difficulty': r['level'], 'difficulty_source': r['ls'], 'response': label(final),
                      'answer': ', '.join(str(label(v)) for v in (q.get('accepted_answers') or [q.get('answer')])),
                      'outcome': r['outcome'], 'marks': q['marks'], 'pos': r['pos'], 'neg': r['neg'], 'time': r['time'], 'par': num(r['par']),
                      'par_source': r['ps'], 'par_n': r['pn'], 'tag': r['tag'], 'marked': bool(q.get('marked')), 'seen': r['seen'],
                      'at': r['at'] if r['at'] >= 0 else None, 'look': look[r['id']],
                      'changed': f'{label(was)}→{label(final)}' if was and final and was != final else None,
                      'visits': len(vq.get(r['id'], ())) if timed else None, 'class': class_view(qstats.get(r['id']), q, label)})
    you = Group(frame, duration, rules).add(entry).profile(summary['maximum'])
    ranked = bool(stats) and bool(klass.get('ranked'))
    place = rank_at(stats, summary['score'], extra) if ranked else {}
    perf = performance(rows, table)
    weak = weak_chapters(rows, table)
    lost = {(g['subject'], g['name']): g['lost'] for g in weak}
    spent = {g['name']: g['time'] for g in you['subjects']}
    for g in perf:
        g['not_seen'] = sum(1 for r in rows if r['subject'] == g['name'] and r['outcome'] == 'skipped' and not r['seen'])
        g['time'] = spent.get(g['name'])
        for c in g['chapters']:
            c['lost'] = lost.get((g['name'], c['name']), 0)
    pot = potential(rows, table, you, stats, summary, rules, extra)
    led = ledger(rows, summary)
    pos, neg = a['rules']['correct'], a['rules']['wrong']
    pot.update(no_negative=led['no_negative'], guess={'pos': pos, 'neg': neg, 'break_even': num(100 * -neg / (pos - neg)) if neg < 0 and pos > 0 else 0})
    easy = [r for r in rows if r['level'] == 'easy']
    leak = {'wrong': [r['id'] for r in easy if r['outcome'] == 'incorrect'], 'skipped': [r['id'] for r in easy if r['outcome'] == 'skipped']}
    leak['marks'] = num(sum(r['pos'] - r['neg'] for r in easy if r['outcome'] == 'incorrect') + sum(r['pos'] for r in easy if r['outcome'] == 'skipped'))
    b = rules['block']
    size = b['short'] if minutes and minutes <= b['short_upto_minutes'] else b['long']
    if duration > size * b['most']:
        size = math.ceil(duration / b['most'] / 60) * 60
    blocks = [{'from': i * size, 'to': min(max(duration, 1), (i + 1) * size), 'correct': 0, 'incorrect': 0, 'answered': 0, 'time': 0} for i in range(max(1, math.ceil(duration / size)))]
    for r in rows:
        if r['at'] >= 0 and r['outcome'] in ('correct', 'incorrect'):
            block = blocks[min(len(blocks) - 1, int(r['at'] // size))]
            block['answered'] += 1
            block[r['outcome']] += 1
    for _, at, d in st:
        blocks[min(len(blocks) - 1, int(at // size))]['time'] += d
    for block in blocks:
        block['time'] = round(block['time']) if timed else None
    by_subject, levels = {}, {}
    for r in rows:
        if r['tag']:
            by_subject.setdefault(r['subject'], Counter())[r['tag']] += 1
        lv = levels.setdefault(r['subject'], {l: {'count': 0, 'correct': 0, 'incorrect': 0, 'skipped': 0} for l in LEVELS})[r['level']]
        lv['count'] += 1
        if r['outcome'] in lv:
            lv[r['outcome']] += 1
    tags = you['tags'] or {}
    quality_on = timed and any(r['par'] for r in rows)
    trip = journey(vs, events, rows, table, start, size, timed, lambda qid, v: (by[qid].get('source_option_labels') or {}).get(v, v))
    if trip['available']:
        head = blocks[0]
        trip['first_block'] = {'minutes': num(size / 60), 'answered': head['answered'], 'correct': head['correct'], 'incorrect': head['incorrect']}
    x = rules['extra']
    more = time_more(rows, look, entry, you) if timed else {}
    unrated = sum(1 for r in rows if r['level'] == 'unrated')
    sections = {'sections': summary['sections'], 'main': summary.get('main_block'), 'bonus': summary.get('bonus_block')} if summary.get('sections') else None
    return {
        'analysis_version': ANALYSIS_VERSION, 'rules_version': VERSION, 'attempt_id': a['id'], 'title': a.get('title'), 'exam': a.get('exam'),
        'mode': a.get('mode'), 'score_version': a.get('score_version', 'original'), 'submitted_at': a.get('submitted_at'),
        'student': student or {},
        'paper': {'count': len(rows), 'minutes': minutes, 'duration': duration, 'block': size, 'not_opened_bonus': len(questions) - len(rows),
                  'marks': {'correct': pos, 'wrong': neg}},
        'time_data': timed, 'copy': COPY, 'class': klass,
        'overview': {'score': summary['score'], 'maximum': summary['maximum'], 'percentage': summary.get('percentage'), **place,
                     'attempted': you['attempted'], 'correct': you['correct'], 'incorrect': you['incorrect'], 'skipped': you['skipped'],
                     'accuracy': you['accuracy'], 'time_used': you['time'], 'time_on_screen': you['on_screen'], 'subjects': you['subjects'],
                     'ledger': led, 'verdict': verdict(you, led, pot, timed),
                     'distribution': distribution(stats, summary['score'], extra) if ranked else None,
                     'next3': next_three(rows, pot, leak, perf, summary, timed)},
        'performance': {'subjects': perf, 'weak': weak[:8], 'sections': sections, 'has_chapters': any(t['topic'] for t in table)},
        'potential': pot,
        'quality': {'available': quality_on, 'counts': tags if quality_on else None,
                    'headline': {'perfect': tags['perfect'], 'wasted': tags['wasted'], 'overtime': tags['slow_correct'] + tags['costly_overtime'],
                                 'confused': tags['confused'], 'concept_gap': tags['concept_gap']} if quality_on else None,
                    'by_subject': [{'name': name, 'counts': {t: c.get(t, 0) for t in TAGS}} for name, c in by_subject.items()] if quality_on else [],
                    'par_from': dict(Counter(r['ps'] for r in rows)),
                    'lucky': [r['id'] for r in rows if r['outcome'] == 'correct' and r['time'] and r['par'] and r['time'] < x['lucky_x'] * r['par']] if quality_on else [],
                    'painful': [r['id'] for r in sorted(rows, key=lambda r: -(r['time'] or 0)) if r['outcome'] == 'incorrect' and r['time'] and r['par'] and r['time'] > r['par']] if quality_on else []},
        'time': {'available': timed, 'elapsed': you['time'], 'on_screen': you['on_screen'], 'by_outcome': you['time_by_outcome'],
                 'by_subject': [{k: g[k] for k in ('name', 'time', 'attempted', 'accuracy', 'count')} for g in you['subjects']],
                 'blocks': blocks, 'pace': you['pace'], 'pace_split': pace_split(rows, duration),
                 'slowest': [r['id'] for r in sorted(rows, key=lambda r: -(r['time'] or 0))[:5] if r['time']] if timed else [], **more},
        'difficulty': {'all': you['difficulty'], 'by_subject': [{'name': name, 'levels': lv} for name, lv in levels.items()], 'leak': leak,
                       'sources': dict(Counter(r['ls'] for r in rows)), 'class_n': (stats or {}).get('n', 0),
                       'tough_solved': [r['id'] for r in rows if r['level'] == 'tough' and r['outcome'] == 'correct'],
                       'unlock': {'have': klass.get('n', 0), 'need': least, 'unrated': unrated} if unrated else None},
        'journey': trip,
        'habits': {'changes': answer_changes(rows, by, first), 'streaks': streaks(rows), 'last': last_stretch(rows, entry, rules)},
        'questions': table,
        'you': you,
        'compare': None,
    }
