"""TEST-ONLY (iteration 212 T1): misfire.sync never starves newer/older papers behind papers still being graded (student bridge 8773).
Clones hero's graded attempt as K newer 'completed' attempts without a ledger (still grading), un-syncs the real paper, and checks
GET /api/my/misfire/summary: real paper taken, pending clones not counted in 'waiting'. Removes the clones (by id) afterwards.
Run: python tests/misfire_sync212.py"""
import json, subprocess, uuid
import requests

S = 'http://127.0.0.1:8773'
B = json.load(open('/tmp/uibridge196/bridge.json'))
DBN = [l for l in open('/tmp/bridge196.log') if l.startswith('READY')][-1].split()[1]
R = []


def ok(n, c, d=''):
    R.append(c); print(('PASS ' if c else 'FAIL ') + n + ('' if c else ' :: ' + str(d)[:400]), flush=True)


def mongo(js):
    return subprocess.run(['mongosh', '--quiet', DBN, '--eval', js], capture_output=True, text=True).stdout.strip()


hero = requests.Session(); hero.headers['Cookie'] = '; '.join(f'{k}={v}' for k, v in B['hero'].items())
AID = B['hero_attempt']


def summary():
    r = hero.get(f'{S}/api/my/misfire/summary'); j = r.json(); return r.status_code, j.get('data', j)


def run(k):
    clones = [f'TEST_ms212_{uuid.uuid4().hex[:10]}' for _ in range(k)]
    mongo("const a=db.tejas_attempts.findOne({id:'%s'}); delete a._id; delete a.ledger; const ids=%s;"
          "ids.forEach((id,i)=>{const c=Object.assign({},a,{id:id,start_key:id,start_request_keys:[id],mode:'TEST_m'+id,submitted_at:a.submitted_at+60+i});db.tejas_attempts.insertOne(c);})" % (AID, json.dumps(clones)))
    n = mongo("db.tejas_attempts.countDocuments({id:{$in:%s}})" % json.dumps(clones)); ok(f'{k} clones inserted', n == str(k), n)
    mongo("db.tejas_misfire_sync.deleteOne({_id:'%s'})" % AID)
    try:
        code, d = summary()
        synced = mongo("db.tejas_misfire_sync.countDocuments({_id:'%s'})" % AID)
        clone_synced = mongo("db.tejas_misfire_sync.countDocuments({_id:{$in:%s}})" % json.dumps(clones))
        print(k, 'clones -> summary', code, {x: d.get(x) for x in ('open', 'fixed', 'waiting')}, 'real synced', synced, 'clones synced', clone_synced)
        return code, d, synced, clone_synced
    finally:
        mongo("db.tejas_attempts.deleteMany({id:{$in:%s}})" % json.dumps(clones))
        mongo("db.tejas_misfire_sync.deleteMany({_id:{$in:%s}})" % json.dumps(clones))


code, base = summary(); print('baseline', {x: base.get(x) for x in ('open', 'fixed', 'waiting')})
ok('baseline summary 200, waiting 0', code == 200 and base.get('waiting') == 0, base)
code, d, synced, cs = run(15)
ok('15 pending: summary 200', code == 200, d)
ok('15 pending: real paper behind them is taken (not starved)', synced == '1', synced)
ok('15 pending: pending clones not marked synced', cs == '0', cs)
ok('15 pending: waiting == 0 (pending not counted)', d.get('waiting') == 0, d.get('waiting'))
ok('15 pending: open count unchanged (idempotent upsert)', d.get('open') == base.get('open'), (d.get('open'), base.get('open')))
code, d, synced, cs = run(40)
ok('40 pending (> BATCH*3): summary 200 (no crash)', code == 200, d)
ok('40 pending: clones not marked synced', cs == '0', cs)
print('INFO 40 pending: real paper synced =', synced, 'waiting =', d.get('waiting'), '(papers past the 36-paper window wait for later visits)')
# make sure the real paper ends synced again
code, d = summary(); ok('final: waiting 0 and real paper synced', d.get('waiting') == 0 and mongo("db.tejas_misfire_sync.countDocuments({_id:'%s'})" % AID) == '1', d)
print('TOTAL', len(R), 'PASS', sum(R), 'FAIL', len(R) - sum(R))
