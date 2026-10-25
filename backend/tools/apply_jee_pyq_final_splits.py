import json
from extract_jee_pyq_sources import ROOT

path = ROOT / 'visual_reviews.json'
reviews = json.loads(path.read_text())
changes = {
    '1WNpd_YogsOGSnPu6k49QqR27trjqBtG3': {'1': {'top': 166.0, 'boundary_evidence': 'Final per-paper sample revealed numerator above Q1 baseline; original page2 viewed from y121.077. Crop begins164pt below SECTION-A and above the complete tangent/log numerator.'}},
    '1-0YnLVIrzU-vARvQ_KNEWilYFai1wRsr': {'2': {'exclude_s_refs': [1], 'continuation_evidence': 'Original first-page right-column region viewed: date/time and MATHEMATICS masthead only before Q3; the OCR p is masthead noise, not Q2 solution content.'}},
    '1DnfcyRt2TK5GXJRR6K_9hvffRloUpO9N': {'67': {'answer_boundary': {'page': 22, 'column': 0, 'rect': [20.825, 503.5, 297.5, 503.5]}, 'adjust_q_refs': [{'index': 0, 'rect': [20.825, 363.14, 297.5, 507], 'omit_rects': [[20.825, 501, 91, 507]]}], 'adjust_s_refs': [{'index': 0, 'rect': [20.825, 501.5, 297.5, 808.32], 'omit_rects': [[91, 501.5, 235, 507]]}], 'split_evidence': 'High-resolution original shows answer ink x47–86 overlapping question subscripts x97–220 around y502–505. Preserve complete option diagrams through507, omit only answer rectangle on question; omit only trailing option subscripts on solution. No source text is replaced.'}},
    '1jR2YgSqqzQK6_8W8T43Nam3tWe8ZG2Ok': {'13': {'answer_boundary': {'page': 6, 'column': 0, 'rect': [20.825, 425.188, 297.5, 425.188]}, 'split_evidence': 'Viewed original optionbaselineandkey; confirmedblank422.438–423.938pt; split423.188avoidsclippingoption30'}},
    '1yz4CzIaEedp5SbfanzVQ0l-f6o1KVQUB': {'22': {'answer_boundary': {'page': 9, 'column': 1, 'rect': [297.5, 149.155, 574.175, 149.155]}, 'split_evidence': 'Viewed original integerquestionlastline; blank146.155–147.905pt; split147.155beforeAns96'}},
    '16Q9NDIGcNio6dWvGdPt_EPhrNRjBFOY1': {'2': {'adjust_s_refs': [{'index': 1, 'rect': [297.5, 150.023, 574.175, 186.615]}], 'continuation_evidence': 'Do NOT delete whole segment: originalSol.Totalstarts152.023with144workedanswer. Removeonlyunrelatedmastheadabove150.023'}},
    '1Vn1Rk4e1gPAu46XWpJK74tm22BFid5O1': {'50': {'exclude_s_refs': [1], 'continuation_evidence': 'Viewed source segmentcontainsCHEMISTRYSECTIONAheadingonly; noQ50workedcontent'}, '52': {'exclude_s_refs': [1], 'continuation_evidence': 'Viewed source segmentcontainsCHEMISTRYheadingonly; noQ52workedcontent'}},
}
for fid, questions in changes.items():
    for number, fields in questions.items():
        reviews[fid].setdefault('questions', {}).setdefault(number, {}).update(fields)
path.write_text(json.dumps(reviews, indent=2))
print('Recorded source-verified final split/continuation fixes, preserving real continued solutions')
