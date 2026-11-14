"""TEST-ONLY: run the real page reader + real mock rebuild over a whole mock-book PDF in memory (no DB writes)."""
import asyncio, json, os, re, sys, time
from collections import Counter
from pathlib import Path
from types import SimpleNamespace
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from dotenv import load_dotenv  # noqa: E402
load_dotenv(Path(__file__).resolve().parents[1] / '.env')  # client object only; nothing is read or written
from tejas.book_pdf import inspect, inspect_many  # noqa: E402
from tejas.book_reader import read_page  # noqa: E402
from tejas.book_models import BookPage  # noqa: E402
from tejas.book_store import identity  # noqa: E402
import tejas.book_publish as P  # noqa: E402

src = sys.argv[1]
limit = int(sys.argv[2]) if len(sys.argv) > 2 else 0
pages_n = inspect(src)['pages']; n = min(pages_n, limit) if limit else pages_n
t = time.time(); data = []
for start in range(1, n + 1, 50):
    nums = list(range(start, min(n, start + 49) + 1))
    data.extend(zip(nums, inspect_many(src, [{'action': 'text', 'page': k} for k in nums], 10)))
print('extracted', len(data), 'pages', round(time.time() - t, 1), 's', flush=True)
context, pages, page_issues = {}, [], Counter()
for number, d in data:
    mapped, context = read_page(d['lines'], context, d.get('geometry', []), d.get('images', []))
    pages.append(BookPage(id=identity('TEST', 'page', number), book_id='TEST', number=number, **mapped.model_dump(),
                          text='\n'.join(x['text'] for x in d['lines']), context=context, provenance={'kind': 'native'}))
    for x in mapped.issues: page_issues[re.sub(r'\d+', '#', x)] += 1
print('PAGE ISSUES', sum(page_issues.values()), 'pages with issues', sum(bool(p.issues) for p in pages))
for k, v in page_issues.most_common(12): print('  ', v, k)
saved = {}


async def pages_for(book): return pages
async def mocks_for(book): return list(saved.values())
async def save_mock(mock): saved[mock.id] = mock
async def fence(book, token): return None
async def now_(): return time.time()
P.pages_for, P.mocks_for, P.save_mock, P.fence, P.database_now = pages_for, mocks_for, save_mock, fence, now_


async def main():
    await P.rebuild(SimpleNamespace(id='TEST', payload={}), 'token')
    mocks = sorted(saved.values(), key=lambda m: m.order)
    print('MOCKS', len(mocks), Counter(m.state for m in mocks), 'total issues', sum(len(m.issues) for m in mocks))
    print('rules set', sum(bool(m.rules) for m in mocks), 'questions per mock', Counter(len(m.questions) for m in mocks).most_common(4))
    agg = Counter(re.sub(r'\d+', '#', x) for m in mocks for x in m.issues)
    examples = {}
    for m in mocks:
        for x in m.issues: examples.setdefault(re.sub(r'\d+', '#', x), []).append(m.label + ' :: ' + x)
    for k, v in agg.most_common(15): print('  ', v, k[:170], '|', ' || '.join(e[:90] for e in examples[k][:int(os.environ.get('EXAMPLES', 3))]))
    if os.environ.get('DUMP'):
        json.dump({m.label: m.issues for m in mocks}, open(os.environ['DUMP'], 'w'), indent=1)
    if os.environ.get('AUDIT'):
        by_page = {p.number: p for p in pages}; flags = Counter(); rows = []
        for m in mocks:
            for q in m.questions:
                regs = q['source_regions']['question']
                text = '\n'.join(r.text for g in regs for r in by_page[g['page']].regions if r.rect == g['rect'])
                other = [int(x) for x in re.findall(r'(?m)^(?:Question\s+)?(\d{1,3})[.)]\s', text) if int(x) != q['number']]
                if q['type'] == 'mcq' and len(q['options']) != 4: flags['mcq without 4 options'] += 1
                if not q['answer']: flags['no key'] += 1
                if other: flags['crop contains another question number'] += 1
                if any(g['rect'][3] - g['rect'][1] > .6 for g in regs): flags['question crop taller than 60% page'] += 1
                if m.rules.get('solution_policy') == 'original_expected' and not q['source_regions']['solution']: flags['solution missing'] += 1
                rows.append({'mock': m.label, 'state': m.state, 'n': q['number'], 'type': q['type'], 'answer': q['answer'], 'q': regs, 's': q['source_regions']['solution']})
        print('AUDIT questions', len(rows), dict(flags), 'types', Counter(r['type'] for r in rows))
        json.dump(rows, open(os.environ['AUDIT'], 'w'))
    if mocks:
        m = mocks[0]; print('MOCK1', m.label, m.state, m.rules and {k: m.rules[k] for k in ('exam', 'minutes', 'expected_questions', 'correct', 'wrong', 'mechanic', 'bonus_count', 'solution_policy')})
        print('  pages', {k: (v[:3], len(v)) for k, v in m.pages.items()})
        for q in m.questions[:2] + m.questions[-2:]:
            print('  Q', q['number'], q['subject'], q['type'], q['answer'], list(q['options']), q['solution_kind'], len(q['source_regions']['question']), len(q['source_regions']['solution']))
        print('  issues sample', m.issues[:8])

asyncio.run(main())
