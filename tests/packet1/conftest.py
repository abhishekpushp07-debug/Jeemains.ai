"""Isolated real-database tests. No application import before this boundary."""
import inspect
import os
import re
import sys
import uuid
from datetime import datetime, timezone, timedelta
from pathlib import Path
import pytest
import pytest_asyncio
from dotenv import dotenv_values
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase

ROOT = Path(__file__).resolve().parents[2]
TEST_DB_NAME = 'tejas_p1_test_' + uuid.uuid4().hex
assert re.fullmatch(r'tejas_p1_test_[0-9a-f]{32}', TEST_DB_NAME)
if 'server' in sys.modules or 'tejas.db' in sys.modules:
    raise RuntimeError('Run Packet 1 separately: application imported before isolation')
values = dotenv_values(ROOT / 'backend/.env')
if not values.get('MONGO_URL') or values.get('DB_NAME') == TEST_DB_NAME:
    raise RuntimeError('Invalid isolated database configuration')
os.environ.update({
    'MONGO_URL': values['MONGO_URL'], 'DB_NAME': TEST_DB_NAME,
    'JWT_SECRET': uuid.uuid4().hex + uuid.uuid4().hex,
    'ADMIN_EMAIL': 'packet1@isolated.invalid', 'ADMIN_PASSWORD': uuid.uuid4().hex,
    'FRONTEND_URL': 'https://testserver', 'EMERGENT_LLM_KEY': 'disabled-test-only',
})
values.clear()
sys.path.insert(0, str(ROOT / 'backend'))


def allowed(name):
    if name != TEST_DB_NAME or os.environ.get('DB_NAME') != TEST_DB_NAME:
        raise RuntimeError('Test database boundary violation')
    return name


_original_get = AsyncIOMotorClient.get_database
_original_item = AsyncIOMotorClient.__getitem__
_original_drop = AsyncIOMotorClient.drop_database
_original_init = AsyncIOMotorDatabase.__init__


def guarded_get(self, name=None, *args, **kwargs):
    return _original_get(self, allowed(name), *args, **kwargs)


def guarded_item(self, name):
    return _original_item(self, allowed(name))


def guarded_init(self, client, name, *args, **kwargs):
    _original_init(self, client, allowed(name), *args, **kwargs)


async def guarded_drop(self, name_or_database, *args, **kwargs):
    name = name_or_database if isinstance(name_or_database, str) else name_or_database.name
    allowed(name)
    return await _original_drop(self, name_or_database, *args, **kwargs)


AsyncIOMotorClient.get_database = guarded_get
AsyncIOMotorClient.__getitem__ = guarded_item
AsyncIOMotorClient.drop_database = guarded_drop
AsyncIOMotorDatabase.__init__ = guarded_init
from tejas import db as tejas_db
assert tejas_db.db.name == TEST_DB_NAME


@pytest.hookimpl(tryfirst=True)
def pytest_collection_modifyitems(items):
    # Both test bodies and async fixtures use one loop. No per-test Motor rebinding.
    for item in items:
        if inspect.iscoroutinefunction(item.obj):
            item.own_markers[:] = [m for m in item.own_markers if m.name != 'asyncio']
            item.add_marker(pytest.mark.asyncio(loop_scope='session'), append=False)


@pytest.fixture(scope='session')
def test_db_name():
    return TEST_DB_NAME


@pytest_asyncio.fixture(scope='session', loop_scope='session')
async def test_client():
    await tejas_db.indexes()
    yield tejas_db.client
    await tejas_db.client.drop_database(allowed(TEST_DB_NAME))
    tejas_db.client.close()


@pytest_asyncio.fixture(loop_scope='session')
async def test_db(test_client):
    allowed(tejas_db.db.name)
    return tejas_db.db


@pytest_asyncio.fixture(loop_scope='session')
async def clean_db(test_db):
    # Reuse indexes within this run; drop/create churn is not the tested workload.
    for name in await test_db.list_collection_names():
        await test_db[name].delete_many({})
    yield test_db
    # Cleanup errors fail the suite, never hidden by except:pass.
    allowed(test_db.name)
    for name in await test_db.list_collection_names():
        await test_db[name].delete_many({})


@pytest.fixture(autouse=True)
def block_external_http(monkeypatch):
    import requests
    import httpx
    import urllib.request
    def denied(*args, **kwargs):
        raise RuntimeError('External HTTP disabled in isolated Packet 1 tests')
    async def async_denied(*args, **kwargs):
        raise RuntimeError('External HTTP disabled in isolated Packet 1 tests')
    monkeypatch.setattr(requests.sessions.Session, 'request', denied)
    monkeypatch.setattr(urllib.request, 'urlopen', denied)
    monkeypatch.setattr(httpx.HTTPTransport, 'handle_request', denied)
    monkeypatch.setattr(httpx.AsyncHTTPTransport, 'handle_async_request', async_denied)


@pytest.fixture
def synthetic_staff_user():
    return {'id': str(uuid.uuid4()), 'email': 'reviewer@isolated.invalid', 'role': 'reviewer',
            'name': 'Synthetic reviewer', 'exam': 'JEE Main', 'access_type': 'staff_password'}


@pytest.fixture
def synthetic_owner_user(synthetic_staff_user):
    return {**synthetic_staff_user, 'role': 'owner'}


@pytest.fixture
def synthetic_student_user():
    return {'id': str(uuid.uuid4()), 'phone': '+12025550184', 'role': 'student',
            'name': 'Synthetic learner', 'exam': 'JEE Main', 'access_type': 'unverified_phone'}


async def session_fixture(db, user, phone=False):
    from tejas.auth import token
    coll = db.tejas_phone_profiles if phone else db.tejas_users
    await coll.insert_one(dict(user))
    sid = str(uuid.uuid4())
    await db.tejas_sessions.insert_one({'id': sid, 'user_id': user['id'],
        'access_type': user['access_type'], 'expires_at': datetime.now(timezone.utc) + timedelta(hours=1)})
    return {'user': user, 'session_id': sid, 'cookies': {
        'access_token': token(user, sid, 'access', 900), 'refresh_token': token(user, sid, 'refresh', 3600)}}


@pytest_asyncio.fixture(loop_scope='session')
async def staff_session(clean_db, synthetic_staff_user):
    return await session_fixture(clean_db, synthetic_staff_user)


@pytest_asyncio.fixture(loop_scope='session')
async def student_session(clean_db, synthetic_student_user):
    return await session_fixture(clean_db, synthetic_student_user, phone=True)


@pytest_asyncio.fixture(loop_scope='session')
async def http_client(clean_db):
    import httpx
    from server import app
    # ASGITransport does not trigger lifespan; indexes are initialized explicitly.
    # Never seed an operator account or run preview maintenance during tests.
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url='https://testserver') as client:
        yield client
