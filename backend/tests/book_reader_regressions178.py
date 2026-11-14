"""TEST-ONLY: page-reader regressions from the 50-mock book that held every mock (answer keys read as instructions).
Pure function checks, no database. Run: cd /app/backend && python tests/book_reader_regressions178.py
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from tejas.book_reader import read_page, anchor_of, printed_keys, option_family  # noqa: E402

RESULTS = []


def check(name, ok, detail=''):
    RESULTS.append(ok)
    print(('PASS ' if ok else 'FAIL ') + name + ('' if ok else f'  -> {detail}'))


def L(text, x0, y0, x1=None, y1=None):
    return {'text': text, 'rect': [x0, y0, x1 if x1 is not None else min(.95, x0 + .01 * max(3, len(text)) * .6), y1 if y1 is not None else y0 + .018]}


def head(mock):
    return [L('TEJAS / JEE MAIN', .081, .006, .226, .023), L(mock, .858, .006, .919, .023)]


HEAD = head('Mock 26')


def key_page():
    lines = HEAD + [L('Answer key', .081, .05, .25, .075)]
    for i in range(1, 16):
        y = .09 + i * .03
        lines += [L(str(i), .10, y, .12, y + .015), L('ABCD'[i % 4], .16, y, .17, y + .015)]
    m, ctx = read_page(lines, {'mock': 'Mock 26', 'role': 'solution', 'subject': 'Chemistry'})
    keys = [r for r in m.regions if r.role == 'key']
    check('answer key heading page classified as answer_key', m.classification == 'answer_key', m.classification)
    check('15 key cells bound to Mock 26', len(keys) == 15 and all(r.mock == 'Mock 26' and r.checked for r in keys), [(r.mock, r.number) for r in keys][:4])
    check('context role is key after the key page', ctx.get('role') == 'key', ctx.get('role'))


def lowercase_answer_is_prose():
    lines = head('Mock 4') + [L('Question 74', .081, .051, .213, .076), L('The yellow precipitate confirms chromium, so the identification decides the', .081, .1, .919, .118),
                    L('answer.', .081, .12, .141, .138), L('Answer: 95 g mol-1', .081, .15, .3, .168), L('Question 75', .081, .2, .213, .225), L('Working text.', .081, .24, .4, .258)]
    m, ctx = read_page(lines, {'mock': 'Mock 4', 'role': 'solution', 'subject': 'Chemistry', 'last': {'solution': 73}})
    roles = {r.role for r in m.regions if r.role not in ('instructions', 'ignore')}
    check("sentence-ending 'answer.' does not switch solutions to keys", roles == {'solution'} and ctx.get('role') == 'solution', (roles, ctx.get('role')))
    check('both Question 74 and 75 solutions found', sorted(r.number for r in m.regions if r.role == 'solution') == [74, 75], [r.number for r in m.regions])


def numbered_steps_continue_solution():
    lines = head('Mock 11') + [L('so x = 12 cm.', .081, .05, .3, .068), L('1. Equate the opposing fields', .081, .1, .328, .118), L('2. Find the coordinate', .081, .16, .27, .178),
                    L('Q2 = 1', .081, .2, .137, .218), L('q2/q1) for the point between like charges.', .21, .24, .54, .258)]
    ctx = {'mock': 'Mock 11', 'role': 'solution', 'subject': 'Physics', 'solution_style': 'q', 'open_s': {'mock': 'Mock 11', 'subject': 'Physics', 'number': 26}}
    m, out = read_page(lines, ctx)
    sol = [r for r in m.regions if r.role == 'solution']
    check('numbered steps and Q-symbols on a solution page are not new solutions', len(sol) == 1 and sol[0].number == 26 and sol[0].continuation, [(r.role, r.number, r.continuation) for r in m.regions])
    check('long solution stays open for the next page', (out.get('open_s') or {}).get('number') == 26, out.get('open_s'))
    check('no review issue for a plain solution continuation', not m.issues, m.issues)


def anchors():
    check("'Q2 = 1' is not a question heading", anchor_of(L('Q2 = 1', .081, .5)) is None)
    check("'q2/q1) for' is not a question heading", anchor_of(L('q2/q1) for the point', .081, .5)) is None)
    check("'Q10' symbol is not a question heading", anchor_of(L('Q10', .081, .5)) is None)
    check("'Q. 2.2 g of Q' (a decimal after a symbol) is not a question heading", anchor_of(L('Q. 2.2 g of Q occupies 1.12 L at STP.', .081, .5)) is None)
    check("'Question 10' is a heading", anchor_of(L('Question 10', .081, .5)) == (10, True, False), anchor_of(L('Question 10', .081, .5)))
    check("'Q10.' is a heading", (anchor_of(L('Q10.', .081, .5)) or (0,))[0] == 10, anchor_of(L('Q10.', .081, .5)))


def formula_pieces_and_wraps():
    lines = head('Mock 6') + [L('3.', .081, .1, .097, .118), L('For t in [0, 2], let p(x) = x2 - 2tx + t - 3. Find c.', .115, .1, .9, .118),
                    L('(A) (2 -', .081, .13, .157, .148), L('5, 2 +', .177, .13, .222, .148), L('5)', .241, .13, .257, .148), L('(C) (-3, 3)', .509, .13, .63, .148),
                    L('(B) [2, 3]', .082, .155, .2, .173), L('(D) (2, 3)', .508, .155, .63, .173),
                    L('4. The magnifying-power magnitude', .081, .19, .5, .208), L('3. Find the objective focal length.', .081, .21, .5, .228),
                    L('(A) 1', .081, .24, .12, .258), L('(B) 2', .514, .24, .56, .258), L('(C) 3', .081, .265, .12, .283), L('(D) 4', .514, .265, .56, .283),
                    L('511.', .081, .3, .118, .318), L('1. Neglecting fringing, the new capacitance is', .081, .315, .5, .328), L('5. Next question text', .081, .33, .5, .348), L('(A) 1', .081, .36, .12, .378), L('(B) 2', .514, .36, .56, .378),
                    L('(C) 3', .081, .385, .12, .403), L('(D) 4', .514, .385, .56, .403)]
    m, _ = read_page(lines, {'mock': 'Mock 6', 'role': 'question', 'subject': 'Mathematics', 'last': {'question': 2}})
    nums = [r.number for r in m.regions if r.role == 'question']
    check("formula '5)', wrapped '3. Find…' and stray '511.' are not questions", nums == [3, 4, 5], nums)
    q3 = next(r for r in m.regions if r.number == 3)
    check('row-wise two-column options A,C,B,D read as one A-D set', q3.response_type == 'mcq' and q3.option_labels == list('ABCD'), (q3.response_type, q3.option_labels))
    check('no review issues on a clean page', not m.issues, m.issues)


def tall_glyph_belongs_to_next_question():
    rows = [L('(D) 4', .5143, .68, .56, .693), L('23.', .0809, .7265, .1067, .745), L('Let A =', .125, .7265, .191, .7449), L('\uf8eb', .196, .7041, .2107, .7159),
            L('\uf8ec', .196, .7249, .2107, .7367), L('\uf8ed', .196, .7325, .2107, .7443), L('2', .2107, .7104, .2199, .7288), L('1', .2366, .7104, .2457, .7288),
            L('0', .2625, .7104, .2716, .7288), L('1', .2107, .7265, .2199, .7449), L('0', .2107, .7426, .2199, .761), L('\uf8f6', .2717, .7041, .2863, .7159),
            L('\uf8f8and B = (A - I3)^-1 (A + I3). Find det(B2 - I3).', .2717, .7258, .6818, .7536), L('24. Next question', .081, .7693, .5328, .7897)]
    m, _ = read_page(head('Mock 34') + [L('22. Earlier question text', .081, .6, .6, .62), L('(A) 1', .081, .66, .13, .673), L('(B) 2', .5143, .66, .56, .673), L('(C) 3', .081, .68, .13, .693)] + rows,
                     {'mock': 'Mock 34', 'role': 'question', 'subject': 'Mathematics', 'numeric': True, 'last': {'question': 21}})
    q23 = next(r for r in m.regions if r.number == 23)
    check('3x3 matrix with TeX bracket pieces stays inside its own question crop', q23.rect[1] <= .7041, q23.rect)
    rows = [L('(C) 11', .0857, .6129, .1376, .6259), L('(D) 1', .5143, .6129, .5578, .6259), L('120.', .0847, .6565, .1221, .6694), L('A =', .1374, .6565, .1705, .6695),
            L('"', .1756, .6454, .1853, .6572), L('4', .1853, .6484, .1945, .6614), L('1', .2112, .6484, .2204, .6614), L('2', .1853, .6645, .1945, .6775),
            L('2', .2112, .6645, .2204, .6775), L('#', .2204, .6454, .2302, .6572), L('. Find tr(BA) without assuming AB=BA.', .3352, .6565, .672, .6695),
            L('(A) -2', .0857, .688, .1432, .7012), L('(B) 18', .5143, .6882, .566, .7012), L('(C) 6', .0857, .709, .14, .722), L('(D) 4', .5143, .709, .56, .722)]
    m, _ = read_page(head('Mock 40') + [L('119.', .0847, .58, .1221, .593), L('Find x.', .14, .58, .3, .593), L('(A) 1', .0857, .595, .13, .608), L('(B) 2', .5143, .595, .56, .608)] + rows,
                     {'mock': 'Mock 40', 'role': 'question', 'subject': 'Mathematics', 'last': {'question': 118}})
    q120 = next(r for r in m.regions if r.number == 120)
    check('stacked 2x2 matrix on the first line stays inside its own question crop', q120.rect[1] <= .6454 and '4\n1' in q120.text and not m.issues, (q120.rect, m.issues))
    lines = HEAD + [L('97.', .086, .1, .113, .113), L('(A) 1', .086, .12, .129, .133), L('(B) 17', .514, .12, .566, .133), L('(C) 16', .086, .141, .138, .154), L('(D) 65', .514, .141, .567, .154),
                    L('98.', .086, .176, .113, .189), L('Let P(x) = (1 +', .128, .176, .259, .189), L('√', .263, .165, .278, .178), L('2 x)8. Find the sum of coefficients.', .278, .174, .835, .189),
                    L('(A) 1154', .086, .197, .156, .21), L('(B) 1150', .514, .197, .584, .21), L('(C) 577', .086, .218, .147, .23), L('(D) 1152', .514, .218, .585, .23)]
    m, _ = read_page(lines, {'mock': 'Mock 1', 'role': 'question', 'subject': 'Mathematics', 'last': {'question': 96}})
    q98 = next(r for r in m.regions if r.number == 98)
    check('raised root sign above the anchor row is inside Q98, no crossing issue', q98.rect[1] <= .165 and not m.issues, (q98.rect, m.issues))


def prose_is_not_a_key():
    m, _ = read_page([L('Answer Key', .067, .06, .2, .08), L('Q1. (B)', .067, .12, .15, .14), L('Q2. (C)', .067, .15, .15, .17), L('Q3. 42', .067, .18, .15, .2)],
                     {'mock': 'Mock 1', 'role': 'question', 'subject': 'Physics', 'last': {'question': 3}})
    check("'Q1. (B)' key lines keep their printed answers", [r.answer for r in m.regions if r.role == 'key'] == ['B', 'C', '42'], [(r.role, r.number, r.answer) for r in m.regions])
    check("'could then answer / a different' is not a printed key", printed_keys('The same collection could then answer\na different kind of search', 'question') == set())
    check("'The correct option is' followed by option list is not a key", printed_keys('The correct option is\n(A) x > 0', 'question') == set())
    check("'Answer: (b) and (d).' statement letters are not option keys", printed_keys('Answer: (b) and (d).\nAnswer: (D)', 'solution') == {'D'}, printed_keys('Answer: (b) and (d).\nAnswer: (D)', 'solution'))
    check("'Answer: (B)' on one line is a printed key", printed_keys('Answer: (B)', 'solution') == {'B'}, printed_keys('Answer: (B)', 'solution'))
    check('options labelled (1)/(2) inside A-D options stay A-D', option_family('', ['(A) G(1) > 0', '(1) > 0', '(C) G', '(2) < 0', '(B) G', '(D) G'])[0] == 'ABCD')


def shared_passage_subject():
    m, _ = read_page(head('Mock 4') + [L('46. Some physical quantities (List-I) are paired with dimensional formulae (List-II).', .081, .05, .9, .07),
                     L('(A)', .2, .09, .23, .105), L('Coefficient of viscosity', .25, .09, .45, .105), L('(B)', .2, .11, .23, .125), L('G', .25, .11, .3, .125),
                     L('(C)', .2, .13, .23, .145), L('Stefan constant', .25, .13, .4, .145), L('(D)', .2, .15, .23, .165), L('Dipole moment', .25, .15, .4, .165),
                     L('(E)', .2, .17, .23, .185), L('Surface tension', .25, .17, .4, .185), L('The number of correctly matched pairs is', .081, .2, .6, .218)],
                     {'mock': 'Mock 4', 'role': 'question', 'subject': 'Physics', 'numeric': True, 'last': {'question': 45}})
    q = next(r for r in m.regions if r.number == 46)
    check('numerical-section match list (A)–(E) is an integer question, not MCQ', q.response_type == 'integer' and not q.option_labels, (q.response_type, q.option_labels))
    m, _ = read_page(head('Mock 44') + [L('Question 33', .081, .05, .2, .07), L('Check', .081, .3, .128, .318),
                     L('Physics agrees: the relaxation time of a sphere in Stokes regime scales as r2.', .081, .334, .668, .352), L('So a = 1.', .081, .36, .3, .378)],
                     {'mock': 'Mock 44', 'role': 'solution', 'subject': 'Physics', 'solution_style': 'q', 'last': {'solution': 32}})
    check("a sentence starting 'Physics agrees: …' is not a subject heading", [r.number for r in m.regions if r.role == 'solution'] == [33] and not m.issues, ([(r.role, r.number, r.rect) for r in m.regions], m.issues))
    lines = HEAD + [L('(D) 4-bromotoluene', .514, .05, .7, .068), L('Read the passage for Question 61', .086, .1, .345, .118), L('When the students recorded memories...', .085, .12, .9, .138),
                    L('English Proficiency', .086, .16, .294, .177), L('61.', .086, .184, .113, .197), L('Which statement best expresses the main idea?', .128, .184, .587, .197),
                    L('(A) one', .087, .208, .2, .221), L('(B) two', .087, .232, .2, .245), L('(C) three', .087, .256, .2, .269), L('(D) four', .087, .28, .2, .293)]
    m, _ = read_page(lines, {'mock': 'Mock 26', 'role': 'question', 'subject': 'Chemistry', 'last': {'question': 60}})
    shared = next((r for r in m.regions if r.role == 'shared'), None)
    check('passage printed above a new subject heading belongs to that subject', shared is not None and shared.subject == 'English' and shared.shared_for == [61], shared and (shared.subject, shared.shared_for))


for t in (key_page, lowercase_answer_is_prose, numbered_steps_continue_solution, anchors, formula_pieces_and_wraps, tall_glyph_belongs_to_next_question, prose_is_not_a_key, shared_passage_subject):
    try:
        t()
    except Exception as exc:
        check(t.__name__ + ' raised', False, repr(exc))
print(f'TOTAL {len(RESULTS)} PASS {sum(RESULTS)} FAIL {len(RESULTS) - sum(RESULTS)}')
