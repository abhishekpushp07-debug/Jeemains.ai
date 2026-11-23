"""TEST-ONLY iteration 220: new picture answers behind the pilot number (ETag/304/206, asset_revision, finished-attempt links and
packs, solutions in packs, WebP), the old answers for everyone else, and the Phase 1 owner routes (block, machine status, staff sign-in limit).
Isolated disposable DB (storage + AI mocked). Run: cd /app/backend && timeout 280 python tests/pictures_iso220.py
"""
import asyncio, hashlib, io, sys, time, uuid
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import get_ready_iso188 as G  # noqa: E402,F401
from get_ready_iso188 import H, mkstaff, client, check, RESULTS, J, go, result, unpack, structure, ATT  # noqa: E402
from structure_iso173 import mkset  # noqa: E402
import fitz  # noqa: E402
from PIL import Image  # noqa: E402
from fastapi import HTTPException  # noqa: E402
from tejas import jobs as JOBS, book_worker  # noqa: E402

DB = H.TDB
PILOT = '7004186276'
PNG = b'\x89PNG\r\n\x1a\n'


def tag(b): return '"' + hashlib.sha256(b).hexdigest()[:32] + '"'
def webp(b): return b[:4] == b'RIFF' and b[8:16] == b'WEBPVP8L'
def flags(url): return int(url.split('/')[-1].split('-')[2])


def png(text):
    doc = fitz.open(); page = doc.new_page(width=420, height=160)
    for n in range(6): page.insert_text((20, 30 + 20 * n), f'{text} line {n}: integrate x^2 dx from 0 to {n + 3}', fontsize=11)
    raw = page.get_pixmap(matrix=fitz.Matrix(2, 2), alpha=False).tobytes('png'); doc.close()
    return raw


async def picture(text):
    raw = png(text); fid = str(uuid.uuid4()); path = f'jeelive/test220/{fid}.png'
    H.STORE[path] = raw
    await DB.tejas_files.insert_one({'id': fid, 'path': path, 'kind': 'rendered_png', 'sha256': hashlib.sha256(raw).hexdigest(), 'created_at': time.time()})
    return {'file_id': fid, 'page': 1, 'rect': [0, 0, 420, 160], 'prerendered': True}


async def paper():
    qs = []
    for i in range(14):
        q = {'id': str(uuid.uuid4()), 'number': i + 1, 'type': 'mcq', 'subject': 'Physics', 'section': 'A', 'options': {k: k for k in 'ABCD'}, 'answer': 'A', 'text': '',
             'solution': '', 'render_mode': 'source', 'accessible_text': f'Q{i + 1}', 'q_refs': [await picture(f'question {i + 1}')], 's_refs': [await picture(f'solution {i + 1}')]}
        if i == 0: q['c_refs'] = [{'part': p, 'w': 420, 'h': 160, **await picture(f'piece {p}')} for p in ('q', 'A', 'B', 'C', 'D')]
        qs.append(q)
    return await mkset('P220', exam='JEE Main', catalog_section_id='jee-main:mocks', test_kind='mock', questions=qs)


async def signup(phone, pin='8261'):
    s = client(); r = await s.post('/api/auth/phone/signup', json={'phone': phone, 'pin': pin, 'confirm_pin': pin})
    assert r.status_code == 200, r.text
    return s


def number(): return '98' + str(uuid.uuid4().int)[:8]


async def old_answers(sid):
    """A student outside the pilot: nothing may differ from before."""
    stu = await signup(number()); a = J(await go(stu, sid, ready=False)); aid, qid = a['id'], a['questions'][0]['id']
    rows = J(await stu.get(f'/api/attempts/{aid}'))['questions']
    check('old: attempt rows carry no asset_revision', all('asset_revision' not in q for q in rows), list(rows[0]))
    url = f'/api/attempts/{aid}/questions/{qid}/asset/question/0'
    r = await stu.get(url); body = r.content
    check('old: picture 200 PNG, no ETag, no Accept-Ranges, private no-store', r.status_code == 200 and body[:8] == PNG and 'etag' not in r.headers and 'accept-ranges' not in r.headers
          and r.headers.get('cache-control') == 'private, no-store' and r.headers.get('content-type') == 'image/png', dict(r.headers))
    r = await stu.get(url, headers={'If-None-Match': tag(body), 'Range': 'bytes=0-0', 'If-Range': tag(body)})
    check('old: If-None-Match / Range ignored (whole picture, 200)', r.status_code == 200 and r.content == body and 'content-range' not in r.headers, r.status_code)
    r = await stu.get(url + '?format=webp'); check('old: format=webp ignored (same PNG)', r.status_code == 200 and r.content == body and r.headers.get('content-type') == 'image/png', r.headers.get('content-type'))
    r = await stu.get(f'/api/attempts/{aid}/assets/links'); d = J(r); legacy = d.get('parts') or []
    check('old: links 200 with the old link flags (0-3)', r.status_code == 200 and legacy and all(flags(u) < 4 for u in legacy), legacy[:1])
    r2 = await stu.get(f'/api/attempts/{aid}/assets/links', params={'kind': 'solution', 'format': 'webp'})
    check('old: kind=solution / format=webp ignored on links', r2.status_code == 200 and J(r2).get('parts') == legacy, r2.status_code)
    head, imgs, ok = unpack((await client().get(legacy[0])).content)
    check('old: part header items unchanged (no etag), PNG pictures', ok and all(set(i) == {'question_id', 'index', 'size'} for i in head['items']) and all(i[:8] == PNG for i in imgs), head['items'][:1])
    r = await stu.get(f'/api/attempts/{aid}/assets/pack', params={'kind': 'solution', 'format': 'webp'}); head, imgs, ok = unpack(r.content)
    check('old: private pack unchanged (question PNGs, no etag)', r.status_code == 200 and ok and all('etag' not in i and 'kind' not in i for i in head['items']) and all(i[:8] == PNG for i in imgs), head['items'][:1])
    await stu.post(f'/api/attempts/{aid}/submit'); await result(stu, aid)
    r = await stu.get(f'/api/attempts/{aid}/assets/links'); check('old: links after submit still 409', r.status_code == 409, r.status_code)
    r = await stu.get(f'/api/attempts/{aid}/assets/pack'); check('old: pack after submit still 409', r.status_code == 409, r.status_code)
    r = await stu.get(f'/api/attempts/{aid}/results'); check('old: results rows carry no asset_revision', r.status_code == 200 and all('asset_revision' not in q for q in J(r)['questions']), r.status_code)
    r = await stu.get(f'/api/attempts/{aid}/questions/{qid}/asset/solution/0'); check('old: solution picture after submit 200, no ETag', r.status_code == 200 and 'etag' not in r.headers, r.status_code)
    # All India series: score and solutions open on submit, so their pictures must open too (rank alone waits for the day's close).
    await ATT.update_one({'id': aid}, {'$set': {'series_id': 'all-india-jee-2026-27', 'series_date': '2026-12-09', 'competition_end': time.time() + 3600}})
    r = await stu.get(f'/api/attempts/{aid}/questions/{qid}/asset/solution/0'); check('series attempt: solution picture opens right after submit', r.status_code == 200, (r.status_code, r.text[:120]))
    await ATT.update_one({'id': aid}, {'$unset': {'series_id': '', 'series_date': ''}})
    r = await stu.get(f'/api/attempts/{aid}/questions/{qid}/asset/solution/0'); check('live exam attempt: solution picture stays sealed (403)', r.status_code == 403, r.status_code)
    return legacy


async def new_answers(sid, legacy):
    stu = await signup(PILOT); a = J(await go(stu, sid, ready=False)); aid = a['id']; q1, q2 = a['questions'][0]['id'], a['questions'][1]['id']
    rows = J(await stu.get(f'/api/attempts/{aid}'))['questions']; revs = {q['id']: q.get('asset_revision') for q in rows}
    check('pilot: every attempt row has a 16-character asset_revision', all(isinstance(v, str) and len(v) == 16 for v in revs.values()), list(revs.values())[:2])
    check('pilot: asset_revision differs per question, same on a second read', len(set(revs.values())) == 14 and {q['id']: q['asset_revision'] for q in J(await stu.get(f'/api/attempts/{aid}'))['questions']} == revs, '')
    url = f'/api/attempts/{aid}/questions/{q1}/asset/question/0'
    r = await stu.get(url); body = r.content; n = len(body)
    check('pilot: picture 200 PNG with strong ETag = hash of the bytes', r.status_code == 200 and body[:8] == PNG and r.headers.get('etag') == tag(body) and r.headers.get('accept-ranges') == 'bytes'
          and r.headers.get('cache-control') == 'private, no-store', dict(r.headers))
    r = await stu.get(url, headers={'If-None-Match': tag(body)}); check('pilot: If-None-Match -> 304, empty, ETag kept', r.status_code == 304 and not r.content and r.headers.get('etag') == tag(body), (r.status_code, len(r.content)))
    r = await stu.get(url, headers={'If-None-Match': '"zz", W/' + tag(body)}); check('pilot: weak/list If-None-Match -> 304', r.status_code == 304, r.status_code)
    r = await stu.get(url, headers={'If-None-Match': '"other"'}); check('pilot: other ETag -> 200 whole picture', r.status_code == 200 and r.content == body, r.status_code)
    r = await stu.get(url, headers={'Range': 'bytes=0-0', 'If-Range': tag(body)})
    check('pilot: Range 0-0 + If-Range -> 206 with full length', r.status_code == 206 and r.content == body[:1] and r.headers.get('content-range') == f'bytes 0-0/{n}' and r.headers.get('etag') == tag(body), (r.status_code, r.headers.get('content-range')))
    r = await stu.get(url, headers={'Range': 'bytes=0-0', 'If-Range': '"changed"'}); check('pilot: If-Range of an old picture -> 200 whole new picture', r.status_code == 200 and r.content == body, r.status_code)
    r = await stu.get(url, headers={'Range': 'bytes=-10'}); check('pilot: last 10 bytes -> 206', r.status_code == 206 and r.content == body[-10:] and r.headers.get('content-range') == f'bytes {n - 10}-{n - 1}/{n}', r.headers.get('content-range'))
    r = await stu.get(url, headers={'Range': f'bytes={n + 5}-'}); check('pilot: range outside the picture -> 416', r.status_code == 416 and r.headers.get('content-range') == f'bytes */{n}', (r.status_code, r.headers.get('content-range')))
    r = await stu.get(url, headers={'Range': 'bytes=0-1,4-5'}); check('pilot: many ranges -> whole picture 200', r.status_code == 200 and r.content == body, r.status_code)
    # WebP
    r = await stu.get(url + '?format=webp'); light = r.content
    same = Image.open(io.BytesIO(light)).size == Image.open(io.BytesIO(body)).size and Image.open(io.BytesIO(light)).convert('RGBA').tobytes() == Image.open(io.BytesIO(body)).convert('RGBA').tobytes()
    check('pilot: format=webp -> lossless WebP (VP8L), image/webp, its own ETag', r.status_code == 200 and webp(light) and r.headers.get('content-type') == 'image/webp' and r.headers.get('etag') == tag(light) != tag(body), (r.headers.get('content-type'), light[:16]))
    check('pilot: WebP has the same pixel size and every pixel, in fewer bytes', same and len(light) < n, (len(light), n))
    r = await stu.get(url + '?format=webp', headers={'If-None-Match': tag(light)}); check('pilot: WebP If-None-Match -> 304', r.status_code == 304, r.status_code)
    r = await stu.get(url + '?format=jpeg'); check('pilot: unknown format -> PNG as before', r.status_code == 200 and r.content == body, r.status_code)
    # active attempt: solutions refused, links tagged
    for path in (f'/api/attempts/{aid}/questions/{q1}/asset/solution/0', f'/api/attempts/{aid}/assets/links?kind=solution', f'/api/attempts/{aid}/assets/pack?kind=solution'):
        r = await stu.get(path); check('pilot: running paper refuses solutions ' + path.split('/')[-1][:24], r.status_code == 403, r.status_code)
    d = J(await stu.get(f'/api/attempts/{aid}/assets/links')); parts = d.get('parts') or []
    check('pilot: links of a running paper (total 14, limit 12, 2 parts, own links)', d.get('total') == 14 and d.get('limit') == 12 and len(parts) == 2 and all(flags(u) == 4 for u in parts) and not set(parts) & set(legacy), (d.get('total'), parts[:1]))
    anon = client(); r = await anon.get(parts[0]); head, imgs, ok = unpack(r.content)
    check('pilot: part without cookies, every item has the ETag of its picture', r.status_code == 200 and ok and len(imgs) == 12 and all(i['etag'] == tag(b) for i, b in zip(head['items'], imgs))
          and r.headers.get('cache-control', '').startswith('public') and r.headers.get('access-control-allow-origin') == '*', (r.status_code, head['items'][:1]))
    check('pilot: pack item ETag == one-picture ETag', head['items'][0]['question_id'] == q1 and head['items'][0]['etag'] == tag(body), head['items'][0])
    d = J(await stu.get(f'/api/attempts/{aid}/assets/links?look=cut')); head, imgs, ok = unpack((await anon.get(d['parts'][0])).content)
    check('pilot: look=cut lists the 5 pieces of the cut question', d.get('total') == 18 and [i.get('kind') for i in head['items'][:6]] == ['piece'] * 5 + [None], [i.get('kind') for i in head['items'][:6]])
    # finished attempt
    await stu.post(f'/api/attempts/{aid}/submit'); r, res = await result(stu, aid)
    check('pilot: results rows carry the same asset_revision', r.status_code == 200 and {q['id']: q.get('asset_revision') for q in res.get('questions', [])} == revs, r.status_code)
    r = await stu.get(f'/api/attempts/{aid}/assets/links'); d = J(r)
    check('pilot: links of a FINISHED attempt 200', r.status_code == 200 and d.get('total') == 14 and len(d.get('parts') or []) == 2, (r.status_code, r.text[:150]))
    head, imgs, ok = unpack((await anon.get(d['parts'][1])).content); check('pilot: finished part 2 holds the last 2 pictures', ok and len(imgs) == 2 and all(i[:8] == PNG for i in imgs), len(imgs))
    one = (await stu.get(f'/api/attempts/{aid}/questions/{q2}/asset/solution/0')).content
    r = await stu.get(f'/api/attempts/{aid}/assets/links?kind=solution'); d = J(r); sol = d.get('parts') or []
    check('pilot: solution links after release 200 (own links)', r.status_code == 200 and d.get('total') == 14 and all(flags(u) == 13 for u in sol), (r.status_code, sol[:1]))
    r = await anon.get(sol[0]); head, imgs, ok = unpack(r.content)
    check('pilot: solution part = the one-picture solution bytes, kind solution, ETag', r.status_code == 200 and ok and all(i.get('kind') == 'solution' for i in head['items']) and imgs[1] == one and head['items'][1]['etag'] == tag(one), head['items'][:2])
    name = sol[0].split('/')[-1]; o, lim, f, rest = name.split('-', 3); base = sol[0].rsplit('/', 1)[0]
    for bad in (f'{o}-{lim}-5-{rest}', f'{o}-{lim}-9-{rest}', f'{o}-{lim}-45-{rest}'):
        r = await anon.get(f'{base}/{bad}'); check('tampered solution link 404 ' + bad[:9], r.status_code == 404, r.status_code)
    d = J(await stu.get(f'/api/attempts/{aid}/assets/links?kind=solution&format=webp')); head, imgs, ok = unpack((await anon.get(d['parts'][0])).content)
    check('pilot: solution links in WebP', all(flags(u) == 29 for u in d['parts']) and ok and all(webp(i) for i in imgs) and all(i['etag'] == tag(b) for i, b in zip(head['items'], imgs)), [i[:12] for i in imgs[:1]])
    r = await stu.get(f'/api/attempts/{aid}/assets/pack', params={'kind': 'solution', 'offset': 12}); head, imgs, ok = unpack(r.content)
    check('pilot: private pack with solutions (offset 12 -> 2 pictures, ETags)', r.status_code == 200 and ok and head['total'] == 14 and len(imgs) == 2 and all(i.get('kind') == 'solution' and i['etag'] == tag(b) for i, b in zip(head['items'], imgs)), (r.status_code, head))
    r = await stu.get(f'/api/attempts/{aid}/assets/pack', params={'format': 'webp'}); head, imgs, ok = unpack(r.content)
    check('pilot: private pack of a finished attempt in WebP', r.status_code == 200 and ok and len(imgs) == 12 and all(webp(i) for i in imgs), r.status_code)
    r = await stu.get(f'/api/attempts/{aid}/assets/links?score_version=nope'); check('pilot: unknown score_version 404', r.status_code == 404, r.status_code)
    other = await signup(number()); r = await other.get(f'/api/attempts/{aid}/assets/links?kind=solution'); check('pilot links: another student 404', r.status_code == 404, r.status_code)
    r = await client().get(f'/api/attempts/{aid}/assets/links'); check('pilot links: no sign-in 401', r.status_code == 401, r.status_code)
    # live exam: answers sealed until the window closes
    await ATT.update_one({'id': aid}, {'$set': {'competition_end': time.time() + 3600}})
    r1 = await stu.get(f'/api/attempts/{aid}/assets/links?kind=solution'); r2 = await stu.get(f'/api/attempts/{aid}/assets/pack?kind=solution'); r3 = await stu.get(f'/api/attempts/{aid}/assets/links')
    check('pilot: sealed live exam -> solutions 403, question links 200', (r1.status_code, r2.status_code, r3.status_code) == (403, 403, 200), (r1.status_code, r2.status_code, r3.status_code))
    await ATT.update_one({'id': aid}, {'$unset': {'competition_end': ''}, '$set': {'set_deleted': True}})
    r = await stu.get(f'/api/attempts/{aid}/assets/links'); check('pilot: deleted test -> links 404', r.status_code == 404, r.status_code)
    await ATT.update_one({'id': aid}, {'$unset': {'set_deleted': ''}})


async def owner_routes():
    own, own_id = await mkstaff('owner', 'p220'); rev, _ = await mkstaff('reviewer', 'p220')
    r = await own.get('/api/admin/machine/status'); d = J(r)
    check('machine status: owner 200 with every part', r.status_code == 200 and all(k in d for k in ('attention', 'storage_mode', 'cron', 'failed_jobs', 'failed_total', 'failed_books', 'stuck', 'disk', 'files_saved')), (r.status_code, list(d)))
    r = await rev.get('/api/admin/machine/status'); check('machine status: reviewer 403', r.status_code == 403, r.status_code)
    phone = number(); stu = await signup(phone, '4826'); me = J(await stu.get('/api/auth/me'))
    r = await rev.post(f"/api/admin/students/{me['id']}/block", json={}); check('block: reviewer 403', r.status_code == 403, r.status_code)
    r = await own.post(f"/api/admin/students/{me['id']}/block", json={}); check('block: owner 200, Hinglish message', r.status_code == 200 and J(r).get('blocked') is True and 'band' in J(r).get('message', ''), r.text[:160])
    r = await stu.get('/api/attempts'); check('blocked student is signed out at once (401)', r.status_code == 401, r.status_code)
    r = await client().post('/api/auth/phone', json={'phone': phone, 'pin': '4826'}); check('blocked student cannot sign in (403)', r.status_code == 403, (r.status_code, r.text[:120]))
    r = await client().post('/api/auth/pin/reset', json={'phone': phone, 'new_pin': '5937', 'confirm_pin': '5937'}); check('blocked student cannot use Forgot PIN (403)', r.status_code == 403, (r.status_code, r.text[:120]))
    row = next((x for x in J(await own.get('/api/admin/students', params={'q': phone[-10:]}))['items'] if x['id'] == me['id']), {})
    check('student list shows blocked', row.get('blocked') is True, row)
    r = await own.delete(f"/api/admin/students/{me['id']}/block"); check('unblock: owner 200', r.status_code == 200 and J(r).get('blocked') is False, r.text[:160])
    r = await client().post('/api/auth/phone', json={'phone': phone, 'pin': '4826'}); check('unblocked student signs in again', r.status_code == 200, (r.status_code, r.text[:120]))
    r = await own.post('/api/admin/students/nobody/block', json={}); check('block: unknown student 404', r.status_code == 404, r.status_code)
    email = f'qa220-{uuid.uuid4().hex[:8]}@example.com'; codes = []
    for _ in range(11):
        codes.append((await client().post('/api/auth/login', json={'email': email, 'password': 'Wrong!' + uuid.uuid4().hex[:8]})).status_code)
    check('staff sign-in: 9 wrong -> 401, the 10th starts a 15-minute wait (429)', codes[:9] == [401] * 9 and codes[9:] == [429, 429], codes)
    # A PDF that another worker is busy with is not a failed job.
    j = await JOBS.enqueue('book_step', own_id, 'bk220', {'key': 'bk220:1', 'book_id': 'bk220'}); orig = book_worker.step

    async def held(job): raise HTTPException(409, 'This book changed or is processing a batch. Reload and retry; saved work is retained.')
    book_worker.step = held
    try: await JOBS.run_job(j['id'], drain=False)
    finally: book_worker.step = orig
    row = await DB.tejas_jobs.find_one({'id': j['id']})
    check('busy PDF: the job waits its turn and keeps its tries', row['status'] == 'queued' and row.get('attempts') == 0 and row.get('next_run_at', 0) > time.time() + 5, {k: row.get(k) for k in ('status', 'attempts', 'next_run_at', 'error')})


async def main():
    await structure.exams.update_one({'_id': 'jee-main'}, {'$set': {'shown': True}})
    sid = await paper()
    for step in (lambda: old_answers(sid), ):
        pass
    legacy = []
    try: legacy = await old_answers(sid)
    except Exception:
        import traceback; traceback.print_exc(); check('old answers ran', False, 'exception above')
    try: await new_answers(sid, legacy)
    except Exception:
        import traceback; traceback.print_exc(); check('new answers ran', False, 'exception above')
    try: await owner_routes()
    except Exception:
        import traceback; traceback.print_exc(); check('owner routes ran', False, 'exception above')


async def run():
    assert not H.leftover_real_handles()
    await H.tdbmod.indexes(); await structure.seed()
    try: await main()
    finally:
        await H.tdbmod.client.drop_database(H.TEST_DB)  # only this run's own disposable database
        ok = sum(1 for r in RESULTS if r[1]); print(f'TOTAL {len(RESULTS)} PASS {ok} FAIL {len(RESULTS) - ok}'); print('dropped', H.TEST_DB)

if __name__ == '__main__':
    asyncio.run(run())
