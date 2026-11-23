"""TEST-ONLY iteration 228 bridge: CEO dashboard API + Mission contacts + usage events on an isolated, throw-away DB.
Clock for the CEO numbers is frozen at 2026-12-14 15:00 IST (AITS day 6). Serves 127.0.0.1:8776; writes /tmp/ceobridge228/bridge.json
(student cookies 'riya' and 'arjun', the test-only CEO key, seeded ids and the expected numbers). The DB is dropped on exit.
Run: cd /app/backend && python tests/ceo_bridge228.py [seconds]
"""
import asyncio, json, os, secrets, sys, uuid
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from book_publishing_iso170 import H  # noqa: E402
import httpx, uvicorn  # noqa: E402
from datetime import date, datetime, timedelta  # noqa: E402
from tejas import live_series, ceo, contacts as contacts_mod, activity  # noqa: E402

OUT = '/tmp/ceobridge228'
KEY = 'TEST_ceo_' + secrets.token_hex(16)
IST = live_series.IST


def ist(d, h=0, m=0):
    return datetime.combine(date.fromisoformat(d), datetime.min.time().replace(hour=h, minute=m), IST).timestamp()


CLOCK = ist('2026-12-14', 15)
BASE = [l.split('=', 1)[1].strip() for l in open('/app/frontend/.env') if l.startswith('REACT_APP_BACKEND_URL')][0].rstrip('/')
DAY = 86400
DAYS = {i: (live_series.FIRST + timedelta(days=i - 1)).isoformat() for i in range(1, 8)}


async def signup(client, phone, web, source=None):
    headers = {'origin': BASE, 'sec-fetch-site': 'same-origin', 'user-agent': 'Mozilla/5.0 (Linux; Android 14) Chrome/131 Mobile'} if web else {}
    body = {'phone': phone, 'pin': '8261', 'confirm_pin': '8261', **({'source': source} if source else {})}
    r = await client.post('/api/auth/phone/signup', json=body, headers=headers)
    assert r.status_code == 200, r.text
    return dict(r.cookies)


def attempt(user, mode, kind, started, submitted=None, score=None, series_date=None, **extra):
    doc = {'id': 'TEST_A228_' + uuid.uuid4().hex[:10], 'user_id': user, 'set_id': 'TEST_set228', 'title': 'TEST paper', 'exam': 'JEE Main',
           'mode': mode, 'test_kind': kind, 'status': 'completed' if submitted else 'active', 'started_at': started, 'submitted_at': submitted,
           'parent_attempt': None, 'grading_status': 'ready' if submitted else None, **extra}
    if score is not None:
        doc['summary'] = {'score': score, 'maximum': 300, 'accuracy': 70.0}
    if series_date:
        doc.update(series_id=live_series.SERIES_ID, series_date=series_date)
    return doc


async def main():
    path = OUT + '/bridge.json'
    try:
        assert not H.leftover_real_handles()
        os.makedirs(OUT, exist_ok=True)
        os.environ['CEO_DASHBOARD_KEY'] = KEY
        T = H.TDB
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=H.app), base_url='http://bridge') as c:
            riya = await signup(c, '9811100001', True, {'utm_source': 'insta', 'utm_campaign': 'aits_launch', 'landing': '/series/all-india-jee'})
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=H.app), base_url='http://bridge') as c:
            arjun = await signup(c, '9811100002', False)
        p1 = (await T.tejas_phone_profiles.find_one({'phone': '+919811100001'}))['id']
        p2 = (await T.tejas_phone_profiles.find_one({'phone': '+919811100002'}))['id']
        await T.tejas_phone_profiles.update_one({'id': p1}, {'$set': {'name': 'Riya S228', 'display_name': 'Riya S228', 'created_at': CLOCK - 2 * 3600, 'last_active_at': CLOCK - 600}})
        await T.tejas_phone_profiles.update_one({'id': p2}, {'$set': {'name': 'Arjun S228', 'display_name': 'Arjun S228', 'created_at': ist('2026-12-08', 10), 'last_active_at': CLOCK - DAY}})
        p3, p4, p5, staff = (str(uuid.uuid4()) for _ in range(4))
        base = {'exam': 'JEE Main', 'pin_hash': 'x', 'pin_version': 1}
        await T.tejas_phone_profiles.insert_many([
            {**base, 'id': p3, 'phone': '+919811100003', 'name': 'Meera S228', 'display_name': 'Meera S228', 'created_at': CLOCK - 10 * DAY,
             'consent_at': CLOCK - 10 * DAY, 'last_seen_at': CLOCK - 10 * DAY, 'signup_channel': 'web', 'signup_device': 'desktop', 'blocked_at': CLOCK - DAY},
            {**base, 'id': p4, 'phone': '+919811100004', 'name': 'Kabir S228', 'display_name': 'Kabir S228', 'created_at': CLOCK - 40 * DAY,
             'consent_at': CLOCK - 40 * DAY, 'last_seen_at': CLOCK - 5 * DAY},
            {**base, 'id': p5, 'phone': '+919811100005', 'name': 'TEST_hidden228', 'display_name': 'TEST_hidden228', 'created_at': CLOCK - 3600,
             'consent_at': CLOCK - 3600, 'last_seen_at': CLOCK - 3600, 'signup_channel': 'web'}])
        await T.tejas_users.insert_one({'id': staff, 'email': 'staff228@test.invalid', 'role': 'owner', 'name': 'Staff 228'})
        rows = [attempt(p1, 'practice', 'mock', CLOCK - 3600, CLOCK - 1800, 150),
                attempt(p1, 'series_live', 'mock', ist(DAYS[6], 9), ist(DAYS[6], 12), 180, DAYS[6])]
        for day, score in zip(range(1, 6), (120, 140, 160, 150, 170)):
            rows.append(attempt(p2, 'series_live', 'mock', ist(DAYS[day], 1), ist(DAYS[day], 4), score, DAYS[day]))
        rows.append(attempt(p2, 'series_live', 'mock', ist(DAYS[6], 14), None, None, DAYS[6]))
        rows += [attempt(p4, 'series_live', 'mock', ist(DAYS[1], 8), ist(DAYS[1], 11), 90, DAYS[1]),
                 attempt(p4, 'series_live', 'mock', ist(DAYS[3], 8), ist(DAYS[3], 11), 110, DAYS[3]),
                 attempt(p4, 'series_practice', 'mock', ist(DAYS[4], 8), ist(DAYS[4], 11), 100, DAYS[2]),
                 attempt(p4, 'practice', 'chapter', CLOCK - 20 * DAY, CLOCK - 20 * DAY + 900, 40, grading_status='failed'),
                 attempt(staff, 'series_live', 'mock', ist(DAYS[6], 10), ist(DAYS[6], 11), 299, DAYS[6]),
                 attempt(p5, 'practice', 'mock', CLOCK - 1800, CLOCK - 600, 250)]
        await T.tejas_attempts.insert_many(rows)
        await T.tejas_sets.insert_many([{'id': f'TEST_S228_day{d}', 'title': f'TEST_All India JEE Mains · Test {d:02d}', 'series_id': live_series.SERIES_ID,
                                         'series_date': DAYS[d], 'status': 'published', 'exam': 'jee-main', 'test_kind': 'mock', 'questions': []} for d in range(1, 7)])
        await T.tejas_invite_contacts.insert_many([
            {'id': 'TEST_C228_1', 'user_id': p2, 'phone': '+919811100001', 'name': 'Riya friend', 'at': CLOCK - 3 * DAY, 'consent': contacts_mod.CONSENT},
            {'id': 'TEST_C228_2', 'user_id': p2, 'phone': '+919822200001', 'name': 'Dost One', 'at': CLOCK - 3600, 'consent': contacts_mod.CONSENT},
            {'id': 'TEST_C228_3', 'user_id': p2, 'phone': '+919811100003', 'name': 'Meera old', 'at': CLOCK - 2 * DAY, 'consent': contacts_mod.CONSENT}])
        await T.tejas_events.insert_many([
            {'id': 'TEST_E228_1', 'name': 'page_open', 'at': CLOCK - 900, 'user_id': p1, 'vid': None, 'props': {'page': 'rank'}},
            {'id': 'TEST_E228_2', 'name': 'rank_tool_open', 'at': CLOCK - 800, 'user_id': p1, 'vid': None, 'props': {'tool': 'cutoff'}},
            {'id': 'TEST_E228_3', 'name': 'page_open', 'at': CLOCK - 700, 'user_id': None, 'vid': 'v-visitor-228a', 'props': {'page': 'landing'}},
            {'id': 'TEST_E228_4', 'name': 'page_open', 'at': CLOCK - 600, 'user_id': staff, 'vid': None, 'props': {'page': 'home'}}])
        ceo.now = contacts_mod.now = activity.now = lambda: CLOCK
        expect = {
            'summary': {'students.total': 4, 'students.blocked': 1, 'by_signup_channel': {'web': 2, 'app': 1, 'other': 0},
                        'signups': {'today': 1, 'last_7_days': 2, 'last_30_days': 3}, 'attempts_today': {'started': 3, 'completed': 2},
                        'aits_today': {'day': 6, 'live_started': 2, 'live_completed': 1}, 'contacts': {'students_who_shared': 1, 'total': 3, 'today': 1}},
            'aits': {'streak_now_at_least.1': 2, 'best_streak_at_least.1': 3, 'best_streak_at_least.7': 0, 'day1.live_completed': 2,
                     'day2.practice_completed': 1, 'day2.day1_people_still_here_pct': 50.0, 'day3.day1_people_still_here_pct': 100.0,
                     'day6.live_started': 2, 'day6.live_completed': 1, 'papers_ready': 6, 'next_day_without_paper': DAYS[7], 'stage': 'live'},
            'funnel_default_30d': {'signed_up': 3, 'started_in_24h': 2, 'completed_in_24h': 2, 'second_test_in_7d': 2, 'never_started': 1},
            'student_arjun': {'aits.current_streak': 5, 'aits.best_streak': 5, 'contacts_shared': 3},
            'contacts_list': {'total': 3, 'Riya friend': {'already_student': True, 'joined_after_share': True}, 'Meera old': {'already_student': True, 'joined_after_share': False},
                              'Dost One': {'already_student': False}},
            'alerts': {'level': 'red', 'codes_include': ['aits_tomorrow_no_paper', 'grading_failed']},
            'excluded_everywhere': ['TEST_hidden228 (+919811100005)', 'staff id ' + staff]}
        with open(path, 'w') as fh:
            json.dump({'riya': riya, 'arjun': arjun, 'ceo_key': KEY, 'ids': {'riya': p1, 'arjun': p2, 'meera': p3, 'kabir': p4, 'test_hidden': p5, 'staff': staff},
                       'clock': CLOCK, 'today_ist': DAYS[6], 'expect': expect}, fh, indent=1)
        os.chmod(path, 0o600)
        print('READY', H.TEST_DB, flush=True)
        server = uvicorn.Server(uvicorn.Config(H.app, host='127.0.0.1', port=8776, log_level='warning', lifespan='off'))
        try:
            await asyncio.wait_for(server.serve(), int(sys.argv[1]) if len(sys.argv) > 1 else 900)
        except asyncio.TimeoutError:
            pass
    finally:
        assert H.TEST_DB.startswith('tejas_isolated_') and H.TEST_DB != H.REAL_DB
        await H.tdbmod.client.drop_database(H.TEST_DB)
        try:
            os.unlink(path)
        except OSError:
            pass
        print('dropped', H.TEST_DB, flush=True)

asyncio.run(main())
