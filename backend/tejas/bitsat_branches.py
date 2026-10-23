from collections import Counter
from typing import Literal
from fastapi import APIRouter, Depends, Query
from .auth import current

router = APIRouter(prefix='/api/bitsat', tags=['BITSAT branch matches'])
REFERENCE = {
    'year': '2026–2027', 'checked_date': '2026-10-23', 'maximum': 390,
    'title': 'BITS Pilani · Final BITSAT cut-off scores, Academic Year 2026–2027',
    'url': 'https://admissions.bits-pilani.ac.in/FD/BITSAT_cutOffs.html',
    'source_scope': 'Official final campus/programme cutoffs, checked against the published 2026–2027 tables and supplied screenshots. Historical reference only, not a future admission prediction.',
}
CAMPUS_NAMES = {'pilani': 'Pilani', 'goa': 'K K Birla Goa', 'hyderabad': 'Hyderabad'}
TABLE = {
    'pilani': [
        ('be', 'B.E. Chemical', 226), ('be', 'B.E. Civil', 222),
        ('be', 'B.E. Electrical & Electronics', 266), ('be', 'B.E. Mechanical', 239),
        ('be', 'B.E. Computer Science', 308), ('be', 'B.E. Electronics & Instrumentation', 261),
        ('be', 'B.E. Electronics & Communication', 289), ('be', 'B.E. Manufacturing', 226),
        ('be', 'B.E. Mathematics and Computing', 299), ('be', 'B.E. Environmental and Sustainability', 213),
        ('be', 'B.E. Pharmaceutical Engg.', 211), ('bpharm', 'B. Pharm', 200),
        ('msc', 'M.Sc. Biological Sciences', 218), ('msc', 'M.Sc. Chemistry', 227),
        ('msc', 'M.Sc. Economics', 256), ('msc', 'M.Sc. Mathematics', 241),
        ('msc', 'M.Sc. Physics', 235), ('msc', 'M.Sc. Semiconductor and Nanoscience', 246),
    ],
    'goa': [
        ('be', 'B.E. Chemical', 223), ('be', 'B.E. Electrical & Electronics', 253),
        ('be', 'B.E. Mechanical', 233), ('be', 'B.E. Computer Science', 274),
        ('be', 'B.E. Electronics & Instrumentation', 250), ('be', 'B.E. Electronics & Communication', 261),
        ('be', 'B.E. Electronics and Computer', 266), ('be', 'B.E. Mathematics and Computing', 270),
        ('be', 'B.E. Environmental and Sustainability', 210),
        ('msc', 'M.Sc. Biological Sciences', 217), ('msc', 'M.Sc. Chemistry', 223),
        ('msc', 'M.Sc. Economics', 246), ('msc', 'M.Sc. Mathematics', 233),
        ('msc', 'M.Sc. Physics', 231), ('msc', 'M.Sc. Semiconductor and Nanoscience', 241),
    ],
    'hyderabad': [
        ('be', 'B.E. Chemical', 223), ('be', 'B.E. Civil', 220),
        ('be', 'B.E. Electrical & Electronics', 251), ('be', 'B.E. Mechanical', 228),
        ('be', 'B.E. Computer Science', 272), ('be', 'B.E. Electronics & Instrumentation', 249),
        ('be', 'B.E. Electronics & Communication', 261), ('be', 'B.E. Mathematics and Computing', 268),
        ('be', 'B.E. Environmental and Sustainability', 208), ('be', 'B.E. Pharmaceutical Engg.', 205),
        ('bpharm', 'B. Pharm', 200), ('msc', 'M.Sc. Biological Sciences', 217),
        ('msc', 'M.Sc. Chemistry', 223), ('msc', 'M.Sc. Economics', 244),
        ('msc', 'M.Sc. Mathematics', 230), ('msc', 'M.Sc. Physics', 229),
        ('msc', 'M.Sc. Semiconductor and Nanoscience', 241),
    ],
}
METHOD = 'Top 3 means distinct programmes with the highest published 2026–2027 cutoffs at or below your score. For each programme, show the highest-cutoff matching campus; other matching campuses are listed too. Equal cutoffs use alphabetical programme/campus order. This is not a quality, placement or personal-preference ranking.'
LIMIT = 'Meeting a historical cutoff is not an admission offer or probability. Cutoffs change each year; official academic/subject eligibility, preferences, seat availability and PCM tie-breaking still apply. M.Sc. is a separate programme, not a guaranteed future B.E. branch. No rank or admission chances are invented.'


def matches_for_score(score, campus='all', programme='be'):
    rows = [{'campus_id': c, 'campus': CAMPUS_NAMES[c], 'programme': name, 'degree': kind, 'cutoff': cutoff}
            for c, entries in TABLE.items() if campus in ('all', c)
            for kind, name, cutoff in entries if programme in ('all', kind)]
    groups = {}
    for row in sorted(rows, key=lambda r: (-r['cutoff'], r['programme'], r['campus'])):
        if row['cutoff'] <= score:
            groups.setdefault(row['programme'], []).append(row)
    selected = []
    for name, options in list(groups.items())[:3]:
        selected.append({**options[0], 'margin': score-options[0]['cutoff'], 'at_cutoff': score == options[0]['cutoff'],
                         'other_campuses': options[1:]})
    above = {}
    for row in sorted(rows, key=lambda r: (r['cutoff'], r['programme'], r['campus'])):
        if row['cutoff'] > score and row['programme'] not in groups:
            above.setdefault(row['programme'], {**row, 'marks_needed': row['cutoff']-score})
    return {'kind': 'branch_matches', 'state': 'available', 'exam': 'BITSAT', 'score': score,
            'maximum': 390, 'score_basis': 'entered_score', 'campus_filter': campus, 'programme_filter': programme,
            'matches': selected, 'matching_programmes': len(groups), 'next_targets': list(above.values())[:3],
            'reference': REFERENCE, 'methodology': METHOD, 'limitation': LIMIT,
            'score_note': 'An entered score on the published 390-mark reference scale. This does not change any saved mock result.'}


def block_score_ok(s):
    return isinstance(s, int) and not isinstance(s, bool) and -130 <= s <= 390


def attempt_matches(a, score_version):
    r, qs = a.get('rules', {}), a.get('questions', [])
    base = [q for q in qs if not q.get('bonus')]
    names = {'maths': 'mathematics', 'english proficiency': 'english'}
    counts = Counter(names.get(q.get('subject', '').strip().lower(), q.get('subject', '').strip().lower()) for q in base)
    valid = (score_version == 'original' and a.get('mode') == 'practice' and not a.get('parent_attempt')
             and not a.get('competition_end') and a.get('test_kind') == 'mock' and r.get('minutes') == 180
             and counts == Counter({'physics': 30, 'chemistry': 30, 'mathematics': 40, 'english': 10, 'logical reasoning': 20})
             and len(qs)-len(base) in (0, 12)
             and all(q.get('type') == 'mcq' and q.get('disposition', 'standard') == 'standard'
                     and (q.get('scoring') or r).get('correct') == 3
                     and (q.get('scoring') or r).get('wrong') == -1
                     and (q.get('scoring') or r).get('skipped') == 0 for q in qs))
    summary = a.get('summary') or {}
    block = summary.get('main_block') if len(qs) > 130 else summary
    block_score = block.get('score') if isinstance(block, dict) else None
    if (not valid or not block_score_ok(block_score) or block.get('maximum') != 390):
        return {'kind': 'branch_matches', 'state': 'unavailable', 'exam': 'BITSAT', 'score': None, 'maximum': 390,
                'matches': [], 'reference': REFERENCE, 'methodology': METHOD, 'limitation': LIMIT,
                'reason': 'Automatic comparison needs an original, standard 180-minute BITSAT full mock with 130 main questions and a saved 390-mark main-block score. No chapter, retry, corrected or scaled scores are used. You can enter a separate reference score below.'}
    result = matches_for_score(block['score'])
    result.update(score_basis='mock_main_block', original_total=summary['score'],
                  bonus_excluded=(summary.get('bonus_block') or {}).get('score', 0),
                  score_note='Using this mock’s original 130-question main-block score out of 390. Extra-question bonus marks are excluded from this reference comparison, never from your saved result. A mock’s difficulty is not calibrated to the real exam.')
    return result


@router.get('/branch-matches')
async def branch_matches(score: int = Query(ge=-130, le=390),
                         campus: Literal['all', 'pilani', 'goa', 'hyderabad'] = 'all',
                         programme: Literal['be', 'msc', 'bpharm', 'all'] = 'be', u=Depends(current)):
    return matches_for_score(score, campus, programme)
