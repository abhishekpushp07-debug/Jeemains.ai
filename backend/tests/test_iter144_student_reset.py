"""Iteration 144 TEST-ONLY: backend/tools/reset_student_data.py prepare/apply against dedicated
isolated DBs (tejas_isolated_reset144 / shadow tejas_isolated_restore144) with an in-memory fake
private object store. Never touches MONGO_URL/DB_NAME customer DB; both DBs dropped at session end."""
import asyncio
import gzip
import hashlib
import json
import os
import re
import sys
import threading
import types
import uuid
from datetime import datetime, timezone
from pathlib import Path

import pytest
from bson import Binary, Code, DBRef, Decimal128, Int64, MaxKey, MinKey, ObjectId, Regex, Timestamp, json_util
from bson.raw_bson import RawBSONDocument
from dotenv import load_dotenv
from pymongo import MongoClient

BACKEND = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND))
load_dotenv(BACKEND / '.env')
REAL_DB = os.environ['DB_NAME']
TEST_DB = 'tejas_isolated_reset144'
SHADOW_DB = 'tejas_isolated_restore144'
assert REAL_DB not in (TEST_DB, SHADOW_DB)

from tools import reset_student_data as R  # noqa: E402

OWNER = 'qa144-owner'
OWNER_EMAIL = 'qa144-owner@example.test'
BINDING = hashlib.sha256(b'qa144-isolated-binding').hexdigest()
OLD = [f'qa144-old-{i:02d}' for i in range(1, 14)]
DEL, DELU = 'del', 'del_unlinked'
JOBONLY = 'qa144-jobonly'
EMPTY = 'tejas_qa_empty_validated'


# ---------------------------------------------------------------- infrastructure
@pytest.fixture(scope='session')
def client():
    c = MongoClient(os.environ['MONGO_URL'], tz_aware=False)
    c.drop_database(TEST_DB); c.drop_database(SHADOW_DB)
    real_before = c[REAL_DB].list_collection_names()
    real_counts = {n: c[REAL_DB][n].estimated_document_count() for n in real_before}
    yield c
    c.drop_database(TEST_DB)
    c.drop_database(SHADOW_DB)
    assert TEST_DB not in c.list_database_names() and SHADOW_DB not in c.list_database_names()
    # customer DB untouched by this suite (no R.* call ever receives it)
    assert sorted(c[REAL_DB].list_collection_names()) == sorted(real_before)
    print('REAL_DB_COUNTS_UNCHANGED', all(c[REAL_DB][n].estimated_document_count() == v for n, v in real_counts.items()))
    c.close()


def wipe(d):
    # delete_many (not drop) keeps WiredTiger idents stable: repeated drop/create churn exhausted
    # mongod's 1024 fd soft limit during the first run (WT_PANIC 'Too many open files').
    assert d.name in (TEST_DB, SHADOW_DB)
    for n in d.list_collection_names():
        d[n].delete_many({})


@pytest.fixture
def db(client):
    d = client[TEST_DB]
    assert d.name == TEST_DB != REAL_DB
    wipe(d)
    yield d


class FakeStore:
    """TEST-ONLY in-memory private object storage (no network / no secrets)."""
    def __init__(self):
        self.objects, self.puts, self.put_hook, self.corrupt_readback = {}, [], None, False

    def put(self, data, owner):
        if self.put_hook:
            self.put_hook(len(self.puts))
        path = f'qa144/{owner}/{uuid.uuid4()}.jsonl.gz'
        self.objects[path] = bytes(data)
        self.puts.append(path)
        return {'path': path}

    def fetch(self, path):
        data = self.objects[path]
        return data[:-1] + bytes([data[-1] ^ 1]) if self.corrupt_readback else data


def restore_shadow(shadow, manifest, store):
    """Operator-style restore from the private backup: recreate options, then indexes, then raw rows."""
    assert shadow.name == SHADOW_DB
    existing = set(shadow.list_collection_names())
    for name, meta in manifest['collections'].items():
        assert meta['type'] == 'collection'
        assert name not in existing, 'shadow must be fresh (dropped once at session start)'
        shadow.create_collection(name, **dict(meta['options']))
        for idx in meta['indexes']:
            if idx['name'] == '_id_':
                continue
            opts = {k: v for k, v in idx.items() if k not in ('key', 'v', 'ns')}
            shadow[name].create_index(list(idx['key'].items()), **opts)
    for p in manifest['parts']:
        rows = [json_util.loads(line) for line in gzip.decompress(store.objects[p['path']]).splitlines()]
        shadow[p['collection']].insert_many(rows)


def canon_all(d):
    out = {}
    for name in sorted(d.list_collection_names()):
        if name == R.RECEIPTS or not d[name].estimated_document_count():
            continue
        out[name] = {R.encoded(r['_id']): R.encoded(r) for r in d[name].find({})}
    return out


def expected_ids(d, include_unlinked):
    marks = {DEL, DELU} if include_unlinked else {DEL}
    return {n: {R.encoded(r['_id']) for r in d[n].find({'_qa': {'$in': list(marks)}})}
            for n in d.list_collection_names() if n != R.RECEIPTS}


def plan_ids(plan):
    return {n: {R.encoded(r['_id']) for r in rows} for n, rows in plan['records'].items()}


# ---------------------------------------------------------------- seed (synthetic only)
def seed(d, big=False):
    t = datetime(2026, 1, 5, 10, 30, 15, 123000)
    ins = lambda c, *docs: d[c].insert_many([dict(x) for x in docs])
    ins('tejas_users',
        {'id': OWNER, 'email': OWNER_EMAIL, 'role': 'owner', 'password_hash': '$2b$12$' + 'x' * 53, 'name': 'QA Owner'},
        {'id': 'qa144-admin', 'email': 'qa144-admin@example.test', 'role': 'admin'},
        {'id': 'qa144-reviewer', 'email': 'qa144-rev@example.test', 'role': 'reviewer'},
        {'id': 'qa144-su1', 'email': 'qa144-su1@example.test', 'role': 'student', '_qa': DEL})
    ins('tejas_phone_profiles',
        {'id': 'qa144-p1', 'phone': '+910000144001', 'role': 'student', 'access_type': 'unverified_phone', '_qa': DEL},
        {'id': 'qa144-p2', 'phone': '+910000144002', 'role': 'student', 'access_type': 'unverified_phone', '_qa': DEL},
        {'id': 'qa144-p3', 'phone': '+910000144003', 'role': 'student', 'access_type': 'unverified_phone', '_qa': DEL})
    # attempts: owner current + completed, students + child retry, 13 unlinked old users
    ins('tejas_attempts',
        {'id': 'qa144-att-own', 'user_id': OWNER, 'status': 'in_progress', 'started_at': t, 'answers': {'q1': 'A'}},
        {'id': 'qa144-att-own2', 'user_id': OWNER, 'status': 'completed', 'mode': 'practice', 'result': {'score': Decimal128('123.25')}},
        {'id': 'qa144-att-su1', 'user_id': 'qa144-su1', 'status': 'completed', '_qa': DEL},
        {'id': 'qa144-att-p1', 'user_id': 'qa144-p1', 'status': 'completed', '_qa': DEL},
        {'id': 'qa144-att-p1r', 'user_id': 'qa144-p1', 'mode': 'retry', 'parent_attempt': 'qa144-att-p1', '_qa': DEL},
        {'id': 'qa144-att-p2', 'user_id': 'qa144-p2', 'status': 'completed', '_qa': DEL},
        *[{'id': f'qa144-oa-{i}', 'user_id': u, 'status': 'completed', '_qa': DELU} for i, u in enumerate(OLD)])
    ins('tejas_ledgers',
        {'id': 'qa144-att-own2', 'user_id': OWNER, 'attempt_id': 'qa144-att-own2', 'rows': [{'id': 'q1', 'outcome': 'correct'}]},
        {'id': 'qa144-ownorph', 'user_id': OWNER, 'rows': []},  # owner orphan ledger -> protected
        {'id': 'qa144-att-su1', 'rows': [{'id': 'q1', 'outcome': 'incorrect'}], '_qa': DEL},  # legacy id-only
        {'id': 'qa144-led-p1', 'attempt_id': 'qa144-att-p1', 'user_id': 'qa144-p1', '_qa': DEL},
        {'id': 'qa144-orphled-1', 'rows': [], '_qa': DELU},  # orphan, no attempt, no user
        {'id': 'qa144-orphled-2', 'user_id': OLD[0], 'rows': [], '_qa': DELU},
        *[{'id': f'qa144-oa-{i}', 'rows': [], '_qa': DELU} for i in range(len(OLD))])
    for c in ('tejas_score_versions', 'tejas_reviews', 'tejas_question_reports'):
        ins(c, {'id': f'{c}-own', 'user_id': OWNER, 'attempt_id': 'qa144-att-own2'},
            {'id': f'{c}-su1', 'user_id': 'qa144-su1', 'attempt_id': 'qa144-att-su1', '_qa': DEL},
            {'id': f'{c}-p1r', 'attempt_id': 'qa144-att-p1r', '_qa': DEL},
            {'id': f'{c}-orph', 'attempt_id': 'qa144-gone-attempt', '_qa': DELU})
    for c in ('tejas_sessions', 'tejas_preflight', 'tejas_saved_tests'):
        ins(c, {'id': f'{c}-own', 'user_id': OWNER, 'expires_at': t},
            {'id': f'{c}-admin', 'user_id': 'qa144-admin'},
            {'id': f'{c}-su1', 'user_id': 'qa144-su1', '_qa': DEL},
            {'id': f'{c}-p1', 'user_id': 'qa144-p1', '_qa': DEL},
            {'id': f'{c}-p3', 'user_id': 'qa144-p3', '_qa': DEL},
            *[{'id': f'{c}-old{i}', 'user_id': u, '_qa': DELU} for i, u in enumerate(OLD)])
    ins('tejas_cohort_entries',
        {'cohort_id': 'C1', 'user_id': OWNER, 'attempt_id': 'qa144-att-own2', 'score': 10},
        {'cohort_id': 'C1', 'user_id': 'qa144-su1', 'attempt_id': 'qa144-att-su1', '_qa': DEL},
        {'cohort_id': 'C1', 'user_id': 'qa144-p1', 'attempt_id': 'qa144-att-p1', '_qa': DEL},
        {'cohort_id': 'C2', 'user_id': 'qa144-p2', 'attempt_id': 'qa144-att-p2', '_qa': DEL},
        {'cohort_id': 'C4', 'user_id': OWNER, 'attempt_id': 'qa144-att-own', 'score': 3},
        {'cohort_id': 'C5', 'attempt_id': 'qa144-gone-attempt2', '_qa': DELU})
    ins('tejas_cohort_snapshots', {'id': 'C1', 'sample_size': 3, '_qa': DEL}, {'id': 'C2', 'sample_size': 1, '_qa': DEL},
        {'id': 'C3', 'sample_size': 0, '_qa': DELU}, {'id': 'C4', 'sample_size': 1}, {'id': 'C5', 'sample_size': 1, '_qa': DELU})
    ins('tejas_cohorts', *[{'id': c, 'dirty': False, 'generation': 'g0', 'set_id': 'qa144-set'} for c in ('C1', 'C2', 'C3', 'C4', 'C5')])
    ins('tejas_jobs',
        {'id': 'j-own', 'kind': 'grade', 'user_id': OWNER, 'payload': {'attempt_id': 'qa144-att-own2'}},
        {'id': 'j-own-cohort', 'kind': 'cohort', 'user_id': OWNER, 'payload': {'cohort_id': 'C1'}},
        {'id': 'j-su1-grade', 'kind': 'grade', 'user_id': 'qa144-su1', 'payload': {'attempt_id': 'qa144-att-su1'}, '_qa': DEL},
        {'id': 'j-p1-report', 'kind': 'report', 'user_id': 'qa144-p1', 'payload': {}, '_qa': DEL},
        {'id': 'j-su1-cohort', 'kind': 'cohort', 'user_id': 'qa144-su1', 'payload': {'cohort_id': 'C1'}, '_qa': DEL},
        {'id': 'j-su1-ai', 'kind': 'ai_solution', 'user_id': 'qa144-su1', 'payload': {'question_id': 'q1'}},  # shared AI kept
        {'id': 'j-old-grade', 'kind': 'grade', 'user_id': OLD[3], 'payload': {'attempt_id': 'qa144-oa-3'}, '_qa': DELU})
    ins('tejas_audits', {'id': 'au-own', 'actor': OWNER, 'action': 'publish'},
        {'id': 'au-su1', 'actor': 'qa144-su1', 'action': 'report', '_qa': DEL},
        {'id': 'au-old', 'actor': OLD[5], 'action': 'x', '_qa': DELU})
    # academic content + shared AI (must be byte-identical)
    ins('tejas_sets', {'id': 'qa144-set', 'title': 'QA paper', 'questions': [{'id': 'q1', 'text': 'é∑ unicode'}], 'created_by': OWNER})
    ins('tejas_versions', {'id': 'qa144-v1', 'set_id': 'qa144-set', 'n': Int64(2 ** 40)})
    ins('tejas_files', {'id': 'qa144-f1', 'blob': Binary(b'%PDF-1.7 original'), 'sha256': 'abc', 'uploaded_by': 'qa144-su1'})
    ins('tejas_packs', {'id': 'qa144-pack', 'sets': ['qa144-set']})
    ins('tejas_chapter_books', {'id': 'qa144-cb'})
    ins('tejas_ai_solutions', {'id': 'qa144-ai', 'question_id': 'q1', 'requested_by': 'qa144-su1', 'text': 'shared'})
    ins('tejas_question_solutions', {'id': 'qa144-qs', 'attempt_id': 'qa144-att-su1'})  # content keyed by attempt -> kept
    # unknown foreign schemas -> never deleted by guessing
    ins('tejas_future_feature', {'user_id': 'qa144-su1', 'x': 1}, {'user_id': OLD[1], 'attempt_id': 'qa144-oa-1'})
    # canonical type stress
    ins('tejas_typecheck', {
        'oid': ObjectId(), 'dt': t, 'dt_old': datetime(1960, 2, 29, 0, 0, 0, 1000), 'bin0': Binary(os.urandom(64)),
        'uuid4': Binary(uuid.uuid4().bytes, 4), 'md5': Binary(hashlib.md5(b'x').digest(), 5), 'user_bin': Binary(b'\x00\xff', 128),
        'dec': Decimal128('-0.000000000000000000001E-10'), 'dec_nan': Decimal128('NaN'), 'i64': Int64(-(2 ** 63)), 'i32': 2 ** 31 - 1,
        'f_neg0': -0.0, 'f_inf': float('inf'), 'f_nan': float('nan'), 'f': 1.0, 'big': 1e308, 'rx': Regex('^qa.*$', 'imx'),
        'ts': Timestamp(1700000000, 7), 'mn': MinKey(), 'mx': MaxKey(), 'code': Code('function(){return x}', {'x': 1}),
        'ref': DBRef('tejas_users', OWNER, TEST_DB), 'nested': {'z': [1, {'b': None, 'a': True}], 'a': 'ड'}, 'empty': {}, 'n': None})
    d.tejas_typecheck.insert_one({'_id': 'string-id', 'v': 1})
    d.tejas_typecheck.insert_one({'_id': {'compound': 1, 'k': 'v'}, 'v': 2})
    d.tejas_users.create_index('email', unique=True)
    # iter146: unlinked user with ONLY a personal report job (captured) + unlinked shared AI job (retained)
    ins('tejas_jobs', {'id': 'j-jobonly-report', 'kind': 'report', 'user_id': JOBONLY, 'payload': {}, '_qa': DELU},
        {'id': 'j-anon-ai', 'kind': 'ai_solution', 'user_id': 'qa144-unknown-ai', 'payload': {'question_id': 'q1'}})
    # iter146: compound unique (key ORDER matters) + TTL (far future so the TTL monitor never fires) indexes
    d.tejas_sessions.create_index([('user_id', 1), ('id', -1)], unique=True, name='uid_id_desc')
    d.tejas_sessions.create_index('expires_at', expireAfterSeconds=10 * 365 * 86400, name='ttl_exp')
    d.tejas_attempts.create_index([('status', -1), ('user_id', 1), ('id', 1)], name='att_cmp')
    # iter146: EMPTY collection with options + compound unique index must be restorable from manifest
    if EMPTY not in d.list_collection_names():
        d.create_collection(EMPTY, validator={'$jsonSchema': {'bsonType': 'object', 'required': ['k']}},
                            validationLevel='moderate', collation={'locale': 'en', 'strength': 2})
    d[EMPTY].create_index([('k', -1), ('a', 1)], unique=True, name='empty_cmp')
    # iter146: 160 docs of typed BSON with varied (non-sorted) field order and nested order
    rng = __import__('random').Random(146)
    vals = [lambda i: ObjectId(), lambda i: t, lambda i: datetime(1950 + i % 70, 1 + i % 12, 1 + i % 28, i % 24, 0, 0, (i % 1000) * 1000),
            lambda i: Binary(bytes([i % 256]) * (i % 9)), lambda i: Binary(uuid.UUID(int=i).bytes, 4), lambda i: Binary(b'\x01' * 16, 3),
            lambda i: Decimal128(f'{i}.{i:03d}E-{i % 30}'), lambda i: Int64(i * 2 ** 33), lambda i: -i, lambda i: float(i) / 7, lambda i: -0.0,
            lambda i: float('-inf'), lambda i: Regex(f'^x{i}', 'i'), lambda i: Timestamp(i + 1, i), lambda i: MinKey(), lambda i: MaxKey(),
            lambda i: Code(f'f{i}'), lambda i: Code('g', {'s': i}), lambda i: DBRef('c', i), lambda i: None, lambda i: bool(i % 2),
            lambda i: 'ü' * (i % 5), lambda i: [i, {'zz': i, 'aa': [None, {'y': 1, 'b': 2}]}], lambda i: {'zeta': {'k2': i, 'k1': -i}, 'alpha': []}]
    stress = []
    for i in range(160):
        keys = [f'f{k:02d}' for k in range(rng.randint(4, 12))]
        rng.shuffle(keys)
        stress.append({'_id': i if i % 3 else f's{i}', **{k: vals[rng.randrange(len(vals))](i) for k in keys}})
    d.tejas_typestress.insert_many(stress)
    if big:  # force 8 MiB chunk boundary with incompressible original-file bytes
        d.tejas_files.insert_many([{'id': f'qa144-big-{i}', 'blob': Binary(os.urandom(900_000))} for i in range(11)])


def do_prepare(d, store, include_unlinked=True):
    return R.prepare(d, BINDING, OWNER_EMAIL, store.put, store.fetch, writers_paused=True, include_unlinked=include_unlinked)


def do_apply(d, store, receipt, approval=None):
    return R.apply(d, BINDING, OWNER_EMAIL, receipt['_id'], approval or receipt['manifest']['sha256'], store.fetch, writers_paused=True)


def assert_nothing_deleted(d, before, phase='prepared', rid=None):
    assert canon_all(d) == before
    if rid:
        assert d[R.RECEIPTS].find_one({'_id': rid})['phase'] == phase


# ---------------------------------------------------------------- guards
class TestGuards:
    def test_writers_paused_required_both_actions(self, db):
        seed(db); store = FakeStore(); before = canon_all(db)
        with pytest.raises(RuntimeError, match='Pause ALL'):
            R.prepare(db, BINDING, OWNER_EMAIL, store.put, store.fetch)
        with pytest.raises(RuntimeError, match='Pause ALL'):
            R.apply(db, BINDING, OWNER_EMAIL, 'x', 'y', store.fetch)
        assert store.puts == [] and canon_all(db) == before and db[R.RECEIPTS].count_documents({}) == 0

    def test_cli_requires_writers_paused_flag(self, monkeypatch):
        monkeypatch.setattr(sys, 'argv', ['reset_student_data.py', 'prepare'])
        with pytest.raises(RuntimeError, match='Pause ALL'):
            R.main()

    def test_missing_owner_fails_closed(self, db):
        seed(db); store = FakeStore()
        with pytest.raises(RuntimeError, match='owner account was not found'):
            R.prepare(db, BINDING, 'nobody@example.test', store.put, store.fetch, writers_paused=True)
        assert store.puts == [] and db[R.RECEIPTS].count_documents({}) == 0

    def test_role_overlap_across_roots_fails(self, db):
        seed(db); db.tejas_phone_profiles.insert_one({'id': 'qa144-reviewer', 'role': 'student', 'phone': '+91x'})
        store = FakeStore()
        with pytest.raises(RuntimeError, match='overlaps a protected'):
            do_prepare(db, store, include_unlinked=False)
        assert db[R.RECEIPTS].count_documents({}) == 0

    def test_readback_mismatch_blocks_prepare(self, db):
        seed(db); store = FakeStore(); store.corrupt_readback = True
        with pytest.raises(RuntimeError, match='read-back hash mismatch'):
            do_prepare(db, store)
        assert db[R.RECEIPTS].count_documents({}) == 0

    @pytest.mark.parametrize('kind', ['target', 'protected'])
    def test_change_during_backup_blocks_prepare(self, db, kind):
        seed(db); store = FakeStore()

        def hook(n):
            if n == 1:
                if kind == 'target':
                    db.tejas_sessions.insert_one({'id': 'late', 'user_id': 'qa144-su1'})
                else:
                    db.tejas_attempts.update_one({'id': 'qa144-att-own'}, {'$set': {'answers.q2': 'B'}})
        store.put_hook = hook
        with pytest.raises(RuntimeError, match='Database changed during backup'):
            do_prepare(db, store)
        assert db[R.RECEIPTS].count_documents({}) == 0


# ---------------------------------------------------------------- plan scope
class TestPlanScope:
    @pytest.mark.parametrize('include_unlinked', [True, False])
    def test_plan_matches_expected_targets_exactly(self, db, include_unlinked):
        seed(db)
        exp = expected_ids(db, include_unlinked)
        plan = R.build_plan(db, include_unlinked)
        got = plan_ids(plan)
        for name in set(exp) | set(got):
            assert got.get(name, set()) == exp.get(name, set()), name
        assert plan['account_ids'] == sorted(['qa144-su1', 'qa144-p1', 'qa144-p2', 'qa144-p3'])
        assert set(OLD).issubset(plan['user_ids']) == include_unlinked
        assert OWNER not in plan['user_ids'] and 'qa144-admin' not in plan['user_ids']
        assert (JOBONLY in plan['user_ids']) == include_unlinked and 'qa144-unknown-ai' not in plan['user_ids']


# ---------------------------------------------------------------- full flow + restore proof
class TestFullFlowAndRestore:
    def test_prepare_backup_restore_apply_end_to_end(self, client, db):
        seed(db, big=True)
        store = FakeStore()
        original = canon_all(db)
        raw_original = {n: {R.encoded(r['_id']): r.raw for r in db.get_collection(n, codec_options=db.codec_options.with_options(document_class=RawBSONDocument)).find({})}
                        for n in db.list_collection_names()}
        exp = expected_ids(db, True)
        receipt = do_prepare(db, store, include_unlinked=True)
        assert receipt['phase'] == 'prepared' and receipt['students'] == 4 and receipt['unlinked_profile_ids'] == 14
        assert canon_all(db) == original, 'prepare must not modify data'
        manifest = R.verified_manifest(receipt, store.fetch)
        assert manifest['database'] == TEST_DB and manifest['binding'] == BINDING and manifest['owner_id'] == OWNER
        # chunk boundary
        fparts = [p for p in manifest['parts'] if p['collection'] == 'tejas_files']
        assert len(fparts) >= 2
        for p in fparts[:-1]:
            assert len(gzip.decompress(store.objects[p['path']])) >= 8 * 1024 * 1024
        assert sum(p['records'] for p in fparts) == db.tejas_files.count_documents({})
        # restore every part into a FRESH shadow DB: options + indexes (key order) + typed raw BSON rows
        shadow = client[SHADOW_DB]
        restore_shadow(shadow, manifest, store)
        restored = canon_all(shadow)
        assert restored == original
        assert EMPTY in shadow.list_collection_names() and shadow[EMPTY].count_documents({}) == 0
        for name, meta in manifest['collections'].items():
            info = next(c for c in shadow.list_collections() if c['name'] == name)
            assert R.backup_encoded(info.get('options', {})) == R.backup_encoded(meta['options']), name
            got = {i['name']: i for i in shadow[name].list_indexes()}
            want = {i['name']: i for i in meta['indexes']}
            assert set(got) == set(want), name
            for iname, idx in want.items():
                assert list(got[iname]['key'].items()) == list(idx['key'].items()), (name, iname)
                assert R.backup_encoded(got[iname]) == R.backup_encoded(idx), (name, iname)
        sidx = {i['name']: i for i in shadow.tejas_sessions.list_indexes()}
        assert list(sidx['uid_id_desc']['key'].items()) == [('user_id', 1), ('id', -1)] and sidx['uid_id_desc']['unique'] is True
        assert sidx['ttl_exp']['expireAfterSeconds'] == 10 * 365 * 86400
        assert shadow.tejas_users.index_information()['email_1']['unique'] is True
        einfo = next(c for c in shadow.list_collections() if c['name'] == EMPTY)
        assert einfo['options']['validationLevel'] == 'moderate' and einfo['options']['collation']['strength'] == 2
        tc = shadow.tejas_typecheck.find_one({'oid': {'$exists': True}})
        assert isinstance(tc['oid'], ObjectId) and isinstance(tc['dt'], datetime) and isinstance(tc['dec'], Decimal128)
        assert isinstance(tc['i64'], Int64) and isinstance(tc['ts'], Timestamp) and isinstance(tc['code'], Code)
        assert isinstance(tc['ref'], DBRef) and isinstance(tc['mn'], MinKey) and isinstance(tc['bin0'], bytes) and isinstance(tc['md5'], Binary) and tc['md5'].subtype == 5
        assert tc['uuid4'] == db.tejas_typecheck.find_one({'_id': tc['_id']})['uuid4']
        assert shadow.tejas_typecheck.count_documents({'_id': {'compound': 1, 'k': 'v'}}) == 1
        # raw BSON byte fidelity (field order + types) for EVERY doc incl. 160 type-stress docs
        raw_shadow = {n: {R.encoded(r['_id']): r.raw for r in shadow.get_collection(n, codec_options=shadow.codec_options.with_options(document_class=RawBSONDocument)).find({})}
                      for n in shadow.list_collection_names()}
        order_lost = sum(1 for n, m in raw_original.items() for k, raw in m.items() if raw_shadow.get(n, {}).get(k) != raw)
        total = sum(len(m) for m in raw_original.values())
        print('RAW_BSON_MISMATCH_DOCS', order_lost, 'of', total, 'stress', len(raw_original['tejas_typestress']))
        assert len(raw_original['tejas_typestress']) == 160 and order_lost == 0
        wipe(shadow)

        # apply
        done = do_apply(db, store, receipt)
        assert done['phase'] == 'complete' and not any(done['remaining'].values())
        after = canon_all(db)
        for name, docs in original.items():
            kept_expected = {k: v for k, v in docs.items() if k not in exp.get(name, set())}
            if name == 'tejas_cohorts':
                assert set(after[name]) == set(kept_expected)
                continue
            assert after.get(name, {}) == kept_expected, name
        coh = {c['id']: c for c in db.tejas_cohorts.find()}
        for cid in ('C1', 'C2', 'C3', 'C5'):
            assert coh[cid]['dirty'] is True and coh[cid]['generation'] == 'student-reset-' + receipt['_id']
        assert coh['C4']['dirty'] is False and coh['C4']['generation'] == 'g0'
        assert db.tejas_cohort_entries.count_documents({'user_id': OWNER}) == 2
        assert db.tejas_attempts.find_one({'id': 'qa144-att-own'})['answers'] == {'q1': 'A'}
        assert db.tejas_future_feature.count_documents({}) == 2
        assert db.tejas_jobs.count_documents({'id': 'j-su1-ai'}) == 1
        # replay: complete -> no re-deletion even if an identical row reappears
        db.tejas_sessions.insert_one({'id': 'reappeared', 'user_id': 'qa144-su1'})
        again = do_apply(db, store, receipt)
        assert again['phase'] == 'complete' and db.tejas_sessions.count_documents({'id': 'reappeared'}) == 1

        # actual auth.identity against the test DB binding (temporary in-process rebind only)
        async def check_identity():
            from motor.motor_asyncio import AsyncIOMotorClient
            from tejas import auth
            mc = AsyncIOMotorClient(os.environ['MONGO_URL'])
            saved = auth.db, auth.users
            try:
                auth.db = mc[TEST_DB]; auth.users = mc[TEST_DB].tejas_users
                owner = await auth.identity({'sub': OWNER})
                assert owner['role'] == 'owner' and 'password_hash' not in owner
                for p in ({'sub': 'qa144-su1'}, {'sub': 'qa144-p1', 'access_type': 'unverified_phone'}):
                    with pytest.raises(ValueError):
                        await auth.identity(p)
            finally:
                auth.db, auth.users = saved
                mc.close()
            assert auth.db.name == REAL_DB
        asyncio.run(check_identity())

    def test_backup_preserves_raw_bson_field_order(self, client, db):
        db.tejas_typecheck.insert_one({'_id': 1, 'z': 1, 'a': {'y': 1, 'b': 2}})
        line = R.backup_encoded(db.tejas_typecheck.find_one({'_id': 1}))
        assert R.encoded({'z': 1, 'a': 2}) == R.encoded({'a': 2, 'z': 1})  # canonical plan hash is order-insensitive
        assert R.backup_encoded({'z': 1, 'a': 2}) != R.backup_encoded({'a': 2, 'z': 1})  # backup keeps order
        client[SHADOW_DB].t.delete_many({})
        client[SHADOW_DB].t.insert_one(json_util.loads(line))
        raw = lambda d, c: d.get_collection(c, codec_options=d.codec_options.with_options(document_class=RawBSONDocument)).find_one({'_id': 1}).raw
        try:
            assert raw(client[SHADOW_DB], 't') == raw(db, 'tejas_typecheck')
        finally:
            client[SHADOW_DB].t.delete_many({})


# ---------------------------------------------------------------- tamper / fail-closed
def rewrite_manifest(d, store, receipt, mutate, rehash_receipt=False):
    """Simulates an attacker/operator re-approving a tampered manifest. rehash_receipt=True additionally
    rewrites the receipt's plan/parts/collections hashes so the deeper coverage checks are exercised."""
    m = json_util.loads(gzip.decompress(store.objects[receipt['manifest']['path']]))
    mutate(m)
    blob = gzip.compress(R.backup_encoded(m), mtime=0)
    store.objects[receipt['manifest']['path']] = blob
    sha = hashlib.sha256(blob).hexdigest()
    upd = {'manifest.sha256': sha}
    if rehash_receipt:
        upd.update({'plan_hash': R.digest(m['plan']), 'parts_hash': R.digest(m['parts']), 'collections_hash': R.record_digest(m['collections'])})
    d[R.RECEIPTS].update_one({'_id': receipt['_id']}, {'$set': upd})
    return sha


class TestFailClosed:
    @pytest.mark.parametrize('case', ['part_bitflip', 'missing_part', 'missing_manifest', 'count_tamper', 'plan_tamper',
                                      'wrong_approval', 'wrong_binding', 'wrong_owner_email', 'other_owner', 'manifest_db_name',
                                      'unknown_reset_id'])
    def test_tamper_blocks_apply_without_deletion(self, db, case):
        seed(db); store = FakeStore(); receipt = do_prepare(db, store)
        before = canon_all(db); approval = receipt['manifest']['sha256']
        rid, owner_email, binding = receipt['_id'], OWNER_EMAIL, BINDING
        m = json_util.loads(gzip.decompress(store.objects[receipt['manifest']['path']]))
        if case == 'part_bitflip':
            p = m['parts'][3]['path']; b = bytearray(store.objects[p]); b[len(b) // 2] ^= 0x10; store.objects[p] = bytes(b)
        elif case == 'missing_part':
            del store.objects[m['parts'][0]['path']]
        elif case == 'missing_manifest':
            del store.objects[receipt['manifest']['path']]
        elif case == 'count_tamper':
            approval = rewrite_manifest(db, store, receipt, lambda x: x['parts'][0].__setitem__('records', x['parts'][0]['records'] + 1))
        elif case == 'plan_tamper':
            approval = rewrite_manifest(db, store, receipt, lambda x: x['plan']['user_ids'].append(OWNER))
        elif case == 'wrong_approval':
            approval = '0' * 64
        elif case == 'wrong_binding':
            binding = 'f' * 64
        elif case == 'wrong_owner_email':
            owner_email = 'qa144-admin@example.test'
        elif case == 'other_owner':
            db.tejas_users.insert_one({'id': 'qa144-owner2', 'email': 'qa144-o2@example.test', 'role': 'owner'})
            before = canon_all(db); owner_email = 'qa144-o2@example.test'
        elif case == 'manifest_db_name':
            approval = rewrite_manifest(db, store, receipt, lambda x: x.__setitem__('database', 'other_db'))
        elif case == 'unknown_reset_id':
            rid = str(uuid.uuid4())
        with pytest.raises((RuntimeError, KeyError)):
            R.apply(db, binding, owner_email, rid, approval, store.fetch, writers_paused=True)
        assert_nothing_deleted(db, before, 'prepared', receipt['_id'])


# ---------------------------------------------------------------- post-prepare drift
class TestDriftAfterPrepare:
    def test_new_student_after_prepare_survives(self, db):
        seed(db); store = FakeStore(); receipt = do_prepare(db, store)
        db.tejas_phone_profiles.insert_one({'id': 'qa144-new', 'role': 'student', 'phone': '+910000144099'})
        db.tejas_attempts.insert_one({'id': 'qa144-att-new', 'user_id': 'qa144-new'})
        db.tejas_sessions.insert_one({'id': 'sess-new', 'user_id': 'qa144-new'})
        db.tejas_ledgers.insert_one({'id': 'qa144-att-new', 'rows': []})
        assert do_apply(db, store, receipt)['phase'] == 'complete'
        assert db.tejas_phone_profiles.count_documents({'id': 'qa144-new'}) == 1
        assert db.tejas_attempts.count_documents({'id': 'qa144-att-new'}) == 1
        assert db.tejas_sessions.count_documents({'id': 'sess-new'}) == 1 and db.tejas_ledgers.count_documents({'id': 'qa144-att-new'}) == 1

    @pytest.mark.parametrize('case', ['new_child_attempt', 'new_session', 'mutated_answers', 'mutated_legacy_ledger',
                                      'promote_reviewer', 'promote_owner', 'phone_promote', 'unlinked_old_activity'])
    def test_target_drift_blocks_apply(self, db, case):
        seed(db); store = FakeStore(); receipt = do_prepare(db, store)
        if case == 'new_child_attempt':
            db.tejas_attempts.insert_one({'id': 'qa144-att-p1r2', 'user_id': 'qa144-p1', 'parent_attempt': 'qa144-att-p1'})
        elif case == 'new_session':
            db.tejas_sessions.insert_one({'id': 'sess-late', 'user_id': 'qa144-su1'})
        elif case == 'mutated_answers':
            db.tejas_attempts.update_one({'id': 'qa144-att-p1'}, {'$set': {'answers': {'q1': 'C'}}})
        elif case == 'mutated_legacy_ledger':
            db.tejas_ledgers.update_one({'id': 'qa144-att-su1'}, {'$set': {'rows': []}})
        elif case == 'promote_reviewer':
            db.tejas_users.update_one({'id': 'qa144-su1'}, {'$set': {'role': 'reviewer'}})
        elif case == 'promote_owner':
            db.tejas_users.update_one({'id': 'qa144-su1'}, {'$set': {'role': 'owner'}})
        elif case == 'phone_promote':
            db.tejas_users.insert_one({'id': 'qa144-p2', 'email': 'p2staff@example.test', 'role': 'reviewer'})
        elif case == 'unlinked_old_activity':
            db.tejas_saved_tests.insert_one({'id': 'late-old', 'user_id': OLD[4]})
        before = canon_all(db)
        with pytest.raises(RuntimeError, match='changed after backup|now protected'):
            do_apply(db, store, receipt)
        assert_nothing_deleted(db, before, 'prepared', receipt['_id'])


# ---------------------------------------------------------------- CAS / crash / mutation during apply
class CollProxy:
    def __init__(self, coll, hooks):
        self._c, self._h = coll, hooks

    def __getattr__(self, n):
        return getattr(self._c, n)

    def delete_many(self, *a, **k):
        self._h.setdefault('delete', lambda name: None)(self._c.name)
        return self._c.delete_many(*a, **k)

    def find_one_and_update(self, *a, **k):
        self._h.setdefault('cas', lambda: None)()
        return self._c.find_one_and_update(*a, **k)


class DBProxy:
    def __init__(self, d, hooks):
        self._d, self._h = d, hooks

    @property
    def name(self):
        return self._d.name

    def __getitem__(self, n):
        return CollProxy(self._d[n], self._h)

    def __getattr__(self, n):
        return CollProxy(self._d[n], self._h) if n.startswith('tejas_') else getattr(self._d, n)


class TestApplyConcurrency:
    def test_partial_crash_then_resume_idempotent(self, db):
        seed(db); store = FakeStore(); exp = expected_ids(db, True); original = canon_all(db)
        receipt = do_prepare(db, store); calls = []

        def crash(name):
            calls.append(name)
            if len(calls) == 4:
                raise ConnectionError('simulated crash')
        with pytest.raises(ConnectionError):
            do_apply(DBProxy(db, {'delete': crash}), store, receipt)
        assert db[R.RECEIPTS].find_one({'_id': receipt['_id']})['phase'] == 'applying'
        assert db.tejas_sessions.count_documents({'_qa': {'$exists': True}}) == 0  # sessions removed first
        done = do_apply(db, store, receipt)
        assert done['phase'] == 'complete'
        after = canon_all(db)
        for name, docs in original.items():
            if name != 'tejas_cohorts':
                assert after.get(name, {}) == {k: v for k, v in docs.items() if k not in exp.get(name, set())}, name

    def test_cas_lost_race_refuses(self, db):
        seed(db); store = FakeStore(); receipt = do_prepare(db, store); before = canon_all(db)

        def rival():
            db[R.RECEIPTS].update_one({'_id': receipt['_id']}, {'$set': {'phase': 'applying', 'protected_sha256': 'rival'}})
        with pytest.raises(RuntimeError, match='Another reset process'):
            do_apply(DBProxy(db, {'cas': rival}), store, receipt)
        assert canon_all(db) == before

    def test_non_target_mutation_during_apply_detected(self, db):
        seed(db); store = FakeStore(); receipt = do_prepare(db, store); fired = []

        def mutate(name):
            if not fired:
                fired.append(1); db.tejas_sets.update_one({'id': 'qa144-set'}, {'$set': {'title': 'tampered'}})
        with pytest.raises(RuntimeError, match='verification failed'):
            do_apply(DBProxy(db, {'delete': mutate}), store, receipt)
        row = db[R.RECEIPTS].find_one({'_id': receipt['_id']})
        assert row['phase'] == 'applying'
        with pytest.raises(RuntimeError, match='Protected data changed'):
            do_apply(db, store, receipt)

    def test_protected_change_between_prepare_and_resume_blocks(self, db):
        seed(db); store = FakeStore(); receipt = do_prepare(db, store)
        db[R.RECEIPTS].update_one({'_id': receipt['_id']}, {'$set': {'phase': 'applying', 'protected_sha256': R.protected_fingerprint(db, R.build_plan(db, True))}})
        db.tejas_attempts.update_one({'id': 'qa144-att-own'}, {'$set': {'answers.q9': 'D'}})
        before = canon_all(db)
        with pytest.raises(RuntimeError, match='Protected data changed'):
            do_apply(db, store, receipt)
        assert canon_all(db) == before


# ---------------------------------------------------------------- CLI operational wiring (fake tejas_storage + fake client -> isolated DB)
def test_cli_storage_imports_match_real_signatures():
    import inspect
    import tejas_storage
    src = (BACKEND / 'tools' / 'reset_student_data.py').read_text()
    names = re.search(r'from tejas_storage import ([\w, ]+)', src).group(1).replace(' ', '').split(',')
    assert sorted(names) == ['put_object', 'request'], names  # no upload(), no cached get_object()
    assert all(hasattr(tejas_storage, n) for n in names)
    assert list(inspect.signature(tejas_storage.put_object).parameters)[:3] == ['path', 'data', 'content_type']
    assert list(inspect.signature(tejas_storage.request).parameters)[:2] == ['method', 'path']
    assert 'get_object' not in src


class _CliClient:
    def __init__(self, real):
        self.real, self.names, self.closed = real, [], 0

    def __getitem__(self, name):
        self.names.append(name)
        return self.real[TEST_DB]

    def close(self):
        self.closed += 1


def test_cli_adapter_wiring_prepare_and_apply(client, db, monkeypatch, capsys):
    seed(db)
    objects, calls, missing = {}, [], set()
    fake = types.ModuleType('tejas_storage')

    def put_object(path, data, content_type='application/pdf'):
        calls.append(('PUT', path, content_type)); objects[path] = bytes(data)
        return path  # real put_object returns the stored path STRING

    class Resp:
        def __init__(self, content):
            self.content = content

    def request(method, path, data=None, content_type=None):
        calls.append((method, path, content_type))
        if path in missing:
            raise RuntimeError('Private storage unavailable (404).')  # real StorageError analogue
        return Resp(objects[path])
    fake.put_object, fake.request = put_object, request
    monkeypatch.setitem(sys.modules, 'tejas_storage', fake)
    cc, urls = _CliClient(client), []
    monkeypatch.setattr(R, 'MongoClient', lambda url, *a, **k: (urls.append(url), cc)[1])
    monkeypatch.setenv('ADMIN_EMAIL', OWNER_EMAIL)
    monkeypatch.setattr(sys, 'argv', ['reset_student_data.py', 'prepare', '--writers-paused', '--include-unlinked'])
    R.main()
    out = capsys.readouterr().out.strip().splitlines()[-1]
    pub = json.loads(out)
    assert urls == [os.environ['MONGO_URL']] and cc.names == [os.environ['DB_NAME']] and cc.closed == 1
    assert pub['phase'] == 'prepared' and pub['private_backup_verified'] is True and pub['students'] == 4
    assert '@' not in out and '+91' not in out and 'student-reset-backups' not in out and 'path' not in pub
    puts = [c for c in calls if c[0] == 'PUT']
    assert puts and all(c[2] == 'application/gzip' for c in puts)
    pat = re.compile(r'^tejas/student-reset-backups/' + re.escape(OWNER) + r'/[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[0-9a-f]{4}-[0-9a-f]{12}\.jsonl\.gz$')
    assert all(pat.match(c[1]) for c in puts) and len({c[1] for c in puts}) == len(puts)
    for i, c in enumerate(calls):  # every PUT is immediately read back via uncached GET of the same path
        if c[0] == 'PUT':
            assert calls[i + 1][:2] == ('GET', c[1])
    receipt = db[R.RECEIPTS].find_one({'_id': pub['reset_id']})
    assert receipt['binding'] == hashlib.sha256((os.environ['MONGO_URL'] + '\0' + os.environ['DB_NAME']).encode()).hexdigest()
    assert receipt['manifest']['path'] in objects and not receipt['manifest']['path'].startswith('http')
    manifest = R.verified_manifest(receipt, lambda p: objects[p])
    # a 404 on any private part during apply fails closed (nothing deleted)
    before = canon_all(db)
    missing.add(manifest['parts'][0]['path'])
    monkeypatch.setattr(sys, 'argv', ['reset_student_data.py', 'apply', '--writers-paused', '--reset-id', pub['reset_id'], '--approval-hash', pub['approval_hash']])
    with pytest.raises(RuntimeError, match='404'):
        R.main()
    assert_nothing_deleted(db, before, 'prepared', pub['reset_id'])
    missing.clear(); calls.clear()
    R.main()
    done = json.loads(capsys.readouterr().out.strip().splitlines()[-1])
    assert done['phase'] == 'complete' and done['owner_and_papers_retained'] is True
    assert [c for c in calls if c[0] == 'PUT'] == []  # apply never writes storage
    got = {c[1] for c in calls if c[0] == 'GET'}
    assert receipt['manifest']['path'] in got and {p['path'] for p in manifest['parts']} <= got
    assert db.tejas_users.count_documents({'role': 'student'}) == 0 and db.tejas_users.count_documents({'id': OWNER}) == 1
    assert db.tejas_sets.count_documents({'id': 'qa144-set'}) == 1 and cc.closed == 3


# ---------------------------------------------------------------- ex-gaps (now ordinary tests)
def raw_rows(d, name, query):
    coll = d.get_collection(name, codec_options=d.codec_options.with_options(document_class=RawBSONDocument))
    return sorted(r.raw for r in coll.find(query))


class TestScopeProtection:
    def test_owner_row_sharing_orphan_attempt_id_is_protected(self, db):
        seed(db)
        db.tejas_reviews.insert_one({'id': 'own-review-gone', 'user_id': OWNER, 'attempt_id': 'qa144-shared-gone'})
        db.tejas_score_versions.insert_one({'id': 'anon-sv-gone', 'attempt_id': 'qa144-shared-gone'})
        store = FakeStore(); do_apply(db, store, do_prepare(db, store))
        assert db.tejas_reviews.count_documents({'id': 'own-review-gone'}) == 1
        assert db.tejas_score_versions.count_documents({'id': 'anon-sv-gone'}) == 0

    def test_all_staff_and_phone_staff_rows_sharing_orphan_id_byte_identical(self, db):
        seed(db)
        db.tejas_phone_profiles.insert_one({'id': 'qa144-ph-staff', 'role': 'reviewer', 'phone': '+910000144555'})
        sh = 'qa144-shared-gone'
        keep = {'tejas_reviews': [{'id': 'kr1', 'user_id': OWNER, 'attempt_id': sh, 'z': 1, 'a': 2}],
                'tejas_ledgers': [{'id': sh, 'user_id': OWNER, 'rows': [{'id': 'q1'}]}, {'id': 'kl2', 'user_id': 'qa144-admin', 'attempt_id': sh}],
                'tejas_jobs': [{'id': 'kj1', 'kind': 'grade', 'user_id': OWNER, 'payload': {'attempt_id': sh}},
                               {'id': 'kj2', 'kind': 'report', 'user_id': 'qa144-reviewer', 'payload': {'attempt_id': sh}},
                               {'id': 'kj3', 'kind': 'cohort', 'user_id': 'qa144-ph-staff', 'payload': {'attempt_id': sh}}],
                'tejas_cohort_entries': [{'cohort_id': 'C9', 'user_id': OWNER, 'attempt_id': sh}],
                'tejas_question_reports': [{'id': 'kq1', 'user_id': 'qa144-ph-staff', 'attempt_id': sh}],
                'tejas_score_versions': [{'id': 'ks1', 'user_id': 'qa144-ph-staff', 'attempt_id': sh}],
                'tejas_sessions': [{'id': 'kss', 'user_id': 'qa144-ph-staff', 'attempt_id': sh}]}
        for n, rows in keep.items():
            db[n].insert_many([{**r, '_keep': 1} for r in rows])
        db.tejas_score_versions.insert_one({'id': 'anon-sv', 'attempt_id': sh})
        db.tejas_jobs.insert_one({'id': 'anon-job', 'kind': 'grade', 'payload': {'attempt_id': sh}})
        before = {n: raw_rows(db, n, {'_keep': 1}) for n in keep}
        staff_before = {n: raw_rows(db, n, {'role': {'$ne': 'student'}}) for n in ('tejas_users', 'tejas_phone_profiles')}
        plan = R.build_plan(db, True)
        assert sh in plan['attempt_ids'] and 'qa144-ph-staff' not in plan['user_ids']
        store = FakeStore(); assert do_apply(db, store, do_prepare(db, store))['phase'] == 'complete'
        assert {n: raw_rows(db, n, {'_keep': 1}) for n in keep} == before
        assert {n: raw_rows(db, n, {'role': {'$ne': 'student'}}) for n in staff_before} == staff_before
        assert db.tejas_score_versions.count_documents({'id': 'anon-sv'}) == 0 and db.tejas_jobs.count_documents({'id': 'anon-job'}) == 0

    def test_unlinked_personal_jobs_captured_shared_ai_retained(self, db):
        seed(db)
        store = FakeStore(); do_apply(db, store, do_prepare(db, store))
        assert db.tejas_jobs.count_documents({'id': {'$in': ['j-jobonly-report', 'j-old-grade']}}) == 0
        assert db.tejas_jobs.count_documents({'id': {'$in': ['j-anon-ai', 'j-su1-ai', 'j-own', 'j-own-cohort']}}) == 4

    def test_legacy_phone_profile_without_role_is_not_targeted(self, db):
        seed(db); db.tejas_phone_profiles.insert_one({'id': 'qa144-legacy', 'phone': '+910000144077'})
        db.tejas_sessions.insert_one({'id': 'legacy-sess', 'user_id': 'qa144-legacy'})
        store = FakeStore(); do_apply(db, store, do_prepare(db, store))
        assert db.tejas_phone_profiles.count_documents({'id': 'qa144-legacy'}) == 1
        assert db.tejas_sessions.count_documents({'id': 'legacy-sess'}) == 1


class TestManifestIntegrity:
    def test_manifest_records_indexes(self, db):
        seed(db); store = FakeStore(); receipt = do_prepare(db, store)
        m = R.verified_manifest(receipt, store.fetch)
        assert 'indexes' not in m and all('indexes' not in p for p in m['parts'])
        names = {n for n in db.list_collection_names() if n != R.RECEIPTS and not n.startswith('system.')}
        assert set(m['collections']) == names and EMPTY in names
        for n, meta in m['collections'].items():
            assert set(meta) == {'options', 'type', 'indexes', 'records', 'sha256'}, n
            assert meta['type'] == 'collection' and meta['records'] == db[n].count_documents({})
            h = hashlib.sha256()
            for row in db[n].find({}).sort('_id', 1):
                h.update(R.backup_encoded(row) + b'\n')
            assert meta['sha256'] == h.hexdigest(), n
            assert sum(p['records'] for p in m['parts'] if p['collection'] == n) == meta['records']
            assert [i['name'] for i in meta['indexes']] == [i['name'] for i in db[n].list_indexes()]
        e = m['collections'][EMPTY]
        assert e['records'] == 0 and e['sha256'] == hashlib.sha256(b'').hexdigest()
        assert e['options']['validationLevel'] == 'moderate' and 'validator' in e['options']
        ix = {i['name']: i for i in e['indexes']}
        assert list(ix['empty_cmp']['key'].items()) == [('k', -1), ('a', 1)] and ix['empty_cmp']['unique'] is True
        sx = {i['name']: i for i in m['collections']['tejas_sessions']['indexes']}
        assert list(sx['uid_id_desc']['key'].items()) == [('user_id', 1), ('id', -1)] and sx['ttl_exp']['expireAfterSeconds'] == 10 * 365 * 86400
        assert {i['name']: i for i in m['collections']['tejas_users']['indexes']}['email_1']['unique'] is True
        assert receipt['parts_hash'] == R.digest(m['parts']) and receipt['collections_hash'] == R.record_digest(m['collections'])
        assert receipt['plan_hash'] == R.digest(m['plan']) and receipt['counts'] == {n: len(r) for n, r in m['plan']['records'].items()}
        for p in m['parts']:
            assert hashlib.sha256(store.objects[p['path']]).hexdigest() == p['sha256'] and p['bytes'] == len(store.objects[p['path']])

    @pytest.mark.parametrize('case', ['drop_part_reapproved', 'drop_part_rehashed', 'drop_part_and_meta_rehashed', 'target_digest_wrong',
                                      'target_missing_from_part', 'duplicate_part', 'collection_count_wrong', 'collection_sha_wrong'])
    def test_manifest_missing_part_for_targets_blocks(self, db, case):
        seed(db); store = FakeStore(); receipt = do_prepare(db, store); before = canon_all(db)
        A = 'tejas_attempts'

        def mut(m):
            ap = [p for p in m['parts'] if p['collection'] == A]
            if case.startswith('drop_part'):
                m['parts'] = [p for p in m['parts'] if p['collection'] != A]
                if case == 'drop_part_and_meta_rehashed':
                    del m['collections'][A]
            elif case == 'target_digest_wrong':
                m['plan']['records'][A][0]['sha256'] = '0' * 64
            elif case == 'target_missing_from_part':
                target = R.backup_encoded(m['plan']['records'][A][0]['_id'])
                lines = [ln for ln in gzip.decompress(store.objects[ap[0]['path']]).splitlines()
                         if R.backup_encoded(json_util.loads(ln)['_id']) != target]
                body = b''.join(ln + b'\n' for ln in lines); blob = gzip.compress(body, mtime=0)
                path = f'qa144/forged/{uuid.uuid4()}'; store.objects[path] = blob
                ap[0].update({'path': path, 'sha256': hashlib.sha256(blob).hexdigest(), 'bytes': len(blob), 'records': len(lines)})
                m['collections'][A].update({'records': len(lines), 'sha256': hashlib.sha256(body).hexdigest()})
            elif case == 'duplicate_part':
                m['parts'].append(dict(ap[0]))
            elif case == 'collection_count_wrong':
                m['collections'][A]['records'] += 1
            elif case == 'collection_sha_wrong':
                m['collections'][A]['sha256'] = '0' * 64
        approval = rewrite_manifest(db, store, receipt, mut, rehash_receipt=case != 'drop_part_reapproved')
        with pytest.raises(RuntimeError):
            do_apply(db, store, receipt, approval)
        assert_nothing_deleted(db, before, 'prepared', receipt['_id'])


# ---------------------------------------------------------------- DB-clock 300s lease
def set_lease(d, rid, offset, token='dead-token', **extra):
    clock = {'$divide': [{'$toLong': '$$NOW'}, 1000]}
    d[R.RECEIPTS].update_one({'_id': rid}, [{'$set': {'lease': token, 'lease_until': {'$add': [clock, offset]}, **extra}}])


def crash_to_applying(db, store, receipt, at=2):
    calls = []

    def crash(name):
        calls.append(name)
        if len(calls) == at:
            raise ConnectionError('simulated crash')
    with pytest.raises(ConnectionError):
        do_apply(DBProxy(db, {'delete': crash}), store, receipt)
    assert db[R.RECEIPTS].find_one({'_id': receipt['_id']})['phase'] == 'applying'


def expected_after(db_original, exp):
    return {n: {k: v for k, v in docs.items() if k not in exp.get(n, set())} for n, docs in db_original.items() if n != 'tejas_cohorts'}


class TestApplyLease:
    def test_handled_failure_releases_lease_immediate_resume(self, db):
        seed(db); store = FakeStore(); receipt = do_prepare(db, store)
        crash_to_applying(db, store, receipt)
        row = db[R.RECEIPTS].find_one({'_id': receipt['_id']})
        assert row['lease_until'] == 0 and 'lease' not in row
        assert do_apply(db, store, receipt)['phase'] == 'complete'

    @pytest.mark.parametrize('phase', ['prepared', 'applying'])
    def test_crashed_future_lease_blocks_until_expiry(self, db, phase):
        seed(db); store = FakeStore(); receipt = do_prepare(db, store)
        if phase == 'applying':
            crash_to_applying(db, store, receipt)
        set_lease(db, receipt['_id'], 300)
        before = canon_all(db)
        with pytest.raises(RuntimeError, match='Another reset process'):
            do_apply(db, store, receipt)
        assert_nothing_deleted(db, before, phase, receipt['_id'])
        assert db[R.RECEIPTS].find_one({'_id': receipt['_id']})['lease'] == 'dead-token'
        set_lease(db, receipt['_id'], 290)  # still in future -> still blocked
        with pytest.raises(RuntimeError, match='Another reset process'):
            do_apply(db, store, receipt)
        assert canon_all(db) == before
        set_lease(db, receipt['_id'], -1)  # expired on DB clock
        assert do_apply(db, store, receipt)['phase'] == 'complete'
        row = db[R.RECEIPTS].find_one({'_id': receipt['_id']})
        assert 'lease' not in row and row['lease_until'] == 0

    @pytest.mark.parametrize('phase', ['prepared', 'applying'])
    def test_nested_rival_resumer_blocked_and_lease_not_refreshed(self, db, phase):
        seed(db); store = FakeStore(); exp = expected_ids(db, True); original = canon_all(db)
        receipt = do_prepare(db, store)
        if phase == 'applying':
            crash_to_applying(db, store, receipt)
        rival_errors, rival_deletes, leases = [], [], []

        def hook(name):
            row = db[R.RECEIPTS].find_one({'_id': receipt['_id']})
            leases.append((row['lease'], row['lease_until']))
            if len(leases) == 1:
                try:
                    do_apply(DBProxy(db, {'delete': rival_deletes.append}), store, receipt)
                except RuntimeError as e:
                    rival_errors.append(str(e))
        done = do_apply(DBProxy(db, {'delete': hook}), store, receipt)
        assert done['phase'] == 'complete' and rival_deletes == [] and len(rival_errors) == 1 and 'Another reset process' in rival_errors[0]
        assert len(leases) > 1 and len(set(leases)) == 1  # same token, same deadline: never refreshed
        after = canon_all(db)
        assert {n: after.get(n, {}) for n in expected_after(original, exp)} == expected_after(original, exp)

    @pytest.mark.parametrize('phase', ['prepared', 'applying'])
    def test_threaded_parallel_resumers_single_writer(self, db, phase):
        seed(db); store = FakeStore(); exp = expected_ids(db, True); original = canon_all(db)
        receipt = do_prepare(db, store)
        if phase == 'applying':
            crash_to_applying(db, store, receipt)
        barrier, results = threading.Barrier(4), []

        def worker(i):
            dels = []
            barrier.wait()
            try:
                r = do_apply(DBProxy(db, {'delete': dels.append}), store, receipt)
                results.append(('ok', r['phase'], len(dels)))
            except RuntimeError as e:
                results.append(('err', str(e), len(dels)))
        ts = [threading.Thread(target=worker, args=(i,)) for i in range(4)]
        [t.start() for t in ts]; [t.join(60) for t in ts]
        assert len(results) == 4
        writers = [r for r in results if r[2] > 0]
        assert len(writers) == 1 and writers[0][:2] == ('ok', 'complete'), results
        for r in results:
            if r is not writers[0]:
                assert r == ('ok', 'complete', 0) or (r[0] == 'err' and 'Another reset process' in r[1] and r[2] == 0), results
        after = canon_all(db)
        assert {n: after.get(n, {}) for n in expected_after(original, exp)} == expected_after(original, exp)

    @pytest.mark.parametrize('how', ['expire', 'steal'])
    def test_lease_lost_mid_apply_stops_next_batch(self, db, how):
        seed(db); store = FakeStore(); receipt = do_prepare(db, store); calls = []

        def hook(name):
            calls.append(name)
            if len(calls) == 1:
                if how == 'expire':
                    db[R.RECEIPTS].update_one({'_id': receipt['_id']}, {'$set': {'lease_until': 0}})
                else:
                    set_lease(db, receipt['_id'], 300, token='thief')
        with pytest.raises(RuntimeError, match='lease expired'):
            do_apply(DBProxy(db, {'delete': hook}), store, receipt)
        assert len(calls) == 1
        row = db[R.RECEIPTS].find_one({'_id': receipt['_id']})
        assert row['phase'] == 'applying'
        if how == 'steal':  # foreign holder's lease untouched by our finally
            assert row['lease'] == 'thief' and row['lease_until'] > 0
            set_lease(db, receipt['_id'], -1, token='thief')
        assert do_apply(db, store, receipt)['phase'] == 'complete'

    def test_lease_expired_before_final_check(self, db):
        seed(db); store = FakeStore(); receipt = do_prepare(db, store)
        total = sum(1 for v in receipt['counts'].values() if v); calls = []

        def hook(name):
            calls.append(name)
            if len(calls) == total:
                db[R.RECEIPTS].update_one({'_id': receipt['_id']}, {'$set': {'lease_until': 0}})
        with pytest.raises(RuntimeError, match='before final verification'):
            do_apply(DBProxy(db, {'delete': hook}), store, receipt)
        assert len(calls) == total
        assert db.tejas_cohorts.count_documents({'dirty': True}) == 0  # finalization not performed
        assert do_apply(db, store, receipt)['phase'] == 'complete'

    @pytest.mark.parametrize('case', ['cancelled_no_hash', 'restored_with_valid_hash', 'aborted_with_valid_hash', 'cas_rival_lease'])
    def test_foreign_phase_or_lost_cas_fails_before_deletion(self, db, case):
        seed(db); store = FakeStore(); receipt = do_prepare(db, store)
        good = R.protected_fingerprint(db, R.build_plan(db, True)); before = canon_all(db); hooks = {}
        if case == 'cancelled_no_hash':
            db[R.RECEIPTS].update_one({'_id': receipt['_id']}, {'$set': {'phase': 'cancelled'}})
        elif case in ('restored_with_valid_hash', 'aborted_with_valid_hash'):
            db[R.RECEIPTS].update_one({'_id': receipt['_id']}, {'$set': {'phase': case.split('_')[0], 'protected_sha256': good}})
        else:
            hooks['cas'] = lambda: set_lease(db, receipt['_id'], 300, token='rival', phase='applying')
        with pytest.raises(RuntimeError):
            do_apply(DBProxy(db, hooks), store, receipt)
        assert canon_all(db) == before
