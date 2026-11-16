"""TEST-ONLY iteration 186 retest: Library delete not partial with ids+uploads (active attempt pre-check),
series paper_live 404 for sets with series_id but no series_date / archived.
Isolated disposable DB via iso_harness_book170. Run: cd /app/backend && timeout 200 python tests/retest_iso186.py
"""
import asyncio, sys, time, uuid
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import book_publishing_iso170 as T  # noqa: E402,F401
from book_publishing_iso170 import H, mkstaff, client, check, RESULTS  # noqa: E402
from structure_iso173 import mkset  # noqa: E402
from tejas import structure, live_series  # noqa: E402
from typed_delete_iso185 import J, M  # noqa: E402

DB = H.TDB
SETS = DB.tejas_sets
L = '/api/admin/library'


async def mixed_delete(own):
    # ids test (archived, no attempts) + upload whose Library test has an active attempt
    x = await mkset('MIXID', exam='JEE Main', catalog_section_id='jee-main:mocks', test_kind='mock', archived=True)
    await DB.tejas_imports.insert_one({'id': 'imp-186', 'title': 'TEST imp186', 'archived': True, 'destination': {}})
    u = await mkset('MIXUP', exam='JEE Main', test_kind='mock', import_id='imp-186', archived=True)
    act = 'TEST_act186_' + uuid.uuid4().hex[:6]
    await DB.tejas_attempts.insert_one({'id': act, 'set_id': u, 'user_id': 'x', 'start_key': act, 'status': 'active', 'deadline': time.time() + 3600, 'title': 'x'})
    r = await own.post(L + '/delete', json={'ids': [x], 'uploads': [{'kind': 'import', 'id': 'imp-186'}], 'confirm': 'DELETE'})
    check('mixed ids+upload with active attempt -> 409 still writing', r.status_code == 409 and 'still writing a test made from this upload' in r.text, (r.status_code, r.text[:200]))
    check('mixed 409: body.ids test NOT deleted', await SETS.find_one({'id': x}) is not None)
    check('mixed 409: upload + its test NOT deleted', await DB.tejas_imports.find_one({'id': 'imp-186'}) and await SETS.find_one({'id': u}))
    check('mixed 409: attempt not marked set_deleted', not (await DB.tejas_attempts.find_one({'id': act})).get('set_deleted'))
    # deadline 0 (untimed active) also blocks
    await DB.tejas_attempts.update_one({'id': act}, {'$set': {'deadline': 0}})
    r = await own.post(L + '/delete', json={'ids': [x], 'uploads': [{'kind': 'import', 'id': 'imp-186'}], 'confirm': 'DELETE'})
    check('deadline 0 active attempt also blocks, nothing deleted', r.status_code == 409 and await SETS.find_one({'id': x}), (r.status_code, r.text[:150]))
    # expired -> full delete
    await DB.tejas_attempts.update_one({'id': act}, {'$set': {'deadline': time.time() - 5}})
    r = await own.post(L + '/delete', json={'ids': [x], 'uploads': [{'kind': 'import', 'id': 'imp-186'}], 'confirm': 'DELETE'}); d = J(r)
    check('after expiry mixed delete 200 removes both', r.status_code == 200 and not await SETS.find_one({'id': x}) and not await SETS.find_one({'id': u}) and not await DB.tejas_imports.find_one({'id': 'imp-186'}), (r.status_code, r.text[:200]))
    check('mixed delete counts', d.get('deleted') == 1 and d.get('uploads') == 1, d)
    check('expired attempt kept with set_deleted', (await DB.tejas_attempts.find_one({'id': act}) or {}).get('set_deleted'))
    # ids active attempt + valid upload -> 409, upload untouched
    y = await mkset('MIXY', exam='JEE Main', catalog_section_id='jee-main:mocks', test_kind='mock', archived=True)
    await DB.tejas_imports.insert_one({'id': 'imp-186b', 'title': 'TEST imp186b', 'archived': True, 'destination': {}})
    ub = await mkset('MIXUB', exam='JEE Main', test_kind='mock', import_id='imp-186b', archived=True)
    await DB.tejas_attempts.insert_one({'id': act + 'y', 'set_id': y, 'user_id': 'y', 'start_key': act + 'y', 'status': 'active', 'deadline': time.time() + 3600, 'title': 'y'})
    r = await own.post(L + '/delete', json={'ids': [y], 'uploads': [{'kind': 'import', 'id': 'imp-186b'}], 'confirm': 'DELETE'})
    check('ids active attempt + upload -> 409, upload kept', r.status_code == 409 and await DB.tejas_imports.find_one({'id': 'imp-186b'}) and await SETS.find_one({'id': ub}) and await SETS.find_one({'id': y}), (r.status_code, r.text[:150]))


async def series_live(own):
    sid = live_series.SERIES_ID
    url = f'{M}/series/{sid}/live'
    nodate = await mkset('NODATE', exam='JEE Main', series_id=sid, test_kind='mock')
    r = await own.post(url, json={'id': nodate, 'live': False}); check('series_id without series_date -> 404', r.status_code == 404, (r.status_code, r.text[:150]))
    check('no-date set unchanged', not (await SETS.find_one({'id': nodate})).get('owner_unlive'))
    empty = await mkset('EMPTYD', exam='JEE Main', series_id=sid, series_date='', test_kind='mock')
    r = await own.post(url, json={'id': empty, 'live': False}); check('series_date empty string -> 404', r.status_code == 404, r.status_code)
    arch = await mkset('ARCHD', exam='JEE Main', series_id=sid, series_date='2026-12-03', test_kind='mock', archived=True)
    r = await own.post(url, json={'id': arch, 'live': False}); check('archived day set -> 404', r.status_code == 404, (r.status_code, r.text[:150]))
    check('archived set unchanged', not (await SETS.find_one({'id': arch})).get('owner_unlive'))
    ok = await mkset('OKDAY', exam='JEE Main', series_id=sid, series_date='2026-12-04', test_kind='mock')
    r = await own.post(url, json={'id': ok, 'live': False}); check('valid day set Off 200', r.status_code == 200 and (await SETS.find_one({'id': ok})).get('owner_unlive'), (r.status_code, r.text[:150]))
    r = await own.post(url, json={'id': ok, 'live': True}); check('valid day set Live 200', r.status_code == 200 and not (await SETS.find_one({'id': ok})).get('owner_unlive'), r.status_code)


async def main():
    check('no customer DB handles', not H.leftover_real_handles(), H.leftover_real_handles())
    await H.tdbmod.indexes(); await structure.seed()
    own, _ = await mkstaff('owner', 'r186')
    try:
        for name, coro in (('mixed', mixed_delete(own)), ('series', series_live(own))):
            try: await coro
            except Exception as e: import traceback; traceback.print_exc(); check(f'{name} block crashed', False, repr(e))
    finally:
        await H.tdbmod.client.drop_database(H.TEST_DB)
        print('dropped', H.TEST_DB)
    failed = [r for r in RESULTS if not r[1]]
    print(f'\nTOTAL {len(RESULTS)} PASS {len(RESULTS) - len(failed)} FAIL {len(failed)}')
    sys.exit(1 if failed else 0)

if __name__ == '__main__':
    asyncio.run(main())
