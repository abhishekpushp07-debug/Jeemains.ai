import hashlib
import json
from extract_jee_pyq_sources import ROOT, load_pages

path = ROOT / 'visual_reviews.json'
reviews = json.loads(path.read_text())
updates = {
    '1-0YnLVIrzU-vARvQ_KNEWilYFai1wRsr': {'9': {'solution_verified': True}, '37': {'solution_verified': True}, '38': {'solution_verified': True}, '39': {'solution_verified': True},
        '43': {'key_only': True, 'warning': 'The supplied PDF prints the answer key but no worked explanation for this question.', 'evidence': 'Viewed complete original page13: Q43 endsAns.(3) atleftbottom; rightcolumnstartsQ44 withoutQ43workedsolution'}},
    '1g6FeoS2KhGfygq7jMak_GqjjzjWob8eE': {'73': {'key_only': True, 'warning': 'The supplied PDF prints the answer key but no worked explanation for this question.', 'evidence': 'Viewed complete originalpage24: Q73endsAns.(375); followingreferencehasnoexplanationbeforeQ74'}},
}
for fid, changes in updates.items():
    sha = hashlib.sha256((ROOT / (fid + '.pdf')).read_bytes()).hexdigest()
    record = reviews.setdefault(fid, {'source_sha256': sha})
    if record['source_sha256'] != sha:
        raise ValueError('Source mismatch')
    for number, values in changes.items():
        record.setdefault('questions', {}).setdefault(number, {}).update(values)
fid = '1EWQdoQGnBBWr14c6XvHcc_dDTbOBQPL2'
pages = load_pages(fid, 6)
page = next(p for p in pages if p['page'] == 22)
review = reviews[fid]
top = page['pdf_height'] * .079
review['questions']['67'] = {'anchor': {'page': 22, 'column': 1, 'rect': [page['pdf_width'] * .512, top, page['pdf_width'] * .94, top + 25], 'text': '67. Figure1 electron probability density for2s orbital; Figure2 wavefunction'},
    'solution_verified': True, 'evidence': 'Viewed complete originalpage22: printed67 beside toporbitaldiagram; itsy-axisstartsnear.08pageheight; bothdiagramsandAns.(1),Sol.At sphericalnode retained'}
path.write_text(json.dumps(reviews, indent=2))
print('Recorded observed key-only source gaps and visually verified orbital question67')
