import json
from extract_jee_pyq_sources import ROOT

path = ROOT / 'visual_reviews.json'
reviews = json.loads(path.read_text())
q = reviews['1DnfcyRt2TK5GXJRR6K_9hvffRloUpO9N'].setdefault('questions', {}).setdefault('67', {})
q['top'] = 365.14
q['boundary_evidence'] = 'Rejected automatic upward expansion because it would include previous solution. Original page22 reviewed: blank band362.39–363.89pt between prior solution descenders andQ67glyphs364.14pt; final crop363.14pt.'
q = reviews['1-0YnLVIrzU-vARvQ_KNEWilYFai1wRsr'].setdefault('questions', {}).setdefault('52', {})
q['top'] = 405.065
q['boundary_evidence'] = 'Visually rejected boundary391.708becauseitincludespreviousworkedanswerW0.336g. Pixelproofpage16left:previousinkends401.315; blank401.565–406.815; finalcrop403.065preservesQ52withoutpreviousanswer.'
path.write_text(json.dumps(reviews, indent=2))
print('Recorded reviewed safe downward boundary for Q67; previous solution is excluded')
