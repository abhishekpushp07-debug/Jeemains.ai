"""TEST-ONLY qa216 copy of media_cdn_iso198 with 4-option questions (Phase 1 rule). iteration 198: question pictures through public, signed, CDN-cacheable links (/assets/links + /api/media/pack).
Isolated disposable DB (storage + AI mocked). Run: cd /app/backend && timeout 290 python tests/media_cdn_iso198.py
"""
import asyncio, sys, time
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import get_ready_iso188 as G  # noqa: E402,F401
from get_ready_iso188 import H, mkstaff, client, upload, complete, drain, check, RESULTS, J, go, student, unpack, structure, M, BM
import fitz  # noqa: E402
from tejas import media as MEDIA  # noqa: E402
from tejas.admission import workload  # noqa: E402

DB = H.TDB


def four_opt_pdf(tag='FOUR'):
    doc = fitz.open(); p = doc.new_page(); p.insert_text((40, 60), 'Physics', fontsize=13); y = 100
    qs = [(1, f'{tag} a ball falls 20 m. Find time.', ['1 s', '2 s', '3 s', '4 s']), (2, f'{tag} a car speed is', ['1 m/s', '2 m/s', '3 m/s', '4 m/s']),
          (3, f'{tag} unit of force is', ['joule', 'newton', 'watt', 'pascal'])]
    for num, text, opts in qs:
        p.insert_text((40, y), f'Q{num}. {text}', fontsize=11); y += 20
        for lab, o in zip('ABCD', opts): p.insert_text((60, y), f'({lab}) {o}', fontsize=11); y += 18
        y += 22
    p = doc.new_page(); p.insert_text((40, 60), 'Answer Key', fontsize=13); y = 100
    for num, ans in [(1, 'B'), (2, 'B'), (3, 'B')]: p.insert_text((40, y), f'Q{num}. ({ans})', fontsize=11); y += 20
    raw = doc.tobytes(); doc.close(); return raw


async def paper(own, stu):
    b = await upload(own, four_opt_pdf('CDN'), 'TEST_CDN', section_id='jee-main:mocks'); await complete(own, b['id']); await drain()
    m = await BM.find_one({'book_id': b['id']}); base = f"/api/admin/books/{b['id']}/mocks/{m['_id']}"
    p = J(await own.get(base + '/problems', params={'all': 'true'}))
    for q in p.get('questions', []):
        p = J(await own.get(base + '/problems', params={'all': 'true'}))
        await own.post(base + '/fix', json={'revision': p['revision'], 'question_id': q['id'], 'response_type': 'mcq', 'option_labels': ['A', 'B', 'C', 'D'], 'answer': 'B', 'complete': True}); await drain()
    await own.post(M + '/status', json={'items': [{'kind': 'book_mock', 'id': m['_id']}], 'to': 'live'}); await drain()
    await asyncio.sleep(2); await structure.visibility(force=True)
    sid = (await BM.find_one({'_id': m['_id']})).get('set_id')
    mm = await BM.find_one({'_id': m['_id']}); check('paper built', bool(sid), (mm.get('state'), mm.get('message'), mm.get('reason')))
    return sid


async def links_and_parts(own, stu, other):
    sid = await paper(own, stu)
    if not sid: return
    x = J(await go(stu, sid)); aid = x['id']
    srcq = [q for q in x.get('questions', []) if q.get('render_mode') == 'source' and q.get('asset_count')]
    check('player: picture questions carry no machine text', srcq and all(q.get('text') == '' for q in srcq), [q.get('text') for q in srcq][:2])
    check('player: screen-reader label kept', all('accessible_text' in q for q in srcq), '')
    r = await client().get('/api/media/probe.bin')
    check('probe public cacheable', r.status_code == 200 and r.headers.get('cache-control', '').startswith('public') and r.headers.get('x-media-cdn') == 'same-server' and r.headers.get('access-control-allow-origin') == '*', dict(r.headers))
    r = await stu.get(f'/api/attempts/{aid}/assets/links'); d = J(r)
    total, parts = d.get('total', 0), d.get('parts') or []
    check('links 200 with total/limit/parts', r.status_code == 200 and d.get('limit') == 12 and total > 0 and len(parts) == -(-total // 12), (r.status_code, r.text[:300]))
    check('links not cached by browser/CDN (private, no-store)', 'no-store' in r.headers.get('cache-control', ''), r.headers.get('cache-control'))
    check('links relative to this server when MEDIA_CDN_URL is empty', d.get('cdn') is False and all(u.startswith('/api/media/pack/') for u in parts), parts[:1])
    check('links expire 1-2 days ahead', 86400 <= d.get('expires_at', 0) - time.time() <= 2 * 86400 + 5, d.get('expires_at'))
    r = await other.get(f'/api/attempts/{aid}/assets/links'); check('links other student 404', r.status_code == 404, r.status_code)
    r = await client().get(f'/api/attempts/{aid}/assets/links'); check('links without sign-in 401', r.status_code == 401, r.status_code)
    y = J(await go(other, sid)); r = await other.get(f"/api/attempts/{y['id']}/assets/links")
    check('second student of same paper gets the same links (one CDN copy)', J(r).get('parts') == parts, '')
    anon = client()
    for k, url in enumerate(parts):
        r = await anon.get(url, headers={'Origin': 'https://evil.example'})
        priv = await stu.get(f'/api/attempts/{aid}/assets/pack', params={'offset': 12 * k, 'limit': 12})
        cc = r.headers.get('cache-control', '')
        check(f'part {k} 200 without cookies', r.status_code == 200 and r.headers.get('content-type', '').startswith('application/octet-stream'), (r.status_code, r.text[:200]))
        check(f'part {k} public cacheable immutable', cc.startswith('public, max-age=') and 's-maxage=' in cc and 'immutable' in cc and 'no-store' not in cc, cc)
        check(f'part {k} ACAO * for any origin, no Vary Origin, no cookie', r.headers.get('access-control-allow-origin') == '*' and 'origin' not in r.headers.get('vary', '').lower() and 'set-cookie' not in r.headers, dict(r.headers))
        check(f'part {k} bytes == private pack bytes', r.content == priv.content and unpack(r.content)[2], (len(r.content), len(priv.content)))
    head, imgs, _ = unpack((await anon.get(parts[0])).content)
    check('part header total == links total, PNG pictures', head['total'] == total and imgs and all(i[:8] == b'\x89PNG\r\n\x1a\n' for i in imgs), head['total'])
    built = MEDIA.stats['built']; await anon.get(parts[0]); check('repeat request served from memory (no rebuild)', MEDIA.stats['built'] == built, MEDIA.stats)
    MEDIA._parts.data.clear(); MEDIA._parts.size = 0; built = MEDIA.stats['built']
    rs = await asyncio.gather(*(anon.get(parts[0]) for _ in range(20)))
    check('20 at once on a cold part -> built once, all 200', MEDIA.stats['built'] == built + 1 and all(x.status_code == 200 for x in rs), (MEDIA.stats, [x.status_code for x in rs]))
    # tampering, expiry
    pid, name = parts[0].split('/')[-2:]
    o, lim, bonus, exp, sig = name[:-4].split('-', 4)
    bad = [f'/api/media/pack/{pid}/{o}-{lim}-{bonus}-{exp}-{"A" * 22}.bin', f'/api/media/pack/{pid}/12-{lim}-{bonus}-{exp}-{sig}.bin',
           f'/api/media/pack/{pid}/{o}-{lim}-1-{exp}-{sig}.bin', f'/api/media/pack/{"0" * 64}/{name}', f'/api/media/pack/{pid}/x.bin']
    for u in bad:
        r = await anon.get(u)
        check('tampered link 404 no-store ' + u[-40:], r.status_code == 404 and 'no-store' in r.headers.get('cache-control', '') and not r.headers.get('cache-control', '').startswith('public'), (r.status_code, r.headers.get('cache-control')))
    old = int(time.time()) - 10
    r = await anon.get(f'/api/media/pack/{pid}/{o}-{lim}-{bonus}-{old}-{MEDIA.sign(pid, int(o), int(lim), int(bonus), old)}.bin')
    check('expired link 404', r.status_code == 404, r.status_code)
    far = int(time.time()) + 10 * 86400
    r = await anon.get(f'/api/media/pack/{pid}/{o}-{lim}-{bonus}-{far}-{MEDIA.sign(pid, int(o), int(lim), int(bonus), far)}.bin')
    check('link valid too far ahead 404', r.status_code == 404, r.status_code)
    # a picture that cannot render: part served but never cached
    MEDIA._parts.data.clear(); MEDIA._parts.size = 0
    orig = MEDIA.render_crop; calls = {'n': 0}

    def broken(src, ref):
        calls['n'] += 1
        if calls['n'] == 1: raise RuntimeError('TEST broken crop')
        return orig(src, ref)
    MEDIA.render_crop = broken
    try:
        r = await anon.get(parts[0])
    finally:
        MEDIA.render_crop = orig
    check('part with one broken picture -> 200, no-store (CDN never keeps it)', r.status_code == 200 and r.headers.get('cache-control') == 'no-store' and len(unpack(r.content)[0]['items']) == len(imgs) - 1, (r.status_code, r.headers.get('cache-control')))
    r = await anon.get(parts[0]); check('next request complete and public again', r.status_code == 200 and r.headers.get('cache-control', '').startswith('public') and len(unpack(r.content)[0]['items']) == len(imgs), r.headers.get('cache-control'))
    # CDN base
    MEDIA.CDN = 'https://cdn.example.test'
    try:
        d2 = J(await stu.get(f'/api/attempts/{aid}/assets/links'))
    finally:
        MEDIA.CDN = ''
    check('MEDIA_CDN_URL set -> links point at the CDN, same path', d2.get('cdn') is True and [u.replace('https://cdn.example.test', '') for u in d2.get('parts', [])] == parts, d2.get('parts', [])[:1])
    # private pack unchanged
    r = await stu.get(f'/api/attempts/{aid}/assets/pack'); check('private pack still private no-store', r.status_code == 200 and 'no-store' in r.headers.get('cache-control', ''), r.headers.get('cache-control'))
    await stu.post(f'/api/attempts/{aid}/submit')
    r = await stu.get(f'/api/attempts/{aid}/assets/links'); check('links after submit 200 (a finished paper loads its pictures in bulk too)', r.status_code == 200, r.status_code)
    for _ in range(30):
        r = await stu.get(f'/api/attempts/{aid}/results')
        if r.status_code == 200: break
        await drain(); await asyncio.sleep(0.5)
    rq = [q for q in J(r).get('questions', []) if q.get('render_mode') == 'source' and q.get('asset_count')]
    check('results: picture questions carry no machine text', r.status_code == 200 and rq and all(q.get('text') == '' for q in rq), (r.status_code, [q.get('text') for q in rq][:2]))


def units():
    qs = [{'id': 'a', 'q_refs': [{'file_id': 'f'}]}, {'id': 'b', 'bonus': True, 'q_refs': [{'file_id': 'f'}, {'file_id': 'f'}]}]
    check('bonus pictures hidden until bonus opens', [x[0] for x in MEDIA.picture_refs(qs, None)] == ['a'] and len(MEDIA.picture_refs(qs, 123.0)) == 3, '')
    check('media requests have their own lane', workload('/api/media/pack/x/y.bin', 'GET') == 'media' and workload('/api/attempts/x/assets/links', 'GET') == 'read', '')


async def main():
    own, _ = await mkstaff('owner', 'c198'); a = await student('93'); b = await student('92')
    await structure.exams.update_one({'_id': 'jee-main'}, {'$set': {'shown': True}})
    units()
    try: await links_and_parts(own, a, b)
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
