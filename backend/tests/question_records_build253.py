"""TEST-ONLY iteration 253 (pocket C1a): the records at full size, made from the owner's own books as the app's reader took them
(/root/link/real_a.pkl and real_b.pkl = AITS 01-25 and 26-50, /root/link/draft.pkl = Chemistry chapter-wise, 1,250 questions).
Only build() is run: no database is read or written, no storage, no AI. A half of the AITS whose pickle has no question words is left out.
Run: cd /app/backend && python -u tests/question_records_build253.py
"""
import collections, copy, json, os, pickle, sys, time
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from dotenv import load_dotenv  # noqa: E402
load_dotenv('/app/backend/.env')  # import only; no database access in this test
from tejas import question_records as QR, question_link as L  # noqa: E402
from tejas.book_store import identity  # noqa: E402

RESULTS = []
SLUG = 'jee-main'


def check(name, ok, detail=''):
    RESULTS.append((name, bool(ok)))
    print(('PASS ' if ok else 'FAIL ') + name + ('' if ok else ' :: ' + str(detail)[:700]), flush=True)


def papers(tag):
    path = f'/root/link/real_{tag}.pkl'
    rows = pickle.load(open(path, 'rb')) if os.path.exists(path) else []
    if not rows or 'text' not in rows[0]:
        return []
    by = collections.OrderedDict()
    for r in rows:
        m = by.setdefault(r['mock_id'], {'_id': r['mock_id'], 'book_id': 'aits-' + tag, 'label': r['label'], 'order': r['order'], 'questions': []})
        m['questions'].append({'id': r['id'], 'text': r['text'], 'type': r['type'], 'answer': r['answer'], 'original_number': r['addr'][1], 'number': r['addr'][1], 'subject': r['subject']})
    return list(by.values())


def chapters():
    by = collections.OrderedDict()
    for i, r in enumerate(pickle.load(open('/root/link/draft.pkl', 'rb'))):
        m = by.setdefault(r['mock'], {'_id': r['mock'], 'book_id': 'chem', 'label': r['label'], 'order': len(by) + 1, 'questions': [],
                                      'chapter': {'number': r['ch'][0], 'title': r['chapter'], 'subject': 'Chemistry'}})
        m['questions'].append({'id': f'chem-{i}', 'text': r['text'], 'type': r['type'], 'answer': r['ans'], 'original_number': r['n'], 'number': r['n'], 'subject': 'Chemistry'})
    return list(by.values())


def book(side, title, rank):
    return {'side': side, 'title': title, 'archived': False, 'series_id': 'all-india-jee-2026-27' if side == 'paper' else '', 'rank': rank}


def stored(docs):
    return {k: {f: v[f] for f in ('words_sha', 'type', 'answer', 'first')} for k, v in docs.items()}


def main():
    halves = {t: papers(t) for t in 'ab'}
    halves = {t: m for t, m in halves.items() if m}
    if not halves or not os.path.exists('/root/link/draft.pkl'):
        print("SKIP the owner's books (with their question words) are not on this machine", flush=True)
        return
    chem = chapters()
    books = {'aits-' + t: book('paper', 'AITS ' + t.upper(), i) for i, t in enumerate(halves)}
    books['chem'] = book('chapter', 'Chemistry chapter-wise', len(books))
    mocks = [m for ms in halves.values() for m in ms] + chem
    paper_n = sum(len(m['questions']) for ms in halves.values() for m in ms)
    printed = {L.address(q['text'])[:3] for ms in halves.values() for m in ms for q in m['questions']}
    chap = [L.address(q['text'])[:3] for m in chem for q in m['questions']]
    both = sum(a in printed for a in chap)
    print(f'  AITS halves with words: {sorted(halves)} | paper questions {paper_n} | chapter questions {len(chap)} | chapter questions whose paper is here {both}', flush=True)
    t = time.time(); docs, s = QR.build(SLUG, books, mocks, {}, 1.0); took = time.time() - t
    size = sum(len(json.dumps(d)) for d in docs.values())
    print(f'  build: {len(docs)} records in {took:.2f} s | {size / 1e6:.1f} MB as stored', flush=True)
    want = {'records': paper_n + len(chap) - both, 'linked': both, 'paper': paper_n - both, 'chapter': len(chap) - both, 'review': 0, 'bare': 0, 'changed': 0}
    got = {k: s[k] for k in want}
    check('one record per printed address: every paper question, every chapter question; a question printed in both is one record', got == want and len(printed) == paper_n, (got, want))
    if len(halves) == 2:
        check('both halves of the AITS are here: 3,750 records, all 1,250 chemistry chapter questions joined to their paper, none left for the owner',
              got == {'records': 3750, 'linked': 1250, 'paper': 2500, 'chapter': 0, 'review': 0, 'bare': 0, 'changed': 0}, got)
    linked = [d for d in docs.values() if d['state'] == 'linked']
    bad = [d['address'] for d in linked if not (d.get('chapter') or {}).get('name') or d['subject'] != 'Chemistry' or [p['side'] for p in d['places']] != ['paper', 'chapter'] or len(d['qids']) != 2
           or not d['has_paper'] or not d['has_chapter'] or d['series_id'] != 'all-india-jee-2026-27' or d['first'] != 'paper']
    check('every joined record: the paper place and the chapter place, both question ids, its chapter name, Chemistry, its series', len(linked) == both and not bad, bad[:5])
    heads = [d['address'] for d in docs.values() if d['text'].lstrip().lower().startswith(('question', 'source', 'mock ', 'ch 0', 'ch 1', 'ch 2'))]
    check("a record's words are the question's own: no number line, no address line, no place line; never longer than 8,000", not heads and max(len(d['text']) for d in docs.values()) <= 8000, heads[:5])
    ids = {identity('question-record', SLUG, L.letters('AITS Mock'), d['mock'], d['q']) for d in docs.values()}
    check('the record of an address is always the same one (its id is made from exam, series, mock and question)', ids == set(docs) and all(d['exam_slug'] == SLUG for d in docs.values()), len(ids))
    rows = s['mocks']
    check('each paper says how many of its 75 are joined: 25 (its Chemistry) in every mock', len(rows) == paper_n // 75 and all(r['questions'] == 75 and r['linked'] == 25 and r['review'] == 0 and r['label'] == f"Mock {r['mock']}" for r in rows),
          [r for r in rows if r['linked'] != 25][:4])
    check('the uploads are named with what was read from each; every question of every upload printed an address', [(b['side'], b['questions'], b['addressed']) for b in s['books']]
          == [('paper', len(m) * 75, len(m) * 75) for m in halves.values()] + [('chapter', len(chap), len(chap))], s['books'])
    again, s2 = QR.build(SLUG, books, copy.deepcopy(mocks), {}, 1.0)
    check('the same Drafts give the same records, to the letter', again == docs and s2 == s, '')
    first = {**{k: {**v, 'rank': v['rank'] + 1} for k, v in books.items() if k != 'chem'}, 'chem': book('chapter', 'Chemistry chapter-wise', 0)}
    turned, _ = QR.build(SLUG, first, mocks, {}, 1.0)
    check('the chapter-wise book uploaded BEFORE the papers: the very same records', turned == docs, [k for k in docs if turned.get(k) != docs[k]][:3])
    alone, sa = QR.build(SLUG, {'chem': book('chapter', 'Chemistry chapter-wise', 0)}, chem, {}, 1.0)
    check('the chapter-wise book alone (no paper yet): every question already has its record under its printed address', sa['records'] == sa['chapter'] == len(chap) and sa['linked'] == 0 and set(alone) <= set(docs)
          and all(d['first'] == 'chapter' for d in alone.values()), (sa['records'], sa['chapter']))
    later, sl = QR.build(SLUG, books, mocks, stored(alone), 2.0)
    check('...then the papers arrive: the same records are joined; none is called "changed" for that', later == docs and sl['changed'] == 0, sl['changed'])
    _, s3 = QR.build(SLUG, books, mocks, stored(docs), 2.0)
    check('a second run over the same Drafts calls nothing "changed"', s3['changed'] == 0 and {k: s3[k] for k in want} == want, s3['changed'])
    # One paper answer is corrected after the join was made (TEST: on a copy of the Drafts).
    edit = copy.deepcopy(mocks)
    target = next(d for d in linked if d['type'] == 'mcq')
    q = next(q for m in edit for q in m['questions'] if q['id'] in target['qids'] and m['book_id'] != 'chem')
    old = q['answer']; q['answer'] = next(x for x in 'ABCD' if x != old)
    d4, s4 = QR.build(SLUG, books, edit, stored(docs), 3.0)
    rid = next(k for k, d in docs.items() if d is target)
    check("a paper's answer corrected, its chapter copy not: counted as changed once, no longer joined, on the owner's list with both answers",
          s4['changed'] == 1 and s4['review'] == 1 and s4['linked'] == both - 1 and d4[rid]['state'] == 'review' and d4[rid]['changed']['answer'] == old and d4[rid]['changed']['words'] is False
          and f"jawab alag: {q['answer']} aur {old}" in d4[rid]['problems'][0]['say'] and d4[rid]['problems'][0]['with'].startswith('Chapter-wise · '), (s4['changed'], s4['review'], d4[rid].get('problems')))
    # Two chapter questions print each other's address (a misprint). Neither may be joined to the other's paper question.
    edit = copy.deepcopy(mocks)
    pair = [q for m in edit if m['book_id'] == 'chem' for q in m['questions'] if q['type'] == 'mcq' and L.address(q['text'])[:3] in printed][:400:399]
    a, b = (L.address(q['text'])[3] for q in pair)
    pair[0]['text'], pair[1]['text'] = pair[0]['text'].replace(a, b), pair[1]['text'].replace(b, a)
    d5, s5 = QR.build(SLUG, books, edit, {}, 1.0)
    shut = [d for d in d5.values() if d['state'] == 'review']
    check('two chapter questions that print each other\'s address: neither is joined; both go to the owner with the reason', s5['review'] == 2 and s5['linked'] == both - 2 and {d['address'] for d in shut} == {a, b}
          and all(p['say'].startswith('Pata wahi') for d in shut for p in d['problems']), (s5['review'], [(d['address'], d['problems']) for d in shut][:2]))
    # The same paper uploaded a second time (another upload of the same pages).
    twin = {**books, 'again': book('paper', 'AITS again', len(books))}
    tag = next(iter(halves))
    more = mocks + [{**m, '_id': m['_id'] + '-2', 'book_id': 'again', 'questions': [{**q, 'id': q['id'] + '-2'} for q in m['questions']]} for m in halves[tag]]
    d6, s6 = QR.build(SLUG, twin, more, {}, 1.0)
    check('the same papers uploaded twice: still one record per question, nothing sent to the owner', {k: s6[k] for k in want} == want and set(d6) == set(docs)
          and all(len(d6[k]['places']) == len(docs[k]['places']) + 1 for k in docs if docs[k]['places'][0]['book_id'] == 'aits-' + tag), {k: s6[k] for k in want})
    bad = [n for n, ok in RESULTS if not ok]
    print(f'TOTAL {len(RESULTS)} PASS {len(RESULTS) - len(bad)} FAIL {len(bad)}', flush=True)


if __name__ == '__main__':
    main()
