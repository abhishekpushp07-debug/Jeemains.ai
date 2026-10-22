"""Iteration 102: journey (full-mock progress), historical-rank evidence gate, My Tests tabs, bookmarks,
side-by-side comparison and question-report priorities. Synthetic TEST_JR_ fixtures only (no AI calls).
Run: pytest backend/tests/test_my_tests_journey.py -p no:asyncio -v
"""
import asyncio, hashlib, json, os, re, sys, time, uuid
from pathlib import Path
import pytest, requests

BACKEND = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND))
from dotenv import load_dotenv
load_dotenv(BACKEND / '.env'); load_dotenv(BACKEND.parent / 'frontend' / '.env')
BASE_URL = os.environ.get('REACT_APP_BACKEND_URL').rstrip('/')
from tejas.db import db
from tejas.packs import insert_attempt

LOOP = asyncio.new_event_loop(); asyncio.set_event_loop(LOOP); run = LOOP.run_until_complete
TAG = 'TEST_JR_' + uuid.uuid4().hex[:8]
PHONE, OTHER_PHONE = '9900000196', '9900000197'
T0 = time.time() - 30 * 86400
PACKS = set()
PROFILES = set()
PRE_PROFILES = set()
REAL = []


def _creds():
    text = (BACKEND.parent / 'memory' / 'test_credentials.md').read_text()
    return re.search(r'Email:\s*(\S+)', text).group(1), re.search(r'Password:\s*(\S+)', text).group(1)


async def _snapshot():
    h, n, qn = hashlib.sha256(), 0, 0
    async for d in db.tejas_sets.find({'id': {'$not': re.compile('^TEST')}}, {'_id': 0}).sort('id', 1):
        h.update(json.dumps(d, sort_keys=True, default=str).encode()); n += 1; qn += len(d.get('questions', []))
    states = {r['_id']: r['count'] async for r in db.tejas_question_solutions.aggregate([{'$group': {'_id': '$state', 'count': {'$sum': 1}}}])}
    return {'sets': n, 'questions': qn, 'sha': h.hexdigest(), 'states': states, 'settings': await db.tejas_settings.count_documents({}) if 'tejas_settings' in await db.list_collection_names() else 0}


async def _cleanup():
    await db.tejas_attempts.delete_many({'$or': [{'id': {'$regex': '^' + TAG}}, {'set_id': {'$regex': '^' + TAG}}]})
    await db.tejas_sets.delete_many({'id': {'$regex': '^' + TAG}})
    await db.tejas_saved_tests.delete_many({'set_id': {'$regex': '^' + TAG}})
    await db.tejas_question_reports.delete_many({'set_id': {'$regex': '^' + TAG}})
    await db.tejas_preflight.delete_many({'set_id': {'$regex': '^' + TAG}})
    await db.tejas_ledgers.delete_many({'id': {'$regex': '^' + TAG}})
    cohort_ids = [c['id'] async for c in db.tejas_cohorts.find({'set_id': {'$regex': '^' + TAG}}, {'id': 1})]
    await db.tejas_cohort_entries.delete_many({'cohort_id': {'$in': cohort_ids}})
    await db.tejas_cohort_snapshots.delete_many({'cohort_id': {'$in': cohort_ids}})
    await db.tejas_cohorts.delete_many({'id': {'$in': cohort_ids}})
    if REAL:
        await db.tejas_ledgers.delete_many({'id': {'$in': REAL}})
        await db.tejas_jobs.delete_many({'id': {'$in': ['grade-' + a for a in REAL]}})
    if PROFILES:
        pre = await db.tejas_profiles.find({'_id': {'$in': list(PROFILES)}}, {'_id': 1}).to_list(10)
        await db.tejas_profiles.delete_many({'_id': {'$in': [p['_id'] for p in pre if p['_id'] not in PRE_PROFILES]}})
    if PACKS:
        await db.tejas_packs.delete_many({'_id': {'$in': list(PACKS)}})


@pytest.fixture(scope='session', autouse=True)
def guard():
    PRE_PROFILES.update(d['_id'] for d in run(db.tejas_profiles.find({}, {'_id': 1}).to_list(10000)))
    before = run(_snapshot()); print('PRESERVATION BEFORE', before)
    yield
    run(_cleanup())
    after = run(_snapshot()); print('PRESERVATION AFTER', after)
    assert after == before


def body(r):
    j = r.json(); return j.get('data', j) if isinstance(j, dict) else j


def login_phone(phone):
    s = requests.Session()
    assert s.post(f'{BASE_URL}/api/auth/phone', json={'phone': phone}).status_code == 200
    me = body(s.get(f'{BASE_URL}/api/auth/me')); s.uid = (me.get('user') or me)['id']; return s


@pytest.fixture(scope='session')
def student(): return login_phone(PHONE)


@pytest.fixture(scope='session')
def other(): return login_phone(OTHER_PHONE)


@pytest.fixture(scope='session')
def owner():
    s = requests.Session(); e, p = _creds()
    r = s.post(f'{BASE_URL}/api/auth/login', json={'email': e, 'password': p})
    if r.status_code != 200: pytest.skip('owner login failed')
    return s


# ---------- fixture builders: real exam shapes ----------
SHAPES = {'JEE Main': [('Physics', 20, 5), ('Chemistry', 20, 5), ('Mathematics', 20, 5)],
          'BITSAT': [('Physics', 30, 0), ('Chemistry', 30, 0), ('English Proficiency', 10, 0), ('Logical Reasoning', 20, 0), ('Mathematics', 40, 0)],
          'COMEDK': [('Physics', 60, 0), ('Chemistry', 60, 0), ('Mathematics', 60, 0)]}
RULES = {'JEE Main': {'minutes': 180, 'correct': 4, 'wrong': -1, 'skipped': 0, 'navigation': 'free', 'numeric_policy': 'integer_exact', 'solution_release': 'after_submit'},
         'BITSAT': {'minutes': 180, 'correct': 3, 'wrong': -1, 'skipped': 0, 'navigation': 'free', 'numeric_policy': 'integer_exact', 'solution_release': 'after_submit',
                    'bonus_rule': {'main_count': 130, 'bonus_count': 12, 'policy': 'Bonus after all main.'}},
         'COMEDK': {'minutes': 180, 'correct': 1, 'wrong': 0, 'skipped': 0, 'navigation': 'free', 'numeric_policy': 'integer_exact', 'solution_release': 'after_submit'}}


def questions(exam, shape=None, toy=False):
    qs, n = [], 0
    for subj, mcq, num in (shape or SHAPES[exam]):
        for i in range(mcq + num):
            n += 1
            qs.append({'id': str(uuid.uuid5(uuid.NAMESPACE_URL, f'{TAG}-{exam}-{n}-{uuid.uuid4()}')), 'number': n, 'subject': subj, 'section': subj,
                       'type': 'mcq' if i < mcq else 'integer', 'text': f'TEST {n}', 'answer': 'B' if i < mcq else '7',
                       'options': {'A': '1', 'B': '2', 'C': '3', 'D': '4'} if i < mcq else {}, 'q_refs': [], 's_refs': [], 'render_mode': 'text'})
            if toy and n >= 10: return qs
    if exam == 'BITSAT':
        for b in range(12):
            n += 1
            qs.append({'id': str(uuid.uuid4()), 'number': n, 'subject': 'Mathematics', 'section': 'Mathematics', 'type': 'mcq', 'bonus': True,
                       'text': f'TEST bonus {n}', 'answer': 'A', 'options': {'A': '1', 'B': '2', 'C': '3', 'D': '4'}, 'q_refs': [], 's_refs': [], 'render_mode': 'text'})
    return qs


QCACHE = {}


def make(uid, exam='JEE Main', set_key='S1', at=0, correct=10, attempted=20, status='completed', rules=None, qs=None, legacy=False,
         seconds=3600, summary=True, **kw):
    """Insert via the production insert_attempt (seals pack and stores progress_family)."""
    if qs is None:
        qs = QCACHE.setdefault((exam, set_key), questions(exam))
    rl = dict(rules or RULES[exam]); total = len([q for q in qs if not q.get('bonus')])
    mark = rl['correct']
    a = {'id': f'{TAG}-att-{uuid.uuid4().hex[:10]}', 'user_id': uid, 'set_id': f'{TAG}-{set_key}', 'title': f'{TAG} {exam} {set_key}',
         'exam': exam, 'version': 1, 'rules': rl, 'questions': json.loads(json.dumps(qs)), 'mode': 'practice', 'status': status,
         'answers': {}, 'test_kind': 'mock', 'parent_attempt': None, 'started_at': T0 + at - 4000, 'deadline': 0,
         'submitted_at': T0 + at if status == 'completed' else None, 'competition_end': 0, 'start_key': uuid.uuid4().hex, 'key_version': 1,
         'summary': {'score': correct * mark - (attempted - correct), 'maximum': total * mark, 'correct': correct, 'attempted': attempted,
                     'incorrect': attempted - correct, 'skipped': total - attempted, 'total_seconds': seconds,
                     'subjects': {'Physics': {'score': correct, 'correct': correct}}} if summary and status == 'completed' else None}
    a.update(kw)
    run(insert_attempt(a)); PACKS.add(a['pack_id'])
    if legacy:
        run(db.tejas_attempts.update_one({'id': a['id']}, {'$unset': {'progress_family': ''}}))
    return a['id']


@pytest.fixture(scope='session')
def J(student, other):
    return build_journey(student.uid, other.uid)


def build_journey(uid, other_uid):
    d = {}
    # 6 DIFFERENT JEE papers; variable attempted denominators
    data = [(10, 20), (30, 40), (20, 60), (50, 55), (5, 10), (40, 75)]
    d['jee'] = []
    for i, (c, att) in enumerate(data):
        rules = dict(RULES['JEE Main'])
        if i == 1: rules['correct'] = 4.0  # numeric normalisation
        d['jee'].append(make(uid, set_key=f'P{i}', at=i * 100, correct=c, attempted=att, rules=rules, legacy=(i == 3)))
    # Excluded variants (submitted between 5 and 6)
    d['marking'] = make(uid, set_key='XM', at=450, rules={**RULES['JEE Main'], 'correct': 3})
    d['duration'] = make(uid, set_key='XD', at=451, rules={**RULES['JEE Main'], 'minutes': 200})
    d['mix'] = make(uid, set_key='XS', at=452, qs=questions('JEE Main', [('Physics', 30, 0), ('Chemistry', 20, 0), ('Mathematics', 25, 0)]))
    d['toy'] = make(uid, set_key='XT', at=453, qs=questions('JEE Main', toy=True))
    d['chapter'] = make(uid, set_key='XC', at=454, test_kind='chapter')
    d['retry'] = make(uid, set_key='P0', at=455, parent_attempt=d['jee'][0])
    d['competition'] = make(uid, set_key='XK', at=456, competition_end=T0 + 300)
    d['preview'] = make(uid, set_key='XP', at=457, mode='preview')
    # guards
    d['foreign'] = make(other_uid, set_key='P0', at=10)
    d['embargo'] = make(uid, set_key='XE', at=600, competition_end=time.time() + 7200)
    d['active'] = make(uid, set_key='XA', at=700, status='active', deadline=time.time() + 3600,
                       answers={'q': {'value': 'B', 'accepted_at': time.time() - 30}})
    d['expired'] = make(uid, set_key='XX', at=701, status='active', deadline=time.time() - 60)
    d['grading'] = make(uid, set_key='XG', at=702, summary=False)
    d['comedk0'] = make(uid, exam='COMEDK', set_key='C1', at=800, correct=0, attempted=0)
    d['bits'] = [make(uid, exam='BITSAT', set_key='B1', at=900), make(uid, exam='BITSAT', set_key='B2', at=901, correct=60, attempted=90)]
    # retake of same paper P0 for comparison (same pack), plus no-time variant
    d['retake'] = make(uid, set_key='P0', at=1000, correct=25, attempted=40, seconds=None)
    return d


def J_url(a, p='journey'): return f'{BASE_URL}/api/attempts/{a}/{p}'


# ---------- Journey ----------
class TestJourney:
    def test_full_journey_weighted_last5(self, student, J):
        r = student.get(J_url(J['jee'][5])); assert r.status_code == 200, r.text
        d = body(r); assert d['state'] == 'available', d
        ids = [p['id'] for p in d['series']]
        assert ids == J['jee'], f'series mismatch {ids}'
        last5 = list(reversed(J['jee'][1:6]))
        assert d['confidence']['attempt_ids'] == last5
        assert d['confidence']['correct'] == 145 and d['confidence']['attempted'] == 240
        assert d['confidence']['accuracy'] == round(100 * 145 / 240, 1)
        mean = round(sum(100 * c / a for c, a in [(30, 40), (20, 60), (50, 55), (5, 10), (40, 75)]) / 5, 1)
        assert d['confidence']['accuracy'] != mean
        assert d['first']['id'] == J['jee'][0] and d['latest']['id'] == J['jee'][5]
        assert d['delta']['score'] == round(d['latest']['score'] - d['first']['score'], 2)
        assert d['delta']['accuracy'] == round(53.3 - 50.0, 1)
        assert d['limited'] is False and 'bounded' in d['coverage'].lower()
        assert 'lifetime' not in json.dumps(d).lower()

    def test_as_of_cutoff(self, student, J):
        d = body(student.get(J_url(J['jee'][2])))
        assert [p['id'] for p in d['series']] == J['jee'][:3] and d['latest']['id'] == J['jee'][2]
        assert d['confidence']['window_size'] == 3

    def test_excluded_variants(self, student, J):
        for k in ('toy', 'chapter', 'retry', 'competition'):
            d = body(student.get(J_url(J[k])))
            assert d['state'] == 'unavailable' and d['series'] == [], k
        for k in ('marking', 'duration', 'mix'):  # own family only
            d = body(student.get(J_url(J[k])))
            assert d['state'] == 'available' and [p['id'] for p in d['series']] == [J[k]], (k, d.get('series'))
        d = body(student.get(J_url(J['jee'][5]) + '?score_version=revised'))
        assert d['state'] == 'unavailable'

    def test_guards_and_null_accuracy(self, student, J):
        assert student.get(J_url(J['foreign'])).status_code == 404
        assert student.get(J_url(J['embargo'])).status_code == 403
        assert student.get(J_url(J['active'])).status_code == 409
        assert student.get(J_url(J['grading'])).status_code == 409
        assert requests.get(J_url(J['jee'][0])).status_code == 401
        d = body(student.get(J_url(J['comedk0'])))
        assert d['state'] == 'available' and d['confidence']['accuracy'] is None and d['latest']['accuracy'] is None
        b = body(student.get(J_url(J['bits'][1])))
        assert b['state'] == 'available' and [p['id'] for p in b['series']] == J['bits']

    def test_persisted_family(self, J):
        docs = {x['id']: x for x in run(db.tejas_attempts.find({'id': {'$in': J['jee'] + [J['toy'], J['chapter']]}}, {'_id': 0, 'id': 1, 'progress_family': 1}).to_list(50))}
        fams = {docs[i].get('progress_family') for i in J['jee'] if i != J['jee'][3]}
        assert len(fams) == 1 and None not in fams, 'numeric marking 4 vs 4.0 must share family'
        assert 'progress_family' not in docs[J['jee'][3]]
        assert docs[J['toy']]['progress_family'] is None and docs[J['chapter']]['progress_family'] is None


# ---------- Historical rank evidence gate ----------
class TestHistoricalRank:
    def test_unavailable_for_all(self, student, J):
        for a in (J['jee'][5], J['bits'][0], J['comedk0']):
            d = body(student.get(J_url(a, 'historical-rank')))
            assert d['state'] == 'unavailable' and d['rank_low'] is None and d['rank_high'] is None
            assert d['reason'] and d['reference']['url'].startswith('https://') and d['reference']['checked_year'] == 2026
            assert 'dataset_year' not in json.dumps(d) and 'percentile_estimate' not in d
        d = body(student.get(J_url(J['chapter'], 'historical-rank')))
        assert 'not a compatible' in d['reason']
        assert student.get(J_url(J['embargo'], 'historical-rank')).status_code == 403
        assert student.get(J_url(J['foreign'], 'historical-rank')).status_code == 404


# ---------- My Tests ----------
MT = f'{BASE_URL}/api/my/tests'
ALLOWED = set(['id', 'set_id', 'title', 'exam', 'status', 'mode', 'started_at', 'submitted_at', 'deadline', 'remaining_seconds', 'saved_answers',
               'last_saved_at', 'count', 'summary', 'version', 'report_allowed', 'resumable', 'result_available', 'compare_eligible'])


class TestMyTests:
    def test_tabs_and_states(self, student, J):
        before = run(db.tejas_attempts.find_one({'id': J['active']}, {'_id': 0}))
        p = body(student.get(MT + '?tab=progress&q=' + TAG))
        ids = [i['id'] for i in p['items']]
        assert J['active'] in ids and J['expired'] not in ids
        act = next(i for i in p['items'] if i['id'] == J['active'])
        assert act['resumable'] and act['remaining_seconds'] > 0 and act['saved_answers'] == 1 and act['summary'] is None
        c = body(student.get(MT + '?tab=completed&q=' + TAG))
        assert c['total'] >= 16 and c['pages'] >= 2 and len(c['items']) == 12
        allc = c['items'] + body(student.get(MT + '?tab=completed&page=2&q=' + TAG))['items']
        m = {i['id']: i for i in allc}
        assert J['preview'] not in m and J['foreign'] not in m
        assert m[J['expired']]['status'] == 'expired' and not m[J['expired']]['resumable']
        assert m[J['embargo']]['status'] == 'embargoed' and m[J['embargo']]['summary'] is None and not m[J['embargo']]['report_allowed']
        assert m[J['grading']]['status'] == 'grading'
        assert m[J['retry']]['compare_eligible'] is False and m[J['retake']]['compare_eligible'] is True
        for i in allc: assert set(i) <= ALLOWED
        assert 'answer' not in json.dumps(allc).replace('answers', '')
        after = run(db.tejas_attempts.find_one({'id': J['active']}, {'_id': 0}))
        assert after == before

    def test_filters_and_errors(self, student, J):
        e = body(student.get(MT + '?tab=completed&status=expired&q=' + TAG))
        assert [i['id'] for i in e['items']] == [J['expired']]
        g = body(student.get(MT + '?tab=completed&status=embargoed&q=' + TAG)); assert [i['id'] for i in g['items']] == [J['embargo']]
        b = body(student.get(MT + '?tab=completed&exam=BITSAT&q=' + TAG)); assert {i['id'] for i in b['items']} == set(J['bits'])
        day = time.strftime('%Y-%m-%d', time.gmtime(T0 - 4000))
        f = body(student.get(MT + f'?tab=completed&start={day}&end={day}&q={TAG}'))
        assert all(time.strftime('%Y-%m-%d', time.gmtime(i['started_at'])) == day for i in f['items'])
        assert body(student.get(MT + '?tab=completed&q=zzznomatch' + TAG))['total'] == 0
        for qs in ('tab=progress&status=expired', 'tab=saved&status=grading', 'tab=completed&start=2026-02-01&end=2026-01-01',
                   'tab=completed&start=notadate', 'tab=bogus', 'tab=completed&exam=NEET', 'tab=completed&page=0'):
            assert student.get(MT + '?' + qs).status_code == 422, qs
        assert requests.get(MT).status_code == 401
        o = body(other.get(MT + '?tab=completed&q=' + TAG)) if (other := login_phone(OTHER_PHONE)) else None
        assert [i['id'] for i in o['items']] == [J['foreign']]


# ---------- Bookmarks ----------
@pytest.fixture(scope='session')
def saved_set():
    sid = f'{TAG}-saveset'
    run(db.tejas_sets.insert_one({'id': sid, 'title': f'TEST save {TAG}', 'exam': 'JEE Main', 'status': 'published', 'audience': 'restricted',
        'allowed_phones': ['+91' + PHONE], 'revision': 1, 'version': 1, 'rules': RULES['JEE Main'], 'questions': questions('JEE Main'),
        'test_kind': 'mock', 'full_length': True, 'competition': False, 'created_at': time.time(), 'published_at': time.time()}))
    return sid


class TestBookmarks:
    def test_save_flow(self, student, other, saved_set):
        S = f'{MT}/saved/{saved_set}'
        n0 = run(db.tejas_attempts.count_documents({'user_id': student.uid}))
        assert body(student.get(S))['saved'] is False
        assert body(student.post(S, json={}))['saved'] is True
        assert student.post(S, json={}).status_code == 200
        assert run(db.tejas_saved_tests.count_documents({'set_id': saved_set})) == 1
        assert run(db.tejas_attempts.count_documents({'user_id': student.uid})) == n0
        assert student.post(S, json={'x': 1}).status_code == 422
        assert student.post(f'{MT}/saved/{TAG}-nope', json={}).status_code == 404
        assert other.post(S, json={}).status_code == 404  # restricted, not visible
        assert body(other.get(S))['saved'] is False
        other.delete(S)
        assert body(student.get(S))['saved'] is True
        t = body(student.get(MT + '?tab=saved&q=' + TAG))
        assert t['items'][0]['set_id'] == saved_set and t['items'][0]['available'] and t['items'][0]['paper']
        assert 'questions' not in json.dumps(t['items'][0]['paper'])
        assert body(student.get(MT + '?tab=saved&status=unavailable&q=' + TAG))['total'] == 0
        run(db.tejas_sets.update_one({'id': saved_set}, {'$set': {'status': 'draft'}}))
        t = body(student.get(MT + '?tab=saved&q=' + TAG))
        assert t['items'][0]['available'] is False and t['items'][0]['paper'] is None and t['items'][0]['reason']
        run(db.tejas_sets.update_one({'id': saved_set}, {'$set': {'status': 'published'}}))
        assert body(student.delete(S))['saved'] is False
        assert body(student.get(MT + '?tab=saved&q=' + TAG))['total'] == 0


# ---------- Comparison ----------
class TestCompare:
    def test_compare(self, student, J):
        C = f'{MT}/compare'
        r = student.post(C, json={'left': J['retake'], 'right': J['jee'][0]}); assert r.status_code == 200, r.text
        d = body(r)
        assert d['left']['id'] == J['jee'][0] and d['right']['id'] == J['retake']
        assert d['score_delta'] == round(d['right']['score'] - d['left']['score'], 2)
        assert d['accuracy_delta'] == round(62.5 - 50.0, 1) and d['time_delta'] is None
        assert student.post(C, json={'left': J['retake'], 'right': J['retake']}).status_code == 409
        assert student.post(C, json={'left': J['retake'], 'right': J['foreign']}).status_code == 404
        assert student.post(C, json={'left': J['jee'][0], 'right': J['jee'][1]}).status_code == 409
        assert student.post(C, json={'left': J['jee'][0], 'right': J['retry']}).status_code == 409
        assert student.post(C, json={'left': J['jee'][0], 'right': J['active']}).status_code == 409
        assert student.post(C, json={'left': J['jee'][0], 'right': J['embargo']}).status_code == 403
        assert student.post(C, json={'left': J['jee'][0]}).status_code == 422


# ---------- Report priorities ----------
def rep(set_id, qid, user, status='open', at=0, source_hash='h1', attempt=None, number=1):
    doc = {'_id': f'{TAG}-r-{uuid.uuid4().hex[:8]}', 'user_id': user, 'attempt_id': attempt or f'{TAG}-a-{uuid.uuid4().hex[:6]}',
           'set_id': set_id, 'question_id': qid, 'number': number, 'title': 'TEST', 'exam': 'JEE Main', 'version': 1, 'category': 'key',
           'context': 'results', 'note': 'TEST', 'status': status, 'created_at': time.time() - 1000 + at, 'review_note': '', 'reviewed_at': None}
    if source_hash is not None: doc['source_hash'] = source_hash
    run(db.tejas_question_reports.insert_one(doc)); return doc['_id']


class TestReportPriorities:
    def test_order_and_groups(self, owner, student):
        S = f'{TAG}-rset'
        for u in ('u1', 'u2', 'u3'): rep(S, 'qA', u, at=1)
        for k in range(3): rep(S, 'qB', 'u9', at=50 + k)  # retakes: one profile
        rep(S, 'qC', 'u1', at=2); rep(S, 'qC', 'u2', at=3)
        rep(S, 'qA', 'u4', source_hash='h2', at=10)
        legacy = rep(S, 'qL', 'u5', source_hash=None, at=5)
        for k in range(25): rep(S, 'qP', 'u7', at=-500 + k)
        P = f'{BASE_URL}/api/studio/question-report-priorities'
        assert student.get(P).status_code == 403 and student.get(f'{BASE_URL}/api/studio/question-report-group?group_id=x').status_code == 403
        d = body(owner.get(P + '?status=open'))
        mine = [i for i in d['items'] if i['set_id'] == S]
        order = [(i['question_id'], i['source_hash'], i['distinct_profiles'], i['reports']) for i in mine]
        assert order[0][:3] == ('qA', 'h1', 3) and order[1][:3] == ('qC', 'h1', 2), order
        b = next(i for i in mine if i['question_id'] == 'qB'); assert b['distinct_profiles'] == 1 and b['reports'] == 3
        assert any(i['question_id'] == 'qL' for i in mine)  # legacy visible
        assert len([i for i in mine if i['question_id'] == 'qA']) == 2  # source-hash split
        assert all('user_id' not in i and 'profiles' not in i for i in d['items'])
        pq = next(i for i in mine if i['question_id'] == 'qP')
        G = f'{BASE_URL}/api/studio/question-report-group?group_id='
        g1 = body(owner.get(G + requests.utils.quote(pq['group_id']))); g2 = body(owner.get(G + requests.utils.quote(pq['group_id']) + '&page=2'))
        assert g1['total'] == 25 and len(g1['items']) == 20 and len(g2['items']) == 5 and g1['pages'] == 2
        assert all('user_id' not in i for i in g1['items'])
        assert owner.get(G + 'nope').status_code == 404
        lg = next(i for i in mine if i['question_id'] == 'qL')
        assert body(owner.get(G + requests.utils.quote(lg['group_id'])))['total'] == 1
        # resolve all of qA/h1 -> removed from open view, visible in resolved
        ga = body(owner.get(G + requests.utils.quote(mine[0]['group_id'])))
        for it in ga['items']:
            assert owner.post(f'{BASE_URL}/api/studio/question-reports/{it["id"]}/review', json={'status': 'resolved', 'note': 'TEST ok'}).status_code == 200
        d2 = [i for i in body(owner.get(P + '?status=open'))['items'] if i['set_id'] == S]
        assert d2[0]['question_id'] == 'qC' and not any(i['question_id'] == 'qA' and i['source_hash'] == 'h1' for i in d2)
        rs = [i for i in body(owner.get(P + '?status=resolved'))['items'] if i['set_id'] == S]
        assert rs and rs[0]['question_id'] == 'qA' and rs[0]['unresolved'] == 0
        assert run(db.tejas_audits.count_documents({'resource': ga['items'][0]['id']})) >= 1 
        assert owner.get(P + '?status=bogus').status_code == 422


# ---------- Real start/submit pathway ----------
class TestRealPathway:
    def test_start_submit_persists_family(self, student, saved_set):
        r = student.post(f'{BASE_URL}/api/sets/{saved_set}/preflight', json={'test_response': 'ok'}); assert r.status_code == 200, r.text
        r = student.post(f'{BASE_URL}/api/sets/{saved_set}/start', json={'start_key': 'TESTJR' + uuid.uuid4().hex, 'device_checked': True})
        assert r.status_code == 200, r.text
        aid = body(r)['id']; REAL.append(aid)
        doc = run(db.tejas_attempts.find_one({'id': aid}, {'_id': 0, 'progress_family': 1, 'test_kind': 1, 'set_id': 1, 'profile': 1, 'pack_id': 1}))
        PROFILES.add(doc['profile']['id']); PACKS.add(doc['pack_id'])
        assert doc['progress_family'] and doc['test_kind'] == 'mock'
        run(db.tejas_attempts.update_one({'id': aid}, {'$set': {'set_id': doc['set_id']}}))
        s = student.post(f'{BASE_URL}/api/attempts/{aid}/submit'); assert s.status_code in (200, 202), s.text
        for _ in range(15):
            res = student.get(f'{BASE_URL}/api/attempts/{aid}/results')
            if res.status_code == 200: break
            time.sleep(2)
        assert res.status_code == 200, res.text
        j = body(student.get(J_url(aid))); assert j['state'] == 'available', j
        assert j['latest']['id'] == aid and j['latest']['accuracy'] is None
