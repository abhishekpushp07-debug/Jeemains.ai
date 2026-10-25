import argparse
import hashlib
import json
from pathlib import Path

from extract_jee_pyq_sources import ROOT


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--confirm', required=True, help='Comma-separated source-region-id:visually-read-question-number pairs')
    args = parser.parse_args()
    regions = {r['id']: r for r in json.loads((ROOT / 'number_review_candidates.json').read_text())}
    path = ROOT / 'visual_reviews.json'
    reviews = json.loads(path.read_text())
    for pair in args.confirm.split(','):
        rid, number = (int(v) for v in pair.split(':'))
        row = regions[rid]
        if number not in row['missing']:
            raise ValueError('Read number is outside the flagged gap; needs a separate review')
        fid = row['file']
        source_sha = hashlib.sha256((ROOT / (fid + '.pdf')).read_bytes()).hexdigest()
        review = reviews.setdefault(fid, {'source_sha256': source_sha})
        if review['source_sha256'] != source_sha:
            raise ValueError('Source changed after review')
        q = review.setdefault('questions', {}).setdefault(str(number), {})
        q['anchor'] = {'page': row['page'], 'column': row['column'], 'rect': row['line']['rect'], 'text': row['line']['text']}
        q['evidence'] = f'Original number-region {rid} visually read as {number}; page{row["page"]}, column{row["column"]}; no numerical inference'
    path.write_text(json.dumps(reviews, indent=2))
    print('Recorded source-number visual confirmations:', len(args.confirm.split(',')))
