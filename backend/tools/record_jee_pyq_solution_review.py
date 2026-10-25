import argparse
import json
from extract_jee_pyq_sources import ROOT

parser = argparse.ArgumentParser()
parser.add_argument('--regions', required=True)
args = parser.parse_args()
rows = {r['id']: r for r in json.loads((ROOT / 'solution_label_candidates.json').read_text())}
path = ROOT / 'visual_reviews.json'
reviews = json.loads(path.read_text())
for rid in [int(n) for n in args.regions.split(',')]:
    row = rows[rid]
    review = reviews.setdefault(row['file'], {'source_sha256': row['source_sha256']})
    if review['source_sha256'] != row['source_sha256']:
        raise ValueError('Review source mismatch')
    q = review.setdefault('questions', {}).setdefault(str(row['number']), {})
    q['solution_verified'] = True
    q['solution_evidence'] = f'Original source solution-region{rid} visually checked on page{row["ref"]["page"]}; printed Sol./worked content exists despite OCR label miss'
path.write_text(json.dumps(reviews, indent=2))
print('Recorded visual solution proofs:', len(args.regions.split(',')))
