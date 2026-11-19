"""Analysis engine v1: one pure function turns a graded attempt (plus its optional time record and class statistics) into the analysis JSON.
No database, no clock and no AI in here: the same inputs always give the same numbers on the website, in the app and in the PDF."""
import math
from collections import Counter
from .analysis_rules import RULES, VERSION, TAGS, LEVELS, COPY, standard_par, par_for, tag_for, difficulty_for

ANALYSIS_VERSION = 3
PACE_POINTS = 20
CODE = {'correct': 'c', 'incorrect': 'w', 'skipped': 's', 'dropped': 'd', 'bonus': 'b'}
OUT = {v: k for k, v in CODE.items()}
ORDER = {'easy': 0, 'moderate': 1, 'unrated': 2, 'tough': 3}


def num(x):
    if x is None:
        return None
    x = round(x, 1)
    return int(x) if x == int(x) else x


def pct(a, b):
    return round(100 * a / b, 1) if b else None


def clock(a):
    start = a.get('ready_until') or a['started_at']
    return start, max(start, a.get('submitted_at') or start)


def stretches(events, known, start, end, cap=RULES['stretch_cap']):
    """Every device's on-screen stretches in time order as (question, offset, seconds): never overlapping, never outside the paper."""
    out, edge = [], start
    for e in sorted((e for e in events or [] if e.get('k') == 'v' and e.get('q') in known), key=lambda e: (e['a'], e['b'])):
        a = max(e['a'], edge)
        b = min(e['b'], end, a + cap)
        if b - a >= 0.5:
            out.append((e['q'], a - start, b - a))
            edge = b
    return out


def visits(st):
    """A visit is one unbroken stay on a question; a hidden tab in the middle does not make it two visits."""
    out = []
    for q, at, d in st:
        if out and out[-1]['q'] == q:
            out[-1]['d'] += d
            out[-1]['end'] = at + d
        else:
            out.append({'q': q, 'a': at, 'd': d, 'end': at + d})
    return out


def entry_of(a, questions, rows, st, summary):
    """One student's paper as short aligned codes: enough for every total, with no question text or answer key."""
    start, end = clock(a)
    secs = Counter()
    for q, _, d in st:
        secs[q] += d
    first, final = a.get('first_answers') or {}, a.get('answers') or {}
    seen = set(a.get('visited') or ()) | set(secs) | set(final)
    locked = bool((a.get('rules') or {}).get('bonus_rule')) and not a.get('bonus_unlocked_at')
    opened = Counter(v['q'] for v in visits(st))

    def answered_at(qid):
        at = (first.get(qid) or final.get(qid) or {}).get('accepted_at')
        return max(0, round(at - start)) if isinstance(at, (int, float)) else -1
    return {
        'o': ''.join('u' if locked and q.get('bonus') else CODE[rows[q['id']]['outcome']] for q in questions),
        't': [round(secs[q['id']]) for q in questions] if st else None,
        'r': [(rows[q['id']].get('normalized_response') or '') if q['type'] == 'mcq' else '' for q in questions],
        'f': [answered_at(q['id']) if rows[q['id']]['outcome'] in ('correct', 'incorrect') else -1 for q in questions],
        'v': ''.join('1' if q['id'] in seen else '0' for q in questions),
        'score': summary['score'], 'maximum': summary['maximum'], 'secs': round(end - start),
        'on': round(sum(secs.values())) if st else None,
        'j': [len(opened), sum(c - 1 for c in opened.values())] if st else None,  # questions opened, times came back
    }


def frame_for(questions, qstats, minutes, marks, hints=None, rules=RULES):
    """Per question: marks, par time and difficulty. Shared by everyone who took the paper."""
    standard = standard_par(questions, minutes, rules)
    average = minutes * 60 / len(questions) if minutes and questions else None
    out = []
    for q in questions:
        stat = (qstats or {}).get(q['id'])
        par, source, solvers = par_for(q, standard, stat, average, rules)
        level, origin = difficulty_for(q, stat, (hints or {}).get(q['id']), rules)
        s = q.get('scoring') or marks
        out.append({'id': q['id'], 'subject': q.get('subject') or 'Unlabelled', 'type': q['type'], 'pos': s['correct'], 'neg': s['wrong'],
                    'max': 0 if q.get('disposition') == 'dropped' else s['correct'],
                    'par': par, 'ps': source, 'pn': solvers, 'level': level, 'ls': origin})
    return out


def rows_of(entry, frame, rules=RULES):
    out = []
    for i, f in enumerate(frame):
        o = entry['o'][i]
        sec = entry['t'][i] if entry.get('t') else None
        seen = entry['v'][i] == '1'
        out.append({**f, 'o': o, 'outcome': OUT.get(o), 'time': sec, 'seen': seen, 'at': entry['f'][i],
                    'tag': tag_for(OUT[o], sec, f['par'], seen, rules) if o != 'u' else None,
                    'marks': f['pos'] if o in 'cb' else f['neg'] if o == 'w' else 0})
    return out


class Group:
    """Totals of one or many students on the same frame. Only totals and averages leave this object."""

    def __init__(self, frame, duration, rules=RULES):
        self.frame, self.duration, self.rules = frame, duration, rules
        self.n = self.timed = self.walked = 0
        self.walk = [0, 0]
        self.tot, self.byo = Counter(), Counter()
        self.q = [[0, 0, 0, 0, 0] for _ in frame]  # correct, wrong, skipped, marks, seconds
        self.tags = [Counter() for _ in frame]
        self.pace = [0] * (PACE_POINTS + 1)

    def add(self, e):
        self.n += 1
        timed = bool(e.get('t'))
        self.timed += timed
        self.tot.update(score=e['score'], secs=e['secs'], on=e.get('on') or 0)
        if e.get('j'):
            self.walked += 1
            self.walk = [self.walk[0] + e['j'][0], self.walk[1] + e['j'][1]]
        for i, f in enumerate(self.frame):
            o, s = e['o'][i], self.q[i]
            if o == 'c':
                s[0] += 1
                s[3] += f['pos']
            elif o == 'w':
                s[1] += 1
                s[3] += f['neg']
            elif o == 's':
                s[2] += 1
            elif o == 'b':
                s[3] += f['pos']
            if timed and o != 'u':
                sec = e['t'][i]
                s[4] += sec
                self.byo['correct' if o == 'c' else 'incorrect' if o == 'w' else 'unanswered'] += sec
                self.tags[i][tag_for(OUT[o], sec, f['par'], e['v'][i] == '1', self.rules)] += 1
        if self.duration:
            for at in e['f']:
                if at >= 0:
                    self.pace[min(PACE_POINTS, math.ceil(at * PACE_POINTS / self.duration))] += 1
        return self

    def times(self):
        """Average seconds on each question, in paper order; None when nobody here has a time record."""
        return [round(s[4] / self.timed) for s in self.q] if self.timed else None

    def profile(self, maximum=None):
        n, t = max(self.n, 1), self.timed
        subjects, tags = {}, Counter()
        levels = {l: {'count': 0, 'correct': 0, 'incorrect': 0, 'skipped': 0} for l in LEVELS}
        for f, s, tg in zip(self.frame, self.q, self.tags):
            g = subjects.setdefault(f['subject'], {'name': f['subject'], 'count': 0, 'maximum': 0, 'score': 0, 'correct': 0, 'incorrect': 0, 'skipped': 0, 'time': 0})
            lv = levels[f['level']]
            g['count'] += 1
            lv['count'] += 1
            g['maximum'] += f['max']
            g['score'] += s[3] / n
            for i, k in enumerate(('correct', 'incorrect', 'skipped')):
                g[k] += s[i] / n
                lv[k] += s[i] / n
            if t:
                g['time'] += s[4] / t
                for name, c in tg.items():
                    if name:
                        tags[name] += c / t

        def close(g):
            tried = g['correct'] + g['incorrect']
            out = {k: (v if isinstance(v, str) else num(v)) for k, v in g.items()}
            out.update(attempted=num(tried), accuracy=pct(g['correct'], tried))
            if 'time' in out and not t:
                out['time'] = None
            return out
        total = {k: sum(g[k] for g in subjects.values()) for k in ('correct', 'incorrect', 'skipped')}
        tried = total['correct'] + total['incorrect']
        run, pace = 0, []
        for c in self.pace:
            run += c
            pace.append(num(run / n))
        return {'n': self.n, 'score': num(self.tot['score'] / n), 'maximum': maximum, **{k: num(v) for k, v in total.items()},
                'attempted': num(tried), 'accuracy': pct(total['correct'], tried), 'time': num(self.tot['secs'] / n),
                'on_screen': num(self.tot['on'] / t) if t else None, 'subjects': [close(g) for g in subjects.values()],
                'difficulty': {l: close(g) for l, g in levels.items()},
                'tags': {k: num(tags[k]) for k in TAGS} if t else None,
                'time_by_outcome': {k: num(self.byo[k] / t) for k in ('correct', 'incorrect', 'unanswered')} if t else None,
                'journey': {'visited': num(self.walk[0] / self.walked), 'revisits': num(self.walk[1] / self.walked)} if self.walked else None,
                'pace': pace if self.duration else None}


def rank_at(stats, score, extra=0):
    """Where a score stands in the class: equal scores share a rank. extra=1 when this student is not counted in the statistics yet."""
    n = (stats.get('n') or 0) + extra
    if not n:
        return {}
    better = sum(c for s, c in stats['scores'] if s > score)
    return {'rank': 1 + better, 'of': n, 'percentile': round(100 * (sum(c for s, c in stats['scores'] if s <= score) + extra) / n, 2)}


def _blank(name=None):
    g = {'count': 0, 'correct': 0, 'incorrect': 0, 'skipped': 0, 'score': 0, 'maximum': 0, 'negative': 0}
    return {'name': name, **g} if name is not None else g


def _add(g, r):
    g['count'] += 1
    g['maximum'] += r['max']
    g['score'] += r['marks']
    if r['outcome'] in ('correct', 'incorrect', 'skipped'):
        g[r['outcome']] += 1
    if r['marks'] < 0:
        g['negative'] -= r['marks']


def _close(g):
    tried = g['correct'] + g['incorrect']
    scored = tried + g['skipped']
    return {**{k: (v if isinstance(v, (str, list, dict)) or v is None else num(v)) for k, v in g.items()},
            'attempted': tried, 'accuracy': pct(g['correct'], tried), 'attempt_rate': pct(tried, scored)}


def performance(rows, table):
    by = {}
    for r, t in zip(rows, table):
        g = by.setdefault(r['subject'], {**_blank(r['subject']), 'types': {}, 'chapters': {}})
        _add(g, r)
        _add(g['types'].setdefault(r['type'], _blank()), r)
        if t['topic']:
            _add(g['chapters'].setdefault(t['topic'], _blank(t['topic'])), r)
    out = []
    for g in by.values():
        chapters = []
        for c in sorted(g['chapters'].values(), key=lambda c: (-c['count'], c['name'])):
            c = _close(c)
            # No strength label on fewer than 3 questions: too few to say anything.
            c['label'] = None if c['count'] < 3 or not c['attempted'] else 'strong' if c['accuracy'] >= 75 else 'weak' if c['accuracy'] < 40 else 'steady'
            chapters.append(c)
        out.append({**_close({k: v for k, v in g.items() if k not in ('types', 'chapters')}),
                    'types': {k: _close(v) for k, v in g['types'].items()}, 'chapters': chapters})
    return out


def potential(rows, table, you, stats, summary, rules=RULES, extra=0):
    """Exact arithmetic on this attempt's own questions; every step lists the questions behind it."""
    qstats = (stats or {}).get('q') or {}
    careless = [r for r in rows if r['tag'] == 'wasted']
    limit = rules['potential']['guard_solved_below']

    def rarely_solved(r):
        s = qstats.get(r['id'])
        return bool(s) and s.get('n', 0) >= rules['compare']['min_finishers'] and 100 * s['correct'] / s['n'] < limit
    guard = [r for r in rows if r['outcome'] == 'incorrect' and r['tag'] != 'wasted' and r['level'] == 'tough' and rarely_solved(r)]
    lost = sum(max(0, r['time'] - r['par']) for r in rows if r['tag'] == 'costly_overtime') + sum(r['time'] for r in rows if r['tag'] == 'confused')
    number = {t['id']: t['number'] for t in table}
    overall = you['accuracy']
    picked, gain, budget = [], 0, lost
    for r in sorted((r for r in rows if r['tag'] in ('not_seen', 'smart_skip') and r['par']), key=lambda r: (ORDER[r['level']], number[r['id']])):
        accuracy = you['difficulty'][r['level']]['accuracy']
        accuracy = overall if accuracy is None else accuracy
        if accuracy is None or r['par'] > budget:
            continue
        expected = accuracy / 100 * r['pos'] + (1 - accuracy / 100) * r['neg']
        if expected > 0:
            budget -= r['par']
            gain += expected
            picked.append(r['id'])
    a = sum(r['pos'] - r['neg'] for r in careless)
    b = sum(-r['neg'] for r in guard)
    c = round(gain, 1)
    current, top = summary['score'], summary['maximum']
    realistic, most = min(top, current + a + b + c / 2), min(top, current + a + b + c)
    steps = [{'key': 'careless', 'marks': num(a), 'questions': [r['id'] for r in careless]},
             {'key': 'guard', 'marks': num(b), 'questions': [r['id'] for r in guard]},
             {'key': 'reinvest', 'marks': num(c), 'minutes': num(lost / 60), 'questions': picked}]
    at = [{'key': k, 'score': num(s), **(rank_at(stats, s, extra) if stats else {})} for k, s in (('current', current), ('realistic', realistic), ('maximum', most))]
    return {'available': any(r['tag'] and r['tag'] != 'no_score' for r in rows), 'current': current, 'steps': steps,
            'realistic': num(realistic), 'maximum': num(most), 'paper_maximum': top, 'at': at}


def next_three(rows, pot, leak, perf, summary, timed):
    """Three things for the next mock, ranked by the marks at stake in this attempt."""
    step = {s['key']: s for s in pot['steps']}
    out = []

    def put(key, marks, title, detail, questions, section):
        if marks and marks > 0:
            out.append({'key': key, 'marks': num(marks), 'title': title, 'detail': detail, 'questions': questions, 'section': section})
    s = step['careless']
    put('careless', s['marks'], 'Careless galti roko', f"{len(s['questions'])} sawaal jaldbaazi mein galat hue. Inhe aaram se padhte to +{s['marks']} marks milte.", s['questions'], 'quality')
    s = step['guard']
    put('guard', s['marks'], 'Mushkil sawaal par risk mat lo', f"{len(s['questions'])} Tough sawaal galat hue jo class mein bhi kam logon se bane. Chhod dete to {s['marks']} marks bach jaate.", s['questions'], 'potential')
    s = step['reinvest']
    put('reinvest', s['marks'] / 2, 'Atka hua time wapas lao', f"{s['minutes']} min aise sawaalon par gaye jahan marks nahi bane. Yeh time chhode hue sawaalon ko dete to lagbhag +{num(s['marks'] / 2)} marks.", s['questions'], 'time')
    put('leak', leak['marks'], 'Easy sawaal pakke karo', f"{len(leak['wrong'])} Easy galat aur {len(leak['skipped'])} Easy chhoote. Yahan se {leak['marks']} marks bach sakte the.", leak['wrong'] + leak['skipped'], 'difficulty')
    weak = [g for g in perf if g['incorrect']]
    if weak:
        g = min(weak, key=lambda g: (g['accuracy'] if g['accuracy'] is not None else 100, -g['negative']))
        wrong = [r for r in rows if r['subject'] == g['name'] and r['outcome'] == 'incorrect']
        marks = sum(r['pos'] - r['neg'] for r in wrong)
        put('subject', marks, f"{g['name']} ko mazboot karo", f"{g['name']} mein {g['incorrect']} galat, Accuracy {g['accuracy']}%. Yeh sahi hote to +{num(marks)} marks.", [r['id'] for r in wrong], 'performance')
    if not timed:
        put('negative', summary.get('penalties'), 'Negative marking kam karo', f"{summary['incorrect']} galat jawab se {summary.get('penalties')} marks kate. Jahan pakka na ho, wahan chhodna behtar hai.", [r['id'] for r in rows if r['outcome'] == 'incorrect'], 'overview')
    seen, top = set(), []
    for item in sorted(out, key=lambda x: -x['marks']):
        mark = frozenset(item['questions'])
        if mark not in seen:
            seen.add(mark)
            top.append(item)
    return top[:3]


def journey(vs, events, rows, table, start, size, timed, show=lambda q, v: v):
    if not timed:
        return {'available': False, 'visits': [], 'summary': None, 'order': [], 'block': size}
    meta = {t['id']: t for t in table}
    changes = {}
    for e in sorted((e for e in events or [] if e.get('k') in ('a', 'm') and e.get('q') in meta), key=lambda e: e['a']):
        changes.setdefault(e['q'], []).append(e)
    held, count, out, order = {}, Counter(), [], []
    for v in vs:
        if v['q'] not in meta:
            continue
        count[v['q']] += 1
        subject = meta[v['q']]['subject']
        if subject not in order:
            order.append(subject)
        item = {'q': v['q'], 'n': meta[v['q']]['number'], 'a': round(v['a']), 'd': round(v['d']), 'v': count[v['q']]}
        for e in changes.get(v['q'], []):
            if start + v['a'] - 1 <= e['a'] <= start + v['end'] + 1:
                if e['k'] == 'm':
                    item['mark'] = e.get('v') == '1'
                elif e.get('v') != held.get(v['q'], ''):
                    before, held[v['q']] = held.get(v['q'], ''), e.get('v') or ''
                    was, new = show(v['q'], before), show(v['q'], held[v['q']])
                    item['set'] = f"{was}→{new}" if before and held[v['q']] else new or 'Clear'
        out.append(item)
    return {'available': True, 'visits': out, 'order': order, 'block': size,
            'summary': {'visited': len(count), 'total': len(rows), 'revisits': sum(c - 1 for c in count.values()), 'thrice': sum(c >= 3 for c in count.values())}}


def class_view(stat, q, label):
    if not stat or not stat.get('n'):
        return None
    n, accepted = stat['n'], set(q.get('accepted_answers') or [q.get('answer')])
    wrong = max(((k, v) for k, v in (stat.get('options') or {}).items() if k not in accepted), key=lambda x: x[1], default=None)
    return {'n': n, 'correct': pct(stat['correct'], n), 'wrong': pct(stat['incorrect'], n), 'skipped': pct(stat['skipped'], n),
            'attempted': pct(stat['correct'] + stat['incorrect'], n), 'right_of_attempted': pct(stat['correct'], stat['correct'] + stat['incorrect']),
            'avg_time': stat.get('avg'), 'topper_time': stat.get('topper') or None,
            'top_wrong': {'option': label(wrong[0]), 'percent': pct(wrong[1], n)} if wrong and wrong[1] else None}


FILTERS = {
    'wrong': lambda q: q['outcome'] == 'incorrect', 'skipped': lambda q: q['outcome'] == 'skipped', 'correct': lambda q: q['outcome'] == 'correct',
    'careless': lambda q: q['tag'] == 'wasted', 'overtime': lambda q: q['tag'] in ('slow_correct', 'costly_overtime'),
    'confused': lambda q: q['tag'] == 'confused', 'marked': lambda q: q['marked'], 'changed': lambda q: bool(q['changed']),
}


def build_analysis(attempt, result, stats=None, rules=RULES, events=None, hints=None, klass=None):
    a, summary, questions = attempt, result['summary'], result['questions']
    by = {q['id']: q for q in questions}
    klass = klass or {'state': 'none'}
    minutes = (a.get('rules') or {}).get('minutes') or 0
    start, end = clock(a)
    duration = round(minutes * 60) or round(end - start)
    st = stretches(events, set(by), start, end, rules['stretch_cap'])
    timed = bool(st)
    entry = entry_of(a, questions, by, st, summary)
    frame = (stats or {}).get('frame')
    if not frame or [f['id'] for f in frame] != [q['id'] for q in questions]:
        stats, frame = None, frame_for(questions, None, minutes, a['rules'], hints, rules)
    qstats = stats['q'] if stats and stats['n'] >= rules['compare']['min_finishers'] else {}
    rows = [r for r in rows_of(entry, frame, rules) if r['o'] != 'u']
    vs = visits(st)
    vcount = Counter(v['q'] for v in vs)
    first = a.get('first_answers') or {}
    table = []
    for r in rows:
        q = by[r['id']]
        label = lambda v, q=q: (q.get('source_option_labels') or {}).get(v, v)
        was, final = (first.get(r['id']) or {}).get('normalized_value', ''), q.get('normalized_response') or ''
        table.append({'id': r['id'], 'number': q['number'], 'subject': r['subject'], 'topic': q.get('topic') or '', 'type': q['type'],
                      'difficulty': r['level'], 'difficulty_source': r['ls'], 'response': label(final),
                      'answer': ', '.join(str(label(v)) for v in (q.get('accepted_answers') or [q.get('answer')])),
                      'outcome': r['outcome'], 'marks': q['marks'], 'time': r['time'], 'par': num(r['par']), 'par_source': r['ps'], 'par_n': r['pn'],
                      'tag': r['tag'], 'marked': bool(q.get('marked')), 'changed': f'{label(was)}→{label(final)}' if was and final and was != final else None,
                      'visits': vcount.get(r['id'], 0) if timed else None, 'class': class_view(qstats.get(r['id']), q, label)})
    you = Group(frame, duration, rules).add(entry).profile(summary['maximum'])
    ranked = bool(stats) and bool(klass.get('ranked'))
    place = rank_at(stats, summary['score']) if ranked else {}
    perf = performance(rows, table)
    pot = potential(rows, table, you, stats, summary, rules)
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
    return {
        'analysis_version': ANALYSIS_VERSION, 'rules_version': VERSION, 'attempt_id': a['id'], 'title': a.get('title'), 'exam': a.get('exam'),
        'mode': a.get('mode'), 'score_version': a.get('score_version', 'original'), 'submitted_at': a.get('submitted_at'),
        'paper': {'count': len(rows), 'minutes': minutes, 'duration': duration, 'block': size, 'not_opened_bonus': len(questions) - len(rows),
                  'marks': {'correct': a['rules']['correct'], 'wrong': a['rules']['wrong']}},
        'time_data': timed, 'copy': COPY, 'class': klass,
        'overview': {'score': summary['score'], 'maximum': summary['maximum'], 'percentage': summary.get('percentage'), **place,
                     'attempted': you['attempted'], 'correct': you['correct'], 'incorrect': you['incorrect'], 'skipped': you['skipped'],
                     'accuracy': you['accuracy'], 'time_used': you['time'], 'time_on_screen': you['on_screen'], 'subjects': you['subjects'],
                     'next3': next_three(rows, pot, leak, perf, summary, timed)},
        'performance': {'subjects': perf},
        'potential': pot,
        'quality': {'available': quality_on, 'counts': tags if quality_on else None,
                    'headline': {'perfect': tags['perfect'], 'wasted': tags['wasted'], 'overtime': tags['slow_correct'] + tags['costly_overtime'],
                                 'confused': tags['confused'], 'concept_gap': tags['concept_gap']} if quality_on else None,
                    'by_subject': [{'name': name, 'counts': {t: c.get(t, 0) for t in TAGS}} for name, c in by_subject.items()] if quality_on else [],
                    'par_from': dict(Counter(r['ps'] for r in rows))},
        'time': {'available': timed, 'elapsed': you['time'], 'on_screen': you['on_screen'], 'by_outcome': you['time_by_outcome'],
                 'by_subject': [{k: g[k] for k in ('name', 'time', 'attempted', 'accuracy', 'count')} for g in you['subjects']],
                 'blocks': blocks, 'pace': you['pace'],
                 'slowest': [r['id'] for r in sorted(rows, key=lambda r: -(r['time'] or 0))[:5] if r['time']] if timed else []},
        'difficulty': {'all': you['difficulty'], 'by_subject': [{'name': name, 'levels': lv} for name, lv in levels.items()], 'leak': leak},
        'journey': trip,
        'questions': table,
        'you': you,
        'compare': None,
    }
