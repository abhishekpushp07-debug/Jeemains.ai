# Forgot PIN (iteration 72): validation, single unknown-number 404, Mongo-seeded throttle (FAKE number only). NO real reset here.
import hashlib
import os
from datetime import datetime, timezone

import pytest
import requests
from dotenv import load_dotenv
from pymongo import MongoClient

load_dotenv('/app/frontend/.env')
load_dotenv('/app/backend/.env')
BASE_URL = (os.environ.get('EXPO_BACKEND_URL') or os.environ['EXPO_PUBLIC_BACKEND_URL']).rstrip('/')
URL = f"{BASE_URL}/api/account/forgot-pin"
QA_PHONE = '7004186276'
UNKNOWN = '7000000099'
FAKE = '9999900077'
FORBIDDEN = ('owner', 'email', 'password', 'cookie', 'pin_version', 'student')


def key(v):
    return hashlib.sha256(v.encode()).hexdigest()


def post(body, headers=None):
    return requests.post(URL, json=body, headers=headers or {}, timeout=40)


@pytest.fixture(scope='module')
def db():
    return MongoClient(os.environ['MONGO_URL'])[os.environ['DB_NAME']]


# Validation runs before throttle and before any upstream call
class TestValidation:
    def test_mismatch_422(self):
        r = post({'phone': QA_PHONE, 'new_pin': '1111', 'confirm_pin': '2222'})
        assert r.status_code == 422
        assert r.json()['detail'] == 'PINs do not match. Please check both fields.'

    @pytest.mark.parametrize('body', [
        {'phone': '12ab', 'new_pin': '1234', 'confirm_pin': '1234'},
        {'phone': '1234567', 'new_pin': '1234', 'confirm_pin': '1234'},
        {'phone': FAKE, 'new_pin': '12', 'confirm_pin': '12'},
        {'phone': FAKE, 'new_pin': 'abcd', 'confirm_pin': 'abcd'},
        {'phone': FAKE, 'new_pin': '12345', 'confirm_pin': '12345'},
        {'phone': FAKE, 'new_pin': '1234'},
        {'phone': FAKE, 'new_pin': '1234', 'confirm_pin': '1234', 'extra': 1},
    ])
    def test_bad_format_422(self, body):
        r = post(body)
        assert r.status_code == 422, r.text


# Unknown number -> 404 (called ONCE)
class TestNotFound:
    def test_unknown_404_once(self, db):
        r = post({'phone': UNKNOWN, 'new_pin': '1234', 'confirm_pin': '1234'}, headers={'X-Forwarded-For': '203.0.113.77'})
        assert r.status_code == 404, r.text
        assert r.json()['detail'] == 'No account uses this number. Create an account instead.'
        low = r.text.lower()
        assert not any(w in low for w in FORBIDDEN), r.text
        row = db.pin_resets.find_one({'phone': key(UNKNOWN)}, sort=[('at', -1)])
        assert row and row['result'] == 'not_found'
        # record whether the client-supplied X-Forwarded-For was trusted for the IP key (reported, not asserted)
        print('SPOOFED_IP_TRUSTED=', row['ip'] == key('203.0.113.77'))


# Throttle path via 5 seeded rows for a FAKE number; no upstream lookups
class TestThrottle:
    def test_phone_throttle_429(self, db):
        now = datetime.now(timezone.utc)
        ids = db.pin_resets.insert_many([{'phone': key(FAKE), 'ip': key('TEST_fake_ip'), 'at': now, 'result': 'TEST_seed'} for _ in range(5)]).inserted_ids
        try:
            r = post({'phone': '+91' + FAKE, 'new_pin': '1234', 'confirm_pin': '1234'})
            assert r.status_code == 429, r.text
            assert r.headers.get('Retry-After') == '3600'
            assert r.json()['detail'] == 'Too many PIN resets for now. Please try again in an hour.'
            # a throttled call must not add a row
            assert db.pin_resets.count_documents({'phone': key(FAKE)}) == 5
            m = post({'phone': FAKE, 'new_pin': '1111', 'confirm_pin': '2222'})
            assert m.status_code == 422
        finally:
            db.pin_resets.delete_many({'_id': {'$in': ids}})
        assert db.pin_resets.count_documents({'phone': key(FAKE)}) == 0
