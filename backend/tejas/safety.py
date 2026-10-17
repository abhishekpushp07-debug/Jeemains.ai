"""Packet 1 safety holds. Containment is not a fix, role system or worker fence."""
import re
from enum import Enum
from fastapi import HTTPException
from .contracts import error_response


class Capability(str, Enum):
    SOURCE_UPLOAD = 'source_upload'
    SOURCE_PARSE = 'source_parse'
    PUBLICATION = 'publication'
    EXTRACTION = 'extraction'
    REGRADE = 'regrade'


# No runtime/browser/env opt-out. Change via reviewed code + owning packet evidence.
HELD_CAPABILITIES = frozenset(Capability)
HOLD_MESSAGE = 'This content operation is temporarily held for safety verification. Existing saved exam answers are unchanged. Contact the operator before retrying.'
RETRY_SECONDS = '3600'
JOB_CAPABILITIES = {'extract': Capability.EXTRACTION, 'regrade': Capability.REGRADE}
ROUTES = (
    ('POST', re.compile(r'^/api/studio/sets/[^/]+/files/?$'), Capability.SOURCE_UPLOAD),
    ('POST', re.compile(r'^/api/studio/sets/[^/]+/publish/?$'), Capability.PUBLICATION),
    ('POST', re.compile(r'^/api/studio/sets/[^/]+/extract/?$'), Capability.EXTRACTION),
    ('POST', re.compile(r'^/api/studio/sets/[^/]+/regrade/?$'), Capability.REGRADE),
    ('GET', re.compile(r'^/api/studio/files/[^/]+/(?:page|text)/[^/]+/?$'), Capability.SOURCE_PARSE),
    ('GET', re.compile(r'^/api/studio/sets/[^/]+/questions/[^/]+/asset/[^/]+/[^/]+/?$'), Capability.SOURCE_PARSE),
)


def held(capability):
    try:
        return Capability(capability) in HELD_CAPABILITIES
    except ValueError:
        return True  # Unknown protected capability is never an allow.


def require_capability(capability):
    if held(capability):
        raise HTTPException(503, HOLD_MESSAGE, headers={'Retry-After': RETRY_SECONDS, 'X-Tejas-Safety-Hold': 'packet-1'})


def job_held(kind):
    capability = JOB_CAPABILITIES.get(kind)
    return capability is not None and held(capability)


class ContentSafetyHold:
    """Reject before JsonBodyLimits, FastAPI dependency resolution or multipart parsing."""
    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope['type'] == 'http':
            for method, pattern, capability in ROUTES:
                if scope.get('method') == method and pattern.fullmatch(scope.get('path', '')) and held(capability):
                    response = error_response(HOLD_MESSAGE, 503, 'capability_held')
                    response.headers['Retry-After'] = RETRY_SECONDS
                    response.headers['X-Tejas-Safety-Hold'] = 'packet-1'
                    response.headers['Cache-Control'] = 'private, no-store'
                    return await response(scope, receive, send)
        await self.app(scope, receive, send)
