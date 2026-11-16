"""TEST-ONLY iteration 190: replays the page reader over a chapter-wise PDF whose chapters print Questions -> Answer key -> Solutions.
Run: cd /app/backend && python tests/chapter_solutions_replay190.py /tmp/maths.pdf [plan] [DEBUG]
No database: pure reader replay. Prints per chapter: questions, solutions, keys, answered, conflicts, then the issue counts.
"""
import sys, collections
sys.path.insert(0, '/app/backend')
from tejas.book_pdf import inspect, inspect_many  # noqa: E402
from tejas.book_reader import read_page  # noqa: E402
from tejas.chapter_reader import plan_start, bookmark_plan  # noqa: E402

SRC = sys.argv[1]
FORCE_PLAN = 'plan' in sys.argv[2:]
info = inspect(SRC)
toc = inspect(SRC, 'toc')['toc']
pages = list(range(1, info['pages'] + 1))
data = dict(zip(pages, inspect_many(SRC, [{'action': 'text', 'page': n} for n in pages], 10)))


def run(plan):
    context = {'chapters': True, 'plan': bool(plan)}
    plan_at = {}
    for e in plan or []:
        plan_at.setdefault(e['page'], []).append(e)
    out = []
    for n in pages:
        for e in plan_at.get(n, []):
            context = plan_start(context, e)
        mapped, context = read_page(data[n]['lines'], context, data[n].get('geometry', []), data[n].get('images', []))
        out.append((n, mapped))
    return out


plan = bookmark_plan(toc, info['pages']) if FORCE_PLAN else None
print('pages', len(pages), 'plan entries', len(plan or []))
chapters, issues = collections.OrderedDict(), collections.Counter()
for n, m in run(plan):
    for r in m.regions:
        if r.role in ('question', 'solution', 'key'):
            c = chapters.setdefault(r.mock or '?', {'question': set(), 'solution': set(), 'key': set(), 'answered': set(), 'pages': set(), 'ans': {}, 'conflicts': set()})
            c[r.role].add(r.number)
            c['pages'].add(n)
            if r.answer:
                c['answered'].add(r.number)
                if r.role in ('key', 'solution'):
                    if c['ans'].get(r.number, r.answer) != r.answer:
                        c['conflicts'].add(r.number)
                    c['ans'][r.number] = r.answer
    for i in m.issues:
        issues[i[:90]] += 1
        if 'DEBUG' in sys.argv:
            print('ISSUE page', n, i[:90])
    if m.classification == 'unresolved':
        issues[f'unresolved page {n}'] += 1
for label, c in chapters.items():
    q, s = c['question'], c['solution']
    print(f"{label[:34]:34} q={len(q):3} s={len(s):3} key={len(c['key']):3} answered={len(c['answered']):3} pages={min(c['pages'])}-{max(c['pages'])} missing_s={sorted(q - s)[:6]} conflicts={sorted(c['conflicts'])[:6]}")
print('CHAPTERS', len(chapters), 'ISSUES', issues.most_common(12))
