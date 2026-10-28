"""Iter55 read-only media smoke and actual bounded canonical transport behavior (isolated IO)."""
import asyncio
import hashlib
import json
import os
import subprocess
from pathlib import Path
from types import SimpleNamespace

import httpx
import pytest
import requests
from dotenv import load_dotenv
from jl_transport import canonical_request

load_dotenv('/app/frontend/.env')
BASE = os.environ['EXPO_PUBLIC_BACKEND_URL'].rstrip('/')
CANONICAL = os.environ['EXPO_PUBLIC_JEELIVE_API'].rstrip('/')

def test_actual_proxy_serializes_cookie_rotating_endpoints(monkeypatch):
    # Actual server function, all IO replaced in-memory; no MongoDB/canonical writes or app startup.
    import server
    active=0
    maximum=0
    started=asyncio.Event()
    release=asyncio.Event()
    jar={'refresh_token':'TEST_INITIAL'}
    async def load(_): return dict(jar)
    async def save(_, cookies): jar.clear(); jar.update(cookies)
    async def canonical(*args, **kwargs):
        nonlocal active, maximum
        active+=1; maximum=max(maximum,active)
        if kwargs['path']=='auth/session':
            started.set()
            await release.wait()
        else:
            release.set()
        active-=1
        return httpx.Response(200,json={'user':{'id':'TEST_A'}},headers={'set-cookie':'refresh_token=TEST_ROTATED; Path=/'})
    monkeypatch.setattr(server,'load_jar',load)
    monkeypatch.setattr(server,'save_jar',save)
    monkeypatch.setattr(server,'canonical_request',canonical)
    class Request:
        headers={}
        query_params={}
        method='GET'
        async def body(self): return b''
    async def run():
        a=asyncio.create_task(server.jeelive_proxy('auth/session',Request(),'TEST-OWN-PROXY-HANDLE-55'))
        await started.wait()
        req=Request();req.method='POST'
        b=asyncio.create_task(server.jeelive_proxy('auth/refresh',req,'TEST-OWN-PROXY-HANDLE-55'))
        await asyncio.sleep(.02)
        release.set()
        responses=await asyncio.gather(a,b)
        assert all(r.status_code==200 for r in responses)
    asyncio.run(run())
    assert maximum==1, 'proxy forwards concurrent rotating endpoints with same stale cookie snapshot'

@pytest.mark.parametrize('path,method,expected', [('auth/session','GET',1),('auth/refresh','POST',1),('auth/phone','POST',1),('my/tests','GET',2)])
def test_transport_only_retries_safe_reads(path, method, expected):
    calls=[]
    async def request(*args, **kwargs):
        calls.append((args,kwargs))
        return httpx.Response(503,json={'detail':'isolated unavailable'})
    async def run():
        r=await canonical_request(SimpleNamespace(request=request),method,CANONICAL+'/'+path,path=path,params={},body=None,headers={})
        assert r.status_code==503 and r.json()['detail']=='isolated unavailable'
    asyncio.run(run())
    assert len(calls)==expected

@pytest.mark.parametrize('variant', ['Vertical','Landscape'])
def test_mobile_compatible_mp4_full_decode_and_faststart(variant):
    p=Path('/app/marketing/launch45/output')/f'JEELIVE-Mobile-{variant}-45s.mp4'
    info=json.loads(subprocess.check_output(['ffprobe','-v','error','-show_streams','-show_format','-of','json',str(p)]))
    video,audio=info['streams']
    assert (video['codec_name'],video['profile'],video['level'],video['pix_fmt'],video['nb_frames'])==('h264','Constrained Baseline',31,'yuv420p','1350')
    assert (video['width'],video['height'])==((720,1280) if variant=='Vertical' else (1280,720))
    assert audio['codec_name']=='aac' and audio['profile']=='LC' and audio['sample_rate']=='44100' and audio['channels']==2
    assert float(info['format']['duration'])==45
    raw=p.read_bytes()
    assert 0<raw.index(b'moov')<raw.index(b'mdat')
    decode=subprocess.run(['ffmpeg','-v','error','-i',str(p),'-f','null','-'],capture_output=True,timeout=90)
    assert decode.returncode==0 and not decode.stderr

@pytest.mark.parametrize('name', ['vertical.mp4','landscape.mp4','launch-pack.zip','vertical-mobile.mp4','landscape-mobile.mp4'])
def test_published_originals_download_integrity(name):
    manifest=json.loads(Path('/app/backend/marketing_manifest.json').read_text())['assets'][name]
    r=requests.get(BASE+'/api/marketing/launch/'+name+'?download=1',timeout=90)
    assert r.status_code==200
    assert len(r.content)==manifest['bytes'] and hashlib.sha256(r.content).hexdigest()==manifest['sha256']
    assert 'attachment;' in r.headers['Content-Disposition'] and manifest['filename'] in r.headers['Content-Disposition']