"""TEST-ONLY iteration 195: Analysis 2.0 end to end in an isolated disposable DB (storage + AI mocked, customer DB never written).
Run: cd /app/backend && python tests/analysis_iso195.py   (prints PASS/FAIL, saves the report PDF and scorecard in /tmp/analysis195, drops its DB)
"""
import asyncio, json, os, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import analysis_fixture195 as F  # noqa: E402
from book_publishing_iso170 import H, mkstaff, check, RESULTS  # noqa: E402

OUT = '/tmp/analysis195'


async def main():
    os.makedirs(OUT, exist_ok=True)
    check('no customer DB handles', not H.leftover_real_handles(), H.leftover_real_handles())
    f = await F.build()
    hero, aid = f['hero'], f['hero_attempt']
    number = {q['id']: q['number'] for q in f['questions']}
    tl = f['hero_timeline']
    check('time record stored once, resend changes nothing', tl['first'] == 200 and tl['again'] == 200 and tl['count'] == tl['sent'] and tl['cursor'] == tl['cursor_again'] == tl['sent'], tl)

    r, an = await F.analysis(hero, aid)
    check('analysis opens', r.status_code == 200 and an, r.text[:300])
    qs = {q['number']: q for q in an['questions']}
    o = an['overview']
    check('version 2 with time data', an['analysis_version'] == 2 and an['time_data'] is True)
    wrong_tags = {n: (qs[n]['tag'], t) for n, t in F.HERO_TAGS.items() if qs[n]['tag'] != t}
    check('every scripted tag is right', not wrong_tags, wrong_tags)
    check('every question has exactly one tag', sum(an['quality']['counts'].values()) == 30 and all(q['tag'] for q in an['questions']), an['quality']['counts'])
    check('tag counts', {k: v for k, v in an['quality']['counts'].items() if v} == {'perfect': 16, 'slow_correct': 1, 'wasted': 2, 'concept_gap': 3, 'costly_overtime': 2, 'confused': 1, 'smart_skip': 2, 'not_seen': 3}, an['quality']['counts'])
    check('score and outcomes', (o['score'], o['maximum'], o['correct'], o['incorrect'], o['skipped']) == (61, 120, 17, 7, 6), o)
    led = o['ledger']
    check('marks ledger', (led['earned'], led['negative'], led['left_wrong'], led['left_skipped'], led['no_negative']) == (68, 7, 28, 24, 68) and led['earned'] + led['left_wrong'] + led['left_skipped'] == led['maximum'], led)
    check('verdict line', len(o['verdict']['text']) > 20 and o['verdict']['section'] in ('time', 'quality', 'potential', 'performance'), o['verdict'])
    check('class ready with all 14 students', an['class']['state'] == 'ready' and an['class']['n'] == 14 and an['class']['included'], an['class'])
    check('rank and percentile', 1 <= o.get('rank', 0) <= 14 and o.get('of') == 14 and 0 < o['percentile'] <= 100, {k: o.get(k) for k in ('rank', 'of', 'percentile')})
    d = o['distribution']
    check('score distribution', d and sum(b['count'] for b in d['bins']) == 14 and sum(b['you'] for b in d['bins']) == 1 and d['n'] == 14, d)
    check('3 things for the next mock', 1 <= len(o['next3']) <= 3 and all(x['marks'] > 0 and x['questions'] for x in o['next3']), o['next3'])
    pot = an['potential']
    careless = next(s for s in pot['steps'] if s['key'] == 'careless')
    check('score potential', careless['marks'] == 10 and sorted(number[i] for i in careless['questions']) == [3, 10] and pot['current'] == 61 <= pot['realistic'] <= pot['maximum'] <= 120 and pot['no_negative'] == 68 and pot['guess']['break_even'] == 20, pot)
    check('rank at each target', [x['key'] for x in pot['at']] == ['current', 'realistic', 'maximum'] and all(x.get('rank') for x in pot['at']), pot['at'])
    t = an['time']
    check('time totals', t['available'] and abs(t['on_screen'] - 2495) <= 3 and t['off_screen'] >= 0 and abs(sum(t['by_outcome'].values()) - t['on_screen']) <= 3, {k: t[k] for k in ('elapsed', 'on_screen', 'off_screen', 'by_outcome')})
    look = t['first_look']
    check('first look vs return', look['first']['count'] + look['return']['count'] == 24 and [number[i] for i in look['return']['questions']] == [21] and qs[21]['look'] == 2 and qs[11]['look'] == 1, look)
    check('time share adds up', abs(sum(x['time_pct'] for x in t['share']) - 100) < 0.5 and abs(sum(x['weight_pct'] for x in t['share']) - 100) < 0.5, t['share'])
    check('pace curves', t['pace'][-1] == 24 and t['pace_split']['correct'][-1] == 17 and t['pace_split']['incorrect'][-1] == 7, [t['pace'][-1], t['pace_split']])
    check('slowest five', [number[i] for i in t['slowest']][:2] == [28, 5], [number[i] for i in t['slowest']])
    ch = an['habits']['changes']
    check('answer changes', [number[i] for i in ch['groups']['w2r']] == [11] and [number[i] for i in ch['groups']['r2w']] == [12] and ch['marks'] == 0 and ch['total'] == 2, ch)
    check('streaks', an['habits']['streaks'] and an['habits']['streaks']['correct'] >= 5, an['habits']['streaks'])
    j = an['journey']
    check('journey', j['available'] and j['summary'] == {'visited': 27, 'total': 30, 'revisits': 3, 'thrice': 0} and len(j['visits']) == 30 and j['order'] == ['Physics', 'Chemistry', 'Mathematics'], j['summary'])
    check('journey shows answer change and mark', any(v.get('set') for v in j['visits']) and any(v.get('mark') for v in j['visits']))
    check('question rows', qs[8]['seen'] is False and qs[13]['marked'] is True and qs[11]['changed'] and qs[1]['par'] and qs[1]['par_source'] == 'standard' and qs[21]['visits'] == 2, qs[11])
    with_class = [q for q in an['questions'] if q['class']]
    check('per-question class numbers', len(with_class) == 30 and all(q['class']['n'] == 14 for q in with_class) and any(q['class']['avg_time'] for q in with_class) and any(q['class']['topper_time'] for q in with_class), with_class[0]['class'] if with_class else None)
    diff = an['difficulty']
    check('difficulty levels and where they came from', sum(x['count'] for x in diff['all'].values()) == 30 and diff['sources'].get('paper') == 15 and sum(diff['sources'].values()) == 30, diff['sources'])
    perf = an['performance']
    check('performance', len(perf['subjects']) == 3 and all(len(g['chapters']) == 3 for g in perf['subjects']) and perf['weak'] and perf['subjects'][0]['not_seen'] == 1 and perf['has_chapters'], perf['weak'][:2])
    check('quality extras', sorted(number[i] for i in an['quality']['painful']) == [4, 5, 28] and isinstance(an['quality']['lucky'], list), an['quality']['painful'])

    for target in ('topper', 'top10', 'average'):
        r, c = await F.analysis(hero, aid, f'?mode=comparative&compare={target}')
        c = c['compare']
        gap_ok = c['available'] and abs(c['split_total']['volume'] + c['split_total']['quality'] - c['gap']) <= 0.6
        check(f'compare with {target}', gap_ok and len(c['times'] or {}) == 30 and c['by_subject'] and c['profile']['pace'], {k: c.get(k) for k in ('available', 'gap', 'split_total', 'reason')})
    r = await hero.get(f'/api/attempts/{aid}/leaderboard')
    board = r.json()
    check('leaderboard', r.status_code == 200 and board['state'] == 'ready' and board['n'] == 14 and len(board['rows']) == 14 and [x['score'] for x in board['rows']] == sorted((x['score'] for x in board['rows']), reverse=True)
          and sum(x['is_you'] for x in board['rows']) == 1 and any(x['is_you'] for x in board['around']) and board['you']['rank'] == o['rank'], board.get('you'))
    check('leaderboard never carries answers', '"entry"' not in r.text and '"user_id"' not in r.text and '"o"' not in r.text and 'phone' not in r.text)
    other = next(x for x in board['rows'] if not x['is_you'])
    r, c = await F.analysis(hero, aid, '?mode=comparative&compare=user:' + other['handle'])
    check('compare with any student: totals and times only', c['compare']['available'] and c['compare']['label'].startswith('Learner ') and c['compare']['score'] == other['score'] and len(c['compare']['times']) == 30
          and '"r"' not in r.text and '"entry"' not in r.text, c['compare'].get('reason'))
    r, c = await F.analysis(hero, aid, '?mode=comparative&compare=user:' + '0' * 16)
    check('unknown student is refused politely', c['compare']['available'] is False and c['compare']['reason'])

    # Display name
    r = await hero.put('/api/profile/display-name', json={'name': '  Arjun   11 '})
    check('display name saved', r.status_code == 200 and r.json()['display_name'] == 'Arjun 11', r.text)
    bad = [(await hero.put('/api/profile/display-name', json={'name': n})).status_code for n in ('9876543210', 'x', 'Jeelive Admin', 'a@b', 'chutiya king')]
    check('bad names refused', bad == [422] * 5, bad)
    me = (await hero.get('/api/auth/session')).json()['user']
    check('session carries the name, never as phone', me.get('display_name') == 'Arjun 11', me)
    friend, friend_attempt = f['class'][0]
    await friend.put('/api/profile/display-name', json={'name': 'Riya'})
    r, an2 = await F.analysis(hero, aid)
    board = (await hero.get(f'/api/attempts/{aid}/leaderboard?q=ri')).json()
    check('name on analysis and leaderboard, search by name', an2['student']['name'] == 'Arjun 11' and board['you']['name'] == 'Arjun 11' and board['you']['named'] and [x['name'] for x in board['found']] == ['Riya'], board['found'])
    top = (await hero.get(f'/api/attempts/{aid}/leaderboard?q=1')).json()
    check('search by rank', len(top['found']) == 1 and top['found'][0]['rank'] == 1, top['found'])
    riya = board['found'][0]
    r, c = await F.analysis(hero, aid, '?mode=comparative&compare=user:' + riya['handle'])
    check('compare shows the display name', c['compare']['label'] == 'Riya', c['compare'].get('label'))
    codes = [(await hero.put('/api/profile/display-name', json={'name': f'Arjun {i}'})).status_code for i in range(3)]
    check('at most 3 name changes a day', 429 in codes, codes)
    own, _ = await mkstaff('owner', 'an195')
    listing = (await own.get('/api/admin/students')).json()
    target = next(x for x in listing['items'] if x.get('display_name') == 'Riya')
    r = await own.delete(f"/api/admin/students/{target['id']}/display-name")
    gone = (await friend.get('/api/auth/session')).json()['user']
    check('owner can remove a display name', r.status_code == 200 and not gone.get('display_name'), [r.status_code, gone])
    check('a student cannot remove names', (await hero.delete(f"/api/admin/students/{target['id']}/display-name")).status_code == 403)

    # 3 seekh
    r = await hero.put(f'/api/attempts/{aid}/learnings', json={'items': ['Easy sawaal pehle', '  Negative   se bacho ']})
    check('learnings saved', r.status_code == 200 and r.json()['items'] == ['Easy sawaal pehle', 'Negative se bacho'], r.text)
    codes = [(await hero.put(f'/api/attempts/{aid}/learnings', json={'items': x})).status_code for x in (['a'] * 4, ['x' * 141])]
    check('learnings limits', codes == [422, 422], codes)
    r, an3 = await F.analysis(hero, aid)
    check('learnings come back with the analysis', an3['learnings']['mine'] == ['Easy sawaal pehle', 'Negative se bacho'] and an3['learnings']['previous'] is None, an3['learnings'])
    check('another student cannot write them', (await friend.put(f'/api/attempts/{aid}/learnings', json={'items': ['x']})).status_code == 404)

    # Files
    r = await hero.get(f'/api/attempts/{aid}/analysis/report.pdf')
    ok = r.status_code == 200 and r.content[:5] == b'%PDF-'
    pages = 0
    if ok:
        import fitz
        Path(OUT + '/report.pdf').write_bytes(r.content)
        doc = fitz.open(stream=r.content, filetype='pdf')
        pages = len(doc)
        text = ' '.join(p.get_text() for p in doc)
        ok = 'Arjun' in text and 'Easy sawaal pehle' in text and 'Marks ka hisaab' in text and 'Speed-Accuracy map' in text
    check('report PDF', ok and 7 <= pages <= 14, [r.status_code, pages])
    r = await hero.get(f'/api/attempts/{aid}/analysis/share.png')
    if r.status_code == 200:
        Path(OUT + '/share.png').write_bytes(r.content)
    check('scorecard image', r.status_code == 200 and r.content[:4] == b'\x89PNG', r.status_code)
    r = await hero.get(f'/api/attempts/{aid}/analysis/questions?filter=careless')
    check('question filter', r.status_code == 200 and r.json()['total'] == 2, r.text[:200])

    # Old attempt (no time record) and access
    old, old_attempt = f['old']
    r, an4 = await F.analysis(old, old_attempt)
    check('attempt without a time record', r.status_code == 200 and an4['time_data'] is False and not an4['quality']['available'] and not an4['time']['available'] and not an4['journey']['available']
          and not an4['potential']['available'] and an4['overview']['ledger'] and an4['habits'] and an4['overview'].get('rank'), an4['class'] if an4 else r.text[:200])
    r = await old.get(f'/api/attempts/{old_attempt}/analysis/report.pdf')
    check('report PDF without a time record', r.status_code == 200 and r.content[:5] == b'%PDF-', r.status_code)
    check('another student cannot open it', (await friend.get(f'/api/attempts/{aid}/analysis')).status_code == 404 and (await friend.get(f'/api/attempts/{aid}/leaderboard')).status_code == 404)
    check('signed-out visitor cannot open it', (await F.client().get(f'/api/attempts/{aid}/analysis')).status_code == 401)

    # A new finisher is counted at once in a small class
    late = await F.student()
    late_attempt, _ = await F.sit(late, f['set'], f['questions'], F.random_steps(7))
    r, an5 = await F.analysis(late, late_attempt)
    check('new finisher is counted', an5['class']['state'] == 'ready' and an5['class']['n'] == 15 and an5['overview']['of'] == 15, an5['class'])
    json.dump(an3, open(OUT + '/analysis.json', 'w'))
    bad = [x for x in RESULTS if not x[1]]
    print(f'\n{len(RESULTS) - len(bad)}/{len(RESULTS)} passed', flush=True)


async def run():
    try:
        await main()
    finally:
        await H.tdbmod.client.drop_database(H.TEST_DB)
        print('dropped', H.TEST_DB, flush=True)

asyncio.run(run())
