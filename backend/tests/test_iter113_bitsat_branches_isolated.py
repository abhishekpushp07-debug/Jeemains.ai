"""Iteration 113: BITSAT branch matches + historical-rank BITSAT delegation (TEST-ONLY ISOLATED DB).
Run: cd /app/backend && python -m pytest tests/test_iter113_bitsat_branches_isolated.py -p no:asyncio -n0 -v
Auth = X-Test-User override (TEST-ONLY MOCKED). Never touches configured DB.
"""
import asyncio, copy, uuid
import httpx, pytest
import iso_harness as H
from tejas.scoring import score as grade
from tejas import bitsat_branches as B

LOOP = asyncio.new_event_loop(); asyncio.set_event_loop(LOOP); run = LOOP.run_until_complete

# Official 2026-27 values crawled from https://admissions.bits-pilani.ac.in/FD/BITSAT_cutOffs.html on 2026-10-23
OFFICIAL = {
 'pilani': {'B.E. Chemical': 226, 'B.E. Civil': 222, 'B.E. Electrical & Electronics': 266, 'B.E. Mechanical': 239,
            'B.E. Computer Science': 308, 'B.E. Electronics & Instrumentation': 261, 'B.E. Electronics & Communication': 289,
            'B.E. Manufacturing': 226, 'B.E. Mathematics and Computing': 299, 'B.E. Environmental and Sustainability': 213,
            'B.E. Pharmaceutical Engg.': 211, 'B. Pharm': 200, 'M.Sc. Biological Sciences': 218, 'M.Sc. Chemistry': 227,
            'M.Sc. Economics': 256, 'M.Sc. Mathematics': 241, 'M.Sc. Physics': 235, 'M.Sc. Semiconductor and Nanoscience': 246},
 'goa': {'B.E. Chemical': 223, 'B.E. Electrical & Electronics': 253, 'B.E. Mechanical': 233, 'B.E. Computer Science': 274,
         'B.E. Electronics & Instrumentation': 250, 'B.E. Electronics & Communication': 261, 'B.E. Electronics and Computer': 266,
         'B.E. Mathematics and Computing': 270, 'B.E. Environmental and Sustainability': 210, 'M.Sc. Biological Sciences': 217,
         'M.Sc. Chemistry': 223, 'M.Sc. Economics': 246, 'M.Sc. Mathematics': 233, 'M.Sc. Physics': 231,
         'M.Sc. Semiconductor and Nanoscience': 241},
 'hyderabad': {'B.E. Chemical': 223, 'B.E. Civil': 220, 'B.E. Electrical & Electronics': 251, 'B.E. Mechanical': 228,
               'B.E. Computer Science': 272, 'B.E. Electronics & Instrumentation': 249, 'B.E. Electronics & Communication': 261,
               'B.E. Mathematics and Computing': 268, 'B.E. Environmental and Sustainability': 208, 'B.E. Pharmaceutical Engg.': 205,
               'B. Pharm': 200, 'M.Sc. Biological Sciences': 217, 'M.Sc. Chemistry': 223, 'M.Sc. Economics': 244,
               'M.Sc. Mathematics': 230, 'M.Sc. Physics': 229, 'M.Sc. Semiconductor and Nanoscience': 241}}


async def _req(method, path, who=None, **kw):
    headers = {'x-test-user': who} if who else {}
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=H.app), base_url='http://iso') as c:
        return await c.request(method, path, headers=headers, **kw)


def req(method, path, who=None, **kw):
    return R(run(_req(method, path, who, **kw)))


class R:
    def __init__(self, r): self.r, self.status_code, self.text = r, r.status_code, r.text
    def json(self):
        j = self.r.json(); return j['data'] if isinstance(j, dict) and 'data' in j else j


def bm(score, who='A', **params):
    return req('GET', '/api/bitsat/branch-matches', who, params={'score': score, **params})


SUBJ = [('Physics', 30), ('Chemistry', 30), ('Mathematics', 40), ('English Proficiency', 10), ('Logical Reasoning', 20)]
RULES = {'minutes': 180, 'correct': 3, 'wrong': -1, 'skipped': 0, 'navigation': 'free', 'bonus_rule': 'all_main_attempted'}


def bitsat_attempt(user_id, n_correct=110, n_wrong=20, bonus_correct=3, bonus=12, **over):
    qs, n = [], 0
    for s, c in SUBJ:
        for _ in range(c):
            n += 1
            qs.append({'id': f'q{n}', 'number': n, 'subject': s, 'section': s, 'type': 'mcq', 'answer': 'B',
                       'options': {'A': '1', 'B': '2', 'C': '3', 'D': '4'}, 'text': 'TEST'})
    for i in range(bonus):
        n += 1
        s = SUBJ[i % 3][0]
        qs.append({'id': f'q{n}', 'number': n, 'subject': s, 'section': 'Bonus', 'type': 'mcq', 'answer': 'B', 'bonus': True,
                   'options': {'A': '1', 'B': '2', 'C': '3', 'D': '4'}, 'text': 'TEST'})
    answers = {}
    for i, q in enumerate(qs[:130]):
        if i < n_correct: answers[q['id']] = {'value': 'B'}
        elif i < n_correct + n_wrong: answers[q['id']] = {'value': 'A'}
    for q in qs[130:130 + bonus_correct]:
        answers[q['id']] = {'value': 'B'}
    a = {'id': 'TEST_BA_' + uuid.uuid4().hex[:8], 'user_id': 'TEST_U_' + user_id, 'exam': 'BITSAT', 'mode': 'practice',
         'test_kind': 'mock', 'status': 'completed', 'parent_attempt': None, 'rules': dict(RULES), 'questions': qs,
         'answers': answers, 'started_at': 1000, 'submitted_at': 1000 + 3 * 3600, 'bonus_unlocked_at': 1500 if bonus else None,
         'title': 'TEST BITSAT', 'set_id': 'TEST_S', 'version': 1}
    a.update(over)
    g = grade(a)
    a['summary'] = g['summary']
    return a


def insert(a):
    run(H.TDB.tejas_attempts.insert_one(copy.deepcopy(a)))
    return a


async def _real_counts():
    real = H.tdbmod.client[H.REAL_DB]
    return {c: await real[c].estimated_document_count() for c in ('tejas_sets', 'tejas_attempts', 'tejas_sessions', 'tejas_audits')}


@pytest.fixture(scope='module', autouse=True)
def isolated():
    rc = run(_real_counts())
    assert H.leftover_real_handles() == []
    run(H.tdbmod.client.drop_database(H.TEST_DB))
    for k in ('A', 'B'):
        H.USERS[k] = {'id': 'TEST_U_' + k, 'role': 'student', 'name': k, 'phone': '990000019' + str(ord(k) % 10),
                      'access_type': 'unverified_phone'}
    yield
    run(H.tdbmod.client.drop_database(H.TEST_DB))
    assert run(_real_counts()) == rc


# ---- dataset ----
def test_all_50_rows_match_official():
    rows = {(c, n): v for c, e in B.TABLE.items() for _, n, v in e}
    off = {(c, n): v for c, e in OFFICIAL.items() for n, v in e.items()}
    assert len(rows) == 50 and rows == off
    assert [len(B.TABLE[c]) for c in ('pilani', 'goa', 'hyderabad')] == [18, 15, 17]
    assert B.REFERENCE['maximum'] == 390 and B.REFERENCE['url'].endswith('BITSAT_cutOffs.html')


# ---- endpoint auth / validation ----
def test_requires_auth():
    assert bm(300, who=None).status_code == 401


@pytest.mark.parametrize('s', ['391', '426', '-131', 'NaN', '300.5', 'abc', ''])
def test_rejects_bad_scores(s):
    assert bm(s).status_code == 422


@pytest.mark.parametrize('p', [{'campus': 'delhi'}, {'programme': 'mba'}, {'campus': 'ALL'}])
def test_rejects_bad_filters(p):
    assert bm(300, **p).status_code == 422


def test_no_mutation_methods():
    assert req('POST', '/api/bitsat/branch-matches?score=300', 'A').status_code == 405


# ---- matching logic ----
def names(j):
    return [(m['programme'], m['campus_id'], m['cutoff']) for m in j['matches']]


def test_308_top3():
    j = bm(308).json()
    assert names(j) == [('B.E. Computer Science', 'pilani', 308), ('B.E. Mathematics and Computing', 'pilani', 299),
                        ('B.E. Electronics & Communication', 'pilani', 289)]
    assert j['matches'][0]['at_cutoff'] is True and j['matches'][0]['margin'] == 0
    assert j['matches'][1]['margin'] == 9 and j['matches'][1]['at_cutoff'] is False
    assert [c['campus_id'] for c in j['matches'][0]['other_campuses']] == ['goa', 'hyderabad']
    assert [c['campus_id'] for c in j['matches'][1]['other_campuses']] == ['goa', 'hyderabad']


def test_300_top3_and_alternative():
    j = bm(300).json()
    assert names(j) == [('B.E. Mathematics and Computing', 'pilani', 299), ('B.E. Electronics & Communication', 'pilani', 289),
                        ('B.E. Computer Science', 'goa', 274)]
    assert [(c['campus_id'], c['cutoff']) for c in j['matches'][2]['other_campuses']] == [('hyderabad', 272)]
    progs = [m['programme'] for m in j['matches']]
    assert len(set(progs)) == 3
    cut = [m['cutoff'] for m in j['matches']]
    assert cut == sorted(cut, reverse=True)


def test_390_boundary():
    j = bm(390).json()
    assert len(j['matches']) == 3 and j['matches'][0]['margin'] == 82 and j['next_targets'] == []


@pytest.mark.parametrize('s', [-130, 0, -5, 200, 204])
def test_low_be_zero(s):
    j = bm(s).json()
    assert j['matches'] == [] and j['matching_programmes'] == 0 and len(j['next_targets']) == 3
    assert all(t['cutoff'] > s and t['marks_needed'] == t['cutoff'] - s for t in j['next_targets'])


def test_205_and_208():
    j = bm(205).json()
    assert names(j) == [('B.E. Pharmaceutical Engg.', 'hyderabad', 205)] and j['matches'][0]['at_cutoff']
    assert all(t['programme'] != 'B.E. Pharmaceutical Engg.' for t in j['next_targets'])
    j = bm(208).json()
    assert names(j) == [('B.E. Environmental and Sustainability', 'hyderabad', 208), ('B.E. Pharmaceutical Engg.', 'hyderabad', 205)]


def test_bpharm():
    j = bm(200, programme='bpharm').json()
    assert len(j['matches']) == 1 and j['matches'][0]['programme'] == 'B. Pharm'
    assert {j['matches'][0]['campus_id']} | {c['campus_id'] for c in j['matches'][0]['other_campuses']} == {'pilani', 'hyderabad'}
    assert bm(390, programme='bpharm', campus='goa').json()['matches'] == []
    assert bm(390, programme='bpharm', campus='goa').json()['next_targets'] == []


def test_msc_and_campus_filters():
    j = bm(250, programme='msc').json()
    # tie 246 Goa Economics vs Pilani Semiconductor -> alphabetical programme order
    assert names(j) == [('M.Sc. Economics', 'goa', 246), ('M.Sc. Semiconductor and Nanoscience', 'pilani', 246),
                        ('M.Sc. Mathematics', 'pilani', 241)]
    assert [(c['campus_id'], c['cutoff']) for c in j['matches'][0]['other_campuses']] == [('hyderabad', 244)]
    j = bm(300, campus='goa').json()
    assert all(m['campus_id'] == 'goa' and not m['other_campuses'] for m in j['matches'])
    assert names(j)[0] == ('B.E. Computer Science', 'goa', 274)
    j = bm(260, programme='all', campus='hyderabad').json()
    assert names(j) == [('B.E. Electrical & Electronics', 'hyderabad', 251), ('B.E. Electronics & Instrumentation', 'hyderabad', 249),
                        ('M.Sc. Economics', 'hyderabad', 244)]


def test_ties_deterministic():
    # Goa/Hyd ECE both 261 tie -> alphabetical campus order; 261 Pilani EI also
    j = bm(261, campus='all').json()
    a = bm(261).json()
    assert j == a
    ece = [m for m in j['matches'] if m['programme'] == 'B.E. Electronics & Communication']
    assert not ece or ece[0]['cutoff'] == 261


# ---- historical-rank delegation ----
def test_auto_main_block_310_bonus_excluded():
    a = insert(bitsat_attempt('A'))
    assert a['summary']['score'] == 319 and a['summary']['main_block']['score'] == 310
    before = run(H.TDB.tejas_attempts.find_one({'id': a['id']}, {'_id': 0}))
    r = req('GET', f'/api/attempts/{a["id"]}/historical-rank', 'A')
    assert r.status_code == 200, r.text
    j = r.json()
    assert j['state'] == 'available' and j['score'] == 310 and j['original_total'] == 319 and j['bonus_excluded'] == 9
    assert j['score_basis'] == 'mock_main_block' and j['kind'] == 'branch_matches'
    assert names(j)[0] == ('B.E. Computer Science', 'pilani', 308)
    assert 'rank_low' not in j
    after = run(H.TDB.tejas_attempts.find_one({'id': a['id']}, {'_id': 0}))
    assert before == after


def test_130_only_no_bonus():
    a = insert(bitsat_attempt('A', bonus=0, bonus_correct=0, rules={**RULES, 'bonus_rule': None}))
    j = req('GET', f'/api/attempts/{a["id"]}/historical-rank', 'A').json()
    assert j['state'] == 'available' and j['score'] == 310


def test_ownership_embargo_incomplete():
    a = insert(bitsat_attempt('A'))
    assert req('GET', f'/api/attempts/{a["id"]}/historical-rank', 'B').status_code in (403, 404)
    assert req('GET', f'/api/attempts/{a["id"]}/historical-rank', None).status_code == 401
    e = insert(bitsat_attempt('A', competition_end=H.CLOCK[0] + 3600))
    r = req('GET', f'/api/attempts/{e["id"]}/historical-rank', 'A')
    assert r.status_code == 403 and '310' not in r.text and '319' not in r.text
    i = insert(bitsat_attempt('A', status='active'))
    assert req('GET', f'/api/attempts/{i["id"]}/historical-rank', 'A').status_code == 409


@pytest.mark.parametrize('over', [
    {'parent_attempt': 'X'}, {'test_kind': 'chapter'}, {'mode': 'series_practice'}, {'rules': {**RULES, 'minutes': 120}},
    {'rules': {**RULES, 'correct': 4}},
])
def test_incompatible_unavailable(over):
    a = insert(bitsat_attempt('A', **over))
    j = req('GET', f'/api/attempts/{a["id"]}/historical-rank', 'A').json()
    assert j['state'] == 'unavailable' and j['matches'] == [] and j['score'] is None


def test_corrected_version_and_missing_block():
    a = insert(bitsat_attempt('A'))
    j = req('GET', f'/api/attempts/{a["id"]}/historical-rank?score_version=corrected', 'A').json()
    assert j['state'] == 'unavailable'
    m = bitsat_attempt('A'); m['summary'].pop('main_block')
    insert(m)
    r = req('GET', f'/api/attempts/{m["id"]}/historical-rank', 'A')
    assert r.status_code == 200 and r.json()['state'] == 'unavailable'


def test_malformed_main_block_score_string_no_500():
    m2 = bitsat_attempt('A'); m2['summary']['main_block'] = {'score': 'x', 'maximum': 390}
    insert(m2)
    r = req('GET', f'/api/attempts/{m2["id"]}/historical-rank', 'A')
    print('malformed', r.status_code, r.text[:200])
    assert r.status_code == 200 and r.json()['state'] == 'unavailable'


def test_subject_count_mismatch_unavailable():
    a = bitsat_attempt('A')
    a['questions'][0]['subject'] = 'Chemistry'
    insert(a)
    j = req('GET', f'/api/attempts/{a["id"]}/historical-rank', 'A').json()
    assert j['state'] == 'unavailable'
