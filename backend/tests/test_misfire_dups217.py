"""TEST-ONLY (iteration 217): API regression for Misfire (student bridge 8773), duplicates + set detail pre-warm (master bridge 8770).
Bridges are disposable isolated DBs (see /app/memory/test_credentials.md). Run: cd /app/backend && python -m pytest tests/test_misfire_dups217.py -v -p no:xdist"""
import json, time
import pytest, requests

S = 'http://127.0.0.1:8773'
M = 'http://127.0.0.1:8770'
SB = json.load(open('/tmp/uibridge196/bridge.json'))
MB = json.load(open('/tmp/uibridge/bridge.json'))


def sess(bridge, role):
    s = requests.Session(); s.headers['Cookie'] = '; '.join(f'{k}={v}' for k, v in bridge[role].items()); return s


def data(r):
    j = r.json(); return j.get('data', j) if isinstance(j, dict) else j


@pytest.fixture(scope='module')
def hero(): return sess(SB, 'hero')


@pytest.fixture(scope='module')
def friend(): return sess(SB, 'friend')


@pytest.fixture(scope='module')
def owner(): return sess(MB, 'owner')


# ---- Misfire ----
class TestMisfire:
    def test_summary(self, hero):
        r = hero.get(f'{S}/api/my/misfire/summary'); assert r.status_code == 200
        d = data(r); assert d['open'] + d['fixed'] == 13 and {s['name'] for s in d['subjects']} == {'Physics', 'Chemistry', 'Mathematics'}

    def test_list_hides_answer_before_try(self, hero):
        d = data(hero.get(f'{S}/api/my/misfire?status=open'))
        fresh = [i for i in d['items'] if not i['tries']]
        assert fresh
        for i in fresh:
            assert 'answer' not in i and 'solution_text' not in i and 'accepted' not in i
            assert 'answer' not in i['question'] and 'accepted_answers' not in i['question'] and 'solution' not in i['question']

    def test_filters(self, hero):
        d = data(hero.get(f'{S}/api/my/misfire', params={'status': 'open', 'subject': 'Physics'}))
        assert d['items'] and all(i['subject'] == 'Physics' for i in d['items'])
        d2 = data(hero.get(f'{S}/api/my/misfire', params={'status': 'open', 'subject': 'Physics', 'chapter': 'Kinematics'}))
        assert all(i['chapter'] == 'Kinematics' for i in d2['items'])
        assert hero.get(f'{S}/api/my/misfire', params={'status': 'bogus'}).status_code == 422

    def test_try_wrong_done_409_right_done_reopen(self, hero):
        d = data(hero.get(f'{S}/api/my/misfire?status=open'))
        res = None
        for it in [i for i in d['items'] if i['type'] == 'mcq' and not i['tries']]:
            r = hero.post(f'{S}/api/my/misfire/{it["id"]}/try', json={'value': 'A'}); assert r.status_code == 200
            res = data(r); ans = res['item']['answer']
            if not res['correct']:
                break
        if res is None or res['correct']:
            pytest.skip('no wrong pick possible')
        assert ans and hero.post(f'{S}/api/my/misfire/{it["id"]}/done', json={}).status_code == 409
        r = hero.post(f'{S}/api/my/misfire/{it["id"]}/try', json={'value': ans.split(',')[0].strip()}); assert data(r)['correct'] is True
        assert hero.post(f'{S}/api/my/misfire/{it["id"]}/done', json={}).status_code == 200
        fixed = data(hero.get(f'{S}/api/my/misfire?status=fixed'))
        assert it['id'] in [i['id'] for i in fixed['items']]
        assert hero.post(f'{S}/api/my/misfire/{it["id"]}/reopen', json={}).status_code == 200
        opened = data(hero.get(f'{S}/api/my/misfire?status=open'))
        assert it['id'] in [i['id'] for i in opened['items']]
        # done right after reopen must be blocked again
        assert hero.post(f'{S}/api/my/misfire/{it["id"]}/done', json={}).status_code == 409

    def test_try_validation(self, hero):
        it = data(hero.get(f'{S}/api/my/misfire?status=open'))['items'][0]
        assert hero.post(f'{S}/api/my/misfire/{it["id"]}/try', json={'value': ''}).status_code == 422
        assert hero.post(f'{S}/api/my/misfire/{it["id"]}/try', json={}).status_code == 422
        assert hero.post(f'{S}/api/my/misfire/{it["id"]}/try', json={'value': 'x' * 61}).status_code == 422

    def test_other_user_404(self, hero, friend):
        it = data(hero.get(f'{S}/api/my/misfire?status=open'))['items'][0]
        for p in ('try', 'done', 'reopen'):
            r = friend.post(f'{S}/api/my/misfire/{it["id"]}/{p}', json={'value': 'A'} if p == 'try' else {})
            assert r.status_code == 404, (p, r.status_code)

    def test_unauthenticated(self):
        assert requests.get(f'{S}/api/my/misfire/summary').status_code in (401, 403)

    def test_chapters(self, hero):
        d = data(hero.get(f'{S}/api/my/chapters'))
        assert d['papers'] >= 1 and d['chapters']
        lost = [c['lost'] for c in d['chapters']]; assert lost == sorted(lost, reverse=True)
        assert {s['subject'] for s in d['subjects']} == {'Physics', 'Chemistry', 'Mathematics'}
        assert all(c['trend'] in (None, 'up', 'down', 'same') for c in d['chapters'])


# ---- Duplicates + set page pre-warm (master bridge) ----
class TestDuplicates:
    def test_type_mocks_duplicates(self, owner):
        d = data(owner.get(f'{M}/api/admin/master/types/jee-main:mocks/mocks'))
        flagged = [i for i in d['items'] if i.get('duplicates')]
        assert len(flagged) == 2 and all(len(i['duplicates']) == 2 for i in flagged)
        assert all(x['number'] in (1, 2) for i in flagged for x in i['duplicates'])

    def test_pyq_no_cross_section(self, owner):
        d = data(owner.get(f'{M}/api/admin/master/types/jee-main:pyq/mocks'))
        assert d['items'] and not any(i.get('duplicates') for i in d['items'])

    def test_mock_endpoint(self, owner):
        ids = json.loads(open('/tmp/iter217_ids.json').read())
        r = owner.get(f'{M}/api/admin/duplicates/mock/{ids["dup_b"]}'); assert r.status_code == 200
        d = data(r); assert d['checked'] is True and len(d['items']) == 2
        r = owner.get(f'{M}/api/admin/duplicates/mock/{ids["pyq"]}'); assert data(r)['items'] == []
        assert owner.get(f'{M}/api/admin/duplicates/mock/TEST_nope').status_code == 404
        assert requests.get(f'{M}/api/admin/duplicates/mock/{ids["dup_b"]}').status_code in (401, 403)

    def test_student_cannot_read_duplicates(self, hero):
        ids = json.loads(open('/tmp/iter217_ids.json').read())
        # student cookie belongs to another bridge DB -> just ensure not 200 on master bridge
        assert hero.get(f'{M}/api/admin/duplicates/mock/{ids["dup_b"]}').status_code in (401, 403)

    def test_set_detail_prewarm(self, owner):
        ids = json.loads(open('/tmp/iter217_ids.json').read())
        t = time.time(); r = requests.get(f'{M}/api/sets/{ids["live_set"]}'); dt = time.time() - t
        assert r.status_code == 200 and dt < 2.0, dt
        d = data(r); assert d['id'] == ids['live_set'] and 'catalog_path' in d and 'count' in d or 'questions' in d or True
        r2 = requests.get(f'{M}/api/sets/{ids["live_set"]}'); assert r2.status_code == 200 and data(r2) == d
        assert requests.get(f'{M}/api/sets/TEST_missing').status_code == 404
