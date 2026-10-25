import argparse
import hashlib
import json
from extract_jee_pyq_sources import ROOT

parser = argparse.ArgumentParser()
parser.add_argument('--indices', required=True)
args = parser.parse_args()
rows = json.loads((ROOT / 'boundary_proposals.json').read_text())
path = ROOT / 'visual_reviews.json'
reviews = json.loads(path.read_text())
for index in (int(n) for n in args.indices.split(',')):
    row = rows[index]
    if row['proposed_top'] is None:
        raise ValueError('No proposed boundary')
    fid = row['file']['drive_id']
    sha = hashlib.sha256((ROOT / (fid + '.pdf')).read_bytes()).hexdigest()
    review = reviews.setdefault(fid, {'source_sha256': sha})
    if review['source_sha256'] != sha:
        raise ValueError('Source changed')
    q = review.setdefault('questions', {}).setdefault(str(row['question']), {})
    q['top'] = row['anchor_top']
    q['boundary_evidence'] = f'Visually approved original-content green/red boundary proof{index}, page{row["page"]}; full formula/diagram preserved and previous solution excluded'
path.write_text(json.dumps(reviews, indent=2))
print('Recorded only visually approved source crop boundaries')
