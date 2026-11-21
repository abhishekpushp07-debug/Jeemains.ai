"""TEST-ONLY (iteration 211): duplicate cache staleness retest on master bridge 8770 (disposable DB).
Needs: TEST_dup_a mock Live (set) + TEST_dup_b waiting mock in jee-main:mocks (ui_batch_dups217.py + ui_dup_live217.py).
Run: cd /app/backend && python -m pytest tests/test_dup_cache211.py -v -p no:xdist -o addopts=''"""
import json, subprocess
import pytest, requests

M = 'http://127.0.0.1:8770'
MB = json.load(open('/tmp/uibridge/bridge.json'))
DBN = [l for l in open('/tmp/bridge181.log') if l.startswith('READY')][-1].split()[1]
TYPE = f'{M}/api/admin/master/types/jee-main:mocks/mocks'


def mongo(js):
    return subprocess.run(['mongosh', '--quiet', DBN, '--eval', js], capture_output=True, text=True).stdout.strip()


def data(r):
    j = r.json(); return j.get('data', j) if isinstance(j, dict) else j


@pytest.fixture(scope='module')
def owner():
    s = requests.Session(); s.headers['Cookie'] = '; '.join(f'{k}={v}' for k, v in MB['owner'].items()); return s


@pytest.fixture(scope='module')
def ids():
    set_id = mongo("db.tejas_book_mocks.findOne({set_id:{$ne:null}, state:'published'}).set_id")
    waiting = mongo("db.tejas_book_mocks.findOne({book_id:{$in:db.tejas_books.find({'payload.filename':/^TEST_dup_b/}).toArray().map(b=>b._id)}})._id")
    assert set_id and waiting
    return {'set': set_id, 'mock': waiting}


def flagged(owner):
    d = data(owner.get(TYPE)); return {i['id']: i['duplicates'] for i in d['items'] if i.get('duplicates')}


class TestDupCache:
    def test_01_baseline_two_flagged(self, owner, ids):
        f = flagged(owner)
        assert set(f) == {ids['set'], ids['mock']}, f
        lines = [m['title'] for rows in f.values() for r in rows for m in r['matches']]
        assert any('TEST_dup_b' in t for t in lines), lines  # waiting book mock title carries upload name

    def test_02_library_clears_immediately(self, owner, ids):
        r = owner.post(f'{M}/api/admin/master/status', json={'to': 'library', 'items': [{'kind': 'set', 'id': ids['set']}]})
        assert r.status_code == 200 and data(r)['done'] == 1, r.text
        assert flagged(owner) == {}  # no Fix page visit needed
        d = data(owner.get(f'{M}/api/admin/duplicates/mock/{ids["mock"]}'))
        assert d['checked'] is True and d['items'] == []

    def test_03_restore_flags_again(self, owner, ids):
        r = owner.post(f'{M}/api/admin/library/restore', json={'ids': [ids['set']]})
        assert r.status_code == 200, r.text
        assert set(flagged(owner)) == {ids['set'], ids['mock']}

    def test_04_edit_live_question_text_invalidates(self, owner, ids):
        """Edit Q1 text of the Live set so it is no longer the same: Q1 must drop out of the alert."""
        flagged(owner)  # cache filled
        s = data(owner.get(f'{M}/api/studio/sets/{ids["set"]}'))
        q1 = next(q for q in s['questions'] if q['number'] == 1)
        new = 'TEST_ edited so it is a totally different question about optics and lenses now'
        r = owner.put(f'{M}/api/studio/sets/{ids["set"]}/questions/{q1["id"]}', json={'accessible_text': new, 'text': new, 'review_note': 'TEST_ edit'})
        if r.status_code == 409 and 'immutable_import' in r.text:
            pytest.skip('book-imported sets are frozen; set revision is not in structure.FIELDS anyway (see report)')
        assert r.status_code == 200, r.text
        f = flagged(owner)
        nums = sorted(x['number'] for x in f.get(ids['mock'], []))
        assert nums == [2], f'stale cache after editing a Live question: mock still flagged on {nums}'


def test_signature_projection_has_revision():
    """section_items keys sets on (id, revision, version) but structure.FIELDS must project them, else edits never refresh."""
    src = open('/app/backend/tejas/structure.py').read()
    block = src[src.index('\nFIELDS = {'):]; block = block[:block.index('}') + 1]
    assert "'revision'" in block and "'version'" in block, 'structure.FIELDS lacks revision/version -> t.get("revision") is always None in duplicates.section_items'
