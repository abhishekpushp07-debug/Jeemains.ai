import json
from extract_jee_pyq_sources import ROOT, load_pages

rows = {r['id']: r for r in json.loads((ROOT / 'key_issue_candidates.json').read_text())}
path = ROOT / 'visual_reviews.json'
reviews = json.loads(path.read_text())
CASES = {
    0: (1, '2', None),
    1: (0, '4', 'The source prints answer value24; its option4 is24. The interface key maps that exact printed value to option4, without solving anew.'),
    2: (1, '4', 'The supplied PDF labels NTA answer4 and AllenBonus. Scoring uses the PDF-labeled NTA key; the disagreement is retained in the source solution.'),
    3: (0, '3', 'The source repeats Ans. before its worked differential-equation derivation; the primary standalone key3 is retained.'),
    4: (0, '1', None),
    5: (0, '2', None),
    7: (0, '3', 'The supplied PDF labels NTA answer3 and AllenBONUS. Scoring uses the PDF-labeled NTA key; the publisher disagreement remains visible.'),
    8: (0, '4', None),
}
for rid, (index, answer, warning) in CASES.items():
    row = rows[rid]
    record = reviews.setdefault(row['file'], {'source_sha256': row['source_sha256']})
    if record['source_sha256'] != row['source_sha256']:
        raise ValueError('Source mismatch')
    source = row['key_rows'][index]
    checked = record.setdefault('questions', {}).setdefault(str(row['question']), {})
    checked.update(answer=answer, accepted_answers=[answer], solution_verified=True,
                   key_anchor={'page': source['page'], 'column': source['column'], 'rect': source['line']['rect'], 'text': source['line']['text']},
                   evidence=f'Visually inspected original key-region{rid}, source page{source["page"]}; printed key/option pairing verified')
    if rid == 1:
        checked['printed_answer'] = '24'
    if warning:
        checked['warning'] = warning
    if rid == 2:
        boundary = row['key_rows'][0]
        checked['answer_boundary'] = {'page': boundary['page'], 'column': boundary['column'], 'rect': boundary['line']['rect']}
    if rid == 5:
        page = next(p for p in load_pages(row['file'], 6) if p['page'] == 18)
        checked['top'] = page['pdf_height'] * .175
        checked['evidence'] += '; original graph begins above question51 number, fullpage18 visually inspected'
row = rows[6]
record = reviews.setdefault(row['file'], {'source_sha256': row['source_sha256']})
page = next(p for p in load_pages(row['file'], 6) if p['page'] == 25)
width, height = page['pdf_width'], page['pdf_height']
source = row['key_rows'][0]
record.setdefault('questions', {}).setdefault('75', {}).update(
    answer='10', accepted_answers=['10'], printed_answer='10.19', solution_verified=True, top=height * .073,
    key_anchor={'page': 25, 'column': 1, 'rect': source['line']['rect'], 'text': 'Source worked result10.19%; question requests nearest integer'},
    key_ref={'page': 25, 'rect': [width * .55, height * .387, width * .94, height * .42]},
    answer_boundary={'page': 25, 'column': 1, 'rect': [width * .5, height * .207, width * .95, height * .207]},
    warning='The PDF omits a separate answer-key line. Its supplied worked result is10.19%; the question explicitly asks for the nearest integer, so the accepted entry is10.',
    evidence='Visually inspected complete originalpage25: original reagent/reaction diagram, Sol. diagram and final10.19% statement; no new solution generated')
path.write_text(json.dumps(reviews, indent=2))
print('Recorded9source-backedkey/option/nearest-integer reviews with explicit provenance')
