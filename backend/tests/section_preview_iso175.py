"""TEST-ONLY iteration 175: shareable section preview link (owner create/rotate/revoke + public read-only preview).
Isolated disposable DB via iso_harness_book170 (storage + AI mocked). Customer DB never written.
Run: cd /app/backend && python tests/section_preview_iso175.py   (prints PASS/FAIL, drops its DB)
"""
import asyncio, hashlib, json, re, sys, time, uuid
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import book_publishing_iso170 as T  # noqa: E402  (imports harness first)
from book_publishing_iso170 import H, mkstaff, client, build_pdf, q3, upload, complete, drain, check, RESULTS  # noqa: E402
from structure_iso173 import mkset  # noqa: E402
from tejas import structure  # noqa: E402

PV = H.TDB.tejas_section_previews
SEC = 'bitsat:mocks'
ITEM_KEYS = {'title', 'state', 'count', 'minutes', 'subject', 'start_at', 'book'}


def link(sid): return f'/api/admin/catalog/sections/{sid}/preview-link'


async def main():
    check('no customer DB handles', not H.leftover_real_handles(), H.leftover_real_handles())
    check('previews collection patched', structure.previews.database.name == H.TEST_DB, structure.previews.database.name)
    await structure.seed()
    own, oid = await mkstaff('owner', 'own175')
    rev, _ = await mkstaff('reviewer', 'rev175')
    stu = client(); r = await stu.post('/api/auth/phone/signup', json={'phone': '94' + str(uuid.uuid4().int)[:8], 'pin': '4826', 'confirm_pin': '4826'})
    check('student signup', r.status_code in (200, 201), (r.status_code, r.text[:150]))
    anon = client()

    # ---- auth on owner endpoints
    for m in ('get', 'post', 'delete'):
        r = await getattr(anon, m)(link(SEC)); check(f'anon {m} preview-link 401', r.status_code == 401, r.status_code)
        r = await getattr(rev, m)(link(SEC)); check(f'reviewer {m} preview-link 403', r.status_code == 403, r.status_code)
        r = await getattr(stu, m)(link(SEC)); check(f'student {m} preview-link 403', r.status_code == 403, r.status_code)
        r = await getattr(own, m)(link('nope:none')); check(f'owner {m} unknown section 404', r.status_code == 404, r.status_code)
    r = await own.get(link(SEC))
    check('status no link -> active false, expires null', r.status_code == 200 and r.json() == {'active': False, 'expires_at': None}, (r.status_code, r.text))

    # ---- seed tests in bitsat:mocks (all non-live states + live)
    fut = time.time() + 86400
    live = await mkset('LIVE', exam='BITSAT', catalog_section_id=SEC, catalog_order=1, count=3)
    await mkset('DRAFT', exam='BITSAT', catalog_section_id=SEC, catalog_order=2, status='draft')
    await mkset('PAUSED', exam='BITSAT', catalog_section_id=SEC, catalog_order=3, live_enabled=False)
    await mkset('UNLIVE', exam='BITSAT', catalog_section_id=SEC, catalog_order=4, owner_unlive=True)
    sched = await mkset('SCHED', exam='BITSAT', catalog_section_id=SEC, catalog_order=5, start_at=fut)
    await mkset('OTHER', exam='BITSAT', catalog_section_id='bitsat:chapters', catalog_order=1)
    # waiting combined-book mocks
    mk = lambda tag: [{'n': 1, 'qs': q3(tag + '1'), 'keys': [(1, 'B'), (2, 'B'), (3, 'C')]}, {'n': 2, 'qs': q3(tag + '2'), 'keys': [(1, 'B'), (2, 'B'), (3, 'C')]}]
    ba = await upload(own, build_pdf(mk('PA')), 'TEST_QA175 BookA', section_id=SEC)
    _, va = await complete(own, ba['id'])
    await asyncio.sleep(0.05)
    bb = await upload(own, build_pdf(mk('PB')), 'TEST_QA175 BookB', section_id=SEC)
    _, vb = await complete(own, bb['id'])
    check('both books ready 2 mocks', [m['state'] for m in va['mocks']] == ['ready', 'ready'] and [m['state'] for m in vb['mocks']] == ['ready', 'ready'],
          ([m['state'] for m in va['mocks']], [m['state'] for m in vb['mocks']]))
    am = {m['label']: m['id'] for m in va['mocks']}; bm = {m['label']: m['id'] for m in vb['mocks']}
    BM = H.TDB.tejas_book_mocks
    await BM.update_one({'_id': am['Mock 2']}, {'$set': {'state': 'held'}})
    await BM.update_one({'_id': bm['Mock 1']}, {'$set': {'publish_requested': True, 'release_at': fut}})
    await BM.update_one({'_id': bm['Mock 2']}, {'$set': {'publish_requested': True, 'release_at': None}})
    sample = await BM.find_one({'_id': am['Mock 1']})
    print('book mock sample keys', sorted(sample.keys()), 'set_id', sample.get('set_id'))

    # ---- create link
    t0 = time.time()
    r = await own.post(link(SEC)); d = r.json() if r.status_code == 200 else {}
    tok = d.get('token', '')
    check('POST create 200 token+expires', r.status_code == 200 and set(d) == {'token', 'expires_at'}, (r.status_code, r.text[:200]))
    check('token 32 url-safe chars', len(tok) == 32 and re.fullmatch(r'[A-Za-z0-9_-]+', tok) is not None, tok and len(tok))
    check('expires ~7 days', abs(d.get('expires_at', 0) - (t0 + 7 * 86400)) < 300, d.get('expires_at', 0) - t0)
    docs = await PV.find({'section_id': SEC}).to_list(10)
    check('DB stores sha256 as _id', len(docs) == 1 and docs[0]['_id'] == hashlib.sha256(tok.encode()).hexdigest(), [x['_id'] for x in docs])
    check('raw token not stored anywhere in previews', tok not in json.dumps(docs, default=str))
    au = await H.TDB.tejas_audits.find_one({'resource': SEC, 'action': {'$regex': 'preview link created'}})
    check('audit entry for create', bool(au) and au.get('actor') == oid, au)
    r = await own.get(link(SEC)); s = r.json()
    check('status active true + expires', s.get('active') is True and s.get('expires_at') == d.get('expires_at'), s)

    # ---- public preview
    r = await anon.get(f'/api/preview/sections/{tok}'); p = r.json() if r.status_code == 200 else {}
    check('public preview 200 without login', r.status_code == 200, (r.status_code, r.text[:200]))
    check('top-level keys', set(p) <= {'exam', 'section', 'items', 'live_count', 'expires_at', 'server_now'} and {'exam', 'section', 'items', 'live_count', 'expires_at'} <= set(p), sorted(p))
    check('exam fields', p.get('exam') == {'name': 'BITSAT', 'short': 'BITS', 'color': 'bitsat', 'shown': True}, p.get('exam'))
    check('section fields', set(p.get('section', {})) == {'name', 'description', 'layout', 'hidden'} and p['section']['layout'] == 'list' and p['section']['hidden'] is False, p.get('section'))
    items = p.get('items', [])
    check('item keys exact', all(set(i) == ITEM_KEYS for i in items), [sorted(i) for i in items][:2])
    got = [(i['title'], i['state']) for i in items]
    print('preview items', got)
    exp_sets = [('TEST_LIVE', 'live'), ('TEST_DRAFT', 'draft'), ('TEST_PAUSED', 'paused'), ('TEST_UNLIVE', 'unlive'), ('TEST_SCHED', 'scheduled')]
    check('tests in catalog_order with states', got[:5] == exp_sets, got[:5])
    check('waiting mocks after tests: ready, held, scheduled, publishing', [x[1] for x in got[5:]] == ['ready', 'held', 'scheduled', 'publishing'] and len(got) == 9, got[5:])
    check('other-section test not included', 'TEST_OTHER' not in [x[0] for x in got])
    check('live_count 1', p.get('live_count') == 1, p.get('live_count'))
    check('scheduled test start_at', items[4]['start_at'] == fut if len(items) > 4 else False)
    check('waiting scheduled mock start_at == release_at', len(items) > 7 and items[7]['start_at'] == fut and items[8]['start_at'] is None, items[7:] if len(items) > 7 else items)
    check('waiting mock count == 3 questions & minutes', len(items) > 5 and items[5]['count'] == 3, items[5] if len(items) > 5 else None)
    blob = r.text
    leaks = [w for w in (live, sched, 'TEST_S173_', 'answer', 'solution', 'LIVE q0', 'PA1', '"id"', 'book_id', 'set_id', tok, hashlib.sha256(tok.encode()).hexdigest()) if w in blob]
    check('no question content / ids / answers / token leaked', not leaks, leaks)
    r = await stu.get(f'/api/preview/sections/{tok}'); check('public preview works for logged-in student too', r.status_code == 200, r.status_code)

    # ---- rotation
    r = await own.post(link(SEC)); tok2 = r.json().get('token')
    check('rotate gives different token', r.status_code == 200 and tok2 and tok2 != tok)
    r = await anon.get(f'/api/preview/sections/{tok}'); check('old token 404 after rotate', r.status_code == 404, r.status_code)
    r = await anon.get(f'/api/preview/sections/{tok2}'); check('new token 200', r.status_code == 200, r.status_code)
    check('only one active row after rotate', await PV.count_documents({'section_id': SEC, 'revoked': False}) == 1)

    # ---- revoke
    r = await own.delete(link(SEC)); check('DELETE 200 inactive', r.status_code == 200 and r.json() == {'active': False, 'expires_at': None}, r.text)
    r = await anon.get(f'/api/preview/sections/{tok2}')
    check('revoked token 404 with message', r.status_code == 404 and 'expired or was turned off' in r.text, (r.status_code, r.text))
    r = await own.delete(link(SEC)); check('DELETE idempotent 200', r.status_code == 200, r.status_code)
    check('one turn-off audit (idempotent second delete no audit)', await H.TDB.tejas_audits.count_documents({'resource': SEC, 'action': {'$regex': 'turned off'}}) == 1)
    r = await own.get(link(SEC)); check('status after revoke inactive', r.json() == {'active': False, 'expires_at': None}, r.text)

    # ---- expired
    r = await own.post(link(SEC)); tok3 = r.json()['token']
    await PV.update_one({'_id': hashlib.sha256(tok3.encode()).hexdigest()}, {'$set': {'expires_at': time.time() - 10}})
    r = await anon.get(f'/api/preview/sections/{tok3}'); check('expired token 404', r.status_code == 404, r.status_code)
    r = await own.get(link(SEC)); check('status for expired link active false', r.json().get('active') is False, r.text)

    # ---- malformed
    for bad in ('abc', 'a' * 19, 'a' * 65, 'a' * 200, 'a' * 25 + '%21', 'a' * 25 + '.x', '%00' * 10 + 'a' * 20, 'a' * 32, '..%2F..%2Fetc%2Fpasswd' + 'a' * 10, "'%3B--" + 'a' * 25):
        r = await anon.get(f'/api/preview/sections/{bad}')
        check(f'malformed {bad[:12]}.. -> 404/422 not 500', r.status_code in (404, 422), r.status_code)

    # ---- hidden custom exam (chapters) + hidden section
    r = await own.post('/api/admin/catalog/exams', json={'name': 'TEST Hidden175', 'short': 'TH175', 'subjects': ['Physics', 'Chemistry'], 'color': 'teal'})
    slug = r.json()['slug']; key = (await H.TDB.tejas_catalog_exams.find_one({'_id': slug}))['key']
    ch = (await own.post(f'/api/admin/catalog/exams/{slug}/sections', json={'name': 'TEST Chaps175', 'layout': 'chapters'})).json()['id']
    await mkset('C1', exam=key, catalog_section_id=ch, catalog_order=1, chapter_subject='Physics', chapter_number=1, test_kind='chapter')
    await mkset('C2', exam=key, catalog_section_id=ch, catalog_order=2, chapter_subject='Chemistry', chapter_number=1, test_kind='chapter')
    r = await own.post(link(ch)); ht = r.json()['token']
    r = await anon.get(f'/api/preview/sections/{ht}'); p = r.json()
    check('hidden exam preview 200 shown=false', r.status_code == 200 and p['exam']['shown'] is False and p['section']['layout'] == 'chapters', (r.status_code, r.text[:200]))
    check('chapter items carry subject', [i['subject'] for i in p.get('items', [])] == ['Physics', 'Chemistry'], p.get('items'))
    r = await own.patch(f'/api/admin/catalog/sections/{ch}', json={'hidden': True}); check('hide section 200', r.status_code == 200, r.text[:150])
    r = await anon.get(f'/api/preview/sections/{ht}'); check('hidden section preview hidden=true', r.status_code == 200 and r.json()['section']['hidden'] is True, r.text[:200])
    r = await stu.get(f'/api/catalog/exams/{slug}'); check('student cannot open hidden exam (404)', r.status_code == 404, r.status_code)
    r = await stu.get('/api/catalog/exams'); check('hidden exam not in student list', slug not in json.dumps(r.json()), r.status_code)
    r = await anon.get(f'/api/catalog/exams/{slug}'); check('anon cannot open hidden exam', r.status_code in (401, 404), r.status_code)

    # ---- removed book's waiting mocks excluded
    await H.TDB.tejas_books.update_one({'_id': bb['id']}, {'$set': {'removed': True}})
    r = await own.post(link(SEC)); t4 = r.json()['token']
    r = await anon.get(f'/api/preview/sections/{t4}')
    check('removed book mocks excluded', [i['state'] for i in r.json()['items']][5:] == ['ready', 'held'], [i['state'] for i in r.json()['items']])
    await own.delete(link(SEC)); await own.delete(link(ch))


async def run():
    try:
        await main()
    except Exception as e:
        import traceback; traceback.print_exc(); check('completed without exception', False, repr(e))
    finally:
        await H.tdbmod.client.drop_database(H.TEST_DB)
        print('dropped', H.TEST_DB)
        f = [r for r in RESULTS if not r[1]]
        print(f'TOTAL {len(RESULTS)} PASS {len(RESULTS) - len(f)} FAIL {len(f)}')
        for x in f: print('  FAILED', x[0], '::', x[2])

if __name__ == '__main__':
    asyncio.run(run())
