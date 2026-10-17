"""Behavioral ingress checks: real HTTP/ASGI and actual JS, no pretend checks."""
import asyncio
import base64
import copy
import json
import subprocess
from pathlib import Path
import pytest
from fastapi import FastAPI

pytestmark = pytest.mark.asyncio(loop_scope='session')
ROOT = Path(__file__).resolve().parents[2]


async def ingress(messages=(), headers=(), method='POST', path='/api/auth/phone', receive_fn=None, query=b''):
    from server import app
    from tejas.http_limits import JsonBodyLimits
    sent, forwarded = [], []
    iterator = iter(messages)
    async def receive():
        return next(iterator)
    async def send(message):
        sent.append(message)
    async def downstream(scope, receive, send):
        forwarded.append(True)
        if method == 'POST':
            forwarded.append(await receive())
    scope = {'type': 'http', 'method': method, 'path': path, 'headers': list(headers), 'query_string': query}
    await JsonBodyLimits(downstream, contracts=app.state.route_contracts)(scope, receive_fn or receive, send)
    status = next((m['status'] for m in sent if m['type'] == 'http.response.start'), None)
    return status, forwarded, sent


def chunk(body, more=False):
    return {'type': 'http.request', 'body': body, 'more_body': more}


async def test_all_routes_contracts_and_schema_refs(http_client):
    from server import app
    spec = (await http_client.get('/api/openapi.json')).json()
    operations = [(path, method, op) for path, methods in spec['paths'].items() for method, op in methods.items() if method in ('get','post','put','patch','delete')]
    actual = {(c.route.path, m.lower()) for c in app.state.route_contracts for m in c.route.methods}
    assert {(p,m) for p,m,_ in operations} == actual
    assert len(operations) == 75  # 73 established operations plus exam-scoped catalogue and owned history reads.
    def check_refs(value):
        if isinstance(value, dict):
            if '$ref' in value:
                target = spec
                for part in value['$ref'][2:].split('/'):
                    target = target[part]
                assert target is not None
            for child in value.values():
                check_refs(child)
        elif isinstance(value, list):
            for child in value:
                check_refs(child)
    check_refs(spec)
    for _,_,op in operations:
        for name in ('x-owner-policy','x-role-scope','x-workload-tier','x-idempotency-mode','x-body-limit-bytes'):
            assert name in op
    for c in app.state.route_contracts:
        if c.json_body:
            assert c.model.model_config['extra'] == 'forbid'
            assert c.model.model_config['strict'] is True
            schema = c.model.model_json_schema()
            assert schema['additionalProperties'] is False
            for nested in schema.get('$defs', {}).values():
                if nested.get('type') == 'object':
                    assert nested['additionalProperties'] is False
    assert spec['paths']['/api/studio/reviewers']['post']['x-role-scope'] == ['owner']
    assert spec['paths']['/api/studio/sets']['post']['x-role-scope'] == ['owner', 'reviewer']
    assert spec['paths']['/api/auth/preferences']['patch']['x-role-scope'] == ['authenticated_profile']
    assert spec['paths']['/api/studio/sets/{id}/files']['post']['x-body-limit-bytes'] == 0


async def test_unlisted_and_missing_model_fail_startup(monkeypatch):
    from tejas.route_contracts import install_contracts, SPEC
    app = FastAPI()
    @app.post('/api/unlisted')
    async def unlisted(data: dict):
        return data
    with pytest.raises(RuntimeError, match='lacks an explicit local contract'):
        install_contracts(app)
    key = unlisted.__module__.split('.')[-1] + '.unlisted'
    monkeypatch.setitem(SPEC, key, ('test', 'normal', 'none'))
    with pytest.raises(RuntimeError, match='lacks an explicit input model'):
        install_contracts(app)


@pytest.mark.parametrize('body', [
    {'phone': '+12025550184', 'role': 'owner'}, {'phone': 12025550184},
    {'phone': '+12025550184', 'password': 'SYNTHETIC-NOT-A-SECRET'},
])
async def test_phone_exact_fields_no_value_echo(http_client, body):
    r = await http_client.post('/api/auth/phone', json=body)
    assert r.status_code == 422
    assert r.json()['error']['code'] == 'validation_error'
    for value in ('12025550184','owner','SYNTHETIC-NOT-A-SECRET'):
        assert value not in r.text


@pytest.mark.parametrize('revision,marked', [('1',False),(True,False),(1,'false'),(1,1)])
async def test_answer_boolean_integer_types(http_client, revision, marked):
    r = await http_client.put('/api/attempts/test/answers/test', json={'value':'1','revision':revision,'marked':marked,'request_id':'test-key-123'})
    assert r.status_code == 422


async def test_no_content_type_valid_body(http_client, staff_session):
    r = await http_client.post('/api/studio/sets', content=b'{"title":"Synthetic ingress practice"}', cookies=staff_session['cookies'])
    assert r.status_code == 200
    assert r.json()['data']['title'] == 'Synthetic ingress practice'


@pytest.mark.parametrize('headers,status', [
    ([(b'content-length',b'5000')],413),
    ([(b'content-length',b'-1')],400),
    ([(b'content-length',b'2'),(b'content-length',b'2')],400),
    ([(b'content-type',b'application/json'),(b'content-type',b'application/json')],400),
    ([(b'content-type',b'text/plain')],415),
    ([(b'content-type',b'application/x-www-form-urlencoded')],415),
    ([(b'content-encoding',b'gzip')],415),
])
async def test_rejection_before_receive(headers,status):
    async def forbidden():
        raise RuntimeError('Body receive must not occur')
    actual, downstream, _ = await ingress(headers=headers, receive_fn=forbidden)
    assert actual == status and downstream == []


async def test_chunked_oversize_without_headers():
    status, forwarded, _ = await ingress([chunk(b' ' * 2048, True),chunk(b' ' * 2049)])
    assert status == 413 and forwarded == []


async def test_declared_length_mismatch():
    status, forwarded, _ = await ingress([chunk(b'{}')], [(b'content-length',b'3')])
    assert status == 400 and forwarded == []


async def test_timeout_and_disconnect(monkeypatch):
    from tejas import http_limits
    monkeypatch.setattr(http_limits, 'READ_SECONDS', .005)
    async def stalled():
        await asyncio.sleep(.1)
        raise RuntimeError('Timeout should cancel receive')
    status, downstream, _ = await ingress(receive_fn=stalled)
    assert status == 408 and downstream == []
    status, downstream, sent = await ingress([{'type':'http.disconnect'}])
    assert status is None and downstream == [] and sent == []


@pytest.mark.parametrize('body', [b'{"x":1,"x":2}',b'{"x":NaN}',b'{"x":Infinity}',b'{"x":1e400}',b'{"x":"\\ud800"}', b'{"x":"\xed\xa0\x80"}', b'[' * 45 + b'0' + b']' * 45])
async def test_invalid_json_exact_400(body):
    status, downstream, _ = await ingress([chunk(body)])
    assert status == 400 and downstream == []


async def test_get_query_budget_and_no_read():
    async def forbidden():
        raise RuntimeError('GET body must not be read')
    status, downstream, _ = await ingress(method='GET',path='/api/health',receive_fn=forbidden)
    assert status is None and downstream == [True]
    status, downstream, _ = await ingress(method='GET',path='/api/health',query=b'x'*8193,receive_fn=forbidden)
    assert status == 414 and downstream == []


async def test_ingress_error_security_headers_and_origin(http_client):
    bad = await http_client.post('/api/auth/phone', json={'phone':0}, headers={'Origin':'https://testserver'})
    assert bad.status_code == 422
    assert bad.headers['access-control-allow-origin'] == 'https://testserver'
    assert bad.headers['Cache-Control'] == 'private, no-store'
    assert bad.headers['X-Content-Type-Options'] == 'nosniff'
    assert bad.headers['X-Frame-Options'] == 'DENY'
    assert 'X-Request-ID' in bad.headers
    bad_origin = await http_client.post('/api/auth/phone', json={'phone':0}, headers={'Origin':'https://untrusted.invalid'})
    assert bad_origin.status_code == 403 and bad_origin.json()['error']['code'] == 'origin_denied'


def actual_js_payload(function, value):
    source = (ROOT/'frontend/src/lib/studioContracts.js').read_bytes()
    uri = 'data:text/javascript;base64,' + base64.b64encode(source).decode()
    script = 'const m=await import(process.argv[1]); console.log(JSON.stringify(m[process.argv[2]](JSON.parse(process.argv[3]))));'
    result = subprocess.run(['node','--input-type=module','-e',script,uri,function,json.dumps(value)],check=True,capture_output=True,text=True,timeout=10)
    return json.loads(result.stdout)


async def test_actual_js_allowlists():
    value={'id':'private','approved':True,'path':'private/source','issues':['private'], 'number':1,'text':'Question','options':{'1':'One'}}
    assert actual_js_payload('questionPayload',value) == {'number':1,'text':'Question','options':{'1':'One'}}
    settings={'id':'private','jobs':[1],'audit':[1],'questions':[1],'status':'published','title':'Test title','rules':{'minutes':0},'audience':'all'}
    assert actual_js_payload('settingsPayload',settings) == {'title':'Test title','rules':{'minutes':0},'audience':'all'}


async def test_actual_studio_create_read_edit_settings_roundtrip(http_client, staff_session, clean_db):
    http_client.cookies.update(staff_session['cookies'])
    created = await http_client.post('/api/studio/sets',json={'title':'Synthetic Studio ingress','exam':'JEE Main'})
    assert created.status_code == 200
    s = created.json()['data']
    q = await http_client.post('/api/studio/sets/'+s['id']+'/questions',json={})
    assert q.status_code == 200
    # Legacy sets can represent an unset expiry as JSON null; preserve that flow.
    await clean_db.tejas_sets.update_one({'id':s['id']},{'$set':{'expires':None}})
    editor = await http_client.get('/api/studio/sets/'+s['id'])
    assert editor.status_code == 200
    full = editor.json()['data']
    draft = {**q.json()['data'],'text':'Changed text','options':{'1':'One','2':'Two'},'answer':'1','subject':'Physics','solution':'Synthetic explanation','solution_number':1}
    url = '/api/studio/sets/'+s['id']+'/questions/'+draft['id']
    rejected = await http_client.put(url,json=draft)
    assert rejected.status_code == 422
    saved = await http_client.put(url,json=actual_js_payload('questionPayload',draft))
    assert saved.status_code == 200
    assert saved.json()['data']['text'] == 'Changed text'
    assert saved.json()['data']['approved'] is False
    settings = actual_js_payload('settingsPayload',{**full,'title':'Updated synthetic title'})
    bad_audience = await http_client.put('/api/studio/sets/'+s['id'],json={**settings,'audience':'unknown'})
    assert bad_audience.status_code == 422
    updated = await http_client.put('/api/studio/sets/'+s['id'],json=settings)
    assert updated.status_code == 200
    stored = await clean_db.tejas_sets.find_one({'id':s['id']})
    assert stored['title'] == 'Updated synthetic title'
    assert stored['questions'][0]['text'] == 'Changed text'
    assert stored['status'] == 'draft'
