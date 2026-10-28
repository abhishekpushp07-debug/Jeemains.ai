"""Iter55 real academic lists with ONE already-created approved UI session; never login/write/start/visit/results."""
import json
import os
from pathlib import Path
import pytest
import requests
from dotenv import load_dotenv

load_dotenv('/app/frontend/.env')
BASE=os.environ['EXPO_PUBLIC_BACKEND_URL'].rstrip('/')+'/api/jl'

@pytest.fixture(scope='module')
def reader():
    p=Path('/tmp/iter55_own_handle.json')
    if not p.exists(): pytest.skip('Explicit current-run session unavailable; no login permitted in this suite')
    s=requests.Session()
    s.headers.update({'X-JL-Sid':json.loads(p.read_text())['sid'],'Accept':'application/json'})
    yield s
    s.close()

def get(reader,path,params=None):
    r=reader.get(BASE+path,params=params,timeout=32)
    if r.status_code in (401,429): pytest.skip('Session rejected/rate limited; stop without login/retry')
    assert r.status_code==200, f'Read-only {path} unavailable: HTTP{r.status_code}'
    data=r.json()
    return data['data'] if isinstance(data,dict) and data.get('meta',{}).get('api_version') else data

def test_real_pyq_same_30_rows(reader):
    data=get(reader,'/pyq/jee-main')
    assert data['total']==30 and len(data['items'])==30
    assert len({p['id'] for p in data['items']})==30
    assert {p['year'] for p in data['items']}=={2025,2026}

def test_real_bitsat_pagination_and_search(reader):
    params={'kind':'mocks','subject':'','q':'','page':1}
    first=get(reader,'/exam-navigation/bitsat/catalogue',params)
    assert first['total']>=len(first['items'])>0 and first['pages']>1
    second=get(reader,'/exam-navigation/bitsat/catalogue',{**params,'page':2})
    assert second['total']==first['total'] and len(second['items'])>0
    assert not ({p['id'] for p in first['items']} & {p['id'] for p in second['items']})
    searched=get(reader,'/exam-navigation/bitsat/catalogue',{**params,'q':'Mock 1'})
    assert searched['items'] and searched['total']<=first['total']
    assert all('mock 1' in item['title'].lower() for item in searched['items'])

@pytest.mark.parametrize('tab',['progress','saved','completed'])
def test_real_mytests_tabs_have_consistent_private_counts(reader,tab):
    data=get(reader,'/my/tests',{'tab':tab,'page':1,'q':'','status':'all','exam':''})
    assert isinstance(data['items'],list) and isinstance(data['total'],int)
    assert all(isinstance(data['counts'][k],int) and data['counts'][k]>=0 for k in ['progress','saved','completed'])
    assert data['total']==data['counts'][tab]
    if tab=='completed': assert data['total']>0 and data['items']