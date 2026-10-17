# BITSAT mock time-limit auto-finalize: simulate expired deadline on a TEST attempt (DB edit of own test attempt only)
import os
import time
import uuid
import pytest
import requests
from pymongo import MongoClient
from dotenv import load_dotenv

load_dotenv('/app/backend/.env')
BASE_URL = os.environ.get('REACT_APP_BACKEND_URL').rstrip('/')
API = BASE_URL + '/api'
HDR = {'Origin': BASE_URL, 'Content-Type': 'application/json'}


def unwrap(r):
    j = r.json()
    return j['data'] if isinstance(j, dict) and 'data' in j and 'error' in j else j


def test_expired_mock_auto_finalized():
    s = requests.Session()
    s.headers.update(HDR)
    assert s.post(API + '/auth/phone', json={'phone': '9900000177'}).status_code == 200
    d = unwrap(s.get(API + '/exam-navigation/bitsat/catalogue', params={'kind': 'mocks', 'page': 4}))
    m = d['items'][0]
    s.post(API + f"/sets/{m['id']}/preflight", json={'test_response': 'A'})
    a = unwrap(s.post(API + f"/sets/{m['id']}/start", json={'start_key': str(uuid.uuid4()), 'device_checked': True}))
    assert a['status'] == 'active'
    main = [q for q in a['questions'] if not q.get('bonus')]
    r = s.put(API + f"/attempts/{a['id']}/answers/{main[0]['id']}", json={'value': 'A', 'revision': 1, 'request_id': str(uuid.uuid4())})
    assert r.status_code == 200
    db = MongoClient(os.environ['MONGO_URL'])[os.environ['DB_NAME']]
    db.tejas_attempts.update_one({'id': a['id']}, {'$set': {'deadline': time.time() - 5}})
    r = s.put(API + f"/attempts/{a['id']}/answers/{main[1]['id']}", json={'value': 'A', 'revision': 1, 'request_id': str(uuid.uuid4())})
    assert r.status_code == 409
    got = unwrap(s.get(API + f"/attempts/{a['id']}"))
    assert got['status'] == 'completed' and got['reason'] == 'time_limit'
    for _ in range(20):
        r = s.get(API + f"/attempts/{a['id']}/results")
        if r.status_code == 200:
            break
        time.sleep(1.5)
    summ = unwrap(r)['summary']
    assert summ['main_block']['skipped'] == 129 and summ['bonus_block']['entered'] is False
