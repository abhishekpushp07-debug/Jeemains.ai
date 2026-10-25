import argparse
import hashlib
import json
from extract_jee_pyq_sources import ROOT

parser = argparse.ArgumentParser()
parser.add_argument('--regions', required=True)
args = parser.parse_args()
rows = {r['id']: r for r in json.loads((ROOT / 'false_anchor_candidates.json').read_text())}
path = ROOT / 'visual_reviews.json'
reviews = json.loads(path.read_text())
for rid in (int(x) for x in args.regions.split(',')):
    row = rows[rid]
    fid = row['file']
    sha = hashlib.sha256((ROOT / (fid + '.pdf')).read_bytes()).hexdigest()
    review = reviews.setdefault(fid, {'source_sha256': sha})
    if review['source_sha256'] != sha:
        raise ValueError('Source changed')
    a = row['anchor']
    item = {'page': a['page'], 'column': a['column'], 'y': a['rect'][1], 'evidence': 'Visually verified region' + str(rid) + ': formula/solution text, not a question number'}
    if item not in review.setdefault('ignored_anchors', []):
        review['ignored_anchors'].append(item)
path.write_text(json.dumps(reviews, indent=2))
print('Recorded only visually confirmed non-question regions')
