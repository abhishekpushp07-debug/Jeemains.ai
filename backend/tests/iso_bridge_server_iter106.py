"""TEST-ONLY MOCKED/ISOLATED browser bridge (iteration 106). NOT production evidence.
Extends iso_bridge_server (iter105) seed: source-image refs (bytes are served by a Playwright route
intercept, never the vault), a saved AI tag on Day-1 Q1 (no AI call), and one READY private JEE import
(revision 0, no set) for the owner-studio assignment UI. DB `tejas_isolated_iter105_test`, port 8765,
clock 2 Dec 2026 10:00 IST. Run: cd /app/backend/tests && python iso_bridge_server_iter106.py &
"""
import asyncio, copy, uuid
import uvicorn
import iso_bridge_server as B
import iso_harness as H

_orig_jq = B.jee_questions


def jq_with_images():
    qs = _orig_jq()
    for q in qs[:2] + qs[25:26]:  # Physics Q1-2 (MCQ) and Chemistry Q1 rendered from source
        q.update(render_mode='source', q_refs=[{'page': 1, 'file_id': 'TEST_F_q' + str(q['number'])}],
                 s_refs=[{'page': 2, 'file_id': 'TEST_F_s' + str(q['number'])}],
                 accessible_text=f"TEST accessible source text {q['number']}", solution_accessible_text='TEST accessible solution text')
    return qs


B.jee_questions = jq_with_images
import tejas.content as _content, tejas.attempts as _attempts


async def _refs_membership_only(s, q, source_map=None):
    """TEST-ONLY: keep the set-membership check, skip vault crop rendering (bytes come from Playwright intercept)."""
    for key in ('q_refs', 's_refs'):
        for r in q.get(key, []):
            if r.get('file_id') not in s.get('file_ids', []):
                from fastapi import HTTPException
                raise HTTPException(400, 'Source region must belong to this set.')
_content.validate_refs = _refs_membership_only
if hasattr(_attempts, 'validate_refs'):
    _attempts.validate_refs = _refs_membership_only
_orig_mk = B.mkpaper


def mk_with_files(title, **over):
    s = _orig_mk(title, **over)
    s['file_ids'] = [r['file_id'] for q in s['questions'] for k in ('q_refs', 's_refs') for r in q.get(k, [])]
    return s


B.mkpaper = mk_with_files


async def seed106():
    await B.seed()
    from tejas.manual_solutions import fingerprint
    p1 = await H.TDB.tejas_sets.find_one({'id': B.SEED['p1']}, {'_id': 0})
    q = next(x for x in p1['questions'] if x['number'] == 3)  # supplied-solution MCQ (even index)
    tag = {'key': q['answer'], 'agrees': True, 'content_hash': fingerprint(q), 'solution': {
        'concept': 'TEST concept: kinetic energy $K=\\frac{1}{2}mv^2$', 'given': ['$m=2\\,\\text{kg}$', '$v=3\\,\\text{m/s}$'],
        'steps': [{'title': '1. Substitute', 'explanation': '$K=\\frac{1}{2}(2)(3)^2$'}, {'title': '2. Evaluate', 'explanation': '$K=9\\,\\text{J}$'}],
        'final_answer': q['answer'], 'insight': 'TEST insight', 'shortcut': 'TEST shortcut', 'common_mistakes': ['Forgetting the $\\frac{1}{2}$'], 'time_tip': 'TEST time tip'}}
    await H.TDB.tejas_sets.update_one({'id': p1['id'], 'questions.id': q['id']}, {'$set': {'questions.$.ai_solution': tag}})
    iid = str(uuid.uuid4()); qs = []
    for x in _orig_jq():
        x = {k: x[k] for k in ('number', 'subject', 'type', 'text', 'answer', 'solution', 'render_mode', 'q_refs', 's_refs')}
        x['id'] = str(uuid.uuid5(uuid.UUID(iid), str(x['number'])))
        x['options'] = {'A': '1', 'B': '2', 'C': '3', 'D': '4'} if x['type'] == 'mcq' else {}
        x.update(approved=False, accessible_text=x['text'], solution_accessible_text=x['solution'], issues=[])
        qs.append(x)
    await H.TDB.tejas_imports.insert_one({'id': iid, 'title': 'TEST Private Series Import', 'format': 'pdf', 'fingerprint': 'TEST', 'sources': [],
        'status': 'ready', 'created_at': H.CLOCK[0], 'created_by': 'TEST_U_owner', 'questions': qs, 'issues': [], 'exam': 'JEE Main',
        'duration_minutes': 180, 'rights_attested_at': H.CLOCK[0], 'rights_attested_by': 'TEST_U_owner', 'message': 'TEST ready'})
    B.SEED.update(imp=iid, tagq=q['id'])
    print('SEED106', B.SEED, flush=True)


if __name__ == '__main__':
    asyncio.set_event_loop(asyncio.new_event_loop())
    server = uvicorn.Server(uvicorn.Config(H.app, host='127.0.0.1', port=8765, log_level='warning', lifespan='off'))
    loop = asyncio.get_event_loop()
    loop.run_until_complete(seed106())
    loop.run_until_complete(server.serve())
