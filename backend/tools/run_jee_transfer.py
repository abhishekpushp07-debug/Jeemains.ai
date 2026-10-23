import argparse
import gzip
import hashlib
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlsplit
import requests
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[1]
load_dotenv(ROOT / '.env')


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--target', required=True)
    parser.add_argument('--report', required=True)
    args = parser.parse_args()
    url = urlsplit(args.target)
    if url.scheme != 'https' or not url.netloc or url.username or url.password or url.path not in ('', '/') or url.query or url.fragment:
        raise ValueError('Supply only the authorized HTTPS site origin.')
    base = args.target.rstrip('/')
    client = requests.Session()
    client.headers.update({'Origin': base, 'Content-Type': 'application/json'})
    report = {'target': base, 'started_at': datetime.now(timezone.utc).isoformat(), 'status': 'not_started', 'samples': []}
    logged_in = False

    def call(method, path, payload=None):
        response = client.request(method, base + '/api' + path, json=payload, timeout=90, allow_redirects=False)
        if response.status_code != 200:
            raise RuntimeError('Operation stopped: ' + path + ' returned HTTP ' + str(response.status_code))
        body = response.json()
        return body['data'] if isinstance(body, dict) and 'data' in body and body.get('meta', {}).get('api_version') else body

    try:
        probe = client.get(base + '/api/studio/jee-transfer', timeout=30, allow_redirects=False)
        if probe.status_code != 401:
            raise RuntimeError('Owner-only importer is not ready on the target; no login or content write attempted.')
        call('POST', '/auth/login', {'email': os.environ['ADMIN_EMAIL'], 'password': os.environ['ADMIN_PASSWORD']})
        logged_in = True
        if call('GET', '/auth/me')['role'] != 'owner':
            raise RuntimeError('An existing authorized owner session is required.')
        report['before'] = call('GET', '/studio/jee-transfer')
        state = report['before']
        for _ in range(110):
            if state['phase'] == 'complete':
                break
            state = call('POST', '/studio/jee-transfer/step', {})
            print(json.dumps({k: state[k] for k in ('phase', 'verified_files', 'processed_records', 'chapter_tests')}), flush=True)
        if state['phase'] != 'complete' or state['verified_files'] != 81 or state['processed_records'] != 162 or state['chapter_tests'] != 78 or not state['existing_content_unchanged']:
            raise RuntimeError('Import is incomplete; resume the same operation rather than re-importing.')
        report['after'] = state
        catalogue = call('GET', '/exam-navigation/jee-main/catalogue?kind=chapters')
        if catalogue['total'] != 78 or catalogue['subject_counts'] != {'Physics': 29, 'Mathematics': 26, 'Chemistry': 23}:
            raise RuntimeError('Live catalogue totals differ; inspect without overwriting records.')
        report['catalogue'] = {k: catalogue[k] for k in ('total', 'pages', 'subject_counts')}
        data = json.loads(gzip.decompress((ROOT / 'resources' / 'jee_chapters.json.gz').read_bytes()))['collections']
        for subject, minutes in [('Physics', 90), ('Mathematics', 120), ('Chemistry', 70)]:
            s = next(s for s in data['tejas_sets'] if s['chapter_subject'] == subject)
            path = '/studio/chapter-books/' + s['chapter_book_id'] + '/chapters/' + s['id']
            preview = call('GET', path)
            chapter, questions = preview['chapter'], preview['questions']
            if chapter['count'] != 50 or chapter['rules']['minutes'] != minutes or [chapter['rules'][k] for k in ('correct', 'wrong', 'skipped')] != [4, -1, 0]:
                raise RuntimeError('Live sample timer or marking differs.')
            if questions != s['questions']:
                raise RuntimeError('Live sample question/solution content differs from the verified source.')
            crops = {}
            for kind in ('question', 'solution'):
                response = client.get(base + '/api' + path + '/questions/' + questions[0]['id'] + '/asset/' + kind + '/0', timeout=90)
                if response.status_code != 200 or not response.content.startswith(b'\x89PNG\r\n\x1a\n'):
                    raise RuntimeError('Live original-source crop is unavailable.')
                crops[kind] = {'bytes': len(response.content), 'sha256': hashlib.sha256(response.content).hexdigest()}
            report['samples'].append({'subject': subject, 'set_id': s['id'], 'minutes': minutes, 'source_questions_and_solutions_equal': True, 'crops': crops})
        report['status'] = 'complete_verified'
        print('COMPLETE: 78 live chapters, 3900 supplied question/solution pairs; existing content preserved.', flush=True)
    except Exception as exc:
        report['status'] = 'incomplete'
        report['error'] = str(exc) if isinstance(exc, RuntimeError) else type(exc).__name__
        print(report['error'], flush=True)
    finally:
        if logged_in:
            try:
                report['operational_session_closed'] = call('POST', '/auth/logout', {}).get('ok') is True
            except Exception:
                report['operational_session_closed'] = False
        client.close()
        report['finished_at'] = datetime.now(timezone.utc).isoformat()
        destination = Path(args.report)
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_text(json.dumps(report, indent=2))
        os.chmod(destination, 0o600)
    if report['status'] != 'complete_verified':
        sys.exit(1)


if __name__ == '__main__':
    main()
