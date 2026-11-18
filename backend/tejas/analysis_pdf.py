"""Analysis report (A4 PDF) and the share image, drawn only from the analysis JSON: no question text, no phone number."""
import io, re, textwrap
from datetime import datetime
from zoneinfo import ZoneInfo
import fitz

IST = ZoneInfo('Asia/Kolkata')
INK, MUTE, RED, GREEN, AMBER, BLUE, LINE, SOFT, WHITE = ((0.07, 0.07, 0.1), (0.42, 0.42, 0.48), (0.85, 0.07, 0.13), (0.1, 0.58, 0.36), (0.82, 0.55, 0.1),
                                                         (0.16, 0.38, 0.82), (0.86, 0.86, 0.9), (0.95, 0.95, 0.97), (1, 1, 1))
RESULT = {'correct': 'Sahi', 'incorrect': 'Galat', 'skipped': 'Chhoda', 'dropped': 'Dropped', 'bonus': 'Bonus'}
TONE = {'correct': GREEN, 'incorrect': RED, 'skipped': MUTE, 'dropped': MUTE, 'bonus': GREEN}
SOURCE = {'students': 'students ke result se', 'early': 'shuruaati result se', 'paper': 'paper ke tag se', 'none': 'Not rated'}


def plain(v):
    s = str('' if v is None else v)
    for a, b in (('→', '->'), ('—', '-'), ('–', '-'), ('−', '-'), ('’', "'"), ('‘', "'"), ('“', '"'), ('”', '"'), ('…', '...')):
        s = s.replace(a, b)
    return s.encode('latin-1', 'replace').decode('latin-1')


def mmss(s):
    if s is None:
        return '-'
    s = round(s)
    return f'{s // 60}m {s % 60:02d}s'


def pc(v):
    return '-' if v is None else f'{v}%'


def when(an):
    return datetime.fromtimestamp(an.get('submitted_at') or 0, IST)


def file_name(an):
    title = re.sub(r'[^A-Za-z0-9]+', '_', an.get('title') or 'Mock').strip('_')[:60] or 'Mock'
    return f'JEELIVE_{title}_{when(an):%Y-%m-%d}'


class Sheet:
    def __init__(self, title, sub):
        self.doc, self.title, self.sub, self.page, self.y = fitz.open(), plain(title), plain(sub), None, 0

    def text(self, at, s, size=10, color=INK, bold=False):
        self.page.insert_text(at, plain(s), fontsize=size, fontname='hebo' if bold else 'helv', color=color)

    def box(self, x0, y0, x1, y1, fill=None, color=None, width=0.7):
        self.page.draw_rect(fitz.Rect(x0, y0, x1, y1), color=color or fill, fill=fill, width=width)

    def new(self):
        self.page = self.doc.new_page(width=595, height=842)
        self.box(0, 0, 595, 6, RED)
        self.text((40, 30), 'JEELIVE.AI  |  ANALYSIS REPORT', 8, RED, True)
        self.text((40, 44), self.title[:95], 9, MUTE)
        self.y = 66

    def need(self, h):
        if self.page is None or self.y + h > 792:
            self.new()

    def h1(self, text, note=''):
        self.need(70)
        self.text((40, self.y + 18), text, 17, INK, True)
        self.y += 28
        if note:
            self.para(note, 9, MUTE)
        self.y += 4

    def h2(self, text):
        self.need(44)
        self.y += 4
        self.text((40, self.y + 12), text, 11.5, RED, True)
        self.y += 20

    def para(self, text, size=10, color=INK, bold=False):
        for line in textwrap.wrap(plain(text), int(515 / (size * 0.5))) or ['']:
            self.need(size + 5)
            self.text((40, self.y + size), line, size, color, bold)
            self.y += size + 4

    def row(self, cells, widths, size, bold=False, fill=None):
        h = size + 9
        if fill:
            self.box(40, self.y, 40 + sum(widths), self.y + h, fill)
        x = 40
        for c, w in zip(cells, widths):
            self.text((x + 4, self.y + size + 3), plain(c)[:max(1, int(w / (size * 0.52)))], size, INK, bold)
            x += w
        self.page.draw_line((40, self.y + h), (40 + sum(widths), self.y + h), color=LINE, width=0.5)
        self.y += h

    def table(self, head, rows, widths, size=9):
        self.need(3 * (size + 9))
        self.row(head, widths, size, True, SOFT)
        for r in rows:
            if self.y + size + 9 > 792:
                self.new()
                self.row(head, widths, size, True, SOFT)
            self.row(r, widths, size)
        self.y += 12

    def tiles(self, items, x0=40, x1=555, h=48):
        self.need(h + 12)
        w = (x1 - x0) / len(items)
        for i, (label, value) in enumerate(items):
            a = x0 + i * w
            self.box(a, self.y, a + w - 6, self.y + h, color=LINE)
            self.text((a + 8, self.y + 15), label, 8, MUTE)
            self.text((a + 8, self.y + 37), value, 14, INK, True)
        self.y += h + 12

    def bar(self, label, value, most, color=RED, note=''):
        self.need(20)
        self.text((40, self.y + 10), plain(label)[:38], 9)
        self.box(220, self.y + 2, 460, self.y + 12, SOFT)
        if most and value and value > 0:
            self.box(220, self.y + 2, 220 + 240 * min(1, value / most), self.y + 12, color)
        self.text((468, self.y + 10), note, 9)
        self.y += 18

    def stack(self, parts):
        """One stacked bar with its legend: [(label, value, colour)]."""
        self.need(46)
        total = sum(max(0, v) for _, v, _ in parts) or 1
        x = 40
        for _, v, color in parts:
            w = 515 * max(0, v) / total
            if w > 0:
                self.box(x, self.y, x + w, self.y + 14, color)
            x += w
        self.y += 22
        x = 40
        for label, v, color in parts:
            self.box(x, self.y, x + 8, self.y + 8, color)
            note = plain(f'{label}: {v}')
            self.text((x + 12, self.y + 8), note, 8.5)
            x += 22 + len(note) * 4.5
        self.y += 20

    def frame(self, height, top, x0=70, x1=545):
        """Axes box with four grid lines; returns (x0, x1, y_top, y_bottom)."""
        self.need(height + 34)
        y0, y1 = self.y + 6, self.y + height
        for i in range(5):
            y = y1 - (y1 - y0) * i / 4
            self.page.draw_line((x0, y), (x1, y), color=LINE, width=0.4)
            self.text((44, y + 3), num(top * i / 4), 7, MUTE)
        return x0, x1, y0, y1

    def lines(self, series, left, right, height=120):
        """Line chart: [(name, values, colour)], all on the same x steps."""
        top = max([max(v) for _, v, _ in series if v] + [1])
        x0, x1, y0, y1 = self.frame(height, top)
        for _, vals, color in series:
            if len(vals) > 1:
                self.page.draw_polyline([fitz.Point(x0 + (x1 - x0) * i / (len(vals) - 1), y1 - (y1 - y0) * v / top) for i, v in enumerate(vals)], color=color, width=1.6)
        self.text((x0, y1 + 11), left, 7.5, MUTE)
        self.text((x1 - 4.2 * len(right), y1 + 11), right, 7.5, MUTE)
        self.legend([(n, c) for n, _, c in series], y1 + 22)
        self.y = y1 + 34

    def legend(self, items, y):
        x = 70
        for name, color in items:
            self.box(x, y - 7, x + 8, y + 1, color)
            self.text((x + 12, y), name, 8)
            x += 26 + len(name) * 4.6

    def blocks(self, items, height=110):
        """Stacked columns: [(label, right, wrong)]."""
        top = max([a + b for _, a, b in items] + [1])
        x0, x1, y0, y1 = self.frame(height, top)
        w = (x1 - x0) / max(len(items), 1)
        for i, (label, right, wrong) in enumerate(items):
            a = x0 + i * w + w * 0.2
            h1, h2 = (y1 - y0) * right / top, (y1 - y0) * wrong / top
            if right:
                self.box(a, y1 - h1, a + w * 0.6, y1, GREEN)
            if wrong:
                self.box(a, y1 - h1 - h2, a + w * 0.6, y1 - h1, RED)
            self.text((a, y1 + 10), label, 7, MUTE)
        self.legend([('Sahi', GREEN), ('Galat', RED)], y1 + 22)
        self.y = y1 + 34

    def scatter(self, points, height=150):
        """Speed-Accuracy map: one dot per question; x = time as a multiple of Par (0 to 3), three lanes by result."""
        self.need(height + 34)
        x0, x1, y0 = 110, 545, self.y + 4
        lane = (height - 8) / 3
        for i, (name, color) in enumerate((('Sahi', GREEN), ('Galat', RED), ('Chhoda', MUTE))):
            self.box(x0, y0 + i * lane, x1, y0 + (i + 1) * lane - 3, SOFT)
            self.text((44, y0 + i * lane + lane / 2 + 3), name, 9, color, True)
        for mult, label in ((0.5, '0.5x'), (1, 'Par'), (1.5, '1.5x'), (2, '2x'), (3, '3x+')):
            x = x0 + (x1 - x0) * mult / 3
            self.page.draw_line((x, y0), (x, y0 + height - 8), color=INK if mult == 1 else LINE, width=0.9 if mult == 1 else 0.5)
            self.text((x - 8, y0 + height + 4), label, 7.5, INK if mult == 1 else MUTE, mult == 1)
        for number, outcome, ratio in points:
            i = {'correct': 0, 'incorrect': 1}.get(outcome, 2)
            x = x0 + (x1 - x0) * min(3, ratio) / 3
            y = y0 + i * lane + 8 + (number * 37 % 100) / 100 * (lane - 19)
            self.page.draw_circle((x, y), 2.6, color=TONE.get(outcome, MUTE), fill=TONE.get(outcome, MUTE), width=0.3)
        self.y = y0 + height + 18

    def ring(self, cx, cy, r, share, color=RED):
        self.page.draw_circle((cx, cy), r, color=SOFT, fill=SOFT)
        if share > 0.999:
            self.page.draw_circle((cx, cy), r, color=color, fill=color)
        elif share > 0.001:
            self.page.draw_sector((cx, cy), (cx, cy - r), -360 * share, color=color, fill=color)
        self.page.draw_circle((cx, cy), r * 0.74, color=WHITE, fill=WHITE)

    def done(self):
        for i, p in enumerate(self.doc):
            p.insert_text((40, 822), f'{self.sub}  |  Personal study report  |  {i + 1} / {len(self.doc)}', fontsize=7.5, color=MUTE)
        return self.doc.tobytes(garbage=3, deflate=True)


def num(v):
    v = round(v, 1)
    return str(int(v)) if v == int(v) else str(v)


def render(an, notes=None):
    o, copy, tags, L = an['overview'], an['copy'], an['copy']['tags'], an['copy']['levels']
    name = (an.get('student') or {}).get('name')
    s = Sheet(an.get('title') or 'Mock', f"{an.get('exam') or 'JEELIVE.AI'} | {when(an):%d %b %Y}" + (f' | {name}' if name else ''))
    rows = {q['id']: q for q in an['questions']}
    qn = lambda ids, most=45: (', '.join('Q' + str(rows[i]['number']) for i in ids[:most] if i in rows) + (f' +{len(ids) - most} aur' if len(ids) > most else '')) or '-'
    later = 'Is attempt mein har sawaal ka time record nahi hua tha. Yeh hissa agle mock se apne aap bharega.'
    klass = an['class']

    # Cover
    s.new()
    s.text((40, 110), 'ANALYSIS REPORT', 10, RED, True)
    y = 140
    for line in textwrap.wrap(plain(an.get('title') or 'Mock'), 34)[:3]:
        s.text((40, y), line, 24, INK, True)
        y += 30
    s.text((40, y + 2), ' | '.join(x for x in (an.get('exam'), f'{when(an):%d %b %Y}', name) if x), 11, MUTE)
    cy = y + 120
    s.ring(120, cy, 70, max(0, o['score']) / max(o['maximum'], 1))
    score = str(o['score'])
    s.text((120 - 8.6 * len(score), cy + 6), score, 30, INK, True)
    s.text((120 - 2.6 * len(f"/ {o['maximum']}"), cy + 24), f"/ {o['maximum']}", 10, MUTE)
    s.y = cy - 62
    s.tiles([('Rank', f"#{o['rank']} / {o['of']}" if o.get('rank') else '-'), ('Percentile', o.get('percentile', '-'))], 220)
    s.tiles([('Accuracy', pc(o['accuracy'])), ('Time', mmss(o['time_used']))], 220)
    s.y = cy + 92
    s.box(40, s.y, 555, s.y + 3, RED)
    s.y += 14
    s.para(o['verdict']['text'], 12.5, INK, True)
    s.y += 6
    led = o['ledger']
    s.h2('Marks ka hisaab')
    s.stack([('Kamaye', led['earned'], GREEN), ('Galat mein reh gaye', led['left_wrong'], RED), ('Chhode mein reh gaye', led['left_skipped'], MUTE)])
    s.para(f"Negative mein kate: {led['negative']} marks. Net Score: {led['net']} / {led['maximum']}. Bina kisi galat jawab ke Score {led['no_negative']} hota.", 9.5)
    s.h2('Is report mein')
    for i, line in enumerate(('Overview: Score, Rank, subject-wise aur agle mock ke 3 kaam', 'Performance: subject aur chapter ka hisaab', 'Score Potential: yahan se marks bach sakte the',
                              'Attempt Quality: har sawaal ka tag aur Speed-Accuracy map', 'Time kahan gaya: subject, blocks aur pace', 'Difficulty aur Question Journey', 'Qs by Qs: har sawaal ka poora hisaab'), 1):
        s.para(f'{i}. {line}', 9.5, MUTE)
    s.para('Yeh report sirf aapke jawab aur time se bani hai. Isme koi andaaza ya AI nahi hai.', 8.5, MUTE)

    # 1 Overview
    s.new()
    s.h1('1. Overview')
    s.tiles([('Attempted', o['attempted']), ('Sahi', o['correct']), ('Galat', o['incorrect']), ('Chhode', o['skipped'])])
    s.table(['Subject', 'Score', 'Sahi', 'Galat', 'Chhode', 'Accuracy', 'Time'],
            [[g['name'], f"{g['score']} / {g['maximum']}", g['correct'], g['incorrect'], g['skipped'], pc(g['accuracy']), mmss(g['time'])] for g in o['subjects']],
            [150, 75, 50, 50, 55, 65, 70])
    dist = o.get('distribution')
    if dist:
        s.h2(f"Aap kahan khade ho ({dist['n']} students mein)")
        most = max(b['count'] for b in dist['bins']) or 1
        for b in dist['bins']:
            if b['count'] or b['you']:
                s.bar(f"{b['from']} se {b['to']}" + ('  <- AAP' if b['you'] else ''), b['count'], most, RED if b['you'] else MUTE, str(b['count']))
        s.para(f"Class average {dist['average']}, median {dist['median']}, top Score {dist['top']}.", 9, MUTE)
    elif klass['state'] == 'ready':
        s.para(f"Abhi {klass['n']} student ne yeh paper diya hai. Aur students aate hi class ka chart yahan dikhega.", 9, MUTE)
    s.h2('Agle mock ke liye 3 kaam')
    for i, item in enumerate(o['next3'], 1):
        s.para(f"{i}. {item['title']} (+{item['marks']} marks): {item['detail']}")
    if not o['next3']:
        s.para('Is attempt mein koi bada sudhaar ka point nahi mila. Ab naye sawaal try karo.')
    mine = (notes or {}).get('mine') or []
    if mine:
        s.h2('Is test se meri 3 seekh')
        for i, line in enumerate(mine, 1):
            s.para(f'{i}. {line}')

    # 2 Performance
    s.new()
    perf = an['performance']
    s.h1('2. Performance', 'Har subject mein Score, Accuracy, Attempt rate aur negative marks.')
    s.table(['Subject', 'Score', 'Accuracy', 'Attempt rate', 'Negative', 'Dekha nahi', 'MCQ sahi', 'Numerical'],
            [[g['name'], f"{g['score']} / {g['maximum']}", pc(g['accuracy']), pc(g['attempt_rate']), g['negative'], g['not_seen'],
              f"{g['types'].get('mcq', {}).get('correct', 0)} / {g['types'].get('mcq', {}).get('count', 0)}",
              f"{g['types'].get('integer', {}).get('correct', 0)} / {g['types'].get('integer', {}).get('count', 0)}"] for g in perf['subjects']],
            [115, 70, 60, 70, 55, 55, 50, 40])
    if perf['weak']:
        s.h2('Marks kis chapter se gaye')
        most = max(g['lost'] for g in perf['weak']) or 1
        for g in perf['weak'][:8]:
            s.bar(f"{g['name']} ({g['subject'][:4]})", g['lost'], most, RED, f"-{g['lost']}  ({g['wrong']} galat, {g['skipped']} chhode)")
        s.y += 6
    chapters = [[g['name'], c['name'], c['count'], c['correct'], c['incorrect'], c['skipped'], pc(c['accuracy']), {'strong': 'Mazboot', 'weak': 'Kamzor', 'steady': 'Theek'}.get(c['label'], '-')]
                for g in perf['subjects'] for c in g['chapters']]
    if chapters:
        s.h2('Chapter-wise')
        s.table(['Subject', 'Chapter', 'Sawaal', 'Sahi', 'Galat', 'Chhode', 'Accuracy', 'Haal'], chapters[:70], [80, 190, 42, 38, 38, 42, 50, 35], 8.5)
    else:
        s.para('Is paper ke sawaalon par chapter ka tag nahi hai, isliye chapter-wise hisaab nahi bana.', 9, MUTE)

    # 3 Score Potential
    s.new()
    pot = an['potential']
    s.h1('3. Score Potential', 'Yahan se marks bach sakte the. Seedha hisaab hai, har step ke peeche ke sawaal likhe hain.')
    step = {x['key']: x for x in pot['steps']}
    most = max(pot['paper_maximum'], 1)
    run = pot['current']
    s.bar('Abhi ka Score', run, most, MUTE, str(run))
    for key, label in (('careless', '+ Careless galti theek'), ('guard', '+ Mushkil par risk nahi'), ('reinvest', '+ Atka time wapas')):
        run += step[key]['marks']
        s.bar(label, run, most, AMBER, f"+{step[key]['marks']}")
    s.bar('Realistic target', pot['realistic'], most, GREEN, str(pot['realistic']))
    s.bar('Maximum potential', pot['maximum'], most, GREEN, str(pot['maximum']))
    s.y += 6
    if not pot['available']:
        s.para('Is attempt mein time record nahi hua, isliye Careless aur Time wale step 0 hain.', 9, MUTE)
    s.para(f"Careless galti ({len(step['careless']['questions'])}): {qn(step['careless']['questions'])}", 9)
    s.para(f"Mushkil par risk ({len(step['guard']['questions'])}): {qn(step['guard']['questions'])}", 9)
    s.para(f"Atka time ({step['reinvest']['minutes']} min) in sawaalon ko dete: {qn(step['reinvest']['questions'])}", 9)
    ranked = [x for x in pot['at'] if x.get('rank')]
    if ranked:
        s.h2('Itne marks par Rank lagbhag')
        s.table(['Score', 'Rank', 'Percentile'], [[x['score'], f"#{x['rank']} / {x['of']}", x['percentile']] for x in ranked], [120, 120, 120])
    g = pot['guess']
    s.h2('Guess ka niyam')
    s.para(f"Is paper mein sahi par +{g['pos']} aur galat par {g['neg']}. Jab aapko {g['break_even']}% se zyada yakeen ho tabhi jawab do. "
           f"4 option mein se 1 bhi pakka hata sako to guess faydemand hai; bilkul andhere mein chhodna behtar. Bina galat jawab ke Score {pot['no_negative']} hota.")

    # 4 Attempt Quality
    s.new()
    quality = an['quality']
    s.h1('4. Attempt Quality', 'Har sawaal ko ek hi tag milta hai. ' + copy['time_label'])
    if quality['available']:
        most = max(an['paper']['count'], 1)
        for key, value in quality['counts'].items():
            if value:
                s.bar(tags[key][0], value, most, GREEN if key == 'perfect' else RED if key in ('wasted', 'costly_overtime', 'concept_gap') else AMBER, str(value))
        s.y += 6
        s.table(['Subject', 'Perfect', 'Careless', 'Concept gap', 'Overtime', 'Confused', 'Smart skip'],
                [[x['name'], x['counts']['perfect'], x['counts']['wasted'], x['counts']['concept_gap'], x['counts']['slow_correct'] + x['counts']['costly_overtime'],
                  x['counts']['confused'], x['counts']['smart_skip']] for x in quality['by_subject']], [130, 60, 60, 75, 65, 60, 65])
        s.h2('Speed-Accuracy map')
        s.para('Har dot ek sawaal hai. Baayein = jaldi, daayein = der. "Par" line ideal time hai.', 8.5, MUTE)
        s.scatter([(q['number'], q['outcome'], q['time'] / q['par']) for q in an['questions'] if q['time'] and q['par'] and q['outcome'] in ('correct', 'incorrect', 'skipped')])
        if quality['painful']:
            s.para(f"Painful sawaal (galat bhi, Par se zyada time bhi): {qn(quality['painful'])}", 9)
        if quality['lucky']:
            s.para(f"Jaldi-sahi (Par ke 25% se kam mein sahi; tukka tha to concept ek baar dekh lo): {qn(quality['lucky'])}", 9)
        s.h2('Tags ke matlab')
        for key in ('perfect', 'slow_correct', 'wasted', 'concept_gap', 'costly_overtime', 'confused', 'smart_skip', 'not_seen'):
            s.para(f'{tags[key][0]}: {tags[key][1]}', 8.5, MUTE)
    else:
        s.para(later)

    # 5 Time
    s.new()
    time = an['time']
    s.h1('5. Time kahan gaya', copy['time_label'])
    if time['available']:
        by = time['by_outcome']
        s.tiles([('Paper mein laga', mmss(time['elapsed'])), ('Screen par', mmss(time['on_screen'])), ('Screen se bahar', mmss(time['off_screen']))])
        s.stack([('Sahi par (sec)', by['correct'], GREEN), ('Galat par (sec)', by['incorrect'], RED), ('Bina jawab (sec)', by['unanswered'], MUTE)])
        share = {x['name']: x for x in time['share']}
        s.table(['Subject', 'Time', 'Time ka hissa', 'Marks ka hissa', 'Attempted', 'Accuracy'],
                [[x['name'], mmss(x['time']), pc(share[x['name']]['time_pct']), pc(share[x['name']]['weight_pct']), f"{x['attempted']} / {x['count']}", pc(x['accuracy'])] for x in time['by_subject']],
                [130, 80, 85, 85, 70, 65])
        s.h2('Time journey')
        s.blocks([(f"{b['from'] // 60}-{b['to'] // 60}m", b['correct'], b['incorrect']) for b in time['blocks']])
        split = time.get('pace_split')
        if time['pace'] and split:
            s.h2('Pace curve')
            s.lines([('Sab jawab', time['pace'], INK), ('Sahi', split['correct'], GREEN), ('Galat', split['incorrect'], RED)], '0 min', f"{round(an['paper']['duration'] / 60)} min")
        look = time['first_look']
        s.h2('Pehli nazar vs wapas aakar')
        s.table(['Kab jawab diya', 'Jawab', 'Sahi', 'Accuracy', 'Time'],
                [[label, look[k]['count'], look[k]['correct'], pc(look[k]['accuracy']), mmss(look[k]['time'])] for k, label in (('first', 'Pehli nazar mein'), ('return', 'Wapas aakar'))], [170, 80, 80, 90, 95])
        s.h2('Sabse dheeme 5 sawaal')
        s.table(['Sawaal', 'Subject', 'Aapka time', 'Par time', 'Result'],
                [['Q' + str(rows[i]['number']), rows[i]['subject'], mmss(rows[i]['time']), mmss(rows[i]['par']), RESULT.get(rows[i]['outcome'], '-')] for i in time['slowest']], [80, 150, 95, 95, 95])
    else:
        s.para(later)

    # 6 Difficulty + Journey
    s.new()
    diff = an['difficulty']
    s.h1('6. Difficulty', 'Easy sawaal chhootna sabse mehnga padta hai. Jahan students ka data kam hai wahan "Not rated" likha hai, andaaza nahi lagaya.')
    s.table(['Level', 'Sawaal', 'Sahi', 'Galat', 'Chhode', 'Accuracy'],
            [[L[l], x['count'], x['correct'], x['incorrect'], x['skipped'], pc(x['accuracy'])] for l, x in diff['all'].items() if x['count']], [130, 75, 75, 75, 75, 85])
    s.para('Level kahan se aaya: ' + ', '.join(f'{n} sawaal {SOURCE.get(k, k)}' for k, n in diff['sources'].items()) + '.', 9, MUTE)
    leak = diff['leak']
    s.para(f"Leak: {len(leak['wrong'])} Easy galat ({qn(leak['wrong'])}) aur {len(leak['skipped'])} Easy chhoote ({qn(leak['skipped'])}). Yahan se {leak['marks']} marks bach sakte the.")
    if diff['tough_solved']:
        s.para(f"Tough jo aapne nikale: {qn(diff['tough_solved'])}.")
    trip, habits = an['journey'], an['habits']
    s.y += 8
    s.h1('7. Question Journey')
    if trip['available']:
        t = trip['summary']
        s.para(f"{t['total']} mein se {t['visited']} sawaal dekhe, {t['revisits']} baar wapas gaye, {t['thrice']} sawaal 3 ya zyada baar dekhe. Subject order: {' -> '.join(trip['order']) or '-'}.")
    else:
        s.para(later, 9, MUTE)
    ch = habits['changes']
    if ch['total']:
        g = ch['groups']
        s.para(f"Jawab badle: {ch['total']}. Galat se sahi {len(g['w2r'])}, sahi se galat {len(g['r2w'])}, galat se galat {len(g['w2w'])}, jawab hataya {len(g['r2s']) + len(g['w2s'])}. "
               f"Is badlav se net {'+' if ch['marks'] > 0 else ''}{ch['marks']} marks.")
    if habits['streaks']:
        s.para(f"Sabse lambi streak: {habits['streaks']['correct']} sahi lagataar, {habits['streaks']['incorrect']} galat lagataar.")
    if habits['last']:
        z = habits['last']
        s.para(f"Aakhri 20% time mein Accuracy {pc(z['late']['accuracy'])} ({z['late']['count']} jawab), usse pehle {pc(z['early']['accuracy'])} ({z['early']['count']} jawab).")
    if trip['available']:
        s.y += 4
        line = '  '.join(f"Q{v['n']}" + (f"({v['v']})" if v['v'] > 1 else '') for v in trip['visits'][:260])
        s.para('Aapka raasta (bracket = kaun si baar): ' + line, 8, MUTE)

    # 8 Qs by Qs
    s.new()
    s.h1('8. Qs by Qs', 'Har sawaal ka poora hisaab. Class ke column tab bharte hain jab kaafi students ne paper diya ho.')
    s.table(['Q', 'Subject', 'Level', 'Aapka', 'Sahi', 'Result', 'Marks', 'Time', 'Par', 'Class avg', 'Topper', 'Class %', 'Tag'],
            [[q['number'], q['subject'][:10], L[q['difficulty']], q['response'] or '-', q['answer'], RESULT.get(q['outcome'], '-'), q['marks'], mmss(q['time']),
              mmss(q['par']), mmss((q['class'] or {}).get('avg_time')), mmss((q['class'] or {}).get('topper_time')), pc((q['class'] or {}).get('correct')),
              tags[q['tag']][0] if q['tag'] else '-'] for q in an['questions']],
            [22, 54, 44, 32, 34, 38, 30, 42, 42, 44, 42, 36, 55], 7)
    return s.done()


def share_png(an):
    """Scorecard for WhatsApp: Score, Rank, Percentile and the display name if the student set one. Never the phone number."""
    import matplotlib
    from PIL import Image, ImageDraw, ImageFont
    base = matplotlib.get_data_path() + '/fonts/ttf/DejaVuSans'
    font = lambda size, bold=True: ImageFont.truetype(base + ('-Bold.ttf' if bold else '.ttf'), size)
    o, name = an['overview'], (an.get('student') or {}).get('name')
    img = Image.new('RGB', (1080, 1350), '#08080A')
    d = ImageDraw.Draw(img)
    d.rectangle((0, 0, 1080, 14), fill='#D91222')
    d.text((72, 80), 'JEELIVE.AI', font=font(44), fill='#FF6974')
    d.text((72, 150), plain(' · '.join(x for x in ((an.get('exam') or '').upper(), name) if x)), font=font(26, False), fill='#B0B0BF')
    y = 215
    for line in textwrap.wrap(plain(an.get('title') or 'Mock'), 30)[:3]:
        d.text((72, y), line, font=font(50), fill='#F8FAFC')
        y += 66
    d.rounded_rectangle((72, 470, 1008, 800), 36, fill='#14141C', outline='#67202C', width=3)
    d.text((112, 505), 'SCORE', font=font(30), fill='#B0B0BF')
    d.text((112, 560), str(o['score']), font=font(170), fill='#F8FAFC')
    d.text((112 + d.textlength(str(o['score']), font=font(170)) + 20, 680), f"/ {o['maximum']}", font=font(56, False), fill='#B0B0BF')
    tiles = [('RANK', f"#{o['rank']}" if o.get('rank') else '-', f"{o['of']} mein se" if o.get('rank') else 'Result ke baad'),
             ('PERCENTILE', str(o.get('percentile', '-')), 'is paper par'), ('ACCURACY', pc(o['accuracy']), f"{o['correct']} sahi / {o['attempted']}")]
    for i, (label, value, note) in enumerate(tiles):
        x = 72 + i * 320
        d.rounded_rectangle((x, 850, x + 296, 1090), 28, fill='#0F0F14', outline='#2A2A38', width=2)
        d.text((x + 28, 880), label, font=font(24), fill='#B0B0BF')
        d.text((x + 28, 930), value, font=font(64), fill='#FF6974' if i == 0 else '#F8FAFC')
        d.text((x + 28, 1030), note, font=font(22, False), fill='#9292A5')
    d.text((72, 1160), f"{when(an):%d %b %Y}", font=font(28, False), fill='#B0B0BF')
    d.text((72, 1215), 'Free mock tests + poora analysis: jeelive.ai', font=font(30), fill='#F8FAFC')
    out = io.BytesIO()
    img.save(out, 'PNG', optimize=True)
    return out.getvalue()
