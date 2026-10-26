import argparse
import hashlib
import json
import os
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlparse
import requests
from dotenv import load_dotenv


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--url', required=True)
    p.add_argument('--output', required=True)
    args = p.parse_args()
    base = args.url.rstrip('/')
    if urlparse(base).scheme != 'https':
        raise SystemExit('HTTPS required')
    load_dotenv('/app/backend/.env')
    out = Path(args.output)
    out.mkdir(parents=True, exist_ok=True)
    s = requests.Session()
    s.headers['Origin'] = base
    def call(method, path, **kwargs):
        r = s.request(method, base + '/api' + path, timeout=60, **kwargs)
        if not r.ok:
            raise RuntimeError(f'{method} {path}: HTTP {r.status_code}')
        v = r.json()
        return v['data'] if isinstance(v, dict) and v.get('meta', {}).get('api_version') else v
    logged = False
    try:
        u = call('POST', '/auth/login', json={'email': os.environ['ADMIN_EMAIL'], 'password': os.environ['ADMIN_PASSWORD']})
        if u.get('role') != 'owner':
            raise RuntimeError('Owner authorisation required')
        logged = True
        data = call('GET', '/pyq/jee-main')
        rows = [{k: row.get(k) for k in ('id', 'title', 'year', 'exam_date', 'shift', 'count')} for row in data['items']]
        assert data['total'] == len(rows) == 30 and sum(row['count'] for row in rows) == 2250
        assert len({row['id'] for row in rows}) == 30
        status = call('GET', '/studio/pyq-import/status')
        public = call('GET', '/sets')
        meta = {'checked_at': datetime.now(timezone.utc).isoformat(), 'api_base': base + '/api',
                'endpoint': 'GET /api/pyq/jee-main', 'verification_role': 'authorised owner; same shared catalogue endpoint',
                'student_session_check': 'Pending existing native learner session; no student impersonation performed',
                'total': data['total'], 'questions': sum(row['count'] for row in rows), 'years': data['years'],
                'paper_ids_sha256': hashlib.sha256('\n'.join(sorted(row['id'] for row in rows)).encode()).hexdigest(),
                'papers': rows, 'import_status': {k: status.get(k) for k in ('phase', 'verified_files', 'total_files', 'inserted_records', 'total_records', 'published_papers', 'total_papers', 'questions')},
                'public_catalogue_counts': public.get('counts'), 'attempts_created': 0,
                'student_accounts_created': 0, 'customer_records_deleted': 0}
        (out / 'canonical-pyq.json').write_text(json.dumps(meta, indent=2) + '\n')
        r = s.get(base + '/api/openapi.json', timeout=60)
        if r.status_code == 200 and 'application/json' in r.headers.get('Content-Type', '') and 'paths' in r.json():
            spec = r.json()
            schema = spec.get('components', {}).get('schemas', {})
            kept = {}
            for path, operations in spec['paths'].items():
                if path.startswith(('/api/auth/', '/api/pyq/', '/api/attempts', '/api/my/', '/api/sets/', '/api/exam-navigation/', '/api/series/')):
                    kept[path] = operations
            refs = set()
            def collect(v):
                if isinstance(v, dict):
                    if '$ref' in v and v['$ref'].startswith('#/components/schemas/'):
                        key = v['$ref'].split('/')[-1]
                        if key not in refs:
                            refs.add(key)
                            collect(schema.get(key, {}))
                    for x in v.values(): collect(x)
                elif isinstance(v, list):
                    for x in v: collect(x)
            collect(kept)
            contract = {'checked_at': meta['checked_at'], 'api_base': base + '/api', 'live': True,
                        'pin_signup_route_live': '/api/auth/phone/signup' in kept, 'pin_change_route_live': '/api/auth/pin' in kept,
                        'paths': kept, 'components': {'schemas': {k: schema[k] for k in sorted(refs) if k in schema}}}
        else:
            contract = {'checked_at': meta['checked_at'], 'api_base': base + '/api', 'openapi_status': r.status_code,
                        'pin_routes_live': 'Not confirmed by schema; prepared revision is not deployed'}
        (out / 'canonical-api-contract.json').write_text(json.dumps(contract, indent=2) + '\n')
        print(json.dumps({'live_catalogue_total': meta['total'], 'questions': meta['questions'], 'import_phase': meta['import_status'].get('phase'), 'public_counts': public.get('counts'), 'student_session_check': 'pending native session'}))
    finally:
        if logged:
            r = s.post(base + '/api/auth/logout', timeout=30)
            print('OPERATIONAL_SESSION_CLOSED', r.status_code == 200)
        s.close()


if __name__ == '__main__':
    main()
