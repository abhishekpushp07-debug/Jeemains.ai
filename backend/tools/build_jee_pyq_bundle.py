import argparse
import copy
import gzip
import hashlib
import json
import sys
import uuid
from datetime import datetime, timezone
from pathlib import Path

from extract_jee_pyq_sources import ROOT

BACKEND = Path(__file__).resolve().parents[1]
RESOURCES = BACKEND / 'resources'
OPTIONS = {'A': 'Option 1, as printed in the source', 'B': 'Option 2, as printed in the source', 'C': 'Option 3, as printed in the source', 'D': 'Option 4, as printed in the source'}
LABELS = dict(zip('ABCD', '1234'))


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(',', ':'), ensure_ascii=False).encode()).hexdigest()


def question(source, record, set_id):
    n = record['number']
    qid = str(uuid.uuid5(uuid.NAMESPACE_URL, set_id + ':question:' + str(n)))
    labels = dict(zip('1234', 'ABCD'))
    keys = record.get('accepted_answers') or []
    key = record['answer']
    if record['type'] == 'mcq':
        key = labels[key] if key else ''
        keys = [labels[value] for value in keys]
    bonus = record['source_status'] in ('dropped', 'bonus')
    refs = lambda name: [{**ref, 'file_id': source['id']} for ref in record[name]]
    warning = ' '.join(record.get('warnings', []))
    if bonus:
        warning = (warning + ' This source question is withdrawn. Full credit is awarded under the published scoring policy; it is not an ordinary wrong-answer penalty.').strip()
    return {'id': qid, 'number': n, 'source_number': n, 'solution_number': n, 'subject': record['subject'], 'section': record['subject'],
            'type': record['type'], 'text': f'Question {n} · {record["subject"]}. Read the original source region.',
            'options': OPTIONS.copy() if record['type'] == 'mcq' else {}, 'answer': key,
            'accepted_answers': keys, 'disposition': 'bonus_all' if bonus else 'multiple_accepted' if len(keys) > 1 else 'standard',
            'source_option_labels': LABELS.copy() if record['type'] == 'mcq' else {}, 'topic': 'Previous-year paper', 'difficulty': 'unrated',
            'render_mode': 'source', 'accessible_text': f'Original scanned {record["subject"]} question {n}. Formulae and diagrams are in the source image; a text transcription is not supplied.',
            'solution_accessible_text': f'Original supplied solution or answer key for question {n}, shown as source images; a text transcription is not supplied.',
            'solution': 'The original supplied explanation or key is shown in the source regions.', 'solution_kind': record['solution_kind'],
            'source_warning': warning, 'q_refs': refs('q_refs'), 's_refs': refs('s_refs'), 'approved': True, 'issues': [],
            'pairing_evidence': f'Printed question{n} and its supplied key/solution boundaries, independently reviewed against source SHA256 {source["sha256"]}.',
            'source_evidence': {'kind': 'owner_supplied_pyq', 'pdf_sha256': source['sha256'], 'printed_key': record['key_evidence'],
                                'printed_answer_normalization': record.get('normalization_evidence'), 'source_status': record['source_status']}}


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--require-approved', action='store_true')
    args = parser.parse_args()
    if not args.require_approved:
        parser.error('Explicit --require-approved is mandatory')
    approvals = json.loads((ROOT / 'approved_papers.json').read_text())
    sources = json.loads((ROOT / 'private_sources.json').read_text())
    collections = {'tejas_files': [], 'tejas_versions': [], 'tejas_sets': []}
    dates = set()
    for fid, approved in approvals['papers'].items():
        candidate = json.loads((ROOT / (fid + '.candidates.json')).read_text())
        if approved['candidate_sha256'] != digest(candidate) or candidate['issues'] or len(candidate['questions']) != 75:
            raise ValueError('A paper changed after source approval')
        if approved['status'] != 'SOURCE_REVIEWED' or candidate['source_sha256'] != sources[fid]['sha256']:
            raise ValueError('Source approval/integrity is incomplete')
        meta = candidate['metadata']
        logical = (meta['exam_date'], meta['shift'])
        if logical in dates:
            raise ValueError('Duplicate printed exam date/shift')
        dates.add(logical)
        set_id = f'jee-main-pyq-{meta["exam_date"]}-s{meta["shift"]}'
        original = copy.deepcopy(sources[fid])
        original['set_id'] = set_id
        original['uploaded_by'] = ''
        original['created_at'] = approvals['approved_at']
        questions = [question(original, q, set_id) for q in candidate['questions']]
        if [q['number'] for q in questions] != list(range(1, 76)):
            raise ValueError('Question numbering is not complete')
        for subject in ('Physics', 'Chemistry', 'Mathematics'):
            sub = [q for q in questions if q['subject'] == subject]
            if len(sub) != 25 or sum(q['type'] == 'mcq' for q in sub) != 20:
                raise ValueError('Source subject/type counts need review')
        rules = {'minutes': 180, 'correct': 4, 'wrong': -1, 'skipped': 0, 'navigation': 'free', 'numeric_policy': 'integer_exact',
                 'solution_release': 'after_submit', 'numeric_rule': 'Exact integer entry; where the source question asks for rounding, enter the requested nearest integer.'}
        version_id = set_id + '-source-v1'
        title = 'JEE Main PYQ · ' + datetime.fromisoformat(meta['exam_date']).strftime('%d %b %Y') + f' · Shift {meta["shift"]}'
        paper = {'id': set_id, 'title': title, 'description': 'Complete dated past paper with source-matched question and solution crops. Independent practice, not an NTA service.',
                 'exam': 'JEE Main', 'year': str(meta['year']), 'pyq_year': meta['year'], 'pyq_date': meta['exam_date'], 'pyq_shift': meta['shift'],
                 'pyq_date_evidence': meta['date_evidence'], 'test_kind': 'pyq', 'full_length': True, 'status': 'published', 'qa_only': False,
                 'questions': questions, 'rules': rules, 'profile_mode': 'practice', 'tags': ['PYQ', 'Source-backed'],
                 'version': 1, 'revision': 1, 'key_version': 1, 'version_id': version_id, 'published': True, 'audience': 'all', 'expires': '',
                 'file_ids': [original['id']], 'rights_upload': True, 'rights_publish': True, 'rights_report': False,
                 'source': 'Owner-supplied Jee written pyq folder; printed original date and shift verified.',
                 'sources': {original['id']: copy.deepcopy(original)}, 'rights_attested': True, 'rights_attested_by': '', 'published_by': '',
                 'created_at': approvals['approved_at'], 'updated_at': approvals['approved_at'], 'published_at': approvals['approved_at'],
                 'competition': False, 'live_enabled': False, 'verification': {'status': 'source_reviewed', 'source_sha256': candidate['source_sha256'],
                 'candidate_sha256': digest(candidate), 'key_verification': approved['key_verification'], 'crop_verification': approved['crop_verification']}}
        collections['tejas_files'].append(original)
        archive = copy.deepcopy(paper)
        archive.update(id=version_id, set_id=set_id)
        collections['tejas_versions'].append(archive)
        collections['tejas_sets'].append(paper)
    out = {'schema_version': 1, 'collections': collections, 'record_sha256': {name: {row['id']: digest(row) for row in docs} for name, docs in collections.items()},
           'audit': {'status': 'SOURCE_REVIEWED', 'papers': len(dates), 'questions': len(dates) * 75, 'blocked_sources': approvals['blocked_sources'],
                     'note': 'Original source anomalies are disclosed; no replacement questions or generated worked solutions.'}}
    raw = json.dumps(out, sort_keys=True, separators=(',', ':'), ensure_ascii=False).encode()
    RESOURCES.mkdir(exist_ok=True)
    (RESOURCES / 'jee_pyq.json.gz').write_bytes(gzip.compress(raw, mtime=0))
    manifest = {'sha256': hashlib.sha256(raw).hexdigest(), 'papers': len(dates), 'questions': len(dates) * 75, 'raw_bytes': len(raw)}
    (RESOURCES / 'jee_pyq_manifest.json').write_text(json.dumps(manifest, indent=2))
    print('REVIEWED_PACKAGE_CREATED', json.dumps(manifest))
