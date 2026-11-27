"""TEST-ONLY iteration 250 (pocket S1b): pictures saved BEFORE the printed address ('Source: AITS Mock 06 / Q65') was hidden still
show it. "Line hatao" cuts them once more from the same PDF with the line painted out, proves each switch, and never removes a picture.
Chapter 8 of the owner's chemistry book through the real app (upload -> Draft -> Live -> a student), Supabase faked at the wire,
Emergent in memory, disposable DB, no network, no AI.
A. before: owner only; what waits is counted (whole-question and solution pictures, never the pieces); a new test waits for nothing.
B. the run: every picture with the line is switched; the new one differs from the old one inside that line alone (white); the old
   picture is still in storage byte for byte; pieces, the test, the frozen paper and the picture proof are untouched.
C. the student: single pictures, the public part links (new address; an old link gives the new picture too), asset_revision,
   solution pictures; a server that has not heard yet learns it from the link itself.
D. pressed again: nothing to do, nothing changes.
E. one picture's trouble stays with it: changed in storage, differs outside the line, gone, cut from another PDF, Supabase keeps
   other bytes, Supabase says yes and keeps nothing: each stays as it is, is listed with its reason, and is tried again next time.
F. Supabase away (and the PDF not on this server): the run waits, nothing is switched, it carries on by itself; Roko; a restart midway.
G. a test whose pictures are in Emergent (Supabase not set, and Supabase set later): the new picture goes beside the old one.
Run: cd /app/backend && python tests/source_repaint250.py   (drops only its own disposable database)
"""
import asyncio, hashlib, io, json, os, sys, time, types
from pathlib import Path
from urllib.parse import unquote
sys.path.insert(0, str(Path(__file__).resolve().parent))
from storage_book229 import H, BM, DB, S, RESULTS, check, mkstaff, upload, cancel_kicks, finish  # noqa: E402
from storage_stuck231 import live  # noqa: E402
from book_speed211 import chapter8  # noqa: E402
from source_hidden248 import J, painted, student, graded  # noqa: E402
from book_publishing_iso170 import client  # noqa: E402
from structure_iso173 import start  # noqa: E402
import httpx  # noqa: E402
from PIL import Image  # noqa: E402
from tejas import structure, media as MEDIA, pictures as P, source_repaint as SR  # noqa: E402
from tejas.book_pdf import inspect_many  # noqa: E402
from tejas.book_store import CACHE  # noqa: E402
from tejas.png_small import shrink_many  # noqa: E402
from tejas.picture_proof import prove  # noqa: E402
from fake_supabase239 import Leaky  # noqa: E402

API = '/api/admin/pictures/source-line'
SETS, FILES, OPS = DB.tejas_sets, DB.tejas_files, DB.tejas_operations
WORK = Path('/root/aitsv_out/rp250'); WORK.mkdir(parents=True, exist_ok=True)
sb = None


class Bent(Leaky):
    """...plus one knob: a small upload whose path contains one of `bend` is kept with one byte changed (Supabase says yes)."""
    def __init__(self, chunk):
        super().__init__(chunk)
        self.bend = []

    def __call__(self, req):
        r = super().__call__(req)
        p = unquote(req.url.path)
        if req.method == 'POST' and r.status_code == 200 and p.startswith('/storage/v1/object/') and any(x in p for x in self.bend):
            key = p[len('/storage/v1/object/'):]
            if key in self.objects:
                self.objects[key] = self.objects[key][:-1] + bytes([self.objects[key][-1] ^ 1])
        return r


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def held(path):
    """What storage holds at a saved reference (None = nothing)."""
    return sb.objects.get(path[len(S.SB):]) if path.startswith(S.SB) else H.STORE.get(path)


def put(path, raw):
    if path.startswith(S.SB):
        sb.objects[path[len(S.SB):]] = raw
    else:
        H.STORE[path] = raw


def forget():
    """TEST: this server forgets what it read before the test changed storage behind its back."""
    S._source_cache = S.ByteCache(64 * 1024 * 1024); MEDIA._parts.clear(); P._revisions.clear()


def unpack(b):
    n = int.from_bytes(b[:4], 'big'); head = json.loads(b[4:4 + n]); pos = 4 + n; out = {}
    for it in head['items']:
        out[(it['question_id'], it['index'])] = b[pos:pos + it['size']]; pos += it['size']
    return out


async def paper(own, chap, tag):
    """Chapter 8 through the real app: upload, Draft, Live. Returns (book id, test id, the PDF's path)."""
    raw = chapter8(); pdf = str(WORK / f'{tag}.pdf'); open(pdf, 'wb').write(raw)
    bid = (await upload(own, raw, 'TEST_RP250_' + tag, section_id=chap, subject='Chemistry'))['id']; await finish(own, bid)
    m = (await BM.find({'book_id': bid}).sort('order', 1).to_list(10))[0]
    assert m['state'] == 'ready', (m['state'], m['issues'][:3])
    r = await live(own, m['_id'])
    mk = await BM.find_one({'_id': m['_id']})
    assert r.status_code == 200 and mk.get('set_id') and mk['state'] == 'published', (r.status_code, r.text[:300], mk['state'], mk['issues'][:3])
    return bid, mk['set_id'], pdf


async def age(sid, pdf, unshrunk=3):
    """TEST: the whole-question and solution pictures of this test become what was saved before the line was hidden: the same
    region of the same page, cut plain. The first `unshrunk` stay as the cutter gave them (as before 23 Nov), the rest made smaller."""
    s = await SETS.find_one({'id': sid}, {'_id': 0})
    ids = list(dict.fromkeys(r['file_id'] for q in s['questions'] for k in ('q_refs', 's_refs') for r in q[k]))
    rows = {f['id']: f for f in await FILES.find({'id': {'$in': ids}}, {'_id': 0}).to_list(None)}
    items = [{'action': 'crop', 'page': rows[i]['original_page'], 'rect': rows[i]['original_rect']} for i in ids]
    plain = await asyncio.to_thread(inspect_many, pdf, items, 10)
    lined = await asyncio.to_thread(inspect_many, pdf, [{**x, 'mask': 'source'} for x in items], 10)
    small = await asyncio.to_thread(shrink_many, [c['image_bytes'] for c in plain])
    where = {r['file_id']: (q['number'], word) for q in s['questions'] for k, word in (('q_refs', 'sawaal'), ('s_refs', 'solution')) for r in q[k]}
    old = {}
    for n, (i, c, m, png) in enumerate(zip(ids, plain, lined, small)):
        png = c['image_bytes'] if n < unshrunk else png
        put(rows[i]['path'], png)
        await FILES.update_one({'id': i}, {'$set': {'sha256': sha(png), 'size': len(png)}, '$unset': {'source_mask': ''}})
        old[i] = {'path': rows[i]['path'], 'sha256': sha(png), 'size': len(png), 'bytes': png, 'line': bool(m.get('masked')), 'at': where[i],
                  'source_sha256': rows[i]['source_sha256'], 'ref': {'page': rows[i]['original_page'], 'rect': rows[i]['original_rect']}}
    forget()
    return s, old


async def old_again(old):
    """TEST: the pictures are once more what they were before a run (the new ones stay in storage, unused)."""
    for i, o in old.items():
        put(o['path'], o['bytes'])
        await FILES.update_one({'id': i}, {'$set': {k: o[k] for k in ('path', 'sha256', 'size', 'source_sha256')}, '$unset': {'source_mask': ''}})
    forget()


async def rows_of(old):
    return {f['id']: f for f in await FILES.find({'id': {'$in': list(old)}}, {'_id': 0}).to_list(None)}


async def ran(own, secs=240):
    """Waits for the run a press started; returns what the owner's panel is told."""
    stop, st = time.time() + secs, {}
    while time.time() < stop:
        if SR._tasks:
            await asyncio.wait(list(SR._tasks), timeout=5)
        st = J(await own.get(API + '/status'))
        if st.get('state') != 'running' and not SR._tasks:
            return st
        await asyncio.sleep(.05)
    return st


async def press(own):
    r = await own.post(API + '/start')
    return r, await ran(own)


def switched(f, o):
    """A picture that was switched: the new one lies beside the old one, in the same store; the record says where the old one is."""
    new = o['path'][:-len('.png')] + '.clean.png'
    m = f.get('source_mask') or {}
    return (f['path'] == new and m.get('state') == 'painted' and m.get('from') == {k: o[k] for k in ('path', 'sha256', 'size')}
            and held(new) is not None and sha(held(new)) == f['sha256'] and len(held(new)) == f['size'])


def untouched(f, o):
    return f['path'] == o['path'] and f['sha256'] == o['sha256'] and (f.get('source_mask') or {}).get('state') != 'painted'


async def only_the_line(pdf, old, rows):
    bad = []
    for i, o in old.items():
        if not o['line']:
            continue
        ok, why = await asyncio.to_thread(painted, pdf, o['ref'], held(rows[i]['path']))
        if not ok:
            bad.append((o['at'], why))
    return bad


async def before(own, rev, sid, pdf):
    for who, c, want in (('a reviewer', rev, (403,)), ('nobody signed in', client(), (401,))):
        got = [(await c.get(API + '/status')).status_code, (await c.post(API + '/start')).status_code, (await c.post(API + '/stop')).status_code]
        check(f'A. {who} cannot see, start or stop it', all(x in want for x in got), got)
    st = J(await own.get(API + '/status'))
    check('A. a test made Live now (its pictures were cut with the line already hidden) waits for nothing', st.get('state') == 'idle' and st.get('waiting') == 0, st)
    s, old = await age(sid, pdf)
    pieces = {r['file_id'] for q in s['questions'] for r in q.get('c_refs') or []}
    want = sum(1 for o in old.values() if o['line'])
    r = await own.get(API + '/status'); st = J(r)
    check('A. pictures saved before the change are counted: every whole-question and solution picture, not one piece', st.get('waiting') == len(old) and want > 0 and pieces and not pieces & set(old)
          and st.get('state') == 'idle', (st, len(old), want, len(pieces)))
    check('A. the panel is told no place in storage', not any(x in r.text for x in ('jeelive/', 'sb://', '.png')), r.text[:300])
    return s, old, want, pieces


async def the_run(own, sid, pdf, s, old, want, pieces):
    set0 = await SETS.find_one({'id': sid}); cut0 = {f['id']: f for f in await FILES.find({'id': {'$in': list(pieces)}}).to_list(None)}
    n0 = (await OPS.find_one({'_id': P.EPOCH}) or {}).get('n', 0)
    r, st = await press(own)
    check('B. "Line hatao": the run finishes; every picture with the line is done, none is left', r.status_code == 200 and st.get('state') == 'done' and st.get('painted') == want
          and st.get('clean') == len(old) - want and st.get('left') == 0 and st.get('failures') == [] and st.get('waiting') == 0 and st.get('total') == len(old), st)
    rows = await rows_of(old)
    check('B. each is switched to a new picture beside the old one, in the same store; the record keeps where the old one is',
          all(switched(rows[i], o) and rows[i]['path'].startswith(S.SB) for i, o in old.items() if o['line']), [(o['at'], rows[i]['path'][-40:], rows[i].get('source_mask')) for i, o in old.items() if o['line']][:2])
    check('B. a picture without the line is left exactly as it was', all(untouched(rows[i], o) and rows[i]['source_mask']['state'] == 'none' for i, o in old.items() if not o['line']),
          [(o['at'], rows[i].get('source_mask')) for i, o in old.items() if not o['line']][:2])
    check('B. no old picture was removed or overwritten: each is still in storage, byte for byte', all(held(o['path']) == o['bytes'] for o in old.values()), [o['at'] for o in old.values() if held(o['path']) != o['bytes']][:4])
    bad = await only_the_line(pdf, old, rows)
    check("B. every new picture differs from the printed page inside the 'Source' line alone, and that line is white (the unshrunk ones too)", not bad, bad[:3])
    check('B. the pieces (question and option pictures) are not touched', {f['id']: f for f in await FILES.find({'id': {'$in': list(pieces)}}).to_list(None)} == cut0, len(cut0))
    check('B. the test itself is not touched (same questions, same picture ids, same revision)', await SETS.find_one({'id': sid}) == set0, '')
    proof = await prove(await SETS.find_one({'id': sid}, {'_id': 0}), full=True)
    check('B. the picture proof still passes: every picture read back, all in Supabase', proof and proof['ok'] and proof['store'] == 'supabase' and proof['proven'] == proof['total'] == len(old) + len(pieces), proof)
    check('B. the servers were told once that pictures were replaced', (await OPS.find_one({'_id': P.EPOCH}) or {}).get('n') == n0 + 1 == P.number(), (n0, await OPS.find_one({'_id': P.EPOCH}), P.number()))
    check('B. the start is in the audit list', await DB.tejas_audits.count_documents({'action': "Older pictures: 'Source' line repaint started"}) == 1, '')
    return rows


async def the_student(sid, pdf, s, old, stu, aid, was):
    rows = await rows_of(old)
    qs = s['questions']; first = {q['id']: q['q_refs'][0]['file_id'] for q in qs}; sol = {q['id']: q['s_refs'][0]['file_id'] for q in qs}
    r = await stu.get(f"/api/attempts/{aid}/questions/{qs[0]['id']}/asset/question/0")
    check('C. the student whose paper was already open now gets the picture without the line', r.status_code == 200 and r.content == held(rows[first[qs[0]['id']]]['path']) != old[first[qs[0]['id']]]['bytes'], (r.status_code, len(r.content)))
    view = J(await stu.get(f'/api/attempts/{aid}'))
    now = {q['id']: q.get('asset_revision') for q in view.get('questions', [])}
    check('C. asset_revision changed for every question (the app loads its pictures again)', now and all(now[k] and now[k] != was['rev'][k] for k in now), [(was['rev'][k], now[k]) for k in now][:2])
    check('C. the paper frozen for the student is not rewritten', await DB.tejas_packs.find_one({'_id': was['pack']}) == was['pack_doc'], '')
    links = J(await stu.get(f'/api/attempts/{aid}/assets/links'))
    anon = client()
    check('C. the public links have new addresses (a CDN cannot answer them with a part it kept)', links.get('parts') and len(links['parts']) == len(was['links']) and not set(links['parts']) & set(was['links']), (links.get('parts', [])[:1], was['links'][:1]))
    got = {}
    for u in links.get('parts', []):
        r = await anon.get(u); got.update(unpack(r.content) if r.status_code == 200 else {})
    check('C. the new links carry the pictures without the line', len(got) == len(qs) and all(got[(q['id'], 0)] == held(rows[first[q['id']]]['path']) for q in qs), len(got))
    r = await anon.get(was['links'][0]); again = unpack(r.content) if r.status_code == 200 else {}
    check('C. a link handed out before the run still opens and gives the new pictures too', r.status_code == 200 and again and all(v == got[k] for k, v in again.items()) and again != was['part'], (r.status_code, len(again)))
    # Another server that has not looked yet: it believes the old number and still holds an old part.
    m = MEDIA._NAME.fullmatch(links['parts'][0].rsplit('/', 1)[1]); stale = f"{was['pack']}.{int(m[1])}.{int(m[2])}.{int(m[3])}.0"
    P._epoch.update(n=0, at=time.monotonic()); MEDIA._parts.clear(); MEDIA._parts.put(stale, r.content[:4] + b'old')
    r = await anon.get(links['parts'][0])
    check('C. a server that has not heard yet learns it from the link itself: it forgets its old part and gives the new pictures', r.status_code == 200 and unpack(r.content) == {k: v for k, v in got.items() if k in unpack(r.content)}
          and len(unpack(r.content)) == 12 and P.number() >= 1 and MEDIA._parts.get(stale) is None, (r.status_code, P.number()))
    bad = links['parts'][0][:-26] + ('A' * 22) + '.bin'
    r = await anon.get(bad)
    check('C. a made-up link is still refused', r.status_code == 404, r.status_code)
    await stu.post(f'/api/attempts/{aid}/begin'); await asyncio.sleep(.2)
    r = await stu.post(f'/api/attempts/{aid}/submit')
    r, d = await graded(stu, aid)
    check('C. the paper is submitted and marked as before', r.status_code == 200 and len(d.get('questions', [])) == len(qs), (r.status_code, r.text[:200]))
    r = await stu.get(f"/api/attempts/{aid}/questions/{qs[0]['id']}/asset/solution/0")
    check('C. the solution picture comes without the line', r.status_code == 200 and r.content == held(rows[sol[qs[0]['id']]]['path']) != old[sol[qs[0]['id']]]['bytes'], r.status_code)
    links = J(await stu.get(f'/api/attempts/{aid}/assets/links', params={'kind': 'solution'}))
    got = {}
    for u in links.get('parts', []):
        r = await anon.get(u); got.update(unpack(r.content) if r.status_code == 200 else {})
    check('C. the solution part links carry the solution pictures without the line', len(got) >= len(qs) and all(got[(q['id'], 0)] == held(rows[sol[q['id']]]['path']) for q in qs), len(got))


async def pressed_again(own, old, want):
    rows0, n0 = await rows_of(old), (await OPS.find_one({'_id': P.EPOCH}))['n']
    objects = len(sb.objects)
    r, st = await press(own)
    check('D. pressed again: nothing waits, nothing is done, nothing is saved, the servers are not told again', st.get('state') == 'done' and st.get('total') == 0 and st.get('painted') == 0 and st.get('waiting') == 0
          and st.get('painted_ever') == want and await rows_of(old) == rows0 and len(sb.objects) == objects and (await OPS.find_one({'_id': P.EPOCH}))['n'] == n0, st)


async def troubles(own, old, want):
    await old_again(old)
    x = [i for i, o in old.items() if o['line']][:6]
    o = [old[i] for i in x]
    put(o[0]['path'], o[0]['bytes'][:-1] + bytes([o[0]['bytes'][-1] ^ 1]))                       # 1. storage holds other bytes than were saved
    im = Image.open(io.BytesIO(o[1]['bytes'])).convert('RGB'); im.putpixel((im.width - 3, im.height - 3), (120, 120, 120))
    out = io.BytesIO(); im.save(out, 'PNG'); other = out.getvalue()                                 # 2. one pixel far from the line is different
    put(o[1]['path'], other); await FILES.update_one({'id': x[1]}, {'$set': {'sha256': sha(other), 'size': len(other)}})
    sb.objects.pop(o[2]['path'][len(S.SB):])                                                        # 3. gone from storage
    await FILES.update_one({'id': x[3]}, {'$set': {'source_sha256': 'f' * 64}})                     # 4. cut from another PDF
    sb.bend, sb.vanish, sb.vanish_first = [x[4] + '.clean.png'], [x[5] + '.clean.png'], None        # 5. kept with other bytes; 6. said yes, kept nothing
    for i in x[4:]:   # TEST: the new pictures an earlier run of this test saved for these two are not in the fake store any more
        sb.objects.pop(old[i]['path'][len(S.SB):-len('.png')] + '.clean.png', None)
    forget()
    want_why = dict(zip(x, (SR.CHANGED, SR.DIFFERENT, SR.UNREAD, SR.OTHER_PDF, SR.NOT_BACK, SR.REFUSED)))
    before = await rows_of({i: old[i] for i in x})
    r, st = await press(own)
    rows = await rows_of(old)
    check('E. six pictures in trouble: the run still finishes, the other pictures are done', st.get('state') == 'done' and st.get('painted') == want - 6 and st.get('left') == 6 and st.get('waiting') == 6
          and all(switched(rows[i], v) for i, v in old.items() if v['line'] and i not in x), st)
    check('E. each of the six stays exactly as it was (same place, same fingerprint) and its record says why',
          all(rows[i]['path'] == before[i]['path'] and rows[i]['sha256'] == before[i]['sha256'] and rows[i].get('source_mask', {}).get('state') == 'left' and rows[i]['source_mask'].get('reason') == want_why[i] for i in x),
          [(old[i]['at'], rows[i].get('source_mask')) for i in x])
    said = {f['label']: f['reason'] for f in st.get('failures', [])}
    check('E. the owner is told which picture (test, question, question or solution) and why, in plain words',
          len(said) == 6 and all(any(k.endswith(f"· Q{old[i]['at'][0]} · {old[i]['at'][1]}") and v == want_why[i] for k, v in said.items()) for i in x), said)
    check('E. the old pictures of the two that Supabase did not keep right are still where they were', held(o[4]['path']) == o[4]['bytes'] and held(o[5]['path']) == o[5]['bytes'], '')
    put(o[2]['path'], o[2]['bytes']); sb.bend, sb.vanish = [], []; forget()
    r, st = await press(own)
    rows = await rows_of(old)
    check('E. pressed again after three were put right: those three are done, the other three are listed again', st.get('state') == 'done' and st.get('total') == 6 and st.get('painted') == 3 and st.get('left') == 3
          and all(switched(rows[i], old[i]) for i in x[2:3] + x[4:]) and all(rows[i].get('source_mask', {}).get('state') == 'left' for i in x[:2] + x[3:4]) and st.get('waiting') == 3, st)


async def away(own, old, want, pdf_sha):
    await old_again(old)
    (CACHE / f'{pdf_sha}.pdf').unlink(missing_ok=True)   # the PDF is not on this server either: it must come from Supabase
    sb.down = True
    r, st = await press(own)
    rows = await rows_of(old)
    check('F. Supabase away: the run waits (it is not failed), not one picture is switched or called missing', r.status_code == 200 and st.get('state') == 'waiting' and st.get('painted') == 0 and st.get('left') == 0
          and all(untouched(rows[i], o) and 'source_mask' not in rows[i] for i, o in old.items()), st)
    sb.down = False; S.STATE.update(down_until=0.0, strikes=0)
    cancel_kicks()
    await own.post('/api/admin/storage/retry')
    st = await ran(own); rows = await rows_of(old)
    check('F. Supabase back: the run carries on by itself and finishes', st.get('state') == 'done' and st.get('painted') == want and st.get('left') == 0 and all(switched(rows[i], o) for i, o in old.items() if o['line']), st)

    await old_again(old)
    SR.CHUNK, chunk = 4, SR.CHUNK
    try:
        await own.post(API + '/start')
        for _ in range(2400):
            st = J(await own.get(API + '/status'))
            if st.get('painted', 0) + st.get('clean', 0) + st.get('left', 0) >= 4 or st.get('state') != 'running':
                break
            await asyncio.sleep(.05)
        r = await own.post(API + '/stop')
        if SR._tasks:
            await asyncio.wait(list(SR._tasks), timeout=120)
        st = J(await own.get(API + '/status')); done = st.get('painted', 0) + st.get('clean', 0) + st.get('left', 0)
        check('F. "Roko" in the middle: it stops after the pictures in hand; the rest still wait', r.status_code == 200 and st.get('state') == 'stopped' and 0 < done < len(old) and st.get('waiting') == len(old) - done, st)
        await OPS.update_one({'_id': SR.OP}, {'$set': {'state': 'running', 'lease': 'a-server-that-stopped', 'lease_until': time.time() - 5}})
        st = J(await own.get(API + '/status'))
        check('F. a server that stopped midway: the panel says so', st.get('state') == 'interrupted', st)
        await SR.resume()   # what the app's own round does every few minutes
        st = await ran(own); rows = await rows_of(old)
        check('F. ...and the run is picked up from where it stopped: every picture done exactly once', st.get('state') == 'done' and st.get('painted') == want and st.get('left') == 0 and st.get('total') == len(old)
              and all(switched(rows[i], o) for i, o in old.items() if o['line']) and not any('.clean.clean' in k for k in sb.objects), st)
    finally:
        SR.CHUNK = chunk


async def emergent(own, chap):
    url = os.environ.pop('SUPABASE_URL')
    try:
        bid, sid, pdf = await paper(own, chap, 'emergent')
        s, old = await age(sid, pdf, unshrunk=0)
        want = sum(1 for o in old.values() if o['line'])
        r, st = await press(own); rows = await rows_of(old)
        check('G. Supabase not set: pictures in Emergent are switched the same way, the new one beside the old one in Emergent', st.get('state') == 'done' and st.get('painted') == want and st.get('left') == 0
              and all(switched(rows[i], o) and not rows[i]['path'].startswith(S.SB) for i, o in old.items() if o['line']) and all(held(o['path']) == o['bytes'] for o in old.values()), st)
        bad = await only_the_line(pdf, old, rows)
        proof = await prove(await SETS.find_one({'id': sid}, {'_id': 0}), full=True)
        check('G. ...only the line differs, and the picture proof passes (all in Emergent)', not bad and proof['ok'] and proof['store'] == 'emergent', (bad[:2], proof))
    finally:
        os.environ['SUPABASE_URL'] = url
    await old_again(old)
    n = len(sb.objects)
    r, st = await press(own); rows = await rows_of(old)
    proof = await prove(await SETS.find_one({'id': sid}, {'_id': 0}), full=True)
    check('G. Supabase set later, the test still in Emergent: the new pictures go beside the old ones in Emergent, so the test stays in one store',
          st.get('state') == 'done' and st.get('painted') == want and all(switched(rows[i], o) and not rows[i]['path'].startswith(S.SB) for i, o in old.items() if o['line'])
          and len(sb.objects) == n and proof['ok'] and proof['store'] == 'emergent', (st, len(sb.objects) - n, proof))


async def main():
    global sb
    assert not H.leftover_real_handles()
    await H.tdbmod.indexes(); await structure.seed()
    sb = Bent(S.TUS_CHUNK)
    wire = httpx.Client(transport=httpx.MockTransport(sb))
    S._client = lambda: wire                                                 # nothing leaves this process
    S.time = types.SimpleNamespace(time=time.time, sleep=lambda s: None)     # the storage code's own waits only
    S.STATE.update(down_until=0.0, strikes=0, last_error='', auth=None, bucket=None, failovers=0, last_failover=None, backup_since=None)
    try:
        own, _ = await mkstaff('owner', 'rp250'); rev, _ = await mkstaff('reviewer', 'rp250r')
        slug = J(await own.post('/api/admin/catalog/exams', json={'name': 'RPX', 'short': 'RP', 'subjects': ['Chemistry'], 'color': 'rose'})).get('slug')
        chap = J(await own.post(f'/api/admin/catalog/exams/{slug}/sections', json={'name': 'Chapter-wise', 'description': '', 'layout': 'chapters', 'kind': 'chapters'})).get('id')
        await structure.exams.update_one({'_id': slug}, {'$set': {'shown': True}})
        bid, sid, pdf = await paper(own, chap, 'main')
        s, old, want, pieces = await before(own, rev, sid, pdf)
        # A student opens the paper while its pictures still show the line.
        await asyncio.sleep(2); await structure.visibility(force=True)
        stu = await student(); r = await start(stu, sid); aid = J(r).get('id')
        q0 = s['questions'][0]; r1 = await stu.get(f"/api/attempts/{aid}/questions/{q0['id']}/asset/question/0")
        check('A. today a student of this test still gets the picture with the line', r.status_code == 200 and r1.status_code == 200 and r1.content == old[q0['q_refs'][0]['file_id']]['bytes'], (r.status_code, r1.status_code))
        view = J(await stu.get(f'/api/attempts/{aid}')); links = J(await stu.get(f'/api/attempts/{aid}/assets/links'))
        a = await DB.tejas_attempts.find_one({'id': aid}, {'pack_id': 1})
        was = {'rev': {q['id']: q.get('asset_revision') for q in view['questions']}, 'links': links['parts'], 'part': unpack((await client().get(links['parts'][0])).content),
               'pack': a['pack_id'], 'pack_doc': await DB.tejas_packs.find_one({'_id': a['pack_id']})}
        await the_run(own, sid, pdf, s, old, want, pieces)
        await the_student(sid, pdf, s, old, stu, aid, was)
        await pressed_again(own, old, want)
        await troubles(own, old, want)
        await away(own, old, want, (await DB.tejas_books.find_one({'_id': bid}))['payload']['sha256'])
        await emergent(own, chap)
    finally:
        cancel_kicks()
        for t in list(SR._tasks):
            t.cancel()
        # Only the disposable database this run created; never the app's own.
        assert H.TEST_DB.startswith('tejas_isolated_') and H.TEST_DB != H.REAL_DB, H.TEST_DB
        await H.tdbmod.client.drop_database(H.TEST_DB)
        print('dropped', H.TEST_DB, flush=True)
    print(f'TOTAL {len(RESULTS)} PASS {sum(RESULTS)} FAIL {len(RESULTS) - sum(RESULTS)}', flush=True)


if __name__ == '__main__':
    asyncio.run(main())
