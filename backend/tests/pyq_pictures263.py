"""TEST-ONLY iteration 263: PYQ pictures when storage cannot give the source PDF back, and an empty picture part.
(a) a PYQ original is read from its kept copy in the repository when storage fails, only if its fingerprint matches;
(b) a part (public link or private pack) in which not one picture could be read answers 503 vault_unavailable, never cached.
Isolated disposable DB (storage in memory, AI mocked). Run: cd /app/backend && bash /root/p2/solo.sh python -u tests/pyq_pictures263.py
"""
import asyncio, hashlib, json, shutil, sys, tempfile, time
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import media_four_qa216 as C  # noqa: E402  (imports the harness first: rebinds DB, storage in memory; 4-option paper)
from media_four_qa216 import H, mkstaff, check, RESULTS, J, go, student, unpack, structure, paper  # noqa: E402
from tejas import media as MEDIA, derivatives as D  # noqa: E402
import tejas_storage as S  # noqa: E402

COPIES = Path('/app/data/jee_pyq/source_audit')
DRIVE = '1-0YnLVIrzU-vARvQ_KNEWilYFai1wRsr'  # '22 jan shift 1 of 2025.pdf', a real kept original
REF = {'file_id': 'jee-pyq-source-1ca9b573decd04c6d188d37b', 'page': 1, 'rect': [20.825, 167.873, 297.5, 227.968]}
REF2 = {'file_id': REF['file_id'], 'page': 2, 'rect': [20.825, 167.873, 297.5, 227.968]}


def code(r):
    try:
        return ((json.loads(r.text) or {}).get('error') or {}).get('code')
    except ValueError:
        return None


def forget():
    D._cache.data.clear(); D._cache.size = 0; D._away.clear()
    S._source_cache.data.clear(); S._source_cache.size = 0


def source():
    sha = hashlib.sha256((COPIES / f'{DRIVE}.pdf').read_bytes()).hexdigest()
    return {'id': REF['file_id'], 'path': f'tejas/jee-pyq/originals/{sha}.pdf', 'sha256': sha, 'source_collection': 'jee-pyq-written',
            'source_drive_id': DRIVE, 'role': 'source', 'media_type': 'application/pdf'}


def units():
    src = source()
    check('kept copy is in the repository folder the code reads', D.PYQ_COPIES == COPIES and (COPIES / f'{DRIVE}.pdf').is_file(), str(D.PYQ_COPIES))
    check('storage does not hold the original (the fault)', src['path'] not in H.STORE, '')
    forget(); calls = {'n': 0}; real_get = S.get_object

    def counted(path):
        calls['n'] += 1
        return real_get(path)
    S.get_object = counted
    try:
        png = D.render_crop(src, REF)
        check('storage fails -> the picture is cut from the kept copy (PNG)', png[:8] == b'\x89PNG\r\n\x1a\n' and len(png) > 1000, len(png))
        check('storage was asked once first', calls['n'] == 1, calls)
        png2 = D.render_crop(src, REF2)
        check('next picture of the same paper: storage not asked again for 30 min', png2[:8] == b'\x89PNG\r\n\x1a\n' and calls['n'] == 1, calls)
        D._away[src['path']] = time.time() - 1801; D._cache.data.clear(); D._cache.size = 0
        D.render_crop(src, REF)
        check('after 30 min storage is asked again', calls['n'] == 2, calls)
    finally:
        S.get_object = real_get
    tmp = Path(tempfile.mkdtemp(prefix='TEST_pyq263_'))
    old = D.PYQ_COPIES
    try:
        (tmp / f'{DRIVE}.pdf').write_bytes(b'%PDF-1.4 TEST not the original')
        D.PYQ_COPIES = tmp; forget()
        try:
            D.render_crop(src, REF); ok = False
        except S.StorageError:
            ok = True
        check('kept copy that differs from the record -> refused (StorageError, no picture)', ok, '')
        (tmp / f'{DRIVE}.pdf').unlink(); forget()
        try:
            D.render_crop(src, REF); ok = False
        except S.StorageError:
            ok = True
        check('no kept copy -> the storage error as before', ok, '')
    finally:
        D.PYQ_COPIES = old; shutil.rmtree(tmp, ignore_errors=True)
    other = {**src, 'source_collection': 'book', 'id': 'TEST_other'}; forget()
    try:
        D.render_crop(other, REF); ok = False
    except S.StorageError:
        ok = True
    check('a source that is not a PYQ original never uses a kept copy', ok, '')
    forget(); H.STORE[src['path']] = (COPIES / f'{DRIVE}.pdf').read_bytes(); D.PYQ_COPIES = tmp
    try:
        png = D.render_crop(src, REF)
        check('storage works -> storage bytes used, kept copy never read', png[:8] == b'\x89PNG\r\n\x1a\n' and not D._away, '')
    finally:
        D.PYQ_COPIES = old; H.STORE.pop(src['path'], None); forget()


async def empty_parts(own, stu):
    sid = await paper(own, stu)
    if not sid: return
    x = J(await go(stu, sid)); aid = x['id']
    parts = J(await stu.get(f'/api/attempts/{aid}/assets/links')).get('parts') or []
    check('paper has picture parts', bool(parts), '')
    if not parts: return
    anon = C.client(); MEDIA._parts.data.clear(); MEDIA._parts.size = 0
    orig = MEDIA.render_crop

    def broken(src, ref): raise S.StorageError('TEST storage away')
    MEDIA.render_crop = broken
    try:
        r = await anon.get(parts[0]); cc = r.headers.get('cache-control', '')
        check('part with NO picture readable -> 503 vault_unavailable (not an empty 200)', r.status_code == 503 and code(r) == 'vault_unavailable', (r.status_code, r.text[:200]))
        check('that 503 is never cached (no-store, not public) and says Retry-After', 'no-store' in cc and not cc.startswith('public') and r.headers.get('retry-after'), (cc, r.headers.get('retry-after')))
        rs = await asyncio.gather(*(anon.get(parts[0]) for _ in range(8)))
        check('8 at once on that part -> all 503, nothing kept in memory', all(x.status_code == 503 for x in rs) and not MEDIA._parts.data, [x.status_code for x in rs])
        r = await stu.get(f'/api/attempts/{aid}/assets/pack', params={'offset': 0, 'limit': 12})
        check('private pack with NO picture readable -> 503 vault_unavailable, no-store', r.status_code == 503 and code(r) == 'vault_unavailable' and 'no-store' in r.headers.get('cache-control', ''), (r.status_code, r.text[:200]))
        r = await stu.get(f'/api/attempts/{aid}/assets/pack', params={'offset': 5000, 'limit': 12})
        check('private pack past the last picture -> still an empty 200 (nothing was asked)', r.status_code == 200 and unpack(r.content)[0]['items'] == [], (r.status_code, r.text[:120]))
    finally:
        MEDIA.render_crop = orig
    r = await anon.get(parts[0]); cc = r.headers.get('cache-control', '')
    check('storage back -> the same link 200, complete, public again', r.status_code == 200 and cc.startswith('public') and unpack(r.content)[0]['items'], cc)
    r = await stu.get(f'/api/attempts/{aid}/assets/pack', params={'offset': 0, 'limit': 12})
    check('storage back -> private pack 200 with pictures', r.status_code == 200 and unpack(r.content)[0]['items'], r.status_code)


async def main():
    own, _ = await mkstaff('owner', 'c263'); a = await student('63')
    await structure.exams.update_one({'_id': 'jee-main'}, {'$set': {'shown': True}})
    units()
    try: await empty_parts(own, a)
    except Exception:
        import traceback; traceback.print_exc(); check('section ran', False, 'exception above')


async def run():
    assert not H.leftover_real_handles()
    await H.tdbmod.indexes(); await structure.seed()
    try: await main()
    finally:
        await H.tdbmod.client.drop_database(H.TEST_DB)
        for r in RESULTS: print('PASS' if r[1] else 'FAIL', r[0], '' if r[1] else r[2])
        ok = sum(1 for r in RESULTS if r[1]); print(f'TOTAL {len(RESULTS)} PASS {ok} FAIL {len(RESULTS) - ok}'); print('dropped', H.TEST_DB)

if __name__ == '__main__':
    asyncio.run(run())
