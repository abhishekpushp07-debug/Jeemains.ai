"""TEST-ONLY iteration 238, Packet E step 1: the proof that every picture of a paper exists, all in one store (tejas/picture_proof.py).
The function alone, wired to nothing yet. Disposable DB, Supabase faked at the wire (tests/fake_supabase229.py), Emergent in memory.
The proof only reads: the last check asserts that nothing was saved or removed in either store.
Run: cd /app/backend && python tests/picture_proof238.py
"""
import asyncio, hashlib, os, sys, time, types, uuid
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from storage_book229 import H, DB, S, RESULTS, check  # noqa: E402
import httpx  # noqa: E402
from fake_supabase229 import FakeSupabase  # noqa: E402
from tejas import picture_proof as PP  # noqa: E402

LIST, READ = '/storage/v1/object/list/', '/storage/v1/object/authenticated/'
EM = []   # every call to Emergent storage
SB = None


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def ref(fid, **kw):
    return {'file_id': fid, 'page': 1, 'rect': [0, 0, 1, 1], 'prerendered': True, **kw}


def crops():
    return f'jeelive/books/{uuid.uuid4()}/crops'


async def picture(where, folder, sized=True, bucket=None):
    fid, raw = str(uuid.uuid4()), b'\x89PNG\r\n\x1a\n' + os.urandom(300)
    inner = f'{folder}/{fid}.png'
    if where == 'supabase':
        bucket = bucket or S.bucket_name()
        SB.objects[f'{bucket}/{inner}'] = raw
        path = f'{S.SB}{bucket}/{inner}'
    else:
        H.STORE[inner] = raw
        path = inner
    await DB.tejas_files.insert_one({'id': fid, 'path': path, 'kind': 'rendered_png', 'sha256': sha(raw), **({'size': len(raw)} if sized else {})})
    return fid


async def paper(where, folder=None, n=3, **kw):
    """n questions, each with a question picture, a solution picture and two cut pieces (the new look), all in one store."""
    folder, qs = folder or crops(), []
    for i in range(n):
        q, s, c1, c2 = [await picture(where, folder, **kw) for _ in range(4)]
        qs.append({'id': str(uuid.uuid4()), 'number': i + 1, 'q_refs': [ref(q)], 's_refs': [ref(s)], 'c_refs': [ref(c1, part='question'), ref(c2, part='A')]})
    return {'id': str(uuid.uuid4()), 'test_kind': 'mock', 'questions': qs}


async def stored(fid):
    """The store's own box and key of one picture, so a test can take it away or change it."""
    path = (await DB.tejas_files.find_one({'id': fid}))['path']
    return (SB.objects, path[len(S.SB):]) if path.startswith(S.SB) else (H.STORE, path)


async def paths(s):
    ids = [r['file_id'] for q in s['questions'] for k in ('q_refs', 's_refs', 'c_refs') for r in q[k]]
    return sorted([f['path'] async for f in DB.tejas_files.find({'id': {'$in': ids}}, {'path': 1})])


def since(n, part):
    return sum(1 for _, _, p in SB.calls[n:] if part in p)


def other(raw):
    return raw[:-1] + bytes([raw[-1] ^ 1])   # the same size, one bit changed


async def main():
    global SB
    assert not H.leftover_real_handles()
    SB = FakeSupabase(S.TUS_CHUNK)
    client = httpx.Client(transport=httpx.MockTransport(SB))
    S._client = lambda: client                                               # nothing leaves this process
    S.time = types.SimpleNamespace(time=time.time, sleep=lambda s: None)     # the storage code's own waits only
    S.STATE.update(down_until=0.0, strikes=0, last_error='', auth=None, bucket=None, failovers=0, last_failover=None, backup_since=None)
    real = S.request

    def logged(method, path, data=None, content_type=None):
        EM.append((method, path))
        return real(method, path, data, content_type)
    S.request = logged
    try:
        # ---- A. A Supabase paper with every picture in place.
        s = await paper('supabase'); n = len(SB.calls)
        r = await PP.prove(s)
        check('A. Supabase paper: all 12 pictures are proven, in Supabase', r['ok'] and r['store'] == 'supabase' and r['total'] == 12 and r['proven'] == 12
              and r['stores'] == {'supabase': 12, 'emergent': 0} and not r['bad'] and r['reason'] == '' and r['full'] is False, r)
        check("A. ...by one look at Supabase's own list of the folder; no picture is downloaded, Emergent is not asked", since(n, LIST) == 1 and since(n, READ) == 0 and not EM, (SB.calls[n:], EM))

        # ---- B. Pictures that are not in Supabase although their records exist. The first one is an option piece (c_refs).
        piece = s['questions'][1]['c_refs'][1]['file_id']; box, k = await stored(piece); kept = {k: box.pop(k)}
        r = await PP.prove(s)
        check('B. one option piece is gone from Supabase: the paper is not proven and names it', not r['ok'] and r['bad'] == {piece: 'missing'} and r['proven'] == 11 and r['total'] == 12
              and r['reason'] == '1 picture storage me nahi mili', r)
        two = [s['questions'][0]['q_refs'][0]['file_id'], s['questions'][2]['s_refs'][0]['file_id']]
        for fid in two:
            box, k = await stored(fid); kept[k] = box.pop(k)
        r = await PP.prove(s)
        check('B. three gone (a question picture, a solution picture, a piece): "3 pictures storage me nahi mili"', not r['ok'] and r['bad'] == {fid: 'missing' for fid in [piece] + two}
              and r['proven'] == 9 and r['reason'] == '3 pictures storage me nahi mili', r)
        SB.objects.update(kept)
        check('B. the pictures are back: proven again', (await PP.prove(s))['ok'])

        # ---- C. Supabase holds another number of bytes than were saved.
        fid = s['questions'][0]['q_refs'][0]['file_id']; box, k = await stored(fid); whole = box[k]; box[k] = whole[:-1]
        r = await PP.prove(s)
        check('C. a picture stored one byte short: caught by its size, without downloading it', not r['ok'] and r['bad'] == {fid: 'size'}
              and r['reason'] == '1 picture storage me badli hui mili (size ya fingerprint alag)', r)
        box[k] = whole
        old = await paper('supabase', sized=False)
        fid2 = old['questions'][0]['q_refs'][0]['file_id']; box2, k2 = await stored(fid2); whole2 = box2[k2]; box2[k2] = whole2[:-1]
        quick, full = await PP.prove(old), await PP.prove(old, full=True)
        check('C. an older record has no size: the quick proof sees only that the picture is there; the full check catches it', quick['ok'] and not full['ok'] and full['bad'] == {fid2: 'bytes'}, (quick, full))
        box2[k2] = whole2

        # ---- D. The full check reads every picture back and compares its fingerprint.
        n = len(SB.calls)
        r = await PP.prove(s, full=True)
        check('D. full check of a healthy paper: every picture is read back once and matches', r['ok'] and r['full'] is True and r['proven'] == 12 and since(n, READ) == 12 and since(n, LIST) == 1, (r, since(n, READ)))
        box[k] = other(whole)
        quick, full = await PP.prove(s), await PP.prove(s, full=True)
        check('D. other bytes of the same size: the quick proof cannot see it, the full check does', quick['ok'] and not full['ok'] and full['bad'] == {fid: 'bytes'}
              and full['reason'] == '1 picture storage me badli hui mili (size ya fingerprint alag)', (quick, full))
        box[k] = whole

        # ---- F. One picture used by two questions is one picture.
        twice = await paper('supabase', n=2); twice['questions'][1]['q_refs'] = twice['questions'][0]['q_refs']
        r = await PP.prove(twice)
        check('F. a picture used by two questions is counted once', r['ok'] and r['total'] == 7 and r['proven'] == 7, r)

        # ---- G. An Emergent paper: Emergent has no list, so every picture is read back and its fingerprint compared.
        e = await paper('emergent'); n, m = len(SB.calls), len(EM)
        r = await PP.prove(e)
        check('G. Emergent paper: all 12 pictures are read back (each once) and match; Supabase is not asked', r['ok'] and r['store'] == 'emergent' and r['total'] == 12 and r['proven'] == 12
              and r['stores'] == {'supabase': 0, 'emergent': 12} and len(SB.calls) == n and sorted(EM[m:]) == [('GET', p) for p in await paths(e)], (r, len(EM) - m))
        fid = e['questions'][0]['q_refs'][0]['file_id']; box, k = await stored(fid); whole = box[k]
        S.get_object(k)   # this server now remembers the picture
        del box[k]
        r = await PP.prove(e)
        check("G. a picture gone from Emergent is caught although this server still remembers it (the proof never reads from memory)", not r['ok'] and r['bad'] == {fid: 'unread'}
              and r['reason'] == '1 picture storage se wapas padhi nahi ja saki', r)
        box[k] = other(whole)
        r = await PP.prove(e)
        check('G. other bytes in Emergent: caught by the fingerprint', not r['ok'] and r['bad'] == {fid: 'bytes'}, r)
        box[k] = whole
        check('G. the picture is back: proven again', (await PP.prove(e))['ok'])

        # ---- H. One mock, one storage: a paper split between the stores is never proven, even when every picture exists.
        a, b = await paper('supabase', n=1), await paper('emergent', n=1)
        r = await PP.prove({'id': 'split', 'test_kind': 'mock', 'questions': a['questions'] + b['questions']})
        check('H. pictures split between Supabase and Emergent: not proven, both counts named', not r['ok'] and r['store'] == 'mixed' and r['stores'] == {'supabase': 4, 'emergent': 4} and not r['bad']
              and r['proven'] == 8 and r['reason'] == 'Pictures do storage me bati hain (4 Supabase me, 4 Emergent me)', r)

        # ---- I. A picture whose record is gone.
        lost = await paper('supabase', n=1); fid = lost['questions'][0]['s_refs'][0]['file_id']
        await DB.tejas_files.delete_one({'id': fid})
        r = await PP.prove(lost)
        check('I. a picture without its record: not proven, counted as not found', not r['ok'] and r['bad'] == {fid: 'record'} and r['reason'] == '1 picture storage me nahi mili', r)

        # ---- J. Verified JEE Main PYQ is never checked.
        pyq = {**(await paper('supabase', n=1)), 'test_kind': 'pyq'}; n, m = len(SB.calls), len(EM)
        r, rf = await PP.prove(pyq), await PP.prove(pyq, full=True)
        check('J. a verified JEE Main PYQ paper: no proof and not one storage call', r is None and rf is None and len(SB.calls) == n and len(EM) == m, (r, rf))
        r = await PP.prove({**pyq, 'master_pyq': True})
        check('J. a PYQ paper the owner made in Master is checked like any other', r and r['ok'] and r['total'] == 4, r)

        # ---- K. A paper without pictures.
        n, m = len(SB.calls), len(EM)
        r = await PP.prove({'id': 'typed', 'test_kind': 'mock', 'questions': [{'id': 'x', 'number': 1, 'q_refs': [], 's_refs': []}]})
        r2 = await PP.prove({'id': 'empty', 'test_kind': 'mock'})
        check('K. a typed paper has no pictures: proven with 0 of 0, no storage call', r['ok'] and r['total'] == 0 and r['store'] == '' and r2['ok'] and r2['total'] == 0 and len(SB.calls) == n and len(EM) == m, (r, r2))

        # ---- L. Supabase itself cannot answer: nothing can be said, so no picture is called missing.
        got = []
        for knob, value in (('down', True), ('block', (402, 'quota exceeded'))):
            setattr(SB, knob, value)
            try:
                got.append(await PP.prove(s))
            except S.StorageError as exc:
                got.append(exc)
            setattr(SB, knob, False if knob == 'down' else None)
        check("L. Supabase away (503) or the project blocked (402): the proof raises Supabase's own trouble with its code", [isinstance(x, S.StorageError) and x.code for x in got] == [503, 402], got)
        check('L. ...and the proof itself never rests Supabase for everyone', S.supabase_on() and S.STATE['strikes'] == 0, S.STATE)
        check('L. Supabase answers again: the same paper is proven', (await PP.prove(s))['ok'])

        # ---- M. A folder with more than 1000 files (a big book): the list is read to its end.
        folder = crops()
        for i in range(1005):
            SB.objects[f'{S.bucket_name()}/{folder}/!filler-{i:04d}.bin'] = b'x'
        big = await paper('supabase', folder=folder, n=1); n = len(SB.calls)
        r = await PP.prove(big)
        check('M. pictures on the second page of a 1009-file folder are found (two list calls)', r['ok'] and r['total'] == 4 and since(n, LIST) == 2, (r, since(n, LIST)))

        # ---- N. Pictures in two folders of the same store.
        a, b = await paper('supabase', n=1), await paper('supabase', n=1); n = len(SB.calls)
        r = await PP.prove({'id': 'two', 'test_kind': 'mock', 'questions': a['questions'] + b['questions']})
        check('N. two folders: each is listed once and the paper is proven in Supabase', r['ok'] and r['store'] == 'supabase' and r['total'] == 8 and since(n, LIST) == 2, (r, since(n, LIST)))

        # ---- O. A picture names its own bucket; that bucket is the one asked.
        ob = await paper('supabase', n=1, bucket='jeelive-an-older-bucket'); n = len(SB.calls)
        r = await PP.prove(ob)
        check("O. pictures in another bucket of the project are looked up in their own bucket", r['ok'] and [p for _, _, p in SB.calls[n:]] == [LIST + 'jeelive-an-older-bucket'], (r, SB.calls[n:]))

        # ---- P. The proof only reads.
        wrote = [(m, p) for m, _, p in SB.calls if m in ('PUT', 'PATCH', 'DELETE') or (m == 'POST' and LIST not in p)]
        check('P. in all of the above nothing was saved or removed in Supabase or in Emergent', not wrote and all(m == 'GET' for m, _ in EM), (wrote, [x for x in EM if x[0] != 'GET']))
    finally:
        S.request = real
        assert H.TEST_DB.startswith('tejas_isolated_') and H.TEST_DB != H.REAL_DB
        await H.tdbmod.client.drop_database(H.TEST_DB)
        print('dropped', H.TEST_DB)
    print(f'TOTAL {len(RESULTS)} PASS {sum(RESULTS)} FAIL {len(RESULTS) - sum(RESULTS)}')


if __name__ == '__main__':
    asyncio.run(main())
