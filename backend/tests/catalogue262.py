"""TEST-ONLY iteration 262 (the app's note of 27 Nov 2026, part 2): the chapter catalogue honours per_page (1 to 100); 12 stays the page
size when it is not sent; nothing else in the answer changes. The real website server in a disposable DB (storage mocked, no AI, no network).
Run: cd /app/backend && bash /root/p2/solo.sh python -u tests/catalogue262.py   (drops only its own disposable database)
"""
import asyncio, secrets, sys, time
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import book_publishing_iso170 as T  # noqa: E402,F401
from book_publishing_iso170 import H, client, check, RESULTS  # noqa: E402
from structure_iso173 import mkset, start  # noqa: E402
from tejas import structure  # noqa: E402

URL = '/api/exam-navigation/jee-main/catalogue'
SUBJECTS = ('Physics', 'Chemistry', 'Mathematics')


async def read(c, **params):
    r = await c.get(URL, params={'kind': 'chapters', **params})
    return r.status_code, (r.json() if r.status_code == 200 else {})


def ids(d):
    return [x['id'] for x in d.get('items', [])]


async def main():
    try:
        check('no customer DB handles', not H.leftover_real_handles(), H.leftover_real_handles())
        await structure.seed()
        stu = client()
        r = await stu.post('/api/auth/phone/signup', json={'phone': '97' + f'{secrets.randbelow(10 ** 8):08d}', 'pin': '4826', 'confirm_pin': '4826'})
        check('a student signs up', r.status_code == 200, r.text[:200])
        t = time.time()
        made = [await mkset(f'C{n:02d}', exam='JEE Main', test_kind='chapter', chapter_book_id='TEST_CB262', chapter_subject=SUBJECTS[n % 3], chapter_number=n,
                            live_enabled=True, start_at=t - 3600, end_at=t + 86400 * 30) for n in range(1, 31)]
        code, d = await read(stu)
        check('per_page not sent: 12 on a page, 30 in all, 3 pages (as before)', code == 200 and len(ids(d)) == 12 and d.get('total') == 30 and d.get('pages') == 3 and d.get('page') == 1,
              (code, len(ids(d)), d.get('total'), d.get('pages')))
        keys = set(d['items'][0]) if d.get('items') else set()
        walked = ids(d) + ids((await read(stu, page=2))[1]) + ids((await read(stu, page=3))[1])
        check('the three pages of 12 give every chapter test once', sorted(walked) == sorted(made), (len(walked), len(set(walked))))
        code, big = await read(stu, per_page=100)
        check('per_page=100: all 30 in one answer, in the same order as the pages of 12; pages 1', code == 200 and ids(big) == walked and big.get('pages') == 1 and big.get('total') == 30,
              (code, len(ids(big)), big.get('pages')))
        check('per_page=100: an item has exactly the fields it had', bool(keys) and all(set(x) == keys for x in big.get('items', [])), sorted(keys))
        check('per_page=100: subject_counts and section are as without it',
              big.get('subject_counts') == d.get('subject_counts') == {s: 10 for s in SUBJECTS} and big.get('section') == d.get('section'), (big.get('subject_counts'), d.get('subject_counts')))
        (code, p), (_, last), (code_over, over) = await read(stu, per_page=5, page=2), await read(stu, per_page=5, page=6), await read(stu, per_page=5, page=7)
        check('per_page=5: page 2 is the 6th to the 10th, 6 pages; page 6 is the last five; page 7 is empty', code == 200 and ids(p) == walked[5:10] and p.get('pages') == 6
              and ids(last) == walked[25:] and code_over == 200 and over.get('items') == [], (code, ids(p) == walked[5:10], p.get('pages'), len(ids(last)), code_over))
        code, s = await read(stu, per_page=100, subject='Chemistry')
        check("per_page=100 with a subject: that subject's 10 only", code == 200 and len(ids(s)) == 10 and all(x['chapter_subject'] == 'Chemistry' for x in s['items']) and s.get('total') == 10,
              (code, len(ids(s)), s.get('total')))
        bad = [(await read(stu, per_page=v))[0] for v in (0, 101, -1, 'all')]
        check('per_page 0, 101, -1 or a word is refused (422), never silently changed', bad == [422] * 4, bad)
        late = walked[19]
        r = await start(stu, late)
        (_, again), (_, second) = await read(stu, per_page=100), await read(stu, page=2)
        a100 = next((x.get('attempt') for x in again.get('items', []) if x['id'] == late), None)
        a12 = next((x.get('attempt') for x in second.get('items', []) if x['id'] == late), None)
        others = [x['id'] for x in again.get('items', []) if x.get('attempt') and x['id'] != late]
        check('a paper this student began (the 20th) carries its attempt in the answer of 100 and on page 2 of 12; no other does',
              r.status_code == 200 and bool(a100) and a100 == a12 and not others, (r.status_code, r.text[:160], a100, a12, others))
        r = await client().get(URL, params={'kind': 'chapters', 'per_page': 100})
        check('signed out: 401, as before', r.status_code == 401, r.status_code)
    except Exception as e:   # noqa: BLE001
        import traceback; traceback.print_exc(); check('no crash', False, repr(e))
    finally:
        # Only the disposable database this run created; never the app's own.
        assert H.TEST_DB.startswith('tejas_isolated_') and H.TEST_DB != H.REAL_DB, H.TEST_DB
        await H.tdbmod.client.drop_database(H.TEST_DB)
        print('dropped', H.TEST_DB, flush=True)
        bad = [r for r in RESULTS if not r[1]]
        print(f'TOTAL {len(RESULTS)} PASS {len(RESULTS) - len(bad)} FAIL {len(bad)}', flush=True)


if __name__ == '__main__':
    asyncio.run(main())
