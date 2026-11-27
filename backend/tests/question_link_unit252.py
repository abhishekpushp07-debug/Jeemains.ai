"""TEST-ONLY iteration 252 (pocket C1a): the plain reading behind "one question, one record": the printed address, a question's own
words, and the locks (same kind, same answer, words alike). No database, no storage, no AI.
Made-up questions first; then, when they are on this machine, the owner's own books as the app's reader took them
(/root/link/real_b.pkl = AITS 26-50, /root/link/draft.pkl = Chemistry chapter-wise): every true pair opens, every wrong pair stays shut.
Run: cd /app/backend && python tests/question_link_unit252.py
"""
import collections, itertools, os, pickle, random, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from dotenv import load_dotenv  # noqa: E402
load_dotenv('/app/backend/.env')  # import only; no database access in this test
from tejas import question_link as L  # noqa: E402

RESULTS = []
PAPER = 'Question 68\nSource: AITS Mock 04 / Q68\nMOCK 04 / Chemistry / Single-correct MCQ\nA 4.68 g mixture contains only CaCO3 and MgCO3. Find the mole fraction of CaCO3 in the mixture given.\n(A) 1/2\n(B) 2/5\n(C) 3/5\n(D) 25/39'
CHAPTER = 'Question 1\nSource: AITS Mock 04 / Q68\nCH 01 / Mole Concept and Stoichiometry\nA 4.68 g mixture contains only CaCO3 and\nMgCO3. Find the mole fraction of CaCO3 in the mixture given.\n(A) 1/2\n(B) 2/5\n(C) 3/5\n(D) 25/39'
NUMERIC = 'Question 71\nSource: AITS Mock 01 / Q71\nMOCK 01 / Chemistry / Numerical value\nA charge of 0.120 mol CH4 reacts to completion. Find the total final dry-gas amount in millimoles.'


def check(name, ok, detail=''):
    RESULTS.append((name, bool(ok)))
    print(('PASS ' if ok else 'FAIL ') + name + ('' if ok else ' :: ' + str(detail)[:700]), flush=True)


def made_up():
    a = L.address(PAPER)
    check('the address is read from a heading line: series, mock, question, as printed', a == ('aitsmock', 4, 68, 'AITS Mock 04 / Q68'), a)
    forms = {'Q1\nSource : aits  mock 4 / q 68\nbody': ('aitsmock', 4, 68), 'Source: AITS Mock 104 / Q.7\nbody': ('aitsmock', 104, 7),
             'Question 3\nSource: Full Test 2027 Paper 12 / Q075\nbody': ('fulltest2027paper', 12, 75)}
    got = {k: (L.address(k) or ())[:3] for k in forms}
    check('spacing, capitals, leading zeros and a dot after Q do not change the address; another series is another series', got == forms, got)
    none = ['A ball is thrown.\nMore words\nAnd more\nAnd more\nSource: AITS Mock 04 / Q68', 'Question 2\nSource: JEE Main 2019 (9 Jan, Shift 1)\nbody', 'Question 2\nbody only', '', None,
            'Question 5\nThe Source: AITS Mock 04 / Q68 is quoted inside a sentence']
    check('no address: the line below the heading, a source that is not "N / Q N", no line, a quote inside a sentence, nothing', [L.address(t) for t in none] == [None] * len(none), [L.address(t) for t in none])
    check("a question's own words: its number, its address and the place line under it are left out; the rest is as printed",
          L.body(PAPER).startswith('A 4.68 g mixture') and L.body(CHAPTER).startswith('A 4.68 g mixture') and 'Source' not in L.body(PAPER) and 'CH 01' not in L.body(CHAPTER) and 'MOCK 04' not in L.body(PAPER)
          and L.body(PAPER).endswith('(D) 25/39'), (L.body(PAPER)[:60], L.body(CHAPTER)[:60]))
    check('a paper that prints no address: only its printed number is left out', L.body('Q5. A ball is thrown up.\n(A) 1') == 'A ball is thrown up.\n(A) 1' and L.body('12) Find x.') == 'Find x.'
          and L.body('5 g of salt is dissolved.') == '5 g of salt is dissolved.', (L.body('Q5. A ball is thrown up.\n(A) 1'), L.body('5 g of salt is dissolved.')))
    check('...and a number on a line of its own, with the place line under it', L.body('Question 56\nMOCK 07 / Chemistry / Single-correct MCQ\nWhich one?\n(A) 1') == 'Which one?\n(A) 1'
          and L.body('Question 56\nWhich one is 5 / 2?') == 'Which one is 5 / 2?' and L.body('Question 56') == 'Question 56', (L.body('Question 56\nMOCK 07 / Chemistry / Single-correct MCQ\nWhich one?\n(A) 1'), L.body('Question 56\nWhich one is 5 / 2?')))
    check('the chapter printed under the address is read; a paper has none', L.chapter_name(CHAPTER) == 'Mole Concept and Stoichiometry' and L.chapter_name(PAPER) == '' and L.chapter_name('Q1\nbody') == '',
          (L.chapter_name(CHAPTER), L.chapter_name(PAPER)))
    check("a paper's own number comes from its heading", [L.mock_number(x) for x in ('Mock 04', 'Mock 26', 'JEE Main Mock Test 7', 'Chapter one', '', None)] == [4, 26, 7, None, None, None],
          [L.mock_number(x) for x in ('Mock 04', 'Mock 26', 'JEE Main Mock Test 7', 'Chapter one', '', None)])
    p, c = L.read(PAPER, 'mcq', 'C'), L.read(CHAPTER, 'mcq', 'C')
    check('the two copies of one question: every lock opens (a line broken elsewhere changes nothing)', L.locks(p, c) is None and p['letters'] == c['letters'] and p['value'] == '3/5' and p['distinct'], (L.locks(p, c), p['value'], p['distinct']))
    shuffled = CHAPTER.replace('(A) 1/2\n(B) 2/5\n(C) 3/5\n(D) 25/39', '(A) 3/5\n(B) 25/39\n(C) 1/2\n(D) 2/5')
    s = L.read(shuffled, 'mcq', 'A')
    check('options printed in another order, the right one now (A): still the same question (its words are compared, not its letter)', L.locks(p, s) is None and s['value'] == '3/5', (L.locks(p, s), s['value']))
    wrong = L.locks(p, L.read(shuffled, 'mcq', 'C'))
    check('...and the old letter on the shuffled copy is another answer: the lock stays shut and says both answers', wrong and wrong['code'] == 'answer' and 'C aur C' not in wrong['say'], wrong)
    shut = L.locks(p, L.read(CHAPTER, 'mcq', 'D'))
    check('same address, another answer: shut, with both answers in the reason', shut and shut['code'] == 'answer' and 'C aur D' in shut['say'], shut)
    shut = L.locks(p, L.read(CHAPTER.replace('(C) 3/5', '(C) 4/5'), 'mcq', 'C'))
    check('same letter, but that option now says something else: shut', shut and shut['code'] == 'answer' and 'shabd alag' in shut['say'], shut)
    shut = L.locks(p, L.read(CHAPTER, 'integer', 'C'))
    check('one is an MCQ, the other numerical: shut', shut and shut['code'] == 'type' and 'MCQ' in shut['say'] and 'numerical' in shut['say'], shut)
    shut = L.locks(p, L.read(CHAPTER, 'mcq', ''))
    check('a copy whose key has no answer yet is not joined', shut and shut['code'] == 'answer' and 'key' in shut['say'], shut)
    other = CHAPTER.replace('A 4.68 g mixture contains only CaCO3 and\nMgCO3. Find the mole fraction of CaCO3 in the mixture given.', 'The oxidation number of manganese in potassium permanganate is to be found here.')
    shut = L.locks(p, L.read(other, 'mcq', 'C'))
    check('same address, same answer, another question: shut by its words, with the percentage', shut and shut['code'] == 'words' and '%' in shut['say'], shut)
    typo = L.read(CHAPTER.replace('mixture contains', 'mixtrue contains'), 'mcq', 'C')
    check('a small misprint in one copy does not break the join', L.locks(p, typo) is None and .8 < L.words_alike(p, typo) < 1, L.words_alike(p, typo))
    same = 'Given below are two statements.\nStatement I: {}\nStatement II: {}\nChoose the correct answer.\n(A) Both Statement I and Statement II are correct\n(B) Both Statement I and Statement II are incorrect\n(C) Statement I is correct but Statement II is incorrect\n(D) Statement I is incorrect but Statement II is correct'
    one, two = (L.read('Q9. ' + same.format(*s), 'mcq', 'A') for s in (('Ice floats on water.', 'Ice is less dense.'), ('Zinc displaces copper.', 'Zinc is more reactive.')))
    shut = L.locks(one, two)
    check('two different questions that share the very same four options and the same answer: shut by the words above the options', shut and shut['code'] == 'words' and one['value'] == two['value'] != '', (shut, L.words_alike(one, two)))
    n = L.read(NUMERIC, 'integer', '180')
    same = [L.locks(n, L.read(NUMERIC, 'integer', v)) for v in ('180', ' 180 ', '180.0', '+180', '0180')]
    check('a numerical answer is compared as a number: 180, 180.0, +180, 0180', same == [None] * 5, same)
    minus = [L.locks(L.read(NUMERIC, 'integer', '-1'), L.read(NUMERIC, 'integer', v)) for v in ('\u22121', '-1', '-1.0')]
    check('every kind of minus sign is one sign', minus == [None] * 3, minus)
    shut = L.locks(n, L.read(NUMERIC, 'integer', '181'))
    check('another number: shut', shut and shut['code'] == 'answer' and '180 aur 181' in shut['say'], shut)
    inline = L.read('Q1. The SI unit of force is the\n(A) joule   (B) newton\n(C) watt   (D) pascal', 'mcq', 'B')
    check('options not printed one below another: nothing is guessed from them; the letter decides', inline['value'] == '' and not inline['distinct'] and L.locks(inline, inline) is None
          and L.locks(inline, {**inline, 'answer': 'C'})['code'] == 'answer', (inline['value'], inline['distinct']))
    twin = L.read('Q1. Pick the structure.\n(A) CH3\n(B) CH3\n(C) H3C\n(D) H3C', 'mcq', 'B')
    check('options that read alike (drawn structures): the letter and that option must both agree', not twin['distinct'] and L.locks(twin, twin) is None and L.locks(twin, {**twin, 'answer': 'A'})['code'] == 'answer', twin['distinct'])
    match = 'Q4. Match List-I with List-II.\n(A)\n{}\n(I)\nnewton\n(B)\n{}\n(II)\njoule\n(C)\nPower\n(III)\nwatt\n(D)\nPressure\n(IV)\npascal\nChoose the correct answer.\n(A) (A)-(I), (B)-(II)\n(B) (A)-(II), (B)-(I)\n(C) (A)-(III), (B)-(IV)\n(D) (A)-(IV), (B)-(III)'
    m1, m2 = L.read(match.format('Force', 'Work'), 'mcq', 'A'), L.read(match.format('Latent heat of fusion of ice', 'Thermal conductivity of a metal rod'), 'mcq', 'A')
    check('Match-the-list: the letters are printed twice; the options are the last four, and the list above them is part of the question',
          m1['value'] == '(a)-(i),(b)-(ii)' and m1['distinct'] and 'force' in m1['stem'] and 'pascal' in m1['stem'] and L.locks(m1, m1) is None and (L.locks(m1, m2) or {}).get('code') == 'words',
          (m1['value'], m1['stem'][:60], L.locks(m1, m2), L.words_alike(m1, m2)))
    check('alike(): the same letters 1, nothing in common 0, an empty copy 0', L.alike('abcdefgh', 'abcdefgh') == 1 and L.alike('abcdefgh', 'zzzzzzzzzz') == 0 and L.alike('', 'abc') == 0 and L.alike('', '') == 1, '')


def damage(word, share, rnd):
    out = []
    for ch in word:
        x = rnd.random()
        if x < share / 2:
            continue
        out.append(rnd.choice('abcdefghijklmnopqrstuvwxyz0123456789') if x < share else ch)
    return ''.join(out)


def owners_books():
    if not (os.path.exists('/root/link/real_b.pkl') and os.path.exists('/root/link/draft.pkl')):
        print("SKIP the owner's books are not on this machine", flush=True)
        return
    paper = {r['addr']: r for r in pickle.load(open('/root/link/real_b.pkl', 'rb'))}
    if 'text' not in next(iter(paper.values())):
        print('SKIP real_b.pkl has no question words (run tests/aits_real247.py b once)', flush=True)
        return
    chapter = pickle.load(open('/root/link/draft.pkl', 'rb'))
    P = {k: L.read(r['text'], r['type'], r['answer']) for k, r in paper.items()}
    heads = [L.address(r['text']) for r in paper.values()]
    check('AITS 26-50 as the app read it: every question prints its own address (mock and number)', len(paper) == 1875 and all(h and h[1:3] == k for h, k in zip(heads, paper)), len(paper))
    C = [(L.address(r['text']), L.read(r['text'], r['type'], r['ans']), r) for r in chapter]
    check('Chemistry chapter-wise as the app read it: all 1,250 questions print an address and a chapter; no address twice', len(C) == 1250 and all(a for a, _, _ in C) and len({a[:3] for a, _, _ in C}) == 1250
          and all(L.chapter_name(r['text']) for _, _, r in C), (len(C), sum(1 for a, _, _ in C if not a)))
    pairs = [(P[a[1:3]], c, a) for a, c, _ in C if a[1:3] in P]
    shut = [(a[3], L.locks(p, c)) for p, c, a in pairs if L.locks(p, c)]
    check('the 625 chapter questions whose paper is in AITS 26-50: every lock opens, every pair has the very same letters', len(pairs) == 625 and not shut and all(p['letters'] == c['letters'] for p, c, _ in pairs), (len(pairs), shut[:3]))
    told = collections.Counter(p['distinct'] and c['distinct'] for p, c, _ in pairs if p['type'] == 'mcq')
    print('   MCQ pairs whose four options are four different readable values on both copies:', told[True], 'of', sum(told.values()), flush=True)
    # A wrong address: each chapter question is held against every other paper question of its own subject and kind. None may open.
    opened, tried, near = [], 0, 0.0
    by = collections.defaultdict(list)
    for k, r in paper.items():
        by[(r['subject'], r['type'])].append(k)
    for p, c, a in pairs:
        for k in by[(paper[a[1:3]]['subject'], c['type'])]:
            if k == a[1:3]:
                continue
            tried += 1
            if L.locks(P[k], c) is None:
                opened.append((a[3], k))
            elif tried % 37 == 0:
                near = max(near, L.alike(P[k]['letters'], c['letters']))
    check(f'a wrong address never opens: {tried:,} wrong pairs of the same subject and kind, none joined', tried > 100000 and not opened, opened[:4])
    best = 0.0
    for kind in by.values():
        sample = kind if len(kind) < 400 else random.Random(5).sample(kind, 400)
        for x, y in itertools.combinations(sample, 2):
            best = max(best, L.words_alike(P[x], P[y]))
    print(f'   two different AITS questions, the most alike seen in the sample: {best:.2f} (the words lock asks for {L.WORDS_OK:.2f})', flush=True)
    check('two different questions never read alike enough for the words lock by themselves in the sample', best < L.WORDS_OK, best)
    rnd = random.Random(11)
    for share in (.01, .03):
        got = [L.locks(p, {**c, 'letters': damage(c['letters'], share, rnd), 'stem': damage(c['stem'], share, rnd), 'ordered': damage(c['ordered'], share, rnd)}) for p, c, _ in pairs]
        ok = sum(g is None for g in got)
        print(f'   letters damaged {share:.0%}: {ok} of {len(pairs)} still join by themselves; the rest go to the owner with the percentage', flush=True)
        check(f'letters damaged {share:.0%}: every copy is either joined or sent to the owner with the reason (its words), none is dropped', all(g is None or (g['code'] == 'words' and '%' in g['say']) for g in got),
              [g for g in got if g and g['code'] != 'words'][:3])
        if share == .01:
            check('one letter in a hundred read differently: at least 9 copies in 10 still join by themselves', ok >= .9 * len(pairs), ok)


if __name__ == '__main__':
    made_up()
    owners_books()
    bad = [n for n, ok in RESULTS if not ok]
    print(f'TOTAL {len(RESULTS)} PASS {len(RESULTS) - len(bad)} FAIL {len(bad)}', flush=True)
