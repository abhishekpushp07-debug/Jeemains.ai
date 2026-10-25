import hashlib
import json
from datetime import datetime, timezone

from extract_jee_pyq_sources import ROOT


def fingerprint(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(',', ':'), ensure_ascii=False).encode()).hexdigest()


papers = {}
blocked = []
for record in json.loads((ROOT / 'extraction_summary.json').read_text()):
    fid = record['file']['drive_id']
    if record.get('error') or record.get('issues'):
        blocked.append({'filename': record['file']['filename'], 'reason': 'Original source is incomplete or has unresolved mapping issues; not published.', 'issues': record.get('issues', record.get('error'))})
        continue
    data = json.loads((ROOT / (fid + '.candidates.json')).read_text())
    keys = json.loads((ROOT / (fid + '.key_checks.json')).read_text())
    edges = json.loads((ROOT / (fid + '.crop_edge_checks.json')).read_text())
    if edges:
        raise ValueError('Source crop boundary still needs review: ' + record['file']['filename'])
    if len(keys) != 75 or any(not k['agreement'] or k['source_sha256'] != data['source_sha256'] for k in keys):
        raise ValueError('Independent answer-key proof is incomplete: ' + record['file']['filename'])
    by_number = {key['number']: key for key in keys}
    for q in data['questions']:
        key = by_number[q['number']]
        if key['candidate_answer'] != q['answer']:
            raise ValueError('Answer changed after its independent verification')
        if not q['q_refs'] or not q['s_refs']:
            raise ValueError('A source crop is missing')
    papers[fid] = {'status': 'SOURCE_REVIEWED', 'candidate_sha256': fingerprint(data),
                   'key_verification': {'count': 75, 'independent_passes': 2, 'agreement': 75, 'source_sha256': data['source_sha256']},
                   'crop_verification': {'uncorrected_cut_edges': 0, 'method': 'Image-edge checks, visual exception/boundary review, per-paper subject samples'}}
if len(papers) != 30 or len(blocked) != 1:
    raise ValueError('Unexpected source inventory; do not silently publish a partial package')
review = ROOT / 'visual_sample_review.json'
if not review.exists() or not json.loads(review.read_text()).get('approved'):
    raise ValueError('Final per-paper visual samples have not been approved')
output = {'approved_at': datetime.now(timezone.utc).timestamp(), 'papers': papers, 'blocked_sources': blocked}
(ROOT / 'approved_papers.json').write_text(json.dumps(output, indent=2))
print('SOURCE_APPROVAL_COMPLETE', len(papers), 'papers', len(papers) * 75, 'questions', len(blocked), 'blocked original')
