"""TEST-ONLY iteration 244 (Packet E, written mocks): a mock typed in Master is shown to students only when every photo of it is
proven in storage: read back from the store itself (never from this server's memory), matched by fingerprint, all in one store.
A. healthy: Live, as before; a typed mock asks storage nothing.
B. a photo Supabase did not keep / a photo that is gone although this server still remembers it / a photo whose bytes changed:
   that mock stays Draft and names the question.
C. one press with other mocks (written and PDF): only the bad one is skipped.
D. Schedule (also as a live exam): the same, and no time is left on the Draft.   E. photo added again: "Live karo" opens it now.
F. Supabase away: the mock says so and stays Draft; Supabase is not rested for everyone; Live once Supabase answers.
G. All India Test Series: a paper that is not proven does not take or keep a day; "fill" carries on with the next paper.
H. photos split between Supabase and Emergent: not Live, the old-store question is named; an all-Emergent (old) mock still goes Live.
I. a mock that is Live: a new photo that is not in storage is refused and nothing is saved; so is a new name while its photos cannot
   be read; other edits work as before, also on a mock whose photos are in the old store.
J. a verified JEE Main PYQ paper is never checked.
K. the paper cannot be made although its photos were proven a moment before: the reason is given, and no time or day stays behind.
Supabase faked at the wire (tests/fake_supabase239.py), Emergent in memory, disposable DB, no network.
Run: cd /app/backend && python tests/written_live244.py
"""
import asyncio, io, json, sys, time, types, uuid
from datetime import datetime, timedelta
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from storage_book229 import H, J, BM, DB, S, RESULTS, check, mkstaff, cancel_kicks, pump  # noqa: E402
from storage_stuck231 import item  # noqa: E402
from picture_gate239 import book  # noqa: E402
import picture_gate239 as PG  # noqa: E402
from book_publishing_iso170 import client  # noqa: E402
import httpx  # noqa: E402
from tejas import structure  # noqa: E402
from tejas.live_series import IST  # noqa: E402
from fake_supabase239 import Leaky  # noqa: E402

M = '/api/admin/master'
SETS, FILES = DB.tejas_sets, DB.tejas_files
LIST = '/storage/v1/object/list/'
GONE, CHANGED = 'ki photo storage mein nahi mili', 'ki photo storage mein badli hui mili'
NOT_LIVE, NOT_SCHEDULED = 'isliye yeh Live nahi hua (Draft hi hai).', 'isliye yeh Schedule nahi hua (Draft hi hai).'
NO_DAY, NOT_SAVED = 'isliye is paper ko din nahi mila (Draft hi hai).', 'isliye yeh badlav save nahi hua (Live paper jaisa tha waisa hi hai).'
AWAY, AGAIN = 'Is mock ki photo abhi jaanchi nahi ja saki (Supabase', 'dobara lagaiye'
TIMES = ('start_at', 'end_at', 'last_start_at', 'competition', 'series_id', 'series_date', 'series_window', 'series_import')


def mcq(text, **kw):
    return {'id': '', 'subject': 'Physics', 'chapter': '', 'text': text, 'image': '', 'type': 'mcq', 'options': [{'text': x, 'image': ''} for x in 'wxyz'],
            'answer': 'B', 'solution': '', 'solution_image': '', **kw}


def png(shade):
    from PIL import Image
    out = io.BytesIO(); Image.new('RGB', (60, 40), (shade, 90, 160)).save(out, 'PNG'); return out.getvalue()


def said(r):
    """The message of an error answer (the harness unwraps only good answers)."""
    try:
        return ((json.loads(r.text) or {}).get('error') or {}).get('message', '')
    except ValueError:
        return ''


async def photo(own, wid, shade=20):
    r = await own.post(f'{M}/written/{wid}/images', files={'file': ('fig.png', png(shade), 'image/png')})
    assert r.status_code == 200, r.text
    return J(r)['id']


async def written(own, sec, title, photos=0, plain=1):
    """A written Draft: `plain` typed questions first, then one question per photo."""
    wid = J(await own.post(f'{M}/types/{sec}/written', json={'title': title})).get('id')
    for i in range(plain):
        r = await own.put(f'{M}/written/{wid}/questions', json=mcq(f'{title} typed question {i + 1}'))
        assert r.status_code == 200, r.text
    for i in range(photos):
        r = await own.put(f'{M}/written/{wid}/questions', json=mcq(f'{title} photo question {i + 1}', image=await photo(own, wid, 20 + 30 * i)))
        assert r.status_code == 200, r.text
    return wid


async def lost(own, sec, sb, title, plain=1):
    """A written Draft whose one photo Supabase said yes to and did not keep."""
    wid = J(await own.post(f'{M}/types/{sec}/written', json={'title': title})).get('id')
    for i in range(plain):
        await own.put(f'{M}/written/{wid}/questions', json=mcq(f'{title} typed question {i + 1}'))
    sb.vanish = [f'/written/{wid}/']
    r = await own.put(f'{M}/written/{wid}/questions', json=mcq(f'{title} photo question', image=await photo(own, wid)))
    sb.vanish = []
    assert r.status_code == 200, r.text
    return wid


async def photos(own, wid):
    """(question number, question id, photo id) of every question that has a photo."""
    return [(q['number'], q['id'], q['q_refs'][0]['file_id']) for q in J(await own.get(f'{M}/written/{wid}'))['questions'] if q['q_refs']]


async def key_of(fid):
    return (await FILES.find_one({'id': fid}))['path'][len(S.SB):]


async def to_emergent(sb, fid):
    """TEST: this photo is in the old store (Emergent), as photos saved before Supabase were."""
    key = await key_of(fid); inner = key.split('/', 1)[1]
    H.STORE[inner] = sb.objects.pop(key)
    await FILES.update_one({'id': fid}, {'$set': {'path': inner}})


async def mend(own, wid, number=None):
    """The owner removes a photo and adds it again (the first photo question, or question `number`)."""
    n, qid, _ = next(x for x in await photos(own, wid) if number in (None, x[0]))
    return await own.put(f'{M}/written/{wid}/questions', json=mcq('photo added again', id=qid, image=await photo(own, wid, 200 + n)))


async def press(own, to, items, **kw):
    r = await own.post(M + '/status', json={'items': items, 'to': to, **kw})
    return r.status_code, J(r)


def one(kind, id):
    return {'kind': kind, 'id': id}


def why_of(d):
    return (d.get('skipped') or [{}])[0].get('reason', '')


async def doc(wid):
    return await SETS.find_one({'id': wid}, {'_id': 0, 'questions': 0}) or {}


def plain_draft(s):
    """Draft, with nothing left behind by a try that failed."""
    return s.get('status') == 'draft' and not any(k in s for k in TIMES)


def same(a, b):
    return all(a.get(k) == b.get(k) for k in ('status', 'revision', 'version', 'questions', 'file_ids'))


async def main():
    assert not H.leftover_real_handles()
    await H.tdbmod.indexes(); await structure.seed()
    sb = Leaky(S.TUS_CHUNK); PG.sb = sb
    wire = httpx.Client(transport=httpx.MockTransport(sb))
    S._client = lambda: wire                                                 # nothing leaves this process
    S.time = types.SimpleNamespace(time=time.time, sleep=lambda s: None)     # the storage code's own waits only
    S.STATE.update(down_until=0.0, strikes=0, last_error='', auth=None, bucket=None, failovers=0, last_failover=None, backup_since=None)
    try:
        own, _ = await mkstaff('owner', 'w244'); anon = client()
        stu = client(); await stu.post('/api/auth/phone/signup', json={'phone': '93' + str(uuid.uuid4().int)[:8], 'pin': '8261', 'confirm_pin': '8261'})
        slug = J(await own.post('/api/admin/catalog/exams', json={'name': 'WRX', 'short': 'WR', 'subjects': ['Physics'], 'color': 'rose'})).get('slug')
        sec = J(await own.post(f'/api/admin/catalog/exams/{slug}/sections', json={'name': 'Mock Tests', 'description': '', 'layout': 'list', 'kind': 'mocks'})).get('id')

        # ---- A. Healthy.
        ok = await written(own, sec, 'W healthy', photos=2); n = len(sb.calls)
        sc, d = await press(own, 'live', [one('set', ok)])
        lists = sum(1 for _, _, p in sb.calls[n:] if p.startswith(LIST)); reads = sum(1 for m, _, p in sb.calls[n:] if m == 'GET' and f'/written/{ok}/' in p)
        check("A. a written mock with photos goes Live, as before; Supabase's own list was asked once and each photo was read back", sc == 200 and d.get('done') == 1 and not d.get('skipped')
              and (await doc(ok)).get('status') == 'published' and (await item(own, sec, ok)).get('status') == 'live' and lists == 1 and reads >= 2, (sc, d, lists, reads))
        typed = await written(own, sec, 'W typed only', plain=2); n = len(sb.calls)
        sc, d = await press(own, 'live', [one('set', typed)])
        check('A. a typed mock (no photo) goes Live and storage is not asked anything', d.get('done') == 1 and (await doc(typed)).get('status') == 'published' and len(sb.calls) == n, (d, sb.calls[n:]))

        # ---- B. A photo that is not proven.
        bad = await lost(own, sec, sb, 'W photo lost')
        fid = (await FILES.find_one({'set_id': bad}))['id']
        r = await own.get(f'{M}/written/{bad}/images/{fid}')
        check('B. setup: the photo has a record, is not in Supabase, and the editor cannot show it', r.status_code == 503 and not any(f'/written/{bad}/' in k for k in sb.objects), r.status_code)
        sc, d = await press(own, 'live', [one('set', bad)]); why = why_of(d)
        check('B. Live karo: a normal answer (no error page); the mock is skipped with its reason', sc == 200 and d.get('done') == 0 and len(d.get('skipped', [])) == 1 and d['skipped'][0]['id'] == bad, (sc, d))
        check('B. the reason names the question, says it is not Live and what to do', why.startswith(f'Q2 {GONE}, {NOT_LIVE}') and AGAIN in why, why)
        check('B. the mock is a plain Draft; students cannot see it', plain_draft(await doc(bad)) and (await item(own, sec, bad)).get('status') == 'draft', await doc(bad))
        check('B. Supabase is NOT rested for everyone', S.supabase_on() and S.STATE['strikes'] == 0, S.STATE['strikes'])
        mem = await written(own, sec, 'W gone but remembered', photos=1); fid = (await photos(own, mem))[0][2]
        r1 = await own.get(f'{M}/written/{mem}/images/{fid}'); sb.objects.pop(await key_of(fid)); r2 = await own.get(f'{M}/written/{mem}/images/{fid}')
        sc, d = await press(own, 'live', [one('set', mem)])
        check('B. a photo gone from Supabase that this server still remembers (the editor still shows it): NOT Live', r1.status_code == 200 and r2.status_code == 200 and d.get('done') == 0
              and why_of(d).startswith(f'Q2 {GONE}, {NOT_LIVE}') and plain_draft(await doc(mem)), (r1.status_code, r2.status_code, d))
        chg = await written(own, sec, 'W photo changed', photos=1); sb.objects[await key_of((await photos(own, chg))[0][2])] = png(250)
        sc, d = await press(own, 'live', [one('set', chg)])
        check('B. other bytes at the photo\'s place: NOT Live, said plainly (not "Source region is invalid")', d.get('done') == 0 and why_of(d).startswith(f'Q2 {CHANGED}, {NOT_LIVE}')
              and AGAIN in why_of(d) and plain_draft(await doc(chg)), d)

        # ---- C. One press: the bad mock first, then two written mocks and a PDF mock.
        a, b = await written(own, sec, 'W plain A'), await written(own, sec, 'W plain B')
        _, pm, _ = await book(own, sec, 'w244_pdf')
        sc, d = await press(own, 'live', [one('set', bad), one('set', a), one('set', b), one('book_mock', pm)]); await pump()
        mk = await BM.find_one({'_id': pm})
        check('C. one press with the bad mock first: only it is skipped; both other written mocks and the PDF mock go Live', sc == 200 and d.get('done') == 3 and [x['id'] for x in d.get('skipped', [])] == [bad]
              and GONE in d['skipped'][0]['reason'] and (await doc(a)).get('status') == 'published' and (await doc(b)).get('status') == 'published'
              and mk['state'] == 'published' and plain_draft(await doc(bad)), (sc, d, mk['state'], mk['issues']))
        c, e = await written(own, sec, 'W plain C'), await written(own, sec, 'W plain E')
        sc, d = await press(own, 'live', [one('set', c), one('set', bad), one('set', e)])
        check('C. the bad mock in the middle: the ones before and after it both go Live', sc == 200 and d.get('done') == 2 and [x['id'] for x in d.get('skipped', [])] == [bad]
              and (await doc(c)).get('status') == 'published' and (await doc(e)).get('status') == 'published', (sc, d))

        # ---- D. Schedule.
        at = time.time() + 86400
        sc, d = await press(own, 'scheduled', [one('set', bad)], at=at)
        check('D. Schedule: skipped, the reason says it was not scheduled; no time is left on the Draft', sc == 200 and d.get('done') == 0 and why_of(d).startswith(f'Q2 {GONE}, {NOT_SCHEDULED}') and plain_draft(await doc(bad)), (sc, d, await doc(bad)))
        sc, d = await press(own, 'scheduled', [one('set', bad)], at=at, live_exam=True)
        check('D. Schedule as a live exam: the same; no time, window or live-exam mark is left behind', sc == 200 and d.get('done') == 0 and plain_draft(await doc(bad)), (sc, d, await doc(bad)))
        g = await written(own, sec, 'W healthy scheduled', photos=1)
        sc, d = await press(own, 'scheduled', [one('set', g)], at=at)
        check('D. unchanged: a healthy written mock is Scheduled for the chosen time', d.get('done') == 1 and abs(((await doc(g)).get('start_at') or 0) - at) < 1 and (await item(own, sec, g)).get('status') == 'scheduled', (d, (await doc(g)).get('start_at')))

        # ---- E. The owner adds the photo again.
        r = await mend(own, bad)
        sc, d = await press(own, 'live', [one('set', bad)])
        s = await doc(bad)
        check('E. photo added again + Live karo: it is Live now (not at the time of the Schedule that failed)', r.status_code == 200 and d.get('done') == 1 and s.get('status') == 'published'
              and not s.get('start_at') and (await item(own, sec, bad)).get('status') == 'live', (r.status_code, d, s.get('status'), s.get('start_at')))

        # ---- F. Supabase itself is away when Live is pressed.
        h = await written(own, sec, 'W while Supabase is away', photos=1)
        sb.down = True
        sc, d = await press(own, 'live', [one('set', h), one('set', await written(own, sec, 'W plain F'))]); why = why_of(d)
        sb.down = False
        check('F. Supabase away: the mock with a photo says so and stays Draft; the typed mock of the same press goes Live', sc == 200 and d.get('done') == 1 and [x['id'] for x in d.get('skipped', [])] == [h]
              and why.startswith(AWAY) and NOT_LIVE[:-1] in why and 'phir koshish kijiye' in why and GONE not in why and plain_draft(await doc(h)), (sc, d))
        check('F. Supabase is NOT rested for everyone by this', S.supabase_on() and S.STATE['strikes'] == 0, S.STATE['strikes'])
        sc, d = await press(own, 'live', [one('set', h)])
        check('F. Supabase answers again + Live karo: Live', d.get('done') == 1 and (await doc(h)).get('status') == 'published', d)
        hb = await written(own, sec, 'W while Supabase is blocked', photos=1)
        sb.block = (402, 'TEST: billing')
        sc, d = await press(own, 'live', [one('set', hb)]); why = why_of(d)
        sb.block = None
        check('F. Supabase project blocked (402): the mock says it is the billing block and stays Draft; Supabase is not rested', d.get('done') == 0
              and why.startswith(AWAY + ' project par billing ya usage ki rok hai (402))') and plain_draft(await doc(hb)) and S.supabase_on(), d)
        sb.list_code = 400
        sc, d = await press(own, 'live', [one('set', hb)]); why = why_of(d)
        sb.list_code = None
        check('F. Supabase answers but does not give the list of photos: the mock says so (no photo is called missing) and stays Draft', d.get('done') == 0
              and 'Supabase ne is mock ki photo ki list nahi di (400)' in why and GONE not in why and plain_draft(await doc(hb)), d)
        sc, d = await press(own, 'live', [one('set', hb)])
        check('F. afterwards the same mock goes Live', d.get('done') == 1 and (await doc(hb)).get('status') == 'published', d)

        # ---- G. All India Test Series.
        first = datetime.now(IST).date() + timedelta(days=2)
        days = [(first + timedelta(days=i)).isoformat() for i in range(4)]
        made = J(await own.post(f'/api/admin/catalog/exams/{slug}/sections', json={'name': 'All India Test Series', 'description': '', 'layout': 'list', 'kind': 'aits',
                 'first_date': days[0], 'days': 4, 'open_time': '09:00', 'last_start': '11:00', 'minutes': 10, 'correct': 4, 'wrong': -1}))
        ser, sid = made.get('id'), made.get('series_id')
        await structure.exams.update_one({'_id': slug}, {'$set': {'shown': True}})
        await own.put(f'{M}/series/{sid}', json={'shown': True})
        sbad = await lost(own, ser, sb, 'W series photo lost')
        good = await written(own, ser, 'W series healthy', plain=2)
        r = await own.post(f'{M}/series/{sid}/assign', json={'kind': 'written', 'id': sbad, 'date': days[0]})
        check('G. a day for a paper whose photo is not in storage: refused with the reason (not an error page)', r.status_code == 409 and said(r).startswith(f'Q2 {GONE}, {NO_DAY}') and AGAIN in said(r), (r.status_code, r.text[:300]))
        check('G. the paper does NOT take the day: it is a plain Draft', plain_draft(await doc(sbad)), await doc(sbad))
        view = J(await own.get(f'{M}/series/{sid}'))
        slot = next(x for x in view['slots'] if x['date'] == days[0])
        check("G. Master: that day is empty and the paper is still in the list of papers without a day", slot.get('paper') is None and any(x['id'] == sbad and x['kind'] == 'written' for x in view['candidates']), (slot.get('paper'), [x['id'] for x in view['candidates']]))
        for who, cl in (('a student', stu), ('a visitor', anon)):
            pub = next((x for x in J(await cl.get(f'/api/series/{sid}/schedule')).get('slots', []) if x['date'] == days[0]), {})
            check(f'G. {who} sees no paper on that day', bool(pub) and pub.get('set_id') is None and not pub.get('can_start') and not pub.get('ready'), pub)
        r = await own.post(f'{M}/series/{sid}/fill')
        s_good, s_bad = await doc(good), await doc(sbad)
        check('G. "fill": the paper that is not proven does not stop the next one, which gets its day and is built', r.status_code == 200 and J(r).get('placed') == 1 and s_good.get('status') == 'published'
              and s_good.get('series_date') in days and plain_draft(s_bad), (r.status_code, r.text[:300], s_good.get('series_date'), s_bad.get('status')))
        free = next(x for x in days if x != s_good.get('series_date'))
        sb.down = True
        r = await own.post(f'{M}/series/{sid}/assign', json={'kind': 'written', 'id': sbad, 'date': free})
        sb.down = False
        check('G. Supabase away when a day is given: refused, the paper says so and keeps no day', r.status_code == 409 and said(r).startswith(AWAY) and NO_DAY[:-1] in said(r) and plain_draft(await doc(sbad)), (r.status_code, r.text[:300]))
        r1 = await mend(own, sbad)
        r = await own.post(f'{M}/series/{sid}/assign', json={'kind': 'written', 'id': sbad, 'date': free})
        s_bad = await doc(sbad)
        check('G. photo added again: the paper takes a day and is built for it', r1.status_code == 200 and r.status_code == 200 and s_bad.get('status') == 'published' and s_bad.get('series_date') == free, (r1.status_code, r.status_code, r.text[:200]))

        # ---- H. One mock, one store.
        mix = await written(own, sec, 'W split between stores', photos=2)
        await to_emergent(sb, (await photos(own, mix))[1][2])
        sc, d = await press(own, 'live', [one('set', mix)]); why = why_of(d)
        check('H. photos split between Supabase and Emergent: NOT Live; both counts and the question in the old store are named', d.get('done') == 0
              and why.startswith(f'Is mock ki photo do storage mein bati hain (1 Supabase mein, 1 Emergent mein), {NOT_LIVE} Q3 ki photo purane storage (Emergent) mein hai') and AGAIN in why
              and plain_draft(await doc(mix)), d)
        sc, d = await press(own, 'scheduled', [one('set', mix)], at=at)
        check('H. the same mock cannot be Scheduled either; no time is left behind', d.get('done') == 0 and NOT_SCHEDULED in why_of(d) and plain_draft(await doc(mix)), d)
        r = await mend(own, mix, 3)
        sc, d = await press(own, 'live', [one('set', mix)])
        check('H. that photo removed and added again (it goes to Supabase): the mock goes Live', r.status_code == 200 and d.get('done') == 1 and (await doc(mix)).get('status') == 'published', (r.status_code, d))
        old = await written(own, sec, 'W all in the old store', photos=2); n = len(sb.calls)
        for _, _, fid in await photos(own, old):
            await to_emergent(sb, fid)
        sc, d = await press(own, 'live', [one('set', old)])
        check('H. unchanged: a mock whose photos are all in Emergent (an old one) still goes Live; each is read back from Emergent', d.get('done') == 1 and (await doc(old)).get('status') == 'published'
              and not any(p.startswith(LIST) for _, _, p in sb.calls[n:]), d)
        gone = await written(own, sec, 'W old store photo gone', photos=1); fid = (await photos(own, gone))[0][2]
        await to_emergent(sb, fid); H.STORE.pop((await FILES.find_one({'id': fid}))['path'])
        sc, d = await press(own, 'live', [one('set', gone)])
        check('H. a photo that does not come back from Emergent: NOT Live, the question is named', d.get('done') == 0 and why_of(d).startswith(f'Q2 ki photo storage se padhi nahi ja saki, {NOT_LIVE}') and plain_draft(await doc(gone)), d)

        # ---- I. A mock that is already Live.
        before = await SETS.find_one({'id': ok}, {'_id': 0})
        sb.vanish = [f'/written/{ok}/']; fid = await photo(own, ok, 150); sb.vanish = []
        r = await own.put(f'{M}/written/{ok}/questions', json=mcq('added while Live, photo not kept', image=fid))
        after = await SETS.find_one({'id': ok}, {'_id': 0})
        check('I. Live mock + a new question whose photo is not in storage: refused with the reason (not an error page)', r.status_code == 409 and said(r).startswith(f'Q4 {GONE}, {NOT_SAVED}') and AGAIN in said(r), (r.status_code, r.text[:300]))
        check('I. nothing was saved: the Live paper, its questions, revision and version are as they were', same(before, after), {k: (before.get(k), after.get(k)) for k in ('status', 'revision', 'version')})
        n = len(sb.calls)
        r = await own.put(f'{M}/written/{ok}/questions', json=mcq('typed question changed while Live', id=before['questions'][0]['id']))
        after = await SETS.find_one({'id': ok}, {'_id': 0})
        check('I. unchanged: a text change on the Live mock is saved as a new version; no photo list is asked for it', r.status_code == 200 and after['version'] == before['version'] + 1
              and len(after['questions']) == 3 and not any(p.startswith(LIST) for _, _, p in sb.calls[n:]), (r.status_code, r.text[:200], after['version']))
        fid = await photo(own, ok, 180); n = len(sb.calls)
        r = await own.put(f'{M}/written/{ok}/questions', json=mcq('added while Live with a healthy photo', image=fid))
        now = await SETS.find_one({'id': ok}, {'_id': 0})
        check('I. unchanged: a new question with a healthy photo is saved on the Live mock; only the new photo was proven', r.status_code == 200 and now['version'] == after['version'] + 1 and len(now['questions']) == 4
              and sum(1 for _, _, p in sb.calls[n:] if p.startswith(LIST)) == 1 and sum(1 for m, _, p in sb.calls[n:] if m == 'GET' and fid in p) >= 1, (r.status_code, r.text[:200], sb.calls[n:]))
        fid = await photo(own, ok, 210)
        sb.down = True
        r = await own.put(f'{M}/written/{ok}/questions', json=mcq('added while Supabase is away', image=fid))
        sb.down = False
        check('I. Supabase away at the save: refused, says so, nothing saved; Supabase is not rested for everyone', r.status_code == 409 and said(r).startswith(AWAY) and NOT_SAVED[:-1] in said(r)
              and same(now, await SETS.find_one({'id': ok}, {'_id': 0})) and S.supabase_on() and S.STATE['strikes'] == 0, (r.status_code, r.text[:300]))
        r = await own.delete(f"{M}/written/{ok}/questions/{now['questions'][-1]['id']}")
        end = await SETS.find_one({'id': ok}, {'_id': 0})
        check('I. unchanged: a question is removed from the Live mock as before', r.status_code == 200 and len(end['questions']) == 3 and end['version'] == now['version'] + 1 and end['status'] == 'published', (r.status_code, r.text[:200]))
        # The Live mock's name: this server's memory is emptied first, as after a restart, so its photos must come from Supabase.
        for f in [x async for x in FILES.find({'id': {'$in': end['file_ids']}})]:
            S._source_cache.remove(f['path'])
        sb.down = True
        r = await own.patch(f'{M}/written/{ok}', json={'title': 'W healthy renamed'})
        sb.down = False
        check('I. Supabase away + a new name for the Live mock (its photos are not in this server\'s memory): refused, says so, nothing changed', r.status_code == 409 and said(r).startswith(AWAY)
              and NOT_SAVED[:-1] in said(r) and same(end, await SETS.find_one({'id': ok}, {'_id': 0})) and (await doc(ok)).get('title') == 'W healthy' and S.supabase_on(), (r.status_code, r.text[:300]))
        r = await own.patch(f'{M}/written/{ok}', json={'title': 'W healthy renamed'})
        named = await SETS.find_one({'id': ok}, {'_id': 0})
        check('I. unchanged: Supabase answers again: the new name is saved as a new version', r.status_code == 200 and named['title'] == 'W healthy renamed' and named['version'] == end['version'] + 1, (r.status_code, r.text[:200]))
        fid = await photo(own, old, 190); n = len(sb.calls); was = await SETS.find_one({'id': old}, {'_id': 0})
        r = await own.put(f'{M}/written/{old}/questions', json=mcq('new photo on an old Live mock', image=fid))
        got = await SETS.find_one({'id': old}, {'_id': 0})
        check('I. unchanged: a Live mock whose photos are in the old store still takes a new question with a photo; the new photo is proven in Supabase', r.status_code == 200 and got['version'] == was['version'] + 1
              and len(got['questions']) == len(was['questions']) + 1 and sum(1 for m, _, p in sb.calls[n:] if m == 'GET' and fid in p) >= 1, (r.status_code, r.text[:300]))
        drafted = await lost(own, sec, sb, 'W draft keeps saving')
        check('I. unchanged: a Draft still saves a question whatever its photo (it is checked when it goes Live)', len((await SETS.find_one({'id': drafted}))['questions']) == 2 and plain_draft(await doc(drafted)))

        # ---- K. The paper cannot be made although its photos were proven a moment before.
        from fastapi import HTTPException
        from tejas import content as C
        real = C.publish_validated

        async def storage_gone(*args, **kw):
            raise S.StorageError('TEST: storage stopped answering')

        async def refused(*args, **kw):
            raise HTTPException(400, 'TEST: refused')

        async def with_maker(fake, call):
            C.publish_validated = fake
            try:
                return await call
            finally:
                C.publish_validated = real
        k = await written(own, sec, 'W made after proof', photos=1)
        sc, d = await with_maker(storage_gone, press(own, 'scheduled', [one('set', k)], at=at, live_exam=True))
        check('K. storage stops answering after the proof (Schedule as a live exam): a normal answer with the reason; no time, window or live-exam mark stays on the Draft', sc == 200 and d.get('done') == 0
              and why_of(d).startswith(AWAY) and NOT_SCHEDULED[:-1] in why_of(d) and plain_draft(await doc(k)), (sc, d, await doc(k)))
        sc, d = await with_maker(refused, press(own, 'scheduled', [one('set', k)], at=at))
        check('K. any other refusal while the paper is made: its own reason; the chosen time does not stay on the Draft', sc == 200 and d.get('done') == 0 and why_of(d) == 'TEST: refused' and plain_draft(await doc(k)), (sc, d, await doc(k)))
        sc, d = await press(own, 'live', [one('set', k)])
        s = await doc(k)
        check('K. Live karo afterwards: Live now, not at the time of the Schedule that failed', d.get('done') == 1 and s.get('status') == 'published' and not s.get('start_at'), (d, s.get('status'), s.get('start_at')))
        ks = await written(own, ser, 'W series made after proof', plain=2)
        day3 = next(x for x in days if x not in (s_good.get('series_date'), free))
        r = await with_maker(storage_gone, own.post(f'{M}/series/{sid}/assign', json={'kind': 'written', 'id': ks, 'date': day3}))
        slot = next(x for x in J(await own.get(f'{M}/series/{sid}'))['slots'] if x['date'] == day3)
        check('K. series day, storage stops answering after the proof: refused with the reason (not an error page); the day is given back', r.status_code == 409 and said(r).startswith(AWAY)
              and NO_DAY[:-1] in said(r) and plain_draft(await doc(ks)) and slot.get('paper') is None, (r.status_code, r.text[:300], slot.get('paper')))

        # ---- J. A verified JEE Main PYQ paper is never checked.
        from tejas.written import photo_trouble
        paper = {'id': 'pyq_x', 'test_kind': 'pyq', 'questions': [{'id': 'q', 'number': 1, 'q_refs': [{'file_id': 'no-such-photo'}], 's_refs': []}]}
        n = len(sb.calls)
        r = await photo_trouble({**paper, 'master_pyq': False}, NOT_LIVE[:-1])
        check('J. a verified JEE Main PYQ paper is never checked: no reason is made and storage is not asked', r is None and len(sb.calls) == n, (r, sb.calls[n:]))
        r = await photo_trouble({**paper, 'master_pyq': True}, NOT_LIVE[:-1])
        check('J. a PYQ paper the owner typed in Master is checked like any written mock', (r or '').startswith(f'Q1 {GONE}, {NOT_LIVE}'), r)

        # ---- L. Which questions are named.
        wid = J(await own.post(f'{M}/types/{sec}/written', json={'title': 'W solution and option photos'})).get('id')
        await own.put(f'{M}/written/{wid}/questions', json=mcq('typed first'))
        sb.vanish = [f'/written/{wid}/']
        r1 = await own.put(f'{M}/written/{wid}/questions', json=mcq('solution photo lost', solution_image=await photo(own, wid, 30)))
        r2 = await own.put(f'{M}/written/{wid}/questions', json=mcq('option photo lost', options=[{'text': '', 'image': await photo(own, wid, 60)}, {'text': 'two', 'image': ''}], answer='A'))
        sb.vanish = []
        sc, d = await press(own, 'live', [one('set', wid)])
        check('L. a solution photo and an option photo that are not in storage: both questions are named', r1.status_code == 200 and r2.status_code == 200 and d.get('done') == 0
              and why_of(d).startswith(f'Q2, Q3 {GONE}, {NOT_LIVE}') and plain_draft(await doc(wid)), (r1.status_code, r2.status_code, d))
        two = await written(own, sec, 'W one gone one changed', photos=2); ph = await photos(own, two)
        sb.objects.pop(await key_of(ph[0][2])); sb.objects[await key_of(ph[1][2])] = png(251)
        sc, d = await press(own, 'live', [one('set', two)])
        check('L. one photo gone and another changed: each is said in its own words', d.get('done') == 0 and why_of(d).startswith(f'Q2 {GONE}; Q3 {CHANGED}, {NOT_LIVE}') and plain_draft(await doc(two)), d)
        many = J(await own.post(f'{M}/types/{sec}/written', json={'title': 'W twelve photos lost'})).get('id')
        sb.vanish = [f'/written/{many}/']
        for i in range(12):
            await own.put(f'{M}/written/{many}/questions', json=mcq(f'photo question {i + 1}', image=await photo(own, many, 10 + i)))
        sb.vanish = []
        sc, d = await press(own, 'live', [one('set', many)])
        ten = ', '.join(f'Q{i}' for i in range(1, 11))
        check('L. twelve photos not in storage: ten questions are named, then "aur baaki"', d.get('done') == 0 and why_of(d).startswith(f'{ten} aur baaki {GONE}, {NOT_LIVE}') and plain_draft(await doc(many)), d)
    finally:
        cancel_kicks()
        assert H.TEST_DB.startswith('tejas_isolated_') and H.TEST_DB != H.REAL_DB
        await H.tdbmod.client.drop_database(H.TEST_DB)
        print('dropped', H.TEST_DB)
    print(f'TOTAL {len(RESULTS)} PASS {sum(RESULTS)} FAIL {len(RESULTS) - sum(RESULTS)}')


if __name__ == '__main__':
    asyncio.run(main())
