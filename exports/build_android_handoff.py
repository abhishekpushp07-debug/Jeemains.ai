import argparse
import copy
import hashlib
import json
import re
import shutil
import zipfile
from datetime import datetime, timezone
from pathlib import Path
import requests

ROOT = Path('/app')
KIT = ROOT / 'exports/android_handoff'
PREFIXES = ('/api/attempts', '/api/exam-navigation', '/api/my/tests', '/api/my/sets', '/api/series/all-india-jee', '/api/bitsat', '/api/competitions')
AUTH = {'/api/auth/session', '/api/auth/me', '/api/auth/phone', '/api/auth/login', '/api/auth/refresh', '/api/auth/logout', '/api/auth/preferences'}
EXACT = AUTH | {'/api/health', '/api/chapter-exams', '/api/my/chapter-exams', '/api/sets'}
REFERENCES = [
    'features/Home.js', 'features/ExamHub.js', 'features/ExamSection.js', 'features/Profile.js',
    'features/Player.js', 'features/Results.js', 'features/LiveSeries.js', 'features/SetDetail.js',
    'features/practice/useAttempt.js', 'components/LiveSeriesBanner.js', 'components/SeriesStreak.js',
    'components/results/SolutionNavigator.js', 'components/exams/ExamNavigation.js',
    'lib/api.js', 'vibrant-ui.css', 'live-series.css', 'learning-workspace.css', 'exam-light.css', 'series-streak.css',
]


def refs(value):
    if isinstance(value, dict):
        if '$ref' in value:
            yield value['$ref']
        for child in value.values():
            yield from refs(child)
    elif isinstance(value, list):
        for child in value:
            yield from refs(child)


def allowed(path):
    return path in EXACT or any(path == p or path.startswith(p + '/') for p in PREFIXES) or bool(re.fullmatch(r'/api/sets/\{[^}]+\}(?:/(start|preflight))?', path)) or bool(re.fullmatch(r'/api/jobs/\{[^}]+\}(?:/(retry|download))?', path))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--schema-url', required=True)
    args = parser.parse_args()
    response = requests.get(args.schema_url, timeout=60)
    response.raise_for_status()
    raw = response.json()
    spec = {'openapi': raw['openapi'], 'info': {'title': 'JEELIVE.AI learner API snapshot', 'version': raw['info']['version'], 'description': 'Preview schema filtered to learner-facing APIs. Inner response DTOs need the runtime JSON envelope. Not Android device validation.'}, 'servers': [{'url': 'https://jeelive.ai'}], 'paths': {p: copy.deepcopy(v) for p, v in raw['paths'].items() if allowed(p)}, 'components': {'schemas': {}}}
    for path, operations in spec['paths'].items():
        if re.fullmatch(r'/api/attempts/\{[^}]+\}/solutions/\{[^}]+\}', path) and 'post' in operations:
            operations['post']['x-native-availability'] = 'unavailable_http_410'
            operations['post']['description'] = 'PAUSED LEGACY OPERATION: authenticated calls currently return HTTP410. Do not expose AI generation, retry this operation or substitute generated content for supplied solutions. GET remains subject to release/ownership checks.'
        if path.startswith('/api/jobs/'):
            for operation in operations.values():
                operation['x-native-note'] = 'Use only server-issued job IDs owned by the current user. GET status may dispatch queued work; not a read-only production test. Retry only failed allowed jobs. Report downloads require ownership, ready status and release.'
    needed = list(refs(spec['paths']))
    seen = set()
    while needed:
        ref = needed.pop()
        if ref in seen:
            continue
        if not ref.startswith('#/components/schemas/'):
            raise ValueError('Unexpected schema reference: ' + ref)
        name = ref.rsplit('/', 1)[-1]
        schema = raw['components']['schemas'][name]
        spec['components']['schemas'][name] = copy.deepcopy(schema)
        seen.add(ref)
        needed.extend(refs(schema))
    api = KIT / 'api'
    (api / 'student-openapi.json').write_text(json.dumps(spec, indent=2))
    commands = json.loads((api / 'command-examples.json').read_text())
    lines = ['# Learner API route inventory', '', 'Generated from preview OpenAPI. Root: https://jeelive.ai. Paths below already contain /api; do not prefix /api twice.', '', 'Read 01_BACKEND_AND_AUTH.md and 03_TEST_ENGINE_AND_SYNC.md first. OpenAPI response schemas describe inner data; runtime envelope and cookies apply. Blank/general response schema means manually inspect known frontend decoding, not invent a fixed shape.', '', '| Method | Path | Scope | Request body |', '|---|---|---|---|']
    collection = {'info': {'name': 'JEELIVE.AI Android handoff — do not run against production as tests', 'schema': 'https://schema.getpostman.com/json/collection/v2.1.0/collection.json', 'description': 'Reference requests, no credentials or auth token scripts. Cookie jar is required. Replace placeholders only in an authorized QA environment; do not run the collection against live customer data.'}, 'variable': [{'key': 'baseUrl', 'value': 'https://jeelive.ai'}, {'key': 'id', 'value': '[RESOURCE_ID]'}, {'key': 'qid', 'value': '[QUESTION_UUID]'}, {'key': 'slug', 'value': 'jee-main'}, {'key': 'kind', 'value': 'question'}, {'key': 'index', 'value': '0'}], 'item': []}
    operations = 0
    for path, paths in spec['paths'].items():
        for method, op in paths.items():
            if method not in ('get', 'post', 'put', 'patch', 'delete'):
                continue
            operations += 1
            reqschema = op.get('requestBody', {}).get('content', {}).get('application/json', {}).get('schema', {})
            request_model = reqschema.get('$ref', '').rsplit('/', 1)[-1]
            lines.append('| ' + ' | '.join([method.upper(), '`' + path + '`', ', '.join(op.get('x-role-scope', [])) or 'See auth guide', request_model or '—']) + ' |')
            url = '{{baseUrl}}' + re.sub(r'\{([^}]+)\}', r'{{\1}}', path)
            request = {'method': method.upper(), 'url': url, 'header': [], 'description': op.get('summary', '') + '\n' + op.get('description', '') + '\n' + op.get('x-native-note', '') + '\nScope: ' + ', '.join(op.get('x-role-scope', [])) + '. Cookie session required where protected. Body below is a template; consult schema.'}
            query = []
            for parameter in op.get('parameters', []):
                if parameter.get('in') == 'query':
                    name = parameter['name']
                    default = parameter.get('schema', {}).get('default')
                    value = str(default).lower() if isinstance(default, bool) else str(default) if default is not None else '[QUERY_' + name.upper() + ']'
                    query.append({'key': name, 'value': value, 'disabled': not parameter.get('required', False)})
            if query:
                active = '&'.join(p['key'] + '=' + p['value'] for p in query if not p['disabled'])
                request['url'] = {'raw': url + ('?' + active if active else ''), 'host': ['{{baseUrl}}'], 'path': re.sub(r'\{([^}]+)\}', r'{{\1}}', path).lstrip('/').split('/'), 'query': query}
            if method in ('post', 'put', 'patch', 'delete'):
                key = 'submit_refresh_logout_bonus_solution_open'
                if path.endswith('/phone'): key = 'phone_entry'
                elif path.endswith('/login'): key = 'staff_login'
                elif path.endswith('/preflight'): key = 'preflight'
                elif path.endswith('/start'): key = 'start'
                elif path.endswith('/visit'): key = 'visit'
                elif '/answers/' in path: key = 'first_answer'
                elif '/reviews/' in path: key = 'reflection'
                elif path.endswith('/report-wrong'): key = 'report_wrong'
                elif path.endswith('/compare'): key = 'compare'
                elif path.endswith('/retry'): key = 'retry_attempt'
                elif path.endswith('/expected-value'): key = 'expected_value'
                elif path.endswith('/preferences'): key = 'preference'
                elif path.endswith('/air-scenario'): key = 'rank_scenario'
                elif path.endswith('/report'): key = 'report_request'
                request['header'] = [{'key': 'Content-Type', 'value': 'application/json'}]
                request['body'] = {'mode': 'raw', 'raw': json.dumps(commands[key], indent=2), 'options': {'raw': {'language': 'json'}}}
            collection['item'].append({'name': method.upper() + ' ' + path, 'request': request})
    (api / 'ENDPOINTS.md').write_text('\n'.join(lines) + '\n')
    (api / 'postman_collection.json').write_text(json.dumps(collection, indent=2))
    for name in ('jeelive-original.jpg', 'jeelive-logo.webp', 'jeelive-icon.png'):
        shutil.copy2(ROOT / 'frontend/public/brand' / name, KIT / 'assets' / name)
    for name in REFERENCES:
        src = ROOT / 'frontend/src' / name
        dst = KIT / 'reference' / name
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dst)
    files = []
    for f in sorted(KIT.rglob('*')):
        if not f.is_file() or f.name == 'MANIFEST.json':
            continue
        rel = f.relative_to(KIT).as_posix()
        if any(part.startswith('.') for part in f.relative_to(KIT).parts) or f.suffix in ('.pdf', '.env', '.pem', '.key'):
            raise ValueError('Disallowed packaged file: ' + rel)
        data = f.read_bytes()
        if f.suffix in ('.md', '.json', '.js', '.css'):
            text = data.decode()
            if re.search(r'mongodb(?:\+srv)?://|-----BEGIN [A-Z ]*PRIVATE KEY-----|\bsk_(?:live|test)_[A-Za-z0-9]{12,}|\beyJ[A-Za-z0-9_-]{20,}\.[A-Za-z0-9_-]{20,}\.', text):
                raise ValueError('Possible credential material in package: ' + rel)
        files.append({'path': rel, 'bytes': len(data), 'sha256': hashlib.sha256(data).hexdigest()})
    manifest = {'handoff_revision': '1.1', 'prepared_at': datetime.now(timezone.utc).isoformat(), 'kind': 'native_android_agent_handoff_not_apk', 'api_schema_source': args.schema_url, 'api_schema_source_sha256': hashlib.sha256(response.content).hexdigest(), 'live_api_root': 'https://jeelive.ai/api', 'path_count': len(spec['paths']), 'operation_count': operations, 'schema_count': len(spec['components']['schemas']), 'credentials_or_customer_records_included': False, 'android_build_tested': False, 'known_identity_gap': 'Student phone entry is unverified, not OTP.', 'files': files}
    (KIT / 'MANIFEST.json').write_text(json.dumps(manifest, indent=2))
    archive = ROOT / 'frontend/public/downloads/JEELIVE_AI_Native_Android_Handoff_v1_1.zip'
    with zipfile.ZipFile(archive, 'w', compression=zipfile.ZIP_DEFLATED, compresslevel=9) as z:
        for f in sorted(KIT.rglob('*')):
            if f.is_file():
                z.write(f, 'JEELIVE_AI_Android_Handoff/' + f.relative_to(KIT).as_posix())
    shutil.copy2(archive, ROOT / 'frontend/public/downloads/JEELIVE_AI_Native_Android_Handoff.zip')
    print(json.dumps({'archive': str(archive), 'bytes': archive.stat().st_size, 'sha256': hashlib.sha256(archive.read_bytes()).hexdigest(), 'files': len(files)+1, 'api_paths': len(spec['paths']), 'api_operations': operations, 'schemas': len(spec['components']['schemas'])}, indent=2))


if __name__ == '__main__':
    main()
