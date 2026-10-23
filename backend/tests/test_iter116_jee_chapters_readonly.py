"""Iteration 116: READ-ONLY post-publication verification of the 78 JEE Main chapter sets on the REAL customer DB.
No writes: only find/count/aggregate. The actual catalogue function (exam_navigation.catalogue) is invoked in-process
with a synthetic read-only principal (no login, no session). The real DB snapshot (counts/hash) is written to
/tmp/iter116_realdb_snapshot.json so a later run can prove nothing changed.
Run: cd /app/backend && python -m pytest tests/test_iter116_jee_chapters_readonly.py -p no:asyncio -n0 -v
"""
import asyncio, hashlib, json, os, sys
from pathlib import Path
import pytest
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from dotenv import load_dotenv
load_dotenv(Path(__file__).resolve().parents[1] / '.env')
from pymongo import MongoClient

DB = MongoClient(os.environ['MONGO_URL'])[os.environ['DB_NAME']]
MANIFEST = json.loads(Path('/app/data/jee_chapters/import_manifest.json').read_text())
EXPECT = {'Physics': (29, 90), 'Mathematics': (26, 120), 'Chemistry': (23, 70)}
LOOP = asyncio.new_event_loop(); asyncio.set_event_loop(LOOP); run = LOOP.run_until_complete
JEE = list(DB.tejas_sets.find({'exam': 'JEE Main', 'chapter_book_id': {'$exists': True}}, {'_id': 0}))
PRINCIPAL = {'id': 'TEST_READONLY_PRINCIPAL_116', 'role': 'student', 'phone': '9900000199', 'access_type': 'unverified_phone'}


def snapshot():
    bits = list(DB.tejas_sets.find({'exam': 'BITSAT'}, {'_id': 0}).sort('id', 1))
    h = hashlib.sha256(json.dumps(bits, sort_keys=True, default=str).encode()).hexdigest()
    jee = list(DB.tejas_sets.find({'exam': 'JEE Main'}, {'_id': 0}).sort('id', 1))
    hj = hashlib.sha256(json.dumps(jee, sort_keys=True, default=str).encode()).hexdigest()
    new_ids = [s['id'] for s in jee]
    return {'bitsat_sets': len(bits), 'bitsat_hash': h, 'jee_hash': hj, 'jee_sets': len(jee),
            'attempts': DB.tejas_attempts.count_documents({}), 'sessions': DB.tejas_sessions.count_documents({}),
            'users': DB.tejas_users.count_documents({}), 'files': DB.tejas_files.count_documents({}),
            'jee_attempts': DB.tejas_attempts.count_documents({'set_id': {'$in': new_ids}}),
            'jee_jobs': DB.tejas_jobs.count_documents({'$or': [{'set_id': {'$in': new_ids}}, {'payload.set_id': {'$in': new_ids}}]}),
            'jee_ai_solutions': DB.tejas_ai_solutions.count_documents({'set_id': {'$in': new_ids}}),
            'jee_solution_requests': DB.tejas_solution_requests.count_documents({'set_id': {'$in': new_ids}}),
            'jee_manual_solves': DB.tejas_manual_solves.count_documents({'set_id': {'$in': new_ids}}),
            'question_solutions': DB.tejas_question_solutions.count_documents({})}


def test_snapshot_written():
    snap = snapshot()
    p = Path('/tmp/iter116_realdb_snapshot.json')
    prev = json.loads(p.read_text()) if p.exists() else None
    p.write_text(json.dumps(snap))
    print('SNAPSHOT', snap, 'PREV', prev)
    assert snap['bitsat_sets'] == 144
    assert snap['jee_attempts'] == 0 and snap['jee_jobs'] == 0 and snap['jee_ai_solutions'] == 0
    if prev:
        for k in ('bitsat_hash', 'jee_hash', 'attempts', 'sessions', 'users', 'files', 'question_solutions'):
            assert prev[k] == snap[k], k


def test_counts_per_subject():
    assert len(JEE) == 78
    by = {}
    for s in JEE:
        by.setdefault(s['chapter_subject'], []).append(s)
    for subj, (n, minutes) in EXPECT.items():
        assert len(by[subj]) == n, subj
        assert sorted(s['chapter_number'] for s in by[subj]) == list(range(1, n + 1))
        assert sum(len(s['questions']) for s in by[subj]) == n * 50
        for s in by[subj]:
            r = s['rules']
            assert (r['minutes'], r['correct'], r['wrong'], r['skipped']) == (minutes, 4, -1, 0), s['id']
    assert sum(len(s['questions']) for s in JEE) == 3900


def test_publication_state_and_proof():
    for s in JEE:
        assert s['status'] == 'published' and s['live_enabled'] is True and s['test_kind'] == 'chapter'
        assert s['solution_kind'] == 'supplied_worked'
        assert s.get('series_id') is None and not s.get('series_import') and not s.get('qa_only')
        assert s['audience'] == 'all'
        assert abs((s['end_at'] - s['start_at']) - 365 * 86400) < 1
        ic = s['independent_check']; assert ic and ic['keys_checked'] == 50 and ic['solutions_checked'] == 50
        assert s['verification']['key_checks_agree'] and s['verification']['solution_keys_agree']
        assert not s['title'].lower().startswith(('chapter ', 'test ', 'untitled'))
        for q in s['questions']:
            assert q['approved'] is True and not q['issues']
            assert q['q_refs'] and q['s_refs'] and q['answer'] not in (None, '')
            assert q['type'] in ('mcq', 'integer')
            if q['type'] == 'mcq':
                assert set(q['options']) == {'A', 'B', 'C', 'D'} and q['answer'] in 'ABCD'


def test_manifest_matches_db():
    ids = {s['id']: s for s in JEE}
    for b in MANIFEST['books']:
        book = DB.tejas_chapter_books.find_one({'id': b['id']}, {'_id': 0})
        assert book['source']['sha256'] == b['source_sha256'] and book['exam'] == 'JEE Main'
        assert book['minutes'] == EXPECT[b['subject']][1]
        assert book.get('requested_by_email') == 'abhishekpushp07@gmail.com'
        for c in b['chapters']:
            s = ids[c['set_id']]
            assert s['title'] == c['title'] and s['chapter_number'] == c['number']
            f = DB.tejas_files.find_one({'id': c['source_file_id']}, {'_id': 0})
            assert f['sha256'] == c['source_sha256'] and s['file_ids'] == [f['id']]


def test_catalogue_function_inprocess_readonly():
    from tejas import exam_navigation as N
    seen, counts = [], None
    for subj, (n, _) in EXPECT.items():
        r = run(N.catalogue('jee-main', kind='chapters', subject=subj, q='', page=1, user=PRINCIPAL))
        assert r.total == n and r.pages == (n + 11) // 12, subj
        counts = r.subject_counts
    assert counts == {'Chemistry': 23, 'Mathematics': 26, 'Physics': 29}
    r = run(N.catalogue('jee-main', kind='chapters', subject='', q='', page=1, user=PRINCIPAL))
    assert r.total == 78 and r.pages == 7
    for p in range(1, 8):
        rows = run(N.catalogue('jee-main', kind='chapters', subject='', q='', page=p, user=PRINCIPAL)).items
        seen += [i['id'] for i in rows]
    assert len(seen) == 78 and len(set(seen)) == 78 and set(seen) == {s['id'] for s in JEE}
    s = run(N.catalogue('jee-main', kind='chapters', subject='', q='Mole', page=1, user=PRINCIPAL))
    assert any(i['title'] == 'Mole Concept' for i in s.items)
    # mocks / BITSAT must not surface new sets
    m = run(N.catalogue('jee-main', kind='mocks', subject='', q='', page=1, user=PRINCIPAL))
    assert not ({i['id'] for i in m.items} & set(seen))
    b = run(N.catalogue('bitsat', kind='chapters', subject='', q='', page=1, user=PRINCIPAL))
    bm = run(N.catalogue('bitsat', kind='mocks', subject='', q='', page=1, user=PRINCIPAL))
    assert not ({i['id'] for i in b.items + bm.items} & set(seen))
    print('BITSAT chapters total', b.total, 'BITSAT mocks total', bm.total, 'JEE mocks', m.total)


def test_summary_hides_keys():
    from tejas import exam_navigation as N
    r = run(N.catalogue('jee-main', kind='chapters', subject='Chemistry', q='', page=1, user=PRINCIPAL))
    blob = json.dumps(r.model_dump(), default=str)
    assert '"answer"' not in blob and '10-mark solution' not in blob and 's_refs' not in blob


def test_bitsat_legacy_chapter_catalogue_excludes_jee():
    from tejas import chapter_books as C
    r = run(C.exam_catalogue('', '', 1, None))
    ids = {s['id'] for s in JEE}
    assert not ({i['id'] for i in r.items} & ids)
    print('legacy /api/chapter-exams total', r.total, r.subject_counts)
