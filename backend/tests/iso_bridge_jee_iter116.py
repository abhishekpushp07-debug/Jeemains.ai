"""TEST-ONLY ISOLATED bridge (iteration 116) for JEE Main chapter practice. NOT production evidence.
Copies ONLY the 78 published JEE chapter sets + their 3 books + 78 file records (read-only find on the real DB) into
dedicated DB `tejas_isolated_iter105_test` (dropped by tester after use). Env MONGO_URL/DB_NAME unchanged.
Storage: put_object is an in-memory mock; object-store HTTP is GET-only (real customer PDFs are read, never written).
Auth: X-Test-User header -> synthetic users student/other/owner (TEST-ONLY MOCKED auth). Port 8765, lifespan off.
Run: cd /app/backend/tests && python iso_bridge_jee_iter116.py &
"""
import asyncio, os, sys
import uvicorn
import iso_harness as H
import tejas_storage

MEM = {}


def mem_put(path, data, content_type='application/pdf'):
    MEM[path] = data
    return path


_real_request = tejas_storage.request


def guarded_request(method, path, data=None, content_type=None):
    if method != 'GET':
        raise RuntimeError(f'TEST GUARD: storage {method} blocked for {path}')
    if path in MEM:
        class _R: content = MEM[path]
        return _R()
    return _real_request(method, path, data, content_type)


tejas_storage.request = guarded_request
tejas_storage.put_object = mem_put
for name, mod in list(sys.modules.items()):
    if mod is not None and (name == 'server' or name.startswith('tejas')) and getattr(mod, 'put_object', None) is not None and name != 'tejas_storage':
        setattr(mod, 'put_object', mem_put)

from pymongo import MongoClient  # noqa: E402
REAL = MongoClient(os.environ['MONGO_URL'])[H.REAL_DB]


async def seed():
    assert H.TEST_DB != H.REAL_DB and not H.leftover_real_handles(), H.leftover_real_handles()
    await H.tdbmod.client.drop_database(H.TEST_DB)
    await H.tdbmod.indexes()
    sets = list(REAL.tejas_sets.find({'exam': 'JEE Main', 'chapter_book_id': {'$exists': True}, 'status': 'published'}, {'_id': 0}))
    book_ids = sorted({s['chapter_book_id'] for s in sets})
    file_ids = sorted({f for s in sets for f in s['file_ids']})
    books = list(REAL.tejas_chapter_books.find({'id': {'$in': book_ids}}, {'_id': 0}))
    files = list(REAL.tejas_files.find({'id': {'$in': file_ids}}, {'_id': 0}))
    await H.TDB.tejas_sets.insert_many(sets)
    await H.TDB.tejas_chapter_books.insert_many(books)
    await H.TDB.tejas_files.insert_many(files)
    H.USERS.update({
        'student': {'id': 'TEST_U116_student', 'role': 'student', 'name': 'TEST Student 116', 'phone': '9900000161', 'access_type': 'unverified_phone', 'exam': 'JEE Main'},
        'other': {'id': 'TEST_U116_other', 'role': 'student', 'name': 'TEST Other 116', 'phone': '9900000162', 'access_type': 'unverified_phone', 'exam': 'JEE Main'},
        'owner': {'id': 'TEST_U116_owner', 'role': 'owner', 'name': 'TEST Owner 116', 'email': 'test-owner-116@example.invalid', 'access_type': 'password'},
    })
    print('SEED116', len(sets), len(books), len(files), flush=True)


if __name__ == '__main__':
    asyncio.set_event_loop(asyncio.new_event_loop())
    loop = asyncio.get_event_loop()
    loop.run_until_complete(seed())
    loop.run_until_complete(uvicorn.Server(uvicorn.Config(H.app, host='127.0.0.1', port=8765, log_level='warning', lifespan='off')).serve())
