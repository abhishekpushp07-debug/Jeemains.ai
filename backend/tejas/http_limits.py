"""Bounded JSON ingress before FastAPI parsing, using the mounted route contract.

Missing/mislabelled media types cannot bypass budgets. Protected multipart paths
remain held by ContentSafetyHold; this module is not the future upload sandbox.
"""
import os
import secrets
import asyncio
import json
import math
import time
from pydantic import ValidationError
from .contracts import error_response

MAX_JSON_BYTES = 1024 * 1024  # Compatibility fallback for standalone middleware.
MAX_DEPTH = 40
MAX_NODES = 50000
READ_SECONDS = 10


def unique_object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError('Duplicate JSON keys are not accepted')
        result[key] = value
    return result


def reject_constant(value):
    raise ValueError('Non-finite JSON numbers are not accepted')


def validated_json(body):
    value = json.loads(body, object_pairs_hook=unique_object, parse_constant=reject_constant)
    stack, count = [(value, 0)], 0
    while stack:
        item, depth = stack.pop()
        count += 1
        if depth > MAX_DEPTH or count > MAX_NODES:
            raise ValueError('JSON structure exceeds its budget')
        if isinstance(item, dict):
            for key in item:
                key.encode('utf-8')
            stack.extend((v, depth + 1) for v in item.values())
        elif isinstance(item, list):
            stack.extend((v, depth + 1) for v in item)
        elif isinstance(item, str):
            item.encode('utf-8')
        elif isinstance(item, float) and not math.isfinite(item):
            raise ValueError('Non-finite exponent')
    return value


class JsonBodyLimits:
    def __init__(self, app, contracts=(), contracts_owner=None):
        self.app = app
        self.contracts = contracts_owner.state.route_contracts if contracts_owner is not None else contracts

    async def __call__(self, scope, receive, send):
        if scope['type'] != 'http':
            return await self.app(scope, receive, send)
        async def reject(message, status, code='invalid_request_body'):
            await error_response(message, status, code)(scope, receive, send)
        if len(scope.get('query_string', b'')) > 8192 or len(scope.get('path', '')) > 2048:
            return await reject('Request address exceeds its budget.', 414)
        method, path = scope.get('method'), scope.get('path', '')
        if method not in ('POST', 'PUT', 'PATCH', 'DELETE'):
            return await self.app(scope, receive, send)
        contract = next((c for c in self.contracts if method in c.route.methods and c.route.path_regex.fullmatch(path)), None)
        raw_headers = scope.get('headers', [])
        if contract and contract.key == 'jobs.cron':
            expected = os.environ.get('WEBHOOK_CRON_SECRET', '')
            credentials = [v.decode('latin-1') for k, v in raw_headers if k.lower() == b'authorization']
            if not expected or len(credentials) != 1 or not secrets.compare_digest(credentials[0], 'Bearer ' + expected):
                return await reject('Unauthorized', 401, 'http_401')
        media = [v.decode('latin-1').lower().split(';', 1)[0].strip() for k, v in raw_headers if k.lower() == b'content-type']
        lengths = [v for k, v in raw_headers if k.lower() == b'content-length']
        encodings = [v.lower() for k, v in raw_headers if k.lower() == b'content-encoding']
        if len(media) > 1 or len(lengths) > 1:
            return await reject('Ambiguous request headers.', 400)
        if contract and not contract.json_body:
            return await self.app(scope, receive, send)
        # In standalone compatibility mode, multipart is not a JSON parser input.
        if not contract and media and media[0] not in ('application/json', ''):
            return await self.app(scope, receive, send)
        if encodings and encodings != [b'identity']:
            return await reject('Encoded request bodies are not accepted.', 415)
        if contract and media and media[0] != 'application/json':
            return await reject('Use application/json for this operation.', 415)
        limit = contract.body_limit if contract else MAX_JSON_BYTES
        try:
            if lengths and (not lengths[0].isdigit() or len(lengths[0]) > 12):
                raise ValueError()
            declared = int(lengths[0]) if lengths else None
        except ValueError:
            return await reject('Invalid request length.', 400)
        if declared is not None and declared > limit:
            return await reject('Request body exceeds this operation’s byte budget.', 413)
        chunks, size, deadline = [], 0, time.monotonic() + READ_SECONDS
        while True:
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                return await reject('Request body was not received in time.', 408)
            try:
                message = await asyncio.wait_for(receive(), remaining)
            except asyncio.TimeoutError:
                return await reject('Request body was not received in time.', 408)
            if message['type'] == 'http.disconnect':
                return
            if message['type'] != 'http.request':
                return await reject('Invalid request stream.', 400)
            chunk = message.get('body', b'')
            size += len(chunk)
            if size > limit:
                return await reject('Request body exceeds this operation’s byte budget.', 413)
            if chunk:
                chunks.append(chunk)
            if not message.get('more_body', False):
                break
        if declared is not None and declared != size:
            return await reject('Request length does not match its body.', 400)
        body = b''.join(chunks)
        try:
            value = validated_json(body) if body else {}
        except (ValueError, RecursionError, UnicodeError):
            return await reject('Invalid JSON: use unique keys, finite numbers, valid text and bounded nesting.', 400)
        if contract and contract.model:
            if not body and contract.route.body_field and contract.route.body_field.required:
                return await reject('This operation requires a JSON body.', 422, 'validation_error')
            try:
                contract.model.model_validate(value)
            except ValidationError:
                # No input values, keys or credential echoes in errors/logs.
                return await reject('Request fields or values do not match this operation’s contract.', 400 if contract.key == 'jobs.cron' else 422, 'validation_error')
        if not media:
            scope = {**scope, 'headers': [*raw_headers, (b'content-type', b'application/json')]}
        delivered = False
        async def replay():
            nonlocal delivered
            if delivered:
                return await receive()
            delivered = True
            return {'type': 'http.request', 'body': body, 'more_body': False}
        await self.app(scope, replay, send)
