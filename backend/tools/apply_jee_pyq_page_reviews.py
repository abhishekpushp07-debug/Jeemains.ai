import hashlib
import json
from extract_jee_pyq_sources import ROOT

path = ROOT / 'visual_reviews.json'
reviews = json.loads(path.read_text())
changes = {
    '1-0YnLVIrzU-vARvQ_KNEWilYFai1wRsr': {
        '9': {'anchor': {'page': 3, 'column': 0, 'rect': [48.79, 458.447, 290.657, 468.265], 'text': '9. The product of all solutions of the equation'}, 'evidence': 'Viewed original page3 left: question9 complete; border OCR changed margin estimate'},
        '38': {'anchor': {'page': 12, 'column': 0, 'rect': [48.492, 188.02, 290.657, 200.515], 'text': '38. A small point of mass m is placed at a distance 2R'}, 'evidence': 'Viewed original page12 left: question38 and its sphere diagram'},
        '39': {'anchor': {'page': 12, 'column': 0, 'rect': [48.492, 592.322, 290.36, 601.842], 'text': '39. The work functions of cesium (Cs) and lithium (Li)'}, 'evidence': 'Viewed original page12 left lower: question39'},
    },
    '16Q9NDIGcNio6dWvGdPt_EPhrNRjBFOY1': {
        '43': {'anchor': {'page': 12, 'column': 0, 'rect': [48.0, 78.5, 291.0, 112.0], 'text': '43. The tube of length L is shown in the figure'}, 'solution_verified': True, 'evidence': 'Viewed original page12: printed43 beside tube diagram, diagram circle1 at80.623pt, start78.5 keeps it intact; matching Sol.figure and equation visible'},
    },
    '1F2htFLI68TiQEQQv0TGi_DpzkVEZJ6WC': {
        '2': {'anchor': {'page': 1, 'column': 0, 'rect': [48.0, 475.0, 291.0, 488.0], 'text': '2. Let I(x) = integral'}, 'evidence': 'Viewed original first page left lower: printed question2 begins integral at about475pt'},
    },
    '1EWQdoQGnBBWr14c6XvHcc_dDTbOBQPL2': {
        '9': {'solution_end': {'page': 4, 'column': 1, 'rect': [0, 1661, 0, 0]}, 'warning': 'The source repeats question10 worked text before the actual question10. That duplicated block is excluded from question9 solution.', 'evidence': 'Viewed original pages4 and5: Q9 solution ends before10.Ans.() at1663.409pt; actualQ10 withAns.(1) and full solution appears on page5'},
    },
}
for fid, questions in changes.items():
    sha = hashlib.sha256((ROOT / (fid + '.pdf')).read_bytes()).hexdigest()
    review = reviews.setdefault(fid, {'source_sha256': sha})
    if review['source_sha256'] != sha:
        raise ValueError('Source mismatch')
    for number, fields in questions.items():
        review.setdefault('questions', {}).setdefault(number, {}).update(fields)
reviews['1F2htFLI68TiQEQQv0TGi_DpzkVEZJ6WC']['source_incomplete'] = {'missing_questions': [48, 49, 50], 'evidence': 'Visually verified page15 ends47; page16 starts51. Do not publish as a complete75-question paper.'}
path.write_text(json.dumps(reviews, indent=2))
print('Recorded explicit page-backed anchor/boundary reviews; incomplete source remains blocked')
