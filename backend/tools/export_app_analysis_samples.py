"""Real Analysis 2.0 payloads for the app packet, read from the TEST-ONLY analysis bridge (disposable DB, synthetic students).
Run: cd /app/backend && python tests/analysis_bridge196.py 900 &  then  python tools/export_app_analysis_samples.py <out_dir>"""
import json, os, sys
import requests

B = os.environ.get('BRIDGE', 'http://127.0.0.1:8773')
ORIGIN = os.environ.get('BRIDGE_ORIGIN', 'https://tejas-route2--1yaz6hh9.preview.emergentagent.com')
CFG = json.load(open(os.environ.get('BRIDGE_JSON', '/tmp/uibridge196/bridge.json')))
OUT = sys.argv[1]
os.makedirs(OUT, exist_ok=True)


def session(cookies):
    s = requests.Session()
    s.headers.update({'Origin': ORIGIN, 'Cookie': '; '.join(f'{k}={v}' for k, v in cookies.items())})
    return s


def save(name, method, path, r, body=None, note=None):
    try:
        data = r.json()
    except ValueError:
        data = {'binary': True, 'bytes': len(r.content)}
    keep = {k: r.headers.get(k) for k in ('content-type', 'cache-control', 'content-disposition', 'retry-after') if r.headers.get(k)}
    doc = {'request': {'method': method, 'path': path, **({'body': body} if body is not None else {})}, 'status': r.status_code, 'headers': keep, 'response': data}
    if note:
        doc['note'] = note
    with open(os.path.join(OUT, name + '.json'), 'w') as fh:
        json.dump(doc, fh, indent=1, ensure_ascii=False)
    print(name, r.status_code, len(r.content))
    return data


def call(s, name, method, path, body=None, note=None):
    r = s.request(method, B + '/api' + path, json=body, timeout=60)
    return save(name, method, path, r, body, note)


hero, old = session(CFG['hero']), session(CFG['old'])
aid, oid = CFG['hero_attempt'], CFG['old_attempt']
call(hero, '01_analysis_personal', 'GET', f'/attempts/{aid}/analysis')
for target in ('topper', 'top10', 'average'):
    call(hero, f'02_analysis_compare_{target}', 'GET', f'/attempts/{aid}/analysis?mode=comparative&compare={target}')
board = call(hero, '03_leaderboard', 'GET', f'/attempts/{aid}/leaderboard')
rows = ((board or {}).get('data') or board or {}).get('rows') or []
other = next((r for r in rows if not r.get('is_you')), None)
if other:
    call(hero, '02_analysis_compare_user', 'GET', f"/attempts/{aid}/analysis?mode=comparative&compare=user:{other['handle']}")
call(hero, '03_leaderboard_search_rank', 'GET', f'/attempts/{aid}/leaderboard?q=1')
call(hero, '04_analysis_questions_wrong', 'GET', f'/attempts/{aid}/analysis/questions?filter=wrong')
call(hero, '05_learnings_save', 'PUT', f'/attempts/{aid}/learnings', {'items': ['Easy sawaal pehle round mein', 'Par ke 2 guna se zyada nahi', '']})
r = hero.get(B + f'/api/attempts/{aid}/analysis/report.pdf', timeout=120)
save('06_report_pdf', 'GET', f'/attempts/{aid}/analysis/report.pdf', r, note='Binary PDF (A4). Save it to a file and open it with the phone PDF viewer.')
r = hero.get(B + f'/api/attempts/{aid}/analysis/share.png', timeout=120)
save('07_share_png', 'GET', f'/attempts/{aid}/analysis/share.png', r, note='Binary PNG scorecard for WhatsApp share. Never contains the phone number.')
call(old, '08_analysis_without_time_record', 'GET', f'/attempts/{oid}/analysis',
     note='An attempt with no time record (older app or website build): time_data false; Time, Attempt Quality and Journey show the "Agle mock se shuru hoga" card.')
if other:
    call(hero, '09_competition_compare_learner', 'GET', f"/competitions/{CFG['set']}/compare/{other['handle']}",
         note='Only for live competition papers (competition_end set). On a practice paper this answers 404 like here.')
call(hero, '10_display_name_set', 'PUT', '/profile/display-name', {'name': 'Arjun'})
call(hero, '11_results_trimmed', 'GET', f'/attempts/{aid}/results')
path = os.path.join(OUT, '11_results_trimmed.json')
doc = json.load(open(path))
d = doc['response'].get('data') or doc['response']
if isinstance(d, dict) and isinstance(d.get('questions'), list):
    d['questions'] = d['questions'][:2]
    doc['note'] = 'questions[] cut to the first 2 for size.'
json.dump(doc, open(path, 'w'), indent=1, ensure_ascii=False)
