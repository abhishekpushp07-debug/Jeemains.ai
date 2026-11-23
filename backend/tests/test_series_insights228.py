# AITS series insights API (GET /api/series/all-india-jee/insights) against the isolated bridge (tests/series_insights_bridge228.py).
import json, os
import pytest
import requests

OUT = os.environ.get('BRIDGE_OUT', '/tmp/uibridge228s')
API = 'http://127.0.0.1:' + os.environ.get('BRIDGE_PORT', '8777')
URL = API + '/api/series/all-india-jee/insights'
B = json.load(open(OUT + '/bridge.json'))
E = B['expect']


def get(role):
    r = requests.get(URL, cookies=B[role], timeout=30)
    assert r.status_code == 200, r.text[:300]
    body = r.json()
    assert set(body) >= {'data', 'error', 'meta'}, body.keys()
    return body['data']


@pytest.fixture(scope='module')
def hero():
    return get('hero')


@pytest.fixture(scope='module')
def peer():
    return get('peer')


# Auth
def test_no_session_401():
    r = requests.get(URL, timeout=30)
    assert r.status_code == 401


# Overall numbers
def test_hero_overall(hero):
    o = hero['overall']
    assert o['days'] == 6 and o['live_days'] == 6 and o['compared_days'] == 5
    assert o['best'] == 210 and o['direction'] == 'up'
    assert hero['total_days'] == 50
    assert isinstance(o['above_average_days'], int)


# Subject trend
def test_hero_subjects(hero):
    got = {s['subject']: s['direction'] for s in hero['subjects']}
    assert got == E['hero']['subjects']
    assert [s['subject'] for s in hero['subjects']] == ['Physics', 'Chemistry', 'Mathematics']


# Chapters
def test_hero_chapters(hero):
    assert hero['chapters_tagged'] is True
    c = hero['chapters'][0]
    assert c['chapter'] == 'Rotational Motion' and c['days'] == 4


# You vs class per day
def test_hero_days_class(hero):
    days = sorted(hero['days'], key=lambda d: d['day'])
    assert [d['day'] for d in days] == [1, 2, 3, 4, 5, 6]
    for d in days[:5]:
        k = str(d['day'])
        assert d['class']['state'] == 'ready'
        assert d['class']['average'] == E['hero']['day_average'][k]
        assert d['class']['topper'] == E['hero']['day_topper'][k]
        assert d['attempt_id'] == B['attempts']['hero'][k]
    assert days[5]['class']['state'] == 'sealed' and days[5]['class']['release_at'] > 0


# Peer: no chapter tags, practice day has no class
def test_peer(peer):
    o = peer['overall']
    assert o['days'] == 4 and o['live_days'] == 3
    assert peer['chapters_tagged'] is False and peer['chapters'] == []
    d5 = [d for d in peer['days'] if d['day'] == 5][0]
    assert d5['mode'] == 'practice' and d5['class'] is None


# Isolation: a student only sees own attempts
def test_isolation(hero, peer):
    hero_ids = set(B['attempts']['hero'].values())
    peer_ids = {d['attempt_id'] for d in peer['days']}
    assert not (hero_ids & peer_ids)
    assert peer_ids == set(B['attempts']['peer'].values())
    assert {d['attempt_id'] for d in hero['days']} == hero_ids
