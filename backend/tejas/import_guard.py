"""Authenticate and cap streamed multipart bytes before form spooling; protect imported truth."""
import asyncio
import time
import re
from starlette.requests import Request
from fastapi import HTTPException
from .contracts import error_response

class UploadBudget(Exception):
    pass

class ImportGuard:
    def __init__(self, app):
        self.app = app
        self.inflight = 0

    async def __call__(self, scope, receive, send):
        if scope['type'] != 'http': return await self.app(scope, receive, send)
        path, method = scope.get('path',''), scope.get('method','')
        if method in ('POST','PUT','PATCH','DELETE') and re.match(r'^/api/studio/sets/[^/]+(?:/|$)', path):
            from .db import sets
            id=path.split('/')[4]
            record=await sets.find_one({'id':id,'$or':[{'import_id':{'$exists':True}},{'chapter_book_id':{'$exists':True}},{'auto_import_id':{'$exists':True}}]},{'_id':0,'id':1})
            if record:
                return await error_response('Imported test content is frozen. Use its organiser to schedule or pause it; upload corrected sources as a new test.',409,'immutable_import')(scope,receive,send)
        if path not in ('/api/studio/imports','/api/studio/chapter-books','/api/studio/auto-imports') or method != 'POST': return await self.app(scope,receive,send)
        from .auth import current, staff, owner
        try: await owner(await staff(await current(Request(scope))))
        except HTTPException as exc:
            return await error_response(exc.detail,exc.status_code,'import_access_denied')(scope,receive,send)
        headers=dict(scope.get('headers',[]))
        if not headers.get(b'content-type',b'').lower().startswith(b'multipart/form-data;'):
            return await error_response('Use a multipart file upload.',415,'invalid_upload_type')(scope,receive,send)
        if headers.get(b'content-encoding',b'identity') != b'identity':
            return await error_response('Compressed request bodies are not accepted.',415,'invalid_upload_encoding')(scope,receive,send)
        limit=101*1024*1024
        declared=headers.get(b'content-length',b'')
        if declared and (not declared.isdigit() or len(declared)>12 or int(declared)>limit):
            return await error_response('Upload exceeds 101 MB total.',413,'upload_too_large')(scope,receive,send)
        if self.inflight>=2:
            return await error_response('Uploads are busy. Retry shortly.',429,'upload_busy')(scope,receive,send)
        size=0; deadline=time.monotonic()+90; started=False
        async def bounded_receive():
            nonlocal size
            remaining=deadline-time.monotonic()
            if remaining<=0: raise UploadBudget()
            try: message=await asyncio.wait_for(receive(),remaining)
            except asyncio.TimeoutError: raise UploadBudget()
            size+=len(message.get('body',b''))
            if size>limit: raise UploadBudget()
            return message
        async def tracked_send(message):
            nonlocal started
            if message['type']=='http.response.start': started=True
            await send(message)
        self.inflight+=1
        try:
            await self.app(scope,bounded_receive,tracked_send)
        except UploadBudget:
            if not started: await error_response('Upload exceeded its size or time budget. Try smaller files.',413,'upload_budget')(scope,receive,send)
        finally:
            self.inflight-=1
