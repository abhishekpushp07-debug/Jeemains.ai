"""TEST-ONLY Packet E on the REAL Supabase, preview bucket only. No app data: the picture records are a list in this file, not the database.
A folder shaped exactly like one upload's own picture folder (jeelive/books/<a fresh random id>/crops/) gets six TEST_ pictures. The proof
(tejas/picture_proof.py) must see them in Supabase's own list with their sizes, notice one that is removed, one stored with another size
and (full check only) one with other bytes of the same size. Everything this test made is removed at the end.
Run: cd /app/backend && python tests/picture_proof_real239.py
"""
import asyncio, hashlib, os, sys, uuid
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from dotenv import load_dotenv
load_dotenv(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), '.env'))
import tejas_storage as S

assert 'preview' in S.bucket_name(), 'preview bucket only'
from tejas import picture_proof as PP  # noqa: E402

RESULTS = []
A = f'jeelive/books/{uuid.uuid4()}/'
CROPS = A + 'crops'
B = S._bucket()


def check(name, ok, detail=''):
    RESULTS.append(bool(ok)); print(('PASS ' if ok else 'FAIL ') + name + ('' if ok else ' :: ' + str(detail)[:400]), flush=True)


class Records:
    """Stands in for the picture records of the database (read only)."""
    def __init__(self):
        self.rows = {}

    def find(self, where, fields=None):
        found = [dict(self.rows[i]) for i in where['id']['$in'] if i in self.rows]

        class Cursor:
            async def to_list(self, n):
                return found
        return Cursor()


def name(fid):
    return f'{CROPS}/TEST_{fid}.png'


def save(fid, raw):
    return S.sb_put(name(fid), raw, 'image/png')


async def main():
    recs = Records()
    PP.files = recs
    data = {}
    try:
        for i in range(6):
            fid, raw = str(uuid.uuid4()), b'\x89PNG\r\n\x1a\n' + os.urandom(2000 + 37 * i)
            data[fid] = raw
            recs.rows[fid] = {'id': fid, 'path': save(fid, raw), 'sha256': hashlib.sha256(raw).hexdigest(), 'size': len(raw)}
        ids = list(data)
        paper = {'id': 'TEST', 'test_kind': 'mock', 'questions': [{'id': 'q1', 'q_refs': [{'file_id': ids[0]}, {'file_id': ids[1]}], 's_refs': [{'file_id': ids[2]}],
                                                                   'c_refs': [{'file_id': ids[3]}, {'file_id': ids[4]}, {'file_id': ids[5]}]}]}
        there = dict(S.sb_list(CROPS, B)[0])
        check("1. real Supabase lists each picture with its size as a number, equal to what was saved", len(there) == 6
              and all(isinstance(there.get(f'TEST_{f}.png'), int) and there[f'TEST_{f}.png'] == len(data[f]) for f in ids), there)
        r = await PP.prove(paper)
        check('2. the proof of the healthy paper: 6 of 6, in Supabase', r['ok'] and r['store'] == 'supabase' and r['total'] == r['proven'] == 6 and not r['bad'], r)
        r = await PP.prove(paper, full=True)
        check('3. the full check reads every picture back and each matches its fingerprint', r['ok'] and r['full'] is True and r['proven'] == 6, r)

        S.sb_remove(A, [name(ids[3])])
        r = await PP.prove(paper)
        check('4. one picture removed from Supabase: found at once, named, counted', not r['ok'] and r['bad'] == {ids[3]: 'missing'} and r['reason'] == '1 picture storage me nahi mili', r)
        save(ids[3], data[ids[3]])
        check('5. saved once more: proven again', (await PP.prove(paper))['ok'])

        save(ids[0], data[ids[0]][:-5])
        r = await PP.prove(paper)
        check('6. a picture stored with another size: caught from the list alone', not r['ok'] and r['bad'] == {ids[0]: 'size'}, r)
        save(ids[0], data[ids[0]])
        check('7. the right bytes saved again: proven again', (await PP.prove(paper))['ok'])

        other = data[ids[1]][:-1] + bytes([data[ids[1]][-1] ^ 1])
        save(ids[1], other)
        quick, full = await PP.prove(paper), await PP.prove(paper, full=True)
        check('8. other bytes of the same size: the quick proof passes it, the full check catches it', quick['ok'] and not full['ok'] and full['bad'] == {ids[1]: 'bytes'}, (quick['bad'], full['bad']))
        save(ids[1], data[ids[1]])
        full = await PP.prove(paper, full=True)
        check('9. the right bytes saved again: the full check passes straight away (no stale copy is read back)', full['ok'], full['bad'])
        check('10. Supabase was never rested by any of this', S.supabase_on() and S.STATE['strikes'] == 0, S.STATE['strikes'])

        # A big book's folder: more files than one page of Supabase's list (1000). The pictures sort after the fillers, so they sit on the second page.
        from concurrent.futures import ThreadPoolExecutor
        with ThreadPoolExecutor(max_workers=16) as pool:
            sent = list(pool.map(lambda i: S.sb_put(f'{CROPS}/!TEST_filler-{i:04d}.bin', b'x', 'application/octet-stream'), range(1005)))
        found = S.sb_list(CROPS, B)[0]
        check("11. a folder with 1011 files: real Supabase's list is read to its end (every file, each once)", len(sent) == 1005 and len(found) == 1011 and len({n for n, _ in found}) == 1011, len(found))
        r = await PP.prove(paper)
        check('12. the pictures on the second page of that folder are proven', r['ok'] and r['proven'] == 6, r)
    finally:
        try:
            S.sb_empty(A)
        except Exception as exc:  # noqa: BLE001
            print('cleanup problem', exc)
        files, inner = S.sb_list(A)
        print('cleanup: left in the test folder:', len(files) + len(inner), flush=True)
    print(f'TOTAL {len(RESULTS)} PASS {sum(RESULTS)} FAIL {len(RESULTS) - sum(RESULTS)}')


if __name__ == '__main__':
    asyncio.run(main())
